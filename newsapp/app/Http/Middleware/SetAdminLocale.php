<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\App;
use App\Models\Setting; // Import the Setting model

class SetAdminLocale
{
    /**
     * Handle an incoming request.
     *
     * @param  \Illuminate\Http\Request  $request
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     * @return \Symfony\Component\HttpFoundation\Response
     */
    public function handle(Request $request, Closure $next)
    {
        // This middleware should only apply to authenticated admin routes.
        // It checks the 'language' setting stored in the database.
        if (auth()->check() && $request->routeIs('admin.*')) {
            $languageSetting = Setting::where('key', 'language')->first();
            if ($languageSetting) {
                // Set the application locale based on the database setting
                App::setLocale($languageSetting->value);
            } else {
                // If no setting is found, fallback to the default application locale (usually 'en')
                App::setLocale(config('app.fallback_locale', 'en'));
            }
        }

        return $next($request);
    }
}
