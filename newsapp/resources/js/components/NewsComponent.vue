<template>
  <div class="h-full bg-blue-700 text-white flex flex-col rounded-xl">
    <div class="p-4 sm:p-6 lg:p-8 border-b border-blue-600">
      <h2 class="text-xl sm:text-2xl lg:text-3xl font-bold break-words leading-tight"
          v-html="currentNews.title || $t('No Title')">
      </h2>
    </div>

    <div class="p-4 sm:p-6 lg:p-8 flex-1 bg-blue-800 flex flex-col">
      <div v-if="currentNews.title" class="flex flex-col h-full">
        <div class="flex flex-wrap items-center space-x-4 lg:space-x-6 mb-4 lg:mb-6">
          <div class="flex items-center text-sm lg:text-base text-blue-200 mb-2 sm:mb-0">
            <svg class="w-4 h-4 lg:w-5 lg:h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            {{ currentNews.date || $t('No Date') }}
          </div>
          <div v-if="currentNews.category" class="px-3 py-1 lg:px-4 lg:py-2 bg-blue-600 text-blue-100 text-sm lg:text-base rounded-full font-medium mb-2 sm:mb-0">
            {{ currentNews.category }}
          </div>
        </div>

        <div class="flex-1 flex flex-col overflow-y-auto custom-scrollbar pr-2">
          <p class="text-blue-100 text-sm sm:text-base lg:text-lg leading-relaxed break-words flex-1"
             v-html="currentNews.full_description || currentNews.description || $t('No Description')">
          </p>
        </div>

        <div v-if="currentNews.location || currentNews.time || currentNews.organizer" class="bg-blue-700 rounded-lg p-4 lg:p-6 mt-4 lg:mt-6">
          <h4 class="font-semibold text-white mb-3 lg:mb-4 text-base lg:text-lg">{{ $t('Event Details') }}</h4>
          <div class="space-y-2 lg:space-y-3">
            <div v-if="currentNews.location" class="flex items-center text-sm lg:text-base text-blue-200">
              <svg class="w-4 h-4 lg:w-5 lg:h-5 mr-2 lg:mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"></path>
              </svg>
              <span><strong>{{ $t('Location:') }}</strong> {{ currentNews.location }}</span>
            </div>
            <div v-if="currentNews.time" class="flex items-center text-sm lg:text-base text-blue-200">
              <svg class="w-4 h-4 lg:w-5 lg:h-5 mr-2 lg:mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
              <span><strong>{{ $t('Time:') }}</strong> {{ currentNews.time }}</span>
            </div>
            <div v-if="currentNews.organizer" class="flex items-center text-sm lg:text-base text-blue-200">
              <svg class="w-4 h-4 lg:w-5 lg:h-5 mr-2 lg:mr-3 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
              </svg>
              <span><strong>{{ $t('Organizer:') }}</strong> {{ currentNews.organizer }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="flex-1 flex items-center justify-center text-center text-blue-200 text-lg sm:text-xl lg:text-2xl">
        {{ $t('No News Articles Yet') }}
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NewsComponent',
  props: {
    newsItems: {
      type: Array,
      required: true,
      default: () => []
    },
    currentIndex: {
      type: Number,
      default: 0
    }
  },
  computed: {
    currentNews() {
      return this.newsItems[this.currentIndex] || {};
    }
  }
};
</script>

<style scoped>
/* Custom scrollbar for better readability on TVs */
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  border: 2px solid rgba(255, 255, 255, 0.1);
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: rgba(255, 255, 255, 0.5);
}

/* Text truncation and wrapping */
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
.break-words {
  word-break: break-word;
}
.whitespace-pre-wrap {
  white-space: pre-wrap;
}
.overflow-wrap-anywhere {
  overflow-wrap: anywhere;
}

/* Smooth transitions */
.transition-colors {
  transition: color 0.2s ease-in-out, background-color 0.2s ease-in-out;
}

/* TV-specific optimizations */
@media screen and (min-width: 1024px) {
  .text-white {
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.9);
    font-weight: 500;
  }
  .text-blue-100,
  .text-blue-200 {
    text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.7);
  }
  .bg-blue-600 {
    background-color: rgb(37, 99, 235);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  .min-h-96 {
    min-height: 28rem;
  }
}

/* 4K TV optimizations */
@media screen and (min-width: 1920px) {
  .text-xl { font-size: 2rem; }
  .text-2xl { font-size: 2.5rem; }
  .text-3xl { font-size: 3rem; }
  .text-lg { font-size: 1.5rem; }
  .text-base { font-size: 1.25rem; }
  .text-sm { font-size: 1.125rem; }

  /* Enhanced shadows for 4K displays */
  .text-white {
    text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.9);
  }
  .text-blue-100,
  .text-blue-200 {
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
  }
}

/* Navigation buttons focus states (from App.vue, but relevant here) */
button:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.5);
}

/* Responsive adjustments for smaller screens */
@media (max-width: 640px) {
  .text-xl, .text-2xl {
    font-size: 1.25rem;
  }
  .text-lg, .text-xl {
    font-size: 1rem;
  }
  .text-sm, .text-base {
    font-size: 0.875rem;
  }
  .p-4, .p-6 {
    padding: 0.75rem;
  }
}

/* RTL support improvements */
[dir="rtl"] .flex {
  flex-direction: row-reverse;
}
[dir="rtl"] .mr-2 {
  margin-right: 0;
  margin-left: 0.5rem;
}
[dir="rtl"] .mr-3 {
  margin-right: 0;
  margin-left: 0.75rem;
}

/* Loading state animations */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
