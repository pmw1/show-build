<template>
  <v-app>
    <!-- Top App Bar -->
    <v-app-bar
      v-if="isAuthenticated"
      color="surface"
      elevation="1"
      style="padding-top: 5px; padding-bottom: 5px;"
    >
      <v-app-bar-nav-icon
        @click="drawer = !drawer"
      ></v-app-bar-nav-icon>

      <v-app-bar-title class="text-primary font-weight-bold app-title-compact" style="margin-right: 0.25em;">
        Show Builder
      </v-app-bar-title>

      <!-- Status Clock (Today's Date) -->
      <StatusClock v-if="isAuthenticated" style="margin-left: -20px;" />

      <!-- Live Clock (Countdown) -->
      <LiveClock v-if="isAuthenticated" class="ms-3" />

      <v-spacer></v-spacer>

      <!-- Authentication Status -->
      <div v-if="isAuthenticated" class="d-flex align-center user-info-section">
        <!-- User name -->
        <div class="me-3 d-none d-sm-flex align-center">
          <span class="user-name-text text-primary">{{ userFullName }}</span>
        </div>

        <!-- User Menu -->
        <v-menu>
          <template v-slot:activator="{ props }">
            <v-btn
              icon
              v-bind="props"
              size="small"
            >
              <v-avatar size="28">
                <v-img
                  v-if="currentUser.profile_picture"
                  :src="currentUser.profile_picture"
                  :alt="userFullName"
                />
                <v-icon color="primary" size="28">mdi-account-circle</v-icon>
              </v-avatar>
            </v-btn>
          </template>
          <v-list>
            <v-list-item
              v-for="(item, i) in userMenuItems"
              :key="i"
              :prepend-icon="item.icon"
              :title="item.title"
              @click="handleUserMenuItem(item)"
            >
            </v-list-item>
          </v-list>
        </v-menu>
      </div>

      <!-- Login Button (when not authenticated) -->
      <v-btn
        v-else
        color="primary"
        variant="outlined"
        prepend-icon="mdi-login"
        @click="showLoginModal = true"
      >
        Login
      </v-btn>
    </v-app-bar>

    <!-- Show Info Header/Main Toolbar (always visible below app bar) -->
    <router-view v-slot="{ Component }">
      <component :is="Component" v-if="$route.name === 'ContentEditor'" />
    </router-view>

    <!-- Navigation Drawer -->
    <v-navigation-drawer
      v-if="isAuthenticated"
      v-model="drawer"
      :temporary="$route.name !== 'ContentEditor'"
    >
      <v-list density="compact" nav>
        <v-list-item
          v-for="(item, i) in navItems"
          :key="i"
          :value="item"
          :to="item.to"
          :prepend-icon="item.icon"
        >
          <v-list-item-title>{{ item.title }}</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <!-- Main Content Area -->
    <v-main>
      <v-container fluid class="pa-0">
        <router-view v-if="$route.name !== 'ContentEditor'" />
      </v-container>
    </v-main>

    <!-- Login Modal -->
    <LoginModal
      v-model="showLoginModal"
      @login-success="handleLoginSuccess"
    />
    
    <!-- Urgent Flash Overlay -->
    <UrgentFlash ref="urgentFlash" />

    <!-- Standard Notification -->
    <StandardNotification ref="standardNotification" />

    <!-- Screen Flash for modal triggers and aborts -->
    <ScreenFlash />

    <!-- Initialization Overlay - shows while health check loads -->
    <InitializationOverlay />

    <!-- Status Grid - Fixed at top center -->
    <div v-if="isAuthenticated" class="status-grid-overlay">
      <!-- Status indicator cells -->
      <div class="grid-cell" :class="{
        'backend-connected': health.status === 'healthy',
        'backend-disconnected': health.status === 'error',
        'backend-unknown': health.status === 'unknown',
        'status-checking': loading
      }">
        BACK
      </div>
      <div class="grid-cell" :class="{
        'db-connected': health.services?.database === 'connected',
        'db-disconnected': health.services?.database === 'auth_failed' || health.services?.database === 'db_not_found' || health.services?.database === 'connection_refused' || health.services?.database === 'error',
        'db-unknown': health.services?.database === 'unknown' || health.services?.database === 'no_config' || !health.services?.database,
        'status-checking': loading
      }">
        DB1
      </div>
      <div class="grid-cell">
        DB2
      </div>
      <div
        v-if="health.services?.ollama"
        class="grid-cell"
        :class="{
          'ollama-connected': health.services?.ollama?.status === 'connected',
          'ollama-disconnected': health.services?.ollama?.status === 'connection_refused' || health.services?.ollama?.status === 'timeout' || health.services?.ollama?.status?.startsWith('error'),
          'ollama-unknown': health.services?.ollama?.status === 'unknown',
          'status-checking': loading
        }"
      >
        OLLAMA
      </div>
      <div
        v-if="health.services?.xtts"
        class="grid-cell"
        :class="{
          'xtts-connected': health.services?.xtts?.status === 'connected',
          'xtts-depleted': health.services?.xtts?.status === 'depleted',
          'xtts-disconnected': health.services?.xtts?.status === 'error' || !health.services?.xtts?.connected,
          'status-checking': loading
        }"
      >
        XTTS
      </div>
      <div class="grid-cell" :class="{
        'redis-connected': health.services?.redis?.connected,
        'redis-disconnected': health.services?.redis?.error || !health.services?.redis?.connected,
        'redis-slow': health.services?.redis?.latency > 100,
        'status-checking': loading
      }">
        REDIS
      </div>
      <div class="grid-cell" :class="{
        'celery-connected': health.services?.celery?.workers?.length > 0,
        'celery-disconnected': health.services?.celery?.error || health.services?.celery?.workers?.length === 0,
        'status-checking': loading
      }">
        {{ health.services?.celery?.workers?.length > 0 ? 'W:' + health.services?.celery?.workers?.length : 'CELERY' }}
      </div>
      <div
        class="grid-cell nfs-cell"
        :class="{
          'nfs-connected': health.services?.nfs?.status === 'connected',
          'nfs-warning': health.services?.nfs?.status === 'warning',
          'nfs-disconnected': health.services?.nfs?.status === 'error' || !health.services?.nfs?.status,
          'status-checking': loading
        }"
        @click="openNfsModal"
        style="cursor: pointer;"
      >
        NFS
      </div>
    </div>

    <!-- NFS Status Modal -->
    <NfsStatusModal ref="nfsModalRef" />
  </v-app>
