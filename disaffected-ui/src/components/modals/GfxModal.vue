<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="1100" persistent>
    <v-card class="gfx-modal-card">
      <v-card-title class="d-flex align-center text-black py-2" :class="`bg-${cueTypeColor}`">
        <v-icon class="mr-2" size="small">mdi-image-multiple</v-icon>
        <span class="text-body-1">Graphics (GFX)</span>
        <v-spacer></v-spacer>
        <v-btn icon size="x-small" variant="text" @click="cancel" color="black">
          <v-icon size="small">mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <!-- Tab Selector -->
      <v-tabs v-model="activeTab" density="compact" bg-color="grey-lighten-4" :color="cueTypeColor">
        <v-tab value="gfx">GFX</v-tab>
        <v-tab value="social">Social</v-tab>
        <v-tab value="infochart" disabled>
          Info/Chart
          <v-tooltip activator="parent" location="bottom">Coming soon</v-tooltip>
        </v-tab>
        <v-tab value="profiles" disabled>
          Profiles
          <v-tooltip activator="parent" location="bottom">Coming soon</v-tooltip>
        </v-tab>
        <v-tab value="custom" disabled>
          Custom
          <v-tooltip activator="parent" location="bottom">Coming soon</v-tooltip>
        </v-tab>
      </v-tabs>

      <v-card-text class="pb-2 compact-gfx-modal pa-3">
        <v-form ref="gfxFormRef" v-model="formValid">
          <v-window v-model="activeTab">

            <!-- ============ GFX TAB ============ -->
            <v-window-item value="gfx">
              <!-- GFX Type Selector -->
              <div class="d-flex align-center mb-3 mt-1" style="gap: 8px;">
                <span class="text-caption text-grey text-uppercase" style="font-weight: 600;">Type:</span>
                <v-btn-toggle v-model="gfxType" mandatory density="compact" color="cyan">
                  <v-btn value="fullscreen-text" size="small">
                    <v-icon size="small" start>mdi-text-box</v-icon>
                    Full Screen Text
                  </v-btn>
                  <v-btn value="title-card" size="small">
                    <v-icon size="small" start>mdi-card-text</v-icon>
                    Title Card
                  </v-btn>
                </v-btn-toggle>
              </div>

              <!-- TWO-COLUMN LAYOUT -->
              <v-row dense>
                <!-- LEFT COLUMN: Preview -->
                <v-col cols="7">
                  <div class="gfx-preview-container mb-2">
                    <video
                      ref="previewVideoRef"
                      class="preview-video-background"
                      autoplay
                      loop
                      muted
                      playsinline
                      @loadeddata="handleVideoLoaded"
                      @error="handleVideoError"
                    >
                      <source :src="previewBackgroundVideo" type="video/mp4">
                    </video>
                    <div class="black-bar-overlay"></div>
                    <div class="gfx-preview" :style="previewStyle">
                      <!-- Full Screen Text mode -->
                      <template v-if="gfxType === 'fullscreen-text'">
                        <div v-if="gfxTitle" class="gfx-title" :style="titleStyle">{{ gfxTitle }}</div>
                        <div class="gfx-body" :style="bodyStyle" v-html="formattedBodyPreview"></div>
                      </template>
                      <!-- Title Card mode -->
                      <template v-else-if="gfxType === 'title-card'">
                        <div class="gfx-title-card-text" :style="titleCardStyle">{{ titleCardText || 'Title Card Text' }}</div>
                      </template>
                    </div>
                  </div>

                  <!-- Character count below preview -->
                  <div class="d-flex align-center justify-space-between mb-2">
                    <div v-if="activeTextContent.length > 0" class="d-inline-flex">
                      <v-chip size="x-small" color="grey-darken-2">{{ activeTextContent.trim().split(/\s+/).filter(w => w.length > 0).length }} words</v-chip>
                    </div>
                    <v-chip v-if="gfxType" size="x-small" variant="outlined" :color="cueTypeColor">{{ gfxTypeLabel }}</v-chip>
                  </div>
                </v-col>

                <!-- RIGHT COLUMN: Controls -->
                <v-col cols="5">
                  <!-- Full Screen Text Controls -->
                  <template v-if="gfxType === 'fullscreen-text'">
                    <v-text-field
                      v-model="gfxTitle"
                      label="Title (Optional)"
                      placeholder="Enter title text..."
                      variant="outlined"
                      density="compact"
                      hide-details="auto"
                      class="mb-2"
                    />
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
                      class="mb-2"
                    />
                  </template>

                  <!-- Title Card Controls -->
                  <template v-if="gfxType === 'title-card'">
                    <v-text-field
                      ref="titleCardFieldRef"
                      v-model="titleCardText"
                      label="Title Card Text"
                      placeholder="Enter title text..."
                      variant="outlined"
                      density="compact"
                      hide-details="auto"
                      :rules="[v => !!v || 'Title text is required']"
                      required
                      class="mb-2"
                    />
                  </template>

                  <!-- Slug (shared) -->
                  <v-text-field
                    v-model="gfxSlug"
                    label="Slug"
                    placeholder="short-slug"
                    variant="outlined"
                    :rules="slugRules"
                    required
                    density="compact"
                    hide-details="auto"
                    class="mb-2"
                    @blur="normalizeSlug"
                  />

                  <v-divider class="mb-2"></v-divider>

                  <!-- Style Settings -->
                  <div class="style-settings mb-2">
                    <div class="text-caption text-grey mb-1">STYLE SETTINGS</div>
                    <v-row dense class="mb-1">
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
                          max="60"
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
                    <v-row dense class="mb-1">
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
                  <div class="render-mode-section mb-2">
                    <div class="text-caption text-grey mb-1">OUTPUT</div>
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

                  <!-- Action Buttons -->
                  <div class="mt-2">
                    <v-btn
                      block
                      color="primary"
                      variant="outlined"
                      @click="handleInsertOnly"
                      :disabled="!canSubmitGfx"
                      class="mb-1"
                      size="default"
                    >
                      <v-icon size="small" class="mr-1">mdi-text-box-plus</v-icon>
                      Insert Cue Only
                    </v-btn>
                    <v-btn
                      block
                      color="success"
                      variant="elevated"
                      @click="handleSubmit"
                      :disabled="!canSubmitGfx"
                      :loading="loading"
                      size="default"
                    >
                      <v-icon size="small" class="mr-1">mdi-creation</v-icon>
                      Generate &amp; Insert
                    </v-btn>
                  </div>
                </v-col>
              </v-row>
            </v-window-item>

            <!-- ============ SOCIAL TAB ============ -->
            <v-window-item value="social">
              <div class="tab-content">
                <!-- Platform Selector -->
                <div class="mb-3">
                  <div class="text-caption text-grey mb-1 text-uppercase" style="font-weight: 600;">Platform</div>
                  <v-btn-toggle v-model="socialPlatform" mandatory color="primary" density="compact" class="d-flex flex-wrap" style="gap: 4px;">
                    <v-btn value="twitter" size="small">Twitter/X</v-btn>
                    <v-btn value="facebook" size="small">Facebook</v-btn>
                    <v-btn value="instagram" size="small">Instagram</v-btn>
                    <v-btn value="youtube" size="small">YouTube</v-btn>
                    <v-btn value="tiktok" size="small">TikTok</v-btn>
                  </v-btn-toggle>
                </div>

                <!-- Source Type (consolidated for all platforms) -->
                <div class="mb-3">
                  <div class="text-caption text-grey mb-1 text-uppercase" style="font-weight: 600;">Generate From</div>
                  <v-btn-toggle v-model="socialSourceType" mandatory color="primary" density="compact" class="d-flex flex-wrap" style="gap: 4px;">
                    <v-btn value="profile" size="small" :disabled="socialPlatform === 'youtube'">Profile</v-btn>
                    <v-btn :value="socialPlatform === 'youtube' || socialPlatform === 'tiktok' ? 'video' : 'post'" size="small">
                      {{ socialPlatform === 'youtube' || socialPlatform === 'tiktok' ? 'Video' : 'Post' }}
                    </v-btn>
                    <v-btn value="comment" size="small" disabled>Comment</v-btn>
                  </v-btn-toggle>
                </div>

                <!-- URL Input -->
                <div v-if="shouldShowUrlInput" class="mb-3">
                  <v-text-field
                    v-model="socialPostUrl"
                    :label="urlInputLabel"
                    :placeholder="urlInputPlaceholder"
                    variant="outlined"
                    density="compact"
                    :hint="urlInputHint"
                    persistent-hint
                  ></v-text-field>

                  <!-- Whiteboard X Posts Selector (Twitter/X only) -->
                  <div v-if="socialPlatform === 'twitter'" class="mt-3">
                    <div class="xpost-divider">
                      <v-divider></v-divider>
                      <span class="xpost-divider-text">OR select from cached X posts</span>
                      <v-divider></v-divider>
                    </div>

                    <v-select
                      v-model="selectedWhiteboardXPost"
                      :items="whiteboardXPosts"
                      item-title="displayLabel"
                      item-value="id"
                      return-object
                      variant="outlined"
                      density="compact"
                      placeholder="Select a cached X post..."
                      :loading="loadingWhiteboardPosts"
                      :no-data-text="currentEpisode ? 'No X posts found on this episode\'s whiteboard' : 'No episode selected'"
                      class="mt-2"
                      clearable
                      @update:model-value="handleXPostSelected"
                    >
                      <template v-slot:item="{ props: itemProps, item }">
                        <v-list-item v-bind="itemProps" :subtitle="item.raw.subtitle" class="xpost-list-item">
                          <template v-slot:prepend>
                            <v-avatar size="32" class="mr-2">
                              <v-img v-if="item.raw.authorAvatar" :src="item.raw.authorAvatar" />
                              <v-icon v-else>mdi-twitter</v-icon>
                            </v-avatar>
                          </template>
                        </v-list-item>
                      </template>
                      <template v-slot:selection="{ item }">
                        <div class="d-flex align-center">
                          <v-avatar size="24" class="mr-2">
                            <v-img v-if="item.raw.authorAvatar" :src="item.raw.authorAvatar" />
                            <v-icon v-else size="16">mdi-twitter</v-icon>
                          </v-avatar>
                          <span class="text-truncate" style="max-width: 500px;">{{ item.raw.displayLabel }}</span>
                        </div>
                      </template>
                    </v-select>

                    <!-- Selected X Post Preview -->
                    <v-card v-if="selectedXPostData" variant="outlined" class="mt-2 xpost-preview-card">
                      <v-card-text class="pa-3">
                        <div class="d-flex align-start">
                          <v-avatar size="40" class="mr-3 flex-shrink-0">
                            <v-img v-if="selectedXPostData.author_avatar" :src="selectedXPostData.author_avatar" />
                            <v-icon v-else>mdi-twitter</v-icon>
                          </v-avatar>
                          <div class="flex-grow-1" style="min-width: 0;">
                            <div class="d-flex align-center mb-1">
                              <strong class="mr-1">{{ selectedXPostData.author_name }}</strong>
                              <v-icon v-if="selectedXPostData.author_verified" size="14" color="blue">mdi-check-decagram</v-icon>
                              <span class="text-grey ml-1 text-caption">@{{ selectedXPostData.author_handle }}</span>
                            </div>
                            <p class="mb-2 text-body-2" style="white-space: pre-wrap; word-break: break-word;">{{ selectedXPostData.tweet_text }}</p>
                            <div v-if="selectedXPostData.media_urls && selectedXPostData.media_urls.length" class="mb-2">
                              <v-img :src="selectedXPostData.media_urls[0]" max-height="150" class="rounded" cover />
                              <span v-if="selectedXPostData.media_urls.length > 1" class="text-caption text-grey">
                                +{{ selectedXPostData.media_urls.length - 1 }} more media
                              </span>
                            </div>
                            <div class="d-flex text-caption text-grey" style="gap: 16px;">
                              <span v-if="selectedXPostData.replies"><v-icon size="14" class="mr-1">mdi-comment-outline</v-icon>{{ selectedXPostData.replies }}</span>
                              <span v-if="selectedXPostData.retweets"><v-icon size="14" class="mr-1">mdi-repeat</v-icon>{{ selectedXPostData.retweets }}</span>
                              <span v-if="selectedXPostData.likes"><v-icon size="14" class="mr-1">mdi-heart-outline</v-icon>{{ selectedXPostData.likes }}</span>
                              <span v-if="selectedXPostData.quotes"><v-icon size="14" class="mr-1">mdi-format-quote-close</v-icon>{{ selectedXPostData.quotes }}</span>
                            </div>
                          </div>
                        </div>
                      </v-card-text>
                    </v-card>
                  </div>
                </div>

                <!-- Aspect Ratio -->
                <div class="mb-3">
                  <div class="text-caption text-grey mb-1 text-uppercase" style="font-weight: 600;">Aspect Ratio</div>
                  <v-btn-toggle v-model="aspectRatio" mandatory color="primary" density="compact">
                    <v-btn value="16:9" size="small">16:9</v-btn>
                    <v-btn value="1:1" size="small">1:1</v-btn>
                    <v-btn value="9:16" size="small">9:16</v-btn>
                    <v-btn value="4:5" size="small">4:5</v-btn>
                  </v-btn-toggle>
                </div>

                <!-- Content Fields (only show if no URL input) -->
                <template v-if="!shouldShowUrlInput">
                  <v-text-field
                    v-model="socialHeadline"
                    label="Headline"
                    placeholder="Enter headline text"
                    variant="outlined"
                    density="compact"
                    hide-details="auto"
                    class="mb-2"
                  />
                  <v-textarea
                    v-model="socialSubtext"
                    label="Subtext (optional)"
                    placeholder="Enter additional text"
                    rows="3"
                    variant="outlined"
                    density="compact"
                    hide-details="auto"
                  />
                </template>
              </div>
            </v-window-item>

            <!-- ============ PLACEHOLDER TABS ============ -->
            <v-window-item value="infochart">
              <div class="tab-content d-flex align-center justify-center" style="min-height: 200px;">
                <div class="text-center text-grey">
                  <v-icon size="64" color="grey-lighten-2">mdi-chart-bar</v-icon>
                  <div class="text-h6 mt-2">Info &amp; Chart</div>
                  <div class="text-caption">Coming soon</div>
                </div>
              </div>
            </v-window-item>
            <v-window-item value="profiles">
              <div class="tab-content d-flex align-center justify-center" style="min-height: 200px;">
                <div class="text-center text-grey">
                  <v-icon size="64" color="grey-lighten-2">mdi-account-box</v-icon>
                  <div class="text-h6 mt-2">Profiles</div>
                  <div class="text-caption">Coming soon</div>
                </div>
              </div>
            </v-window-item>
            <v-window-item value="custom">
              <div class="tab-content d-flex align-center justify-center" style="min-height: 200px;">
                <div class="text-center text-grey">
                  <v-icon size="64" color="grey-lighten-2">mdi-brush</v-icon>
                  <div class="text-h6 mt-2">Custom Request</div>
                  <div class="text-caption">Coming soon</div>
                </div>
              </div>
            </v-window-item>

          </v-window>
        </v-form>
      </v-card-text>

      <!-- Footer -->
      <v-card-actions class="px-3 py-2">
        <v-btn size="small" color="error" @click="cancel" variant="text">
          Cancel
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn
          v-if="editMode && pngUrl"
          size="small"
          variant="tonal"
          color="deep-purple"
          @click="showPngPreview = true"
        >
          <v-icon size="small" start>mdi-eye</v-icon>
          View PNG
        </v-btn>
        <!-- Social tab insert button -->
        <v-btn
          v-if="activeTab === 'social'"
          color="primary"
          variant="flat"
          size="small"
          @click="handleSocialInsert"
          :disabled="!canInsertSocial"
          :loading="loading"
        >
          <v-icon size="small" start>mdi-twitter</v-icon>
          Insert X Post Cue
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- PNG Preview Modal -->
    <v-dialog v-model="showPngPreview" max-width="960">
      <v-card class="gfx-png-preview-card">
        <v-card-title class="d-flex align-center pa-2 bg-grey-darken-4">
          <v-icon class="mr-2" color="white">mdi-image-multiple</v-icon>
          <span class="text-white">GFX Preview</span>
          <v-spacer></v-spacer>
          <v-chip size="small" color="info" class="mr-2">960x540</v-chip>
          <v-btn icon size="small" variant="text" color="white" @click="showPngPreview = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-card-text class="pa-0">
          <div class="gfx-png-preview-container">
            <video class="gfx-png-preview-video" autoplay loop muted playsinline>
              <source :src="previewBackgroundVideo" type="video/mp4">
            </video>
            <img :src="pngUrl" class="gfx-png-preview-overlay" />
          </div>
        </v-card-text>
        <v-card-actions class="bg-grey-darken-4 pa-2">
          <v-chip size="small" color="grey-darken-2">{{ gfxSlug || 'No slug' }}</v-chip>
          <v-spacer></v-spacer>
          <span class="text-caption text-grey-lighten-1">Press ESC to close</span>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Not Implemented Dialog -->
    <v-dialog v-model="showNotImplementedDialog" max-width="400">
      <v-card>
        <v-card-title class="text-body-1 font-weight-bold bg-warning text-white pa-2">
          Not Yet Implemented
        </v-card-title>
        <v-card-text class="pa-4">
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

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'
import { getColorValue } from '@/utils/themeColorMap'

