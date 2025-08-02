<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\News;
use App\Models\Image;
use App\Models\Category;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;
use Intervention\Image\ImageManager;
use Intervention\Image\Drivers\Gd\Driver;
use Illuminate\Validation\ValidationException;

class NewsController extends Controller
{
    public function index()
    {
        try {
            $news = News::with('category', 'images')->latest()->paginate(10);
            return view('admin.news.index', compact('news'));
        } catch (\Exception $e) {
            Log::error('Error fetching news articles for index: ' . $e->getMessage());
            return redirect()->back()->with('error', 'Failed to load news articles. Please try again.');
        }
    }

    public function create()
    {
        try {
            $categories = Category::all();
            return view('admin.news.create', compact('categories'));
        } catch (\Exception $e) {
            Log::error('Error loading news creation form: ' . $e->getMessage());
            return redirect()->back()->with('error', 'Failed to load the creation form. Please try again.');
        }
    }

    public function store(Request $request)
    {
        try {
            $request->validate([
                'title' => 'required|string|max:255',
                'description' => 'required|string',
                'category_id' => 'required|exists:categories,id',
                'images' => 'required|array|min:1', // Ensure at least one image is uploaded
                'images.*' => 'image|mimes:jpeg,png,jpg,gif,svg|max:1024', // Max 1MB per image
                'status' => 'required|in:draft,published',
                'date' => 'required|date',
                'slider_duration' => 'nullable|integer|min:1',
            ]);

            $news = News::create([
                'title' => $request->title,
                'description' => $request->description,
                'category_id' => $request->category_id,
                'status' => $request->status,
                'date' => $request->date,
            ]);

            if ($request->hasFile('images')) {
                $this->processAndStoreImages($request->file('images'), $news, $request->slider_duration ?? 5);
            }

            return response()->json(['success' => true, 'message' => 'News article created successfully!', 'redirect' => route('admin.news.index')]);

        } catch (ValidationException $e) {
            Log::error('Validation error creating news article: ' . $e->getMessage(), ['errors' => $e->errors()]);
            return response()->json(['success' => false, 'message' => 'Validation failed', 'errors' => $e->errors()], 422);
        } catch (\Exception $e) {
            Log::error('Error creating news article: ' . $e->getMessage());
            return response()->json(['success' => false, 'message' => 'Failed to create news article. Please try again.'], 500);
        }
    }

    public function edit(News $news)
    {
        try {
            $categories = Category::all();
            // Eager load images to ensure they are available
            $news->load('images');
            return view('admin.news.edit', compact('news', 'categories'));
        } catch (\Exception $e) {
            Log::error('Error loading news edit form: ' . $e->getMessage());
            return redirect()->back()->with('error', 'Failed to load the edit form. Please try again.');
        }
    }


    public function update(Request $request, News $news)
    {
        try {
            $request->validate([
                'title' => 'required|string|max:255',
                'description' => 'required|string',
                'category_id' => 'required|exists:categories,id',
                'new_images.*' => 'nullable|image|mimes:jpeg,png,jpg,gif,svg|max:1024', // Max 1MB per new image
                'status' => 'required|in:draft,published',
                'date' => 'required|date',
                'existing_image_duration.*' => 'nullable|integer|min:1', // Validate duration for existing images
                'new_slide_duration' => 'nullable|integer|min:1', // Default duration for new images
            ]);

            $news->update([
                'title' => $request->title,
                'description' => $request->description,
                'category_id' => $request->category_id,
                'status' => $request->status,
                'date' => $request->date,
            ]);

            // Update durations for existing images
            if ($request->has('existing_image_duration')) {
                foreach ($request->input('existing_image_duration') as $imageId => $duration) {
                    $image = Image::find($imageId);
                    if ($image) {
                        // Store duration in milliseconds
                        $image->slide_duration = $duration * 1000;
                        $image->save();
                    }
                }
            }

            // Process and store new images
            if ($request->hasFile('new_images')) {
                $this->processAndStoreImages($request->file('new_images'), $news, $request->new_slide_duration ?? 5);
            }

            return response()->json(['success' => true, 'message' => 'News article updated successfully!', 'redirect' => route('admin.news.index')]);

        } catch (ValidationException $e) {
            Log::error('Validation error updating news article: ' . $e->getMessage(), ['errors' => $e->errors()]);
            return response()->json(['success' => false, 'message' => 'Validation failed', 'errors' => $e->errors()], 422);
        } catch (\Exception $e) {
            Log::error('Error updating news article: ' . $e->getMessage());
            return response()->json(['success' => false, 'message' => 'Failed to update news article. Please try again.'], 500);
        }
    }

public function destroy(News $news)
{
    try {
        // Delete associated images from storage
        foreach ($news->images as $image) {
            Storage::disk('public')->delete($image->url); // Delete original
            // Delete resized versions if paths are stored in 'sizes'
            if (is_array($image->sizes)) {
                foreach ($image->sizes as $sizeData) {
                    if (isset($sizeData['path'])) {
                         Storage::disk('public')->delete($sizeData['path']);
                    }
                }
            }
        }
        $news->delete();

        // Return redirect with flash message instead of JSON
        return redirect()->route('admin.news.index')
                       ->with('success', 'News article deleted successfully!');

    } catch (\Exception $e) {
        Log::error('Error deleting news article: ' . $e->getMessage());

        // Return redirect with error message instead of JSON
        return redirect()->route('admin.news.index')
                       ->with('error', 'Failed to delete news article. Please try again.');
    }
}

