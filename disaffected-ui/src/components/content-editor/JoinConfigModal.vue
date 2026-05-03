<template>
  <v-dialog
    :model-value="visible"
    max-width="550"
    persistent
    @update:model-value="$emit('update:visible', $event)"
  >
    <v-card class="join-config-card">
      <v-card-title class="d-flex align-center pa-4">
        <v-icon class="mr-2" color="deep-purple">mdi-set-merge</v-icon>
        <span>Join Segments</span>
        <v-spacer />
        <v-btn icon size="small" variant="text" @click="$emit('cancel')">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      <v-divider />

      <v-card-text class="pa-4">
        <!-- Slug -->
        <v-text-field
          v-model="newSlug"
          label="New Slug"
          variant="outlined"
          density="compact"
          class="mb-3"
          hide-details
          placeholder="e.g. MERGED-SEGMENT"
          @keydown.enter="handleConfirm"
        />

        <!-- Title -->
        <v-text-field
          v-model="newTitle"
          label="New Title"
          variant="outlined"
          density="compact"
          class="mb-4"
          hide-details
          placeholder="e.g. Combined Discussion"
          @keydown.enter="handleConfirm"
        />

        <!-- Item Type -->
        <v-select
          v-model="newType"
          :items="typeOptions"
          item-title="text"
          item-value="value"
          label="Item Type"
          variant="outlined"
          density="compact"
          class="mb-4"
          hide-details
        />

        <!-- Concatenation Order -->
        <div class="text-subtitle-2 mb-2 d-flex align-center">
          <v-icon size="small" class="mr-1">mdi-sort</v-icon>
          Concatenation Order
          <span class="text-caption text-grey ml-2">(drag to reorder)</span>
        </div>

        <draggable
          v-model="orderedItems"
          tag="div"
          item-key="asset_id"
          :animation="200"
          ghost-class="join-ghost"
          handle=".drag-handle"
          class="join-order-list"
        >
          <template #item="{ element, index }">
            <div class="join-order-item">
              <v-icon class="drag-handle mr-2" size="small">mdi-drag-vertical</v-icon>
              <span class="join-order-number">{{ index + 1 }}</span>
              <span class="join-order-type">{{ (element.type || element.item_type || 'SEG').toUpperCase().substring(0, 3) }}</span>
              <span class="join-order-slug">{{ element.slug || element.title }}</span>
              <span class="join-order-chars text-grey text-caption">
                {{ (element.script_content || '').length }} chars
              </span>
            </div>
          </template>
        </draggable>

        <!-- Content preview -->
        <div class="mt-4 text-caption text-grey">
          Merged content: {{ totalChars }} characters from {{ orderedItems.length }} segments
        </div>
      </v-card-text>

      <v-divider />
      <v-card-actions class="pa-3">
        <v-btn variant="text" @click="$emit('cancel')">Cancel</v-btn>
        <v-spacer />
        <v-btn
          color="deep-purple"
          variant="elevated"
          :disabled="!canConfirm"
          @click="handleConfirm"
        >
          <v-icon class="mr-1" size="small">mdi-set-merge</v-icon>
          Merge &amp; Place
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import draggable from 'vuedraggable' // eslint-disable-line no-unused-vars

const props = defineProps({
  visible: { type: Boolean, default: false },
  selectedItems: { type: Array, default: () => [] }
})

const emit = defineEmits(['confirm', 'cancel', 'update:visible'])

const newSlug = ref('')
const newTitle = ref('')
const newType = ref('segment')
const orderedItems = ref([])

const typeOptions = computed(() => {
  return [
    { text: 'Segment', value: 'segment' },
    { text: 'Open', value: 'open' },
    { text: 'Cold Open', value: 'coldopen' },
    { text: 'Tease', value: 'tease' },
    { text: 'Interview', value: 'interview' },
    { text: 'Package', value: 'package' },
    { text: 'Reader', value: 'reader' },
    { text: 'Close', value: 'close' }
  ]
})

const totalChars = computed(() => {
  return orderedItems.value.reduce((sum, item) => sum + (item.script_content || '').length, 0)
})

const canConfirm = computed(() => {
  return newSlug.value.trim().length > 0 && orderedItems.value.length >= 2
})

watch(() => props.selectedItems, (items) => {
  if (items && items.length > 0) {
    orderedItems.value = items.map(i => ({ ...i }))
    if (!newSlug.value) {
      newSlug.value = items.map(i => i.slug || '').filter(Boolean).join(' + ')
    }
    if (!newTitle.value) {
      newTitle.value = items.map(i => i.title || '').filter(Boolean).join(' + ')
    }
    newType.value = items[0]?.type || items[0]?.item_type || 'segment'
  }
}, { immediate: true })

watch(() => props.visible, (val) => {
  if (!val) {
    newSlug.value = ''
    newTitle.value = ''
    orderedItems.value = []
  }
})

function handleConfirm() {
  if (!canConfirm.value) return
  emit('confirm', {
    slug: newSlug.value.trim(),
    title: newTitle.value.trim(),
    type: newType.value,
    orderedItems: orderedItems.value
  })
}
</script>

<style scoped>
.join-config-card {
  border: 1px solid rgba(103, 58, 183, 0.3);
}

.join-order-list {
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  overflow: hidden;
}

.join-order-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  cursor: default;
  transition: background 0.15s;
}

.join-order-item:last-child {
  border-bottom: none;
}

.join-order-item:hover {
  background: rgba(103, 58, 183, 0.1);
}

.drag-handle {
  cursor: grab;
  opacity: 0.5;
}

.drag-handle:hover {
  opacity: 1;
}

.join-order-number {
  font-size: 11px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.4);
  min-width: 18px;
}

.join-order-type {
  font-size: 11px;
  font-weight: 600;
  color: rgba(103, 58, 183, 0.8);
  min-width: 30px;
  text-transform: uppercase;
}

.join-order-slug {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.join-order-chars {
  font-size: 11px;
  white-space: nowrap;
}

.join-ghost {
  opacity: 0.4;
  background: rgba(103, 58, 183, 0.2) !important;
}
</style>
