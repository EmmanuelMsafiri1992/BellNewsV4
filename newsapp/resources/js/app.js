import { createApp } from 'vue';
import { createI18n } from 'vue-i18n';
import App from './App.vue';
import SliderComponent from './components/SliderComponent.vue';
import NewsComponent from './components/NewsComponent.vue';

// Dynamically import translation files
import en from '../lang/en.json';
import he from '../lang/he.json';
import ar from '../lang/ar.json';

const i18n = createI18n({
  locale: localStorage.getItem('locale') || 'en', // Default or stored locale
  fallbackLocale: 'en',
  messages: {
    en,
    he,
    ar
  }
});

const app = createApp(App);
app.component('slider-component', SliderComponent);
app.component('news-component', NewsComponent);
app.use(i18n);
app.mount('#app');
