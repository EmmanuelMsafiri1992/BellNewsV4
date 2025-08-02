<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        Schema::table('settings', function (Blueprint $table) {
            // Add license_key column, nullable, and unique if you want to enforce one active license key
            $table->string('license_key')->nullable()->unique()->after('value');
            // Add license_expiration_date column, nullable
            $table->timestamp('license_expiration_date')->nullable()->after('license_key');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('settings', function (Blueprint $table) {
            $table->dropColumn('license_key');
            $table->dropColumn('license_expiration_date');
        });
    }
};
