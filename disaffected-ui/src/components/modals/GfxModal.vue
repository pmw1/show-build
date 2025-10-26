<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="900">
    <v-card>
      <v-card-title style="font-size: 1.3em; font-weight: bold;">ADD GRAPHICS (GFX) CUE</v-card-title>

      <!-- Tab Selector -->
      <v-tabs v-model="activeTab" bg-color="grey-lighten-3">
        <v-tab value="gfx">GFX</v-tab>
        <v-tab value="social">Social</v-tab>
        <v-tab value="infochart">Info and Chart</v-tab>
        <v-tab value="profiles">Profiles</v-tab>
        <v-tab value="custom">Custom Request</v-tab>
      </v-tabs>

      <v-card-text style="min-height: 400px; padding: 20px;">
        <!-- Hidden Fields (Required but not displayed) -->
        <input type="hidden" v-model="internalSlug" />
        <input type="hidden" v-model="internalDescription" />

        <!-- GFX Tab -->
        <v-window v-model="activeTab">
          <v-window-item value="gfx">
            <div class="tab-content">
              <h3 class="mb-3" style="font-size: 1.1em; font-weight: 600;">Generate Graphics</h3>
              <p class="text-caption mb-4" style="color: #666;">
                GFX content is for graphics that need to be generated: guest teasers, infographics, charts, social media full screens, etc.
                <strong>Note:</strong> Copied images are IMG content, not GFX.
              </p>
            </div>
          </v-window-item>

          <!-- Social Tab -->
          <v-window-item value="social">
            <div class="tab-content">
              <h3 class="mb-3" style="font-size: 1.1em; font-weight: 600;">Social Media Graphics</h3>
              <p class="text-caption mb-4" style="color: #666;">
                Generate graphics optimized for social media platforms.
              </p>

              <!-- Platform Selector -->
              <div class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Platform:</label>
                <v-btn-toggle v-model="socialPlatform" mandatory color="primary" class="d-flex flex-wrap" style="gap: 8px;">
                  <v-btn value="twitter" size="small">Twitter/X</v-btn>
                  <v-btn value="facebook" size="small">Facebook</v-btn>
                  <v-btn value="instagram" size="small">Instagram</v-btn>
                  <v-btn value="youtube" size="small">YouTube</v-btn>
                  <v-btn value="tiktok" size="small">TikTok</v-btn>
                </v-btn-toggle>
              </div>

              <!-- Twitter/X Specific Options -->
              <div v-if="socialPlatform === 'twitter'" class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Generate From:</label>
                <v-btn-toggle v-model="socialSourceType" mandatory color="primary" class="d-flex flex-wrap" style="gap: 8px;">
                  <v-btn value="profile" size="small" disabled style="opacity: 0.4;">Profile</v-btn>
                  <v-btn value="post" size="small">Post</v-btn>
                  <v-btn value="comment" size="small" disabled style="opacity: 0.4;">Comment</v-btn>
                </v-btn-toggle>
              </div>

              <!-- Facebook Specific Options -->
              <div v-if="socialPlatform === 'facebook'" class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Generate From:</label>
                <v-btn-toggle v-model="socialSourceType" mandatory color="primary" class="d-flex flex-wrap" style="gap: 8px;">
                  <v-btn value="profile" size="small" disabled style="opacity: 0.4;">Profile</v-btn>
                  <v-btn value="post" size="small">Post</v-btn>
                  <v-btn value="comment" size="small" disabled style="opacity: 0.4;">Comment</v-btn>
                </v-btn-toggle>
              </div>

              <!-- Instagram Specific Options -->
              <div v-if="socialPlatform === 'instagram'" class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Generate From:</label>
                <v-btn-toggle v-model="socialSourceType" mandatory color="primary" class="d-flex flex-wrap" style="gap: 8px;">
                  <v-btn value="profile" size="small" disabled style="opacity: 0.4;">Profile</v-btn>
                  <v-btn value="post" size="small">Post</v-btn>
                  <v-btn value="comment" size="small" disabled style="opacity: 0.4;">Comment</v-btn>
                </v-btn-toggle>
              </div>

              <!-- YouTube Specific Options -->
              <div v-if="socialPlatform === 'youtube'" class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Generate From:</label>
                <v-btn-toggle v-model="socialSourceType" mandatory color="primary" class="d-flex flex-wrap" style="gap: 8px;">
                  <v-btn value="channel" size="small" disabled style="opacity: 0.4;">Channel</v-btn>
                  <v-btn value="video" size="small">Video</v-btn>
                  <v-btn value="comment" size="small" disabled style="opacity: 0.4;">Comment</v-btn>
                </v-btn-toggle>
              </div>

              <!-- TikTok Specific Options -->
              <div v-if="socialPlatform === 'tiktok'" class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Generate From:</label>
                <v-btn-toggle v-model="socialSourceType" mandatory color="primary" class="d-flex flex-wrap" style="gap: 8px;">
                  <v-btn value="profile" size="small" disabled style="opacity: 0.4;">Profile</v-btn>
                  <v-btn value="video" size="small">Video</v-btn>
                  <v-btn value="comment" size="small" disabled style="opacity: 0.4;">Comment</v-btn>
                </v-btn-toggle>
              </div>

              <!-- Social Media URL Input (for all platforms when post/video is selected) -->
              <div v-if="shouldShowUrlInput" class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">{{ urlInputLabel }}:</label>
                <v-text-field
                  v-model="socialPostUrl"
                  :placeholder="urlInputPlaceholder"
                  variant="outlined"
                  density="compact"
                  :hint="urlInputHint"
                  persistent-hint
                ></v-text-field>
              </div>

              <!-- Aspect Ratio -->
              <div class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Aspect Ratio:</label>
                <v-btn-toggle v-model="aspectRatio" mandatory color="primary">
                  <v-btn value="16:9" size="small">16:9</v-btn>
                  <v-btn value="1:1" size="small">1:1 (Square)</v-btn>
                  <v-btn value="9:16" size="small">9:16 (Vertical)</v-btn>
                  <v-btn value="4:5" size="small">4:5</v-btn>
                </v-btn-toggle>
              </div>

              <!-- Content Fields (only show if no URL input) -->
              <div v-if="!shouldShowUrlInput" class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Headline:</label>
                <v-text-field
                  v-model="socialHeadline"
                  placeholder="Enter headline text"
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </div>

              <div v-if="!shouldShowUrlInput" class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Subtext (optional):</label>
                <v-textarea
                  v-model="socialSubtext"
                  placeholder="Enter additional text"
                  rows="3"
                  variant="outlined"
                ></v-textarea>
              </div>
            </div>
          </v-window-item>

          <!-- Info and Chart Tab -->
          <v-window-item value="infochart">
            <div class="tab-content">
              <h3 class="mb-3" style="font-size: 1.1em; font-weight: 600;">Infographics & Charts</h3>
              <p class="text-caption mb-4" style="color: #666;">
                Create data visualizations, charts, and informational graphics.
              </p>

              <!-- Chart Type -->
              <div class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Chart Type:</label>
                <v-select
                  v-model="chartType"
                  :items="['Bar Chart', 'Line Chart', 'Pie Chart', 'Area Chart', 'Scatter Plot', 'Infographic']"
                  placeholder="Select chart type"
                  variant="outlined"
                  density="compact"
                ></v-select>
              </div>

              <!-- Data Input -->
              <div class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Data (CSV or JSON):</label>
                <v-textarea
                  v-model="chartData"
                  placeholder="Paste CSV data or JSON array"
                  rows="8"
                  variant="outlined"
                ></v-textarea>
              </div>

              <!-- Chart Title -->
              <div class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Chart Title:</label>
                <v-text-field
                  v-model="chartTitle"
                  placeholder="Enter chart title"
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </div>

              <!-- Color Scheme -->
              <div class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Color Scheme:</label>
                <v-btn-toggle v-model="colorScheme" mandatory color="primary">
                  <v-btn value="default" size="small">Default</v-btn>
                  <v-btn value="monochrome" size="small">Monochrome</v-btn>
                  <v-btn value="vibrant" size="small">Vibrant</v-btn>
                  <v-btn value="pastel" size="small">Pastel</v-btn>
                </v-btn-toggle>
              </div>
            </div>
          </v-window-item>

          <!-- Profiles Tab -->
          <v-window-item value="profiles">
            <div class="tab-content">
              <h3 class="mb-3" style="font-size: 1.1em; font-weight: 600;">Guest/Speaker Profiles</h3>
              <p class="text-caption mb-4" style="color: #666;">
                Generate guest profile cards, speaker introductions, and biographical graphics.
              </p>

              <!-- Profile Type -->
              <div class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Profile Type:</label>
                <v-btn-toggle v-model="profileType" mandatory color="primary">
                  <v-btn value="guest-card" size="small">Guest Card</v-btn>
                  <v-btn value="speaker-intro" size="small">Speaker Intro</v-btn>
                  <v-btn value="bio-slide" size="small">Bio Slide</v-btn>
                </v-btn-toggle>
              </div>

              <!-- Name -->
              <div class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Name:</label>
                <v-text-field
                  v-model="profileName"
                  placeholder="Enter guest/speaker name"
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </div>

              <!-- Title/Credentials -->
              <div class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Title/Credentials:</label>
                <v-text-field
                  v-model="profileTitle"
                  placeholder="e.g., PhD, CEO, Author"
                  variant="outlined"
                  density="compact"
                ></v-text-field>
              </div>

              <!-- Bio/Description -->
              <div class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Bio/Description:</label>
                <v-textarea
                  v-model="profileBio"
                  placeholder="Enter biographical information"
                  rows="4"
                  variant="outlined"
                ></v-textarea>
              </div>

              <!-- Photo Upload -->
              <div class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">Profile Photo:</label>
                <div class="d-flex" style="gap: 10px;">
                  <v-btn color="primary" size="small" @click="$emit('select-file')">Upload Photo</v-btn>
                  <v-btn color="secondary" size="small" @click="$emit('paste-from-clipboard')">Paste from Clipboard</v-btn>
                </div>
                <v-img
                  v-if="graphicPreview"
                  :src="graphicPreview"
                  max-height="150"
                  max-width="150"
                  class="mt-3"
                  style="border-radius: 8px;"
                ></v-img>
              </div>
            </div>
          </v-window-item>

          <!-- Custom Request Tab -->
          <v-window-item value="custom">
            <div class="tab-content">
              <h3 class="mb-3" style="font-size: 1.1em; font-weight: 600;">Custom Graphic Request</h3>
              <p class="text-caption mb-4" style="color: #666;">
                Submit a custom request for graphics that don't fit other categories.
              </p>
            </div>
          </v-window-item>
        </v-window>
      </v-card-text>

      <v-card-actions style="padding: 20px; border-top: 1px solid #e0e0e0;">
        <v-spacer></v-spacer>
        <v-btn color="error" variant="outlined" @click="$emit('update:show', false)">Cancel</v-btn>
        <v-btn
          color="success"
          variant="flat"
          @click="handleSubmit"
          :disabled="activeTab !== 'gfx'"
        >Generate & Attach</v-btn>
      </v-card-actions>
    </v-card>

    <!-- Not Implemented Dialog -->
    <v-dialog v-model="showNotImplementedDialog" max-width="400">
      <v-card>
        <v-card-title style="font-size: 1.2em; font-weight: bold; background: #ff9800; color: white;">
          Not Yet Implemented
        </v-card-title>
        <v-card-text style="padding: 20px; font-size: 1em;">
          This functionality hasn't yet been deployed.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="showNotImplementedDialog = false">OK</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script>
