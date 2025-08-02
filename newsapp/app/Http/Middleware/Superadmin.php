<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;
use Illuminate\Support\Facades\Auth; // Don't forget to import Auth

class Superadmin
{
    /**
     * Handle an incoming request.
     *
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        // Assuming your User model has a method or property to check for superadmin status
        if (Auth::check() && Auth::user()->isSuperAdmin()) { // Replace isSuperAdmin() with your actual method/property
            return $next($request);
        }

        // If not a superadmin, you can redirect them or abort with an error
        return redirect('/home')->with('error', 'Unauthorized access.'); // Or abort(403);
    }
}

