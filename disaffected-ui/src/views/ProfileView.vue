<template>
  <v-container fluid class="pa-0">
    <!-- Header Section -->
    <v-row class="header-row ma-0">
      <v-col cols="12" class="pa-4">
        <div class="d-flex align-center mb-4">
          <v-btn
            icon="mdi-arrow-left"
            variant="text"
            @click="$router.go(-1)"
            class="me-3"
          />
          <h2 class="text-h4 font-weight-bold">User Profile</h2>
        </div>
      </v-col>
    </v-row>

    <!-- Profile Content -->
    <v-row class="ma-0">
      <v-col cols="12" md="8" lg="6" class="pa-4">
        <v-card>
          <!-- Profile Header -->
          <v-card-text class="pa-6">
            <div class="d-flex align-center mb-6">
              <v-avatar size="80" class="me-4">
                <v-img
                  v-if="user.profile_picture"
                  :src="user.profile_picture"
                  :alt="user.first_name + ' ' + user.last_name"
                />
                <v-icon v-else size="40" color="grey-lighten-1">
                  mdi-account-circle
                </v-icon>
              </v-avatar>
              <div>
                <h3 class="text-h5 font-weight-bold mb-1">
                  {{ user.first_name || user.username }} {{ user.last_name }}
                </h3>
                <v-chip
                  :color="getAccessLevelColor(user.access_level)"
                  variant="flat"
                  size="small"
                  class="text-uppercase font-weight-bold"
                >
                  {{ user.access_level }}
                </v-chip>
              </div>
            </div>

            <!-- Profile Information -->
            <v-divider class="mb-6" />
            
            <div class="profile-info">
              <h4 class="text-h6 font-weight-bold mb-4">Contact Information</h4>
              
              <div class="info-row mb-3">
                <v-icon class="me-3" color="grey-darken-1">mdi-account</v-icon>
                <div>
                  <div class="text-caption text-grey-darken-1">Username</div>
                  <div class="text-body-1 font-weight-medium">{{ user.username }}</div>
                </div>
              </div>

              <div v-if="user.email" class="info-row mb-3">
                <v-icon class="me-3" color="grey-darken-1">mdi-email</v-icon>
                <div>
                  <div class="text-caption text-grey-darken-1">Email</div>
                  <div class="text-body-1 font-weight-medium">{{ user.email }}</div>
                </div>
              </div>

              <div v-if="user.phone" class="info-row mb-3">
                <v-icon class="me-3" color="grey-darken-1">mdi-phone</v-icon>
                <div>
                  <div class="text-caption text-grey-darken-1">Phone</div>
                  <div class="text-body-1 font-weight-medium">{{ user.phone }}</div>
                </div>
              </div>

              <div class="info-row mb-3">
                <v-icon class="me-3" color="grey-darken-1">mdi-shield-account</v-icon>
                <div>
                  <div class="text-caption text-grey-darken-1">Access Level</div>
                  <div class="text-body-1 font-weight-medium text-capitalize">
                    {{ user.access_level }}
                  </div>
                </div>
              </div>
            </div>
          </v-card-text>

          <!-- Profile Actions -->
          <v-card-actions class="pa-6 pt-0">
            <v-spacer />
            <v-btn
              color="primary"
              variant="outlined"
              prepend-icon="mdi-logout"
              @click="handleLogout"
            >
              Logout
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Additional Info Panel -->
      <v-col cols="12" md="4" lg="6" class="pa-4">
        <v-card>
          <v-card-title class="pa-4">
            <v-icon class="me-2">mdi-information</v-icon>
            System Information
          </v-card-title>
          <v-card-text class="pa-4">
            <div class="info-row mb-3">
              <v-icon class="me-3" color="grey-darken-1">mdi-clock</v-icon>
              <div>
                <div class="text-caption text-grey-darken-1">Session Expires</div>
                <div class="text-body-2">{{ getTokenExpiry() }}</div>
              </div>
            </div>
            
            <div class="info-row mb-3">
              <v-icon class="me-3" color="grey-darken-1">mdi-web</v-icon>
              <div>
                <div class="text-caption text-grey-darken-1">Browser</div>
                <div class="text-body-2">{{ getBrowserInfo() }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { useAuth } from '@/composables/useAuth'
import { useRouter } from 'vue-router'
import { onMounted } from 'vue'

export default {
  name: 'ProfileView',
  setup() {
    const { currentUser, handleLogout } = useAuth()
    const router = useRouter()
    
    const getAccessLevelColor = (level) => {
      switch (level) {
        case 'admin':
          return 'error'
        case 'user':
          return 'success'
        case 'guest':
          return 'warning'
        default:
          return 'grey'
      }
    }
    
    const getTokenExpiry = () => {
      const expiry = localStorage.getItem('auth-token-expiry')
      if (expiry) {
        const expiryDate = new Date(parseInt(expiry))
        return expiryDate.toLocaleString()
      }
      return 'Unknown'
    }
    
    const getBrowserInfo = () => {
      return navigator.userAgent.split(' ').slice(-2).join(' ')
    }
    
    const handleUserLogout = () => {
      handleLogout()
      router.push('/dashboard')
      window.location.reload()
    }
    
    onMounted(() => {
      if (!currentUser.value || Object.keys(currentUser.value).length === 0) {
        router.push('/')
      }
    })
    
    return {
      user: currentUser,
      getAccessLevelColor,
      getTokenExpiry,
      getBrowserInfo,
      handleLogout: handleUserLogout
    }
  }
}
</script>

<style scoped>
.header-row {
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  background: white;
}

.v-card {
  border-radius: 12px !important;
}

.info-row {
  display: flex;
  align-items: flex-start;
}

.profile-info .info-row {
  padding: 8px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.profile-info .info-row:last-child {
  border-bottom: none;
}

.v-avatar {
  border: 3px solid rgba(0, 0, 0, 0.1);
}

.v-chip {
  font-size: 0.75rem !important;
  height: 24px !important;
}
</style>
