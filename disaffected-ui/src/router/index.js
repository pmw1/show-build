import { createRouter, createWebHistory } from 'vue-router'
import StackOrganizer from '@/components/StackOrganizer.vue'
import ContentEditor from '@/components/ContentEditor.vue'
import DashboardView from '@/views/DashboardView.vue'
import SetupView from '@/views/SetupView.vue'
import { useAuth } from '@/composables/useAuth';

// Authentication check function
function isAuthenticated() {
  const { checkAuthStatus } = useAuth();
  return checkAuthStatus();
}

// Check if database configuration exists
async function checkDatabaseConfig() {
  try {
    const response = await fetch('/api/setup/status')
    if (response.ok) {
      const status = await response.json()
      return status.configured
    }
  } catch (error) {
    console.log('Setup status check failed:', error)
  }
  return false
}

const routes = [
  {
    path: '/',
    name: 'home',
    redirect: '/dashboard'
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue')
  },
  {
    path: '/setup',
    name: 'setup',
    component: SetupView
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView,
    meta: { requiresAuth: true }
  },
  {
    path: '/episodes',
    name: 'episodes',
    component: () => import('@/views/EpisodesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    // Keep existing RundownManager route with episode parameter - renamed to Stack Manager
    path: '/stack/:episode?',
    name: 'stack',
    component: StackOrganizer,
    props: true,
    meta: { requiresAuth: true }
  },
  {
    path: '/rundown-manager/:episode?',
    redirect: to => {
      return { path: `/stack/${to.params.episode || ''}` }
    }
  },
  {
    path: '/content-editor/:episode?',
    name: 'content-editor',
    component: ContentEditor,
    props: true,
    meta: { requiresAuth: true }
  },
  // Add new routes for other sections
  {
    path: '/assets',
    name: 'assets',
    component: () => import('@/views/AssetsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/templates',
    name: 'templates',
    component: () => import('@/views/TemplatesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/tools',
    name: 'tools',
    component: () => import('@/views/ToolsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/item-types',
    name: 'item-types',
    component: () => import('@/views/ItemTypesView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/users',
    name: 'users',
    component: () => import('@/views/UserManagement.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/organization',
    name: 'organization',
    component: () => import('@/components/OrganizationEdit.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/show',
    name: 'show',
    component: () => import('@/components/ShowEdit.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard to check setup and authentication
router.beforeEach(async (to, from, next) => {
  // Skip setup and login check for those pages themselves
  if (to.name === 'setup' || to.name === 'login') {
    next()
    return
  }

  // For home route, check configuration and authentication
  if (to.name === 'home') {
    const configured = await checkDatabaseConfig()
    if (!configured) {
      next('/setup')
      return
    }
    // If configured, check authentication
    if (isAuthenticated()) {
      next('/dashboard')
    } else {
      next('/login')
    }
    return
  }

  // Check if system is configured for all other routes
  const configured = await checkDatabaseConfig()
  if (!configured) {
    next('/setup')
    return
  }

  // Check authentication for protected routes
  if (to.meta.requiresAuth && !isAuthenticated()) {
    // Redirect to login if not authenticated
    next('/login')
  } else {
    next()
  }
})

export default router
