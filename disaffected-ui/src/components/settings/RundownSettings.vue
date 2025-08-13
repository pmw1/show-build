<template>
  <v-card class="pa-4">
    <v-card-title class="text-h6 mb-4">
      <v-icon left>mdi-format-list-bulleted</v-icon>
      Rundown Settings
    </v-card-title>
    <v-card-text>
      <p class="text-body-2 mb-4">Configure rundown behavior, defaults, and item types.</p>
      
      <!-- Default Rundown Item Types -->
      <v-row class="mb-6">
        <v-col cols="12">
          <h3 class="text-subtitle-1 mb-3">Rundown Item Types</h3>
          <p class="text-body-2 mb-3">Configure available rundown item types and their default settings.</p>
          
          <v-list>
            <v-list-item
              v-for="itemType in settings.itemTypes"
              :key="itemType.id"
              class="px-0"
            >
              <v-row align="center">
                <v-col cols="3">
                  <v-text-field
                    v-model="itemType.name"
                    label="Type Name"
                    dense
                  />
                </v-col>
                <v-col cols="2">
                  <v-select
                    v-model="itemType.color"
                    :items="['primary', 'secondary', 'success', 'warning', 'error', 'info']"
                    label="Color"
                    dense
                  />
                </v-col>
                <v-col cols="2">
                  <v-text-field
                    v-model="itemType.prefix"
                    label="Prefix"
                    dense
                    placeholder="SEG"
                  />
                </v-col>
                <v-col cols="2">
                  <v-text-field
                    v-model="itemType.defaultDuration"
                    label="Duration (sec)"
                    type="number"
                    dense
                  />
                </v-col>
                <v-col cols="2">
                  <v-switch
                    v-model="itemType.enabled"
                    label="Enabled"
                    dense
                  />
                </v-col>
                <v-col cols="1">
                  <v-btn
                    @click="removeItemType(itemType.id)"
                    color="error"
                    variant="text"
                    size="small"
                  >
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </v-col>
              </v-row>
            </v-list-item>
          </v-list>
          
          <v-btn
            @click="addItemType"
            color="primary"
            variant="outlined"
            class="mt-2"
          >
            <v-icon left>mdi-plus</v-icon>
            Add Item Type
          </v-btn>
        </v-col>
      </v-row>

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
  </v-card>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      itemTypes: [
        { id: 1, name: 'Segment', prefix: 'SEG', defaultDuration: 300, color: 'primary', enabled: true },
        { id: 2, name: 'Break', prefix: 'BRK', defaultDuration: 120, color: 'warning', enabled: true },
        { id: 3, name: 'Package', prefix: 'PKG', defaultDuration: 180, color: 'info', enabled: true },
        { id: 4, name: 'Interview', prefix: 'INT', defaultDuration: 240, color: 'success', enabled: true }
      ],
      defaultSegmentDuration: 300,
      defaultBreakDuration: 120,
      showBacktiming: true,
      autoCalculateTiming: true,
      autoNumber: true,
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
let nextItemId = ref(Math.max(...props.modelValue.itemTypes.map(t => t.id)) + 1)

function removeItemType(id) {
  const index = settings.value.itemTypes.findIndex(t => t.id === id)
  if (index > -1) {
    settings.value.itemTypes.splice(index, 1)
  }
}

function addItemType() {
  settings.value.itemTypes.push({
    id: nextItemId.value++,
    name: 'New Type',
    prefix: 'NEW',
    defaultDuration: 180,
    color: 'secondary',
    enabled: true
  })
}

async function saveSettings() {
  saving.value = true
  try {
    const response = await fetch('/api/settings/rundown', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(settings.value)
    })

    if (response.ok) {
      emit('save', settings.value)
      alert('Rundown settings saved successfully')
    } else {
      throw new Error('Failed to save settings')
    }
  } catch (error) {
    console.error('Error saving rundown settings:', error)
    alert('Failed to save rundown settings')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.v-list-item {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.v-list-item:last-child {
  border-bottom: none;
}
</style>