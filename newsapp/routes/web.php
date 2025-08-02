<?php

use Illuminate\Support\Facades\Route;
use Illuminate\Support\Facades\Auth;
use App\Http\Controllers\Admin\NewsController as AdminNewsController;
use App\Http\Controllers\NewsController;
use App\Http\Controllers\Admin\DashboardController;
use App\Http\Controllers\Admin\LicenseController;
use App\Http\Controllers\Admin\CategoryController;
use App\Http\Middleware\SetAdminLocale;
use App\Http\Middleware\CheckLicense;
use App\Http\Controllers\LicenseActivationController;


// Public landing page
Route::get('/', function () {
    return view('layouts.app');
});

// Public news page (non-admin)
Route::get('/news', [NewsController::class, 'index'])->name('news.index');

// Auth routes
Auth::routes();

// Add the license expired route (accessible even if not authenticated or license is invalid)
Route::get('/license-expired', function () {
    return view('auth.license-expired');
})->name('license.expired');

// New route for license activation (accessible to guests, as logged-out users will hit this)
Route::post('/license/activate', [LicenseActivationController::class, 'activate'])->name('license.activate');

// Admin routes
Route::prefix('admin')->middleware(['auth', SetAdminLocale::class])->group(function () {
    Route::get('/dashboard', [DashboardController::class, 'index'])->name('admin.dashboard');
    Route::get('/settings', [DashboardController::class, 'settings'])->name('admin.settings');
    Route::post('/settings/password', [DashboardController::class, 'updatePassword'])->name('admin.settings.password');
    // New route for application settings
    Route::post('/settings/application', [DashboardController::class, 'updateApplicationSettings'])->name('admin.settings.application');
      // New route for language settings
    Route::post('/settings/language', [DashboardController::class, 'updateLanguageSettings'])->name('admin.settings.language'); // Add this line

    // Admin News routes
    Route::get('/news', [AdminNewsController::class, 'index'])->name('admin.news.index');
    Route::get('/news/create', [AdminNewsController::class, 'create'])->name('admin.news.create');
    Route::post('/news', [AdminNewsController::class, 'store'])->name('admin.news.store');
    Route::get('/news/{news}/edit', [AdminNewsController::class, 'edit'])->name('admin.news.edit');
    Route::put('/news/{news}', [AdminNewsController::class, 'update'])->name('admin.news.update');
    Route::delete('/news/{news}', [AdminNewsController::class, 'destroy'])->name('admin.news.destroy');
    Route::get('/news/{news}', [AdminNewsController::class, 'show'])->name('admin.news.show');

    // !!! ADD THIS ROUTE FOR IMAGE DELETION !!!
    Route::delete('/news/{news}/images/{image}', [AdminNewsController::class, 'destroyImage'])->name('admin.news.images.destroy');

    Route::get('/news/images/{imagePath}', [AdminNewsController::class, 'showImage'])->name('admin.news.showImage');
    Route::post('/settings/footer', [DashboardController::class, 'updateFooterSettings'])->name('admin.settings.footer');
    Route::post('/settings/header', [DashboardController::class, 'updateHeaderSettings'])->name('admin.settings.header');

    // NEW LICENSE ROUTE (This was the first instance, keeping it)
    Route::post('/settings/license', [DashboardController::class, 'updateLicenseSettings'])->name('admin.settings.license');
    // Categories
    Route::get('/categories', [App\Http\Controllers\Admin\CategoryController::class, 'index'])->name('admin.categories.index');
    Route::post('/categories', [App\Http\Controllers\Admin\CategoryController::class, 'store'])->name('admin.categories.store');
        // Superadmin-only Routes for License Management - ADD THIS BLOCK
    Route::middleware('superadmin')->group(function () {
        Route::get('/licenses/generate', [App\Http\Controllers\Admin\LicenseController::class, 'generateForm'])->name('admin.licenses.generate.form');
        Route::post('/licenses/generate', [App\Http\Controllers\Admin\LicenseController::class, 'generate'])->name('admin.licenses.generate');
        Route::get('/licenses', [App\Http\Controllers\Admin\LicenseController::class, 'index'])->name('admin.licenses.index'); // List all licenses
        // The line below was the duplicate and has been removed:
        // Route::post('/settings/license', [DashboardController::class, 'updateLicenseSettings'])->name('admin.settings.license');
        Route::delete('/licenses/{license}', [LicenseController::class, 'destroy'])->name('admin.licenses.destroy');
            // New route for Slider settings - ADD THIS LINE
        Route::post('/settings/slider', [DashboardController::class, 'updateSliderSettings'])->name('admin.settings.slider');
       // User Management
       Route::resource('users', App\Http\Controllers\Admin\UserController::class, ['as' => 'admin'])->except(['show', 'update']);
       Route::put('/users/{user}/password', [App\Http\Controllers\Admin\UserController::class, 'updatePassword'])->name('admin.users.updatePassword');
      Route::get('/users/{user}/license/edit', [App\Http\Controllers\Admin\UserController::class, 'editLicense'])->name('admin.users.license.edit');
       Route::put('/users/{user}/license', [App\Http\Controllers\Admin\UserController::class, 'updateLicense'])->name('admin.users.license.update');

    });
});
