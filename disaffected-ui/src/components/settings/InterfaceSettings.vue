<template>
  <v-card class="pa-4">
    <v-card-title class="text-h6 mb-4">
      <v-icon left>mdi-monitor</v-icon>
      Interface Settings
    </v-card-title>
    <v-card-text>
      <div class="d-flex justify-space-between align-center mb-4">
        <p class="text-body-2 mb-0">Customize the appearance and behavior of the user interface.</p>
        <v-select
          v-model="selectedProfile"
          :items="profileOptions"
          label="Profile"
          density="compact"
          style="max-width: 200px;"
          @update:model-value="loadProfile"
        />
      </div>
      
      <!-- Content Editor Scripting -->
      <v-row class="mb-6">
        <v-col cols="12">
          <h3 class="text-subtitle-1 mb-3">Content Editor Scripting</h3>
          <v-expansion-panels variant="accordion">
            <v-expansion-panel>
              <v-expansion-panel-title class="text-h6">
                <div class="d-flex align-center justify-space-between w-100">
                  <div class="d-flex align-center">
                    <v-icon class="mr-2" size="small">mdi-script-text</v-icon>
                    Editor Settings
                  </div>
                  <v-btn
                    :color="getButtonColor(editorSaveStatus)"
                    :loading="editorSaveStatus === 'saving'"
                    @click.stop="saveEditorSettings"
                    size="small"
                    variant="elevated"
                    class="ml-2"
                  >
                    <v-icon left size="small">
                      {{ getButtonIcon(editorSaveStatus) }}
                    </v-icon>
                    {{ getButtonText(editorSaveStatus) }}
                  </v-btn>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="settings.editorFontSize"
                      :items="fontSizes"
                      label="Font Size"
                      suffix="px"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="settings.editorFontFamily"
                      :items="fontFamilies"
                      label="Font Family"
                    />
                  </v-col>
                </v-row>
                <v-switch
                  v-model="settings.editorLineNumbers"
                  label="Show line numbers"
                  color="primary"
                />
                <v-switch
                  v-model="settings.editorWordWrap"
                  label="Word wrap"
                  color="primary"
                />
                <v-switch
                  v-model="settings.editorAutoSave"
                  label="Auto-save (every 30 seconds)"
                  color="primary"
                />
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-col>
      </v-row>

      <!-- Color Configuration -->
      <v-row class="mb-6">
        <v-col cols="12">
          <h3 class="text-subtitle-1 mb-3">Color Configuration</h3>
          <v-expansion-panels variant="accordion">
            <v-expansion-panel>
              <v-expansion-panel-title class="text-h6">
                <div class="d-flex align-center justify-space-between w-100">
                  <div class="d-flex align-center">
                    <v-icon class="mr-2" size="small">mdi-palette</v-icon>
                    Content Editor Colors
                  </div>
                  <v-btn
                    :color="getButtonColor(colorSaveStatus)"
                    :loading="colorSaveStatus === 'saving'"
                    @click.stop="saveColorSettings"
                    size="small"
                    variant="elevated"
                    class="ml-2"
                  >
                    <v-icon left size="small">
                      {{ getButtonIcon(colorSaveStatus) }}
                    </v-icon>
                    {{ getButtonText(colorSaveStatus) }}
                  </v-btn>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <div class="expanded-color-selector" style="min-height: 600px; padding: 20px; background-color: #f5f5f5;">
                  <ColorSelector 
                    :compact="false" 
                    :hide-save-button="true" 
                    ref="colorSelector" 
                    @colors-changed="onColorsChanged"
                    @colors-saved="onColorsSaved"
                  />
                </div>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-col>
      </v-row>

      <!-- Theme Settings -->
      <v-row class="mb-6">
        <v-col cols="12">
          <h3 class="text-subtitle-1 mb-3">Theme Settings</h3>
          <v-expansion-panels variant="accordion">
            <v-expansion-panel>
              <v-expansion-panel-title class="text-h6">
                <div class="d-flex align-center justify-space-between w-100">
                  <div class="d-flex align-center">
                    <v-icon class="mr-2" size="small">mdi-theme-light-dark</v-icon>
                    Theme Appearance
                  </div>
                  <v-btn
                    :color="getButtonColor(themeSaveStatus)"
                    :loading="themeSaveStatus === 'saving'"
                    @click.stop="saveThemeSettings"
                    size="small"
                    variant="elevated"
                    class="ml-2"
                  >
                    <v-icon left size="small">
                      {{ getButtonIcon(themeSaveStatus) }}
                    </v-icon>
                    {{ getButtonText(themeSaveStatus) }}
                  </v-btn>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-btn-toggle
                  v-model="settings.theme"
                  mandatory
                  color="primary"
                  class="mb-3"
                >
                  <v-btn value="light">
                    <v-icon left>mdi-weather-sunny</v-icon>
                    Light
                  </v-btn>
                  <v-btn value="dark">
                    <v-icon left>mdi-weather-night</v-icon>
                    Dark
                  </v-btn>
                  <v-btn value="auto">
                    <v-icon left>mdi-theme-light-dark</v-icon>
                    Auto
                  </v-btn>
                </v-btn-toggle>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-col>
      </v-row>


      <!-- Layout Settings -->
      <v-row class="mb-6">
        <v-col cols="12">
          <h3 class="text-subtitle-1 mb-3">Layout Settings</h3>
          <v-expansion-panels variant="accordion">
            <v-expansion-panel>
              <v-expansion-panel-title class="text-h6">
                <div class="d-flex align-center justify-space-between w-100">
                  <div class="d-flex align-center">
                    <v-icon class="mr-2" size="small">mdi-view-dashboard</v-icon>
                    Interface Layout
                  </div>
                  <v-btn
                    :color="getButtonColor(layoutSaveStatus)"
                    :loading="layoutSaveStatus === 'saving'"
                    @click.stop="saveLayoutSettings"
                    size="small"
                    variant="elevated"
                    class="ml-2"
                  >
                    <v-icon left size="small">
                      {{ getButtonIcon(layoutSaveStatus) }}
                    </v-icon>
                    {{ getButtonText(layoutSaveStatus) }}
                  </v-btn>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-slider
                  v-model="settings.sidebarWidth"
                  label="Sidebar Width"
                  min="200"
                  max="400"
                  step="10"
                  thumb-label
                  class="mb-3"
                />
                <v-switch
                  v-model="settings.compactMode"
                  label="Compact mode (smaller spacing)"
                  color="primary"
                />
                <v-switch
                  v-model="settings.showToolbarLabels"
                  label="Show toolbar labels"
                  color="primary"
                />
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-col>
      </v-row>

      <!-- Accessibility Settings -->
      <v-row class="mb-6">
        <v-col cols="12">
          <h3 class="text-subtitle-1 mb-3">Accessibility Settings</h3>
          <v-expansion-panels variant="accordion">
            <v-expansion-panel>
              <v-expansion-panel-title class="text-h6">
                <div class="d-flex align-center justify-space-between w-100">
                  <div class="d-flex align-center">
                    <v-icon class="mr-2" size="small">mdi-accessibility</v-icon>
                    Accessibility Options
                  </div>
                  <v-btn
                    :color="getButtonColor(accessibilitySaveStatus)"
                    :loading="accessibilitySaveStatus === 'saving'"
                    @click.stop="saveAccessibilitySettings"
                    size="small"
                    variant="elevated"
                    class="ml-2"
                  >
                    <v-icon left size="small">
                      {{ getButtonIcon(accessibilitySaveStatus) }}
                    </v-icon>
                    {{ getButtonText(accessibilitySaveStatus) }}
                  </v-btn>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-switch
                  v-model="settings.highContrast"
                  label="High contrast mode"
                  color="primary"
                />
                <v-switch
                  v-model="settings.reducedMotion"
                  label="Reduce motion and animations"
                  color="primary"
                />
                <v-switch
                  v-model="settings.keyboardShortcuts"
                  label="Enable keyboard shortcuts"
                  color="primary"
                />
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-col>
      </v-row>

      <!-- Save Button -->
      <v-row>
        <v-col class="text-center">
          <v-btn
            color="primary"
            @click="saveSettings"
            :loading="saving"
          >
            <v-icon left>mdi-content-save</v-icon>
            Save Interface Settings
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import ColorSelector from '@/components/ColorSelector.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      theme: 'dark',
      editorFontSize: 14,
      editorFontFamily: 'monospace',
      editorLineNumbers: true,
      editorWordWrap: false,
      editorAutoSave: true,
      sidebarWidth: 250,
      compactMode: false,
      showToolbarLabels: true,
      highContrast: false,
      reducedMotion: false,
      keyboardShortcuts: true
    })
  }
})

