@extends('layouts.app')

@section('content')
    {{--
    |--------------------------------------------------------------------------
    | Positioning Examples for the Login Card
    |--------------------------------------------------------------------------
    |
    | This section demonstrates how to position the login card using Tailwind CSS
    | flexbox utilities. Choose one set of classes for the outer 'div'
    | (the one with 'min-h-screen', 'flex', 'justify-center', 'items-center', etc.)
    | based on where you want the login form to appear.
    |
    --}}

    {{--
    DEFAULT / CENTERED (Horizontal & Vertical)
    This is the most common and generally recommended for login forms.
    It centers the card both horizontally and vertically on the screen.
    --}}
    <div class="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-100">
        <div class="w-full max-w-md"> {{-- Max-width for responsiveness --}}
            @include('auth.login_card_content')
        </div>
    </div>

    {{--
    DISABLED EXAMPLES BELOW:
    Uncomment ONE of the blocks below to see a different positioning.
    Make sure to comment out the "DEFAULT / CENTERED" block above first.
    --}}

    {{--
    TOP-CENTERED
    Positions the card at the top, horizontally centered.
    <div class="min-h-screen flex justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-100 items-start">
        <div class="w-full max-w-md">
            @include('auth.login_card_content')
        </div>
    </div>
    --}}

    {{--
    BOTTOM-CENTERED
    Positions the card at the bottom, horizontally centered.
    <div class="min-h-screen flex justify-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-100 items-end">
        <div class="w-full max-w-md">
            @include('auth.login_card_content')
        </div>
    </div>
    --}}

    {{--
    LEFT-CENTERED (Vertical)
    Positions the card on the far left, vertically centered.
    <div class="min-h-screen flex justify-start items-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-100">
        <div class="w-full max-w-md">
            @include('auth.login_card_content')
        </div>
    </div>
    --}}

    {{--
    RIGHT-CENTERED (Vertical)
    Positions the card on the far right, vertically centered.
    <div class="min-h-screen flex justify-end items-center py-12 px-4 sm:px-6 lg:px-8 bg-gray-100">
        <div class="w-full max-w-md">
            @include('auth.login_card_content')
        </div>
    </div>
    --}}
@endsection
