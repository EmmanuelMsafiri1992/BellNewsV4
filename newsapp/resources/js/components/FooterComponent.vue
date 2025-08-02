<template>
  <footer class="bg-gray-800 text-white p-4 sm:p-6 lg:p-8 border-t border-gray-600 z-20">
    <div class="container mx-auto flex flex-col md:flex-row justify-between items-center text-sm sm:text-base text-gray-400">
      <div class="mb-2 md:mb-0 text-center md:text-left text-sm sm:text-base">
        {{ footerCopyrightText }}
      </div>

      <div v-if="footerContactInfo" class="mb-2 md:mb-0 text-center md:text-left text-sm sm:text-base">
        <p>{{ footerContactInfo }}</p>
      </div>
      <div class="flex space-x-4 sm:space-x-6">
        <a href="/" class="hover:text-white transition-colors duration-300 text-base sm:text-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-opacity-75 rounded px-2 py-1">
          {{ $t('home') }}
        </a>
        <a href="/login" class="hover:text-white transition-colors duration-300 text-base sm:text-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:ring-opacity-75 rounded px-2 py-1">
          {{ $t('login') }}
        </a>
      </div>
    </div>
  </footer>
</template>

<script>
import axios from 'axios';

export default {
  name: 'FooterComponent',
  data() {
    return {
      footerCopyrightText: this.$t('All rights reserved.'), // Default value
      footerContactInfo: '' // Initialize footerContactInfo
    };
  },
  methods: {
    async fetchSettings() {
      try {
        const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
        const response = await axios.get(`${apiBaseUrl}/api/settings`);
        if (response.data) {
          if (response.data.footer_copyright_text) {
            this.footerCopyrightText = response.data.footer_copyright_text;
          }
          if (response.data.footer_contact_info) {
            this.footerContactInfo = response.data.footer_contact_info;
          }
        }
      } catch (error) {
        console.error('Error fetching footer settings:', error);
        this.footerCopyrightText = this.$t('All rights reserved.'); // Fallback to defaults on error
        this.footerContactInfo = '';
      }
    }
  },
  mounted() {
    this.fetchSettings();
  }
};
</script>

<style scoped>
/* No additional CSS needed for this component, Tailwind handles it */
</style>
