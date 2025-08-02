<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ __('Manage Licenses') }}</title>
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

        .content {
            padding: 20px;
        }
    </style>
</head>

<body>
    <div class="d-flex">
        @include('admin.sidebar') {{-- Assuming you have a sidebar partial --}}

        <div class="content flex-grow-1 p-4">
            <div class="container">
                <h1 class="mb-4">{{ __('Manage Licenses') }}</h1>

                @if (session('success'))
                    <div class="alert alert-success" role="alert">
                        {{ session('success') }}
                    </div>
                @endif

                @if (session('error')) {{-- Added to display error messages --}}
                    <div class="alert alert-danger" role="alert">
                        {{ session('error') }}
                    </div>
                @endif

                @if ($errors->any())
                    <div class="alert alert-danger">
                        <ul>
                            @foreach ($errors->all() as $error)
                                <li>{{ $error }}</li>
                            @endforeach
                        </ul>
                    </div>
                @endif

                <div class="card mb-4">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5>{{ __('All Licenses') }}</h5>
                        <a href="{{ route('admin.licenses.generate.form') }}" class="btn btn-sm btn-primary">
                            <i class="fas fa-plus-circle me-2"></i> {{ __('Generate New Licenses') }}
                        </a>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead>
                                    <tr>
                                        <th>{{ __('License Code') }}</th>
                                        <th>{{ __('Used By') }}</th>
                                        <th>{{ __('Is Used?') }}</th>
                                        <th>{{ __('Generated At') }}</th>
                                        <th>{{ __('Last Updated') }}</th>
                                        <th>{{ __('Actions') }}</th> {{-- NEW: Actions header --}}
                                    </tr>
                                </thead>
                                <tbody>
                                    @forelse ($licenses as $license)
                                        <tr>
                                            <td><code>{{ $license->code }}</code></td>
                                            <td>
                                                @if ($license->user)
                                                    {{ $license->user->name }} ({{ $license->user->email }})
                                                @else
                                                    <span class="text-muted">{{ __('Not used yet') }}</span>
                                                @endif
                                            </td>
                                            <td>
                                                @if ($license->is_used)
                                                    <span class="badge bg-success">{{ __('Yes') }}</span>
                                                @else
                                                    <span class="badge bg-secondary">{{ __('No') }}</span>
                                                @endif
                                            </td>
                                            <td>{{ $license->created_at->format('Y-m-d H:i') }}</td>
                                            <td>{{ $license->updated_at->format('Y-m-d H:i') }}</td>
                                            <td>
                                                {{-- NEW: Delete button form --}}
                                                <form action="{{ route('admin.licenses.destroy', $license->id) }}" method="POST" onsubmit="return confirm('Are you sure you want to delete this license? This action cannot be undone.');">
                                                    @csrf
                                                    @method('DELETE')
                                                    <button type="submit" class="btn btn-danger btn-sm">
                                                        <i class="fas fa-trash"></i> {{ __('Delete') }}
                                                    </button>
                                                </form>
                                            </td>
                                        </tr>
                                    @empty
                                        <tr>
                                            <td colspan="6" class="text-center">{{ __('No licenses found.') }}</td> {{-- colspan updated --}}
                                        </tr>
                                    @endforelse
                                </tbody>
                            </table>
                        </div>
                        <div class="d-flex justify-content-center">
                            {{ $licenses->links() }}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
</body>

</html>
