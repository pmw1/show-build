<template>
  <v-card flat>
    <v-card-title class="d-flex align-center">
      <v-icon class="me-2">mdi-notebook-edit</v-icon>
      Whiteboard Settings
    </v-card-title>
    <v-card-text>
      <!-- Parent Node Types -->
      <h3 class="text-h6 mb-3">Parent Node Types</h3>
      <p class="text-body-2 text-grey mb-4">
        Configure the types of parent nodes available in the whiteboard mindmap.
      </p>

      <v-table density="compact" class="mb-4">
        <thead>
          <tr>
            <th>Name</th>
            <th>Color</th>
            <th>Icon</th>
            <th>Preview</th>
            <th width="80">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(nodeType, index) in parentNodeTypes" :key="index">
            <td>
              <v-text-field
                v-model="nodeType.name"
                variant="plain"
                density="compact"
                hide-details
                placeholder="Type name"
              ></v-text-field>
            </td>
            <td>
              <v-menu :close-on-content-click="false">
                <template v-slot:activator="{ props }">
                  <v-btn
                    v-bind="props"
                    size="small"
                    variant="flat"
                    :color="nodeType.color"
                    class="text-white"
                  >
                    {{ nodeType.color }}
                  </v-btn>
                </template>
                <v-color-picker
                  v-model="nodeType.color"
                  mode="hex"
                  :swatches="colorSwatches"
                  show-swatches
                ></v-color-picker>
              </v-menu>
            </td>
            <td>
              <v-select
                v-model="nodeType.icon"
                :items="iconOptions"
                variant="plain"
                density="compact"
                hide-details
                item-title="label"
                item-value="value"
              >
                <template v-slot:prepend-inner>
                  <v-icon size="small">{{ nodeType.icon }}</v-icon>
                </template>
              </v-select>
            </td>
            <td>
              <v-chip :color="nodeType.color" variant="flat" size="small">
                <v-icon size="small" start>{{ nodeType.icon }}</v-icon>
                {{ nodeType.name }}
              </v-chip>
            </td>
            <td>
              <v-btn
                size="x-small"
                icon="mdi-delete"
                variant="text"
                color="error"
                @click="removeNodeType(index)"
              ></v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>

      <v-btn
        size="small"
        variant="tonal"
        color="primary"
        prepend-icon="mdi-plus"
        @click="addNodeType"
        class="mb-6"
      >
        Add Node Type
      </v-btn>

      <v-divider class="mb-6"></v-divider>

      <!-- Connection Line Style -->
      <h3 class="text-h6 mb-3">Connection Lines</h3>

      <v-row>
        <v-col cols="6">
          <v-select
            v-model="lineStyle"
            :items="['curved', 'straight']"
            label="Line Style"
            variant="outlined"
            density="compact"
            hide-details
          ></v-select>
        </v-col>
        <v-col cols="6">
          <v-select
            v-model="defaultLineColor"
            :items="lineColorOptions"
            label="Default Line Color"
            variant="outlined"
            density="compact"
            hide-details
            item-title="label"
            item-value="value"
          >
            <template v-slot:prepend-inner>
              <div :style="{ width: '16px', height: '16px', borderRadius: '50%', background: defaultLineColor }"></div>
            </template>
          </v-select>
        </v-col>
      </v-row>

      <v-checkbox
        v-model="showLabels"
        label="Show connection labels by default"
        density="compact"
        hide-details
        class="mt-2 mb-6"
      ></v-checkbox>

      <v-divider class="mb-6"></v-divider>

      <!-- Default Zoom -->
      <h3 class="text-h6 mb-3">Default Zoom</h3>
      <v-select
        v-model="defaultZoom"
        :items="[
          { title: '100%', value: 1.0 },
          { title: '65%', value: 0.65 },
          { title: '40%', value: 0.4 }
        ]"
        label="Default zoom level"
        variant="outlined"
        density="compact"
        hide-details
        class="mb-6"
        style="max-width: 200px;"
      ></v-select>
    </v-card-text>

    <v-card-actions>
      <v-btn
        variant="text"
        @click="resetDefaults"
      >
        Reset to Defaults
      </v-btn>
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        variant="elevated"
        prepend-icon="mdi-content-save"
        :loading="saving"
        @click="saveSettings"
      >
        Save Whiteboard Settings
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { fetchJson } from '@/utils/apiHelpers'
import { useStandardNotification, NOTIFICATION_COLORS } from '@/composables/useStandardNotification'