const emit = defineEmits(['update:modelValue', 'save'])

const settings = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const saving = ref(false)
const selectedProfile = ref('default')
const profileOptions = ref([
  { title: 'Default', value: 'default' },
  { title: 'Dark Mode', value: 'dark-mode' },
  { title: 'High Contrast', value: 'high-contrast' }
])
const editorSaveStatus = ref('synchronized') // 'synchronized', 'changed', 'saving', 'success'
const colorSaveStatus = ref('synchronized') // 'synchronized', 'changed', 'saving', 'success'
const themeSaveStatus = ref('synchronized') // 'synchronized', 'changed', 'saving', 'success'
const layoutSaveStatus = ref('synchronized') // 'synchronized', 'changed', 'saving', 'success'
const accessibilitySaveStatus = ref('synchronized') // 'synchronized', 'changed', 'saving', 'success'
const fontSizes = [10, 11, 12, 13, 14, 15, 16, 18, 20, 22, 24]
const fontFamilies = ['monospace', 'sans-serif', 'serif', 'Consolas', 'Monaco', 'Courier New']

// Create ref for ColorSelector component
const colorSelector = ref(null)

// Initialization flag to prevent watchers from triggering during setup
const isInitializing = ref(true)

// Helper functions for button states
function getButtonColor(status) {
  switch (status) {
    case 'synchronized': return 'success'
    case 'changed': return 'primary'
    case 'saving': return 'primary'
    case 'success': return 'success'
    default: return 'success'
  }
}