const props = defineProps({
  show: { type: Boolean, required: true },
  slug: { type: String, default: '' },
  description: { type: String, default: '' },
  graphicPreview: { type: String, default: '' },
  currentEpisode: { type: String, default: '' },
  editMode: { type: Boolean, default: false },
  editData: { type: Object, default: null },
})

const emit = defineEmits([
  'update:show',
  'update:slug',
  'update:description',
  'paste-from-clipboard',
  'select-file',
  'paste-url',
  'submit',
])

const route = useRoute()

// ---- Template Refs ----
const gfxFormRef = ref(null) // eslint-disable-line no-unused-vars
const previewVideoRef = ref(null)
const bodyFieldRef = ref(null)
const titleCardFieldRef = ref(null)

// ---- Core State ----
const activeTab = ref('gfx')
const formValid = ref(false)
const showNotImplementedDialog = ref(false)
const loading = ref(false)
const showPngPreview = ref(false)

// GFX Type selector
const gfxType = ref('fullscreen-text')

// Full Screen Text fields
const gfxTitle = ref('')
const gfxBody = ref('')
const gfxSlug = ref('')

// Title Card fields
const titleCardText = ref('')

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

// Hidden required fields
const internalSlug = ref(props.slug) // eslint-disable-line no-unused-vars
const internalDescription = ref(props.description) // eslint-disable-line no-unused-vars

