<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ __('Generate Licenses') }}</title>
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
                <h1 class="mb-4">{{ __('Generate Licenses') }}</h1>

                @if (session('success'))
                    <div class="alert alert-success" role="alert">
                        {{ session('success') }}
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
                    <div class="card-header">
                        <h5>{{ __('Generate New License Codes') }}</h5>
                    </div>
                    <div class="card-body">
                        <form action="{{ route('admin.licenses.generate') }}" method="POST">
                            @csrf
                            <div class="mb-3">
                                <label for="count"
                                    class="form-label">{{ __('Number of Licenses to Generate') }}</label>
                                <input type="number" class="form-control" id="count" name="count" min="1"
                                    max="100" value="{{ old('count', 1) }}" required>
                            </div>
                            <div class="mb-3">
                                <label for="validity_days"
                                    class="form-label">{{ __('License Validity (Days from Activation)') }}</label>
                                <input type="number" class="form-control" id="validity_days" name="validity_days"
                                    min="1" value="{{ old('validity_days', 30) }}" required>
                                <div class="form-text">
                                    {{ __('The generated license will activate a user\'s account for this many days from the moment they use it.') }}
                                </div>
                            </div>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-magic me-2"></i> {{ __('Generate Licenses') }}
                            </button>
                        </form>
                    </div>
                </div>

                @if (session('generated_codes'))
                    <div class="card mt-4">
                        <div class="card-header">
                            <h5>{{ __('Recently Generated License Codes') }}</h5>
                            <small class="text-muted">{{ __('These licenses will be valid for') }}
                                {{ session('validity_days') }} {{ __('days from activation.') }}</small>
                        </div>
                        <div class="card-body">
                            <ul class="list-group">
                                @foreach (session('generated_codes') as $code)
                                    <li class="list-group-item d-flex justify-content-between align-items-center">
                                        <code>{{ $code }}</code>
                                        <button class="btn btn-sm btn-outline-secondary copy-btn"
                                            data-clipboard-text="{{ $code }}">
                                            <i class="fas fa-copy"></i> {{ __('Copy') }}
                                        </button>
                                    </li>
                                @endforeach
                            </ul>
                            <div class="mt-3 text-muted">
                                {{ __('Distribute these codes to your users. Each code can be used once to activate an account.') }}
                            </div>
                        </div>
                    </div>
                @endif
            </div>
        </div>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
    {{-- Include Clipboard.js for easy copying --}}
    <script src="https://cdnjs.cloudflare.com/ajax/libs/clipboard.js/2.0.11/clipboard.min.js"></script>
    <script>
        // Initialize Clipboard.js
        new ClipboardJS('.copy-btn');

        document.addEventListener('DOMContentLoaded', function() {
            const copyButtons = document.querySelectorAll('.copy-btn');
            copyButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const originalText = this.innerHTML;
                    this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    setTimeout(() => {
                        this.innerHTML = originalText;
                    }, 2000);
                });
            });
        });
    </script>
</body>

</html>
