<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\License;
use Illuminate\Http\Request;
use Illuminate\Support\Str; // For generating unique license codes
use Carbon\Carbon; // For date manipulation
use Illuminate\Support\Facades\Log; // Import the Log facade

class LicenseController extends Controller
{
    public function __construct()
    {
        // Ensure only Superadmins can access methods in this controller
        $this->middleware('superadmin');
    }

    /**
     * Show the form for generating new licenses.
     */
    public function generateForm()
    {
        return view('admin.licenses.generate');
    }

    /**
     * Generate new license codes.
     */
    public function generate(Request $request)
    {
        $request->validate([
            'count' => ['required', 'integer', 'min:1', 'max:100'],
            'validity_days' => ['required', 'integer', 'min:1'],
        ]);

        $licenses = [];
        // Explicitly cast validity_days to an integer to prevent Carbon error
        $validityDays = (int) $request->validity_days;

        for ($i = 0; $i < $request->count; $i++) {
            $code = Str::uuid()->toString();
            // Calculate the expiration date based on the provided validity_days
            $expiresAt = Carbon::now()->addDays($validityDays); // Use the casted integer

            $licenses[] = [
                'code' => $code,
                'expires_at' => $expiresAt,
                'is_used' => false,
                'user_id' => null,
                'created_at' => Carbon::now(),
                'updated_at' => Carbon::now(),
            ];
        }

        License::insert($licenses);

        return redirect()->route('admin.licenses.generate.form')
                         ->with('success', $request->count . ' licenses generated successfully!')
                         ->with('generated_codes', collect($licenses)->pluck('code')->toArray())
                         ->with('validity_days', $request->validity_days);
    }

    /**
     * Display a list of all licenses.
     */
    public function index()
    {
        $licenses = License::orderBy('created_at', 'desc')->paginate(20);
        return view('admin.licenses.index', compact('licenses'));
    }

    /**
     * Remove the specified license from storage.
     */
    public function destroy(License $license) // Using route model binding
    {
        try {
            $license->delete();
            // Log::info('License deleted successfully.', ['license_id' => $license->id, 'license_code' => $license->code]);
            return redirect()->route('admin.licenses.index')->with('success', 'License deleted successfully!');
        } catch (\Exception $e) {
            // Log::error('Error deleting license.', ['license_id' => $license->id, 'error' => $e->getMessage()]);
            return redirect()->route('admin.licenses.index')->with('error', 'Failed to delete license: ' . $e->getMessage());
        }
    }
}

