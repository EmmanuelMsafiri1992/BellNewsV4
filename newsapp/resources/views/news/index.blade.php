<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>School News - News</title>
    <link rel="icon" type="image/png" href="{{ asset('favicon.ico') }}">
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Roboto', sans-serif;
            background-color: #f7f9fc;
            margin: 0;
            padding: 0;
            color: #333;
        }
        .container {
            max-width: 1280px;
            margin-left: auto;
            margin-right: auto;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        #app {
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
    </style>
</head>
<body class="antialiased">
    <div id="app">
        {{-- Example of passing news data. Replace with your actual data from Laravel --}}
        <?php
            // This is just an example. In a real Laravel app, this data would come from your controller.
            $newsData = [
                [
                    'title' => 'Important School Announcement',
                    'date' => '2025-07-01',
                    'category' => 'General',
                    // This is the HTML content with tags that you want to render
                    'description' => '<p>Dear students and parents,</p><p>Please be informed that <b>classes will be suspended tomorrow</b>, July 2, 2025, due to unforeseen circumstances. We apologize for any inconvenience this may cause.</p><p>For more details, visit our <a href="#">school website</a>.</p>'
                ],
                [
                    'title' => 'Sports Day Success!',
                    'date' => '2025-06-28',
                    'category' => 'Sports',
                    'description' => '<p>What a fantastic Sports Day! Our students showed incredible spirit and athleticism. Congratulations to all participants and winners!</p><p>We saw amazing performances in <em>track and field</em> events.</p>'
                ]
            ];
        ?>
        <NewsComponent :news-items='@json($newsData)' :current-index="0"></NewsComponent>
    </div>

    <script src="{{ asset('js/app.js') }}" defer></script>
</body>
</html>
