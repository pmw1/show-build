import { createRouter, createWebHistory } from 'vue-router'
import RundownManager from '@/components/RundownManager.vue'
import DashboardView from '@/views/DashboardView.vue'

const routes = [
  {
    path: '/',
    redirect: '/dashboard'
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView
  },
  {
    // Keep existing RundownManager route with episode parameter
    path: '/rundown/:episode?',
    name: 'rundown',
    component: RundownManager,
    props: true
  },
  {
    path: '/rundown-manager/:episode?',
    redirect: to => {
      return { path: `/rundown/${to.params.episode || ''}` }
    }
  },
  // Add new routes for other sections
  {
    path: '/assets',
    name: 'assets',
    component: () => import('@/views/AssetsView.vue')
  },
  {
    path: '/templates',
    name: 'templates',
    component: () => import('@/views/TemplatesView.vue')
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
