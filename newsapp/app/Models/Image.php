<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Image extends Model
{
    protected $fillable = ['news_id', 'title', 'url', 'slide_duration', 'sizes'];

       protected $casts = [
        'sizes' => 'array',
    ];


    public function news()
    {
        return $this->belongsTo(News::class);
    }
}
