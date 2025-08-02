<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\License; // Import License model
use App\Models\User;    // Import User model
use Illuminate\Support\Facades\Auth; // Import Auth facade
use Carbon\Carbon;       // Import Carbon for date handling

class LicenseActivationController extends Controller
{
    /**
     * Handle the activation of a new license key for the currently authenticated user.
     *
     * @param  \Illuminate\Http\Request  $request
     * @return \Illuminate\Http\Response
     */
    public function activate(Request $request)
    {
        // Validate the incoming request for the license key
        $request->validate([
            'license_key' => ['required', 'string', 'max:255'],
        ]);

        $licenseKey = $request->input('license_key');
        $user = Auth::user(); // Get the currently authenticated user

        // If no user is authenticated, redirect them to login with an error
        if (!$user) {
            return redirect()->route('login')->with('error', __('Please log in to activate your license.'));
        }

        // Find the license in the database that matches the provided key and is not used
        $license = License::where('code', $licenseKey)
                          ->where('is_used', false)
                          ->first();

        // If no valid, unused license is found
        if (!$license) {
            return redirect()->back()->with('error', __('Invalid or already used license key. Please try again or contact support.'));
        }

        // Activate the license for the user
        try {
            // Update the license record
            $license->is_used = true;
            $license->user_id = $user->id; // Associate the license with the user
            $license->save();

            // Update the user's license details
            $user->is_active = true;
            $user->license_expires_at = $license->expires_at;
            $user->save();

            // Log the user back in to refresh their session with the new license status
            // This is important because the middleware checks the session user object.
            Auth::login($user);

            return redirect()->intended('/admin/dashboard')->with('success', __('License activated successfully! You can now access your account.'));

        } catch (\Exception $e) {
            // Handle any database errors during activation
            return redirect()->back()->with('error', __('An error occurred during license activation. Please try again.'));
        }
    }
}

