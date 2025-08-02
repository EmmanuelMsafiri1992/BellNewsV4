<template>
  <header class="bg-gray-800 text-white p-4 sm:p-6 lg:p-8 relative z-20">
    <div class="container mx-auto flex items-center justify-between relative">
      <!-- Title centered using absolute positioning and transform for perfect centering -->
      <h1 class="text-xl sm:text-2xl lg:text-3xl font-bold absolute left-1/2 -translate-x-1/2 whitespace-nowrap overflow-hidden text-ellipsis max-w-[calc(100%-160px)] md:max-w-[calc(100%-200px)]">
        {{ headerTitle }}
      </h1>
      <!-- Navigation aligned to the right -->
      <nav class="flex space-x-4 sm:space-x-6 items-center ml-auto">
        <a href="#" class="hover:text-gray-300 transition-colors duration-300 text-base sm:text-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-opacity-75 rounded px-2 py-1">
          {{ $t('home') }}
        </a>
        <a href="/login" class="hover:text-gray-300 transition-colors duration-300 text-base sm:text-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-opacity-75 rounded px-2 py-1">
          {{ $t('login') }}
        </a>
      </nav>
    </div>
  </header>
</template>

<script>
import axios from 'axios';

export default {
  name: 'HeaderComponent',
  data() {
    return {
      headerTitle: this.$t('School News'), // Default value
      showLocaleDropdown: false,
    };
  },
  methods: {
    saveLocale() {
      localStorage.setItem('locale', this.$i18n.locale);
      // Trigger a re-render or re-evaluation of RTL class in App.vue
      document.documentElement.setAttribute('dir', (this.$i18n.locale === 'he' || this.$i18n.locale === 'ar') ? 'rtl' : 'ltr');
    },
    async fetchSettings() {
      try {
        const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await axios.get(`${apiBaseUrl}/api/settings`);
        if (response.data && response.data.header_title) {
          this.headerTitle = response.data.header_title;
        }
      } catch (error) {
        console.error('Error fetching header settings:', error);
        this.headerTitle = this.$t('School News'); // Fallback to default if there's an error
      }
    },
    toggleLocaleDropdown() {
      this.showLocaleDropdown = !this.showLocaleDropdown;
    },
    closeLocaleDropdown() {
      this.showLocaleDropdown = false;
    },
    setLocale(locale) {
      this.$i18n.locale = locale;
      this.saveLocale();
      this.closeLocaleDropdown();
    }
  },
  mounted() {
    this.fetchSettings();
    // Set initial dir attribute based on current locale
    document.documentElement.setAttribute('dir', (this.$i18n.locale === 'he' || this.$i18n.locale === 'ar') ? 'rtl' : 'ltr');
  }
};
</script>

<style scoped>
/* No additional CSS needed for this component, Tailwind handles it */
/* The `max-w-[calc(100%-160px)]` and `md:max-w-[calc(100%-200px)]` ensure the title doesn't overlap with navigation */
/* The `whitespace-nowrap overflow-hidden text-ellipsis` handles long titles */
</style>