// ---- Computed ----
const cueTypeColor = computed(() => getColorValue('gfx'))

const editMode = computed(() => !!props.editData) // eslint-disable-line no-unused-vars

const pngUrl = computed(() => {
  const data = props.editData
  if (!data?.assetUrl && !data?.mediaUrl) return ''
  const url = data.assetUrl || data.mediaUrl
  if (url.startsWith('http') || url.startsWith('/')) return url
  const episode = route?.params?.episode || props.currentEpisode || ''
  return `/episodes/${episode}/assets/gfx/${url}`
})

const gfxTypeLabel = computed(() => {
  const labels = { 'fullscreen-text': 'Full Screen Text', 'title-card': 'Title Card' }
  return labels[gfxType.value] || gfxType.value
})

const activeTextContent = computed(() => {
  if (gfxType.value === 'title-card') return titleCardText.value || ''
  return gfxBody.value || ''
})

const canSubmitGfx = computed(() => {
  if (gfxType.value === 'fullscreen-text') {
    return gfxBody.value && gfxBody.value.trim().length >= 5 && !!gfxSlug.value
  }
  if (gfxType.value === 'title-card') {
    return !!titleCardText.value && !!gfxSlug.value
  }
  return false
})

const fontMap = {
  'sans-serif': 'Helvetica, Arial, sans-serif',
  'serif': 'Georgia, "Times New Roman", serif',
  'monospace': '"Courier New", Courier, monospace'
}

