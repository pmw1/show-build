import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { vuetify } from './plugins/vuetify'
import { loadFonts } from './plugins/webfontloader'
import axios from 'axios'
import { createPinia } from 'pinia'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
import './styles/vuetify-fixes.css'
import './assets/styles/llm-visual-feedback.css'
import { initializeTts } from '@/composables/useTts'

loadFonts()

// Set global axios defaults to use relative URLs (proxy handles routing to backend)
// This ensures all axios imports use the correct baseURL
// Use window.location.origin to ensure HTTPS protocol matches
axios.defaults.baseURL = typeof window !== 'undefined' ? window.location.origin : ''
console.log('Axios baseURL set to:', axios.defaults.baseURL)

// Handle hot module reload and prevent duplicate app mounting
const appElement = document.getElementById('app')

// Check if app is already mounted and unmount it properly
if (appElement.__vue_app__) {
  appElement.__vue_app__.unmount()
  delete appElement.__vue_app__
}

const app = createApp(App)

// Suppress known vuedraggable errors (library bug, doesn't affect functionality)
app.config.errorHandler = (err, instance, info) => {
  // Filter out vuedraggable internal errors
  if (err.message && err.message.includes("Cannot read properties of undefined (reading 'updated')")) {
    // Silently ignore this known vuedraggable bug
    return
  }
  // Log all other errors normally
  console.error('Error:', err)
  console.error('Info:', info)
}

// Suppress benign ResizeObserver errors (occurs with Vuetify expansion panels/modals)
// This is a browser timing issue that doesn't affect functionality
const resizeObserverErr = window.onerror
window.onerror = function(message, source, lineno, colno, error) {
  if (message === 'ResizeObserver loop completed with undelivered notifications.' ||
      (typeof message === 'string' && message.includes('ResizeObserver loop'))) {
    return true // Suppress the error
  }
  return resizeObserverErr ? resizeObserverErr(message, source, lineno, colno, error) : false
}

window.addEventListener('error', (e) => {
  if (e.message && e.message.includes('ResizeObserver loop')) {
    e.stopImmediatePropagation()
    e.preventDefault()
    return false
  }
}, true) // Use capture phase to catch it early

app.use(router)
app.use(vuetify)
app.use(createPinia())
app.use(Toast, {
  transition: "Vue-Toastification__bounce",
  maxToasts: 20,
  newestOnTop: true,
  timeout: 5000,  // 5 seconds display time
  containerClassName: "toast-container-high-z toast-custom-style",  // Custom classes for z-index and styling
  toastClassName: "toast-blue-small"  // Custom class for individual toasts
});

const axiosInstance = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || '/api',
});

// Add JWT token to all requests
axiosInstance.interceptors.request.use(config => {
  const token = localStorage.getItem('auth-token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

app.config.globalProperties.$axios = axiosInstance;

// Mount app and store reference for hot module reload
app.mount('#app')
appElement.__vue_app__ = app

// Initialize TTS configuration
initializeTts().then(() => {
  console.log('TTS configuration initialized')
}).catch((error) => {
  console.error('Failed to initialize TTS:', error)
})
