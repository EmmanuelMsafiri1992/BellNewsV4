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
        Schema::table('images', function (Blueprint $table) {
            // Add the 'sizes' column as a JSON column.
            // It's nullable because existing images might not have this data initially.
            $table->json('sizes')->nullable()->after('slide_duration');
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('images', function (Blueprint $table) {
            // Drop the 'sizes' column if the migration is rolled back.
            $table->dropColumn('sizes');
        });
    }
};

