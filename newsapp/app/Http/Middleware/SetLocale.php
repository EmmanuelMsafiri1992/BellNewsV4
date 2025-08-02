<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\App;

class SetLocale
{
    public function handle(Request $request, Closure $next)
    {
        // Check session, cookie, or header for locale
        $locale = $request->session()->get('locale') ?: $request->cookie('locale');
        if (!$locale && $request->hasHeader('X-Locale')) {
            $locale = $request->header('X-Locale');
        }
        if (!$locale && $request->has('locale')) {
            $locale = $request->input('locale');
        }

        // Fallback to localStorage (via JavaScript) if available, otherwise default to 'en'
        if (!$locale) {
            $locale = session('locale') ?: (isset($_SERVER['HTTP_X_LOCALE']) ? $_SERVER['HTTP_X_LOCALE'] : 'en');
        }

        // Set the application locale
        App::setLocale($locale);

        // Pass the locale to the next request
        return $next($request)->withCookie(cookie()->forever('locale', $locale));
    }
}
