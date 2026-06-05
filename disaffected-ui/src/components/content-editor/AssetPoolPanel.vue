<template>
  <div class="asset-pool-panel">
    <div class="asset-pool-header">
      <router-link
        v-if="episodeNumber"
        :to="{ name: 'whiteboard', query: { episode: episodeNumber } }"
        class="jump-to-wb-link ml-auto"
      >[jump to whiteboard]</router-link>
    </div>

    <!-- Category Tabs -->
    <v-tabs
      v-model="activeTab"
      density="compact"
      show-arrows
      height="32"
      class="asset-pool-tabs"
    >
      <v-tab
        v-for="cat in categories"
        :key="cat.value"
        :value="cat.value"
        size="small"
        class="asset-pool-tab"
      >
        {{ cat.label }}
      </v-tab>
    </v-tabs>

    <!-- Search -->
    <div class="asset-pool-search-row">
      <v-icon size="small" color="grey">mdi-magnify</v-icon>
      <input
        v-model="searchQuery"
        placeholder="Search..."
        class="asset-pool-search-input"
      />
      <v-icon v-if="searchQuery" size="x-small" color="grey" class="search-clear" @click="searchQuery = ''">mdi-close</v-icon>
    </div>

    <!-- Items List -->
    <div class="asset-pool-items">
      <div v-if="loading" class="text-center py-4">
        <v-progress-circular indeterminate size="24" width="2" color="primary" />
      </div>

      <!-- Whiteboard Tree View -->
      <template v-else-if="activeTab === 'whiteboard'">
        <div v-if="whiteboardTree.length === 0" class="text-center py-4">
          <p class="text-caption text-grey">No whiteboard items found</p>
        </div>
        <div v-else class="wb-tree">
          <template v-for="(node, nodeIdx) in filteredTree" :key="node.id">
            <!-- Parent node -->
            <div
              v-if="node.isParent"
              class="wb-parent-node"
              :class="{ 'drop-into': dropTarget && dropTarget.parentId === node.id && dropTarget.type === 'into' }"
              draggable="true"
              @dragstart="onDragStart($event, 'top', nodeIdx, null, node)"
              @dragover.prevent="onParentDragOver($event, node)"
              @dragleave="onDragLeave"
              @drop="onDropIntoParent($event, node)"
              @dragend="onDragEnd"
              @click="toggleParentExpand(node.id)"
            >
              <v-icon size="x-small" class="drag-handle mr-1">mdi-drag-vertical</v-icon>
              <v-icon size="x-small" class="mr-1">
                {{ expandedParents[node.id] ? 'mdi-chevron-down' : 'mdi-chevron-right' }}
              </v-icon>
              <span class="wb-type-badge wb-parent-badge" :style="{ background: parentBadgeBg(node), color: parentBadgeColor(node) }">
                <v-icon size="x-small" class="wb-badge-icon">{{ parentBadgeIcon(node) }}</v-icon>
                {{ parentBadgeLabel(node) }}
              </span>
              <span class="wb-parent-title">{{ node.title || 'Untitled Group' }}</span>
              <v-chip size="x-small" variant="tonal" color="grey" class="ml-auto wb-count-chip">
                {{ node.children.length }}
              </v-chip>
            </div>
            <!-- Children of parent -->
            <template v-if="node.isParent && expandedParents[node.id]">
              <div
                v-for="(child, childIdx) in node.children"
                :key="child.id"
                class="wb-child-node"
                :class="{ 'drop-into': dropTarget && dropTarget.parentId === node.id && dropTarget.type === 'into' }"
                draggable="true"
                @dragstart="onDragStart($event, 'child', childIdx, node.id, child)"
                @dragover.prevent="onChildDragOver($event, node)"
                @dragleave="onDragLeave"
                @drop="onDropIntoParent($event, node)"
                @dragend="onDragEnd"
              >
                <v-icon size="x-small" class="drag-handle mr-1">mdi-drag-vertical</v-icon>
                <span class="wb-type-badge" :style="{ background: resolveBadgeBg(child), color: resolveBadgeFg(child) }">
                  <v-icon size="x-small" class="wb-badge-icon">{{ resolveBadgeIcon(child) }}</v-icon>
                  {{ resolveBadgeLabel(child) }}
                </span>
                <span class="wb-child-title" :title="child.title">{{ child.title }}</span>
              </div>
            </template>
            <!-- Top-level non-parent (orphan) -->
            <div
              v-if="!node.isParent"
              class="wb-orphan-node"
              :class="{ 'drag-over-reorder': dropTarget && dropTarget.orphanIdx === nodeIdx && dropTarget.type === 'reorder' }"
              draggable="true"
              @dragstart="onDragStart($event, 'top', nodeIdx, null, node)"
              @dragover.prevent="onOrphanDragOver($event, nodeIdx)"
              @dragleave="onDragLeave"
              @drop="onDropReorder($event, nodeIdx)"
              @dragend="onDragEnd"
            >
              <v-icon size="x-small" class="drag-handle mr-1">mdi-drag-vertical</v-icon>
              <span class="wb-type-badge" :style="{ background: resolveBadgeBg(node), color: resolveBadgeFg(node) }">
                <v-icon size="x-small" class="wb-badge-icon">{{ resolveBadgeIcon(node) }}</v-icon>
                {{ resolveBadgeLabel(node) }}
              </span>
              <span class="wb-child-title" :title="node.title">{{ node.title }}</span>
            </div>
          </template>
        </div>
      </template>

      <!-- Scripts list -->
      <template v-else-if="activeTab === 'scripts'">
        <div v-if="scriptsData.length === 0" class="text-center py-4">
          <p class="text-caption text-grey">No generated scripts</p>
          <p class="text-caption text-grey">Use Workflow Tools to generate scripts</p>
        </div>
        <div v-else class="scripts-list">
          <div v-for="g in groupedScripts" :key="g.type" class="script-entry">
            <div class="script-row d-flex align-start">
              <v-icon size="small" :color="getScriptIconColor(g.selected)" class="mr-2 script-icon">{{ getScriptIcon(g.selected) }}</v-icon>
              <div class="flex-grow-1 d-flex align-center flex-wrap ga-2" style="min-width: 0;">
                <span class="script-name text-body-2 font-weight-medium text-truncate">{{ g.label }}</span>
                <!-- The revision chip is clickable when older revisions exist:
                     it expands this row to list the selected format's revisions. -->
                <v-chip
                  size="x-small"
                  color="primary"
                  :variant="g.doc.pastRevisions && g.doc.pastRevisions.length > 0 ? 'flat' : 'tonal'"
                  style="height: 14px; font-size: 0.6rem;"
                  :class="{ 'revision-chip-clickable': g.doc.pastRevisions && g.doc.pastRevisions.length > 0 }"
                  @click="g.doc.pastRevisions && g.doc.pastRevisions.length > 0 && toggleOlderRevisions(g.type + '_' + g.selected)"
                >
                  R{{ g.doc.revision || '?' }}
                  <v-icon
                    v-if="g.doc.pastRevisions && g.doc.pastRevisions.length > 0"
                    end
                    size="x-small"
                    :class="{ 'rotate-180': scriptRevisionsOpen[g.type + '_' + g.selected] }"
                  >mdi-chevron-down</v-icon>
                  <v-tooltip v-if="g.doc.pastRevisions && g.doc.pastRevisions.length > 0" activator="parent" location="top">
                    {{ g.doc.pastRevisions.length }} older revision{{ g.doc.pastRevisions.length === 1 ? '' : 's' }}
                  </v-tooltip>
                </v-chip>
                <!-- Format selector: one row per script type, format chosen here. -->
                <div class="format-toggle d-flex align-center">
                  <button
                    v-for="fmt in g.available"
                    :key="fmt"
                    class="format-chip"
                    :class="{ 'format-chip-active': fmt === g.selected }"
                    @click="selectScriptFormat(g.type, fmt)"
                  >{{ fmt.toUpperCase() }}</button>
                </div>
                <span v-if="g.doc.size_formatted" class="text-caption text-grey">{{ g.doc.size_formatted }}</span>
              </div>
              <v-btn icon size="x-small" variant="text" color="primary" @click="openScript(g.doc)">
                <v-icon size="small">mdi-open-in-new</v-icon>
                <v-tooltip activator="parent" location="top">Preview {{ g.selected.toUpperCase() }}</v-tooltip>
              </v-btn>
              <v-btn icon size="x-small" variant="text" color="grey" @click="downloadScript(g.doc)">
                <v-icon size="small">mdi-download</v-icon>
                <v-tooltip activator="parent" location="top">Download {{ g.selected.toUpperCase() }}</v-tooltip>
              </v-btn>
            </div>
            <!-- Older revisions of the selected format — expanded by the chip -->
            <v-expand-transition v-if="g.doc.pastRevisions && g.doc.pastRevisions.length > 0">
              <div v-if="scriptRevisionsOpen[g.type + '_' + g.selected]" class="older-revisions ml-4">
                <div v-for="rev in g.doc.pastRevisions" :key="rev.filename" class="revision-row d-flex align-center py-1">
                  <v-chip size="x-small" variant="tonal" color="grey" style="height: 14px; font-size: 0.55rem;" class="mr-2">R{{ rev.revision || '?' }}</v-chip>
                  <span class="text-caption text-grey flex-grow-1">{{ rev.modified_formatted }}</span>
                  <v-btn icon size="x-small" variant="text" color="grey" @click="openScript(rev)">
                    <v-icon size="x-small">mdi-open-in-new</v-icon>
                  </v-btn>
                  <v-btn icon size="x-small" variant="text" color="grey" @click="downloadScript(rev)">
                    <v-icon size="x-small">mdi-download</v-icon>
                  </v-btn>
                </div>
              </div>
            </v-expand-transition>
          </div>
        </div>
      </template>

      <!-- Media: files preserved in the pool for this episode (released-from-cue
           media). Double-click an item to re-insert it as a cue (a cue-type
           picker appears, filtered to the file's kind). Small preview/download
           icons sit on the right of each row. -->
      <template v-else-if="activeTab === 'media'">
        <!-- Tiny upload button: media can also be added directly to the pool,
             not just via cue deletion. -->
        <div class="d-flex align-center justify-end mb-1">
          <input
            ref="poolUploadInputRef"
            type="file"
            multiple
            style="display: none;"
            @change="onPoolUploadSelected"
          />
          <v-btn size="x-small" variant="tonal" color="primary" @click="triggerPoolUpload" :loading="poolUploading">
            <v-icon size="small" start>mdi-upload</v-icon>
            Upload
          </v-btn>
        </div>
        <div v-if="filteredPoolMedia.length === 0" class="text-center py-4">
          <p class="text-caption text-grey">No pooled media for this episode</p>
        </div>
        <v-list v-else density="compact" class="asset-pool-list pa-0">
          <v-list-item
            v-for="m in filteredPoolMedia"
            :key="m.asset_id"
            class="asset-pool-item pool-media-item"
            @dblclick="reinsertPoolMedia(m)"
          >
            <template #prepend>
              <v-btn
                icon
                size="x-small"
                variant="tonal"
                color="success"
                @click.stop="reinsertPoolMedia(m)"
                class="place-btn mr-2"
              >
                <v-icon size="small">mdi-plus</v-icon>
                <v-tooltip activator="parent" location="left">{{ addToLabel }}</v-tooltip>
              </v-btn>
            </template>
            <div class="flex-grow-1" style="min-width: 0;">
              <div class="text-caption font-weight-medium text-truncate d-flex align-center ga-1 pool-media-name">
                <v-icon size="x-small" :color="poolKindColor(m.kind)">{{ poolKindIcon(m.kind) }}</v-icon>
                <span class="text-truncate">{{ m.original_filename || m.filename }}</span>
              </div>
              <div class="text-caption text-grey d-flex align-center ga-2">
                <span>{{ (m.kind || 'file').toUpperCase() }}</span>
                <span v-if="m.file_size">{{ formatBytes(m.file_size) }}</span>
                <span v-if="m.origin_cue_type" class="text-truncate">· from {{ m.origin_cue_type }}</span>
              </div>
            </div>
            <template #append>
              <v-btn icon size="x-small" variant="text" color="primary" @click.stop="previewPoolMedia(m)">
                <v-icon size="small">mdi-eye</v-icon>
                <v-tooltip activator="parent" location="top">Preview</v-tooltip>
              </v-btn>
              <v-btn icon size="x-small" variant="text" color="grey" @click.stop="downloadPoolMedia(m)">
                <v-icon size="small">mdi-download</v-icon>
                <v-tooltip activator="parent" location="top">Download</v-tooltip>
              </v-btn>
            </template>
          </v-list-item>
        </v-list>
      </template>

      <!-- Flat list for scheduled/other -->
      <template v-else>
        <div v-if="filteredItems.length === 0" class="text-center py-4">
          <p class="text-caption text-grey">No {{ activeCategoryLabel }} found</p>
          <v-btn
            size="x-small"
            variant="text"
            color="primary"
            @click="$emit('create-new-item', { itemType: activeTab })"
          >
            <v-icon left size="small">mdi-plus</v-icon>
            Create New
          </v-btn>
        </div>

        <v-list v-else density="compact" class="asset-pool-list pa-0">
          <v-list-item
            v-for="item in filteredItems"
            :key="item.asset_id || item.id"
            class="asset-pool-item"
          >
            <template v-slot:prepend>
              <v-btn
                icon
                size="x-small"
                variant="tonal"
                color="success"
                @click.stop="placeItem(item)"
                class="place-btn mr-2"
              >
                <v-icon size="small">mdi-plus</v-icon>
                <v-tooltip activator="parent" location="left">Add to rundown</v-tooltip>
              </v-btn>
            </template>

            <v-list-item-title class="text-body-2 asset-item-title">
              {{ item.title || item.slug || 'Untitled' }}
            </v-list-item-title>
            <v-list-item-subtitle class="text-caption asset-item-sub">
              <v-chip v-if="item._subtype" size="x-small" :color="item._subtype === 'ad' ? 'orange' : 'purple'" variant="tonal" class="mr-1" style="height: 14px; font-size: 0.55rem;">{{ item._subtype }}</v-chip>
              <span v-if="item.customer">{{ item.customer }} &bull; </span>
              <span v-if="item.duration">{{ item.duration }}</span>
            </v-list-item-subtitle>

            <template v-slot:append>
              <v-chip
                v-if="isPlaced(item)"
                size="x-small"
                color="info"
                variant="tonal"
                class="placed-chip"
              >
                Placed
              </v-chip>
            </template>
          </v-list-item>
        </v-list>
      </template>
    </div>

    <!-- Pooled-media preview modal (image/video shown inline, not a new tab) -->
    <v-dialog v-model="poolPreview.show" max-width="900" @keydown.esc="closePoolPreview">
      <v-card v-if="poolPreview.item">
        <v-toolbar density="compact" color="grey-darken-3">
          <v-toolbar-title class="text-body-2 text-truncate">
            {{ poolPreview.item.original_filename || poolPreview.item.filename }}
          </v-toolbar-title>
          <v-spacer />
          <v-btn icon size="small" @click="downloadPoolMedia(poolPreview.item)">
            <v-icon size="small">mdi-download</v-icon>
            <v-tooltip activator="parent" location="bottom">Download</v-tooltip>
          </v-btn>
          <v-btn icon size="small" @click="closePoolPreview">
            <v-icon size="small">mdi-close</v-icon>
          </v-btn>
        </v-toolbar>
        <div class="pool-preview-body">
          <video
            v-if="poolPreview.item.kind === 'video'"
            :src="poolPreview.item.url"
            controls
            autoplay
            class="pool-preview-media"
          />
          <img
            v-else-if="poolPreview.item.kind === 'image'"
            :src="poolPreview.item.url"
            class="pool-preview-media"
            :alt="poolPreview.item.filename"
          />
          <audio
            v-else-if="poolPreview.item.kind === 'audio'"
            :src="poolPreview.item.url"
            controls
            autoplay
            class="pa-6"
            style="width: 100%;"
          />
          <div v-else class="text-center pa-8 text-grey">
            <v-icon size="48" class="mb-2">{{ poolKindIcon(poolPreview.item.kind) }}</v-icon>
            <div class="text-body-2">No inline preview for this file type.</div>
            <v-btn class="mt-3" size="small" variant="tonal" color="primary" @click="downloadPoolMedia(poolPreview.item)">
              <v-icon start size="small">mdi-download</v-icon> Download
            </v-btn>
          </div>
        </div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { fetchJson } from '@/utils/apiHelpers'

const props = defineProps({
  episodeNumber: {
    type: String,
    default: null
  },
  rundownItems: {
    type: Array,
    default: () => []
  },
  panelWidth: {
    type: String,
    default: 'wide'
  },
  // Friendly label of the currently-selected rundown item's type (e.g.
  // "Segment", "Advertisement"). Drives the "Add to {type}" tooltip.
  selectedItemLabel: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['place-item', 'create-new-item', 'reinsert-pool-media'])

// "Add to {selected rundown item type}" — falls back to a generic label when
// no item is selected.
const addToLabel = computed(() =>
  props.selectedItemLabel ? `Add to ${props.selectedItemLabel}` : 'Add to rundown item'
)

// ── Reactive state ──
const activeTab = ref('media')
const searchQuery = ref('')
const loading = ref(false)
const categories = ref([
  { label: 'Media', value: 'media' },
  { label: 'Whiteboard', value: 'whiteboard' },
  { label: 'Scheduled', value: 'scheduled' },
  { label: 'Scripts', value: 'scripts' }
])
// Pooled media for this episode (released-from-cue media + loose uploads).
const poolMedia = ref([])
const poolUploadInputRef = ref(null)
const poolUploading = ref(false)
// Preview modal state for pooled media (image/video shown inline, not a new tab).
const poolPreview = reactive({ show: false, item: null })
const scriptsData = ref([]) // [{type, label, format, latest: doc, pastRevisions: [doc,...]}]
const scriptRevisionsOpen = reactive({}) // { 'host_full_pdf': true } toggles
// Per script-type: which format the user has selected to view (e.g. host_full → 'pdf').
const selectedScriptFormat = reactive({})

// Preferred format order when picking the default for a type.
const FORMAT_PRIORITY = ['pdf', 'html', 'md']

// Collapse the per-(type,format) documents into one row per type, with the
// available formats selectable. Each format keeps its own url/revision/size/
// pastRevisions; the row shows whichever format is currently selected.
const groupedScripts = computed(() => {
  const byType = new Map()
  for (const doc of scriptsData.value) {
    if (!byType.has(doc.type)) {
      byType.set(doc.type, { type: doc.type, label: doc.label, formats: {} })
    }
    byType.get(doc.type).formats[doc.format] = doc
  }
  return Array.from(byType.values()).map(g => {
    const available = Object.keys(g.formats)
      .sort((a, b) => {
        const ia = FORMAT_PRIORITY.indexOf(a); const ib = FORMAT_PRIORITY.indexOf(b)
        return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib)
      })
    const selected = selectedScriptFormat[g.type] && g.formats[selectedScriptFormat[g.type]]
      ? selectedScriptFormat[g.type]
      : available[0]
    return { ...g, available, selected, doc: g.formats[selected] }
  })
})

function selectScriptFormat(type, format) {
  selectedScriptFormat[type] = format
}
const itemsCache = reactive({})
const currentItems = ref([])
const whiteboardTree = ref([])
const expandedParents = reactive({})
// Drag state
const dragSource = ref(null)
const dropTarget = ref(null)
let dragLeaveTimer = null

// ── Computed ──
const activeCategoryLabel = computed(() => {
  const cat = categories.value.find(c => c.value === activeTab.value)
  return cat ? cat.label : ''
})

const filteredItems = computed(() => {
  if (!searchQuery.value) return currentItems.value
  const q = searchQuery.value.toLowerCase()
  return currentItems.value.filter(item =>
    (item.title || '').toLowerCase().includes(q) ||
    (item.slug || '').toLowerCase().includes(q) ||
    (item.customer || '').toLowerCase().includes(q) ||
    (item.url || '').toLowerCase().includes(q)
  )
})

const filteredTree = computed(() => {
  if (!searchQuery.value) return whiteboardTree.value
  const q = searchQuery.value.toLowerCase()
  return whiteboardTree.value.map(node => {
    if (node.isParent) {
      const filteredChildren = node.children.filter(c =>
        (c.title || '').toLowerCase().includes(q) ||
        (c.url || '').toLowerCase().includes(q)
      )
      const parentMatches = (node.title || '').toLowerCase().includes(q)
      if (parentMatches || filteredChildren.length > 0) {
        return { ...node, children: parentMatches ? node.children : filteredChildren }
      }
      return null
    }
    if ((node.title || '').toLowerCase().includes(q) || (node.url || '').toLowerCase().includes(q)) {
      return node
    }
    return null
  }).filter(Boolean)
})

const filteredPoolMedia = computed(() => {
  if (!searchQuery.value) return poolMedia.value
  const q = searchQuery.value.toLowerCase()
  return poolMedia.value.filter(m =>
    (m.original_filename || m.filename || '').toLowerCase().includes(q) ||
    (m.origin_slug || '').toLowerCase().includes(q) ||
    (m.kind || '').toLowerCase().includes(q)
  )
})

const placedAssetIds = computed(() => {
  const ids = new Set()
  for (const ri of props.rundownItems) {
    if (ri.library_asset_id) ids.add(ri.library_asset_id)
    if (ri.asset_id) ids.add(ri.asset_id)
  }
  return ids
})

// ── Watch ──
watch(activeTab, (newVal) => {
  loadCategory(newVal)
}, { immediate: true })

// ── Methods ──
async function loadCategory(category) {
  if (itemsCache[category]) {
    if (category === 'whiteboard') {
      whiteboardTree.value = itemsCache[category]
    } else if (category === 'media') {
      poolMedia.value = itemsCache[category]
    } else {
      currentItems.value = itemsCache[category]
    }
    return
  }

  loading.value = true
  currentItems.value = []

  try {
    if (category === 'whiteboard') {
      await loadWhiteboardItems()
      return
    }

    if (category === 'scripts') {
      await loadScripts()
      return
    }

    if (category === 'scheduled') {
      const [adsData, promosData] = await Promise.all([
        fetchJson('/api/content-library/?item_type=ad&is_active=true&limit=100'),
        fetchJson('/api/content-library/?item_type=promo&is_active=true&limit=100')
      ])
      const ads = (adsData?.items || adsData || []).map(i => ({ ...i, _subtype: 'ad' }))
      const promos = (promosData?.items || promosData || []).map(i => ({ ...i, _subtype: 'promo' }))
      const items = [...ads, ...promos]
      itemsCache[category] = items
      currentItems.value = items
      return
    }

    if (category === 'media') {
      await loadPoolMedia()
      return
    }

    const data = await fetchJson(`/api/content-library/?item_type=${category}&is_active=true&limit=100`)
    const items = data?.items || data || []
    itemsCache[category] = items
    currentItems.value = items
  } catch (error) {
    console.error(`Error loading ${category} items:`, error)
    currentItems.value = []
  } finally {
    loading.value = false
  }
}

async function loadPoolMedia() {
  if (!props.episodeNumber) {
    poolMedia.value = []
    loading.value = false
    return
  }
  try {
    const data = await fetchJson(`/api/episodes/${props.episodeNumber}/cue-assets/pool`)
    const items = data?.items || []
    itemsCache['media'] = items
    poolMedia.value = items
  } catch (error) {
    console.error('Error loading pool media:', error)
    poolMedia.value = []
  } finally {
    loading.value = false
  }
}

// ── Pool media helpers ──
function poolKindIcon(kind) {
  return { video: 'mdi-filmstrip', image: 'mdi-image', audio: 'mdi-music-note' }[kind] || 'mdi-file'
}
function poolKindColor(kind) {
  return { video: 'blue', image: 'green', audio: 'purple' }[kind] || 'grey'
}
function formatBytes(n) {
  if (!n) return ''
  if (n >= 1048576) return (n / 1048576).toFixed(1) + ' MB'
  if (n >= 1024) return (n / 1024).toFixed(0) + ' KB'
  return n + ' B'
}
function previewPoolMedia(m) {
  // Show the file inline in a modal (served via the /pool static mount).
  poolPreview.item = m
  poolPreview.show = true
}
function closePoolPreview() {
  poolPreview.show = false
  poolPreview.item = null
}
function downloadPoolMedia(m) {
  const a = document.createElement('a')
  a.href = m.url
  a.download = m.original_filename || m.filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}
function reinsertPoolMedia(m) {
  // Hand the pooled file up to ContentEditor, which shows a cue-type picker
  // (filtered to this file's kind) and then opens the matching cue modal
  // pre-loaded with the file URL.
  emit('reinsert-pool-media', m)
}
function triggerPoolUpload() {
  poolUploadInputRef.value?.click()
}
async function onPoolUploadSelected(e) {
  const files = Array.from(e.target.files || [])
  if (!files.length || !props.episodeNumber) return
  poolUploading.value = true
  try {
    const token = localStorage.getItem('auth-token')
    for (const f of files) {
      const fd = new FormData()
      fd.append('file', f)
      await fetch(`/api/episodes/${props.episodeNumber}/cue-assets/pool/upload`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: fd
      })
    }
    delete itemsCache['media']   // force refresh
    await loadPoolMedia()
  } catch (err) {
    console.error('Pool upload failed:', err)
  } finally {
    poolUploading.value = false
    if (poolUploadInputRef.value) poolUploadInputRef.value.value = ''  // reset picker
  }
}

