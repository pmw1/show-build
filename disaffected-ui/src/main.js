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

app.use(router)
app.use(vuetify)
app.use(createPinia())
app.use(Toast, {
  transition: "Vue-Toastification__bounce",
  maxToasts: 20,
  newestOnTop: true
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
