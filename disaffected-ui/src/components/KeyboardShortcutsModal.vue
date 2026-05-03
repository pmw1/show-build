<template>
  <v-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" max-width="900" scrollable>
    <v-card class="shortcuts-card">
      <v-card-title class="d-flex align-center bg-indigo text-white py-2">
        <v-icon size="small" class="me-2">mdi-keyboard</v-icon>
        <span class="text-body-1">Keyboard Shortcuts</span>
        <v-spacer />
        <v-btn icon size="x-small" variant="text" color="white" @click="$emit('update:modelValue', false)">
          <v-icon size="small">mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-tabs v-model="activeTab" density="compact" bg-color="grey-lighten-4" color="indigo">
        <v-tab value="shortcuts">
          <v-icon size="small" start>mdi-keyboard-outline</v-icon>
          Shortcuts
        </v-tab>
        <v-tab value="conflicts">
          <v-icon size="small" start>mdi-alert</v-icon>
          Conflicts ({{ conflicts.length }})
        </v-tab>
      </v-tabs>

      <v-card-text class="pa-3 shortcuts-body">
        <v-window v-model="activeTab">
          <!-- Shortcuts tab -->
          <v-window-item value="shortcuts">
            <v-text-field
              v-model="filter"
              placeholder="Filter shortcuts…"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              class="mb-3"
              autofocus
            />

            <div v-for="section in filteredSections" :key="section.id" class="shortcut-section mb-3">
              <div class="section-header">
                <v-icon size="small" class="me-2" color="indigo">{{ section.icon }}</v-icon>
                <span>{{ section.title }}</span>
              </div>
              <div class="shortcut-list">
                <div
                  v-for="(sc, idx) in section.shortcuts"
                  :key="`${section.id}-${idx}`"
                  class="shortcut-row"
                >
                  <div class="shortcut-keys">
                    <template v-for="(key, ki) in sc.keys" :key="ki">
                      <kbd class="sc-kbd">{{ key }}</kbd>
                      <span v-if="ki < sc.keys.length - 1" class="sc-sep">or</span>
                    </template>
                  </div>
                  <div class="shortcut-label">
                    {{ sc.label }}
                    <span v-if="sc.notes" class="shortcut-notes">— {{ sc.notes }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="filteredSections.length === 0" class="text-center text-grey py-4">
              No shortcuts match "{{ filter }}"
            </div>
          </v-window-item>

          <!-- Conflicts tab -->
          <v-window-item value="conflicts">
            <div class="text-caption text-grey mb-2">
              Known overlaps between app shortcuts, other views, or browser defaults. Most are context-isolated.
            </div>
            <div v-for="(c, idx) in conflicts" :key="idx" class="conflict-row">
              <div class="conflict-keys">
                <kbd class="sc-kbd">{{ c.keys }}</kbd>
              </div>
              <div class="conflict-details">
                <div class="conflict-contexts">
                  <v-chip v-for="ctx in c.contexts" :key="ctx" size="x-small" variant="outlined" class="me-1 mb-1">
                    {{ ctx }}
                  </v-chip>
                </div>
                <div class="conflict-note">{{ c.note }}</div>
              </div>
            </div>
          </v-window-item>
        </v-window>
      </v-card-text>

      <v-card-actions class="px-3 py-2 bg-grey-lighten-5">
        <span class="text-caption text-grey">
          Press <kbd class="sc-kbd sc-kbd-inline">?</kbd> or <kbd class="sc-kbd sc-kbd-inline">F1</kbd> anywhere to open this.
          <kbd class="sc-kbd sc-kbd-inline">Esc</kbd> to close.
        </span>
        <v-spacer />
        <v-btn size="small" variant="text" @click="$emit('update:modelValue', false)">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { shortcutSections, knownConflicts } from '@/data/keyboardShortcuts'

defineProps({
  modelValue: { type: Boolean, required: true }
})

defineEmits(['update:modelValue'])

const activeTab = ref('shortcuts')
const filter = ref('')
const conflicts = knownConflicts

const filteredSections = computed(() => {
  const q = (filter.value || '').trim().toLowerCase()
  if (!q) return shortcutSections
  return shortcutSections
    .map(section => ({
      ...section,
      shortcuts: section.shortcuts.filter(sc => {
        const hay = [
          ...(sc.keys || []),
          sc.label || '',
          sc.notes || '',
          section.title
        ].join(' ').toLowerCase()
        return hay.includes(q)
      })
    }))
    .filter(section => section.shortcuts.length > 0)
})
</script>

<style scoped>
.shortcuts-card {
  border-radius: 4px !important;
  overflow: hidden;
}

.shortcuts-body {
  max-height: 70vh;
}

.shortcut-section + .shortcut-section {
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  padding-top: 10px;
}

.section-header {
  display: flex;
  align-items: center;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #3949ab;
  margin-bottom: 6px;
}

.shortcut-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.shortcut-row {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 12px;
  align-items: baseline;
  padding: 3px 6px;
  border-radius: 3px;
}

.shortcut-row:nth-child(odd) {
  background: rgba(0, 0, 0, 0.02);
}

.shortcut-keys {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.sc-kbd {
  display: inline-block;
  font-family: ui-monospace, 'SF Mono', Monaco, 'Cascadia Code', Consolas, monospace;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 6px;
  background: #f5f5f5;
  border: 1px solid #d0d0d0;
  border-bottom-width: 2px;
  border-radius: 3px;
  color: #333;
  white-space: nowrap;
}

.sc-kbd-inline {
  font-size: 0.68rem;
  padding: 1px 4px;
}

.sc-sep {
  font-size: 0.68rem;
  color: #888;
  text-transform: uppercase;
}

.shortcut-label {
  font-size: 0.82rem;
  color: rgba(0, 0, 0, 0.8);
}

.shortcut-notes {
  font-size: 0.72rem;
  color: #888;
  font-style: italic;
}

.conflict-row {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 12px;
  padding: 8px 6px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  align-items: start;
}

.conflict-keys .sc-kbd {
  white-space: normal;
}

.conflict-contexts {
  margin-bottom: 4px;
}

.conflict-note {
  font-size: 0.75rem;
  color: #666;
  line-height: 1.4;
}
</style>
