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

          <!-- Display Profile (drives presence/messaging UI) -->
          <v-divider />
          <v-card-text class="pa-6">
            <h4 class="text-h6 font-weight-bold mb-4">
              <v-icon class="me-2">mdi-account-tie</v-icon>
              Display Profile
            </h4>
            <p class="text-caption text-grey-darken-1 mb-4">
              How other users see you in the People menu and your message bubbles.
            </p>

            <v-text-field
              v-model="displayName"
              label="Display name"
              hint="Shown in the People menu, message threads, and unread toasts. Falls back to your username."
              persistent-hint
              variant="outlined"
              density="compact"
              maxlength="100"
              counter
              class="mb-4"
            />

            <div class="text-body-2 mb-2">Chip color</div>
            <div class="d-flex flex-wrap ga-2 mb-2">
              <button
                v-for="opt in chipColorOptions"
                :key="opt.value"
                type="button"
                class="color-swatch"
                :class="{ active: chipColor === opt.value }"
                :style="{ backgroundColor: opt.hex }"
                :title="opt.label"
                @click="chipColor = opt.value"
              >
                <v-icon v-if="chipColor === opt.value" size="14" color="white">mdi-check</v-icon>
              </button>
              <button
                type="button"
                class="color-swatch color-swatch-clear"
                :class="{ active: !chipColor }"
                title="No color (default)"
                @click="chipColor = ''"
              >
                <v-icon size="14" color="grey">mdi-close</v-icon>
              </button>
            </div>
            <p class="text-caption text-grey-darken-1 mb-4">
              Preview:
              <v-avatar :color="chipColor || 'primary'" size="28" class="ms-2 align-middle">
                <span class="text-caption text-white">{{ previewInitials }}</span>
              </v-avatar>
            </p>

            <v-btn
              color="primary"
              variant="elevated"
              prepend-icon="mdi-content-save"
              :disabled="!displayProfileDirty || savingProfile"
              :loading="savingProfile"
              @click="saveDisplayProfile"
            >
              Save display profile
            </v-btn>
            <span v-if="displayProfileSaved" class="ms-3 text-caption text-success">
              <v-icon size="x-small">mdi-check-circle</v-icon>
              Saved
            </span>
          </v-card-text>

          <!-- Active overrides -->
          <v-divider />
          <v-card-text class="pa-6">
            <h4 class="text-h6 font-weight-bold mb-4">
              <v-icon class="me-2">mdi-tune</v-icon>
              Your active personalizations
              <v-chip size="x-small" variant="tonal" color="primary" class="ms-2">
                {{ overrideEntries.length }}
              </v-chip>
            </h4>
            <p class="text-caption text-grey-darken-1 mb-4">
              Settings you've changed for yourself. Reset any of these to fall back
              to the global default.
            </p>

            <v-list v-if="overrideEntries.length > 0" density="compact" class="pa-0">
              <v-list-item
                v-for="entry in overrideEntries"
                :key="entry.key"
                class="override-row"
              >
                <v-list-item-title class="text-body-2">
                  <code class="override-key">{{ entry.key }}</code>
                </v-list-item-title>
                <v-list-item-subtitle class="text-caption">
                  {{ entry.preview }}
                </v-list-item-subtitle>
                <template #append>
                  <v-btn
                    size="x-small"
                    variant="tonal"
                    color="primary"
                    prepend-icon="mdi-restore"
                    @click="resetOverride(entry.key)"
                  >
                    Reset
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
            <div v-else class="text-caption text-grey">
              No personalizations yet — your settings match the global defaults.
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

<script setup>
import { useAuth } from '@/composables/useAuth'
import { useRouter } from 'vue-router'
import { onMounted, ref, computed } from 'vue'
import VoicePrintRecorder from '@/components/VoicePrintRecorder.vue' // eslint-disable-line no-unused-vars
import axios from 'axios'
import { useUserPrefs } from '@/composables/useUserPrefs'
import { useMessages } from '@/composables/useMessages'

const userPrefs = useUserPrefs()
const messagesApi = useMessages()

const { currentUser, handleLogout: authLogout, refreshUserProfile } = useAuth()
const router = useRouter()
const fileInputRef = ref(null)

const user = currentUser // eslint-disable-line no-unused-vars

// ──────────────────────────────────────────────────────────────────
// Display profile editor (display_name + chip_color → /api/users/me)
// ──────────────────────────────────────────────────────────────────
const displayName = ref('')
const chipColor = ref('')
const _serverDisplayName = ref('')
const _serverChipColor = ref('')
const savingProfile = ref(false)
const displayProfileSaved = ref(false)

