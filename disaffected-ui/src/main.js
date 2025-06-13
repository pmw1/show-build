import { createApp } from 'vue'
import App from './App.vue'
import { vuetify } from './plugins/vuetify'
import router from './router'
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'
import { loadFonts } from './plugins/webfontloader'

loadFonts()

const app = createApp(App)
app.use(router)
app.use(vuetify)
app.mount('#app')

