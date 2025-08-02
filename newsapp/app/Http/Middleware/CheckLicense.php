<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use App\Models\Setting; // Import the Setting model
use Carbon\Carbon; // Import Carbon for date handling
use App\Models\User; // Import User model

class CheckLicense
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
        // Only apply this check to authenticated users trying to access admin routes
        // and not when they are already on the license expired page.
        if (Auth::check() && $request->routeIs('admin.*') && !$request->routeIs('license.expired')) {
            $user = Auth::user();

            // If the user is a superadmin, bypass all license checks and proceed.
            if ($user->isSuperAdmin()) {
                return $next($request);
            }

            // For all other authenticated users (non-superadmins) accessing admin routes,
            // perform the global application license check first.
            $licenseKeySetting = Setting::where('key', 'license_key')->first();
            $expirationDateSetting = Setting::where('key', 'license_expiration_date')->first();

            $licenseKey = $licenseKeySetting ? $licenseKeySetting->value : null;
            $expirationDate = $expirationDateSetting ? Carbon::parse($expirationDateSetting->value) : null;

            $isLicensed = !empty($licenseKey);
            $isExpired = $expirationDate && $expirationDate->isPast();

            // If no global license key is set OR global license is expired
            if (!$isLicensed || $isExpired) {
                session()->flash('error', __('Your application license is invalid or has expired. Please renew your license to continue.'));
                // Keep the user authenticated so they can activate their personal license if needed.
                return redirect()->route('license.expired');
            }

            // After the global license check, check the individual user's license status.
            // This block will only be reached by non-superadmins if the global license is valid.
            if (!$user->hasActiveLicense()) {
                session()->flash('error', __('Your license is invalid or has expired. Please activate a new license.'));
                // Keep the user authenticated so they can activate their license.
                return redirect()->route('license.expired');
            }
        }

        return $next($request);
    }
}

