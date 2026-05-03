<template>
  <v-dialog
    :model-value="showModal"
    @update:model-value="showModal = $event"
    max-width="800"
    content-class="hotkey-modal-dialog"
  >
    <v-card class="hotkey-modal-card">
      <v-card-title class="hotkey-modal-header d-flex align-center">
        <v-icon class="me-2" color="amber">mdi-keyboard</v-icon>
        <span>Keyboard Shortcuts</span>
        <v-spacer />
        <v-chip size="x-small" variant="outlined" color="grey-lighten-1" class="me-2">
          Alt + 1 to close
        </v-chip>
        <v-btn icon size="x-small" variant="text" color="grey-lighten-1" @click="showModal = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text class="hotkey-modal-body pa-0">
        <div v-for="group in hotkeyGroups" :key="group.section" class="hotkey-section">
          <div class="hotkey-section-header" :class="{ 'hotkey-section-active': group.active }">
            <v-icon v-if="group.active" size="small" color="amber" class="me-1">mdi-star</v-icon>
            {{ group.section }}
            <v-chip v-if="group.active" size="x-small" color="amber" variant="tonal" class="ms-2">Current</v-chip>
          </div>
          <div class="hotkey-entries">
            <div
              v-for="(entry, idx) in group.entries"
              :key="idx"
              class="hotkey-row"
            >
              <span class="hotkey-description">{{ entry.description }}</span>
              <span class="hotkey-keys">
                <kbd v-for="(part, pi) in parseKeys(entry.keys)" :key="pi" class="hotkey-kbd">{{ part }}</kbd>
              </span>
            </div>
          </div>
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { useHotkeys } from '@/composables/useHotkeys'

const { showModal, getSortedHotkeys } = useHotkeys()
const hotkeyGroups = computed(() => getSortedHotkeys())

function parseKeys(keyStr) {
  return keyStr.split('+').map(k => k.trim())
}
</script>

<style scoped>
.hotkey-modal-card {
  background: #1a1a2e !important;
  color: #e0e0e0;
  border: 1px solid rgba(255, 255, 255, 0.08);
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.hotkey-modal-header {
  background: #16213e;
  color: #fff;
  font-size: 1.1rem;
  font-weight: 600;
  padding: 12px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.hotkey-modal-body {
  overflow-y: auto;
  padding: 0;
  flex: 1;
  min-height: 0;
}

.hotkey-section {
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.hotkey-section:last-child {
  border-bottom: none;
}

.hotkey-section-header {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.45);
  padding: 10px 20px 4px;
  display: flex;
  align-items: center;
}

.hotkey-section-active {
  color: #ffc107;
}

.hotkey-entries {
  padding: 0 12px 8px;
}

.hotkey-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 8px;
  border-radius: 4px;
  transition: background 0.15s;
}

.hotkey-row:hover {
  background: rgba(255, 255, 255, 0.04);
}

.hotkey-description {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
}

.hotkey-keys {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
  margin-left: 16px;
}

.hotkey-kbd {
  display: inline-block;
  padding: 2px 8px;
  font-size: 0.75rem;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  color: #e0e0e0;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 4px;
  min-width: 24px;
  text-align: center;
  line-height: 1.6;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}
</style>