async function loadWhiteboardItems() {
  if (!props.episodeNumber) {
    whiteboardTree.value = []
    loading.value = false
    return
  }

  try {
    const data = await fetchJson(`/api/whiteboard/${props.episodeNumber}`)

    const wbItems = data?.items || []
    const nodeLinks = data?.node_links || []

    const itemMap = {}
    for (const item of wbItems) {
      itemMap[item.id] = item
    }

    const parentChildren = {}
    const childOfParent = new Set()

    for (const link of nodeLinks) {
      const srcIdx = link.source_index != null ? link.source_index : null
      const tgtIdx = link.target_index != null ? link.target_index : null
      const src = srcIdx != null ? wbItems[srcIdx] : itemMap[link.source_item_id]
      const tgt = tgtIdx != null ? wbItems[tgtIdx] : itemMap[link.target_item_id]
      if (!src || !tgt) continue

      if (src.item_type === 'parent') {
        if (!parentChildren[src.id]) parentChildren[src.id] = new Set()
        parentChildren[src.id].add(tgt.id)
        childOfParent.add(tgt.id)
      }
      if (tgt.item_type === 'parent') {
        if (!parentChildren[tgt.id]) parentChildren[tgt.id] = new Set()
        parentChildren[tgt.id].add(src.id)
        childOfParent.add(src.id)
      }
    }

    const tree = []

    for (const item of wbItems) {
      if (item.item_type === 'parent') {
        const childIds = parentChildren[item.id] || new Set()
        const children = [...childIds].map(cid => transformItem(itemMap[cid])).filter(Boolean)
        tree.push({
          id: item.id,
          isParent: true,
          title: item.title || 'Untitled Group',
          description: item.text_content,
          social_metadata: item.social_metadata,
          children: children
        })
        expandedParents[item.id] = true
      }
    }

    for (const item of wbItems) {
      if (item.item_type !== 'parent' && !childOfParent.has(item.id)) {
        tree.push(transformItem(item))
      }
    }

    whiteboardTree.value = tree
    itemsCache['whiteboard'] = tree
  } catch (error) {
    console.error('Error loading whiteboard items:', error)
    whiteboardTree.value = []
  } finally {
    loading.value = false
  }
}

