<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ __('License Expired') }}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            text-align: center;
        }

        .card {
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
            padding: 40px;
            max-width: 500px;
            width: 90%;
            color: #333;
        }

        .card h1 {
            color: #dc3545;
            /* Red for warning */
            margin-bottom: 20px;
        }

        .card .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 25px;
            padding: 10px 25px;
            font-weight: 600;
            transition: all 0.3s ease;
        }

        .card .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
    </style>
</head>

<body>
    <div class="card">
        <h1><i class="fas fa-exclamation-triangle"></i> {{ __('License Required!') }}</h1>
        <p class="lead">{{ __('Your license is either missing or has expired.') }}</p>
        <p>{{ __('Please enter a new license key to activate your account.') }}</p>

        @if (session('error'))
            <div class="alert alert-danger mt-3" role="alert">
                {{ session('error') }}
            </div>
        @endif

        @if (session('success'))
            <div class="alert alert-success mt-3" role="alert">
                {{ session('success') }}
            </div>
        @endif

        <form action="{{ route('license.activate') }}" method="POST" class="mt-4">
            @csrf
            <div class="mb-3">
                <input type="text" name="license_key" class="form-control" placeholder="{{ __('Enter License Key') }}" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">{{ __('Activate License') }}</button>
        </form>

        <a href="{{ route('login') }}" class="btn btn-secondary mt-3">{{ __('Go to Login') }}</a>
    </div>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js"></script>
</body>

</html>