const previewStyle = computed(() => ({
  alignItems: textAlign.value === 'center' ? 'center' :
             textAlign.value === 'left' ? 'flex-start' :
             textAlign.value === 'right' ? 'flex-end' : 'center'
}))

const titleStyle = computed(() => {
  const fontSizeVw = ((fontSize.value + 8) / 1920) * 100
  return {
    fontFamily: fontMap[fontFamily.value] || fontMap['sans-serif'],
    fontSize: `${fontSizeVw}vw`,
    fontWeight: 'bold',
    textAlign: textAlign.value,
    marginBottom: '0.5em'
  }
})

const bodyStyle = computed(() => {
  const fontSizeVw = (fontSize.value / 1920) * 100
  return {
    fontFamily: fontMap[fontFamily.value] || fontMap['sans-serif'],
    fontSize: `${fontSizeVw}vw`,
    textAlign: textAlign.value
  }
})

const titleCardStyle = computed(() => {
  const fontSizeVw = ((fontSize.value + 4) / 1920) * 100
  return {
    fontFamily: fontMap[fontFamily.value] || fontMap['sans-serif'],
    fontSize: `${fontSizeVw}vw`,
    fontWeight: 'bold',
    textAlign: 'center',
    lineHeight: 1.3,
    textShadow: '2px 2px 4px rgba(0, 0, 0, 0.8)'
  }
})

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

