<template>
  <div>
    <h3 class="text-h6 mb-4">
      <v-icon class="me-2">mdi-music</v-icon>
      MP3 Encoding Profiles
    </h3>
    <p class="text-body-2 text-grey-darken-1 mb-4">
      Define encoding profiles for episode MP3 generation. The default profile will be used when no profile is specified.
    </p>

    <!-- Profile List -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title class="d-flex align-center py-2 px-4 bg-grey-lighten-4">
        <span class="text-subtitle-1 font-weight-bold">Profiles</span>
        <v-spacer />
        <v-btn
          size="small"
          color="primary"
          variant="flat"
          prepend-icon="mdi-plus"
          @click="openCreateDialog"
        >
          New Profile
        </v-btn>
      </v-card-title>

      <v-divider />

      <!-- Loading -->
      <div v-if="loading" class="pa-8 text-center">
        <v-progress-circular indeterminate color="primary" />
        <p class="mt-2 text-body-2 text-grey">Loading profiles...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="profiles.length === 0" class="pa-8 text-center">
        <v-icon size="48" color="grey-lighten-1">mdi-music-off</v-icon>
        <p class="mt-2 text-body-1 text-grey">No encoding profiles defined</p>
        <v-btn
          color="primary"
          variant="outlined"
          size="small"
          class="mt-2"
          @click="openCreateDialog"
        >
          Create First Profile
        </v-btn>
      </div>

      <!-- Profile Cards -->
      <v-list v-else lines="three" class="pa-0">
        <template v-for="(profile, idx) in profiles" :key="profile.id">
          <v-list-item
            :class="{ 'bg-blue-lighten-5': profile.is_default }"
            @click="openEditDialog(profile)"
          >
            <template v-slot:prepend>
              <v-icon :color="profile.is_default ? 'primary' : 'grey'">
                {{ profile.is_default ? 'mdi-star' : 'mdi-music-note' }}
              </v-icon>
            </template>

            <v-list-item-title class="font-weight-bold">
              {{ profile.name }}
              <v-chip
                v-if="profile.is_default"
                size="x-small"
                color="primary"
                class="ms-2"
              >
                Default
              </v-chip>
              <v-chip
                v-if="!profile.is_active"
                size="x-small"
                color="warning"
                class="ms-2"
              >
                Inactive
              </v-chip>
            </v-list-item-title>

            <v-list-item-subtitle>
              {{ profile.description || 'No description' }}
            </v-list-item-subtitle>

            <v-list-item-subtitle class="mt-1">
              <v-chip size="x-small" variant="outlined" class="me-1">
                {{ profile.bitrate }}
              </v-chip>
              <v-chip size="x-small" variant="outlined" class="me-1">
                {{ profile.sample_rate }} Hz
              </v-chip>
              <v-chip size="x-small" variant="outlined" class="me-1">
                {{ profile.channels === 1 ? 'Mono' : 'Stereo' }}
              </v-chip>
              <v-chip v-if="profile.quality !== null && profile.quality !== undefined" size="x-small" variant="outlined" class="me-1">
                VBR Q{{ profile.quality }}
              </v-chip>
              <v-chip v-if="profile.normalize_audio" size="x-small" variant="outlined" color="info" class="me-1">
                Normalized
              </v-chip>
            </v-list-item-subtitle>

            <template v-slot:append>
              <v-menu>
                <template v-slot:activator="{ props: menuProps }">
                  <v-btn
                    icon="mdi-dots-vertical"
                    variant="text"
                    size="small"
                    v-bind="menuProps"
                    @click.stop
                  />
                </template>
                <v-list density="compact">
                  <v-list-item @click="openEditDialog(profile)">
                    <template v-slot:prepend>
                      <v-icon size="small">mdi-pencil</v-icon>
                    </template>
                    <v-list-item-title>Edit</v-list-item-title>
                  </v-list-item>
                  <v-list-item
                    v-if="!profile.is_default"
                    @click="setDefault(profile)"
                  >
                    <template v-slot:prepend>
                      <v-icon size="small">mdi-star</v-icon>
                    </template>
                    <v-list-item-title>Set as Default</v-list-item-title>
                  </v-list-item>
                  <v-divider />
                  <v-list-item
                    @click="confirmDelete(profile)"
                    class="text-error"
                  >
                    <template v-slot:prepend>
                      <v-icon size="small" color="error">mdi-delete</v-icon>
                    </template>
                    <v-list-item-title>Delete</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-menu>
            </template>
          </v-list-item>
          <v-divider v-if="idx < profiles.length - 1" />
        </template>
      </v-list>
    </v-card>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="showEditDialog" max-width="550" persistent>
      <v-card>
        <v-card-title class="bg-primary text-white d-flex align-center">
          <v-icon class="me-2">{{ editingProfile.id ? 'mdi-pencil' : 'mdi-plus' }}</v-icon>
          {{ editingProfile.id ? 'Edit Profile' : 'New Profile' }}
        </v-card-title>
        <v-card-text class="pa-4">
          <v-text-field
            v-model="editingProfile.name"
            label="Profile Name"
            placeholder="e.g., Podcast Standard"
            variant="outlined"
            density="comfortable"
            :rules="[v => !!v || 'Name is required']"
            class="mb-2"
          />

          <v-textarea
            v-model="editingProfile.description"
            label="Description"
            placeholder="Optional description of this profile's use case"
            variant="outlined"
            density="comfortable"
            rows="2"
            class="mb-2"
          />

          <v-divider class="my-3" />
          <p class="text-subtitle-2 font-weight-bold mb-3">Encoding Parameters</p>

          <v-row>
            <v-col cols="6">
              <v-select
                v-model="editingProfile.bitrate"
                label="Bitrate"
                :items="bitrateOptions"
                variant="outlined"
                density="comfortable"
              />
            </v-col>
            <v-col cols="6">
              <v-select
                v-model="editingProfile.sample_rate"
                label="Sample Rate"
                :items="sampleRateOptions"
                item-title="title"
                item-value="value"
                variant="outlined"
                density="comfortable"
              />
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="6">
              <v-select
                v-model="editingProfile.channels"
                label="Channels"
                :items="channelOptions"
                item-title="title"
                item-value="value"
                variant="outlined"
                density="comfortable"
              />
            </v-col>
            <v-col cols="6">
              <v-select
                v-model="editingProfile.quality"
                label="VBR Quality"
                :items="vbrOptions"
                item-title="title"
                item-value="value"
                variant="outlined"
                density="comfortable"
                clearable
                hint="Leave empty for constant bitrate (CBR)"
                persistent-hint
              />
            </v-col>
          </v-row>

          <v-switch
            v-model="editingProfile.normalize_audio"
            label="Normalize Audio (EBU R128 loudness)"
            color="primary"
            density="comfortable"
            hide-details
            class="mt-2"
          />

          <v-switch
            v-model="editingProfile.is_default"
            label="Set as default profile"
            color="primary"
            density="comfortable"
            hide-details
            class="mt-2"
          />

          <v-switch
            v-model="editingProfile.is_active"
            label="Active"
            color="primary"
            density="comfortable"
            hide-details
            class="mt-2"
          />
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="showEditDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            :loading="saving"
            :disabled="!editingProfile.name"
            @click="saveProfile"
          >
            {{ editingProfile.id ? 'Save Changes' : 'Create Profile' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="bg-error text-white">
          <v-icon class="me-2">mdi-delete</v-icon>
          Delete Profile
        </v-card-title>
        <v-card-text class="pa-4">
          Are you sure you want to delete <strong>{{ deletingProfile?.name }}</strong>?
          This action cannot be undone.
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">Cancel</v-btn>
          <v-btn
            color="error"
            variant="flat"
            :loading="deleting"
            @click="deleteProfile"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="showSnackbar" :color="snackbarColor" timeout="3000">
      {{ snackbarMessage }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, inject, onMounted } from 'vue'

const axios = inject('axios')

// State
const profiles = ref([])
const loading = ref(false)
const saving = ref(false)
const deleting = ref(false)
const showEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

const editingProfile = ref(getEmptyProfile())
const deletingProfile = ref(null)

// Options
const bitrateOptions = ['64k', '96k', '128k', '160k', '192k', '224k', '256k', '320k']

const sampleRateOptions = [
  { title: '22050 Hz', value: 22050 },
  { title: '44100 Hz', value: 44100 },
  { title: '48000 Hz', value: 48000 }
]

const channelOptions = [
  { title: 'Mono', value: 1 },
  { title: 'Stereo', value: 2 }
]

const vbrOptions = [
  { title: 'VBR 0 (Best)', value: 0 },
  { title: 'VBR 1', value: 1 },
  { title: 'VBR 2 (Recommended)', value: 2 },
  { title: 'VBR 3', value: 3 },
  { title: 'VBR 4', value: 4 },
  { title: 'VBR 5', value: 5 },
  { title: 'VBR 6', value: 6 },
  { title: 'VBR 7', value: 7 },
  { title: 'VBR 8', value: 8 },
  { title: 'VBR 9 (Worst)', value: 9 }
]

function getEmptyProfile() {
  return {
    id: null,
    name: '',
    description: '',
    bitrate: '192k',
    sample_rate: 44100,
    channels: 2,
    quality: null,
    normalize_audio: false,
    is_default: false,
    is_active: true,
    sort_order: 0
  }
}

// Load profiles
async function loadProfiles() {
  loading.value = true
  try {
    const response = await axios.get('/settings/mp3-profiles/')
    profiles.value = response.data
  } catch (error) {
    console.error('Failed to load MP3 profiles:', error)
    showNotification('Failed to load profiles', 'error')
  } finally {
    loading.value = false
  }
}

// Dialog handlers
function openCreateDialog() {
  editingProfile.value = getEmptyProfile()
  showEditDialog.value = true
}

function openEditDialog(profile) {
  editingProfile.value = { ...profile }
  showEditDialog.value = true
}

function confirmDelete(profile) {
  deletingProfile.value = profile
  showDeleteDialog.value = true
}

// CRUD operations
async function saveProfile() {
  saving.value = true
  try {
    if (editingProfile.value.id) {
      await axios.put(
        `/settings/mp3-profiles/${editingProfile.value.id}`,
        editingProfile.value
      )
      showNotification('Profile updated')
    } else {
      await axios.post('/settings/mp3-profiles/', editingProfile.value)
      showNotification('Profile created')
    }
    showEditDialog.value = false
    await loadProfiles()
  } catch (error) {
    const detail = error.response?.data?.detail || error.message
    showNotification(`Failed to save profile: ${detail}`, 'error')
  } finally {
    saving.value = false
  }
}

async function setDefault(profile) {
  try {
    await axios.put(`/settings/mp3-profiles/${profile.id}`, {
      is_default: true
    })
    showNotification(`"${profile.name}" set as default`)
    await loadProfiles()
  } catch (error) {
    showNotification('Failed to set default', 'error')
  }
}

async function deleteProfile() {
  deleting.value = true
  try {
    await axios.delete(`/settings/mp3-profiles/${deletingProfile.value.id}`)
    showNotification(`"${deletingProfile.value.name}" deleted`)
    showDeleteDialog.value = false
    deletingProfile.value = null
    await loadProfiles()
  } catch (error) {
    showNotification('Failed to delete profile', 'error')
  } finally {
    deleting.value = false
  }
}

function showNotification(message, color = 'success') {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

onMounted(() => {
  loadProfiles()
})
</script>
