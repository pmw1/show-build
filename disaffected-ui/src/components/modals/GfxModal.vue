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

              <!-- GFX Type Selector -->
              <div class="mb-4">
                <label class="d-block mb-2" style="font-size: 14px; font-weight: 500; color: #555;">GFX Type:</label>
                <v-btn-toggle v-model="gfxType" mandatory color="primary" class="d-flex flex-wrap" style="gap: 8px;">
                  <v-btn value="fullscreen-text" size="small">Full Screen Text (Generic)</v-btn>
                </v-btn-toggle>
              </div>

              <!-- Full Screen Text Interface -->
              <div v-if="gfxType === 'fullscreen-text'" class="fullscreen-text-interface">
                <!-- Large Preview Container -->
                <div class="gfx-preview-container mb-4">
                  <video
                    ref="previewVideoRef"
                    class="preview-video-background"
                    autoplay
                    loop
                    muted
                    playsinline
                  >
                    <source :src="previewBackgroundVideo" type="video/mp4">
                  </video>
                  <div class="black-bar-overlay"></div>
                  <div class="gfx-preview" :style="previewStyle">
                    <div v-if="gfxTitle" class="gfx-title" :style="titleStyle">{{ gfxTitle }}</div>
                    <div class="gfx-body" :style="bodyStyle" v-html="formattedBodyPreview"></div>
                  </div>
                </div>

                <!-- Title (Optional) -->
                <v-text-field
                  v-model="gfxTitle"
                  label="Title (Optional)"
                  placeholder="Enter title text..."
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                  class="mb-3"
                />

                <!-- Body Text -->
                <v-textarea
                  ref="bodyFieldRef"
                  v-model="gfxBody"
                  label="Body Text"
                  placeholder="Enter body text..."
                  variant="outlined"
                  rows="4"
                  auto-grow
                  :rules="bodyRules"
                  required
                  density="compact"
                  hide-details="auto"
                  class="mb-3"
                />

                <!-- Slug -->
                <v-text-field
                  v-model="gfxSlug"
                  label="Slug"
                  placeholder="short-slug"
                  variant="outlined"
                  :rules="slugRules"
                  required
                  density="compact"
                  hide-details="auto"
                  class="mb-3"
                  @blur="normalizeSlug"
                />

                <v-divider class="mb-3"></v-divider>

                <!-- Style Settings -->
                <div class="style-settings">
                  <div class="text-caption text-grey mb-2">STYLE SETTINGS</div>
                  <v-row dense class="mb-2">
                    <v-col cols="4">
                      <v-text-field
                        v-model.number="fontSize"
                        label="Size"
                        type="number"
                        variant="outlined"
                        density="compact"
                        hide-details
                        suffix="px"
                        min="10"
                        max="50"
                      />
                    </v-col>
                    <v-col cols="8">
                      <v-select
                        v-model="fontFamily"
                        :items="fontOptions"
                        label="Font"
                        variant="outlined"
                        density="compact"
                        hide-details
                      />
                    </v-col>
                  </v-row>
                  <v-row dense class="mb-2">
                    <v-col cols="12">
                      <v-btn-toggle
                        v-model="textAlign"
                        mandatory
                        density="compact"
                        color="primary"
                        class="w-100"
                      >
                        <v-btn value="left" size="small" class="flex-grow-1">
                          <v-icon size="small">mdi-format-align-left</v-icon>
                        </v-btn>
                        <v-btn value="center" size="small" class="flex-grow-1">
                          <v-icon size="small">mdi-format-align-center</v-icon>
                        </v-btn>
                        <v-btn value="right" size="small" class="flex-grow-1">
                          <v-icon size="small">mdi-format-align-right</v-icon>
                        </v-btn>
                      </v-btn-toggle>
                    </v-col>
                  </v-row>
                </div>

                <!-- Render Mode -->
                <div class="render-mode-section mt-3">
                  <div class="text-caption text-grey mb-2">OUTPUT</div>
                  <v-btn-toggle
                    v-model="renderMode"
                    mandatory
                    density="compact"
                    color="lime"
                    class="w-100"
                  >
                    <v-btn value="png" size="small" class="flex-grow-1">
                      <v-icon size="small" class="mr-1">mdi-file-image</v-icon>
                      PNG
                    </v-btn>
                    <v-btn value="video" size="small" class="flex-grow-1">
                      <v-icon size="small" class="mr-1">mdi-video</v-icon>
                      Video
                    </v-btn>
                  </v-btn-toggle>
                </div>
              </div>
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
          color="primary"
          variant="outlined"
          @click="handleInsertOnly"
          :disabled="activeTab !== 'gfx' || (gfxType === 'fullscreen-text' && (!gfxBody || gfxBody.length < 5))"
        >
          <v-icon size="small" class="mr-1">mdi-text-box-plus</v-icon>
          Insert Cue Only
        </v-btn>
        <v-btn
          color="success"
          variant="flat"
          @click="handleSubmit"
          :disabled="activeTab !== 'gfx' || (gfxType === 'fullscreen-text' && (!gfxBody || gfxBody.length < 5))"
          :loading="loading"
        >
          <v-icon size="small" class="mr-1">mdi-creation</v-icon>
          Generate & Insert
        </v-btn>
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
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import axios from 'axios'