// ---- Social Tab ----
const socialPlatform = ref('twitter')
const socialSourceType = ref('post')
const socialPostUrl = ref('')
const aspectRatio = ref('16:9')
const socialHeadline = ref('')
const socialSubtext = ref('')

// Whiteboard X Post selection
const whiteboardXPosts = ref([])
const loadingWhiteboardPosts = ref(false)
const selectedWhiteboardXPost = ref(null) // eslint-disable-line no-unused-vars
const selectedXPostData = ref(null)

const shouldShowUrlInput = computed(() => {
  return ['post', 'video'].includes(socialSourceType.value)
})

const urlInputLabel = computed(() => {
  const labels = { twitter: 'X/Twitter Post URL', facebook: 'Facebook Post URL', instagram: 'Instagram Post URL', youtube: 'YouTube Video URL', tiktok: 'TikTok Video URL' }
  return labels[socialPlatform.value] || 'URL'
})

const urlInputPlaceholder = computed(() => {
  const placeholders = { twitter: 'https://x.com/username/status/1234567890', facebook: 'https://www.facebook.com/username/posts/1234567890', instagram: 'https://www.instagram.com/p/ABC123DEF456/', youtube: 'https://www.youtube.com/watch?v=ABC123DEF456', tiktok: 'https://www.tiktok.com/@username/video/1234567890' }
  return placeholders[socialPlatform.value] || 'Enter URL'
})