import { ref, computed } from 'vue'

export default {
  name: 'GfxModal',
  props: {
    show: { type: Boolean, required: true },
    slug: { type: String, default: '' },
    description: { type: String, default: '' },
    graphicPreview: { type: String, default: '' },
  },
  emits: [
    'update:show',
    'update:slug',
    'update:description',
    'paste-from-clipboard',
    'select-file',
    'paste-url',
    'submit',
  ],
  setup(props, { emit }) {
    const activeTab = ref('gfx')
    const showNotImplementedDialog = ref(false)

    // Hidden required fields
    const internalSlug = ref(props.slug)
    const internalDescription = ref(props.description)


    // Social Tab
    const socialPlatform = ref('twitter')
    const socialSourceType = ref('post')
    const socialPostUrl = ref('')
    const aspectRatio = ref('16:9')
    const socialHeadline = ref('')
    const socialSubtext = ref('')

    // Computed properties for URL input
    const shouldShowUrlInput = computed(() => {
      const isPost = ['post', 'video'].includes(socialSourceType.value)
      return isPost
    })

    const urlInputLabel = computed(() => {
      switch (socialPlatform.value) {
        case 'twitter': return 'X/Twitter Post URL'
        case 'facebook': return 'Facebook Post URL'
        case 'instagram': return 'Instagram Post URL'
        case 'youtube': return 'YouTube Video URL'
        case 'tiktok': return 'TikTok Video URL'
        default: return 'URL'
      }
    })

    const urlInputPlaceholder = computed(() => {
      switch (socialPlatform.value) {
        case 'twitter': return 'https://x.com/username/status/1234567890'
        case 'facebook': return 'https://www.facebook.com/username/posts/1234567890'
        case 'instagram': return 'https://www.instagram.com/p/ABC123DEF456/'
        case 'youtube': return 'https://www.youtube.com/watch?v=ABC123DEF456'
        case 'tiktok': return 'https://www.tiktok.com/@username/video/1234567890'
        default: return 'Enter URL'
      }
    })

    const urlInputHint = computed(() => {
      switch (socialPlatform.value) {
        case 'twitter': return 'Paste the direct URL to the X/Twitter post'
        case 'facebook': return 'Paste the direct URL to the Facebook post'
        case 'instagram': return 'Paste the direct URL to the Instagram post'
        case 'youtube': return 'Paste the direct URL to the YouTube video'
        case 'tiktok': return 'Paste the direct URL to the TikTok video'
        default: return 'Paste the URL'
      }
    })

    // Info and Chart Tab
    const chartType = ref(null)
    const chartData = ref('')
    const chartTitle = ref('')
    const colorScheme = ref('default')

    // Profiles Tab
    const profileType = ref('guest-card')
    const profileName = ref('')
    const profileTitle = ref('')
    const profileBio = ref('')

    const handleSubmit = () => {
      // Show not implemented dialog for non-GFX tabs
      if (activeTab.value !== 'gfx') {
        showNotImplementedDialog.value = true
        return
      }

      // Generate slug and description from tab data if not provided
      if (!internalSlug.value) {
        internalSlug.value = `gfx-${Date.now()}`
      }

      if (!internalDescription.value) {
        internalDescription.value = 'Generated graphic'
      }

      emit('update:slug', internalSlug.value)
      emit('update:description', internalDescription.value)
      emit('submit', {
        tab: activeTab.value,
        data: {}
      })
    }

    return {
      activeTab,
      showNotImplementedDialog,
      internalSlug,
      internalDescription,
      // Social
      socialPlatform,
      socialSourceType,
      socialPostUrl,
      aspectRatio,
      socialHeadline,
      socialSubtext,
      shouldShowUrlInput,
      urlInputLabel,
      urlInputPlaceholder,
      urlInputHint,
      // Info and Chart
      chartType,
      chartData,
      chartTitle,
      colorScheme,
      // Profiles
      profileType,
      profileName,
      profileTitle,
      profileBio,
      handleSubmit
    }
  }
}
</script>

<style scoped>
.tab-content {
  padding: 15px 0;
}

.v-btn-toggle {
  flex-wrap: wrap;
}

.preview-container {
  margin-top: 20px;
}
</style>
