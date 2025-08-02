<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\Category;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;

class CategoryController extends Controller
{
    public function __construct()
    {
        $this->middleware('auth');
    }

    public function index()
    {
        $categories = Category::select('id', 'name')->get();
        return response()->json($categories);
    }

    public function store(Request $request)
    {
        Log::info('Category store request received', $request->all());

        try {
            $request->validate([
                'name' => 'required|string|max:255|unique:categories,name',
            ]);

            $category = Category::create($request->all());
            Log::info('Category created', ['category' => $category]);

            if ($request->expectsJson()) {
                return response()->json([
                    'success' => true,
                    'category' => $category,
                    'message' => 'Category added successfully'
                ]);
            }

            return redirect()->back()->with('success', 'Category added successfully');
        } catch (\Exception $e) {
            Log::error('Error creating category', ['error' => $e->getMessage(), 'request' => $request->all()]);
            return redirect()->back()->with('error', 'Failed to add category: ' . $e->getMessage());
        }
    }
}
