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
            // Drop the unique index first if it exists (SQLite requires this before dropping the column)
            $table->dropUnique('settings_license_key_unique');

            // Then drop the columns
            if (Schema::hasColumn('settings', 'license_key')) {
                $table->dropColumn('license_key');
            }
            if (Schema::hasColumn('settings', 'license_expiration_date')) {
                $table->dropColumn('license_expiration_date');
            }
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('settings', function (Blueprint $table) {
            // Re-add the columns
            $table->string('license_key')->unique()->nullable()->after('value');
            $table->timestamp('license_expiration_date')->nullable()->after('license_key');
        });
    }
};
