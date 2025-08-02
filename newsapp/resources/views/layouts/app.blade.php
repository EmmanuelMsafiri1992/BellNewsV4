<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}" dir="{{ (app()->getLocale() === 'he' || app()->getLocale() === 'ar') ? 'rtl' : 'ltr' }}">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="viewport-fit=cover, width=device-width, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>{{ config('app.name', 'School News') }}</title>

    <meta name="csrf-token" content="{{ csrf_token() }}">

    {{-- Preconnect to Google Fonts for faster loading --}}
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    {{-- Using Inter font for better readability across devices, with fallbacks --}}
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

    {{-- Removed old Nunito font link to use Inter, or you can keep both if needed --}}
    {{-- <link href="https://fonts.googleapis.com/css?family=Nunito" rel="stylesheet"> --}}
</head>

{{-- Ensure body takes full height and uses Inter font --}}
<body class="bg-white font-inter antialiased min-h-screen flex flex-col">

    {{-- Blade conditional logic to decide if Vue app should load --}}
    @php
        // Define URL paths where the Vue app should NOT be mounted.
        // These are typically Blade-only pages (authentication, admin panels).
        $noVuePaths = [
            'login',
            'register',
            'password/*', // Covers all password reset routes
            'admin*', // Covers all routes under the '/admin' prefix
        ];

        $loadVueApp = true; // Assume Vue app should load by default

        foreach ($noVuePaths as $path) {
            if (request()->is($path)) {
                $loadVueApp = false;
                break;
            }
        }
    @endphp

    @if ($loadVueApp)
        {{-- This is the mount point for your Vue.js application.
             Your resources/js/app.js will mount App.vue here. --}}
        <div id="app" class="flex-1">
            {{-- App.vue will render its entire content here --}}
        </div>

        {{-- Use Vite directive - it handles dev vs production automatically --}}
        @vite(['resources/css/app.css', 'resources/js/app.js'])
    @else
        {{-- For authentication pages, and other dedicated Blade-only pages (like admin panel list/forms),
             only render the content specified in their respective Blade files.
             The <div id="app-blade-content"> is optional, but helps differentiate. --}}
        <div id="app-blade-content" class="min-h-screen flex-1">
            @yield('content')
        </div>

        {{-- Load only CSS for Blade-only pages --}}
        @vite('resources/css/app.css')
    @endif

</body>

</html>
