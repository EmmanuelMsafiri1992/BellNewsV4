<?php

use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use App\Http\Middleware\SuperadminMiddleware;
use App\Http\Middleware\SetApplicationName;


return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        $middleware->web(append: [
        SetApplicationName::class,  
        ]);
        $middleware->alias([
            'superadmin' => SuperadminMiddleware::class, // Register your middleware alias here
            // ... other aliases
            // 'auth' => \App\Http\Middleware\Authenticate::class,
            'set.admin.locale' => \App\Http\Middleware\SetAdminLocale::class,
            'set.app.name' => \App\Http\Middleware\SetApplicationName::class,
        ]);
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        //
    })->create();