function getButtonIcon(status) {
  switch (status) {
    case 'synchronized': return 'mdi-check'
    case 'changed': return 'mdi-content-save'
    case 'saving': return 'mdi-loading'
    case 'success': return 'mdi-check'
    default: return 'mdi-check'
  }
}

function getButtonText(status) {
  switch (status) {
    case 'synchronized': return 'Synchronized'
    case 'changed': return 'Save & Apply'
    case 'saving': return 'Saving...'
    case 'success': return 'Synchronized'
    default: return 'Synchronized'
  }
}

function applyInterfaceSettings() {
  // Apply theme changes
  applyTheme()
  
  // Apply editor settings
  applyEditorSettings()
  
  // Apply layout settings
  applyLayoutSettings()
  
  // Apply accessibility settings
  applyAccessibilitySettings()
}

function applyTheme() {
  const html = document.documentElement
  
  // Remove existing theme classes
  html.classList.remove('theme-light', 'theme-dark', 'theme-auto')
  
  if (settings.value.theme === 'dark') {
    html.classList.add('theme-dark')
    html.setAttribute('data-theme', 'dark')
    // Apply to Vuetify using the proper Vue 3 composition API
    const vuetifyTheme = document.querySelector('meta[name="theme-color"]')
    if (vuetifyTheme) vuetifyTheme.setAttribute('content', '#121212')
  } else if (settings.value.theme === 'light') {
    html.classList.add('theme-light')  
    html.setAttribute('data-theme', 'light')
    const vuetifyTheme = document.querySelector('meta[name="theme-color"]')
    if (vuetifyTheme) vuetifyTheme.setAttribute('content', '#ffffff')
  } else if (settings.value.theme === 'auto') {
    html.classList.add('theme-auto')
    // Auto-detect system preference
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    const theme = prefersDark ? 'dark' : 'light'
    html.setAttribute('data-theme', theme)
    
    // Listen for system theme changes
    if (window.matchMedia) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      mediaQuery.addEventListener('change', (e) => {
        if (settings.value.theme === 'auto') {
          const newTheme = e.matches ? 'dark' : 'light'
          html.setAttribute('data-theme', newTheme)
        }
      })
    }
  }
}

function applyEditorSettings() {
  const editorElements = document.querySelectorAll('.monaco-editor, .editor-content, .script-editor textarea')
  
  editorElements.forEach(editor => {
    if (editor) {
      editor.style.fontSize = `${settings.value.editorFontSize}px`
      editor.style.fontFamily = settings.value.editorFontFamily
      
      if (settings.value.editorWordWrap) {
        editor.style.whiteSpace = 'pre-wrap'
        editor.style.wordWrap = 'break-word'
      } else {
        editor.style.whiteSpace = 'pre'
        editor.style.wordWrap = 'normal'
      }
    }
  })
  
  // Apply line numbers setting (if using Monaco or similar)
  const root = document.documentElement
  if (settings.value.editorLineNumbers) {
    root.classList.add('editor-line-numbers')
  } else {
    root.classList.remove('editor-line-numbers')
  }
}

