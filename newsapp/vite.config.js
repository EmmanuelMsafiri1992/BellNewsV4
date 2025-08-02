import { defineConfig, loadEnv } from 'vite';
import laravel from 'laravel-vite-plugin';
import vue from '@vitejs/plugin-vue';
import legacy from '@vitejs/plugin-legacy';
import os from 'os';

// Function to get the local IP address for HMR
function getLocalIp() {
  const interfaces = os.networkInterfaces();
  for (const name of Object.keys(interfaces)) {
    for (const iface of interfaces[name]) {
      if (iface.family === 'IPv4' && !iface.internal) {
        return iface.address;
      }
    }
  }
  return 'localhost'; // fallback if no LAN IP found
}

// Get environment variables from .env file
const env = loadEnv(process.env.NODE_ENV, process.cwd(), '');

// Define the API base URL. We are prioritizing the environment variable
// passed by the build script over the one in the .env file.
const apiBaseUrl = env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export default defineConfig({
  plugins: [
    laravel({
      input: [
        'resources/css/app.css',
        'resources/js/app.js',
      ],
      refresh: true,
    }),
    vue(),
    legacy({
      targets: [
        'defaults',
        'not IE 11',
        'ie >= 11',
        'chrome >= 49',
        'safari >= 9',
        'edge >= 12',
        'firefox >= 45',
        'samsung >= 5',
        'opera >= 36',
        'android >= 4.4',
        'last 2 versions',
      ],
      additionalLegacyPolyfills: [
        'regenerator-runtime/runtime',
        'core-js/es/array',
        'core-js/es/promise',
        'core-js/es/symbol',
        'core-js/es/object/assign',
      ],
      modernPolyfills: true,
    }),
  ],
  css: {
    postcss: './postcss.config.js',
  },
  server: {
    host: '0.0.0.0', // CHANGE THIS LINE to allow access from other devices on the network
    port: 5173,
    hmr: {
      host: getLocalIp(), // Use local IP for HMR to work across devices
      clientPort: 5173,
    },
  },
  build: {
    target: 'es5',
    minify: true,
  },
  // Ensure the base URL is correctly set for the frontend
  define: {
    'process.env.VITE_API_BASE_URL': JSON.stringify(apiBaseUrl),
  },
});
