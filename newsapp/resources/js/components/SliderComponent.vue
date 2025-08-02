<template>
  <div class="relative h-96 sm:h-[400px] lg:h-[500px] xl:h-[600px] 2xl:h-[720px] overflow-hidden bg-gray-100 rounded-xl"
       @mouseenter="$emit('pause')"
       @mouseleave="$emit('resume')"
       tabindex="0"
       @keydown.left="prevSlide"
       @keydown.right="nextSlide"
       aria-label="News Slider"
  >
    <!-- Loading state -->
    <div v-if="!newsItems || newsItems.length === 0" class="absolute inset-0 flex flex-col items-center justify-center bg-gray-200 text-gray-600 p-4">
      <div class="animate-spin rounded-full h-16 w-16 sm:h-20 sm:w-20 border-b-4 border-blue-600 mx-auto"></div>
      <p class="mt-6 text-lg sm:text-xl font-medium">{{ $t('Loading images...') }}</p>
    </div>

    <!-- Slider container -->
    <div
      v-else
      class="slider-container h-full w-full flex"
      :style="{ transform: `translateX(-${currentIndex * 100}%)` }"
    >
      <div
        v-for="(news, index) in newsItems"
        :key="news.id || `slide-${index}`"
        class="slider-slide h-full flex-none w-full relative"
      >
        <!-- Image with fallback -->
        <img
          :src="news.image_url"
          :alt="news.title || $t('News image')"
          class="news-image w-full h-full object-cover transition-opacity duration-300"
          :class="{ 'loading': !imageLoaded[index] && !imageErrors[index], 'opacity-0': imageErrors[index] }"
          @load="handleImageLoad(index)"
          @error="handleImageError(index)"
          loading="lazy"
        />

        <!-- Fallback content when image fails -->
        <div
          v-if="imageErrors[index]"
          class="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-blue-600 to-purple-700 text-white p-6 sm:p-8 lg:p-12 text-center"
        >
          <div class="max-w-md">
            <svg class="w-20 h-20 sm:w-24 sm:h-24 mx-auto mb-6 opacity-80" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
            </svg>
            <h3 class="text-xl sm:text-2xl lg:text-3xl font-bold mb-3" v-html="news.title || $t('News Update')"></h3>
            <p class="text-base sm:text-lg opacity-90">{{ news.category || $t('Latest News') }}</p>
          </div>
        </div>

        <!-- Image overlay with news info -->
        <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent flex items-end p-6 sm:p-8 lg:p-10">
          <div class="text-white w-full">
            <h3 class="text-xl sm:text-2xl lg:text-3xl font-bold mb-2 line-clamp-2" v-html="news.title || $t('Untitled')"></h3>
            <p class="text-sm sm:text-base opacity-90 line-clamp-1">{{ news.date || '' }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Navigation dots -->
    <div
      v-if="newsItems && newsItems.length > 1"
      class="absolute bottom-4 sm:bottom-6 left-1/2 transform -translate-x-1/2 flex space-x-2 sm:space-x-3 z-10"
    >
      <button
        v-for="(_, index) in newsItems"
        :key="`dot-${index}`"
        @click="goToSlide(index)"
        class="w-3 h-3 sm:w-4 sm:h-4 rounded-full transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-800"
        :class="currentIndex === index ? 'bg-white' : 'bg-white bg-opacity-50 hover:bg-opacity-75'"
        :aria-label="`Go to slide ${index + 1}`"
      ></button>
    </div>

    <!-- Navigation arrows -->
    <button
      v-if="newsItems && newsItems.length > 1"
      @click="prevSlide"
      class="absolute left-4 sm:left-6 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-3 sm:p-4 rounded-full hover:bg-opacity-75 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-800 z-10"
      aria-label="Previous slide"
    >
      <svg class="w-6 h-6 sm:w-8 sm:h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
      </svg>
    </button>

    <button
      v-if="newsItems && newsItems.length > 1"
      @click="nextSlide"
      class="absolute right-4 sm:right-6 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-3 sm:p-4 rounded-full hover:bg-opacity-75 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-offset-2 focus:ring-offset-gray-800 z-10"
      aria-label="Next slide"
    >
      <svg class="w-6 h-6 sm:w-8 sm:h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
      </svg>
    </button>
  </div>
</template>

<script>
export default {
  name: 'SliderComponent',
  props: {
    newsItems: {
      type: Array,
      required: true,
      default: () => []
    },
    currentIndex: {
      type: Number,
      default: 0
    },
    autoSlide: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      imageErrors: {},
      imageLoaded: {},
    };
  },
  methods: {
    handleImageLoad(index) {
      this.$set(this.imageLoaded, index, true);
      this.$set(this.imageErrors, index, false);
    },
    handleImageError(index) {
      this.$set(this.imageErrors, index, true);
      console.warn(`Failed to load image for slide ${index}. Displaying fallback.`);
    },
    nextSlide() {
      if (!this.newsItems || this.newsItems.length === 0) return;
      const newIndex = (this.currentIndex + 1) % this.newsItems.length;
      this.$emit('slide-change', newIndex);
    },
    prevSlide() {
      if (!this.newsItems || this.newsItems.length === 0) return;
      const newIndex = this.currentIndex === 0 ? this.newsItems.length - 1 : this.currentIndex - 1;
      this.$emit('slide-change', newIndex);
    },
    goToSlide(index) {
      if (index >= 0 && index < this.newsItems.length) {
        this.$emit('slide-change', index);
      }
    }
  }
};
</script>