async function loadScripts() {
  if (!props.episodeNumber) {
    scriptsData.value = []
    loading.value = false
    return
  }
  try {
    const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
    const response = await fetch(`/api/scripts/episode/${props.episodeNumber}/generated`, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data = await response.json()
    scriptsData.value = (data.documents || []).map(doc => ({
      ...doc,
      label: formatScriptName(doc.type),
      icon: getScriptIcon(doc.format)
    }))
  } catch (error) {
    console.error('Error loading scripts:', error)
    scriptsData.value = []
  } finally {
    loading.value = false
  }
}

function refreshScripts() {
  delete itemsCache['scripts']
  loadCategory('scripts')
}

function formatScriptName(type) {
  const map = {
    host_full: 'Host Script',
    host_clean: 'Host Clean',
    production: 'Director Script',
    host_script: 'Host Script (Legacy)',
    media_list: 'Media List',
    show_caller: 'Show Caller',
    prompter: 'Prompter'
  }
  return map[type] || type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

function getScriptIcon(format) {
  if (format === 'pdf') return 'mdi-file-pdf-box'
  if (format === 'html') return 'mdi-language-html5'
  if (format === 'txt') return 'mdi-file-document-outline'
  return 'mdi-file-outline'
}

function getScriptIconColor(format) {
  if (format === 'pdf') return 'red'
  if (format === 'html') return 'orange'
  return 'grey'
}

function toggleOlderRevisions(key) {
  scriptRevisionsOpen[key] = !scriptRevisionsOpen[key]
}

function openScript(doc) {
  // doc.url is a root-relative path like "/episodes/0225/scripts/current/FILE.pdf"
  // served by the FastAPI StaticFiles mount at /episodes (see app/main.py). The
  // Vue dev server proxies /episodes -> backend, so use the URL as-is.
  // Do NOT prepend /api — the static mount lives outside the /api prefix.
  const url = doc.url
  if (url) window.open(url, '_blank')
}

function downloadScript(doc) {
  const url = doc.url
  if (!url) return
  const a = document.createElement('a')
  a.href = url
  a.download = doc.filename
  a.click()
}

// Expose refresh for parent to call after generation
// (expose merged into the defineExpose at end of script)

function transformItem(item) {
  if (!item) return null
  const sm = item.social_metadata || {}
  let title = item.title || sm.author_name || sm.title || ''

  if (item.item_type === 'link') {
    const handle = sm.author_handle ? `@${sm.author_handle}` : ''
    const text = sm.tweet_text || sm.post_text || ''
    title = title || text.substring(0, 60) || item.url || 'Link'
    if (handle && !title.includes(handle)) title = `${handle}: ${title}`
  } else if (item.item_type === 'text') {
    title = title || (item.text_content || '').substring(0, 60) || 'Text note'
  } else if (item.item_type === 'image') {
    title = title || item.caption || 'Image'
  } else if (item.item_type === 'video') {
    title = title || 'Video'
  } else if (item.item_type === 'audio') {
    title = title || 'Audio'
  } else if (item.item_type === 'code') {
    title = title || 'Code snippet'
  } else if (item.item_type === 'markdown') {
    title = title || 'Markdown'
  } else if (item.item_type === 'html') {
    title = title || 'HTML embed'
  } else {
    title = title || item.item_type || 'Item'
  }

  return {
    id: item.id,
    isParent: false,
    title: title,
    item_type: item.item_type,
    url: item.url,
    media_url: item.media_url,
    asset_id: item.media_asset_id,
    social_metadata: sm
  }
}

function toggleParentExpand(parentId) {
  expandedParents[parentId] = !expandedParents[parentId]
}

// ── Drag and drop ──

function onDragStart(event, level, index, parentId, node) {
  dragSource.value = { level, index, parentId, node }
  event.dataTransfer.effectAllowed = 'move'
  event.target.classList.add('dragging')
}

function onParentDragOver(event, parentNode) {
  if (!dragSource.value) return
  if (dragSource.value.node?.id === parentNode.id) return
  clearTimeout(dragLeaveTimer)
  event.dataTransfer.dropEffect = 'move'
  dropTarget.value = { type: 'into', parentId: parentNode.id }
}

function onChildDragOver(event, parentNode) {
  if (!dragSource.value) return
  clearTimeout(dragLeaveTimer)
  event.dataTransfer.dropEffect = 'move'
  dropTarget.value = { type: 'into', parentId: parentNode.id }
}

function onOrphanDragOver(event, nodeIdx) {
  if (!dragSource.value) return
  clearTimeout(dragLeaveTimer)
  event.dataTransfer.dropEffect = 'move'
  dropTarget.value = { type: 'reorder', orphanIdx: nodeIdx }
}

function onDragLeave() {
  clearTimeout(dragLeaveTimer)
  dragLeaveTimer = setTimeout(() => {
    dropTarget.value = null
  }, 50)
}

function onDragEnd(event) {
  event.target.classList.remove('dragging')
  dragSource.value = null
  dropTarget.value = null
}

async function onDropIntoParent(event, parentNode) {
  event.preventDefault()
  const src = dragSource.value
  dropTarget.value = null
  if (!src || !src.node) return
  // Don't drop parent onto itself or a child already in this parent
  if (src.node.id === parentNode.id) return
  if (src.level === 'child' && src.parentId === parentNode.id) return

  const draggedItem = src.node
  const tree = whiteboardTree.value

  // Remove from source
  if (src.level === 'top') {
    const idx = tree.findIndex(n => n.id === draggedItem.id)
    if (idx >= 0) tree.splice(idx, 1)
  } else if (src.level === 'child') {
    const srcParent = tree.find(n => n.id === src.parentId)
    if (srcParent) {
      const idx = srcParent.children.findIndex(c => c.id === draggedItem.id)
      if (idx >= 0) srcParent.children.splice(idx, 1)
    }
  }

  // Add to target parent
  parentNode.children.push(draggedItem)
  expandedParents[parentNode.id] = true

  // Create node_link in backend
  await createNodeLink(draggedItem.id, parentNode.id)

  dragSource.value = null
  itemsCache['whiteboard'] = [...tree]
}

async function onDropReorder(event, targetIdx) {
  event.preventDefault()
  const src = dragSource.value
  dropTarget.value = null
  if (!src) return

  const tree = whiteboardTree.value

  if (src.level === 'top' && src.index !== targetIdx) {
    const item = tree.splice(src.index, 1)[0]
    tree.splice(targetIdx > src.index ? targetIdx : targetIdx, 0, item)
  }

  dragSource.value = null
  itemsCache['whiteboard'] = [...tree]
}

async function createNodeLink(sourceItemId, targetItemId) {
  if (!props.episodeNumber) return
  try {
    await fetchJson(`/api/whiteboard/${props.episodeNumber}/link-nodes`, {
      method: 'POST',
      body: JSON.stringify({
        source_item_id: sourceItemId,
        target_item_id: targetItemId
      })
    })
    console.log(`Created node link: ${sourceItemId} -> ${targetItemId}`)
  } catch (error) {
    console.error('Failed to create node link:', error)
  }
}

// ── Badge resolvers ──

function parentNodeColor(node) { // eslint-disable-line no-unused-vars
  const sm = node.social_metadata || {}
  return sm.parentNodeColor || '#6A1B9A'
}

function parentBadgeLabel(node) {
  const sm = node.social_metadata || {}
  return sm.parentNodeType || 'Group'
}

function parentBadgeIcon(node) {
  const sm = node.social_metadata || {}
  return sm.parentNodeIcon || 'mdi-folder-outline'
}

function parentBadgeColor(node) {
  const sm = node.social_metadata || {}
  return sm.parentNodeColor || '#6A1B9A'
}

function parentBadgeBg(node) {
  const color = parentBadgeColor(node)
  const r = parseInt(color.slice(1, 3), 16)
  const g = parseInt(color.slice(3, 5), 16)
  const b = parseInt(color.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, 0.12)`
}

function whiteboardTypeColor(type) { // eslint-disable-line no-unused-vars
  const colors = { link: 'blue', text: 'grey', image: 'green', video: 'red', audio: 'orange', markdown: 'teal', code: 'indigo', html: 'deep-purple' }
  return colors[type] || 'grey'
}

function whiteboardTypeBg(type) {
  const bgs = {
    link: '#E3F2FD', text: '#F5F5F5', image: '#E8F5E9', video: '#FFEBEE',
    audio: '#FFF3E0', markdown: '#E0F2F1', code: '#E8EAF6', html: '#F3E5F5'
  }
  return bgs[type] || '#F5F5F5'
}

function whiteboardTypeFg(type) {
  const fgs = {
    link: '#1565C0', text: '#616161', image: '#2E7D32', video: '#C62828',
    audio: '#E65100', markdown: '#00695C', code: '#283593', html: '#6A1B9A'
  }
  return fgs[type] || '#616161'
}

function whiteboardTypeIcon(type) {
  const icons = {
    link: 'mdi-link', text: 'mdi-text', image: 'mdi-image', video: 'mdi-video',
    audio: 'mdi-music-note', markdown: 'mdi-language-markdown',
    code: 'mdi-code-braces', html: 'mdi-language-html5'
  }
  return icons[type] || 'mdi-card-outline'
}

function resolveBadgeLabel(item) {
  if (item.item_type !== 'link') return item.item_type

  const url = (item.url || '').toLowerCase()
  const sm = item.social_metadata || {}
  const platform = sm.platform || ''

  if (platform === 'x' || platform === 'twitter' || /\b(x\.com|twitter\.com)\b/.test(url)) {
    if (/\/status\/\d+/.test(url)) {
      if (sm.conversation_id && sm.tweet_id && sm.conversation_id !== sm.tweet_id) return 'X-Reply'
      return 'X-Post'
    }
    if (/\/lists\//.test(url)) return 'X-List'
    if (/\/spaces\//.test(url)) return 'X-Space'
    if (/\/(x|twitter)\.com\/[^/]+\/?$/.test(url) || /\/(x|twitter)\.com\/@[^/]+\/?$/.test(url)) return 'X-Profile'
    return 'X-Link'
  }
  if (/tiktok\.com/.test(url)) {
    if (/\/video\/\d+/.test(url)) return 'TikTok'
    if (/\/@[^/]+\/?$/.test(url)) return 'TikTok-Profile'
    return 'TikTok'
  }
  if (/youtube\.com|youtu\.be/.test(url)) {
    if (/\/watch\?|youtu\.be\//.test(url)) return 'YouTube'
    if (/\/shorts\//.test(url)) return 'YT-Short'
    if (/\/@|\/channel\/|\/c\//.test(url)) return 'YT-Channel'
    if (/\/playlist/.test(url)) return 'YT-Playlist'
    return 'YouTube'
  }
  if (/instagram\.com/.test(url)) {
    if (/\/p\//.test(url)) return 'IG-Post'
    if (/\/reel\//.test(url)) return 'IG-Reel'
    if (/\/stories\//.test(url)) return 'IG-Story'
    return 'Instagram'
  }
  if (/rumble\.com/.test(url)) return 'Rumble'
  if (/soundcloud\.com/.test(url)) return 'SoundCloud'
  if (/reddit\.com/.test(url)) {
    if (/\/comments\//.test(url)) return 'Reddit-Post'
    if (/\/r\/[^/]+\/?$/.test(url)) return 'Subreddit'
    return 'Reddit'
  }
  if (url) {
    try {
      const domain = new URL(url).hostname.replace('www.', '')
      return domain.split('.')[0]
    } catch { /* ignore */ }
  }
  return 'Link'
}

function resolveBadgeIcon(item) {
  if (item.item_type !== 'link') return whiteboardTypeIcon(item.item_type)
  const label = resolveBadgeLabel(item)
  if (label.startsWith('X-')) return 'mdi-twitter'
  if (label.startsWith('TikTok')) return 'mdi-music-note-eighth'
  if (label.startsWith('YouTube') || label.startsWith('YT-')) return 'mdi-youtube'
  if (label.startsWith('IG-') || label === 'Instagram') return 'mdi-instagram'
  if (label === 'Rumble') return 'mdi-video'
  if (label === 'SoundCloud') return 'mdi-soundcloud'
  if (label.startsWith('Reddit') || label === 'Subreddit') return 'mdi-reddit'
  return 'mdi-link'
}

function resolveBadgeBg(item) {
  const label = resolveBadgeLabel(item)
  if (label.startsWith('X-')) return '#E3F2FD'
  if (label.startsWith('TikTok')) return '#FCE4EC'
  if (label.startsWith('YouTube') || label.startsWith('YT-')) return '#FFEBEE'
  if (label.startsWith('IG-') || label === 'Instagram') return '#F3E5F5'
  if (label === 'Rumble') return '#E8F5E9'
  if (label === 'SoundCloud') return '#FFF3E0'
  if (label.startsWith('Reddit') || label === 'Subreddit') return '#FFF3E0'
  return whiteboardTypeBg(item.item_type)
}

function resolveBadgeFg(item) {
  const label = resolveBadgeLabel(item)
  if (label.startsWith('X-')) return '#1565C0'
  if (label.startsWith('TikTok')) return '#C2185B'
  if (label.startsWith('YouTube') || label.startsWith('YT-')) return '#C62828'
  if (label.startsWith('IG-') || label === 'Instagram') return '#6A1B9A'
  if (label === 'Rumble') return '#2E7D32'
  if (label === 'SoundCloud') return '#E65100'
  if (label.startsWith('Reddit') || label === 'Subreddit') return '#E65100'
  return whiteboardTypeFg(item.item_type)
}

function isPlaced(item) {
  return placedAssetIds.value.has(item.asset_id) || placedAssetIds.value.has(String(item.id))
}

function placeItem(item) {
  emit('place-item', { libraryItem: item })
}

function refreshCategory(category) {
  delete itemsCache[category || activeTab.value]
  loadCategory(category || activeTab.value)
}

// Expose methods that parent may call via template ref
defineExpose({ refreshCategory, refreshScripts })
</script>

<style scoped>
/* Scripts section */
.scripts-list {
  padding: 4px;
}
.script-entry {
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  padding: 6px 4px;
}
.script-entry:last-child {
  border-bottom: none;
}
.script-name {
  font-size: 0.8rem !important;
  line-height: 1.2;
  /* Fixed column so the R#/format/size metadata lines up across rows.
     Sized to fit the longest common label ("Director Script") without
     crowding the action buttons; longer labels truncate. */
  flex: 0 0 auto;
  width: 100px;
}
/* Keep the leading icon flush with the first text line (top-aligned row). */
.script-icon {
  margin-top: 1px;
}
/* Compact format selector (PDF / HTML / MD) for each script type. */
.format-toggle {
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  overflow: hidden;
}
.format-chip {
  font-size: 0.55rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  padding: 1px 6px;
  line-height: 1.4;
  color: rgba(0, 0, 0, 0.55);
  background: transparent;
  border: none;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}
.format-chip:last-child {
  border-right: none;
}
.format-chip:hover {
  background: rgba(25, 118, 210, 0.08);
}
.format-chip-active {
  background: #1976d2;
  color: #fff;
}

/* The revision chip doubles as the revisions expander when older
   revisions exist. */
.revision-chip-clickable {
  cursor: pointer;
}
.revision-chip-clickable :deep(.v-icon) {
  transition: transform 0.2s ease;
}
.rotate-180 {
  transform: rotate(180deg);
}
.older-revisions {
  border-left: 2px solid rgba(0, 0, 0, 0.08);
  padding-left: 6px;
}
.revision-row {
  border-bottom: 1px dotted rgba(0, 0, 0, 0.06);
}
.revision-row:last-child {
  border-bottom: none;
}
.asset-pool-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.asset-pool-header {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.03);
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.asset-pool-title {
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: rgba(0, 0, 0, 0.5);
}

.jump-to-wb-link {
  font-size: 0.6rem;
  color: rgba(25, 118, 210, 0.7);
  text-decoration: none;
  white-space: nowrap;
}

.jump-to-wb-link:hover {
  color: #1976D2;
  text-decoration: underline;
}

.asset-pool-tabs {
  flex-shrink: 0;
}

.asset-pool-tab {
  font-size: 0.7rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.3px !important;
  min-width: 48px !important;
  padding: 0 8px !important;
}

.asset-pool-search-row {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}

.asset-pool-search-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 0.75rem;
  padding: 2px 0;
  background: transparent;
  line-height: 1.2;
}

.search-clear {
  cursor: pointer;
  opacity: 0.5;
}

.search-clear:hover {
  opacity: 1;
}

.asset-pool-items {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

/* Whiteboard Tree */
.wb-tree {
  padding: 2px 0;
}

.wb-parent-node {
  display: flex;
  align-items: center;
  padding: 5px 8px;
  cursor: pointer;
  background: #EDE7F6;
  border-bottom: 1px solid rgba(106, 27, 154, 0.12);
  user-select: none;
  transition: padding-left 0.15s ease, background 0.15s ease;
}

.wb-parent-node:hover {
  background: #D1C4E9;
}

.wb-parent-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.8);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.wb-count-chip {
  font-size: 0.55rem !important;
  height: 16px !important;
  flex-shrink: 0;
}

.wb-child-node {
  display: flex;
  align-items: center;
  padding: 4px 8px 4px 28px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.03);
  min-height: 28px;
  transition: padding-left 0.15s ease, background 0.15s ease;
}

.wb-child-node:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.wb-orphan-node {
  display: flex;
  align-items: center;
  padding: 4px 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  min-height: 28px;
  transition: padding-left 0.15s ease;
}

.wb-orphan-node:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

.wb-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  padding: 1px 6px 1px 3px;
  border-radius: 3px;
  font-size: 0.6rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  white-space: nowrap;
  flex-shrink: 0;
  margin-right: 6px;
}

.wb-badge-icon {
  font-size: 11px !important;
  color: inherit !important;
}

.wb-parent-badge {
  margin-right: 6px;
  font-weight: 700;
}

.wb-child-title {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.7);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Drag and drop */
.drag-handle {
  cursor: grab;
  opacity: 0.3;
  flex-shrink: 0;
}

.wb-parent-node:hover .drag-handle,
.wb-child-node:hover .drag-handle,
.wb-orphan-node:hover .drag-handle {
  opacity: 0.7;
}

.dragging {
  opacity: 0.4;
}

/* Drop into parent: highlight the parent and all its children */
.drop-into {
  background: rgba(25, 118, 210, 0.12) !important;
  border-left: 3px solid #1976D2 !important;
  padding-left: 25px;
}

.wb-parent-node.drop-into {
  padding-left: 5px;
  background: rgba(25, 118, 210, 0.2) !important;
  border-left: 4px solid #1565C0 !important;
}

/* Reorder indicator for orphans */
.drag-over-reorder {
  border-top: 2px solid #1976D2 !important;
}

/* Flat list (scheduled) */
.asset-pool-list {
  background: transparent !important;
}

.asset-pool-item {
  min-height: 36px !important;
  padding: 2px 8px !important;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}

.asset-pool-item:hover {
  background: rgba(var(--v-theme-primary), 0.06);
}

.asset-item-title {
  font-size: 0.8rem !important;
  font-weight: 500;
  line-height: 1.3;
}

.asset-item-sub {
  font-size: 0.65rem !important;
  opacity: 0.7;
}

.place-btn {
  width: 22px !important;
  height: 22px !important;
}

.placed-chip {
  font-size: 0.55rem !important;
  height: 16px !important;
}

/* Pooled-media row: slightly smaller filename text */
.pool-media-name {
  font-size: 0.78rem !important;
  line-height: 1.2;
}

/* Pooled-media preview modal */
.pool-preview-body {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  max-height: 80vh;
  overflow: hidden;
}
.pool-preview-media {
  display: block;
  max-width: 100%;
  max-height: 80vh;
  object-fit: contain;
}
</style>
