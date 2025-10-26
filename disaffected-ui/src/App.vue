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

      <!-- Episode Selector (universal - visible on all pages) -->
      <v-select
        v-if="isAuthenticated"
        v-model="selectedEpisode"
        :items="episodes"
        item-title="display"
        item-value="episode_number"
        label="Episode"
        variant="outlined"
        hide-details
        color="primary"
        bg-color="rgba(25, 118, 210, 0.05)"
        style="max-width: 440px; min-width: 440px;"
        class="ms-3 episode-selector"
        @update:model-value="loadEpisode"
      >
        <template v-slot:prepend-inner>
          <v-icon size="medium" color="primary">mdi-television-play</v-icon>
        </template>
      </v-select>

      <v-spacer></v-spacer>

      <!-- Authentication Status -->
      <div v-if="isAuthenticated" class="d-flex align-center user-info-section">
        <!-- User name -->
        <div class="me-3 d-none d-sm-flex align-center">
          <span class="user-name-text text-primary">{{ userFullName }}</span>
          <!-- Access Level Badge -->
          <v-chip
            v-if="userAccessLevel"
            :color="accessLevelColor"
            size="x-small"
            class="ms-2 text-uppercase font-weight-bold"
            variant="flat"
          >
            {{ userAccessLevel }}
          </v-chip>
        </div>

        <!-- LLM Notification Center -->
        <NotificationCenter />

        <!-- Job Monitor (Admin Only) -->
        <JobMonitor v-if="userAccessLevel === 'admin'" class="ms-2" />

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
      permanent
      width="320"
    >
      <v-list density="compact" nav v-model:opened="openGroups">
        <!-- Top level items -->
        <v-list-item to="/dashboard" prepend-icon="mdi-view-dashboard">
          <v-list-item-title>Dashboard</v-list-item-title>
        </v-list-item>

        <!-- Show Factory Section -->
        <v-list-group value="scriptfactory">
          <template v-slot:activator="{ props }">
            <v-list-item v-bind="props" prepend-icon="mdi-script-text">
              <v-list-item-title>Show Factory</v-list-item-title>
            </v-list-item>
          </template>
          <v-list-item to="/episodes" prepend-icon="mdi-television-classic">
            <v-list-item-title>Episodes</v-list-item-title>
          </v-list-item>
          <v-list-item to="/content-editor" prepend-icon="mdi-script-text-outline">
            <v-list-item-title>Content Editor</v-list-item-title>
          </v-list-item>
          <v-list-item to="/stack" prepend-icon="mdi-playlist-edit">
            <v-list-item-title>Stack Manager</v-list-item-title>
          </v-list-item>
          <v-list-item to="/assets" prepend-icon="mdi-folder">
            <v-list-item-title>Asset Pool</v-list-item-title>
          </v-list-item>
          <v-list-item to="/templates" prepend-icon="mdi-file-document">
            <v-list-item-title>Templates</v-list-item-title>
          </v-list-item>
          <v-list-item to="/item-types" prepend-icon="mdi-format-list-bulleted-type">
            <v-list-item-title>Item Types</v-list-item-title>
          </v-list-item>

          <!-- Preshow submenu within Show Factory -->
          <v-list-group value="brainstorm" subgroup>
            <template v-slot:activator="{ props }">
              <v-list-item v-bind="props" prepend-icon="mdi-lightbulb-on">
                <v-list-item-title>Preshow</v-list-item-title>
              </v-list-item>
            </template>
            <v-list-item to="/whiteboard" prepend-icon="mdi-notebook-edit">
              <v-list-item-title>Whiteboard</v-list-item-title>
            </v-list-item>
            <v-list-item to="/voice-meeting" prepend-icon="mdi-microphone">
              <v-list-item-title>Production Meeting</v-list-item-title>
            </v-list-item>
          </v-list-group>
        </v-list-group>

        <!-- MediaFactory Section (conditional based on group membership or admin) -->
        <v-list-item
          v-if="isAdmin || userGroups.some(g => g.slug === 'mediafactory')"
          to="/mediafactory"
          prepend-icon="mdi-factory"
        >
          <v-list-item-title>MediaFactory</v-list-item-title>
        </v-list-item>

        <!-- MetaFactory Section (conditional based on group membership or admin) -->
        <v-list-item
          v-if="isAdmin || userGroups.some(g => g.slug === 'metafactory')"
          to="/metafactory"
          prepend-icon="mdi-database-cog"
        >
          <v-list-item-title>MetaFactory</v-list-item-title>
        </v-list-item>

        <!-- Other items -->
        <v-list-item to="/tools" prepend-icon="mdi-toolbox">
          <v-list-item-title>Tools</v-list-item-title>
        </v-list-item>
        <v-list-item to="/organization" prepend-icon="mdi-domain">
          <v-list-item-title>Organization</v-list-item-title>
        </v-list-item>
        <v-list-item to="/settings" prepend-icon="mdi-cog">
          <v-list-item-title>Settings</v-list-item-title>
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

    <!-- Episode Loading Overlay -->
    <v-overlay
      v-model="isLoadingEpisode"
      persistent
      class="episode-loading-overlay"
      :scrim="false"
      :contained="false"
    >
      <div class="loading-content">
        <v-progress-circular
          indeterminate
          size="64"
          width="6"
          color="primary"
          class="loading-spinner"
        ></v-progress-circular>
        <div class="loading-text">
          Loading Episode {{ loadingEpisodeInfo.number }}: {{ loadingEpisodeInfo.title }}<span class="loading-dots"></span>
        </div>
      </div>
    </v-overlay>
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
import NotificationCenter from '@/components/NotificationCenter.vue'
import JobMonitor from '@/components/JobMonitor.vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'
import { useUrgentFlash } from '@/composables/useUrgentFlash'
import { useStandardNotification } from '@/composables/useStandardNotification'
import { useSystemHealth } from '@/composables/useSystemHealth'
import { NOTIFICATION_COLORS } from '@/composables/useStandardNotification'
import { ref, computed, onMounted, watch } from 'vue'
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
    NfsStatusModal,
    NotificationCenter,
    JobMonitor
  },
  setup() {
    const { isAuthenticated, currentUser, checkAuthStatus, handleLogout, setAuth } = useAuth()
    const { registerFlashComponent } = useUrgentFlash()
    const { registerNotificationComponent } = useStandardNotification()
    const { health, isLoading: loading } = useSystemHealth() // eslint-disable-line no-unused-vars
    const router = useRouter()

    const drawer = ref(false)
    const showLoginModal = ref(false)

    // Episode selector state
    const episodes = ref([])
    const selectedEpisode = ref(null)
    const isLoadingEpisode = ref(false)
    const loadingEpisodeInfo = ref({ number: '', title: '' })

    // Close drawer when navigating to a new route
    watch(
      () => router.currentRoute.value,
      () => {
        drawer.value = false
      }
    )
    const isAdmin = ref(false)
    const allOrganizations = ref([])
    const selectedOrgId = ref(null)
    const urgentFlash = ref(null)
    const standardNotification = ref(null)
    const nfsModalRef = ref(null)
    const userGroups = ref([])
    const openGroups = ref(['scriptfactory', 'brainstorm', 'mediafactory', 'metafactory']) // Auto-expand all factory groups
    
    const navItems = [
      { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/dashboard' },
      { title: 'Episodes', icon: 'mdi-television-classic', to: '/episodes' },
      { title: 'Tools', icon: 'mdi-toolbox', to: '/tools' },
      { title: 'Organization', icon: 'mdi-domain', to: '/organization' },
      { title: 'Stack Manager', icon: 'mdi-playlist-edit', to: '/stack' },
      { title: 'Content Editor', icon: 'mdi-script-text-outline', to: '/content-editor' },
      { title: 'Asset Pool', icon: 'mdi-folder', to: '/assets' },
      { title: 'Templates', icon: 'mdi-file-document', to: '/templates' },
      { title: 'Item Types', icon: 'mdi-format-list-bulleted-type', to: '/item-types' },
      { title: 'MediaFactory', icon: 'mdi-factory', to: '/mediafactory', requiresGroup: 'mediafactory' },
      { title: 'MetaFactory', icon: 'mdi-database-cog', to: '/metafactory', requiresGroup: 'metafactory' },
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

    // Computed property for user's access level
    const userAccessLevel = computed(() => {
      return currentUser.value?.access_level || null
    })

    // Computed property for access level badge color
    const accessLevelColor = computed(() => {
      const level = userAccessLevel.value
      if (level === 'admin') return 'error'
      if (level === 'editor') return 'warning'
      if (level === 'viewer') return 'info'
      return 'grey'
    })

    // Computed property to filter nav items based on group membership
    const filteredNavItems = computed(() => {
      return navItems.filter(item => {
        // If item doesn't require a group, always show it
        if (!item.requiresGroup) return true

        // Check if user is in the required group
        return userGroups.value.some(group => group.slug === item.requiresGroup)
      })
    })

    // Load user groups
    const loadUserGroups = async () => {
      if (!currentUser.value || !currentUser.value.id) {
        userGroups.value = []
        return
      }

      try {
        const response = await axios.get(`/api/rbac/users/${currentUser.value.id}/groups`)
        if (response.data.success) {
          userGroups.value = response.data.groups || []
        }
      } catch (error) {
        console.error('Failed to load user groups:', error)
        userGroups.value = []
      }
    }
    
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

      // Load user groups for menu filtering
      await loadUserGroups()
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
    
    // Fetch episodes for selector
    async function fetchEpisodes() {
      try {
        const response = await axios.get('/api/episodes')
        episodes.value = response.data.episodes
          .sort((a, b) => b.episode_number.localeCompare(a.episode_number))
          .map(ep => ({
            episode_number: ep.episode_number,
            display: `${ep.episode_number} - ${ep.title || 'Untitled'}`
          }))

        // Load current episode from sessionStorage
        const storedEpisode = sessionStorage.getItem('currentEpisode')
        if (storedEpisode) {
          selectedEpisode.value = storedEpisode
        }
      } catch (error) {
        console.error('Failed to fetch episodes:', error)
      }
    }

    // Update current episode session variable (stay on current route)
    function loadEpisode(episodeNumber) {
      if (!episodeNumber) return

      // Check if this is a different episode
      const currentEpisode = sessionStorage.getItem('currentEpisode')
      if (currentEpisode !== episodeNumber) {
        // Different episode - show loading overlay
        const episodeData = episodes.value.find(ep => ep.episode_number === episodeNumber)
        if (episodeData) {
          loadingEpisodeInfo.value = {
            number: episodeNumber,
            title: episodeData.title || episodeData.display || 'Untitled Episode'
          }
          isLoadingEpisode.value = true

          // Hide overlay after a delay (components will finish loading)
          setTimeout(() => {
            isLoadingEpisode.value = false
          }, 1500)
        }
      }

      // Store in sessionStorage for cross-component access
      sessionStorage.setItem('currentEpisode', episodeNumber)

      // Update route parameter if current route supports it
      const currentRoute = router.currentRoute.value

      if (currentRoute.params.episode !== undefined || currentRoute.query.episode !== undefined) {
        // Route has episode parameter - update it
        if (currentRoute.params.episode !== undefined) {
          router.push({ ...currentRoute, params: { ...currentRoute.params, episode: episodeNumber } })
        } else if (currentRoute.query.episode !== undefined) {
          router.push({ ...currentRoute, query: { ...currentRoute.query, episode: episodeNumber } })
        }
      }
      // If route doesn't have episode param, just update session (components will pick it up)
    }

    // Watch route changes to sync selected episode with URL
    watch(
      () => router.currentRoute.value,
      (newRoute) => {
        // Check if route has episode parameter (params or query)
        const routeEpisode = newRoute.params.episode || newRoute.query.episode

        if (routeEpisode) {
          selectedEpisode.value = routeEpisode
          sessionStorage.setItem('currentEpisode', routeEpisode)
        } else {
          // Route doesn't have episode param, use sessionStorage value
          const storedEpisode = sessionStorage.getItem('currentEpisode')
          if (storedEpisode) {
            selectedEpisode.value = storedEpisode
          }
        }

        // Fetch episodes if not already loaded
        if (episodes.value.length === 0) {
          fetchEpisodes()
        }
      },
      { immediate: true }
    )

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
        // Load user groups for menu filtering
        await loadUserGroups()
        // Load episodes for selector
        await fetchEpisodes()
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
      userAccessLevel,
      accessLevelColor,
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
      loading,
      userGroups,
      filteredNavItems,
      loadUserGroups,
      openGroups,
      episodes,
      selectedEpisode,
      loadEpisode,
      isLoadingEpisode,
      loadingEpisodeInfo
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

/* Episode Selector - Match clock height and blue theme */
.episode-selector {
  border: 1px solid rgba(25, 118, 210, 0.3) !important;
  height: 100%;
  display: flex;
  align-items: stretch;
}

.episode-selector .v-input__control {
  height: 100%;
}

.episode-selector .v-field__input {
  font-size: 1.1rem !important;
  font-weight: 500 !important;
}

.episode-selector .v-select__selection-text {
  font-size: 1.1rem !important;
  font-weight: 500 !important;
}

.episode-selector .v-field {
  background: rgba(25, 118, 210, 0.05) !important;
  border-color: rgba(25, 118, 210, 0.3) !important;
  border-radius: 0 !important;
}

.episode-selector .v-field--focused {
  border-color: #1976d2 !important;
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2) !important;
}

.episode-selector .v-field__outline {
  color: rgba(25, 118, 210, 0.3) !important;
}

.episode-selector .v-field--focused .v-field__outline {
  color: #1976d2 !important;
}

.episode-selector .v-label {
  color: #1976d2 !important;
  font-weight: 500 !important;
}

/* Episode Selector Dropdown Menu - Blue theme, no rounded corners */
.v-overlay .v-menu__content {
  border-radius: 0 !important;
}

.episode-selector + .v-overlay .v-list {
  background: rgba(25, 118, 210, 0.02) !important;
  border: 1px solid rgba(25, 118, 210, 0.3) !important;
  border-radius: 0 !important;
}

.episode-selector + .v-overlay .v-list-item {
  border-radius: 0 !important;
}

.episode-selector + .v-overlay .v-list-item:hover {
  background: rgba(25, 118, 210, 0.1) !important;
}

.episode-selector + .v-overlay .v-list-item--active {
  background: rgba(25, 118, 210, 0.15) !important;
  color: #1976d2 !important;
}

/* Episode Selector Scrollbar - Blue themed */
.episode-selector + .v-overlay .v-list::-webkit-scrollbar {
  width: 8px;
}

.episode-selector + .v-overlay .v-list::-webkit-scrollbar-track {
  background: rgba(25, 118, 210, 0.05);
  border-radius: 0;
}

.episode-selector + .v-overlay .v-list::-webkit-scrollbar-thumb {
  background: rgba(25, 118, 210, 0.4);
  border-radius: 0;
}

.episode-selector + .v-overlay .v-list::-webkit-scrollbar-thumb:hover {
  background: rgba(25, 118, 210, 0.6);
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

/* Episode Loading Overlay */
.episode-loading-overlay {
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(8px) !important;
  -webkit-backdrop-filter: blur(8px) !important;
}

.episode-loading-overlay .v-overlay__scrim {
  opacity: 0 !important;
}

.episode-loading-overlay > .v-overlay__content {
  position: absolute !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
}

.loading-spinner {
  margin-bottom: 8px;
}

.loading-text {
  font-size: 1.5rem;
  font-weight: 600;
  color: #333;
  text-align: center;
  letter-spacing: 0.5px;
}

.loading-dots::after {
  content: '';
  animation: dots 1.5s steps(4, end) infinite;
}

@keyframes dots {
  0%, 20% {
    content: '';
  }
  40% {
    content: '.';
  }
  60% {
    content: '..';
  }
  80%, 100% {
    content: '...';
  }
}

</style>