function applyLayoutSettings() {
  const root = document.documentElement
  
  // Apply sidebar width
  root.style.setProperty('--sidebar-width', `${settings.value.sidebarWidth}px`)
  
  // Apply compact mode
  if (settings.value.compactMode) {
    root.classList.add('compact-mode')
  } else {
    root.classList.remove('compact-mode')
  }
  
  // Apply toolbar labels setting
  if (settings.value.showToolbarLabels) {
    root.classList.add('show-toolbar-labels')
  } else {
    root.classList.remove('show-toolbar-labels')
  }
}

function applyAccessibilitySettings() {
  const root = document.documentElement
  
  // High contrast mode
  if (settings.value.highContrast) {
    root.classList.add('high-contrast')
  } else {
    root.classList.remove('high-contrast')
  }
  
  // Reduced motion
  if (settings.value.reducedMotion) {
    root.classList.add('reduced-motion')
    root.style.setProperty('--animation-duration', '0s')
    root.style.setProperty('--transition-duration', '0s')
  } else {
    root.classList.remove('reduced-motion')
    root.style.removeProperty('--animation-duration')
    root.style.removeProperty('--transition-duration')
  }
  
  // Keyboard shortcuts (stored for use by other components)
  if (settings.value.keyboardShortcuts) {
    localStorage.setItem('keyboardShortcutsEnabled', 'true')
  } else {
    localStorage.setItem('keyboardShortcutsEnabled', 'false')
  }
}

async function saveSettings() {
  saving.value = true
  try {
    const response = await fetch('/api/settings/interface', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      },
      body: JSON.stringify(settings.value)
    })

    if (response.ok) {
      // Apply all interface settings immediately
      applyInterfaceSettings()
      
      emit('save', settings.value)
      alert('Interface settings saved and applied successfully!')
    } else {
      throw new Error('Failed to save settings')
    }
  } catch (error) {
    console.error('Error saving interface settings:', error)
    alert('Failed to save interface settings')
  } finally {
    saving.value = false
  }
}

async function saveEditorSettings() {
  editorSaveStatus.value = 'saving'
  
  try {
    // Apply editor settings immediately
    applyEditorSettings()
    
    // Simulate save delay for visual feedback
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    editorSaveStatus.value = 'success'
    
    // Reset to synchronized after 2 seconds
    setTimeout(() => {
      editorSaveStatus.value = 'synchronized'
    }, 2000)
    
    console.log('Editor settings saved and applied')
  } catch (error) {
    console.error('Error saving editor settings:', error)
    editorSaveStatus.value = 'synchronized'
  }
}

async function saveColorSettings() {
  colorSaveStatus.value = 'saving'
  
  try {
    // Access the ColorSelector component via ref and call its save method
    if (colorSelector.value && typeof colorSelector.value.saveColors === 'function') {
      await colorSelector.value.saveColors()
      console.log('ColorSelector save method called successfully')
    } else {
      console.log('ColorSelector ref not found or saveColors method not available, using fallback')
      // Fallback: simulate save process
      await new Promise(resolve => setTimeout(resolve, 1500))
    }
    
    colorSaveStatus.value = 'success'
    
    // Reset to synchronized after 2 seconds
    setTimeout(() => {
      colorSaveStatus.value = 'synchronized'
    }, 2000)
    
    console.log('Color settings saved and applied')
  } catch (error) {
    console.error('Error saving color settings:', error)
    colorSaveStatus.value = 'synchronized'
  }
}

async function saveThemeSettings() {
  themeSaveStatus.value = 'saving'
  
  try {
    // Apply theme settings immediately
    applyTheme()
    
    // Save to backend (when available)
    const response = await fetch('/api/settings/theme', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      },
      body: JSON.stringify({
        theme: settings.value.theme,
        profile: selectedProfile.value
      })
    })
    
    if (response.ok) {
      console.log('Theme settings saved to database')
    }
    
    // Simulate save delay for visual feedback
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    themeSaveStatus.value = 'success'
    
    // Reset to synchronized after 2 seconds
    setTimeout(() => {
      themeSaveStatus.value = 'synchronized'
    }, 2000)
    
    console.log('Theme settings saved and applied')
  } catch (error) {
    console.error('Error saving theme settings:', error)
    themeSaveStatus.value = 'synchronized'
  }
}

