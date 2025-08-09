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
  </v-app>
</template>

<script>
import LoginModal from '@/components/LoginModal.vue'
import axios from 'axios'
import { useAuth } from '@/composables/useAuth'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

export default {
  name: 'App',
  components: {
    LoginModal
  },
  setup() {
    const { isAuthenticated, currentUser, checkAuthStatus, handleLogout, setAuth } = useAuth()
    const router = useRouter()
    
    const drawer = ref(false)
    const showLoginModal = ref(false)
    
    const navItems = [
      { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/dashboard' },
      { title: 'Rundown Editor', icon: 'mdi-playlist-edit', to: '/rundown' },
      { title: 'Content Editor', icon: 'mdi-script-text-outline', to: '/content-editor' },
      { title: 'Asset Manager', icon: 'mdi-folder', to: '/assets' },
      { title: 'Templates', icon: 'mdi-file-document', to: '/templates' },
      { title: 'Settings', icon: 'mdi-cog', to: '/settings' }
    ]
    
    const userMenuItems = [
      { title: 'Profile', icon: 'mdi-account', action: 'profile' },
      { title: 'Settings', icon: 'mdi-cog', action: 'settings' },
      { title: 'Logout', icon: 'mdi-logout', action: 'logout' }
    ]
    
    const handleLoginSuccess = (authData) => {
      setAuth(authData.token, authData.user, authData.expiry)
      showLoginModal.value = false
    }
    
    const handleUserMenuItem = (item) => {
      if (item.action === 'profile') router.push('/profile')
      else if (item.action === 'settings') router.push('/settings')
      else if (item.action === 'logout') {
        handleLogout()
        router.push('/dashboard')
      }
    }
    
    onMounted(() => {
      checkAuthStatus()
      
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
      handleUserMenuItem
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
</style>
