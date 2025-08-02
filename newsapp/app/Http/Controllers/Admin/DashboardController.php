<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\News;
use App\Models\Setting;
use App\Models\License; // Import the License model
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules\Password;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\App;
use Carbon\Carbon;
use Illuminate\Support\Facades\Log; // Ensure Log facade is imported

class DashboardController extends Controller
{
    public function index()
    {
        // Get recent news for dashboard overview, eager load images to access them in the view
        // Select slide_duration from images relationship
        $recentNews = News::with(['images' => function($query) {
                                $query->select('id', 'news_id', 'url', 'slide_duration');
                            }])
                            ->latest()
                            ->take(5)
                            ->get();
        $totalNews = News::count();

        return view('admin.dashboard', compact('recentNews', 'totalNews'));
    }
        // NEW: Method to update header settings
    public function updateHeaderSettings(Request $request)
    {
        // Ensure only superadmins can call this method (optional, depending on your requirements)
        if (!Auth::user()->isSuperAdmin()) {
            abort(403, __('Unauthorized action.'));
        }

        $request->validate([
            'header_title' => 'nullable|string|max:255',
            'header_logo_url' => 'nullable|url|max:255', // Assuming it's a URL to a logo
        ]);

        Setting::updateOrCreate(['key' => 'header_title'], ['value' => $request->input('header_title')]);
        Setting::updateOrCreate(['key' => 'header_logo_url'], ['value' => $request->input('header_logo_url')]);

        return redirect()->route('admin.settings')->with('success', __('Header settings updated successfully!'));
    }
        // NEW: Method to update global application license settings
    public function updateLicenseSettings(Request $request)
    {
        // Ensure only superadmins can call this method
        if (!Auth::user()->isSuperAdmin()) {
            abort(403, __('Unauthorized action.'));
        }

        $request->validate([
            'license_key' => 'nullable|string|max:255',
            'license_expiration_date' => 'nullable|date|after_or_equal:today',
        ]);

        // Store license_key as a key-value pair in the settings table
        Setting::updateOrCreate(['key' => 'license_key'], ['value' => $request->input('license_key')]);

        $expirationDate = $request->input('license_expiration_date');
        // Store license_expiration_date as a key-value pair in the settings table
        Setting::updateOrCreate(['key' => 'license_expiration_date'], ['value' => $expirationDate ? Carbon::parse($expirationDate)->format('Y-m-d H:i:s') : null]);

        return redirect()->route('admin.settings')->with('success', __('Application license updated successfully!'));
    }
        public function updateLanguageSettings(Request $request)
    {
        $request->validate([
            'language' => ['required', 'string', 'in:en,he,ar'], // Assuming these are your supported locales
        ]);

        Setting::updateOrCreate(['key' => 'language'], ['value' => $request->input('language')]);

        // Set the locale for the current session immediately after update
        session()->put('locale', $request->input('language'));
        app()->setLocale($request->input('language'));

        return redirect()->route('admin.settings')->with('success', __('Language updated successfully!'));
    }

    public function settings()
    {
        Log::info('Fetching all settings for display.');
        // Fetch all settings from the database as key-value pairs
        $settings = Setting::pluck('value', 'key')->toArray();
        Log::info('Settings fetched:', $settings); // Log all fetched settings

        return view('admin.settings', compact('settings'));
    }

