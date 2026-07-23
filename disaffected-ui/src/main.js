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
import { initializeXtts } from '@/composables/useXtts'

loadFonts()

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
  timeout: 4000,  // Increased from default 3000ms to 4000ms (1 second longer)
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

// Initialize XTTS configuration
initializeXtts().then(() => {
  console.log('XTTS configuration initialized')
}).catch((error) => {
  console.error('Failed to initialize XTTS:', error)
})
