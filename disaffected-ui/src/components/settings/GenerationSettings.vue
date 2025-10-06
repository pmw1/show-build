<template>
  <v-card class="pa-0">
    <v-row no-gutters class="fill-height">
      <!-- Vertical Tabs on Left -->
      <v-col cols="3" class="border-r">
        <v-tabs
          v-model="generationSubTab"
          direction="vertical"
          color="primary"
          class="generation-vertical-tabs"
        >
          <v-tab value="fsq-generator" prepend-icon="mdi-format-quote-close">
            FSQ Quote Generator
          </v-tab>
          <v-tab value="llm-routing" prepend-icon="mdi-robot">
            AI/LLM Routing
          </v-tab>
          <v-tab value="templates" prepend-icon="mdi-file-document-multiple">
            Templates Library
          </v-tab>
          <v-tab value="media-assets" prepend-icon="mdi-folder-image">
            Media Assets
          </v-tab>
        </v-tabs>
      </v-col>

      <!-- Tab Content on Right -->
      <v-col cols="9">
        <v-tabs-window v-model="generationSubTab" class="pa-6">

          <!-- FSQ Quote Generator -->
          <v-tabs-window-item value="fsq-generator">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-format-quote-close</v-icon>
              FSQ Quote Generator
            </h3>
            <p class="text-body-2 mb-4">Configure settings for Full Screen Quote generation and preview.</p>

            <v-card variant="tonal" color="deep-purple" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-video</v-icon>
                Preview Background Video
              </h4>
              <v-text-field
                v-model="localSettings.fsqBackgroundVideo"
                label="Background Video Path"
                placeholder="/assets/preview-background.mp4"
                variant="outlined"
                density="comfortable"
                hint="Path to compressed video for FSQ modal preview (1920x1080 → 640x360, ~1MB)"
                persistent-hint
              />

              <v-alert type="info" variant="tonal" class="mt-4">
                <v-alert-title>Compressed Preview</v-alert-title>
                The preview uses an ultra-compressed version of your branded background.
                Current: <code>{{ localSettings.fsqBackgroundVideo }}</code>
              </v-alert>
            </v-card>

            <v-card variant="tonal" color="deep-purple" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-palette</v-icon>
                Default FSQ Style
              </h4>
              <v-row>
                <v-col cols="6">
                  <v-select
                    v-model="localSettings.fsqDefaultAlignment"
                    :items="alignmentOptions"
                    label="Default Text Alignment"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="6">
                  <v-select
                    v-model="localSettings.fsqDefaultFont"
                    :items="fontOptions"
                    label="Default Font Family"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
              </v-row>

              <v-slider
                v-model="localSettings.fsqDefaultFontSize"
                label="Default Font Size"
                min="10"
                max="50"
                step="1"
                thumb-label
                hint="Default font size for new FSQ quotes (10-50px)"
                persistent-hint
              >
                <template v-slot:append>
                  <v-chip size="small" color="primary">
                    {{ localSettings.fsqDefaultFontSize }}px
                  </v-chip>
                </template>
              </v-slider>
            </v-card>

            <v-card variant="outlined" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-cog</v-icon>
                Generation Options
              </h4>
              <v-checkbox
                v-model="localSettings.fsqIncludeAttributionByDefault"
                label="Include attribution by default"
                hint="When enabled, the attribution radio button will be pre-selected to 'Include Attribution'"
                persistent-hint
                density="comfortable"
              />
            </v-card>

            <v-card variant="outlined" class="pa-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-scissors-cutting</v-icon>
                Quote Splitting Rules
              </h4>
              <p class="text-body-2 mb-4 text-medium-emphasis">
                Configure how AI determines when to split long quotes for optimal display (1920x1080 full screen).
              </p>

              <v-row>
                <v-col cols="6">
                  <v-slider
                    v-model="localSettings.fsqMaxLines"
                    label="Max Lines Per Slide"
                    min="3"
                    max="8"
                    step="1"
                    thumb-label
                    hint="Maximum comfortable lines for full-screen display"
                    persistent-hint
                  >
                    <template v-slot:append>
                      <v-chip size="small" color="primary">
                        {{ localSettings.fsqMaxLines }} lines
                      </v-chip>
                    </template>
                  </v-slider>
                </v-col>

                <v-col cols="6">
                  <v-slider
                    v-model="localSettings.fsqCharsPerLine"
                    label="Characters Per Line"
                    min="50"
                    max="90"
                    step="5"
                    thumb-label
                    hint="Approximate characters per line at default font size"
                    persistent-hint
                  >
                    <template v-slot:append>
                      <v-chip size="small" color="primary">
                        {{ localSettings.fsqCharsPerLine }} chars
                      </v-chip>
                    </template>
                  </v-slider>
                </v-col>
              </v-row>

              <v-alert type="info" variant="tonal" class="mt-4">
                <v-alert-title>Automatic Calculation</v-alert-title>
                Max characters per slide: <strong>{{ localSettings.fsqMaxLines * localSettings.fsqCharsPerLine }}</strong>
                ({{ localSettings.fsqMaxLines }} lines × {{ localSettings.fsqCharsPerLine }} chars)
                <br><small>Quotes exceeding this limit will be intelligently split by AI at natural boundaries.</small>
              </v-alert>
            </v-card>
          </v-tabs-window-item>

          <!-- LLM Routing -->
          <v-tabs-window-item value="llm-routing">
            <LLMRoutingSettings
              v-model="llmSettings"
              @save="handleLLMSave"
            />
          </v-tabs-window-item>

          <!-- Templates Library -->
          <v-tabs-window-item value="templates">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-file-document-multiple</v-icon>
              Templates Library
            </h3>
            <p class="text-body-2 mb-4">Manage paths to reusable content templates stored on the media drive.</p>

            <v-card variant="tonal" color="primary" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-folder-multiple</v-icon>
                Template Library Root
              </h4>
              <v-text-field
                v-model="localSettings.templateLibraryPath"
                label="Template Library Path"
                placeholder="/mnt/sync/disaffected/templates"
                variant="outlined"
                density="comfortable"
                hint="Root path for all template categories"
                persistent-hint
              />
            </v-card>

            <v-card variant="outlined" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3">Template Categories</h4>
              <v-list density="compact">
                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-text-box</v-icon>
                  </template>
                  <v-list-item-title>Rundown Templates</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.templateLibraryPath }}/rundown/</v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-script-text</v-icon>
                  </template>
                  <v-list-item-title>Script Templates</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.templateLibraryPath }}/scripts/</v-list-item-subtitle>
                </v-list-item>

                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-image-multiple</v-icon>
                  </template>
                  <v-list-item-title>Graphic Templates</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.templateLibraryPath }}/graphics/</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card>

            <v-alert type="info" variant="tonal">
              <v-alert-title>Storage Location</v-alert-title>
              Templates are stored on the media drive (<code>/mnt/sync/disaffected/</code>) for persistence and backup via Syncthing.
            </v-alert>
          </v-tabs-window-item>

          <!-- Media Assets -->
          <v-tabs-window-item value="media-assets">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-folder-image</v-icon>
              Media Assets
            </h3>
            <p class="text-body-2 mb-4">Configure paths to shared media library for backgrounds, graphics, and audio.</p>

            <v-card variant="tonal" color="primary" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-folder-image</v-icon>
                Media Assets Root
              </h4>
              <v-text-field
                v-model="localSettings.mediaAssetsPath"
                label="Media Assets Path"
                placeholder="/mnt/sync/disaffected/media assets"
                variant="outlined"
                density="comfortable"
                hint="Root path for all shared media assets"
                persistent-hint
              />
            </v-card>

            <v-card variant="outlined" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3">Media Asset Categories</h4>
              <v-list density="compact">
                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-video</v-icon>
                  </template>
                  <v-list-item-title>Video Assets</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.mediaAssetsPath }}/video/</v-list-item-subtitle>
                </v-list-item>

                <v-list-subheader>Video Subcategories</v-list-subheader>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-video-outline</v-icon>
                  </template>
                  <v-list-item-subtitle>Backgrounds: {{ localSettings.mediaAssetsPath }}/video/backgrounds/</v-list-item-subtitle>
                </v-list-item>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-video-outline</v-icon>
                  </template>
                  <v-list-item-subtitle>Templates: {{ localSettings.mediaAssetsPath }}/video/templates/</v-list-item-subtitle>
                </v-list-item>

                <v-divider class="my-2" />

                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-music</v-icon>
                  </template>
                  <v-list-item-title>Audio Assets</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.mediaAssetsPath }}/audio/</v-list-item-subtitle>
                </v-list-item>

                <v-list-subheader>Audio Subcategories</v-list-subheader>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-music-note</v-icon>
                  </template>
                  <v-list-item-subtitle>Music: {{ localSettings.mediaAssetsPath }}/audio/music/</v-list-item-subtitle>
                </v-list-item>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-waveform</v-icon>
                  </template>
                  <v-list-item-subtitle>SFX: {{ localSettings.mediaAssetsPath }}/audio/sfx/</v-list-item-subtitle>
                </v-list-item>

                <v-divider class="my-2" />

                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-image</v-icon>
                  </template>
                  <v-list-item-title>Graphics Assets</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.mediaAssetsPath }}/graphics/</v-list-item-subtitle>
                </v-list-item>

                <v-list-subheader>Graphics Subcategories</v-list-subheader>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-format-quote-close</v-icon>
                  </template>
                  <v-list-item-subtitle>FSQ Templates: {{ localSettings.mediaAssetsPath }}/graphics/fsq-templates/</v-list-item-subtitle>
                </v-list-item>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-text-box</v-icon>
                  </template>
                  <v-list-item-subtitle>Lower Thirds: {{ localSettings.mediaAssetsPath }}/graphics/lower-thirds/</v-list-item-subtitle>
                </v-list-item>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-transition</v-icon>
                  </template>
                  <v-list-item-subtitle>Transitions: {{ localSettings.mediaAssetsPath }}/graphics/transitions/</v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card>

            <v-alert type="success" variant="tonal">
              <v-alert-title>Source Video</v-alert-title>
              Current background source: <code>/mnt/sync/disaffected/media assets/video/backgrounds/background-branded-slow.mp4</code>
            </v-alert>
          </v-tabs-window-item>

        </v-tabs-window>
      </v-col>
    </v-row>

    <!-- Save Button (Fixed at bottom of card) -->
    <v-card-actions class="px-4 pb-4 border-t">
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="save" variant="elevated">
        <v-icon left>mdi-content-save</v-icon>
        Save Generation Settings
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import LLMRoutingSettings from './LLMRoutingSettings.vue'