const chipColorOptions = [
  { value: 'red',         hex: '#F44336', label: 'Red' },
  { value: 'pink',        hex: '#E91E63', label: 'Pink' },
  { value: 'purple',      hex: '#9C27B0', label: 'Purple' },
  { value: 'deep-purple', hex: '#673AB7', label: 'Deep Purple' },
  { value: 'indigo',      hex: '#3F51B5', label: 'Indigo' },
  { value: 'blue',        hex: '#2196F3', label: 'Blue' },
  { value: 'cyan',        hex: '#00BCD4', label: 'Cyan' },
  { value: 'teal',        hex: '#009688', label: 'Teal' },
  { value: 'green',       hex: '#4CAF50', label: 'Green' },
  { value: 'lime',        hex: '#CDDC39', label: 'Lime' },
  { value: 'amber',       hex: '#FFC107', label: 'Amber' },
  { value: 'orange',      hex: '#FF9800', label: 'Orange' },
  { value: 'deep-orange', hex: '#FF5722', label: 'Deep Orange' },
  { value: 'brown',       hex: '#795548', label: 'Brown' },
  { value: 'blue-grey',   hex: '#607D8B', label: 'Blue Grey' },
]

const displayProfileDirty = computed(() => {
  return (displayName.value || '') !== (_serverDisplayName.value || '')
      || (chipColor.value || '') !== (_serverChipColor.value || '')
})

const previewInitials = computed(() => {
  const name = displayName.value || (currentUser.value?.username || '?')
  const parts = String(name).trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return (parts[0]?.slice(0, 2) || '??').toUpperCase()
})

async function loadDisplayProfile() {
  try {
    const res = await axios.get('/api/users/me', {
      headers: { Authorization: `Bearer ${localStorage.getItem('auth-token')}` }
    })
    _serverDisplayName.value = res.data?.display_name || ''
    _serverChipColor.value = res.data?.chip_color || ''
    displayName.value = _serverDisplayName.value
    chipColor.value = _serverChipColor.value
  } catch (err) {
    console.warn('Failed to load profile:', err)
  }
}

// Active personalizations — keys with personal values in the prefs cache.
// Filter out internal/keyed-by-system entries so the user only sees the
// ones they care about.
const HIDDEN_KEYS = new Set([
  'editor.cursorMemory',           // huge map; not useful to display
  'session.last_location',         // implementation detail
])

const overrideEntries = computed(() => {
  const cache = userPrefs.cache.value || {}
  return Object.entries(cache)
    .filter(([k]) => !HIDDEN_KEYS.has(k) && !k.startsWith('_'))
    .map(([key, value]) => ({ key, preview: previewFor(value) }))
    .sort((a, b) => a.key.localeCompare(b.key))
})

function previewFor(v) {
  if (v == null) return '—'
  if (typeof v === 'string') return v.length > 60 ? v.slice(0, 57) + '…' : v
  if (typeof v === 'boolean' || typeof v === 'number') return String(v)
  try {
    const s = JSON.stringify(v)
    return s.length > 80 ? s.slice(0, 77) + '…' : s
  } catch {
    return '[object]'
  }
}

async function resetOverride(key) {
  if (!confirm(`Reset "${key}" to the global default?`)) return
  await userPrefs.remove(key)
}

async function saveDisplayProfile() {
  savingProfile.value = true
  displayProfileSaved.value = false
  try {
    await axios.patch('/api/users/me',
      { display_name: displayName.value, chip_color: chipColor.value },
      { headers: { Authorization: `Bearer ${localStorage.getItem('auth-token')}`, 'Content-Type': 'application/json' } }
    )
    _serverDisplayName.value = displayName.value
    _serverChipColor.value = chipColor.value
    // Sync the cached user-data so other components (PresenceMenu's "self"
    // row, MessagesPanel's currentUserId lookups) see the new values
    // without a page reload.
    try {
      const u = JSON.parse(localStorage.getItem('user-data') || '{}')
      u.display_name = displayName.value
      u.chip_color = chipColor.value
      localStorage.setItem('user-data', JSON.stringify(u))
      if (currentUser.value) {
        currentUser.value.display_name = displayName.value
        currentUser.value.chip_color = chipColor.value
      }
    } catch { /* noop */ }
    // Refresh the shared users list so PresenceMenu (this user's "self"
    // row and any open MessagesPanel) updates without waiting for the
    // 60s poll.
    try { messagesApi.fetchUsers() } catch { /* noop */ }
    displayProfileSaved.value = true
    setTimeout(() => { displayProfileSaved.value = false }, 3000)
  } catch (err) {
    console.error('Failed to save display profile:', err)
    alert('Save failed — see console.')
  } finally {
    savingProfile.value = false
  }
}

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

const handleLogout = () => {
  authLogout()
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
    return
  }
  loadDisplayProfile()
})
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

.color-swatch {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.12s ease, border-color 0.12s ease;
  padding: 0;
}

.color-swatch:hover {
  transform: scale(1.1);
}

.color-swatch.active {
  border-color: rgba(0, 0, 0, 0.7);
  box-shadow: 0 0 0 2px white inset;
}

.color-swatch-clear {
  background: white;
  border-color: rgba(0, 0, 0, 0.15);
}

.override-row {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
.override-row:last-child {
  border-bottom: none;
}
.override-key {
  background: rgba(0, 0, 0, 0.04);
  padding: 1px 6px;
  border-radius: 3px;
  font-family: 'Roboto Mono', monospace;
  font-size: 0.75rem;
}
</style>