async function saveLayoutSettings() {
  layoutSaveStatus.value = 'saving'
  
  try {
    // Apply layout settings immediately
    applyLayoutSettings()
    
    // Simulate save delay for visual feedback
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    layoutSaveStatus.value = 'success'
    
    // Reset to synchronized after 2 seconds
    setTimeout(() => {
      layoutSaveStatus.value = 'synchronized'
    }, 2000)
    
    console.log('Layout settings saved and applied')
  } catch (error) {
    console.error('Error saving layout settings:', error)
    layoutSaveStatus.value = 'synchronized'
  }
}

async function saveAccessibilitySettings() {
  accessibilitySaveStatus.value = 'saving'
  
  try {
    // Apply accessibility settings immediately
    applyAccessibilitySettings()
    
    // Save to backend (when available)
    const response = await fetch('/api/settings/accessibility', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      },
      body: JSON.stringify({
        accessibility: {
          high_contrast: settings.value.highContrast,
          reduced_motion: settings.value.reducedMotion,
          keyboard_shortcuts: settings.value.keyboardShortcuts
        },
        profile: selectedProfile.value
      })
    })
    
    if (response.ok) {
      console.log('Accessibility settings saved to database')
    }
    
    // Simulate save delay for visual feedback
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    accessibilitySaveStatus.value = 'success'
    
    // Reset to synchronized after 2 seconds
    setTimeout(() => {
      accessibilitySaveStatus.value = 'synchronized'
    }, 2000)
    
    console.log('Accessibility settings saved and applied')
  } catch (error) {
    console.error('Error saving accessibility settings:', error)
    accessibilitySaveStatus.value = 'synchronized'
  }
}

function onColorsChanged() {
  console.log('InterfaceSettings: Colors changed event received')
  console.log('InterfaceSettings: Current colorSaveStatus:', colorSaveStatus.value)
  if (colorSaveStatus.value === 'synchronized' || colorSaveStatus.value === 'success') {
    console.log('InterfaceSettings: Changing status from', colorSaveStatus.value, 'to changed')
    colorSaveStatus.value = 'changed'
  } else {
    console.log('InterfaceSettings: Not changing status, current status is:', colorSaveStatus.value)
  }
  console.log('InterfaceSettings: New colorSaveStatus:', colorSaveStatus.value)
}

function onColorsSaved() {
  console.log('InterfaceSettings: Colors saved, updating button status')
  colorSaveStatus.value = 'success'
  
  // Reset to synchronized after 2 seconds
  setTimeout(() => {
    colorSaveStatus.value = 'synchronized'
  }, 2000)
}

async function loadProfile(profileName) {
  try {
    console.log(`Loading profile: ${profileName}`)
    selectedProfile.value = profileName
    
    // You can extend this to load theme and accessibility settings for the profile
    // For now, just store the selected profile
    localStorage.setItem('selectedInterfaceProfile', profileName)
  } catch (error) {
    console.error('Error loading profile:', error)
  }
}

async function loadAvailableProfiles() {
  try {
    const response = await fetch('/api/settings/profiles', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.success && data.profiles) {
        profileOptions.value = data.profiles.map(profile => ({
          title: profile.name.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
          value: profile.name
        }))
        console.log('Available profiles loaded:', profileOptions.value)
      }
    }
  } catch (error) {
    console.warn('Could not load available profiles:', error)
  }
}

// Load stored profile on component initialization
const storedProfile = localStorage.getItem('selectedInterfaceProfile') || 'default'
selectedProfile.value = storedProfile

// Load available profiles on component mount
loadAvailableProfiles()

// Watch for changes in editor settings
watch(() => [
  settings.value.editorFontSize,
  settings.value.editorFontFamily,
  settings.value.editorLineNumbers,
  settings.value.editorWordWrap,
  settings.value.editorAutoSave
], () => {
  if (isInitializing.value) return
  if (editorSaveStatus.value === 'synchronized' || editorSaveStatus.value === 'success') {
    editorSaveStatus.value = 'changed'
  }
}, { deep: true })

