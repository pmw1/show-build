import { createRouter, createWebHistory } from 'vue-router'
import RundownManager from '@/components/RundownManager.vue'
import ContentEditor from '@/components/ContentEditor.vue'
import DashboardView from '@/views/DashboardView.vue'

// Authentication check function
function isAuthenticated() {
  const token = localStorage.getItem('auth-token')
  const expiry = localStorage.getItem('auth-token-expiry')
  
  if (!token || !expiry) return false
  
  return Date.now() < parseInt(expiry)
}

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
  {
    path: '/content-editor/:episode?',
    name: 'content-editor',
    component: ContentEditor,
    props: true
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
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard to check authentication
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !isAuthenticated()) {
    // Redirect to dashboard if not authenticated
    next('/dashboard')
  } else {
    next()
  }
})

export default router
