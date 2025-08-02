<?php

namespace Database\Seeders;

use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;

class AdminUserSeeder extends Seeder
{
    /**
     * Run the database seeds.
     */
    public function run(): void
    {
        // Superadmin User
        $superadminEmail = 'admin@vcns.co.il';
        if (!DB::table('users')->where('email', $superadminEmail)->exists()) {
            DB::table('users')->insert([
                'name' => 'Super Admin',
                'email' => $superadminEmail,
                'password' => Hash::make('password'),
                'email_verified_at' => now(),
                'role' => 'superadmin',
                'is_active' => true, // Superadmin is active by default
                'created_at' => now(),
                'updated_at' => now(),
            ]);

            $this->command->info('Super Admin user created successfully!');
            $this->command->info('Email: ' . $superadminEmail);
            $this->command->info('Password: password');
            $this->command->info('Role: superadmin');
        } else {
            $this->command->info('Super Admin user already exists. Skipping creation.');
        }

        // Regular User (non-superadmin)
        $regularUserEmail = 'user@vcns.co.il';
        if (!DB::table('users')->where('email', $regularUserEmail)->exists()) {
            DB::table('users')->insert([
                'name' => 'Regular User',
                'email' => $regularUserEmail,
                'password' => Hash::make('password'),
                'email_verified_at' => now(),
                'role' => 'user', // Default user role
                'is_active' => false, // Inactive by default, requires license
                'license_expires_at' => null, // No license yet
                'created_at' => now(),
                'updated_at' => now(),
            ]);

            $this->command->info('Regular user created successfully!');
            $this->command->info('Email: ' . $regularUserEmail);
            $this->command->info('Password: password');
            $this->command->info('Role: user (inactive, requires license)');
        } else {
            $this->command->info('Regular user already exists. Skipping creation.');
        }
    }
}