</template>

<script>
import LoginModal from '@/components/LoginModal.vue'
import UrgentFlash from '@/components/UrgentFlash.vue'
import StandardNotification from '@/components/StandardNotification.vue'
import ScreenFlash from '@/components/ScreenFlash.vue'
import InitializationOverlay from '@/components/InitializationOverlay.vue'
import LiveClock from '@/components/LiveClock.vue'
import StatusClock from '@/components/StatusClock.vue'
import NfsStatusModal from '@/components/NfsStatusModal.vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'
import { useUrgentFlash } from '@/composables/useUrgentFlash'
import { useStandardNotification } from '@/composables/useStandardNotification'
import { useSystemHealth } from '@/composables/useSystemHealth'
import { NOTIFICATION_COLORS } from '@/composables/useStandardNotification'
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'App',
  components: {
    LoginModal,
    UrgentFlash,
    StandardNotification,
    ScreenFlash,
    InitializationOverlay,
    LiveClock,
    StatusClock,
    NfsStatusModal
  },
  setup() {
    const { isAuthenticated, currentUser, checkAuthStatus, handleLogout, setAuth } = useAuth()
    const { registerFlashComponent } = useUrgentFlash()
    const { registerNotificationComponent } = useStandardNotification()
    const { health, isLoading: loading } = useSystemHealth() // eslint-disable-line no-unused-vars
    const router = useRouter()

    const drawer = ref(false)
    const showLoginModal = ref(false)
    const isAdmin = ref(false)
    const allOrganizations = ref([])
    const selectedOrgId = ref(null)
    const urgentFlash = ref(null)
    const standardNotification = ref(null)
    const nfsModalRef = ref(null)
    
    const navItems = [
      { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/dashboard' },
      { title: 'Episodes', icon: 'mdi-television-classic', to: '/episodes' },
      { title: 'Tools', icon: 'mdi-toolbox', to: '/tools' },
      { title: 'Organization', icon: 'mdi-domain', to: '/organization' },
      { title: 'Stack Manager', icon: 'mdi-playlist-edit', to: '/stack' },
      { title: 'Content Editor', icon: 'mdi-script-text-outline', to: '/content-editor' },
      { title: 'Asset Manager', icon: 'mdi-folder', to: '/assets' },
      { title: 'Templates', icon: 'mdi-file-document', to: '/templates' },
      { title: 'Item Types', icon: 'mdi-format-list-bulleted-type', to: '/item-types' },
      { title: 'Settings', icon: 'mdi-cog', to: '/settings' }
    ]
    
    const userMenuItems = [
      { title: 'Profile', icon: 'mdi-account', action: 'profile' },
      { title: 'Settings', icon: 'mdi-cog', action: 'settings' },
      { title: 'Logout', icon: 'mdi-logout', action: 'logout' }
    ]

    // Computed property for user's full name
    const userFullName = computed(() => {
      if (currentUser.value?.first_name && currentUser.value?.last_name) {
        return `${currentUser.value.first_name} ${currentUser.value.last_name}`
      } else if (currentUser.value?.first_name) {
        return currentUser.value.first_name
      } else if (currentUser.value?.last_name) {
        return currentUser.value.last_name
      } else {
        return currentUser.value?.username || 'User'
      }
    })
    
    const handleLoginSuccess = async (authData) => {
      setAuth(authData.token, authData.user, authData.expiry)
      showLoginModal.value = false
      
      // Show success notification
      window.notifyUserStandard("Login successful!", NOTIFICATION_COLORS.SUCCESS, 2000)
      
      // Check if user is admin and load organizations
      isAdmin.value = authData.user?.access_level === 'admin'
      if (isAdmin.value) {
        await loadOrganizations()
      }
    }
    
    const handleUserMenuItem = (item) => {
      if (item.action === 'profile') router.push('/profile')
      else if (item.action === 'settings') router.push('/settings')
      else if (item.action === 'logout') {
        handleLogout()
        router.push('/dashboard')
      }
    }

    const loadOrganizations = async () => {
      try {
        const response = await axios.get('/api/organizations/')
        if (response.data && response.data.length > 0) {
          allOrganizations.value = response.data
          
          // Set Polaris as default or first org
          let defaultOrg = response.data.find(org => 
            org.name.toLowerCase().includes('polaris') || 
            org.legal_name?.toLowerCase().includes('polaris')
          )
          if (!defaultOrg) {
            defaultOrg = response.data[0]
          }
          selectedOrgId.value = defaultOrg.id
        }
      } catch (error) {
        console.error('Failed to load organizations:', error)
      }
    }

    const switchOrganization = (orgId) => {
      // You can emit an event or use a global state management solution
      // For now, just update the selected org
      selectedOrgId.value = orgId
      console.log('Switched to organization ID:', orgId)
    }

    const openNfsModal = () => {
      if (nfsModalRef.value) {
        nfsModalRef.value.open()
      }
    }
    
    onMounted(async () => {
      checkAuthStatus()

      // Register the urgent flash component
      if (urgentFlash.value) {
        registerFlashComponent(urgentFlash.value)
      }

      // Register the standard notification component
      if (standardNotification.value) {
        registerNotificationComponent(standardNotification.value)
      }

      // Check if user is admin and load organizations
      if (isAuthenticated.value) {
        isAdmin.value = currentUser.value?.access_level === 'admin'
        if (isAdmin.value) {
          await loadOrganizations()
        }
      }

      // Setup axios interceptors
      axios.interceptors.response.use(
        response => response,
        error => {
          if (error.response?.status === 401) {
            // Don't clear localStorage token on 401 - just show login modal
            // This prevents logout loops when token expires or API calls fail
            isAuthenticated.value = false
            showLoginModal.value = true
          }
          return Promise.reject(error)
        }
      )
    })
    
    return {
      drawer,
      showLoginModal,
      isAuthenticated,
      currentUser,
      userFullName,
      navItems,
      userMenuItems,
      handleLoginSuccess,
      handleUserMenuItem,
      isAdmin,
      allOrganizations,
      selectedOrgId,
      switchOrganization,
      urgentFlash,
      standardNotification,
      nfsModalRef,
      openNfsModal,
      health,
      loading
    }
  }
}
</script>