    public function deleteImage(News $news, Image $image)
    {
        try {
            // Ensure the image belongs to the news article
            if ($image->news_id !== $news->id) {
                return response()->json(['success' => false, 'message' => 'Image does not belong to this news article.'], 403);
            }

            // Delete image files from storage
            Storage::disk('public')->delete($image->url); // Delete original
            if (is_array($image->sizes)) {
                foreach ($image->sizes as $sizeData) {
                    if (isset($sizeData['path'])) {
                         Storage::disk('public')->delete($sizeData['path']);
                    }
                }
            }

            // Delete image record from database
            $image->delete();

            return response()->json(['success' => true, 'message' => 'Image deleted successfully.']);
        } catch (\Exception $e) {
            Log::error('Error deleting image: ' . $e->getMessage());
            return response()->json(['success' => false, 'message' => 'Failed to delete image. Please try again.'], 500);
        }
    }


    /**
     * Helper function to process and store images, including resized versions and dimensions.
     * @param array $imageFiles Array of uploaded files.
     * @param News $news The news article to associate images with.
     * @param int $slideDuration Default slide duration in seconds.
     */
    private function processAndStoreImages(array $imageFiles, News $news, int $slideDuration)
    {
        $manager = new ImageManager(new Driver());

        foreach ($imageFiles as $imageFile) {
            if (!$this->isValidImage($imageFile)) {
                Log::warning('Skipping invalid image file: ' . $imageFile->getClientOriginalName());
                continue;
            }

            $image = $manager->read($imageFile->getRealPath());

            // Get original dimensions
            $originalWidth = $image->width();
            $originalHeight = $image->height();

            $imageSizesData = []; // To store path, width, height for each size

            // Define target sizes for compression and resizing
            // The toJpeg(80) call applies 80% quality compression.
            $targetSizes = [
                'thumbnail' => ['width' => 150, 'height' => 150],
                'medium' => ['width' => 600, 'height' => 400],
                'large' => ['width' => 1200, 'height' => 800],
            ];

            foreach ($targetSizes as $name => $dims) {
                // Clone the image instance to avoid modifying the original for subsequent resizes
                $resizedImage = $image->scaleDown($dims['width'], $dims['height']); // Use scaleDown to maintain aspect ratio and not upscale
                $path = 'news_images/' . $name . '/' . Str::random(20) . '.jpg';
                Storage::disk('public')->put($path, (string) $resizedImage->toJpeg(80)); // Compression at 80% quality
                $imageSizesData[$name] = [
                    'path' => $path,
                    'width' => $resizedImage->width(),
                    'height' => $resizedImage->height(),
                ];
            }

            // Store original as well, with its dimensions
            $originalPath = $imageFile->store('news_images/original', 'public');
            $imageSizesData['original'] = [
                'path' => $originalPath,
                'width' => $originalWidth,
                'height' => $originalHeight,
            ];

            $imageTitle = $this->generateImageTitle($imageFile->getClientOriginalName());

            $news->images()->create([
                'url' => $originalPath, // Store original URL in 'url' column
                'title' => $imageTitle,
                'slide_duration' => $slideDuration * 1000, // Store in milliseconds
                'sizes' => $imageSizesData, // Store comprehensive size data (path, width, height for each)
            ]);
        }
    }

    private function isValidImage($file)
    {
        try {
            if (!$file || !$file->isValid()) return false;
            $allowedMimes = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif', 'image/svg+xml'];
            if (!in_array($file->getMimeType(), $allowedMimes)) return false;
            // Ensure it's a real image and not just a file with an image mime type
            return getimagesize($file->getRealPath()) !== false;
        } catch (\Exception $e) {
            Log::error('Image validation failed: ' . $e->getMessage());
            return false;
        }
    }

    private function generateImageTitle($filename)
    {
        $title = pathinfo($filename, PATHINFO_FILENAME);
        $title = str_replace(['-', '_', '.'], ' ', $title);
        $title = preg_replace('/\d+/', '', $title);
        $title = preg_replace('/\b(img|image|photo|pic|picture)\b/i', '', $title);
        $title = trim(preg_replace('/\s+/', ' ', $title));
        $title = ucwords(strtolower($title));
        return $title;
    }
}
