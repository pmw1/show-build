<template>
  <v-app>
    <!-- Top App Bar -->
    <v-app-bar 
      color="surface"
      elevation="1"
    >
      <v-app-bar-nav-icon
        @click="drawer = !drawer"
      ></v-app-bar-nav-icon>

      <v-app-bar-title class="text-primary font-weight-bold">
        Show Builder
      </v-app-bar-title>

      <v-spacer></v-spacer>

      <!-- Authentication Status -->
      <div v-if="isAuthenticated" class="d-flex align-center">
        <!-- Admin Organization Switcher -->
        <div v-if="isAdmin && allOrganizations.length > 1" class="me-4">
          <v-select
            v-model="selectedOrgId"
            :items="allOrganizations"
            item-title="name"
            item-value="id"
            label="Organization"
            variant="outlined"
            density="compact"
            style="min-width: 180px; transform: scale(0.85) translateY(12px); transform-origin: center center; margin-right: -27px;"
            @update:model-value="switchOrganization"
          />
        </div>

        <!-- Welcome message -->
        <div class="me-4 d-none d-sm-flex">
          <span class="text-body-2 text-grey-darken-1">Welcome, </span>
          <span class="text-body-2 font-weight-medium ml-1">{{ currentUser.username }}</span>
        </div>

        <!-- User Menu -->
        <v-menu>
          <template v-slot:activator="{ props }">
            <v-btn
              icon
              v-bind="props"
            >
              <v-avatar size="32">
                <v-img
                  v-if="currentUser.profile_picture"
                  :src="currentUser.profile_picture"
                  :alt="currentUser.username"
                />
                <v-icon v-else>mdi-account-circle</v-icon>
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
    
    <!-- Status Grid - Fixed at top center -->
    <div v-if="isAuthenticated" class="status-grid-overlay">
      <div class="grid-cell" v-for="n in 7" :key="n" :class="{ 
        'backend-connected': n === 5 && backendConnected, 
        'backend-disconnected': n === 5 && !backendConnected,
        'db-connected': n === 6 && backendStatus === 'healthy',
        'db-disconnected': n === 6 && backendStatus === 'degraded',
        'db-unknown': n === 6 && (backendStatus === 'unknown' || backendStatus === 'disconnected')
      }">
        {{ n === 5 ? 'BACK' : n === 6 ? 'DB1' : n === 7 ? 'DB2' : n }}
      </div>
    </div>
  </v-app>
</template>

<script>
import LoginModal from '@/components/LoginModal.vue'
import UrgentFlash from '@/components/UrgentFlash.vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'
import { useUrgentFlash } from '@/composables/useUrgentFlash'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'App',
  components: {
    LoginModal,
    UrgentFlash
  },
  setup() {
    const { isAuthenticated, currentUser, checkAuthStatus, handleLogout, setAuth } = useAuth()
    const { registerFlashComponent } = useUrgentFlash()
    const router = useRouter()
    
    const drawer = ref(false)
    const showLoginModal = ref(false)
    const isAdmin = ref(false)
    const allOrganizations = ref([])
    const selectedOrgId = ref(null)
    const urgentFlash = ref(null)
    const backendConnected = ref(false)
    const backendStatus = ref('unknown')
    
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
    
    const handleLoginSuccess = async (authData) => {
      setAuth(authData.token, authData.user, authData.expiry)
      showLoginModal.value = false
      
      // Show success flash
      window.showUrgentFlash("WINNER!", "green")
      
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

    const checkBackendHealth = async () => {
      try {
        const response = await axios.get('/health', { timeout: 5000 })
        backendConnected.value = response.data.status === 'healthy'
        backendStatus.value = response.data.status
      } catch (error) {
        backendConnected.value = false
        backendStatus.value = 'disconnected'
      }
    }
    
    onMounted(async () => {
      checkAuthStatus()
      
      // Register the urgent flash component
      if (urgentFlash.value) {
        registerFlashComponent(urgentFlash.value)
      }
      
      // Check if user is admin and load organizations
      if (isAuthenticated.value) {
        isAdmin.value = currentUser.value?.access_level === 'admin'
        if (isAdmin.value) {
          await loadOrganizations()
        }
      }
      
      // Start backend health monitoring
      await checkBackendHealth()
      setInterval(checkBackendHealth, 30000)
      
      // Setup axios interceptors
      axios.interceptors.response.use(
        response => response,
        error => {
          if (error.response?.status === 401) {
            handleLogout()
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
      navItems,
      userMenuItems,
      handleLoginSuccess,
      handleUserMenuItem,
      isAdmin,
      allOrganizations,
      selectedOrgId,
      switchOrganization,
      urgentFlash,
      backendConnected,
      backendStatus
    }
  }
}
</script>

<style>
.v-app-bar {
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
}

.v-main {
  background: #f5f5f5;
  padding-top: 64px !important;  /* Only app bar height */
  padding-left: 0 !important;
  padding-right: 0 !important;
  padding-bottom: 0 !important;
}

/* Status Grid Overlay - Fixed at top of screen */
.status-grid-overlay {
  position: fixed;
  top: 0px;
  left: 50%;
  transform: translateX(-50%) scale(0.85);
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

</style>
