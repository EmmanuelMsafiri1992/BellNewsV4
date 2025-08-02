<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\NewsController;
use App\Http\Controllers\SettingController; // Ensure this controller exists and is imported

// Unified News API endpoint.
// It's generally better to use a named route and a specific API method like 'apiIndex'.
Route::get('/news', [NewsController::class, 'apiIndex'])->name('api.news.index');

// Public API endpoint to fetch global settings
Route::get('/settings', [SettingController::class, 'index'])->name('api.settings.index');