const { notifyUserStandard } = useStandardNotification()

const saving = ref(false)

const defaultParentNodeTypes = [
  { name: 'Segment', color: '#2196F3', icon: 'mdi-filmstrip' },
  { name: 'Interview', color: '#009688', icon: 'mdi-account-voice' },
  { name: 'Topic', color: '#9C27B0', icon: 'mdi-tag' },
  { name: 'Research', color: '#FF9800', icon: 'mdi-magnify' }
]

const parentNodeTypes = ref([...defaultParentNodeTypes.map(t => ({ ...t }))])
const lineStyle = ref('curved')
const defaultLineColor = ref('#1976d2')
const showLabels = ref(true)
const defaultZoom = ref(1.0)

const iconOptions = [
  { label: 'Filmstrip', value: 'mdi-filmstrip' },
  { label: 'Account Voice', value: 'mdi-account-voice' },
  { label: 'Tag', value: 'mdi-tag' },
  { label: 'Magnify', value: 'mdi-magnify' },
  { label: 'Lightbulb', value: 'mdi-lightbulb' },
  { label: 'Star', value: 'mdi-star' },
  { label: 'Hub', value: 'mdi-hub' },
  { label: 'Chat', value: 'mdi-chat' },
  { label: 'Video', value: 'mdi-video' },
  { label: 'Music', value: 'mdi-music-note' },
  { label: 'Image', value: 'mdi-image' },
  { label: 'Link', value: 'mdi-link' },
  { label: 'Flag', value: 'mdi-flag' },
  { label: 'Alert', value: 'mdi-alert' },
  { label: 'Bookmark', value: 'mdi-bookmark' },
  { label: 'Code', value: 'mdi-code-braces' }
]

const colorSwatches = [
  ['#2196F3', '#1976D2', '#0D47A1'],
  ['#009688', '#00796B', '#004D40'],
  ['#9C27B0', '#7B1FA2', '#4A148C'],
  ['#FF9800', '#F57C00', '#E65100'],
  ['#F44336', '#D32F2F', '#B71C1C'],
  ['#4CAF50', '#388E3C', '#1B5E20']
]

const lineColorOptions = [
  { label: 'Blue', value: '#1976d2' },
  { label: 'Grey', value: '#757575' },
  { label: 'Teal', value: '#009688' },
  { label: 'Orange', value: '#FF9800' },
  { label: 'Red', value: '#F44336' }
]

function addNodeType() {
  parentNodeTypes.value.push({
    name: 'New Type',
    color: '#607D8B',
    icon: 'mdi-hub'
  })
}

function removeNodeType(index) {
  parentNodeTypes.value.splice(index, 1)
}

function resetDefaults() {
  parentNodeTypes.value = [...defaultParentNodeTypes.map(t => ({ ...t }))]
  lineStyle.value = 'curved'
  defaultLineColor.value = '#1976d2'
  showLabels.value = true
  defaultZoom.value = 1.0
}

async function loadSettings() {
  try {
    const response = await fetchJson('/api/settings/api-configs')
    if (response?.success && response?.data) {
      const wb = response.data.whiteboard
      if (wb) {
        if (wb.parent_node_types) parentNodeTypes.value = wb.parent_node_types
        if (wb.line_style) lineStyle.value = wb.line_style
        if (wb.default_line_color) defaultLineColor.value = wb.default_line_color
        if (wb.show_labels !== undefined) showLabels.value = wb.show_labels
        if (wb.default_zoom) defaultZoom.value = wb.default_zoom
      }
    }
  } catch {
    // Use defaults silently
  }
}

async function saveSettings() {
  saving.value = true
  try {
    // Load existing config, merge whiteboard section
    const existing = await fetchJson('/api/settings/api-configs')
    const config = existing?.data || {}

    config.whiteboard = {
      parent_node_types: parentNodeTypes.value,
      line_style: lineStyle.value,
      default_line_color: defaultLineColor.value,
      show_labels: showLabels.value,
      default_zoom: defaultZoom.value
    }

    await fetchJson('/api/settings/api-configs', {
      method: 'POST',
      body: JSON.stringify({ config })
    })

    notifyUserStandard('Whiteboard settings saved', NOTIFICATION_COLORS.SUCCESS, 3000)
  } catch (error) {
    console.error('Failed to save whiteboard settings:', error)
    notifyUserStandard('Failed to save settings', NOTIFICATION_COLORS.ERROR, 3000)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>