const urlInputHint = computed(() => {
  return `Paste the direct URL to the ${socialPlatform.value === 'twitter' ? 'X/Twitter' : socialPlatform.value} ${socialSourceType.value}`
})

const canInsertSocial = computed(() => {
  if (socialPlatform.value === 'twitter') {
    return !!(selectedXPostData.value || socialPostUrl.value)
  }
  return !!socialPostUrl.value
})

// ---- Methods ----
function cancel() {
  emit('update:show', false)
}

function handleVideoLoaded() {
  console.log('GFX preview video loaded')
}

function handleVideoError() {
  console.warn('GFX preview video failed to load')
}

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

const resetForm = () => {
  gfxTitle.value = ''
  gfxBody.value = ''
  gfxSlug.value = ''
  titleCardText.value = ''
  fontSize.value = 25
  fontFamily.value = 'sans-serif'
  textAlign.value = 'center'
  renderMode.value = 'png'
}

function loadEditData() {
  if (!props.editData) return
  const data = props.editData.rawData || props.editData
  if (data.gfxType) gfxType.value = data.gfxType
  if (data.title) gfxTitle.value = data.title
  if (data.body) gfxBody.value = data.body
  if (data.titleCardText) titleCardText.value = data.titleCardText
  if (data.slug) gfxSlug.value = data.slug
  if (data.style?.fontSize) fontSize.value = data.style.fontSize
  if (data.style?.fontFamily) fontFamily.value = data.style.fontFamily
  if (data.style?.textAlign) textAlign.value = data.style.textAlign
  if (data.renderMode) renderMode.value = data.renderMode
}

