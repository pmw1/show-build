import { createApp } from 'vue';
import App from './App.vue';
import router from './router'; // <--- This line is critical
import vuetify from './plugins/vuetify';
import { loadFonts } from './plugins/webfontloader';

loadFonts();

createApp(App)
  .use(router) // <--- Also critical
  .use(vuetify)
  .mount('#app');

