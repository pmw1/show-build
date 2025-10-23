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
              <div class="position-relative">
                <v-avatar size="80" class="me-4">
                  <v-img
                    v-if="user.profile_picture"
                    :src="getProfilePictureUrl(user.profile_picture)"
                    :alt="user.first_name + ' ' + user.last_name"
                  />
                  <v-icon v-else size="40" color="grey-lighten-1">
                    mdi-account-circle
                  </v-icon>
                </v-avatar>
                <v-btn
                  icon
                  size="x-small"
                  color="primary"
                  class="upload-btn"
                  @click="triggerFileUpload"
                >
                  <v-icon size="16">mdi-camera</v-icon>
                </v-btn>
                <input
                  ref="fileInputRef"
                  type="file"
                  accept="image/*"
                  style="display: none"
                  @change="handleFileUpload"
                />
              </div>
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

    <!-- Voice Print Recording Section -->
    <v-row class="ma-0 mt-4">
      <v-col cols="12" class="pa-4">
        <VoicePrintRecorder @voice-profile-updated="handleVoiceProfileUpdate" />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { useAuth } from '@/composables/useAuth'
import { useRouter } from 'vue-router'
import { onMounted, ref } from 'vue'
import VoicePrintRecorder from '@/components/VoicePrintRecorder.vue'
import axios from 'axios'

export default {
  name: 'ProfileView',
  components: {
    VoicePrintRecorder
  },
  setup() {
    const { currentUser, handleLogout, refreshUserProfile } = useAuth()
    const router = useRouter()
    const fileInputRef = ref(null)

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

    const getProfilePictureUrl = (profilePicture) => {
      if (!profilePicture) return ''
      // If it's already a full URL, return it
      if (profilePicture.startsWith('http')) return profilePicture
      // Otherwise prepend the API base URL
      const baseUrl = process.env.VUE_APP_API_BASE_URL || 'http://192.168.51.210:8888'
      return `${baseUrl}${profilePicture}`
    }

    const triggerFileUpload = () => {
      fileInputRef.value.click()
    }

    const handleFileUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        alert('File size must be less than 5MB')
        return
      }

      // Validate file type
      const allowedTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif', 'image/webp']
      if (!allowedTypes.includes(file.type)) {
        alert('Please upload a valid image file (JPEG, PNG, GIF, or WebP)')
        return
      }

      const formData = new FormData()
      formData.append('file', file)

      try {
        const token = localStorage.getItem('auth-token')
        const baseUrl = process.env.VUE_APP_API_BASE_URL || 'http://192.168.51.210:8888'

        const response = await axios.post(
          `${baseUrl}/api/auth/upload-profile-picture`,
          formData,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'multipart/form-data'
            }
          }
        )

        if (response.data.success) {
          // Update the user's profile picture in the currentUser object
          currentUser.value.profile_picture = response.data.profile_picture

          // Optionally refresh the entire user profile
          if (refreshUserProfile) {
            await refreshUserProfile()
          }

          alert('Profile picture updated successfully!')
        }
      } catch (error) {
        console.error('Error uploading profile picture:', error)
        alert('Failed to upload profile picture. Please try again.')
      }

      // Reset the file input
      event.target.value = ''
    }

    const handleUserLogout = () => {
      handleLogout()
      router.push('/dashboard')
      window.location.reload()
    }

    const handleVoiceProfileUpdate = (data) => {
      console.log('Voice profile updated:', data)
      // You can add UI feedback here (toast notification, etc.)
    }

    onMounted(() => {
      if (!currentUser.value || Object.keys(currentUser.value).length === 0) {
        router.push('/dashboard')
      }
    })

    return {
      user: currentUser,
      fileInputRef,
      getAccessLevelColor,
      getTokenExpiry,
      getBrowserInfo,
      getProfilePictureUrl,
      triggerFileUpload,
      handleFileUpload,
      handleLogout: handleUserLogout,
      handleVoiceProfileUpdate
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

.position-relative {
  position: relative;
  display: inline-block;
}

.upload-btn {
  position: absolute !important;
  bottom: 0;
  right: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}
</style>
