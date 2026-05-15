<template>
  <v-card variant="outlined" class="mb-4">
    <v-card-title class="d-flex align-center">
      <v-icon class="mr-2">mdi-brain</v-icon>
      Meta Extraction Settings
    </v-card-title>
    <v-card-subtitle>
      Configure which rundown item types are eligible for LLM metadata extraction
    </v-card-subtitle>
    <v-divider />
    <v-card-text>
      <v-alert type="info" variant="tonal" density="compact" class="mb-4">
        Select which item types should appear in the MetaFactory extraction tool.
        Unselected types will be hidden from the extraction list.
      </v-alert>

      <div class="text-subtitle-2 mb-2">Eligible Item Types</div>

      <v-row>
        <v-col
          v-for="itemType in allItemTypes"
          :key="itemType.value"
          cols="12"
          sm="6"
          md="4"
        >
          <v-checkbox
            v-model="selectedTypes"
            :value="itemType.value"
            :label="itemType.title"
            density="compact"
            hide-details
            class="item-type-checkbox"
          >
            <template v-slot:label>
              <div class="d-flex align-center">
                <v-icon :color="itemType.color" size="small" class="mr-2">
                  {{ itemType.icon }}
                </v-icon>
                <span>{{ itemType.title }}</span>
              </div>
            </template>
          </v-checkbox>
        </v-col>
      </v-row>

      <v-divider class="my-4" />

      <div class="text-subtitle-2 mb-2">Autorun</div>
      <v-alert type="info" variant="tonal" density="compact" class="mb-3">
        Skip the manual button-clicking. With autorun on, eligible segments fire their entity
        extraction automatically — Phase 1 when MetaFactory loads a rundown, Phase 2 the moment
        Phase 1 finishes.
      </v-alert>
      <v-row>
        <v-col cols="12" md="6">
          <v-switch
            v-model="autorunPhase1"
            color="primary"
            density="compact"
            hide-details
            inset
          >
            <template v-slot:label>
              <div class="d-flex align-center">
                <v-icon color="primary" size="small" class="mr-2">mdi-brain</v-icon>
                <div>
                  <div class="text-body-2 font-weight-medium">Auto-fire Phase 1 (Ollama)</div>
                  <div class="text-caption text-medium-emphasis">
                    Extract entities automatically on every eligible segment when MetaFactory loads.
                  </div>
                </div>
              </div>
            </template>
          </v-switch>
        </v-col>
        <v-col cols="12" md="6">
          <v-switch
            v-model="autorunPhase2"
            color="purple"
            density="compact"
            hide-details
            inset
          >
            <template v-slot:label>
              <div class="d-flex align-center">
                <v-icon color="purple" size="small" class="mr-2">mdi-creation</v-icon>
                <div>
                  <div class="text-body-2 font-weight-medium">Auto-fire Phase 2 (Grok)</div>
                  <div class="text-caption text-medium-emphasis">
                    Run Grok enrichment immediately after Phase 1 completes. Costs API credits.
                  </div>
                </div>
              </div>
            </template>
          </v-switch>
        </v-col>
      </v-row>

      <v-divider class="my-4" />

      <div class="d-flex align-center ga-2">
        <v-btn
          color="primary"
          variant="flat"
          @click="saveSettings"
          :loading="saving"
          :disabled="!hasChanges"
        >
          Save Changes
        </v-btn>
        <v-btn
          variant="tonal"
          @click="resetToDefaults"
          :disabled="saving"
        >
          Reset to Defaults
        </v-btn>
        <v-spacer />
        <v-chip
          v-if="hasChanges"
          color="warning"
          variant="tonal"
          size="small"
        >
          Unsaved changes
        </v-chip>
        <v-chip
          v-else-if="lastSaved"
          color="success"
          variant="tonal"
          size="small"
        >
          Saved
        </v-chip>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { CORE_ITEM_TYPES } from '@/config/itemTypes'
import axios from 'axios'

const allItemTypes = ref([...CORE_ITEM_TYPES])
const selectedTypes = ref([])
const originalTypes = ref([])
const defaultTypes = ref([])
const autorunPhase1 = ref(false)
const autorunPhase2 = ref(false)
const originalAutorunPhase1 = ref(false)
const originalAutorunPhase2 = ref(false)
const saving = ref(false)
const lastSaved = ref(false)

const hasChanges = computed(() => {
  if (selectedTypes.value.length !== originalTypes.value.length) return true
  if (!selectedTypes.value.every(t => originalTypes.value.includes(t))) return true
  if (autorunPhase1.value !== originalAutorunPhase1.value) return true
  if (autorunPhase2.value !== originalAutorunPhase2.value) return true
  return false
})

function getAuthHeaders() {
  const token = localStorage.getItem('auth-token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

async function loadSettings() {
  try {
    const response = await axios.get('/api/settings/meta_extraction', { headers: getAuthHeaders() })
    if (response.data?.item_types) {
      selectedTypes.value = [...response.data.item_types]
      originalTypes.value = [...response.data.item_types]
    }
    if (response.data?.defaults) defaultTypes.value = [...response.data.defaults]
    autorunPhase1.value = !!response.data?.autorun_phase1
    autorunPhase2.value = !!response.data?.autorun_phase2
    originalAutorunPhase1.value = autorunPhase1.value
    originalAutorunPhase2.value = autorunPhase2.value
  } catch (error) {
    console.error('Failed to load meta extraction settings:', error)
  }
}

async function saveSettings() {
  saving.value = true
  lastSaved.value = false
  try {
    await axios.post('/api/settings/meta_extraction', {
      item_types: selectedTypes.value,
      autorun_phase1: autorunPhase1.value,
      autorun_phase2: autorunPhase2.value,
    }, { headers: getAuthHeaders() })
    originalTypes.value = [...selectedTypes.value]
    originalAutorunPhase1.value = autorunPhase1.value
    originalAutorunPhase2.value = autorunPhase2.value
    lastSaved.value = true
    setTimeout(() => { lastSaved.value = false }, 3000)
  } catch (error) {
    console.error('Failed to save meta extraction settings:', error)
  } finally {
    saving.value = false
  }
}

function resetToDefaults() {
  selectedTypes.value = [...defaultTypes.value]
  autorunPhase1.value = false
  autorunPhase2.value = false
}

onMounted(loadSettings)
</script>

<style scoped>
.item-type-checkbox {
  margin-bottom: 4px;
}
</style>