// Generate AssetID
const generateAssetId = async () => {
  try {
    const formData = new FormData()
    formData.append('slug', gfxSlug.value || 'gfx-text')
    formData.append('type', 'gfx')

    const response = await axios.post('/assetid/generate-legacy', formData, {
      headers: {
        'Accept': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
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

// Build cue data based on current gfxType
function buildCueData(assetId, extras = {}) {
  const base = {
    type: 'GFX',
    gfxType: gfxType.value,
    assetId: assetId,
    slug: gfxSlug.value,
    style: {
      fontSize: fontSize.value,
      fontFamily: fontFamily.value,
      textAlign: textAlign.value
    },
    renderMode: renderMode.value,
    ...extras
  }

  if (gfxType.value === 'fullscreen-text') {
    base.title = gfxTitle.value || null
    base.body = gfxBody.value
  } else if (gfxType.value === 'title-card') {
    base.titleCardText = titleCardText.value
    base.body = titleCardText.value // Also set body for cue display
  }

  return base
}

const handleInsertOnly = async () => {
  if (!canSubmitGfx.value) return

  try {
    const assetId = await generateAssetId()
    const cueData = buildCueData(assetId, { status: 'pending' })
    console.log('Inserting GFX cue only (no generation):', cueData)
    emit('submit', cueData)
    resetForm()
    emit('update:show', false)
  } catch (error) {
    console.error('Error creating GFX cue:', error)
  }
}

const handleSubmit = async () => {
  if (activeTab.value !== 'gfx') {
    showNotImplementedDialog.value = true
    return
  }

  if (!canSubmitGfx.value) return

  loading.value = true

  try {
    const assetId = await generateAssetId()

    console.log('Submitting GFX to Celery...')
    const response = await axios.post('/api/gfx/generate', {
      episode_id: props.currentEpisode || '0000',
      gfx_type: gfxType.value,
      body: gfxType.value === 'title-card' ? titleCardText.value : gfxBody.value,
      slug: gfxSlug.value,
      asset_id: assetId,
      title: gfxType.value === 'title-card' ? titleCardText.value : (gfxTitle.value || null),
      alignment: gfxType.value === 'title-card' ? 'center' : textAlign.value,
      font_family: fontFamily.value,
      font_size: fontSize.value,
      render_mode: renderMode.value,
      priority: 'high'
    }, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })

    console.log('GFX generated:', response.data)
    const cueData = buildCueData(assetId, {
      assetUrl: response.data.asset_url,
      assetPath: response.data.asset_path
    })

    emit('submit', cueData)
    resetForm()
    emit('update:show', false)

  } catch (error) {
    console.error('Error creating GFX:', error)
    if (error.response?.status === 202) {
      console.log('GFX generation in progress, proceeding with cue insertion')
      const assetId = await generateAssetId()
      emit('submit', buildCueData(assetId, { status: 'pending' }))
      resetForm()
      emit('update:show', false)
    }
  } finally {
    loading.value = false
  }
}

// ---- Social Methods ----
const fetchWhiteboardXPosts = async () => {
  if (!props.currentEpisode) return
  loadingWhiteboardPosts.value = true
  try {
    const response = await axios.get(`/api/whiteboard/${props.currentEpisode}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })
    const items = response.data?.items || []
    const xPosts = items.filter(item => {
      const sm = item.social_metadata
      if (!sm) return false
      return sm.platform === 'x' || sm.tweet_id || (item.url && (item.url.includes('x.com') || item.url.includes('twitter.com')))
    })
    whiteboardXPosts.value = xPosts.map(item => {
      const sm = item.social_metadata || {}
      const text = sm.tweet_text || item.preview_description || ''
      const truncated = text.length > 80 ? text.substring(0, 80) + '...' : text
      return {
        id: item.id,
        displayLabel: `@${sm.author_handle || '?'}: ${truncated}`,
        subtitle: `${sm.likes ? sm.likes + ' likes' : ''} ${sm.retweets ? sm.retweets + ' RTs' : ''} ${sm.published_time ? '- ' + new Date(sm.published_time).toLocaleDateString() : ''}`.trim(),
        authorAvatar: sm.author_avatar || null,
        socialMetadata: sm,
        url: item.url,
        mediaAssetId: item.media_asset_id,
        mediaPath: item.media_path,
        assetId: item.asset_id
      }
    })
  } catch (error) {
    console.error('Failed to fetch whiteboard X posts:', error)
    whiteboardXPosts.value = []
  } finally {
    loadingWhiteboardPosts.value = false
  }
}

const handleXPostSelected = (item) => {
  if (!item) {
    selectedXPostData.value = null
    socialPostUrl.value = ''
    return
  }
  selectedXPostData.value = item.socialMetadata
  socialPostUrl.value = item.url || ''
}

const handleSocialInsert = async () => {
  if (socialPlatform.value !== 'twitter') {
    showNotImplementedDialog.value = true
    return
  }

  loading.value = true
  try {
    let xPostData = selectedXPostData.value
    let postUrl = socialPostUrl.value

    if (!xPostData && postUrl) {
      try {
        const previewResp = await axios.get(`/api/whiteboard/fetch-link-preview?url=${encodeURIComponent(postUrl)}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
          }
        })
        const preview = previewResp.data
        xPostData = {}
        for (const [key, val] of Object.entries(preview)) {
          if (key.startsWith('x_')) {
            xPostData[key.substring(2)] = val
          }
        }
        if (!xPostData.tweet_id) {
          const tweetIdMatch = postUrl.match(/status\/(\d+)/)
          if (tweetIdMatch) xPostData.tweet_id = tweetIdMatch[1]
        }
      } catch (err) {
        console.error('Failed to fetch X post data:', err)
      }
    }

    if (!xPostData || (!xPostData.tweet_id && !xPostData.tweet_text)) {
      alert('Could not retrieve X post data. Please try again or select a cached post.')
      return
    }

    const assetId = await generateAssetId()
    const slug = (xPostData.author_handle || 'xpost') + '-' + (xPostData.tweet_id || Date.now()).toString().slice(-8)

    const cueData = {
      type: 'GFX',
      gfxType: 'xpost',
      assetId: assetId,
      slug: slug,
      tweetId: xPostData.tweet_id,
      tweetText: xPostData.tweet_text,
      authorName: xPostData.author_name,
      authorHandle: xPostData.author_handle,
      authorAvatar: xPostData.author_avatar,
      authorVerified: xPostData.author_verified || false,
      authorBio: xPostData.author_bio,
      authorFollowers: xPostData.author_followers,
      authorFollowing: xPostData.author_following,
      publishedTime: xPostData.published_time,
      conversationId: xPostData.conversation_id,
      likes: xPostData.likes,
      retweets: xPostData.retweets,
      replies: xPostData.replies,
      quotes: xPostData.quotes,
      mediaUrls: xPostData.media_urls || [],
      mediaObjects: xPostData.media_objects || [],
      entities: xPostData.entities || {},
      referencedTweets: xPostData.referenced_tweets || [],
      sourceUrl: postUrl,
      platform: 'x',
      aspectRatio: aspectRatio.value,
      fullMetadata: xPostData
    }

    emit('submit', cueData)
    resetSocialForm()
    emit('update:show', false)
  } catch (error) {
    console.error('Error inserting X post cue:', error)
  } finally {
    loading.value = false
  }
}

