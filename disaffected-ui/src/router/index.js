import { createRouter, createWebHistory } from 'vue-router';
import RundownManager from '@/components/RundownManager.vue';
import ColorSelector from '@/components/ColorSelector.vue';

const routes = [
  {
    path: '/',
    redirect: '/rundown-manager/:episodeID'
  },
  {
    path: '/rundown-manager/:episodeID',
    name: 'RundownManager',
    component: RundownManager,
  },
  {
    path: '/color-selector',
    name: 'ColorSelector',
    component: ColorSelector,
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
