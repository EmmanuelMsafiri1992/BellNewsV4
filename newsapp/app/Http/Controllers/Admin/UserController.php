<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Models\License; // Import the License model
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules\Password;
use Illuminate\Support\Facades\Log; // Ensure Log facade is imported
use Carbon\Carbon; // Import Carbon

class UserController extends Controller
{
    public function __construct()
    {
        $this->middleware('auth');
    }

    /**
     * Display a listing of the users.
     * Eager load the 'license' relationship.
     *
     * @return \Illuminate\Http\Response
     */
    public function index()
    {
        // Eager load the 'license' relationship to avoid N+1 query problem
        $users = User::with('license')->latest()->paginate(10);
        return view('admin.users.index', compact('users'));
    }

    /**
     * Show the form for creating a new user.
     *
     * @return \Illuminate\Http\Response
     */
    public function create()
    {
        return view('admin.users.create');
    }

    /**
     * Store a newly created user in storage.
     *
     * @param  \Illuminate\Http\Request  $request
     * @return \Illuminate\Http\Response
     */
    public function store(Request $request)
    {
        $request->validate([
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'string', 'email', 'max:255', 'unique:users'],
            'password' => ['required', 'confirmed', Password::defaults()],
        ]);

        try {
            User::create([
                'name' => $request->name,
                'email' => $request->email,
                'password' => Hash::make($request->password),
                'role' => 'user', // Default role for new users, adjust as needed
            ]);
            return redirect()->route('admin.users.index')->with('success', 'User created successfully!');
        } catch (\Exception $e) {
            Log::error('Error creating user: ' . $e->getMessage());
            return redirect()->back()->with('error', 'Failed to create user. Please try again.');
        }
    }

    /**
     * Show the form for editing the specified user's password.
     *
     * @param  \App\Models\User  $user
     * @return \Illuminate\Http\Response
     */
    public function edit(User $user)
    {
        return view('admin.users.edit', compact('user'));
    }

    /**
     * Update the specified user's password in storage.
     *
     * @param  \Illuminate\Http\Request  $request
     * @param  \App\Models\User  $user
     * @return \Illuminate\Http\Response
     */
    public function updatePassword(Request $request, User $user)
    {
        $request->validate([
            'password' => ['required', 'confirmed', Password::defaults()],
        ]);

        try {
            $user->password = Hash::make($request->password);
            $user->save();
            return redirect()->route('admin.users.index')->with('success', 'User password updated successfully!');
        } catch (\Exception $e) {
            Log::error('Error updating user password: ' . $e->getMessage());
            return redirect()->back()->with('error', 'Failed to update user password. Please try again.');
        }
    }

    /**
     * Show the form for editing a user's license.
     *
     * @param  \App\Models\User  $user
     * @return \Illuminate\Http\Response
     */
    public function editLicense(User $user)
    {
        // Eager load the license relationship for the specific user
        $user->load('license');
        return view('admin.users.edit_license', compact('user'));
    }

    /**
     * Update a user's license in storage.
     *
     * @param  \Illuminate\Http\Request  $request
     * @param  \App\Models\User  $user
     * @return \Illuminate\Http\Response
     */
    public function updateLicense(Request $request, User $user)
    {
        Log::info('Attempting to update license for user ID: ' . $user->id);
        Log::info('Request data:', $request->all());

        // --- FIX START ---
        // Changed 'is_used' validation from 'nullable|boolean' to 'nullable'
        // because HTML checkboxes send "on" which Laravel's 'boolean' rule doesn't parse.
        // The boolean conversion is correctly handled by $request->has('is_used') later.
        $request->validate([
            'is_used' => 'nullable', // Allow it to be present (e.g., "on") or not present
            'expires_at' => 'nullable|date|after_or_equal:today',
        ]);
        // --- FIX END ---

        try {
            // Find or create a license record for this user
            $license = $user->license()->firstOrNew(['user_id' => $user->id]);

            // Set is_used based on checkbox presence. If checkbox is not in request, it means it's unchecked.
            $license->is_used = $request->has('is_used');
            Log::info('License is_used will be set to: ' . ($license->is_used ? 'true' : 'false'));

            // Set expires_at. If input is empty, it will be null.
            $license->expires_at = $request->input('expires_at');
            // Log the parsed Carbon date if it's not null, otherwise 'null'
            Log::info('License expires_at will be set to: ' . ($license->expires_at ? Carbon::parse($license->expires_at)->format('Y-m-d H:i:s') : 'null'));


            $license->save(); // Save the license record

            Log::info('License update successful for user ID: ' . $user->id);
            return redirect()->route('admin.users.index')->with('success', 'User license updated successfully!');
        } catch (\Illuminate\Validation\ValidationException $e) {
            Log::error('Validation error updating user license: ' . $e->getMessage(), $e->errors());
            return redirect()->back()->withErrors($e->errors())->withInput();
        } catch (\Exception $e) {
            Log::error('Error updating user license: ' . $e->getMessage(), ['exception' => $e]);
            return redirect()->back()->with('error', 'Failed to update user license. Please try again.');
        }
    }

    /**
     * Remove the specified user from storage.
     *
     * @param  \App\Models\User  $user
     * @return \Illuminate\Http\Response
     */
    public function destroy(User $user)
    {
        try {
            // Optionally, delete the associated license when a user is deleted
            if ($user->license) {
                $user->license->delete();
            }
            $user->delete();
            return redirect()->route('admin.users.index')->with('success', 'User deleted successfully!');
        } catch (\Exception $e) {
            Log::error('Error deleting user: ' . $e->getMessage());
            return redirect()->back()->with('error', 'Failed to delete user. Please try again.');
        }
    }
}