export default {
  name: 'GenerationSettings',
  components: {
    LLMRoutingSettings
  },
  props: {
    modelValue: {
      type: Object,
      default: () => ({
        fsqBackgroundVideo: '/assets/preview-background.mp4',
        fsqDefaultAlignment: 'left',
        fsqDefaultFont: 'sans-serif',
        fsqDefaultFontSize: 30,
        fsqIncludeAttributionByDefault: true,
        fsqMaxLines: 4,
        fsqCharsPerLine: 70,
        templateLibraryPath: '/mnt/sync/disaffected/templates',
        mediaAssetsPath: '/mnt/sync/disaffected/media assets'
      })
    }
  },
  emits: ['update:modelValue', 'save'],
  data() {
    return {
      generationSubTab: 'fsq-generator',
      localSettings: { ...this.modelValue },
      llmSettings: {
        routing: {
          quoteSplitting: 'auto',
          slugGeneration: 'auto',
          scriptSummary: 'auto',
          titleGeneration: 'auto',
          contentExpansion: 'auto',
          factChecking: 'auto',
          enableFallback: true,
          fallbackOrder: ['ollama', 'openai', 'anthropic', 'gemini', 'grok']
        },
        prompts: []
      },
      alignmentOptions: [
        { title: 'Left Aligned', value: 'left' },
        { title: 'Centered', value: 'centered' },
        { title: 'Right Aligned', value: 'right' }
      ],
      fontOptions: [
        { title: 'Sans Serif (Helvetica)', value: 'sans-serif' },
        { title: 'Serif (Georgia)', value: 'serif' },
        { title: 'Monospace (Courier)', value: 'monospace' }
      ]
    }
  },
  watch: {
    modelValue: {
      handler(newVal) {
        this.localSettings = { ...newVal }
      },
      deep: true
    }
  },
  mounted() {
    this.loadLLMSettings()
  },
  methods: {
    save() {
      this.$emit('update:modelValue', this.localSettings)
      this.$emit('save', this.localSettings)
    },
    async loadLLMSettings() {
      // Load LLM settings from localStorage or API
      const saved = localStorage.getItem('llm-routing-settings')
      if (saved) {
        this.llmSettings = JSON.parse(saved)
      }
    },
    handleLLMSave(settings) {
      this.llmSettings = settings
      // Save to localStorage and/or backend
      localStorage.setItem('llm-routing-settings', JSON.stringify(settings))
      console.log('LLM routing settings saved:', settings)
    }
  }
}
</script>

<style scoped>
.border-r {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.border-t {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.generation-vertical-tabs {
  height: 100%;
}

.v-card {
  border-radius: 8px;
}
</style>
