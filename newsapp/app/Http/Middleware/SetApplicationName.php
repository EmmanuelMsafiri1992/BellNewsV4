<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use App\Models\Setting;
use Illuminate\Support\Facades\Config;
use Illuminate\Support\Facades\Schema;
use Illuminate\Support\Facades\Log;

class SetApplicationName
{
    public function handle(Request $request, Closure $next)
    {
        Log::info('SetApplicationName Middleware: Starting execution.'); // <--- ADD THIS LOG

        // Only attempt to load from DB if the settings table exists
        if (Schema::hasTable('settings')) {
            Log::info('SetApplicationName Middleware: Settings table exists. Attempting to fetch app_name.'); // <--- ADD THIS LOG
            try {
                $appNameSetting = Setting::where('key', 'app_name')->first();

                if ($appNameSetting) {
                    $newValue = $appNameSetting->value;
                    Config::set('app.name', $newValue);
                    Log::info('SetApplicationName Middleware: app.name set from DB to: ' . $newValue); // <--- ADD THIS LOG (SUCCESS)
                } else {
                    $fallbackValue = env('APP_NAME', 'Laravel');
                    Config::set('app.name', $fallbackValue);
                    Log::info('SetApplicationName Middleware: app_name not found in DB. Falling back to .env: ' . $fallbackValue); // <--- ADD THIS LOG (DB entry missing)
                }
            } catch (\Exception $e) {
                // Catch any database connection or query errors
                $fallbackValue = env('APP_NAME', 'Laravel');
                Config::set('app.name', $fallbackValue);
                Log::error('SetApplicationName Middleware: Error fetching app_name from DB: ' . $e->getMessage()); // <--- ADD THIS LOG (DB error)
                Log::info('SetApplicationName Middleware: Falling back to .env due to error: ' . $fallbackValue); // <--- ADD THIS LOG
            }
        } else {
            $fallbackValue = env('APP_NAME', 'Laravel');
            Config::set('app.name', $fallbackValue);
            Log::info('SetApplicationName Middleware: Settings table does NOT exist. Falling back to .env: ' . $fallbackValue); // <--- ADD THIS LOG (Table missing)
        }

        // Add a log to see the final config value right before the request continues
        Log::info('SetApplicationName Middleware: Final config(app.name) value: ' . config('app.name')); // <--- ADD THIS CRITICAL FINAL LOG

        return $next($request);
    }
}