    public function updatePassword(Request $request)
    {
        $request->validate([
            'current_password' => ['required', 'current_password'],
            'password' => ['required', 'confirmed', Password::defaults()],
        ]);

        $user = Auth::user();
        $hashedPassword = Hash::make($request->password);

        if ($user instanceof \Illuminate\Database\Eloquent\Model) {
            $user->password = $hashedPassword;
            $user->save();
        } else {
            DB::table('users')->where('id', $user->id)->update(['password' => $hashedPassword]);
        }

        return redirect()->route('admin.settings')->with('success', 'Password updated successfully!');
    }
    public function updateApplicationSettings(Request $request)
    {
        $request->validate([
            'app_name' => 'required|string|max:255',
        ]);

        Setting::updateOrCreate(['key' => 'app_name'], ['value' => $request->input('app_name')]);

        return redirect()->route('admin.settings')->with('success', __('Application settings updated successfully!'));
    }
    // New method to update license key (This is for individual user licenses, not global app license)
    public function updateLicense(Request $request)
    {
        Log::info('Attempting to update license for user ID: ' . Auth::id());
        Log::info('Request data:', $request->all());

        $request->validate([
            'is_used' => 'nullable', // Allow it to be present (e.g., "on") or not present
            'expires_at' => 'nullable|date|after_or_equal:today',
        ]);

        try {
            // Find or create a license record for this user
            $user = Auth::user(); // Get the authenticated user
            $license = $user->license()->firstOrNew(['user_id' => $user->id]);

            // Set is_used based on checkbox presence. If checkbox is not in request, it means it's unchecked.
            $license->is_used = $request->has('is_used');
            Log::info('License is_used will be set to: ' . ($license->is_used ? 'true' : 'false'));

            // Set expires_at. If input is empty, it will be null.
            $license->expires_at = $request->input('expires_at');
            // Log the parsed Carbon date if it's not null, otherwise 'null'
            Log::info('License expires_at will be set to: ' . ($license->expires_at ? Carbon::parse($license->expires_at)->format('Y-m-d H:i:s') : 'null'));


            $license->save(); // Save the license record

            Log::info('License update successful for user ID: ' . $user->id);
            return redirect()->route('admin.users.index')->with('success', 'User license updated successfully!');
        } catch (\Illuminate\Validation\ValidationException $e) {
            Log::error('Validation error updating user license: ' . $e->getMessage(), $e->errors());
            return redirect()->back()->withErrors($e->errors())->withInput();
        } catch (\Exception $e) {
            Log::error('Error updating user license: ' . $e->getMessage(), ['exception' => $e]);
            return redirect()->back()->with('error', 'Failed to update user license. Please try again.');
        }
    }
    public function updateSliderSettings(Request $request)
    {
        Log::info('Attempting to update slider settings.');
        Log::info('Slider Request data:', $request->all()); // Log incoming data

        // Ensure only Superadmins can update slider settings
        if (!Auth::user()->isSuperAdmin()) {
            abort(403, __('Unauthorized action.'));
        }

        try {
            $request->validate([
                'slider_news_count' => 'required|integer|min:1|max:10', // Example: 1 to 10 news items
                'slider_display_time' => 'required|integer|min:1|max:60', // Example: 1 to 60 seconds per slide
            ]);

            Setting::updateOrCreate(
                ['key' => 'slider_news_count'],
                ['value' => $request->input('slider_news_count')]
            );

            Setting::updateOrCreate(
                ['key' => 'slider_display_time'],
                ['value' => $request->input('slider_display_time')]
            );

            Log::info('Slider settings updated successfully.');
            // Retrieve the updated value directly after saving to confirm
            $updatedSliderDisplayTime = Setting::where('key', 'slider_display_time')->value('value');
            Log::info('Value of slider_display_time after save: ' . $updatedSliderDisplayTime);

            return redirect()->route('admin.settings')->with('success', __('Slider settings updated successfully!'));
        } catch (\Illuminate\Validation\ValidationException $e) {
            Log::error('Validation error updating slider settings: ' . $e->getMessage(), $e->errors());
            return redirect()->back()->withErrors($e->errors())->withInput();
        } catch (\Exception $e) {
            Log::error('Error updating slider settings: ' . $e->getMessage(), ['exception' => $e]);
            return redirect()->back()->with('error', 'Failed to update slider settings. Please try again.');
        }
    }
        public function getSliderSettings()
    {
        $sliderNewsCount = Setting::where('key', 'slider_news_count')->value('value');
        $sliderDisplayTime = Setting::where('key', 'slider_display_time')->value('value');

        // Provide default values if settings are not found
        $sliderNewsCount = $sliderNewsCount !== null ? (int)$sliderNewsCount : 5;
        $sliderDisplayTime = $sliderDisplayTime !== null ? (int)$sliderDisplayTime : 5;

        return response()->json([
            'slider_news_count' => $sliderNewsCount,
            'slider_display_time' => $sliderDisplayTime,
        ]);
    }
    // NEW: Method to update footer settings
    public function updateFooterSettings(Request $request)
    {
        $request->validate([
            'footer_copyright_text' => 'nullable|string|max:1000',
            'footer_contact_info' => 'nullable|string|max:1000',
        ]);

        Setting::updateOrCreate(
            ['key' => 'footer_copyright_text'],
            ['value' => $request->footer_copyright_text]
        );

        Setting::updateOrCreate(
            ['key' => 'footer_contact_info'],
            ['value' => $request->footer_contact_info]
        );

        return redirect()->route('admin.settings')->with('success', __('Footer settings updated successfully!'));
    }
}