<style scoped>
/* Slider container and slide transitions */
.slider-container {
  display: flex;
  transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94); /* Smoother ease-in-out */
  will-change: transform;
  backface-visibility: hidden; /* Improves rendering performance */
}
.slider-slide {
  flex-shrink: 0;
}
.slider-slide img {
  backface-visibility: hidden;
  transform: translateZ(0); /* Promotes hardware acceleration */
  will-change: opacity;
}

/* Text truncation for titles and descriptions */
.line-clamp-1 {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}
.line-clamp-2 {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* Spin animation for loading indicators */
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.animate-spin {
  animation: spin 1s linear infinite;
}

/* Responsive height adjustments for the slider */
.h-96 { height: 24rem; } /* Default for small screens */
@media screen and (min-width: 640px) { /* sm */
  .sm\:h-\[400px\] { height: 25rem; } /* ~400px */
}
@media screen and (min-width: 1024px) { /* lg */
  .lg\:h-\[500px\] { height: 31.25rem; } /* ~500px */
}
@media screen and (min-width: 1280px) { /* xl */
  .xl\:h-\[600px\] { height: 37.5rem; } /* ~600px */
}
@media screen and (min-width: 1536px) { /* 2xl */
  .2xl\:h-\[720px\] { height: 45rem; } /* ~720px for larger displays */
}

/* 4K TV optimizations (already present, adjusted slightly) */
@media screen and (min-width: 1920px) {
  .h-96 { height: 32rem; } /* Base height for 4K, consider larger if needed */
  .text-xl { font-size: 1.875rem !important; } /* 30px */
  .text-sm { font-size: 1.125rem !important; } /* 18px */
  .p-3 { padding: 1rem; } /* 16px */
  .w-6, .h-6 { width: 2rem; height: 2rem; } /* 32px */
  .w-3, .h-3 { width: 1rem; height: 1rem; } /* 16px */
  button { min-width: 48px; min-height: 48px; } /* Larger touch targets */
  button:focus, .focusable:focus {
    outline: 3px solid #3b82f6;
    outline-offset: 2px;
    box-shadow: 0 0 0 6px rgba(59, 130, 246, 0.3);
  }
}

/* Specific styling for TV contrast and readability */
@media screen and (min-width: 1920px) {
  .bg-black { background-color: rgba(0, 0, 0, 0.85); }
  .text-white { text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.9); font-weight: 500; }
}
@media (prefers-contrast: high) {
  .text-white { color: #ffffff; text-shadow: 2px 2px 0px #000000; }
  .bg-black { background-color: #000000; }
  .bg-white { background-color: #ffffff; }
}

/* Image loading animation (from App.vue, but relevant here) */
.news-image.loading {
  opacity: 0.7;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
}
@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
