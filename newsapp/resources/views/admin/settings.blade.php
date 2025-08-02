<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {{-- <title>{{ __('Admin Settings') }}</title> --}}
    <title>{{ config('app.name') }} - {{ __('Admin Settings') }}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        /* Sidebar styles remain the same */
        .sidebar {
            min-height: 100vh;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .sidebar .nav-link {
            color: rgba(255, 255, 255, 0.8);
            padding: 15px 20px;
            border-radius: 8px;
            margin: 5px 0;
            transition: all 0.3s ease;
        }

        .sidebar .nav-link:hover {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            transform: translateX(5px);
        }

        .sidebar .nav-link.active {
            background: rgba(255, 255, 255, 0.2);
            color: white;
        }

        /* Main content and card styles remain the same */
        .main-content {
            background-color: #f8f9fa;
            min-height: 100vh;
        }

        .card {
            border: none;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 25px;
            padding: 12px 30px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .navbar-brand {
            font-weight: bold;
            font-size: 1.5rem;
        }

        /* Styles for tabs */
        .nav-tabs .nav-link {
            color: #495057;
            border: 1px solid transparent;
            border-top-left-radius: .25rem;
            border-top-right-radius: .25rem;
            margin-bottom: -1px;
            background-color: #e9ecef;
            border-color: #dee2e6 #dee2e6 #f8f9fa;
        }

        .nav-tabs .nav-link.active {
            color: #495057;
            background-color: #fff;
            border-color: #dee2e6 #dee2e6 #fff;
        }

        .tab-content {
            padding-top: 20px;
        }
    </style>
</head>

<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-2 p-0">
                @include('admin.sidebar')
            </div>

            <div class="col-md-10 main-content p-4">
                <h1 class="mb-4"><i class="fas fa-cog"></i> {{ __('Settings') }}</h1>

                @if (session('success'))
                    <div class="alert alert-success alert-dismissible fade show" role="alert">
                        {{ session('success') }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                @endif

                @if (session('error'))
                    <div class="alert alert-danger alert-dismissible fade show" role="alert">
                        {{ session('error') }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                    </div>
                @endif

                <ul class="nav nav-tabs mb-4" id="settingsTab" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="general-tab" data-bs-toggle="tab" data-bs-target="#general"
                            type="button" role="tab" aria-controls="general"
                            aria-selected="true">{{ __('General') }}</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="account-tab" data-bs-toggle="tab" data-bs-target="#account"
                            type="button" role="tab" aria-controls="account"
                            aria-selected="false">{{ __('Account') }}</button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="display-tab" data-bs-toggle="tab" data-bs-target="#display"
                            type="button" role="tab" aria-controls="display"
                            aria-selected="false">{{ __('Display') }}</button>
                    </li>
                    {{-- Removed Localization Tab --}}
                    {{--
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="localization-tab" data-bs-toggle="tab"
                            data-bs-target="#localization" type="button" role="tab" aria-controls="localization"
                            aria-selected="false">{{ __('Localization') }}</button>
                    </li>
                    --}}
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="admin-tab" data-bs-toggle="tab" data-bs-target="#admin"
                            type="button" role="tab" aria-controls="admin"
                            aria-selected="false">{{ __('Admin') }}</button>
                    </li>
                </ul>

                <div class="tab-content" id="settingsTabContent">
                    {{-- General Settings Tab --}}
                    <div class="tab-pane fade show active" id="general" role="tabpanel" aria-labelledby="general-tab">
                        <div class="row">
                            <div class="col-md-6 mb-4">
                                <div class="card p-3">
                                    <h5 class="mb-3">{{ __('Application Settings') }}</h5>
                                    <form action="{{ route('admin.settings.application') }}" method="POST">
                                        @csrf
                                        <div class="mb-3">
                                            <label for="app_name"
                                                class="form-label">{{ __('Application Name') }}</label>
                                            <input type="text" class="form-control" id="app_name" name="app_name"
                                                value="{{ $settings['app_name'] ?? config('app.name') }}" required>
                                            @error('app_name')
                                                <div class="text-danger mt-2">{{ $message }}</div>
                                            @enderror
                                        </div>
                                        <button type="submit"
                                            class="btn btn-primary">{{ __('Update Settings') }}</button>
                                    </form>
                                </div>
                            </div>

                            <div class="col-md-6 mb-4">
                                <div class="card p-3">
                                    <h5 class="mb-3">{{ __('Header Settings') }}</h5>
                                    <form action="{{ route('admin.settings.header') }}" method="POST">
                                        @csrf
                                        <div class="mb-3">
                                            <label for="header_title"
                                                class="form-label">{{ __('Header Title') }}</label>
                                            <input type="text" class="form-control" id="header_title"
                                                name="header_title" value="{{ $settings['header_title'] ?? '' }}"
                                                required>
                                            @error('header_title')
                                                <div class="text-danger mt-2">{{ $message }}</div>
                                            @enderror
                                        </div>
                                        <button type="submit"
                                            class="btn btn-primary">{{ __('Update Header Settings') }}</button>
                                    </form>
                                </div>
                            </div>

                            {{-- Footer Settings: Only visible to SuperAdmins --}}
                            @if (Auth::user()->isSuperAdmin())
                                <div class="col-md-6 mb-4">
                                    <div class="card p-3">
                                        <h5 class="mb-3">{{ __('Footer Settings') }}</h5>
                                        <form action="{{ route('admin.settings.footer') }}" method="POST">
                                            @csrf
                                            <div class="mb-3">
                                                <label for="footer_copyright_text"
                                                    class="form-label">{{ __('Footer Copyright Text') }}</label>
                                                <input type="text" class="form-control" id="footer_copyright_text"
                                                    name="footer_copyright_text"
                                                    value="{{ $settings['footer_copyright_text'] ?? '' }}">
                                            </div>
                                            <div class="mb-3">
                                                <label for="footer_contact_info"
                                                    class="form-label">{{ __('Footer Contact Info') }}</label>
                                                <textarea class="form-control" id="footer_contact_info" name="footer_contact_info" rows="3">{{ $settings['footer_contact_info'] ?? '' }}</textarea>
                                            </div>
                                            <button type="submit"
                                                class="btn btn-primary">{{ __('Update Footer Settings') }}</button>
                                        </form>
                                    </div>
                                </div>
                            @endif
                        </div>
                    </div>

                    {{-- Account Settings Tab --}}
                    <div class="tab-pane fade" id="account" role="tabpanel" aria-labelledby="account-tab">
                        <div class="row">
                            <div class="col-md-6 mb-4">
                                <div class="card p-3">
                                    <h5 class="mb-3">{{ __('Change Password') }}</h5>
                                    <form action="{{ route('admin.settings.password') }}" method="POST">
                                        @csrf
                                        <div class="mb-3">
                                            <label for="current_password"
                                                class="form-label">{{ __('Current Password') }}</label>
                                            <input type="password" class="form-control" id="current_password"
                                                name="current_password" required>
                                            @error('current_password')
                                                <div class="text-danger mt-2">{{ $message }}</div>
                                            @enderror
                                        </div>
                                        <div class="mb-3">
                                            <label for="password" class="form-label">{{ __('New Password') }}</label>
                                            <input type="password" class="form-control" id="password"
                                                name="password" required>
                                            @error('password')
                                                <div class="text-danger mt-2">{{ $message }}</div>
                                            @enderror
                                        </div>
                                        <div class="mb-3">
                                            <label for="password_confirmation"
                                                class="form-label">{{ __('Confirm New Password') }}</label>
                                            <input type="password" class="form-control" id="password_confirmation"
                                                name="password_confirmation" required>
                                        </div>
                                        <button type="submit"
                                            class="btn btn-primary">{{ __('Update Password') }}</button>
                                    </form>
                                </div>
                            </div>

                            {{-- License Status for Regular Users --}}
                            @if (!Auth::user()->isSuperAdmin())
                                <div class="col-md-6 mb-4">
                                    <div class="card p-3">
                                        <h5 class="mb-3">{{ __('Your License Status') }}</h5>
                                        @php
                                            $user = Auth::user();
                                            // Ensure the license relationship is loaded for the current user
                                            $user->loadMissing('license'); // Load if not already loaded

                                            $userLicense = $user->license; // Get the related license object

                                            $status = 'Inactive';
                                            $remainingDays = 'N/A';
                                            $statusClass = 'bg-secondary';
                                            $expiresOn = 'N/A';

                                            if ($userLicense && $userLicense->is_used && $userLicense->expires_at) {
                                                if ($userLicense->expires_at->isFuture()) {
                                                    $status = 'Active';
                                                    $statusClass = 'bg-success';
                                                    $remainingDays = $userLicense->expires_at->diffInDays(now(), true);
                                                    if ($remainingDays < 1) {
                                                        $remainingDays = '< 1';
                                                    } else {
                                                        $remainingDays = ceil($remainingDays);
                                                    }
                                                    $expiresOn = $userLicense->expires_at->format('M d, Y');
                                                } else {
                                                    $status = 'Expired';
                                                    $statusClass = 'bg-danger';
                                                    $remainingDays = '0';
                                                    $expiresOn = $userLicense->expires_at->format('M d, Y');
                                                }
                                            }
                                        @endphp

                                        <p><strong>{{ __('Status') }}:</strong> <span
                                                class="badge {{ $statusClass }}">{{ __($status) }}</span></p>

                                        @if ($expiresOn !== 'N/A')
                                            <p><strong>{{ __('Expires On') }}:</strong> {{ $expiresOn }}</p>
                                            <p><strong>{{ __('Days Remaining') }}:</strong> {{ $remainingDays }}
                                                {{ __('days') }}</p>
                                        @else
                                            <p>{{ __('No active license found for your account.') }}</p>
                                        @endif

                                        {{-- Prompt to activate new license if expired/inactive --}}
                                        @if (
                                            !$userLicense ||
                                                !$userLicense->is_used ||
                                                ($userLicense && $userLicense->expires_at && $userLicense->expires_at->isPast()))
                                            <div class="alert alert-info mt-3" role="alert">
                                                {{ __('Your license is not active or has expired. Please activate a new license key.') }}
                                            </div>
                                            <a href="{{ route('license.expired') }}" class="btn btn-primary w-100">
                                                {{ __('Activate New License') }}
                                            </a>
                                        @endif
                                    </div>
                                </div>
                            @endif
                        </div>
                    </div>

                    {{-- Display Settings Tab --}}
                    <div class="tab-pane fade" id="display" role="tabpanel" aria-labelledby="display-tab">
                        <div class="row">
                            <div class="col-md-6 mb-4">
                                <div class="card p-3">
                                    <h5 class="mb-3">{{ __('Slider Settings') }}</h5>
                                    <form action="{{ route('admin.settings.slider') }}" method="POST">
                                        @csrf
                                        {{-- NEW: Input for slider_news_count --}}
                                        <div class="mb-3">
                                            <label for="slider_news_count"
                                                class="form-label">{{ __('Number of News Articles in Slider') }}</label>
                                            <input type="number" name="slider_news_count" id="slider_news_count"
                                                class="form-control"
                                                value="{{ $settings['slider_news_count'] ?? 5 }}" min="1"
                                                max="10" required>
                                            @error('slider_news_count')
                                                <div class="text-danger mt-2">{{ $message }}</div>
                                            @enderror
                                            <div class="form-text text-muted">
                                                {{ __('The maximum number of news articles to display in the slider.') }}
                                            </div>
                                        </div>

                                        <div class="mb-3">
                                            <label for="slider_display_time"
                                                class="form-label">{{ __('Slide Duration (seconds)') }}</label>
                                            <input type="number" name="slider_display_time" id="slider_display_time"
                                                class="form-control"
                                                value="{{ $settings['slider_display_time'] ?? 5 }}" min="1"
                                                max="60" required>
                                            @error('slider_display_time')
                                                <div class="text-danger mt-2">{{ $message }}</div>
                                            @enderror
                                            <div class="form-text text-muted">
                                                {{ __('The number of seconds each image will display in the news slider.') }}
                                            </div>
                                        </div>
                                        <button type="submit"
                                            class="btn btn-primary">{{ __('Save Slider Settings') }}</button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>

                    {{-- Removed Localization Tab --}}
                    {{--
                    <div class="tab-pane fade" id="localization" role="tabpanel" aria-labelledby="localization-tab">
                        <div class="row">
                            <div class="col-md-6 mb-4">
                                <div class="card p-3">
                                    <h5 class="mb-3">{{ __('Language Settings') }}</h5>
                                    <form action="{{ route('admin.settings.language') }}" method="POST">
                                        @csrf
                                        <div class="mb-3">
                                            <label for="language" class="form-label">{{ __('Language') }}</label>
                                            <select class="form-select" id="language" name="language">
                                                <option value="en"
                                                    {{ session('locale', config('app.locale')) == 'en' ? 'selected' : '' }}>
                                                    {{ __('English') }}</option>
                                                <option value="he"
                                                    {{ session('locale', config('app.locale')) == 'he' ? 'selected' : '' }}>
                                                    {{ __('Hebrew') }}</option>
                                                <option value="ar"
                                                    {{ session('locale', config('app.locale')) == 'ar' ? 'selected' : '' }}>
                                                    {{ __('Arabic') }}</option>
                                            </select>
                                            @error('language')
                                                <div class="text-danger mt-2">{{ $message }}</div>
                                            @enderror
                                        </div>
                                        <button type="submit"
                                            class="btn btn-primary">{{ __('Update Settings') }}</button>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                    --}}

                    {{-- Admin Settings Tab --}}
                    <div class="tab-pane fade" id="admin" role="tabpanel" aria-labelledby="admin-tab">
                        <div class="row">
                            @if (Auth::user()->isSuperAdmin())
                                <div class="col-md-6 mb-4">
                                    <div class="card p-3">
                                        <h5 class="mb-3">{{ __('License Management') }}</h5>
                                        <p><strong>{{ __('Current License Status') }}:</strong>
                                            @php
                                                // Retrieve from settings table using key/value pairs
                                                $licenseKey = $settings['license_key'] ?? null;
                                                $expirationDate = $settings['license_expiration_date'] ?? null;
                                                $isExpired = false;
                                                if ($expirationDate) {
                                                    try {
                                                        $expirationCarbon = \Carbon\Carbon::parse($expirationDate);
                                                        $isExpired = $expirationCarbon->isPast();
                                                    } catch (\Exception $e) {
                                                        $expirationDate = null; // Invalid date format
                                                    }
                                                }
                                            @endphp

                                            @if ($licenseKey && $expirationDate && !$isExpired)
                                                <span class="badge bg-success">{{ __('Active') }}</span>
                                            @elseif ($licenseKey && $expirationDate && $isExpired)
                                                <span class="badge bg-danger">{{ __('Expired') }}</span>
                                            @else
                                                <span class="badge bg-secondary">{{ __('Inactive/Invalid') }}</span>
                                            @endif
                                        </p>
                                        @if ($licenseKey)
                                            <p><strong>{{ __('License Key') }}:</strong>
                                                <code>{{ $licenseKey }}</code>
                                            </p>
                                        @endif
                                        @if ($expirationDate)
                                            <p><strong>{{ __('Expiration Date') }}:</strong>
                                                {{ \Carbon\Carbon::parse($expirationDate)->format('M d, Y') }}
                                                @if ($isExpired)
                                                    <span class="text-danger"> ({{ __('Expired on') }}
                                                        {{ \Carbon\Carbon::parse($expirationDate)->format('M d, Y') }})</span>
                                                @endif
                                            </p>
                                        @endif

                                        <form action="{{ route('admin.settings.license') }}" method="POST">
                                            @csrf
                                            <div class="mb-3">
                                                <label for="license_key"
                                                    class="form-label">{{ __('License Key') }}</label>
                                                <input type="text" class="form-control" id="license_key"
                                                    name="license_key" value="{{ $settings['license_key'] ?? '' }}">
                                                @error('license_key')
                                                    <div class="text-danger mt-2">{{ $message }}</div>
                                                @enderror
                                            </div>
                                            <div class="mb-3">
                                                <label for="license_expiration_date"
                                                    class="form-label">{{ __('Expiration Date') }}</label>
                                                <input type="date" class="form-control"
                                                    id="license_expiration_date" name="license_expiration_date"
                                                    value="{{ isset($settings['license_expiration_date']) ? \Carbon\Carbon::parse($settings['license_expiration_date'])->format('Y-m-d') : '' }}">
                                                @error('license_expiration_date')
                                                    <div class="text-danger mt-2">{{ $message }}</div>
                                                @enderror
                                                {{-- Debugging line for date input --}}
                                                <small class="form-text text-muted">Value sent: <span
                                                        id="debug_license_expiration_date"></span></small>
                                            </div>
                                            <button type="submit"
                                                class="btn btn-primary">{{ __('Update License') }}</button>
                                        </form>

                                        <hr class="my-3">

                                        {{-- NEW: Link to Generate User Licenses page from Settings --}}
                                        <a href="{{ route('admin.licenses.generate.form') }}"
                                            class="btn btn-outline-primary mt-2 w-100">
                                            <i class="fas fa-plus-circle me-2"></i> {{ __('Generate New Licenses') }}
                                            for
                                            Users
                                        </a>
                                    </div>
                                </div>
                            @endif

                            <div class="col-md-6 mb-4">
                                <div class="card p-3">
                                    <h5 class="mb-3">{{ __('Quick Stats') }}</h5>
                                    <div class="card-body">
                                        <div class="d-flex justify-content-between align-items-center mb-2">
                                            <span>{{ __('Total News Articles') }}</span>
                                            <span class="badge bg-primary">{{ App\Models\News::count() }}</span>
                                        </div>
                                        <div class="d-flex justify-content-between align-items-center mb-2">
                                            <span>{{ __('Published Today') }}</span>
                                            <span
                                                class="badge bg-success">{{ App\Models\News::whereDate('created_at', today())->count() }}</span>
                                        </div>
                                        <div class="d-flex justify-content-between align-items-center">
                                            <span>{{ __('This Week') }}</span>
                                            <span
                                                class="badge bg-info">{{ App\Models\News::whereBetween('created_at', [\Carbon\Carbon::now()->startOfWeek(), \Carbon\Carbon::now()->endOfWeek()])->count() }}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    <script>
        // Debugging script for license_expiration_date
        document.addEventListener('DOMContentLoaded', function() {
            const dateInput = document.getElementById('license_expiration_date');
            const debugSpan = document.getElementById('debug_license_expiration_date');

            if (dateInput && debugSpan) {
                // Update on initial load
                debugSpan.textContent = dateInput.value;

                // Update on input change
                dateInput.addEventListener('change', function() {
                    debugSpan.textContent = this.value;
                });
            }
        });
    </script>
</body>

</html>
