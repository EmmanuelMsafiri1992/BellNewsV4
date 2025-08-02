<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header-component />

    <!-- Hero Section -->
    <section class="bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-16">
      <div class="container mx-auto px-4 text-center">
        <h1 class="text-4xl md:text-5xl font-extrabold mb-4">Latest News</h1>
        <p class="text-lg md:text-xl mb-6">Stay updated with the latest events and stories.</p>
        <div v-if="latestNews" class="max-w-4xl mx-auto bg-white bg-opacity-10 rounded-lg p-6 shadow-lg">
          <img :src="latestNews.image_url || ''" :alt="latestNews.title" class="w-full h-64 object-cover rounded-t-lg">
          <div class="p-4">
            <h2 class="text-2xl font-semibold mb-2">{{ latestNews.title }}</h2>
            <p class="text-gray-200 mb-4">{{ latestNews.description }}</p>
            <p class="text-sm text-gray-300">Published: {{ latestNews.date }}</p>
          </div>
        </div>
        <p v-else class="text-gray-200">No latest news available.</p>
      </div>
    </section>

    <!-- News Grid -->
    <section class="container mx-auto px-4 py-12">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <div v-for="news in newsItems" :key="news.id" class="bg-white rounded-lg shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden">
          <img :src="news.image_url || ''" :alt="news.title" class="w-full h-48 object-cover">
          <div class="p-4">
            <h3 class="text-xl font-semibold mb-2">{{ news.title }}</h3>
            <p class="text-gray-600 mb-4">{{ truncateDescription(news.description, 100) }}</p>
            <button @click="showDetails(news)" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors duration-300">Read More</button>
          </div>
        </div>
        <div v-if="newsItems.length === 0" class="col-span-full text-center text-gray-500">
          No news items available.
        </div>
      </div>
    </section>

    <!-- News Details Modal -->
    <div v-if="selectedNews" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 overflow-y-auto max-h-[90vh]">
        <button @click="selectedNews = null" class="absolute top-4 right-4 text-gray-500 hover:text-gray-700">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
        <img :src="selectedNews.image_url || ''" :alt="selectedNews.title" class="w-full h-64 object-cover rounded-t-lg">
        <div class="p-4">
          <h2 class="text-2xl font-bold mb-2">{{ selectedNews.title }}</h2>
          <p class="text-gray-600 mb-4">{{ selectedNews.full_description || selectedNews.description }}</p>
          <p class="text-sm text-gray-500">Published: {{ selectedNews.date }}</p>
          <p class="text-sm text-gray-500 mt-2">Status: {{ selectedNews.status }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import HeaderComponent from './HeaderComponent.vue';

export default {
  name: 'NewsPage',
  components: {
    HeaderComponent,
  },
  data() {
    return {
      newsItems: [],
      selectedNews: null,
      loading: true,
    };
  },
  computed: {
    latestNews() {
      return this.newsItems.length > 0 ? this.newsItems[0] : null;
    },
  },
  methods: {
    truncateDescription(text, maxLength) {
      if (!text) return '';
      return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },
    showDetails(news) {
      this.selectedNews = news;
    },
    async fetchNews() {
      this.loading = true;
      try {
        const response = await fetch('http://localhost:8000/api/news');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        if (data.success && Array.isArray(data.data)) {
          this.newsItems = data.data;
        } else {
          this.newsItems = [];
        }
      } catch (error) {
        console.error('Error fetching news:', error);
        this.newsItems = [];
      } finally {
        this.loading = false;
      }
    },
  },
  mounted() {
    this.fetchNews();
  }
};
</script>

<style scoped>
/* Custom scrollbar for modal */
.max-h-\[90vh\]::-webkit-scrollbar {
  width: 8px;
}
.max-h-\[90vh\]::-webkit-scrollbar-track {
  background: #f1f1f1;
}
.max-h-\[90vh\]::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}
.max-h-\[90vh\]::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* Ensure modal content is scrollable */
.max-h-\[90vh\] {
  scrollbar-width: thin;
  scrollbar-color: #888 #f1f1f1;
}
</style>
