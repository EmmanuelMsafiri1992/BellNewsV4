<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class License extends Model
{
    use HasFactory;

    protected $fillable = [
        'code',
        'expires_at',
        'is_used',
        'user_id',
    ];

    protected function casts(): array
    {
        return [
            'expires_at' => 'datetime',
            'is_used' => 'boolean',
        ];
    }

    /**
     * Define the relationship with the User model.
     * A license can be used by one user.
     */
    public function user()
    {
        return $this->belongsTo(User::class);
    }
}
