<template>
  <v-card class="pa-4">
    <v-card-title class="text-h6 mb-4">
      <v-icon left>mdi-format-list-bulleted</v-icon>
      Rundown Settings
    </v-card-title>
    <v-card-text>
      <p class="text-body-2 mb-4">Configure rundown behavior, defaults, and item types.</p>
      

      <!-- Timing Settings -->
      <v-row class="mb-6">
        <v-col cols="12">
          <h3 class="text-subtitle-1 mb-3">Timing & Duration</h3>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="settings.defaultSegmentDuration"
                label="Default Segment Duration (seconds)"
                type="number"
                suffix="seconds"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="settings.defaultBreakDuration"
                label="Default Break Duration (seconds)"
                type="number"
                suffix="seconds"
              />
            </v-col>
          </v-row>
          <v-switch
            v-model="settings.showBacktiming"
            label="Show backtiming in rundown"
            color="primary"
          />
          <v-switch
            v-model="settings.autoCalculateTiming"
            label="Auto-calculate segment timing"
            color="primary"
          />
        </v-col>
      </v-row>

      <!-- Auto-numbering -->
      <v-row class="mb-6">
        <v-col cols="12">
          <h3 class="text-subtitle-1 mb-3">Auto-numbering</h3>
          <v-switch
            v-model="settings.autoNumber"
            label="Auto-number rundown items"
            color="primary"
          />
          <v-switch
            v-model="settings.enumerateMarkdownFiles"
            label="Enumerate rundown item markdown files with order number"
            color="primary"
            class="mt-2"
          />
          <div class="text-caption text-grey ml-8 mt-1 mb-3">
            When enabled: "010-coldopen-show-cold-open.md", when disabled: "coldopen-show-cold-open.md"
          </div>
          <v-row v-if="settings.autoNumber">
            <v-col cols="12" md="6">
              <v-text-field
                v-model="settings.numberingStart"
                label="Starting Number"
                type="number"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="settings.numberingStep"
                label="Step Increment"
                type="number"
              />
            </v-col>
          </v-row>
        </v-col>
      </v-row>

      <!-- Export Settings -->
      <v-row class="mb-6">
        <v-col cols="12">
          <h3 class="text-subtitle-1 mb-3">Export Defaults</h3>
          <v-select
            v-model="settings.defaultExportFormat"
            :items="['Markdown', 'PDF', 'HTML', 'JSON', 'CSV']"
            label="Default Export Format"
          />
          <v-switch
            v-model="settings.includeTimingInExport"
            label="Include timing in exports"
            color="primary"
          />
          <v-switch
            v-model="settings.includeNotesInExport"
            label="Include production notes in exports"
            color="primary"
          />
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
            Save Rundown Settings
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>

    <!-- Snackbar for messages -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
      location="bottom"
    >
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      defaultSegmentDuration: 300,
      defaultBreakDuration: 120,
      showBacktiming: true,
      autoCalculateTiming: true,
      autoNumber: true,
      enumerateMarkdownFiles: true,
      numberingStart: 1,
      numberingStep: 1,
      defaultExportFormat: 'Markdown',
      includeTimingInExport: true,
      includeNotesInExport: true
    })
  }
})

const emit = defineEmits(['update:modelValue', 'save'])

const settings = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const saving = ref(false)

// Snackbar state
const snackbar = ref({
  show: false,
  message: '',
  color: 'success',
  timeout: 4000
})

const showSnackbar = (message, color = 'success') => {
  snackbar.value.message = message
  snackbar.value.color = color
  snackbar.value.show = true
}

async function loadSettings() {
  try {
    const response = await fetch('/api/settings/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'X-API-Key': localStorage.getItem('api_key')
      }
    })

    if (response.ok) {
      const data = await response.json()
      const rundownData = data.rundown || {}
      
      // Map backend settings to frontend format
      if (Object.keys(rundownData).length > 0) {
        settings.value = {
          ...settings.value,
          showBacktiming: rundownData.show_cumulative_time ?? settings.value.showBacktiming,
          autoCalculateTiming: rundownData.auto_calculate_duration ?? settings.value.autoCalculateTiming,
          autoNumber: rundownData.auto_number_rundown_items ?? settings.value.autoNumber,
          enumerateMarkdownFiles: rundownData.enumerate_rundown_markdown_files ?? settings.value.enumerateMarkdownFiles
        }
      }
    } else {
      console.warn('Could not load settings, using defaults')
    }
  } catch (error) {
    console.error('Error loading rundown settings:', error)
  }
}

async function saveSettings() {
  saving.value = true
  try {
    // Map frontend settings to backend API format
    const backendSettings = {
      default_segment_duration: "00:05:00", // Convert to time format
      enable_timecode: true,
      timecode_format: "HH:MM:SS", 
      show_cumulative_time: settings.value.showBacktiming || true,
      enable_drag_drop: true,
      auto_calculate_duration: settings.value.autoCalculateTiming || true,
      warn_on_delete: true,
      show_item_numbers: true,
      auto_number_rundown_items: settings.value.autoNumber || true,
      enumerate_rundown_markdown_files: settings.value.enumerateMarkdownFiles || true
    }

    const response = await fetch('/api/settings/rundown', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'X-API-Key': localStorage.getItem('api_key')
      },
      body: JSON.stringify(backendSettings)
    })

    if (response.ok) {
      emit('save', settings.value)
      showSnackbar('Rundown settings saved successfully', 'success')
    } else {
      const errorData = await response.text()
      console.error('Save failed:', errorData)
      throw new Error('Failed to save settings')
    }
  } catch (error) {
    console.error('Error saving rundown settings:', error)
    showSnackbar('Failed to save rundown settings', 'error')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.v-list-item {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.v-list-item:last-child {
  border-bottom: none;
}
</style>