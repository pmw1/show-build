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
    redirect: async () => {
      const configured = await checkDatabaseConfig()
      return configured ? '/dashboard' : '/setup'
    }
  },
  {
    path: '/setup',
    name: 'setup',
    component: SetupView
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: DashboardView
  },
  {
    path: '/episodes',
    name: 'episodes',
    component: () => import('@/views/EpisodesView.vue')
  },
  {
    // Keep existing RundownManager route with episode parameter - renamed to Stack Manager
    path: '/stack/:episode?',
    name: 'stack',
    component: StackOrganizer,
    props: true
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
    path: '/tools',
    name: 'tools',
    component: () => import('@/views/ToolsView.vue')
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue')
  },
  {
    path: '/item-types',
    name: 'item-types',
    component: () => import('@/views/ItemTypesView.vue')
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/views/ProfileView.vue'),
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
  // Skip setup check for setup page itself
  if (to.name === 'setup') {
    next()
    return
  }
  
  // Check if system is configured
  const configured = await checkDatabaseConfig()
  if (!configured) {
    next('/setup')
    return
  }
  
  // Check authentication for protected routes
  if (to.meta.requiresAuth && !isAuthenticated()) {
    // Redirect to dashboard if not authenticated
    next('/dashboard')
  } else {
    next()
  }
})

export default router