<style>
.v-app-bar {
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

/* App title - shrink to content width */
.app-title-compact {
  min-width: 150px !important;
  max-width: 200px !important;
}

/* User info section - add spacing below status indicators */
.user-info-section {
  margin-top: 14px;
}

/* User name styling - matches Show Builder title color */
.user-name-text {
  font-size: 0.9rem;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.v-main {
  background: #f5f5f5;
  padding-top: 64px !important;  /* Only app bar height */
  padding-left: 0 !important;
  padding-right: 0 !important;
  padding-bottom: 0 !important;
}

/* Status Grid Overlay - Fixed at top right above user info */
.status-grid-overlay {
  position: fixed;
  top: 0px;
  right: 0px;
  transform: scale(0.75);
  transform-origin: top right;
  display: flex;
  flex-direction: row;
  gap: 1px;
  align-items: center;
  z-index: 9999;
  pointer-events: none;
  border-radius: 4px;
  padding: 2px;
}

.grid-cell {
  width: 60px;
  height: 25px;
  background-color: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  color: #666;
  flex-shrink: 0;
  border-radius: 2px;
}

.grid-cell.backend-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.backend-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.backend-unknown {
  background-color: #757575;
  color: white;
  font-weight: bold;
}

.grid-cell.db-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.db-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.db-unknown {
  background-color: #ff9800;
  color: black;
  font-weight: bold;
}

.grid-cell.xtts-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.xtts-depleted {
  background-color: #ffc107;
  color: black;
  font-weight: bold;
}

.grid-cell.xtts-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.ollama-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.ollama-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.ollama-disabled {
  background-color: #9e9e9e;
  color: white;
  font-weight: bold;
}

.grid-cell.ollama-unknown {
  background-color: #757575;
  color: white;
  font-weight: bold;
}

.grid-cell.redis-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.redis-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.redis-slow {
  background-color: #ff9800;
  color: black;
  font-weight: bold;
}

.grid-cell.celery-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.celery-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.nfs-connected {
  background-color: #4caf50;
  color: white;
  font-weight: bold;
}

.grid-cell.nfs-warning {
  background-color: #ff9800;
  color: black;
  font-weight: bold;
}

.grid-cell.nfs-disconnected {
  background-color: #f44336;
  color: white;
  font-weight: bold;
}

.grid-cell.nfs-cell:hover {
  opacity: 0.8;
  transform: scale(1.05);
  transition: all 0.2s ease;
}

/* Status checking animation - blue/white throb */
.grid-cell.status-checking {
  animation: status-throb 1.5s ease-in-out infinite;
  position: relative;
}

@keyframes status-throb {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(33, 150, 243, 0.7);
  }
  50% {
    box-shadow: 0 0 12px 4px rgba(33, 150, 243, 0.4);
  }
}

/* GLOBAL FIX: Vuetify 3 label positioning issues across all modals and forms */
.v-field .v-field__label {
  transition: all 0.2s ease !important;
  transform-origin: top left !important;
}

/* Ensure labels start in the correct position */
.v-field:not(.v-field--focused):not(.v-field--active):not(.v-field--dirty) .v-field__label {
  top: 50% !important;
  transform: translateY(-50%) !important;
  font-size: 1rem !important;
}

/* When field is focused, active, or has value, move label up */
.v-field--focused .v-field__label,
.v-field--active .v-field__label,
.v-field--dirty .v-field__label {
  top: 0 !important;
  transform: translateY(-50%) scale(0.75) !important;
  font-size: 0.75rem !important;
  background-color: white !important;
  padding: 0 4px !important;
  z-index: 1 !important;
}

</style>
