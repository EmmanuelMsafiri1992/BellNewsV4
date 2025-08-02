<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens; // Assuming you use Sanctum
use Carbon\Carbon;

class User extends Authenticatable
{
    use HasApiTokens, HasFactory, Notifiable;

    /**
     * The attributes that are mass assignable.
     *
     * @var array<int, string>
     */
    protected $fillable = [
        'name',
        'email',
        'password',
        'role', // Assuming 'role' is used for superadmin/admin
        // Removed 'is_active' and 'license_expires_at' from fillable,
        // as these should be managed via the related License model.
    ];

    /**
     * The attributes that should be hidden for serialization.
     *
     * @var array<int, string>
     */
    protected $hidden = [
        'password',
        'remember_token',
    ];

    /**
     * The attributes that should be cast.
     *
     * @var array<string, string>
     */
    protected $casts = [
        'email_verified_at' => 'datetime',
        'password' => 'hashed',
        // Removed 'is_active' and 'license_expires_at' from casts,
        // as their status is now derived from the related License model.
    ];

    /**
     * Define the relationship with the License model.
     * A user can have one active license.
     */
    public function license()
    {
        return $this->hasOne(License::class);
    }

    /**
     * Check if the user is a superadmin.
     *
     * @return bool
     */
    public function isSuperAdmin()
    {
        return $this->role === 'superadmin';
    }

    /**
     * Check if the user is an admin (including superadmin).
     *
     * @return bool
     */
    public function isAdmin()
    {
        return in_array($this->role, ['superadmin', 'admin']);
    }

    /**
     * Check if the user has an active license from the 'licenses' table.
     *
     * @return bool
     */
    public function hasActiveLicense()
    {
        // Eager load the license relationship if it's not already loaded
        // This prevents N+1 query problem if called multiple times
        if (!$this->relationLoaded('license')) {
            $this->load('license');
        }

        // A user has an active license if:
        // 1. They have a related license record.
        // 2. That license record is marked as 'is_used' (meaning it's activated).
        // 3. The 'expires_at' date of that license is in the future.
        return $this->license && $this->license->is_used && $this->license->expires_at && $this->license->expires_at->isFuture();
    }
}
