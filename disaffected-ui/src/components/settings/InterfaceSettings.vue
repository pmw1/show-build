<template>
  <v-card class="pa-0">
    <v-row no-gutters class="fill-height">
      <!-- Vertical Tabs on Left -->
      <v-col cols="3" class="border-r">
        <v-tabs
          v-model="interfaceSubTab"
          direction="vertical"
          color="primary"
          class="interface-vertical-tabs"
        >
          <v-tab value="editor" prepend-icon="mdi-file-document-edit">
            Content Editor
          </v-tab>
          <v-tab value="colors" prepend-icon="mdi-palette">
            Colors & Themes
          </v-tab>
          <v-tab value="theme" prepend-icon="mdi-theme-light-dark">
            Theme Settings
          </v-tab>
          <v-tab value="layout" prepend-icon="mdi-view-dashboard">
            Layout
          </v-tab>
          <v-tab value="accessibility" prepend-icon="mdi-wheelchair-accessibility">
            Accessibility
          </v-tab>
        </v-tabs>
      </v-col>

      <!-- Tab Content on Right -->
      <v-col cols="9">
        <v-tabs-window v-model="interfaceSubTab" class="pa-6">

          <!-- Content Editor Tab -->
          <v-tabs-window-item value="editor">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-file-document-edit</v-icon>
              Content Editor Settings
            </h3>
            <p class="text-body-2 mb-4">Configure how the content editor behaves and appears.</p>

            <!-- Font Settings -->
            <v-row>
              <v-col cols="12" md="6">
                <v-slider
                  v-model="interfaceSettings.editorFontSize"
                  label="Font Size"
                  min="10"
                  max="24"
                  step="1"
                  thumb-label
                  class="mb-4"
                >
                  <template v-slot:append>
                    <v-text-field
                      v-model="interfaceSettings.editorFontSize"
                      type="number"
                      style="width: 60px"
                      density="compact"
                      suffix="px"
                      hide-details
                    />
                  </template>
                </v-slider>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="interfaceSettings.editorFontFamily"
                  :items="[
                    { title: 'Monospace', value: 'monospace' },
                    { title: 'Arial', value: 'Arial, sans-serif' },
                    { title: 'Times New Roman', value: 'Times New Roman, serif' },
                    { title: 'Helvetica', value: 'Helvetica, sans-serif' }
                  ]"
                  label="Font Family"
                  class="mb-4"
                />
              </v-col>
            </v-row>

            <!-- Code Mode Settings -->
            <v-divider class="my-4"></v-divider>
            <h4 class="text-subtitle-1 mb-3">Code Mode Settings</h4>

            <v-switch
              v-model="interfaceSettings.editorAutoSave"
              label="Auto-save"
              color="primary"
              class="mb-3"
            />

            <!-- Script Mode Settings -->
            <v-divider class="my-4"></v-divider>
            <h4 class="text-subtitle-1 mb-3">Script Mode Settings</h4>

            <v-switch
              v-model="interfaceSettings.editorLineNumbers"
              label="Show line numbers"
              color="primary"
              class="mb-3"
            />

            <v-switch
              v-model="interfaceSettings.editorWordWrap"
              label="Word wrap"
              color="primary"
              class="mb-3"
            />

            <v-switch
              v-model="interfaceSettings.pastePlainTextOnly"
              label="Paste as plain text only"
              hint="Strip all formatting when pasting (removes colors, fonts, styles from copied text)"
              persistent-hint
              color="primary"
              class="mb-3"
            />

            <v-select
              v-model="interfaceSettings.cueCardAlignment"
              :items="[
                { title: 'Left', value: 'left' },
                { title: 'Center', value: 'center' },
                { title: 'Right', value: 'right' }
              ]"
              label="Cue Card Alignment"
              hint="How cue cards are aligned in script mode"
              persistent-hint
              class="mb-4"
            />

            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingInterface"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Editor Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Colors & Themes Tab -->
          <v-tabs-window-item value="colors">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-palette</v-icon>
              Colors & Theme Configuration
            </h3>
            <p class="text-body-2 mb-4">Configure segment colors, interface themes, and visual styling.</p>

            <!-- Color Selector Component -->
            <ColorSelector />

            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingInterface"
              class="mt-4"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Color Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Theme Settings Tab -->
          <v-tabs-window-item value="theme">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-theme-light-dark</v-icon>
              Theme Settings
            </h3>
            <p class="text-body-2 mb-4">Configure the overall appearance and theme of the interface.</p>

            <v-select
              v-model="interfaceSettings.theme"
              :items="[
                { title: 'Dark', value: 'dark' },
                { title: 'Light', value: 'light' },
                { title: 'Auto', value: 'auto' }
              ]"
              label="Color Theme"
              class="mb-4"
            />

            <v-switch
              v-model="interfaceSettings.highContrast"
              label="High contrast mode"
              color="primary"
              class="mb-3"
            />

            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingInterface"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Theme Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Layout Tab -->
          <v-tabs-window-item value="layout">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-view-dashboard</v-icon>
              Layout Settings
            </h3>
            <p class="text-body-2 mb-4">Configure the layout and behavior of interface elements.</p>

            <v-slider
              v-model="interfaceSettings.sidebarWidth"
              label="Sidebar Width"
              min="200"
              max="500"
              step="10"
              thumb-label
              class="mb-4"
            >
              <template v-slot:append>
                <v-text-field
                  v-model="interfaceSettings.sidebarWidth"
                  type="number"
                  style="width: 80px"
                  density="compact"
                  suffix="px"
                  hide-details
                />
              </template>
            </v-slider>

            <v-switch
              v-model="interfaceSettings.compactMode"
              label="Compact mode"
              color="primary"
              class="mb-3"
            />

            <v-switch
              v-model="interfaceSettings.showToolbarLabels"
              label="Show toolbar labels"
              color="primary"
              class="mb-3"
            />

            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingInterface"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Layout Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Accessibility Tab -->
          <v-tabs-window-item value="accessibility">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-wheelchair-accessibility</v-icon>
              Accessibility Options
            </h3>
            <p class="text-body-2 mb-4">Configure accessibility features and preferences.</p>

            <v-switch
              v-model="interfaceSettings.reducedMotion"
              label="Reduce motion and animations"
              color="primary"
              class="mb-3"
            />

            <v-switch
              v-model="interfaceSettings.keyboardShortcuts"
              label="Enable keyboard shortcuts"
              color="primary"
              class="mb-3"
            />

            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingInterface"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Accessibility Settings
            </v-btn>
          </v-tabs-window-item>

        </v-tabs-window>
      </v-col>
    </v-row>
  </v-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import ColorSelector from '@/components/ColorSelector.vue'

// Component props
const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

// Component emits
const emit = defineEmits(['update:modelValue', 'save'])

// Interface sub-tab state
const interfaceSubTab = ref('editor')

// Loading state
const savingInterface = ref(false)

// Local reactive copy of interface settings
const interfaceSettings = ref({ ...props.modelValue })

// Watch for changes to props and update local state
watch(() => props.modelValue, (newValue) => {
  // Only update if values actually changed to avoid loops
  if (JSON.stringify(interfaceSettings.value) !== JSON.stringify(newValue)) {
    interfaceSettings.value = { ...newValue }
  }
}, { deep: true })

// Watch for changes to local state and emit updates
watch(interfaceSettings, (newValue) => {
  emit('update:modelValue', newValue)
}, { deep: true, flush: 'post' })

// Methods
const handleSave = () => {
  savingInterface.value = true
  // Only emit 'save', don't double-emit 'update:modelValue' since watcher already does it
  emit('save', interfaceSettings.value)
  // Reset loading state after a brief delay
  setTimeout(() => {
    savingInterface.value = false
  }, 1000)
}
</script>

<style scoped>
.interface-vertical-tabs {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.border-r {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.v-card {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}
</style>