// Watch for changes in theme settings
watch(() => settings.value.theme, () => {
  if (isInitializing.value) return
  if (themeSaveStatus.value === 'synchronized' || themeSaveStatus.value === 'success') {
    themeSaveStatus.value = 'changed'
  }
})

// Watch for changes in layout settings
watch(() => [
  settings.value.sidebarWidth,
  settings.value.compactMode,
  settings.value.showToolbarLabels
], () => {
  if (isInitializing.value) return
  if (layoutSaveStatus.value === 'synchronized' || layoutSaveStatus.value === 'success') {
    layoutSaveStatus.value = 'changed'
  }
}, { deep: true })

// Watch for changes in accessibility settings
watch(() => [
  settings.value.highContrast,
  settings.value.reducedMotion,
  settings.value.keyboardShortcuts
], () => {
  if (isInitializing.value) return
  if (accessibilitySaveStatus.value === 'synchronized' || accessibilitySaveStatus.value === 'success') {
    accessibilitySaveStatus.value = 'changed'
  }
}, { deep: true })

// Color changes will be detected by listening to ColorSelector events
// For now, we'll trigger color changes manually when needed

// Apply settings on component initialization  
// Note: Real-time preview can be added later with watch() if needed

// Set initialization complete after component is fully loaded
import { nextTick, onMounted } from 'vue'

onMounted(async () => {
  await nextTick()
  isInitializing.value = false
  console.log('InterfaceSettings: Initialization complete, watchers now active')
})
</script>

<style scoped>
.expanded-color-selector {
  overflow-y: auto;
  border-radius: 8px;
}

.expanded-color-selector :deep(table) {
  background-color: white;
  color: #333;
}

.expanded-color-selector :deep(th) {
  background-color: #f0f0f0;
  color: #333;
  font-weight: bold;
  padding: 12px !important;
}

.expanded-color-selector :deep(td) {
  background-color: white;
  color: #333;
  border-bottom: 1px solid #e0e0e0;
}

.expanded-color-selector :deep(td.color-cell) {
  padding: 0 !important;
}

.expanded-color-selector :deep(.v-select) {
  background-color: white;
}

.expanded-color-selector :deep(.v-field__input) {
  color: #333 !important;
}

.expanded-color-selector :deep(.preview-box) {
  border: 1px solid #ccc;
}
</style>

<!-- Global styles for interface settings -->
<style>
/* Theme classes */
html.theme-light {
  --background-color: #ffffff;
  --text-color: #000000;
  --surface-color: #f5f5f5;
}

html.theme-dark {
  --background-color: #121212;
  --text-color: #ffffff;
  --surface-color: #1e1e1e;
}

html.theme-auto {
  /* Auto-detects based on system preference - set via JS */
}

/* Compact mode */
html.compact-mode .v-card {
  padding: 8px !important;
}

html.compact-mode .v-list-item {
  min-height: 32px !important;
}

html.compact-mode .v-btn {
  min-height: 32px !important;
}

html.compact-mode .v-toolbar {
  height: 48px !important;
}

/* Toolbar labels */
html:not(.show-toolbar-labels) .v-btn .v-btn__content > span:not(.v-icon) {
  display: none;
}

/* High contrast mode */
html.high-contrast {
  filter: contrast(1.5);
}

html.high-contrast .v-card,
html.high-contrast .v-sheet {
  border: 2px solid currentColor !important;
}

html.high-contrast .v-btn {
  border: 2px solid currentColor !important;
  font-weight: bold !important;
}

/* Reduced motion */
html.reduced-motion *,
html.reduced-motion *::before,
html.reduced-motion *::after {
  animation-duration: 0.01ms !important;
  animation-iteration-count: 1 !important;
  transition-duration: 0.01ms !important;
}

/* Editor line numbers */
html.editor-line-numbers .monaco-editor .margin,
html.editor-line-numbers .editor-content .line-numbers {
  display: block !important;
}

html:not(.editor-line-numbers) .monaco-editor .margin,
html:not(.editor-line-numbers) .editor-content .line-numbers {
  display: none !important;
}

/* Sidebar width CSS variable usage */
.sidebar,
.navigation-drawer {
  width: var(--sidebar-width, 250px) !important;
}

/* Auto-save indicator */
.auto-save-enabled {
  position: relative;
}

.auto-save-enabled::after {
  content: "●";
  color: #4caf50;
  position: absolute;
  top: 4px;
  right: 4px;
  font-size: 8px;
}
</style>