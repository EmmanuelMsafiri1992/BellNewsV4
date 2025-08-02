<div class="text-center">
    <h1 class="text-3xl font-bold text-gray-900">{{ __('Login') }}</h1>
</div>

<form method="POST" action="{{ route('login') }}" class="space-y-6">
    @csrf

    <!-- Email Input -->
    <div>
        <label for="email" class="block text-sm font-medium text-gray-700">{{ __('Email Address') }}</label>
        <div class="mt-1 relative">
            <div
                class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none {{ app()->getLocale() === 'ar' || app()->getLocale() === 'he' ? 'right-0 left-auto pr-3' : '' }}">
                <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                </svg>
            </div>
            <input id="email" type="email" name="email" value="{{ old('email') }}" required autofocus
                aria-label="{{ __('Email Address') }}"
                class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150 ease-in-out {{ app()->getLocale() === 'ar' || app()->getLocale() === 'he' ? 'rtl' : 'ltr' }}"
                placeholder="{{ __('Email Address') }}">
        </div>
        @error('email')
            <span class="mt-2 text-sm text-red-600" role="alert">{{ $message }}</span>
        @enderror
    </div>

    <!-- Password Input -->
    <div>
        <label for="password" class="block text-sm font-medium text-gray-700">{{ __('Password') }}</label>
        <div class="mt-1 relative">
            <div
                class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none {{ app()->getLocale() === 'ar' || app()->getLocale() === 'he' ? 'right-0 left-auto pr-3' : '' }}">
                <svg class="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    aria-hidden="true">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M12 11c0-1.1-.9-2-2-2s-2 .9-2 2 2 4 2 4m0 0c0 1.1.9 2 2 2s2-.9 2-2-2-4-2-4zm0 0h6m-6 0H6" />
                </svg>
            </div>
            <input id="password" type="password" name="password" required aria-label="{{ __('Password') }}"
                class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition duration-150 ease-in-out {{ app()->getLocale() === 'ar' || app()->getLocale() === 'he' ? 'rtl' : 'ltr' }}"
                placeholder="{{ __('Password') }}">
        </div>
        @error('password')
            <span class="mt-2 text-sm text-red-600" role="alert">{{ $message }}</span>
        @enderror
    </div>

    <!-- Remember Me Checkbox -->
    <div class="flex items-center justify-between">
        <div class="flex items-center">
            <input id="remember" type="checkbox" name="remember"
                class="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                aria-label="{{ __('Remember Me') }}">
            <label for="remember" class="ml-2 block text-sm text-gray-900">{{ __('Remember Me') }}</label>
        </div>
    </div>

    <!-- Submit Button -->
    <div>
        <button type="submit"
            class="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition duration-150 ease-in-out">
            {{ __('Login') }}
        </button>
    </div>
{{--
    <!-- Forgot Password Link -->
    @if (Route::has('password.request'))
        <div class="text-center">
            <a href="{{ route('password.request') }}"
                class="text-sm text-blue-600 hover:text-blue-800 transition duration-150 ease-in-out">
                {{ __('Forgot Your Password?') }}
            </a>
        </div>
    @endif --}}
</form>
