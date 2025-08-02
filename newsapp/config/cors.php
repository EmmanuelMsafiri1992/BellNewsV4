<?php

return [
    /*
     * You can enable or disable CORS by setting this value to true or false.
     */
    'enabled' => env('CORS_ENABLED', true),

    /*
     * These are the paths to which CORS will be applied.
     * The default 'api/*' is crucial for your case.
     */
    'paths' => ['api/*', 'sanctum/csrf-cookie'],

    /*
     * The list of origins that can make CORS requests.
     * Use an environment variable to make this dynamic.
     */
    'allowed_origins' => explode(',', env('CORS_ALLOWED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000')),

    /*
     * The list of headers that are allowed to be sent with CORS requests.
     */
    'allowed_headers' => ['*'],

    /*
     * The list of methods that are allowed.
     */
    'allowed_methods' => ['*'],

    /*
     * The maximum age of the CORS preflight request (in seconds).
     */
    'max_age' => 0,

    /*
     * If true, the response will include a `Vary: Origin` header.
     */
    'supports_credentials' => false,
];
