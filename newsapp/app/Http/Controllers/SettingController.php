<?php

namespace App\Http\Controllers;

use App\Models\Setting;
use Illuminate\Http\Request;

class SettingController extends Controller
{
    /**
     * Display a listing of the settings for the API.
     *
     * @return \Illuminate\Http\Response
     */
    public function index()
    {
        // Fetch specific settings that the frontend needs
        $settings = Setting::whereIn('key', [
            'header_title',
            'footer_copyright_text',
            'footer_contact_info',
            // **FIXED**: Add slider settings to the API response
            'slider_display_time',
            'slider_news_count'
        ])->pluck('value', 'key')->toArray();

        // **FIXED**: Provide default values if settings are not in the database
        $defaults = [
            'slider_display_time' => 5, // Default to 5 seconds
            'slider_news_count' => 5,   // Default to 5 articles
        ];

        // Merge the settings from the database with the defaults.
        // The values from the database will overwrite the defaults if they exist.
        $settings = array_merge($defaults, $settings);


        return response()->json($settings);
    }
}
