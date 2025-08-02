<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;
use App\Models\News;
use App\Models\Image;

return new class extends Migration
{
    public function up(): void
    {
        // Add news_id to images table
        Schema::table('images', function (Blueprint $table) {
            $table->unsignedBigInteger('news_id')->nullable()->after('id');
            $table->foreign('news_id')->references('id')->on('news')->onDelete('cascade');
        });

        // Migrate existing image data from news to images table
        $newsItems = News::whereNotNull('image')->get();
        foreach ($newsItems as $news) {
            Image::create([
                'news_id' => $news->id,
                'title' => $news->title, // Use news title as image title
                'url' => $news->image,
                'created_at' => $news->created_at,
                'updated_at' => $news->updated_at,
            ]);
        }

        // Drop the image column from news table
        Schema::table('news', function (Blueprint $table) {
            $table->dropColumn('image');
        });
    }

    public function down(): void
    {
        // Recreate the image column in news table
        Schema::table('news', function (Blueprint $table) {
            $table->string('image')->nullable()->after('title');
        });

        // Migrate image data back to news table (take the first image)
        $newsItems = News::has('images')->get();
        foreach ($newsItems as $news) {
            $firstImage = $news->images()->first();
            if ($firstImage) {
                $news->update(['image' => $firstImage->url]);
            }
        }

        // Remove news_id and foreign key from images table
        Schema::table('images', function (Blueprint $table) {
            $table->dropForeign(['news_id']);
            $table->dropColumn('news_id');
        });
    }
};