export default {
  name: 'GfxModal',
  props: {
    show: { type: Boolean, required: true },
    slug: { type: String, default: '' },
    description: { type: String, default: '' },
    graphicPreview: { type: String, default: '' },
    currentEpisode: { type: String, default: '' },
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
    const loading = ref(false)
    const previewVideoRef = ref(null)
    const bodyFieldRef = ref(null)

    // GFX Type selector
    const gfxType = ref('fullscreen-text')

    // Full Screen Text fields
    const gfxTitle = ref('')
    const gfxBody = ref('')
    const gfxSlug = ref('')

    // Style settings
    const fontSize = ref(25)
    const fontFamily = ref('sans-serif')
    const textAlign = ref('center')
    const renderMode = ref('png')

    // Preview background
    const previewBackgroundVideo = ref('/assets/preview-background.mp4')

    // Validation rules
    const bodyRules = [
      v => !!v || 'Body text is required',
      v => !v || v.length >= 5 || 'Body must be at least 5 characters'
    ]

    const slugRules = [
      v => !!v || 'Slug is required'
    ]

    // Font options
    const fontOptions = [
      { title: 'Sans Serif (Helvetica)', value: 'sans-serif' },
      { title: 'Serif (Georgia)', value: 'serif' },
      { title: 'Monospace (Courier)', value: 'monospace' }
    ]

    // ESC key handler
    const handleKeydown = (event) => {
      if (event.key === 'Escape' && props.show) {
        event.preventDefault()
        event.stopPropagation()
        emit('update:show', false)
      }
    }

    // Lifecycle hooks for ESC handling
    onMounted(() => {
      document.addEventListener('keydown', handleKeydown)
    })
    onBeforeUnmount(() => {
      document.removeEventListener('keydown', handleKeydown)
    })

    // Watch for modal open to focus body field
    watch(() => props.show, async (newVal) => {
      if (newVal) {
        await nextTick()
        if (bodyFieldRef.value) {
          bodyFieldRef.value.focus()
        }
        // Start video preview
        if (previewVideoRef.value) {
          previewVideoRef.value.load()
          previewVideoRef.value.play().catch(err => {
            console.warn('Video autoplay prevented:', err)
          })
        }
      }
    })

    // Auto-generate slug from body text
    watch(gfxBody, (newVal) => {
      if (newVal && !gfxSlug.value) {
        const words = newVal.trim().split(/\s+/).slice(0, 3)
        gfxSlug.value = words
          .join(' ')
          .toLowerCase()
          .replace(/[^a-z0-9\s-]/g, '')
          .replace(/\s+/g, '-')
          .replace(/-+/g, '-')
          .replace(/^-+|-+$/g, '')
      }
    })

    // Normalize slug on blur
    const normalizeSlug = () => {
      if (!gfxSlug.value) return
      gfxSlug.value = gfxSlug.value
        .toLowerCase()
        .trim()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-+|-+$/g, '')
        .substring(0, 50)
    }

    // Hidden required fields
    const internalSlug = ref(props.slug)
    const internalDescription = ref(props.description)

    // Computed: preview style
    const previewStyle = computed(() => ({
      alignItems: textAlign.value === 'center' ? 'center' :
                 textAlign.value === 'left' ? 'flex-start' :
                 textAlign.value === 'right' ? 'flex-end' : 'center'
    }))

    // Computed: title style
    const titleStyle = computed(() => {
      const fontMap = {
        'sans-serif': 'Helvetica, Arial, sans-serif',
        'serif': 'Georgia, "Times New Roman", serif',
        'monospace': '"Courier New", Courier, monospace'
      }
      const fontSizeVw = ((fontSize.value + 8) / 1920) * 100  // Title slightly larger
      return {
        fontFamily: fontMap[fontFamily.value] || fontMap['sans-serif'],
        fontSize: `${fontSizeVw}vw`,
        fontWeight: 'bold',
        textAlign: textAlign.value,
        marginBottom: '0.5em'
      }
    })

    // Computed: body style
    const bodyStyle = computed(() => {
      const fontMap = {
        'sans-serif': 'Helvetica, Arial, sans-serif',
        'serif': 'Georgia, "Times New Roman", serif',
        'monospace': '"Courier New", Courier, monospace'
      }
      const fontSizeVw = (fontSize.value / 1920) * 100
      return {
        fontFamily: fontMap[fontFamily.value] || fontMap['sans-serif'],
        fontSize: `${fontSizeVw}vw`,
        textAlign: textAlign.value
      }
    })

    // Computed: formatted body preview
    const formattedBodyPreview = computed(() => {
      const rawText = gfxBody.value || 'Body text will appear here...'
      return rawText
        .replace(/&/g, '&amp;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>')
    })

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

    // Generate AssetID
    const generateAssetId = async () => {
      try {
        const formData = new FormData()
        formData.append('slug', gfxSlug.value || 'gfx-text')
        formData.append('type', 'gfx')

        const response = await axios.post('/assetid/generate-legacy', formData, {
          headers: {
            'Accept': 'application/json',
            'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
          }
        })

        if (response.data && response.data.id) {
          return response.data.id
        }
        throw new Error('Invalid response')
      } catch (error) {
        console.warn('AssetID generation failed, using fallback:', error)
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        let result = 'LOCAL_GFX_'
        for (let i = 0; i < 8; i++) {
          result += chars.charAt(Math.floor(Math.random() * chars.length))
        }
        return result
      }
    }

    // Reset form
    const resetForm = () => {
      gfxTitle.value = ''
      gfxBody.value = ''
      gfxSlug.value = ''
      fontSize.value = 25
      fontFamily.value = 'sans-serif'
      textAlign.value = 'center'
      renderMode.value = 'png'
    }

    // Insert cue only (without generating the graphic)
    const handleInsertOnly = async () => {
      // Validate fullscreen-text
      if (gfxType.value === 'fullscreen-text') {
        if (!gfxBody.value || gfxBody.value.trim().length < 5) {
          console.warn('Body text required')
          return
        }
        if (!gfxSlug.value) {
          console.warn('Slug required')
          return
        }

        try {
          const assetId = await generateAssetId()

          // Build cue data without generating graphic
          const cueData = {
            type: 'GFX',
            gfxType: gfxType.value,
            assetId: assetId,
            slug: gfxSlug.value,
            title: gfxTitle.value || null,
            body: gfxBody.value,
            style: {
              fontSize: fontSize.value,
              fontFamily: fontFamily.value,
              textAlign: textAlign.value
            },
            renderMode: renderMode.value,
            status: 'pending'  // Mark as pending since graphic not yet generated
          }

          console.log('📝 Inserting GFX cue only (no generation):', cueData)
          emit('submit', cueData)

          resetForm()
          emit('update:show', false)

        } catch (error) {
          console.error('Error creating GFX cue:', error)
        }
      }
    }

    const handleSubmit = async () => {
      // Show not implemented dialog for non-GFX tabs
      if (activeTab.value !== 'gfx') {
        showNotImplementedDialog.value = true
        return
      }

      // Validate fullscreen-text
      if (gfxType.value === 'fullscreen-text') {
        if (!gfxBody.value || gfxBody.value.trim().length < 5) {
          console.warn('Body text required')
          return
        }
        if (!gfxSlug.value) {
          console.warn('Slug required')
          return
        }

        loading.value = true

        try {
          const assetId = await generateAssetId()

          // Call GFX generation API
          console.log('🎨 Submitting GFX to Celery...')
          const response = await axios.post('/api/gfx/generate', {
            episode_id: props.currentEpisode || '0000',
            gfx_type: gfxType.value,
            body: gfxBody.value,
            slug: gfxSlug.value,
            asset_id: assetId,
            title: gfxTitle.value || null,
            alignment: textAlign.value,
            font_family: fontFamily.value,
            font_size: fontSize.value,
            render_mode: renderMode.value,
            priority: 'high'
          }, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
            }
          })

          console.log('✅ GFX generated:', response.data)

          // Build cue data with asset info
          const cueData = {
            type: 'GFX',
            gfxType: gfxType.value,
            assetId: assetId,
            slug: gfxSlug.value,
            title: gfxTitle.value || null,
            body: gfxBody.value,
            style: {
              fontSize: fontSize.value,
              fontFamily: fontFamily.value,
              textAlign: textAlign.value
            },
            renderMode: renderMode.value,
            assetUrl: response.data.asset_url,
            assetPath: response.data.asset_path
          }

          emit('submit', cueData)

          resetForm()
          emit('update:show', false)

        } catch (error) {
          console.error('Error creating GFX:', error)
          // Still emit the cue data even if generation fails (can regenerate later)
          if (error.response?.status === 202) {
            // Task is still running - proceed with basic cue data
            console.log('GFX generation in progress, proceeding with cue insertion')
            const assetId = await generateAssetId()
            emit('submit', {
              type: 'GFX',
              gfxType: gfxType.value,
              assetId: assetId,
              slug: gfxSlug.value,
              title: gfxTitle.value || null,
              body: gfxBody.value,
              style: {
                fontSize: fontSize.value,
                fontFamily: fontFamily.value,
                textAlign: textAlign.value
              },
              renderMode: renderMode.value,
              status: 'pending'
            })
            resetForm()
            emit('update:show', false)
          }
        } finally {
          loading.value = false
        }
        return
      }

      // Legacy submit for other tabs
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
      loading,
      previewVideoRef,
      bodyFieldRef,
      internalSlug,
      internalDescription,
      // GFX Type
      gfxType,
      // Full Screen Text
      gfxTitle,
      gfxBody,
      gfxSlug,
      fontSize,
      fontFamily,
      textAlign,
      renderMode,
      previewBackgroundVideo,
      bodyRules,
      slugRules,
      fontOptions,
      previewStyle,
      titleStyle,
      bodyStyle,
      formattedBodyPreview,
      normalizeSlug,
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
      handleSubmit,
      handleInsertOnly
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

/* GFX Preview Container - 16:9 aspect ratio */
.gfx-preview-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 4px;
  overflow: hidden;
  background: #000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.gfx-preview-container .preview-video-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}

.gfx-preview-container .black-bar-overlay {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  background: rgba(0, 0, 0, 0.75);
  z-index: 2;
  pointer-events: none;
}

.gfx-preview-container .gfx-preview {
  position: absolute;
  top: 10%;
  left: 0;
  width: 100%;
  height: 80%;
  color: white;
  padding: 8% 8% 15% 8%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  z-index: 3;
  box-sizing: border-box;
}

.gfx-title {
  color: white;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
  line-height: 1.3;
}

.gfx-body {
  color: white;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
  line-height: 1.4;
}

/* Style settings section */
.style-settings {
  background: rgba(255, 255, 255, 0.03);
  padding: 12px;
  border-radius: 4px;
}

/* Render mode section */
.render-mode-section {
  background: rgba(255, 255, 255, 0.03);
  padding: 12px;
  border-radius: 4px;
}

/* Full screen text interface */
.fullscreen-text-interface {
  margin-top: 8px;
}
</style>
