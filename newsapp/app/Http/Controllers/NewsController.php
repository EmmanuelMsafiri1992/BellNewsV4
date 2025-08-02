<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\News;
use Illuminate\Support\Facades\Log;

class NewsController extends Controller
{
    public function index()
    {
        $news = News::all();
        return view('news.index', compact('news')); // Example for admin view
    }

    // public function apiIndex()
    // {
    //     try {
    //         $news = News::with('category')->get();
    //         if ($news->isEmpty()) {
    //             Log::info('No news records found in the database.');
    //             return response()->json([
    //                 'success' => true,
    //                 'data' => []
    //             ]);
    //         }
    //         return response()->json([
    //             'success' => true,
    //             'data' => $news->map(function ($item) {
    //                 return [
    //                     'id' => $item->id,
    //                     'image_url' => $item->image ? asset('storage/' . $item->image) : null,
    //                     'title' => $item->title ?? 'No Title',
    //                     'description' => $item->description ?? 'No Description',
    //                     'full_description' => $item->description ?? 'No Description', // Assuming full_description is the same as description
    //                     'date' => $item->created_at ? $item->created_at->format('M d, Y') : null,
    //                     'status' => $item->status ?? 'draft',
    //                     'category' => $item->category ? $item->category->name : 'Uncategorized',
    //                 ];
    //             })
    //         ]);
    //     } catch (\Exception $e) {
    //         Log::error('Error in apiIndex: ' . $e->getMessage());
    //         return response()->json([
    //             'success' => false,
    //             'message' => 'An error occurred while fetching news.',
    //             'error' => $e->getMessage()
    //         ], 500);
    //     }
    // }
//     public function apiIndex()
// {
//     try {
//         $news = News::with('category', 'images')->get(); // Load images relationship

//         if ($news->isEmpty()) {
//             Log::info('No news records found in the database.');
//             return response()->json([
//                 'success' => true,
//                 'data' => []
//             ]);
//         }

//         return response()->json([
//             'success' => true,
//             'data' => $news->map(function ($item) {
//                 return [
//                     'id' => $item->id,
//                     // Get the first image from the images relationship
//                     'image_url' => $item->images->isNotEmpty()
//                         ? asset('storage/' . $item->images->first()->url)
//                         : null,
//                     'title' => $item->title ?? 'No Title',
//                     'description' => $item->description ?? 'No Description',
//                     'full_description' => $item->description ?? 'No Description',
//                     'date' => $item->created_at ? $item->created_at->format('M d, Y') : null,
//                     'status' => $item->status ?? 'draft',
//                     'category' => $item->category ? $item->category->name : 'Uncategorized',
//                     // Optional: include all images if needed
//                     'all_images' => $item->images->map(function($img) {
//                         return asset('storage/' . $img->url);
//                     }),
//                 ];
//             })
//         ]);
//     } catch (\Exception $e) {
//         Log::error('Error in apiIndex: ' . $e->getMessage());
//         return response()->json([
//             'success' => false,
//             'message' => 'An error occurred while fetching news.',
//             'error' => $e->getMessage()
//         ], 500);
//     }
// }
// public function apiIndex()
// {
//     try {
//         $news = News::with('category', 'images')->get();

//         // Debug logging
//         Log::info('News count: ' . $news->count());
//         foreach ($news as $item) {
//             Log::info('News ID: ' . $item->id . ', Images count: ' . $item->images->count());
//             foreach ($item->images as $image) {
//                 Log::info('Image URL: ' . $image->url);
//                 Log::info('Full asset URL: ' . asset('storage/' . $image->url));
//             }
//         }

//         if ($news->isEmpty()) {
//             return response()->json(['success' => true, 'data' => []]);
//         }

//         return response()->json([
//             'success' => true,
//             'data' => $news->map(function ($item) {
//                 $imageUrl = null;
//                 if ($item->images->isNotEmpty()) {
//                     $imageUrl = asset('storage/' . $item->images->first()->url);
//                 }

//                 return [
//                     'id' => $item->id,
//                     'image_url' => $imageUrl,
//                     'title' => $item->title ?? 'No Title',
//                     'description' => $item->description ?? 'No Description',
//                     'full_description' => $item->description ?? 'No Description',
//                     'date' => $item->created_at ? $item->created_at->format('M d, Y') : null,
//                     'status' => $item->status ?? 'draft',
//                     'category' => $item->category ? $item->category->name : 'Uncategorized',
//                     // Debug info - remove this later
//                     'debug_images_count' => $item->images->count(),
//                     'debug_raw_image_path' => $item->images->first()->url ?? null,
//                 ];
//             })
//         ]);
//     } catch (\Exception $e) {
//         Log::error('Error in apiIndex: ' . $e->getMessage());
//         return response()->json([
//             'success' => false,
//             'message' => 'An error occurred while fetching news.',
//             'error' => $e->getMessage()
//         ], 500);
//     }
// }
public function apiIndex()
{
    try {
        $news = News::with('category', 'images')->get();

        $slides = [];

        foreach ($news as $item) {
            if ($item->images->isNotEmpty()) {
                // Create a slide for each image
                foreach ($item->images as $image) {
                    $slides[] = [
                        'id' => $item->id . '_' . $image->id, // Unique ID
                        'news_id' => $item->id,
                        'image_url' => asset('storage/' . $image->url),
                        'title' => $item->title ?? 'No Title',
                        'description' => $item->description ?? 'No Description',
                        'full_description' => $item->description ?? 'No Description',
                        'date' => $item->created_at ? $item->created_at->format('M d, Y') : null,
                        'status' => $item->status ?? 'draft',
                        'category' => $item->category ? $item->category->name : 'Uncategorized',
                    ];
                }
            } else {
                // News with no images - use placeholder or skip
                $slides[] = [
                    'id' => $item->id,
                    'news_id' => $item->id,
                    'image_url' => '',
                    'title' => $item->title ?? 'No Title',
                    'description' => $item->description ?? 'No Description',
                    'full_description' => $item->description ?? 'No Description',
                    'date' => $item->created_at ? $item->created_at->format('M d, Y') : null,
                    'status' => $item->status ?? 'draft',
                    'category' => $item->category ? $item->category->name : 'Uncategorized',
                ];
            }
        }

        return response()->json([
            'success' => true,
            'data' => $slides
        ]);

    } catch (\Exception $e) {
        Log::error('Error in apiIndex: ' . $e->getMessage());
        return response()->json([
            'success' => false,
            'message' => 'An error occurred while fetching news.',
            'error' => $e->getMessage()
        ], 500);
    }
}
}
