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

    <!-- Navigation Drawer -->
    <v-navigation-drawer
      v-model="drawer"
      temporary
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
        <router-view></router-view>
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

export default {
  name: 'App',
  components: {
    LoginModal
  },
  data: () => ({
    drawer: false,
    showLoginModal: false,
    isAuthenticated: false,
    currentUser: {},
    navItems: [
      {
        title: 'Dashboard',
        icon: 'mdi-view-dashboard',
        to: '/dashboard'
      },
      {
        title: 'Rundown Editor',
        icon: 'mdi-playlist-edit',
        to: '/rundown'
      },
      {
        title: 'Asset Manager',
        icon: 'mdi-folder',
        to: '/assets'
      },
      {
        title: 'Templates',
        icon: 'mdi-file-document',
        to: '/templates'
      },
      {
        title: 'Settings',
        icon: 'mdi-cog',
        to: '/settings'
      }
    ],
    userMenuItems: [
      {
        title: 'Profile',
        icon: 'mdi-account',
        action: 'profile'
      },
      {
        title: 'Settings',
        icon: 'mdi-cog',
        action: 'settings'
      },
      {
        title: 'Logout',
        icon: 'mdi-logout',
        action: 'logout'
      }
    ]
  }),
  mounted() {
    this.checkAuthStatus()
    this.setupAxiosInterceptors()
  },
  methods: {
    checkAuthStatus() {
      const token = localStorage.getItem('auth-token')
      const expiry = localStorage.getItem('auth-token-expiry')
      const userData = localStorage.getItem('user-data')

      if (token && expiry && userData) {
        const currentTime = Date.now()
        const expiryTime = parseInt(expiry)

        if (currentTime < expiryTime) {
          // Token is still valid
          this.isAuthenticated = true
          this.currentUser = JSON.parse(userData)
          
          // Set auth header for axios
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        } else {
          // Token expired, clear auth data
          this.clearAuthData()
        }
      }
    },
    setupAxiosInterceptors() {
      // Add response interceptor to handle token expiration
      axios.interceptors.response.use(
        response => response,
        error => {
          if (error.response?.status === 401) {
            // Token expired or invalid, clear auth and show login
            this.clearAuthData()
            this.showLoginModal = true
          }
          return Promise.reject(error)
        }
      )
    },
    handleLoginSuccess(authData) {
      this.isAuthenticated = true
      this.currentUser = authData.user
      console.log('Login successful:', authData.user)
    },
    handleUserMenuItem(item) {
      switch (item.action) {
        case 'profile':
          this.$router.push('/profile')
          break
        case 'settings':
          this.$router.push('/settings')
          break
        case 'logout':
          this.handleLogout()
          break
        default:
          console.log(`User menu action: ${item.action}`)
      }
    },
    handleLogout() {
      this.clearAuthData()
      this.$router.push('/dashboard')
    },
    clearAuthData() {
      this.isAuthenticated = false
      this.currentUser = {}
      
      // Clear localStorage
      localStorage.removeItem('auth-token')
      localStorage.removeItem('auth-token-expiry')
      localStorage.removeItem('user-data')
      
      // Clear axios auth header
      delete axios.defaults.headers.common['Authorization']
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
  padding-top: 64px !important;  /* Add padding equal to app bar height */
  padding-left: 0 !important;
  padding-right: 0 !important;
  padding-bottom: 0 !important;
}

.v-main .v-container {
  max-width: none;
  padding: 0 !important;
}
</style>
