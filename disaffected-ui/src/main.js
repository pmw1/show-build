import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { vuetify } from './plugins/vuetify'
import { loadFonts } from './plugins/webfontloader'
import axios from 'axios'
import { createPinia } from 'pinia'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'

loadFonts()

const app = createApp(App)

app.use(router)
app.use(vuetify)
app.use(createPinia())
app.use(Toast, {
  transition: "Vue-Toastification__bounce",
  maxToasts: 20,
  newestOnTop: true
});

app.config.globalProperties.$axios = axios.create({
  baseURL: process.env.VUE_APP_API_BASE_URL || '/api',
});

app.mount('#app')
