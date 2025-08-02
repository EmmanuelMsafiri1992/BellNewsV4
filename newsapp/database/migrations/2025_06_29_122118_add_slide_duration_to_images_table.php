<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('images', function (Blueprint $table) {
            // Add slide_duration column (in milliseconds, default to 5 seconds)
            $table->integer('slide_duration')->default(5000)->after('url')->comment('Slide duration in milliseconds');
        });
    }

    public function down(): void
    {
        Schema::table('images', function (Blueprint $table) {
            $table->dropColumn('slide_duration');
        });
    }
};
