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
        Schema::create('licenses', function (Blueprint $table) {
            $table->id();
            $table->string('code')->unique(); // The actual license key (e.g., UUID or random string)
            $table->timestamp('expires_at')->nullable(); // When this license itself expires
            $table->boolean('is_used')->default(false); // Whether this license has been used to activate an account
            $table->foreignId('user_id')->nullable()->constrained()->onDelete('set null'); // The user who used this license
            $table->timestamps();
        });
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('licenses');
    }
};