const resetSocialForm = () => {
  socialPostUrl.value = ''
  selectedWhiteboardXPost.value = null
  selectedXPostData.value = null
  socialHeadline.value = ''
  socialSubtext.value = ''
}

// ---- ESC Key ----
const handleKeydown = (event) => {
  if (event.key === 'Escape' && props.show) {
    event.preventDefault()
    event.stopPropagation()
    emit('update:show', false)
  }
}

// ---- Watchers ----
watch(() => props.show, async (newVal) => {
  if (newVal) {
    if (props.editData) {
      loadEditData()
    }

    await nextTick()
    // Focus appropriate field
    if (gfxType.value === 'title-card' && titleCardFieldRef.value) {
      titleCardFieldRef.value.focus()
    } else if (bodyFieldRef.value) {
      bodyFieldRef.value.focus()
    }
    // Start video
    if (previewVideoRef.value) {
      previewVideoRef.value.load()
      previewVideoRef.value.play().catch(err => {
        console.warn('Video autoplay prevented:', err)
      })
    }
  } else {
    showPngPreview.value = false
  }
})

// Auto-generate slug
watch([gfxBody, titleCardText, gfxType], ([body, title, type]) => {
  const text = type === 'title-card' ? title : body
  if (text && !gfxSlug.value) {
    const words = text.trim().split(/\s+/).slice(0, 3)
    gfxSlug.value = words
      .join(' ')
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-+|-+$/g, '')
  }
})

// Social tab watchers
watch([activeTab, socialPlatform], ([tab, platform]) => {
  if (tab === 'social' && platform === 'twitter' && props.currentEpisode) {
    fetchWhiteboardXPosts()
  }
})

watch(() => props.show, (newVal) => {
  if (newVal && activeTab.value === 'social' && socialPlatform.value === 'twitter') {
    fetchWhiteboardXPosts()
  }
})

// ---- Lifecycle ----
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
.gfx-modal-card {
  max-height: 90vh;
  overflow-y: auto;
}

.compact-gfx-modal {
  font-size: 0.9rem;
}

.compact-gfx-modal :deep(.v-label),
.compact-gfx-modal :deep(.v-field-label),
.compact-gfx-modal :deep(.v-input__details),
.compact-gfx-modal :deep(.v-messages) {
  font-size: 0.85rem;
}

.tab-content {
  padding: 12px 0;
}

/* GFX Preview Container */
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

.gfx-title-card-text {
  color: white;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

/* Style settings section */
.style-settings {
  background: rgba(255, 255, 255, 0.03);
  padding: 8px;
  border-radius: 4px;
}

/* Render mode section */
.render-mode-section {
  background: rgba(255, 255, 255, 0.03);
  padding: 8px;
  border-radius: 4px;
}

/* X Post selector styles */
.xpost-divider {
  display: flex;
  align-items: center;
  gap: 12px;
}

.xpost-divider-text {
  font-size: 0.8rem;
  color: #888;
  white-space: nowrap;
  font-weight: 500;
}

.xpost-list-item {
  border-bottom: 1px solid #f0f0f0;
}

.xpost-preview-card {
  border-color: #1da1f2 !important;
  background: #f8fcff;
}

/* PNG Preview Modal */
.gfx-png-preview-card {
  border-radius: 0 !important;
  overflow: hidden;
}

.gfx-png-preview-container {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #000;
}

.gfx-png-preview-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 1;
}

.gfx-png-preview-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
  z-index: 2;
}

/* Sharp corners for consistency */
.gfx-modal-card :deep(.v-field),
.gfx-modal-card :deep(.v-text-field),
.gfx-modal-card :deep(.v-textarea),
.gfx-modal-card :deep(.v-card),
.gfx-modal-card :deep(.v-alert),
.gfx-modal-card :deep(.v-btn),
.gfx-modal-card :deep(.v-chip) {
  border-radius: 0 !important;
}
</style>
