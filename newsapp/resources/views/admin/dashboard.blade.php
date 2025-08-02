<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ __('Admin Dashboard') }}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
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

        .stat-card {
            background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
            color: white;
        }

        .stat-card .card-body {
            padding: 30px;
        }

        .stat-number {
            font-size: 3rem;
            font-weight: bold;
        }

        .news-card {
            background: white;
            border-left: 4px solid #667eea;
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

        .btn-danger {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            border: none;
            border-radius: 25px;
            padding: 8px 20px;
        }

        .btn-warning {
            background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
            border: none;
            border-radius: 25px;
            padding: 8px 20px;
        }

        .navbar-brand {
            font-weight: bold;
            font-size: 1.5rem;
        }

        .welcome-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
        }

        /* --- START: New CSS for Carousel (Minimal, essential for functionality) --- */
        .news-slider-card .carousel-item img {
            height: 400px;
            /* Fixed height for consistency */
            object-fit: cover;
            /* Cover the area, cropping if necessary */
            width: 100%;
            border-radius: 15px;
            /* Match card border-radius */
        }

        .news-slider-card .carousel-caption {
            background-color: rgba(0, 0, 0, 0.6);
            /* Slightly darker overlay for readability */
            padding: 15px;
            border-radius: 8px;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            width: 90%;
            max-width: 600px;
            /* Limit width of caption */
        }

        /* --- END: New CSS for Carousel --- */
    </style>
</head>

<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-2 p-0">
                <div class="sidebar p-3">
                    <div class="text-center mb-4">
                        <h4><i class="fas fa-tachometer-alt"></i> {{ __('Admin Panel') }}</h4>
                    </div>
                    <nav class="nav flex-column">
                        <a class="nav-link active" href="{{ route('admin.dashboard') }}">
                            <i class="fas fa-home me-2"></i> {{ __('Dashboard') }}
                        </a>
                        <a class="nav-link" href="{{ route('admin.news.index') }}">
                            <i class="fas fa-newspaper me-2"></i> {{ __('All News') }}
                        </a>
                        <a class="nav-link" href="{{ route('admin.settings') }}">
                            <i class="fas fa-cog me-2"></i> {{ __('Settings') }}
                        </a>
                        <hr class="my-3">
                        <a class="nav-link" href="#"
                            onclick="event.preventDefault(); document.getElementById('logout-form').submit();">
                            <i class="fas fa-sign-out-alt me-2"></i> {{ __('Logout') }}
                        </a>
                        <form id="logout-form" action="{{ route('logout') }}" method="POST" style="display: none;">
                            @csrf
                        </form>
                    </nav>
                </div>
            </div>

            <div class="col-md-10 main-content p-4">
                <div class="welcome-section">
                    <div class="row align-items-center">
                        <div class="col-md-8">
                            <h1><i class="fas fa-user-shield"></i>
                                {{ __('Welcome, :name!', ['name' => Auth::user()->name]) }}</h1>
                            <p class="mb-0">{{ __('Manage your news content from this dashboard') }}</p>
                        </div>
                        <div class="col-md-4 text-end">
                            <div class="text-white-50">
                                <i class="fas fa-calendar-alt"></i> {{ date('F j, Y') }}
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row mb-4">
                    <div class="col-md-4">
                        <div class="card stat-card">
                            <div class="card-body text-center">
                                <div class="stat-number">{{ $totalNews }}</div>
                                <div class="h5">{{ __('Total News') }}</div>
                                <i class="fas fa-newspaper fa-2x opacity-50"></i>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card"
                            style="background: linear-gradient(135deg, #48cae4 0%, #0077b6 100%); color: white;">
                            <div class="card-body text-center">
                                <div class="stat-number">{{ $recentNews->count() }}</div>
                                <div class="h5">{{ __('Recent News') }}</div>
                                <i class="fas fa-clock fa-2x opacity-50"></i>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card"
                            style="background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); color: white;">
                            <div class="card-body text-center">
                                <div class="stat-number">{{ date('H') }}</div>
                                <div class="h5">{{ __('Current Hour') }}</div>
                                <i class="fas fa-clock fa-2x opacity-50"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row mb-4">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header bg-transparent">
                                <h5 class="mb-0"><i class="fas fa-bolt"></i> {{ __('Quick Actions') }}</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-4 mb-3">
                                        <a href="{{ route('admin.news.create') }}" class="btn btn-primary w-100">
                                            <i class="fas fa-plus-circle me-2"></i> {{ __('Create New News') }}
                                        </a>
                                    </div>
                                    <div class="col-md-4 mb-3">
                                        <a href="{{ route('admin.news.index') }}" class="btn btn-info w-100">
                                            <i class="fas fa-list me-2"></i> {{ __('View All News') }}
                                        </a>
                                    </div>
                                    <div class="col-md-4 mb-3">
                                        <a href="{{ route('admin.settings') }}" class="btn btn-warning w-100">
                                            <i class="fas fa-cog me-2"></i> {{ __('Settings') }}
                                        </a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header bg-transparent d-flex justify-content-between align-items-center">
                                <h5 class="mb-0"><i class="fas fa-newspaper"></i> {{ __('Recent News Articles') }}
                                </h5>
                                <a href="{{ route('admin.news.index') }}"
                                    class="btn btn-sm btn-outline-primary">{{ __('View All') }}</a>
                            </div>
                            <div class="card-body">
                                @if ($recentNews->count() > 0)
                                    <div class="row">
                                        @foreach ($recentNews as $news)
                                            <div class="col-md-6 mb-3">
                                                <div class="card news-card h-100">
                                                    <div class="card-body">
                                                        {{-- FIX: Decode HTML entities before limiting and rendering --}}
                                                        <h6 class="card-title">{!! Str::limit(html_entity_decode($news->title), 50) !!}</h6>
                                                        <p class="card-text text-muted small">
                                                            {!! Str::limit(html_entity_decode($news->description), 100) !!}</p>
                                                        <div class="d-flex justify-content-between align-items-center">
                                                            <small class="text-muted">
                                                                <i class="fas fa-clock"></i>
                                                                {{ $news->created_at->diffForHumans() }}
                                                            </small>
                                                            <div>
                                                                <a href="{{ route('admin.news.edit', $news) }}"
                                                                    class="btn btn-sm btn-warning">
                                                                    <i class="fas fa-edit"></i>
                                                                </a>
                                                                <form method="POST"
                                                                    action="{{ route('admin.news.destroy', $news) }}"
                                                                    class="d-inline">
                                                                    @csrf
                                                                    @method('DELETE')
                                                                    <button type="submit"
                                                                        class="btn btn-sm btn-danger"
                                                                        onclick="return confirm('{{ __('Are you sure?') }}')">
                                                                        <i class="fas fa-trash"></i>
                                                                    </button>
                                                                </form>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        @endforeach
                                    </div>
                                @else
                                    <div class="text-center py-5">
                                        <i class="fas fa-newspaper fa-3x text-muted mb-3"></i>
                                        <h5 class="text-muted">{{ __('No news articles yet') }}</h5>
                                        <p class="text-muted">{{ __('Start by creating your first news article') }}
                                        </p>
                                        <a href="{{ route('admin.news.create') }}" class="btn btn-primary">
                                            <i class="fas fa-plus-circle me-2"></i> {{ __('Create First News') }}
                                        </a>
                                    </div>
                                @endif
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
</body>

</html>
