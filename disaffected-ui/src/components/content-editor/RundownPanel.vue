<template>
  <div
    :class="['rundown-panel', panelWidth === 'narrow' ? 'narrow' : 'wide']"
    :style="{ width: panelWidthValue }"
  >
    <v-card class="h-auto" flat>
      <!-- Rundown Header -->
      <v-card-title class="d-flex align-center pa-2 rundown-title">
        <span class="text-h6">Rundown</span>
        <v-spacer></v-spacer>
        <v-btn
          size="small"
          variant="text"
          @click="$emit('toggle-width')"
        >
          <v-icon size="small" class="mr-1">{{ panelWidth === 'narrow' ? 'mdi-arrow-expand-horizontal' : 'mdi-arrow-collapse-horizontal' }}</v-icon>
          <span class="btn-text-tiny">{{ panelWidth === 'narrow' ? 'Expand' : 'Narrow' }}</span>
        </v-btn>
        <v-btn size="small" variant="text" @click="$emit('close')">
          <v-icon size="small" class="mr-1">mdi-close</v-icon>
          <span class="btn-text-tiny">Close</span>
        </v-btn>
      </v-card-title>
      
      <v-divider style="border-width: 0.5px; opacity: 0.3;"></v-divider>
      
      <!-- Rundown Toolbar - Split Layout with Fixed Options Menu -->
      <div class="rundown-toolbar-split pa-1" style="background-color: rgb(var(--v-theme-surface));">
        <!-- Main Toolbar Grid (left side) -->
        <div class="toolbar-main-grid">
          <!-- New Item Button -->
          <v-btn
            size="x-small"
            color="primary"
            variant="elevated"
            @click="$emit('new-item')"
            class="toolbar-btn-tile"
          >
            <v-icon size="small" class="mr-1">mdi-plus</v-icon>
            <span class="btn-text-tiny">New</span>
            <v-tooltip activator="parent" location="bottom">
              Add New Rundown Item (Ctrl+Shift+N)
            </v-tooltip>
          </v-btn>

          <!-- Delete Selected Button -->
          <v-btn
            size="x-small"
            color="error"
            variant="elevated"
            @click="handleDeleteSelected"
            :disabled="!hasSelections"
            class="toolbar-btn-tile"
          >
            <v-icon size="small" class="mr-1">mdi-delete</v-icon>
            <span class="btn-text-tiny">Del ({{ totalSelectionsCount }})</span>
            <v-tooltip activator="parent" location="bottom">
              <div v-if="hasMultipleSelections">
                Delete Selected: {{ selectionSummary }}
              </div>
              <div v-else-if="selectedItemIndex !== -1">
                Delete Selected Item (Del) - Index: {{ selectedItemIndex }}
              </div>
              <div v-else-if="selectedRegionId">
                Delete Selected Region: {{ getRegionById(selectedRegionId)?.name }}
              </div>
            </v-tooltip>
          </v-btn>


          <!-- Save Button -->
          <v-btn
            size="x-small"
            :color="saveState?.hasChanges ? 'info' : (saveState?.buttonColor || 'success')"
            variant="elevated"
            @click="$emit('save')"
            :disabled="saveState?.isDisabled ?? true"
            class="toolbar-btn-tile"
          >
            <v-icon size="small" class="mr-1">{{ saveState?.buttonIcon || 'mdi-check-circle' }}</v-icon>
            <span class="btn-text-tiny">{{ saveState?.buttonText || 'Sync' }}</span>
            <v-tooltip activator="parent" location="bottom">
              {{ saveState?.tooltip || 'Episode is synchronized - no changes to save' }}
            </v-tooltip>
          </v-btn>

          <!-- View Regions Toggle Button -->
          <v-btn
            size="x-small"
            :color="showRegions ? 'primary' : 'grey'"
            variant="elevated"
            @click="toggleRegionsVisibility"
            class="toolbar-btn-tile"
          >
            <v-icon size="small" class="mr-1">{{ showRegions ? 'mdi-view-grid' : 'mdi-view-list' }}</v-icon>
            <span class="btn-text-tiny">Regions</span>
            <v-tooltip activator="parent" location="bottom">
              {{ showRegions ? 'Hide Regions (Alt+Shift+R)' : 'Show Regions (Alt+Shift+R)' }}
            </v-tooltip>
          </v-btn>

          <!-- Refresh Button -->
          <v-btn
            size="x-small"
            color="primary"
            variant="elevated"
            @click="handleRefresh"
            :loading="loading"
            class="toolbar-btn-tile"
          >
            <v-icon size="small" class="mr-1">mdi-refresh</v-icon>
            <span class="btn-text-tiny">Refresh</span>
            <v-tooltip activator="parent" location="bottom">Refresh Rundown (Ctrl+Shift+R)</v-tooltip>
          </v-btn>

          <!-- Options Menu -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                size="x-small"
                color="orange-darken-2"
                variant="elevated"
                v-bind="props"
                class="toolbar-btn-tile"
              >
                <v-icon size="small" class="mr-1">mdi-dots-vertical</v-icon>
                <span class="btn-text-tiny">Options</span>
                <v-tooltip activator="parent" location="bottom">Rundown Options</v-tooltip>
              </v-btn>
            </template>
            <v-list density="compact">
              <v-list-item @click="createNewRegion">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-plus</v-icon>
                </template>
                <v-list-item-title>Add New Region</v-list-item-title>
                <v-list-item-subtitle>Create a new region</v-list-item-subtitle>
              </v-list-item>
              <v-divider></v-divider>
              <v-list-item @click="$emit('export')">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-export</v-icon>
                </template>
                <v-list-item-title>Export Rundown</v-list-item-title>
                <v-list-item-subtitle>Ctrl+Shift+E</v-list-item-subtitle>
              </v-list-item>
              <v-list-item @click="$emit('sync-order')">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-order-numeric-ascending</v-icon>
                </template>
                <v-list-item-title>Sync Order</v-list-item-title>
                <v-list-item-subtitle>Update order values</v-list-item-subtitle>
              </v-list-item>
              <v-list-item @click="toggleAllBreaksExpansion">
                <template v-slot:prepend>
                  <v-icon size="small">{{ allBreaksCollapsed ? 'mdi-arrow-expand-all' : 'mdi-arrow-collapse-all' }}</v-icon>
                </template>
                <v-list-item-title>{{ allBreaksCollapsed ? 'Expand Breaks' : 'Collapse Breaks' }}</v-list-item-title>
                <v-list-item-subtitle>{{ allBreaksCollapsed ? 'Expand all break regions' : 'Collapse all break regions' }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-menu>
        </div>

      </div>
      
      <v-card-text class="pa-1 rundown-content">
        <!-- List View -->
        <div class="list-view">
          <!-- Column Headers -->
          <div class="rundown-headers" v-if="items && items.length > 0">
            <div class="header-index">#</div>
            <div class="header-type">Type</div>
            <div class="header-slug">Slug</div>
          <div v-if="panelWidth === 'wide'" class="header-duration">Duration</div>
        </div>

        <!-- NEW: Hierarchical Region Structure -->
        <div class="rundown-regions-container" style="min-height: 20px;">
          <!-- Region-level draggable -->
          <draggable
            v-model="regions"
            tag="div"
            :item-key="region => region.id"
            :animation="200"
            class="regions-draggable"
            group="regions"
            ghost-class="ghost-region"
            chosen-class="chosen-region"
            drag-class="drag-region"
            :disabled="false"
            @start="handleRegionDragStart"
            @end="handleRegionDragEnd"
          >
            <template #item="{ element: region }">
              <div
                class="region-container"
                :class="{
                  'region-break': region.type === 'break',
                  'region-selected': selectedRegionId === region.id,
                  'region-collapsed': shouldCollapseRegion(region),
                  'regions-hidden': !showRegions
                }"
                :style="{
                  '--region-color': resolveVuetifyColor(getRegionColor(region.type))
                }"
              >
                <!-- Region Header -->
                <div
                  v-if="showRegions"
                  class="region-header"
                  :class="{
                    'break-region': region.type === 'break',
                    'multi-selected-region': selectedRegionIds.has(region.id)
                  }"
                  :style="selectedRegionId === region.id ? {
                    backgroundColor: getSelectionColor(),
                    color: getSelectionTextColor()
                  } : {
                    backgroundColor: `color-mix(in srgb, ${resolveVuetifyColor(getRegionColor(region.type))} 15%, transparent)`,
                    color: getTextColorForBackground(resolveVuetifyColor(getRegionColor(region.type)))
                  }"
                  @click="handleRegionSelect(region, $event)"
                  @dblclick="handleRegionDoubleClick(region)"
                >
                  <div class="region-header-left">
                    <span class="region-name font-weight-bold">{{ region.name }}</span>
                    <span class="region-duration-inline">: {{ calculateRegionDuration(region) }}</span>
                  </div>

                  <div class="region-header-right">
                    <v-menu>
                      <template v-slot:activator="{ props }">
                        <v-btn
                          icon
                          size="x-small"
                          variant="text"
                          v-bind="props"
                          :style="{ color: getTextColorForBackground(getRegionHeaderColor(getRegionColor(region.type))) }"
                        >
                          <v-icon size="small">mdi-dots-vertical</v-icon>
                        </v-btn>
                      </template>

                      <v-list density="compact">
                        <v-list-item @click="handleEditRegion(region)">
                          <v-list-item-title>Edit Region</v-list-item-title>
                          <template v-slot:prepend>
                            <v-icon size="small">mdi-pencil</v-icon>
                          </template>
                        </v-list-item>

                        <v-list-item @click="toggleRegionCollapse(region)">
                          <v-list-item-title>{{ region.isCollapsed ? 'Expand Region' : 'Collapse Region' }}</v-list-item-title>
                          <template v-slot:prepend>
                            <v-icon size="small">{{ region.isCollapsed ? 'mdi-arrow-expand-all' : 'mdi-arrow-collapse-all' }}</v-icon>
                          </template>
                        </v-list-item>

                        <v-divider style="border-width: 0.5px; opacity: 0.3;" />

                        <v-list-item
                          @click="handleDeleteRegion(region)"
                          class="text-error"
                        >
                          <v-list-item-title>Delete Region</v-list-item-title>
                          <template v-slot:prepend>
                            <v-icon size="small">mdi-delete</v-icon>
                          </template>
                        </v-list-item>
                      </v-list>
                    </v-menu>

                  </div>
                </div>

                <!-- Region Items Container -->
                <div
                  class="region-items"
                  v-show="!shouldCollapseRegion(region)"
                  :class="{
                    'break-region-items': region.type === 'break'
                  }"
                >
                  <!-- Item-level draggable -->
                  <draggable
                    v-model="region.items"
                    tag="div"
                    :item-key="item => item.id"
                    :animation="200"
                    class="items-draggable"
                    group="rundown-items"
                    ghost-class="ghost-item"
                    chosen-class="chosen-item"
                    drag-class="drag-item"
                    :move="allowMove"
                    @start="handleItemDragStart"
                    @end="handleItemDragEnd"
                    @change="handleItemChange"
                  >
                    <template #item="{ element: item }">
                      <v-card
                        flat
                        :class="[
                          'rundown-item-card',
                          { 'selected-item': getItemGlobalIndex(item) === selectedItemIndex },
                          { 'multi-selected-item': selectedItemIndices.has(getItemGlobalIndex(item)) },
                          { 'editing-item': getItemGlobalIndex(item) === editingItemIndex },
                          { 'placeholder-item': item.isPlaceholder },
                          { 'region-item-selected': isItemRegionSelected(item) },
                          { 'generating-item': getItemGlobalIndex(item) === generatingItemIndex },
                          llmState ? llmState.getVisualClass('item', item.id) : ''
                        ]"
                        :style="Object.assign({},
                          {
                            backgroundColor: getItemGlobalIndex(item) === selectedItemIndex ? getSelectionColor() : getBackgroundColorForItem(item?.type || 'unknown'),
                            color: getItemGlobalIndex(item) === selectedItemIndex ? getSelectionTextColor() : getTextColorForItem(item?.type || 'unknown')
                          },
                          llmState ? llmState.getVisualStyle('item', item.id) : {}
                        )"
                        @click="handleItemSelect(item, $event)"
                        @dblclick="handleItemDoubleClick(item)"
                      >
                        <div class="compact-rundown-row">
                            <!-- Index Number Cell -->
                            <div class="index-number-cell">
                              <!-- Red bar for non-production status -->
                              <div
                                v-if="item && item.status !== 'production'"
                                class="status-indicator"
                                :title="`Status: ${item.status}`"
                              ></div>
                              <div class="index-number">{{ (getItemGlobalIndex(item) + 1) * 10 }}</div>
                            </div>

                            <!-- Type -->
                            <div class="type-label">{{ (item?.type || 'UNKNOWN').toUpperCase().substring(0, 3) }}</div>

                            <!-- Slug -->
                            <div class="slug-column">
                              <div class="slug-text">{{ truncateSlug(item?.slug || '', panelWidth) }}</div>
                              <div v-if="panelWidth === 'narrow' && getItemGlobalIndex(item) === selectedItemIndex" class="word-count-display">
                                WC: {{ getWordCount(item) }}
                              </div>
                            </div>

                            <!-- Duration (Right side) -->
                            <div class="duration-display">
                              {{ formatDurationShort(item?.duration || '0:00') }}
                            </div>

                            <!-- Hamburger menu for selected item -->
                            <v-menu v-if="getItemGlobalIndex(item) === selectedItemIndex" location="bottom end">
                              <template v-slot:activator="{ props }">
                                <v-btn
                                  icon
                                  size="small"
                                  variant="text"
                                  class="item-menu-btn-right"
                                  v-bind="props"
                                  @click.stop
                                >
                                  <v-icon size="default">mdi-dots-vertical</v-icon>
                                </v-btn>
                              </template>
                              <v-list>
                                <v-list-item @click="handleItemDelete(item)">
                                  <v-list-item-title>
                                    <v-icon size="small" class="mr-2" color="error">mdi-delete</v-icon>
                                    Delete Item
                                  </v-list-item-title>
                                </v-list-item>
                                <v-list-item @click="requestNewItemAssetID(item)">
                                  <v-list-item-title>
                                    <v-icon size="small" class="mr-2" color="primary">mdi-refresh</v-icon>
                                    Request New AssetID
                                  </v-list-item-title>
                                </v-list-item>
                              </v-list>
                            </v-menu>
                          </div>
                        </v-card>
                    </template>
                  </draggable>
                </div>
              </div>
            </template>
          </draggable>

        </div>


        <!-- Empty state -->
        <div v-if="!items || items.length === 0" class="text-center py-8">
          <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-playlist-remove</v-icon>
          <p class="text-h6 text-grey-lighten-1">No rundown items found</p>
          <p class="text-caption text-grey">Switch to Rundown Manager to add items</p>
        </div>
        </div> <!-- End list-view -->
      </v-card-text>
    </v-card>

    <!-- Flash Message -->
    <v-snackbar
      v-model="showFlashMessage"
      :timeout="3000"
      location="top center"
      color="info"
      variant="elevated"
    >
      {{ flashMessage }}
      <template v-slot:actions>
        <v-btn
          color="white"
          variant="text"
          @click="showFlashMessage = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>

    <!-- New Region Modal -->
    <v-dialog v-model="showNewRegionModal" max-width="400" persistent>
      <v-card>
        <v-card-title class="text-h6">
          Add New Region
        </v-card-title>

        <v-card-text>
          <p class="mb-4">Select the type of region to add:</p>

          <div class="region-type-buttons">
            <v-btn
              v-for="regionType in availableRegionTypes"
              :key="regionType.type"
              :color="regionType.color"
              variant="elevated"
              size="large"
              class="region-type-btn"
              @click="createRegionOfType(regionType.type)"
            >
              {{ regionType.name }}
            </v-btn>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="closeNewRegionModal"
          >
            Cancel
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Region Confirmation Dialog -->
    <v-dialog v-model="showDeleteRegionDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="text-h6 text-error">
          <v-icon class="mr-2" color="error">mdi-delete-alert</v-icon>
          Delete Region
        </v-card-title>

        <v-card-text>
          <div v-if="regionToDelete">
            <p class="mb-4">
              Are you sure you want to delete <strong>{{ regionToDelete.regionName }}</strong>?
            </p>

            <v-alert
              v-if="!regionToDelete.isSelectedRegionDeletion"
              color="warning"
              variant="outlined"
              icon="mdi-alert-circle"
              class="mb-4"
            >
              <div class="text-subtitle-2">This action will permanently delete:</div>
              <ul class="mt-2">
                <li><strong>{{ regionToDelete.itemCount }}</strong> rundown {{ regionToDelete.itemCount === 1 ? 'item' : 'items' }}</li>
                <li>All content and metadata for these items</li>
                <li>This action cannot be undone</li>
              </ul>
            </v-alert>

            <v-alert
              v-else
              color="info"
              variant="outlined"
              icon="mdi-information"
              class="mb-4"
            >
              <div class="text-subtitle-2">This action will:</div>
              <ul class="mt-2">
                <li>Delete the <strong>{{ regionToDelete.regionName }}</strong> region</li>
                <li>Move <strong>{{ regionToDelete.itemCount }}</strong> rundown {{ regionToDelete.itemCount === 1 ? 'item' : 'items' }} to the <strong>"Unassigned"</strong> region</li>
                <li>Preserve all content and metadata</li>
              </ul>
            </v-alert>

            <div class="text-caption text-medium-emphasis">
              Region: {{ regionToDelete.regionName }} ({{ regionToDelete.region.type }})
            </div>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="cancelDeleteRegion"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            variant="elevated"
            @click="confirmDeleteRegion"
          >
            <v-icon class="mr-1">mdi-delete</v-icon>
            Delete Region
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Deletion Confirmation Modal -->
    <v-dialog v-model="showDeleteConfirmModal" max-width="500" persistent>
      <v-card>
        <v-card-title class="text-h6 d-flex align-center">
          <v-icon color="error" class="mr-2">mdi-delete-alert</v-icon>
          Confirm Deletion
        </v-card-title>

        <v-card-text>
          <div class="mb-3">
            <strong>{{ deletionSummary.title }}</strong>
          </div>

          <div v-if="deletionSummary.details.length > 0" class="mb-3">
            <div class="text-subtitle2 mb-2">Items to be deleted:</div>
            <v-list density="compact" class="bg-grey-lighten-4">
              <v-list-item
                v-for="(detail, index) in deletionSummary.details"
                :key="index"
                :prepend-icon="detail.icon"
                :title="detail.name"
                :subtitle="detail.subtitle"
              >
                <template v-slot:append>
                  <v-chip size="small" :color="detail.type === 'region' ? 'primary' : 'secondary'">
                    {{ detail.type }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>
          </div>

          <v-alert
            type="warning"
            variant="tonal"
            density="compact"
            class="mb-0"
          >
            <strong>Warning:</strong> This action cannot be undone.
          </v-alert>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="cancelDeletion"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            variant="elevated"
            @click="confirmDeletion"
            :loading="deletionInProgress"
          >
            <v-icon class="mr-1">mdi-delete</v-icon>
            Delete {{ deletionSummary.count > 1 ? 'All' : '' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Clear Entire Rundown Confirmation Modal -->
    <v-dialog v-model="showClearRundownModal" max-width="600" persistent>
      <v-card>
        <v-card-title class="text-h6 d-flex align-center">
          <v-icon color="error" class="mr-2" size="large">mdi-delete-sweep</v-icon>
          Clear Entire Rundown
        </v-card-title>

        <v-card-text>
          <div class="mb-4">
            <v-alert type="error" variant="tonal" class="mb-4">
              <strong>WARNING: This action cannot be undone!</strong>
            </v-alert>

            <p class="text-body-1 mb-3">
              You are about to <strong>permanently delete</strong> the entire rundown for episode <strong>{{ episode }}</strong>.
            </p>

            <p class="text-body-2 mb-3">
              This will:
            </p>

            <ul class="text-body-2 mb-4">
              <li>Delete all rundown items and regions</li>
              <li>Remove all corresponding .md files from the file system</li>
              <li>Clear all database entries for this episode's rundown</li>
              <li>Reset the rundown to a completely blank state</li>
            </ul>

            <v-alert type="info" variant="tonal" density="compact">
              <strong>Note:</strong> This was triggered by the keyboard shortcut <kbd>Ctrl+Alt+Shift+0</kbd>
            </v-alert>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="secondary"
            @click="cancelClearRundown"
            :disabled="clearRundownInProgress"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            variant="elevated"
            @click="confirmClearRundown"
            :loading="clearRundownInProgress"
          >
            <v-icon class="mr-1">mdi-delete-sweep</v-icon>
            Clear Entire Rundown
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { themeColorMap, getColorValue, resolveVuetifyColor, getTextColorForBackground, loadColorsFromDatabase } from '@/utils/themeColorMap'
import { useRegions } from '@/composables/useRegions'
import draggable from 'vuedraggable'

export default {
  name: 'RundownPanel',
  components: {
    draggable
  },
  emits: [
    'close',
    'toggle-width',
    'save',
    'new-item',
    'delete-selected',
    'sync-order',
    'export',
    'refresh',
    'toggle-options',
    'select-item',
    'edit-item',
    'reorder-items',
    'create-region',
    'delete-region',
    'rundown-cleared',
    'select-region'
  ],
  props: {
    panelWidth: {
      type: String,
      default: 'wide',
      validator: (value) => ['narrow', 'wide'].includes(value)
    },
    items: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    selectedItemIndex: {
      type: Number,
      default: -1
    },
    editingItemIndex: {
      type: Number,
      default: -1
    },
    collapseBreakRegions: {
      type: Boolean,
      default: false
    },
    saveState: {
      type: Object,
      default: () => ({
        hasChanges: false,
        buttonText: 'Synchronized',
        buttonColor: 'success',
        buttonIcon: 'mdi-check-circle',
        isDisabled: true,
        tooltip: 'Episode is synchronized - no changes to save'
      })
    },
    generatingItemIndex: {
      type: Number,
      default: -1
    },
    llmState: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      isDragging: false,
      originalTransforms: new Map(), // Store original transforms
      showNewRegionModal: false,
      selectedRegionType: null,
      newRegionName: '',
      isDraggingRegion: false, // Track if dragging entire region
      draggedRegionType: null, // Type of region being dragged (block/break)
      draggedRegionId: null, // ID of region being dragged
      hoveredRegionId: null, // Region currently being hovered over during drag
      showDeleteRegionDialog: false, // Show region deletion confirmation
      regionToDelete: null, // Store region data for deletion
      selectedRegionId: null, // Track which region is currently selected
      flashMessage: '', // Flash message text
      showFlashMessage: false, // Flash message visibility

      // Multi-selection support
      selectedItemIndices: new Set(), // Set of selected item indices
      selectedRegionIds: new Set(), // Set of selected region IDs
      isMultiSelectMode: false, // Whether we're in multi-select mode

      // Deletion confirmation modal
      showDeleteConfirmModal: false,
      deletionInProgress: false,
      pendingDeletion: null, // Store deletion data: { type, items, regions, callback }

      // Clear entire rundown modal
      showClearRundownModal: false,
      clearRundownInProgress: false,

      // Region visibility toggle
      showRegions: false  // Default to regions hidden
    }
  },
  setup() {
    const { groupItemsIntoRegions, getRegionColor } = useRegions()
    return {
      groupItemsIntoRegions,
      getRegionColor,
      resolveVuetifyColor,
      getTextColorForBackground
    }
  },
  computed: {
    panelWidthValue() {
      return this.panelWidth === 'narrow' ? '300px' : '520px'
    },
    safeItems() {
      return this.items || []
    },
    localItems: {
      get() {
        return this.safeItems
      },
      set(/* newValue */) {
        // This will be called when vue.draggable reorders items
        // We don't need to do anything here as the parent manages the data
      }
    },

    regions() {
      return this.groupItemsIntoRegions(this.safeItems)
    },

    // Convert hierarchical regions back to flat array for parent compatibility
    flatItemsFromRegions() {
      if (!this.regions) return []

      const flatItems = []
      this.regions.forEach(region => {
        region.items.forEach(item => {
          // Remove regionId when flattening to avoid circular references
          // eslint-disable-next-line no-unused-vars
          const { regionId, ...cleanItem } = item
          flatItems.push(cleanItem)
        })
      })
      return flatItems
    },

    // Create a flat array of items with region headers interspersed
    itemsWithHeaders() {
      if (!this.regions.length) return []

      const result = []
      let blockCounter = 0
      let breakCounter = 0

      this.regions.forEach((region, regionIndex) => {
        // Generate region header name
        let regionName
        if (region.type === 'block') {
          blockCounter++
          regionName = `Block ${String.fromCharCode(64 + blockCounter)}` // A, B, C...
        } else if (region.type === 'break') {
          breakCounter++
          regionName = `Break ${breakCounter}`
        } else {
          regionName = region.name
        }

        // Add region header
        const regionColor = this.getRegionColor(region.type);
        console.log(`[DEBUG] Region ${region.type} color:`, regionColor);
        result.push({
          isRegionHeader: true,
          regionId: region.id,
          regionType: region.type,
          regionName: regionName,
          regionColor: regionColor,
          itemCount: region.items.length
        })

        // Add region items
        region.items.forEach(item => {
          result.push({
            ...item,
            regionId: region.id,
            regionType: region.type,
            regionColor: this.getRegionColor(region.type)
          })
        })

        // Add new region button after the last region
        if (regionIndex === this.regions.length - 1) {
          result.push({
            isNewRegionButton: true,
            id: 'new-region-button'
          })
        }
      })

      return result
    },

    // Available region types for the modal
    availableRegionTypes() {
      return [
        {
          type: 'block',
          name: 'Standard Block',
          color: 'primary'
        },
        {
          type: 'break',
          name: 'Break',
          color: 'secondary'
        }
      ]
    },

    // Get the region ID that contains the currently selected item
    selectedItemRegionId() {
      if (this.selectedItemIndex === -1 || !this.safeItems[this.selectedItemIndex]) {
        return null
      }
      const selectedItem = this.safeItems[this.selectedItemIndex]
      return this.getRegionIdForItem(selectedItem)
    },

    // Multi-selection computed properties
    hasMultipleSelections() {
      return this.selectedItemIndices.size > 0 || this.selectedRegionIds.size > 0
    },

    hasSelections() {
      return this.hasMultipleSelections || this.selectedItemIndex !== -1 || this.selectedRegionId !== null
    },

    totalSelectionsCount() {
      return this.selectedItemIndices.size + this.selectedRegionIds.size
    },

    selectionSummary() {
      const items = this.selectedItemIndices.size
      const regions = this.selectedRegionIds.size

      if (items === 0 && regions === 0) return 'None'
      if (items === 0) return `${regions} region${regions === 1 ? '' : 's'}`
      if (regions === 0) return `${items} item${items === 1 ? '' : 's'}`
      return `${items} item${items === 1 ? '' : 's'} & ${regions} region${regions === 1 ? '' : 's'}`
    },

    deletionSummary() {
      if (!this.pendingDeletion) {
        return { title: '', details: [], count: 0 }
      }

      const { regions = [], items = [] } = this.pendingDeletion
      const details = []
      let count = 0

      // Add regions to deletion summary
      regions.forEach(region => {
        const regionName = region.name || region.type || `Region ${region.id}`
        const itemCount = region.items ? region.items.length : 0
        details.push({
          name: regionName,
          subtitle: itemCount > 0 ? `${itemCount} item${itemCount === 1 ? '' : 's'}` : 'Empty region',
          icon: 'mdi-folder',
          type: 'region'
        })
        count++
      })

      // Add individual items to deletion summary
      items.forEach(item => {
        const itemName = item.slug || item.title || `Item ${item.id}`
        details.push({
          name: itemName,
          subtitle: `Type: ${(item.type || 'unknown').toUpperCase()}`,
          icon: 'mdi-file-document',
          type: 'item'
        })
        count++
      })

      // Generate title based on what's being deleted
      let title = ''
      const regionCount = regions.length
      const itemCount = items.length

      if (regionCount > 0 && itemCount > 0) {
        title = `Delete ${regionCount} region${regionCount === 1 ? '' : 's'} and ${itemCount} item${itemCount === 1 ? '' : 's'}?`
      } else if (regionCount > 0) {
        title = `Delete ${regionCount} region${regionCount === 1 ? '' : 's'}?`
      } else if (itemCount > 0) {
        title = `Delete ${itemCount} item${itemCount === 1 ? '' : 's'}?`
      } else {
        title = 'Delete selected items?'
      }

      return {
        title,
        details,
        count
      }
    },

    // Check if all break regions are collapsed
    allBreaksCollapsed() {
      const breakRegions = this.regions.filter(region => region.type === 'break')
      if (breakRegions.length === 0) return false
      return breakRegions.every(region => region.isCollapsed === true)
    }

  },
  async mounted() {
    // Load color configuration from database
    try {
      await loadColorsFromDatabase('default');
      console.log('Colors loaded successfully in RundownPanel');
      // Force reactivity update
      this.$forceUpdate();
    } catch (error) {
      console.warn('Failed to load colors in RundownPanel, using defaults:', error);
    }

    // Add keyboard listener for clear rundown shortcut - use capture phase for higher priority
    document.addEventListener('keydown', this.handleKeydown, true);
  },
  beforeUnmount() {
    // Clean up keyboard listener
    document.removeEventListener('keydown', this.handleKeydown, true);
  },
  methods: {
    // Region visibility toggle
    toggleRegionsVisibility() {
      this.showRegions = !this.showRegions;
      console.log(`Regions ${this.showRegions ? 'shown' : 'hidden'}`);
    },

    // Handle refresh with flash message
    handleRefresh() {
      // Show flash message
      this.flashMessage = 'Refreshing';
      this.showFlashMessage = true;

      // Emit refresh event
      this.$emit('refresh');

      // Hide flash message after 2 seconds
      setTimeout(() => {
        this.showFlashMessage = false;
      }, 2000);
    },

    // NEW: Methods for hierarchical structure (future use)
    calculateRegionDuration(region) {
      if (!region.items || region.items.length === 0) {
        return region.estimatedDuration || '00:00:00'
      }

      let totalSeconds = 0
      region.items.forEach(item => {
        if (item.duration) {
          const [hours, minutes, seconds] = item.duration.split(':').map(Number)
          totalSeconds += hours * 3600 + minutes * 60 + seconds
        }
      })

      const hours = Math.floor(totalSeconds / 3600)
      const minutes = Math.floor((totalSeconds % 3600) / 60)
      const seconds = totalSeconds % 60

      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
    },

    shouldCollapseRegion(region) {
      // All regions (including break regions) follow their isCollapsed state
      // Break regions stay expanded once opened until explicitly collapsed
      return region.isCollapsed
    },

    toggleAllBreaksExpansion() {
      // Find all break regions
      const breakRegions = this.regions.filter(region => region.type === 'break')
      if (breakRegions.length === 0) return

      // Determine target state - if all are collapsed, expand them; otherwise collapse all
      const shouldExpand = this.allBreaksCollapsed

      // Toggle all break regions to the target state
      breakRegions.forEach(region => {
        region.isCollapsed = !shouldExpand
      })

      console.log(`${shouldExpand ? 'Expanded' : 'Collapsed'} ${breakRegions.length} break regions`)
    },

    toggleRegionCollapse(region) {
      // Toggle the collapse state of a specific region
      const newState = !region.isCollapsed
      region.isCollapsed = newState

      console.log(`${newState ? 'Collapsed' : 'Expanded'} region: ${region.name}`)
    },

    getItemGlobalIndex(item) {
      // Find the global index of an item across all regions
      let globalIndex = 0
      for (const region of this.regions) {
        const itemIndex = region.items.findIndex(i => i.id === item.id)
        if (itemIndex !== -1) {
          return globalIndex + itemIndex
        }
        globalIndex += region.items.length
      }
      return -1
    },

    // Check if an item's parent region is selected
    isItemRegionSelected(item) {
      if (!this.selectedRegionId || !item) return false

      // Find which region this item belongs to
      for (const region of this.regions) {
        const itemIndex = region.items.findIndex(i => i.id === item.id)
        if (itemIndex !== -1) {
          return region.id === this.selectedRegionId
        }
      }
      return false
    },

    getTextColorForItem(type) {
      const colorMapping = themeColorMap[type] || themeColorMap.unknown
      // The themeColorMap now calculates text color dynamically based on contrast
      return colorMapping.textColor || '#ffffff'
    },
    
    getBackgroundColorForItem(type) {
      const colorValue = getColorValue(type.toLowerCase()) || 'grey'
      const resolvedColor = resolveVuetifyColor(colorValue)
      return resolvedColor
    },
    
    getSelectionColor() {
      const selectionValue = getColorValue('Selection-interface') || 'orange'
      const resolvedColor = resolveVuetifyColor(selectionValue)
      console.log('🎨 Selection Color Debug:', {
        raw: selectionValue,
        resolved: resolvedColor,
        key: 'Selection-interface'
      })
      return resolvedColor
    },

    getSelectionTextColor() {
      // Use the theme system's contrast logic for selection background
      const colorMapping = themeColorMap['Selection-interface'] || themeColorMap.unknown
      return colorMapping.textColor || '#000000'
    },
    formatDuration(duration) {
      if (!duration) return '0:00'
      if (typeof duration === 'string' && duration.includes(':')) {
        return duration
      }
      // Handle numeric duration (assuming seconds)
      if (typeof duration === 'number') {
        const minutes = Math.floor(duration / 60)
        const seconds = duration % 60
        return `${minutes}:${seconds.toString().padStart(2, '0')}`
      }
      return duration.toString()
    },

    formatDurationShort(duration) {
      // Format duration as mm:ss only (4 digits + colon)
      if (!duration) return '00:00'

      let durationStr = duration
      if (typeof duration === 'number') {
        const minutes = Math.floor(duration / 60)
        const seconds = duration % 60
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
      }

      if (typeof duration === 'string') {
        // Clean string - remove any non-numeric/non-colon characters
        durationStr = durationStr.replace(/[^0-9:]/g, '')

        const parts = durationStr.split(':').filter(p => p !== '')

        if (parts.length === 0) return '00:00'

        // Parse based on number of parts
        let totalMinutes = 0
        let seconds = 0

        if (parts.length >= 3) {
          // Format: hh:mm:ss (or more parts, take first 3)
          const hours = parseInt(parts[0]) || 0
          const minutes = parseInt(parts[1]) || 0
          seconds = parseInt(parts[2]) || 0
          totalMinutes = (hours * 60) + minutes
        } else if (parts.length === 2) {
          // Format: mm:ss
          totalMinutes = parseInt(parts[0]) || 0
          seconds = parseInt(parts[1]) || 0
        } else if (parts.length === 1) {
          // Format: just seconds
          seconds = parseInt(parts[0]) || 0
        }

        return `${totalMinutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
      }

      return '00:00'
    },

    truncateSlug(slug, panelWidth) {
      // Truncate slug to 17 characters or nearest word boundary not exceeding 20 chars
      if (!slug) return ''

      const lowerSlug = slug.toLowerCase()

      // In expanded mode, apply truncation logic
      if (panelWidth === 'wide' && lowerSlug.length > 20) {
        // Try to find word boundary (space or hyphen) near 17 chars, but not exceeding 20
        let truncateAt = 17

        // Look for word boundary between position 17 and 20
        for (let i = 17; i <= 20 && i < lowerSlug.length; i++) {
          if (lowerSlug[i] === ' ' || lowerSlug[i] === '-') {
            truncateAt = i
            break
          }
        }

        // If no word boundary found between 17-20, look backwards from 17
        if (truncateAt === 17) {
          for (let i = 17; i >= 0; i--) {
            if (lowerSlug[i] === ' ' || lowerSlug[i] === '-') {
              truncateAt = i
              break
            }
          }
        }

        return lowerSlug.substring(0, truncateAt) + '...'
      }

      return lowerSlug
    },

    getWordCount(item) {
      // Calculate word count from script_content, excluding code blocks but counting FSQ quotes
      if (!item?.script_content) return 0

      let content = item.script_content

      // Remove YAML frontmatter (everything between --- markers)
      content = content.replace(/^---[\s\S]*?---\n?/m, '')

      // Remove code blocks (fenced with ``` or indented)
      content = content.replace(/```[\s\S]*?```/g, '')
      content = content.replace(/^( {4}|\t).*$/gm, '')

      // Remove HTML/XML tags
      content = content.replace(/<[^>]*>/g, '')

      // Remove markdown links but keep the text
      content = content.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')

      // Remove markdown image syntax
      content = content.replace(/!\[([^\]]*)\]\([^)]+\)/g, '')

      // Count words (split by whitespace and filter empty strings)
      const words = content.trim().split(/\s+/).filter(w => w.length > 0)

      return words.length
    },

    // Dropline color methods for ghost item styling
    getDroplineColor() {
      const droplineValue = getColorValue('dropline') || 'green-lighten-4'
      return resolveVuetifyColor(droplineValue)
    },

    getDroplineBackground() {
      const droplineValue = getColorValue('dropline') || 'green-lighten-4'
      const baseColor = resolveVuetifyColor(droplineValue)
      // Convert to rgba with low opacity for background
      const rgb = baseColor.match(/\w\w/g)?.map(hex => parseInt(hex, 16))
      return rgb ? `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.2)` : 'rgba(200, 230, 201, 0.2)'
    },

    getDroplineTextColor() {
      const droplineValue = getColorValue('dropline') || 'green-lighten-4'
      const baseColor = resolveVuetifyColor(droplineValue)
      // Use slightly more opaque version for text
      const rgb = baseColor.match(/\w\w/g)?.map(hex => parseInt(hex, 16))
      return rgb ? `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.8)` : 'rgba(200, 230, 201, 0.8)'
    },
    
    // Drag handlers for vue.draggable.next - implementing SortableJS transform workaround
    handleChoose(/* event */) {
      // Capture all transforms before SortableJS destroys them
      this.originalTransforms.clear()
      const container = this.$el.querySelector('.rundown-items-container')
      const cards = container.querySelectorAll('.rundown-item-card')
      
      cards.forEach((card, index) => {
        const computedStyle = window.getComputedStyle(card)
        this.originalTransforms.set(index, computedStyle.transform)
      })
    },

    handleDragStart(/* event */) {
      this.isDragging = true
    },
    
    handleDragEnd(event) {
      this.isDragging = false
      
      // Restore transforms after SortableJS finishes (workaround from GitHub issue #2423)
      setTimeout(() => {
        const container = this.$el.querySelector('.rundown-items-container')
        const cards = container.querySelectorAll('.rundown-item-card')
        
        cards.forEach((card, index) => {
          const originalTransform = this.originalTransforms.get(index)
          if (originalTransform && originalTransform !== 'none') {
            card.style.transform = originalTransform
          }
        })
        
        this.originalTransforms.clear()
      }, 50) // Short delay to let SortableJS finish
      
      // Create properly reordered array
      const newItems = [...this.safeItems]
      const [draggedItem] = newItems.splice(event.oldIndex, 1)
      newItems.splice(event.newIndex, 0, draggedItem)
      
      this.$emit('reorder-items', {
        oldIndex: event.oldIndex,
        newIndex: event.newIndex,
        items: newItems
      })
    },

    // Helper method to get the original index of an item in the safeItems array (0-based)
    getItemIndex(item) {
      return this.safeItems.findIndex(i => i.id === item.id)
    },

    // Get a light background color for region items
    getRegionBackgroundColor(regionColor) {
      const resolvedColor = resolveVuetifyColor(regionColor)
      // Convert hex to RGB and apply low opacity
      const rgb = resolvedColor.match(/\w\w/g)?.map(hex => parseInt(hex, 16))
      return rgb ? `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.08)` : 'rgba(0, 0, 0, 0.05)'
    },

    // Get a darker variant of the region color for headers
    getRegionHeaderColor(regionColor) {
      console.log(`[DEBUG] getRegionHeaderColor input:`, regionColor);

      // Handle undefined/null regionColor
      if (!regionColor) {
        return resolveVuetifyColor('grey-darken-1')
      }

      // Try to get a darker variant by appending -darken-1
      let darkerColor = regionColor

      // If it doesn't already have a variant, add -darken-1
      if (!regionColor.includes('-lighten-') && !regionColor.includes('-darken-')) {
        darkerColor = regionColor + '-darken-1'
      } else if (regionColor.includes('-lighten-')) {
        // Convert lighten to darken, but cap at darken-4 for all colors
        const lightenLevel = parseInt(regionColor.match(/-lighten-(\d)/)?.[1]) || 1
        const darkenLevel = Math.min(lightenLevel, 4) // Cap at darken-4
        darkerColor = regionColor.replace('-lighten-' + lightenLevel, '-darken-' + darkenLevel)
      } else if (regionColor.includes('-darken-')) {
        // Already dark, but make it slightly darker (cap at darken-4)
        const currentLevel = parseInt(regionColor.match(/-darken-(\d)/)?.[1]) || 1
        darkerColor = regionColor.replace(/-darken-\d/, `-darken-${Math.min(currentLevel + 1, 4)}`)
      }

      const resolvedColor = resolveVuetifyColor(darkerColor);
      console.log(`[DEBUG] getRegionHeaderColor output: ${darkerColor} -> ${resolvedColor}`);
      return resolvedColor;
    },

    // Region handler methods
    handleEditRegion(regionHeader) {
      console.log('Edit region:', regionHeader.regionName)
      // TODO: Implement region editing
    },

    handleDuplicateRegion(regionHeader) {
      console.log('Duplicate region:', regionHeader.regionName)
      // TODO: Implement region duplication
    },

    handleDeleteRegion(element) {
      // Find the region that this element belongs to
      const region = this.getRegionForItem(element)
      if (!region) {
        console.error('Could not find region for element:', element)
        return
      }

      console.log('Delete region:', region)

      // Store the region data for the confirmation dialog
      this.regionToDelete = {
        region: region,
        element: element,
        regionName: this.getRegionHeaderName(element),
        itemCount: region.items.length
      }

      // Show confirmation dialog
      this.showDeleteRegionDialog = true
    },

    confirmDeleteRegion() {
      if (!this.regionToDelete) return

      const { region, regionName, itemCount, isSelectedRegionDeletion } = this.regionToDelete

      if (isSelectedRegionDeletion) {
        console.log(`Moving items from region "${regionName}" to unassigned region`)

        // Emit event to parent to handle moving items to unassigned region
        this.$emit('move-region-to-unassigned', {
          regionId: region.id,
          regionType: region.type,
          regionName: regionName,
          items: region.items,
          itemIds: region.items.map(item => item.id)
        })
      } else {
        console.log(`Deleting region "${regionName}" with ${itemCount} items`)

        // Emit event to parent to handle the actual deletion
        this.$emit('delete-region', {
          regionId: region.id,
          regionType: region.type,
          regionName: regionName,
          items: region.items,
          itemIds: region.items.map(item => item.id)
        })
      }

      // Close dialog and reset
      this.cancelDeleteRegion()
    },

    cancelDeleteRegion() {
      this.showDeleteRegionDialog = false
      this.regionToDelete = null
    },

    // Calculate total duration for a region
    getRegionTotalDuration(regionId) {
      // Find the region from our grouped data
      const region = this.regions.find(r => r.id === regionId)
      if (!region || !region.items || region.items.length === 0) {
        return '00:00:00'
      }

      let totalSeconds = 0
      region.items.forEach(item => {
        if (item.duration) {
          // Handle different duration formats
          let duration = item.duration.toString()

          // Remove any non-digit characters except colons
          duration = duration.replace(/[^\d:]/g, '')

          // Parse duration parts
          const parts = duration.split(':')
          if (parts.length >= 2) {
            const hours = parts.length >= 3 ? parseInt(parts[0]) || 0 : 0
            const minutes = parseInt(parts[parts.length - 2]) || 0
            const seconds = parseInt(parts[parts.length - 1]) || 0

            totalSeconds += hours * 3600 + minutes * 60 + seconds
          }
        }
      })

      // Convert back to HH:MM:SS:FF format (8 digits to match other durations)
      const hours = Math.floor(totalSeconds / 3600)
      const minutes = Math.floor((totalSeconds % 3600) / 60)
      const secs = totalSeconds % 60
      const frames = 0 // Default to 00 frames for region totals

      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`
    },

    // New Region Modal Methods
    getRegionNamePlaceholder(regionType) {
      const existingRegions = this.regions.filter(r => r.type === regionType)
      const nextNumber = existingRegions.length + 1

      if (regionType === 'block') {
        return `Block ${String.fromCharCode(64 + nextNumber)}` // A, B, C...
      } else if (regionType === 'break') {
        return `Break ${nextNumber}`
      }
      return `${regionType} ${nextNumber}`
    },

    closeNewRegionModal() {
      this.showNewRegionModal = false
      this.selectedRegionType = null
      this.newRegionName = ''
    },


    createRegionOfType(regionType) {
      // Generate default name for the region type
      const regionName = this.getRegionNamePlaceholder(regionType)

      // Emit an event to parent to handle region creation
      this.$emit('create-region', {
        type: regionType,
        name: regionName
      })

      console.log(`Creating new ${regionType} region: ${regionName}`)

      this.closeNewRegionModal()
    },

    // Helper method to determine if an item should be collapsed
    shouldCollapseItem(element) {
      // If collapse setting is disabled, never collapse
      if (!this.collapseBreakRegions) return false

      // Don't collapse if no element
      if (!element) return false

      // Check if this element is in a break region by region type OR region name
      const regionType = element.regionType || this.determineRegionType(element)

      // Get region info to check name as well
      const region = this.getRegionForItem(element)
      const isBreakRegion = (regionType === 'break') ||
                           (region && region.type === 'break') ||
                           (region && region.name && region.name.toLowerCase().includes('break'))

      // Only collapse break regions
      if (!isBreakRegion) return false

      // Don't collapse if this specific region is explicitly selected (clicked on region header)
      const regionId = this.getRegionIdForItem(element)
      const shouldCollapse = this.selectedRegionId !== regionId

      // Debug logging for break region expansion issues
      if (isBreakRegion) {
        console.log(`Break region collapse check - Element: ${element.slug}, RegionId: ${regionId}, SelectedRegionId: ${this.selectedRegionId}, ShouldCollapse: ${shouldCollapse}`)
      }

      // ALWAYS collapse break regions by default, even if an individual item is selected
      // The region will only expand if the user explicitly clicks the region header
      return shouldCollapse
    },

    // Helper methods for draggable template
    shouldShowRegionHeader(element) {
      if (!element || !this.safeItems) return false

      const currentIndex = this.safeItems.findIndex(item => item.id === element.id)
      if (currentIndex === 0) return true // Always show header for first item

      const previousItem = this.safeItems[currentIndex - 1]
      if (!previousItem) return true

      // Show header if region type changes
      const currentRegionType = element.regionType || this.determineRegionType(element)
      const previousRegionType = previousItem.regionType || this.determineRegionType(previousItem)

      return currentRegionType !== previousRegionType
    },

    getRegionHeaderName(element) {
      const regionType = element.regionType || this.determineRegionType(element)

      // Count how many regions of this type exist before this item
      let counter = 1
      const currentIndex = this.safeItems.findIndex(item => item.id === element.id)

      for (let i = 0; i < currentIndex; i++) {
        const itemRegionType = this.safeItems[i].regionType || this.determineRegionType(this.safeItems[i])
        if (itemRegionType === regionType) {
          // Check if this is a region boundary (first item of its type in sequence)
          const prevIndex = i - 1
          if (prevIndex < 0) {
            counter++
          } else {
            const prevRegionType = this.safeItems[prevIndex].regionType || this.determineRegionType(this.safeItems[prevIndex])
            if (prevRegionType !== itemRegionType) {
              counter++
            }
          }
        }
      }

      if (regionType === 'block') {
        return `Block ${String.fromCharCode(64 + counter)}` // A, B, C...
      } else if (regionType === 'break') {
        return `Break ${counter}`
      }
      return `Region ${counter}`
    },

    determineRegionType(item) {
      if (item.regionType) return item.regionType

      const itemType = item.type || item.item_type || 'segment'


      // Use the same logic as useRegions.js
      const regionTypes = [
        {
          type: 'break',
          allowedItemTypes: ['ad', 'promo', 'cta', 'trans', 'break', 'bump']
        },
        {
          type: 'block',
          allowedItemTypes: ['segment', 'interview', 'live', 'pkg', 'vo', 'sot']
        }
      ]

      for (const regionType of regionTypes) {
        if (regionType.allowedItemTypes.includes(itemType)) {
          return regionType.type
        }
      }

      return 'block' // Default
    },

    getRegionDurationForItem(element) {
      const regionType = element.regionType || this.determineRegionType(element)

      // Find all items of the same region type that are consecutive
      const currentIndex = this.safeItems.findIndex(item => item.id === element.id)
      let regionItems = [element]

      // Find consecutive items of the same region type
      for (let i = currentIndex + 1; i < this.safeItems.length; i++) {
        const itemRegionType = this.safeItems[i].regionType || this.determineRegionType(this.safeItems[i])
        if (itemRegionType === regionType) {
          regionItems.push(this.safeItems[i])
        } else {
          break
        }
      }

      // Calculate total duration
      let totalSeconds = 0
      regionItems.forEach(item => {
        if (item.duration) {
          let duration = item.duration.toString().replace(/[^\d:]/g, '')
          const parts = duration.split(':')
          if (parts.length >= 2) {
            const hours = parts.length >= 3 ? parseInt(parts[0]) || 0 : 0
            const minutes = parseInt(parts[parts.length - 2]) || 0
            const seconds = parseInt(parts[parts.length - 1]) || 0
            totalSeconds += hours * 3600 + minutes * 60 + seconds
          }
        }
      })

      const hours = Math.floor(totalSeconds / 3600)
      const minutes = Math.floor((totalSeconds % 3600) / 60)
      const secs = totalSeconds % 60
      const frames = 0

      return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}:${frames.toString().padStart(2, '0')}`
    },

    isLastItem(element) {
      if (!this.safeItems || this.safeItems.length === 0) return false
      const lastItem = this.safeItems[this.safeItems.length - 1]
      return lastItem && lastItem.id === element.id
    },

    // Region drag and drop methods
    getRegionIdForItem(element) {
      const regions = this.regions
      for (const region of regions) {
        if (region.items.some(item => item.id === element.id)) {
          return region.id
        }
      }
      return null
    },

    getRegionForItem(element) {
      const regions = this.regions
      return regions.find(region =>
        region.items.some(item => item.id === element.id)
      )
    },

    isCompatibleDropTarget(element) {
      if (!this.isDraggingRegion || !this.draggedRegionType) return false
      const targetRegionType = this.determineRegionType(element)
      return targetRegionType === this.draggedRegionType
    },



    handleRegionDragOver(event, element) {
      if (!this.isDraggingRegion) return

      if (this.isCompatibleDropTarget(element)) {
        event.dataTransfer.dropEffect = 'move'
      } else {
        event.dataTransfer.dropEffect = 'none'
      }
    },

    handleRegionDragEnter(event, element) {
      if (!this.isDraggingRegion) return
      const regionId = this.getRegionIdForItem(element)
      if (regionId && regionId !== this.draggedRegionId) {
        this.hoveredRegionId = regionId
      }
    },

    handleRegionDragLeave() {
      this.hoveredRegionId = null
    },

    handleRegionDrop(event, element) {
      if (!this.isDraggingRegion) return

      const dropRegion = this.getRegionForItem(element)
      const draggedRegion = this.regions.find(r => r.id === this.draggedRegionId)

      if (!dropRegion || !draggedRegion || dropRegion.id === draggedRegion.id) {
        return
      }

      if (!this.isCompatibleDropTarget(element)) {
        return
      }

      // Swap the two regions by swapping their items' order values
      this.swapRegions(draggedRegion, dropRegion)

      // Re-expand items immediately after drop
      this.$nextTick(() => {
        this.$forceUpdate() // Force reactivity to re-expand items
      })
    },

    swapRegions(region1, region2) {
      // Get all items from both regions
      const region1Items = [...region1.items]
      const region2Items = [...region2.items]

      // Get the order ranges for each region
      const region1Orders = region1Items.map(item => item.order).sort((a, b) => a - b)
      const region2Orders = region2Items.map(item => item.order).sort((a, b) => a - b)

      // Assign region1's items to region2's order positions
      region1Items.forEach((item, index) => {
        if (region2Orders[index] !== undefined) {
          item.order = region2Orders[index]
        }
      })

      // Assign region2's items to region1's order positions
      region2Items.forEach((item, index) => {
        if (region1Orders[index] !== undefined) {
          item.order = region1Orders[index]
        }
      })

      // Emit the reorder event with all affected items
      const allAffectedItems = [...region1Items, ...region2Items]
      this.$emit('reorder-items', {
        type: 'region-swap',
        items: allAffectedItems,
        region1: region1.id,
        region2: region2.id
      })
    },


    // Check if this element shows a region header for a selected region
    isSelectedRegionStart(element) {
      return this.shouldShowRegionHeader(element) &&
             this.selectedRegionId === this.getRegionIdForItem(element)
    },

    // Check if this is the last item in a selected region
    isSelectedRegionEnd(element) {
      if (this.selectedRegionId !== this.getRegionIdForItem(element)) {
        return false
      }

      const currentIndex = this.safeItems.findIndex(item => item.id === element.id)
      const nextIndex = currentIndex + 1

      // It's the last item if there's no next item, or the next item is in a different region
      if (nextIndex >= this.safeItems.length) {
        return true
      }

      const nextElement = this.safeItems[nextIndex]
      const nextRegionId = this.getRegionIdForItem(nextElement)

      return nextRegionId !== this.selectedRegionId
    },

    // Check if this element shows a region header for the region containing selected item
    isSelectedItemRegionStart(element) {
      return this.shouldShowRegionHeader(element) &&
             this.selectedItemRegionId === this.getRegionIdForItem(element)
    },

    // Check if this is the last item in the region containing selected item
    isSelectedItemRegionEnd(element) {
      if (this.selectedItemRegionId !== this.getRegionIdForItem(element)) {
        return false
      }

      const currentIndex = this.safeItems.findIndex(item => item.id === element.id)
      const nextIndex = currentIndex + 1

      // It's the last item if there's no next item, or the next item is in a different region
      if (nextIndex >= this.safeItems.length) {
        return true
      }

      const nextElement = this.safeItems[nextIndex]
      const nextRegionId = this.getRegionIdForItem(nextElement)

      return nextRegionId !== this.selectedItemRegionId
    },


    handleItemDelete(element) {
      const itemIndex = this.getItemIndex(element)
      const item = this.safeItems[itemIndex]

      // Emit event to parent to handle the actual deletion
      this.$emit('delete-item', {
        itemIndex: itemIndex,
        item: item,
        itemId: item.id,
        slug: item.slug || item.title || 'Unnamed Item'
      })

      console.log('Item delete requested:', item)
    },

    handleItemDoubleClick(element) {
      const itemIndex = this.getItemIndex(element)
      const item = this.safeItems[itemIndex]

      this.showFlashMessage = false // Hide any existing message
      this.flashMessage = `Double-clicked rundown item: "${item?.slug || item?.title || 'Unnamed Item'}" (Index: ${itemIndex})`
      this.showFlashMessage = true

      // Auto-hide flash message after 3 seconds
      setTimeout(() => {
        this.showFlashMessage = false
      }, 3000)

      console.log('Item double-clicked:', item)
    },

    handleRegionDoubleClick(element) {
      const regionName = this.getRegionHeaderName(element)
      const regionId = this.getRegionIdForItem(element)

      this.showFlashMessage = false // Hide any existing message
      this.flashMessage = `Double-clicked region: "${regionName}" (ID: ${regionId})`
      this.showFlashMessage = true

      // Auto-hide flash message after 3 seconds
      setTimeout(() => {
        this.showFlashMessage = false
      }, 3000)

      console.log('Region double-clicked:', regionName, regionId)
    },

    handleSelectedRegionDelete(element) {
      // Use the same logic as the existing region deletion but with different messaging
      const region = this.getRegionForItem(element)
      if (!region) {
        console.error('Could not find region for element:', element)
        return
      }

      console.log('Delete selected region:', region)

      // Store the region data for the confirmation dialog
      this.regionToDelete = {
        region: region,
        element: element,
        regionName: this.getRegionHeaderName(element),
        itemCount: region.items.length,
        isSelectedRegionDeletion: true // Flag to indicate this is from the selected region delete button
      }

      // Show confirmation dialog
      this.showDeleteRegionDialog = true
    },

    // NEW: Hierarchical drag handlers
    handleRegionDragStart(evt) {
      console.log('🚀 Region drag started', evt)
      console.log('🔍 Regions array before drag:', this.regions.map(r => ({ id: r.id, name: r.name, type: r.type })))
      this.isDragging = true

      // Enhanced region drag start
      if (evt.item) {
        evt.item.classList.add('currently-dragging-region')
      }
    },

    handleRegionDragEnd(evt) {
      try {
        console.log('🏁 Region drag ended', evt)
        console.log('🔍 Regions array after drag:', this.regions.map(r => ({ id: r.id, name: r.name, type: r.type })))
        console.log('📊 Old index:', evt.oldIndex, 'New index:', evt.newIndex)
        this.isDragging = false

        // Clean up drag classes
        if (evt.item) {
          evt.item.classList.remove('currently-dragging-region')
        }

        // Only emit changes if the position actually changed
        if (evt.oldIndex !== evt.newIndex) {
          console.log('✅ Region order changed - emitting updates')

          // Emit region reorder - parent will handle the logic
          if (this.flatItemsFromRegions) {
            this.$emit('reorder-items', this.flatItemsFromRegions)
          }
          if (this.regions) {
            this.$emit('regions-updated', this.regions)
          }

          // Force save to persist changes to backend
          this.$emit('save')
        } else {
          console.log('ℹ️ Region position unchanged - no updates needed')
        }
      } catch (error) {
        console.error('❌ Error in handleRegionDragEnd:', error)
        this.isDragging = false // Ensure we reset state
      }
    },

    handleItemDragStart(evt) {
      console.log('Item drag started', evt)
      this.isDragging = true

      // Enhanced drag start - add visual feedback
      if (evt.item) {
        evt.item.classList.add('currently-dragging')
      }
    },

    handleItemDragEnd(evt) {
      try {
        console.log('Item drag ended', evt)
        this.isDragging = false

        // Clean up drag classes
        if (evt.item) {
          evt.item.classList.remove('currently-dragging')
        }

        // Enhanced drag end handling - emit reordered items for any drag operation
        // This ensures proper parent synchronization even for within-region moves
        if (this.flatItemsFromRegions) {
          this.$emit('reorder-items', this.flatItemsFromRegions)
        }
        if (this.regions) {
          this.$emit('regions-updated', this.regions)
        }

        // Force save to persist changes to backend
        this.$emit('save')
      } catch (error) {
        console.error('❌ Error in handleItemDragEnd:', error)
        this.isDragging = false // Ensure we reset state
      }
    },

    allowMove(evt) {
      // Debug drag-and-drop blocking issue
      const draggedElement = evt.draggedElement
      const relatedElement = evt.related

      console.log('🔍 Drag Move Validation:', {
        draggedElement: draggedElement,
        draggedData: draggedElement?.__draggable_context?.element,
        itemType: draggedElement?.__draggable_context?.element?.type,
        related: relatedElement,
        targetRegion: evt.to?.closest('.region-container'),
        willAccept: evt.willAccept
      })

      return true  // Allow all moves for debugging
    },

    handleItemChange(evt) {
      try {
        console.log('Item change event', evt)

        // Handle cross-region moves
        if (evt.added) {
          console.log('Item added to region:', evt.added)
          // Update the item's regionId to match its new region
          const addedItem = evt.added.element
          if (addedItem && this.regions) {
            const targetRegion = this.regions.find(r => r.items && r.items.some(item => item.id === addedItem.id))
            if (targetRegion) {
              addedItem.regionId = targetRegion.id
              console.log(`🎯 Updated item ${addedItem.id} to region ${targetRegion.id}`)
            }
          }
        }

        if (evt.removed) {
          console.log('Item removed from region:', evt.removed)
        }

        if (evt.moved) {
          console.log('Item moved within region:', evt.moved)
        }

        // Emit the flattened items back to parent for persistence
        console.log('🔄 Emitting updated items after cross-region change')
        if (this.flatItemsFromRegions) {
          this.$emit('reorder-items', this.flatItemsFromRegions)
        }
        if (this.regions) {
          this.$emit('regions-updated', this.regions)
        }

        // Force save to persist changes to backend
        this.$emit('save')
      } catch (error) {
        console.error('❌ Error in handleItemChange:', error)
        // Don't let the error propagate and crash the component
      }
    },

    // Update region selection for hierarchical structure
    handleRegionSelect(region, event) {
      const isCtrlClick = event && (event.ctrlKey || event.metaKey)

      if (isCtrlClick) {
        // Multi-selection mode with Ctrl+click
        this.isMultiSelectMode = true

        if (this.selectedRegionIds.has(region.id)) {
          // Remove from multi-selection if already selected
          this.selectedRegionIds.delete(region.id)
        } else {
          // Add to multi-selection
          this.selectedRegionIds.add(region.id)
        }
      } else {
        // Normal single selection mode
        if (this.isMultiSelectMode) {
          // Clear all multi-selections first
          this.selectedRegionIds.clear()
          this.selectedItemIndices.clear()
          this.isMultiSelectMode = false
        }

        // Clear item selection when selecting a region
        this.$emit('select-item', -1)

        // Toggle selection: if already selected, deselect; otherwise select
        if (this.selectedRegionId === region.id) {
          this.selectedRegionId = null
          this.$emit('select-region', null) // Emit deselection
          // For break regions, toggle collapsed state when clicking on selected region
          if (region.type === 'break') {
            region.isCollapsed = !region.isCollapsed
          }
        } else {
          this.selectedRegionId = region.id
          this.$emit('select-region', region) // Emit selection with region data
          // For break regions, expand when selected
          if (region.type === 'break') {
            region.isCollapsed = false
          }
        }
      }

      console.log('Region selected:', region.id, 'Ctrl+click:', isCtrlClick, 'Multi-selections:', this.selectedRegionIds.size)
    },

    // Update item selection for hierarchical structure
    handleItemSelect(item, event) {
      const itemIndex = this.getItemGlobalIndex(item)
      const isCtrlClick = event && (event.ctrlKey || event.metaKey)

      if (isCtrlClick) {
        // Multi-selection mode with Ctrl+click
        this.isMultiSelectMode = true

        if (this.selectedItemIndices.has(itemIndex)) {
          // Remove from multi-selection if already selected
          this.selectedItemIndices.delete(itemIndex)
        } else {
          // Add to multi-selection
          this.selectedItemIndices.add(itemIndex)
        }
      } else {
        // Normal single selection mode
        if (this.isMultiSelectMode) {
          // Clear all multi-selections first
          this.selectedRegionIds.clear()
          this.selectedItemIndices.clear()
          this.isMultiSelectMode = false
        }

        // Clear region selection when selecting an item
        this.selectedRegionId = null

        // Toggle selection: if already selected, deselect; otherwise select
        if (this.selectedItemIndex === itemIndex) {
          this.$emit('select-item', -1) // Deselect by passing -1
        } else {
          this.$emit('select-item', itemIndex) // Select the item
        }
      }

      console.log('Item selected:', item.slug, 'index:', itemIndex, 'Ctrl+click:', isCtrlClick, 'Multi-selections:', this.selectedItemIndices.size)
    },

    // Create new region button handler
    createNewRegion() {
      console.log('Create new region clicked')
      this.showNewRegionModal = true
    },

    // Enhanced delete selected functionality - now uses modal
    handleDeleteSelected() {
      try {
        if (this.isMultiSelectMode && this.hasMultipleSelections) {
          // Multi-selection deletion
          const regions = []
          const items = []

          // Collect region objects
          for (const regionId of this.selectedRegionIds) {
            const region = this.regions.find(r => r.id === regionId)
            if (region) regions.push(region)
          }

          // Collect item objects
          for (const itemIndex of this.selectedItemIndices) {
            const item = this.getItemByGlobalIndex(itemIndex)
            if (item) items.push(item)
          }

          this.showDeletionModal({ type: 'multi', regions, items })

        } else if (this.selectedRegionId) {
          // Single region deletion
          const region = this.regions.find(r => r.id === this.selectedRegionId)
          if (region) {
            this.showDeletionModal({ type: 'region', regions: [region], items: [] })
          }
        } else if (this.selectedItemIndex !== -1) {
          // Single item deletion
          const item = this.getItemByGlobalIndex(this.selectedItemIndex)
          if (item) {
            this.showDeletionModal({ type: 'item', regions: [], items: [item] })
          }
        }
      } catch (error) {
        console.error('Error preparing deletion:', error)
      }
    },

    // Show deletion confirmation modal
    showDeletionModal(deletionData) {
      this.pendingDeletion = deletionData
      this.showDeleteConfirmModal = true
    },

    // Cancel deletion
    cancelDeletion() {
      this.showDeleteConfirmModal = false
      this.pendingDeletion = null
      this.deletionInProgress = false
    },

    // Confirm and execute deletion
    async confirmDeletion() {
      if (!this.pendingDeletion) return

      this.deletionInProgress = true

      try {
        const { regions, items } = this.pendingDeletion

        // Delete all selected regions first
        for (const region of regions) {
          const regionName = region.name || region.type || `Region ${region.id}`
          console.log('Deleting region:', regionName)
          this.$emit('delete-region', region)
        }

        // Delete all selected items
        for (const item of items) {
          console.log('Deleting item:', item.slug || item.title || item.id)
          this.$emit('delete-item', item)
        }

        // Clear all selections
        this.selectedRegionIds.clear()
        this.selectedItemIndices.clear()
        this.isMultiSelectMode = false
        this.selectedRegionId = null
        this.$emit('select-item', -1)

        // Close modal
        this.cancelDeletion()

      } catch (error) {
        console.error('Error executing deletion:', error)
        this.deletionInProgress = false
      }
    },

    // Keyboard event handler
    handleKeydown(event) {
      // Ctrl+Shift+R - Refresh/Reload rundown data
      if (event.ctrlKey && event.shiftKey && event.key === 'R') {
        event.preventDefault();
        event.stopPropagation();
        this.$emit('refresh');
        return;
      }

      // Alt+Shift+R - Toggle regions visibility
      if (event.altKey && event.shiftKey && event.key === 'R') {
        event.preventDefault();
        event.stopPropagation();
        this.toggleRegionsVisibility();
        return;
      }

      // Check for Esc key to cancel multi-selection
      if (event.key === 'Escape') {
        // Only handle Esc if we're in multi-select mode or have selections
        if (this.isMultiSelectMode || this.hasMultipleSelections || this.selectedRegionId !== null || this.selectedItemIndex !== -1) {
          console.log('🚫 Esc pressed: Cancelling all selections')
          this.cancelAllSelections()

          // Prevent ALL further processing of this Esc key event
          event.preventDefault()
          event.stopPropagation()
          event.stopImmediatePropagation()

          // Return early to ensure no other handlers run
          return false
        }

        // If Esc is pressed but we don't have selections, still prevent default behavior
        // to avoid unwanted navigation
        console.log('🚫 Esc pressed: No selections to cancel, preventing default navigation')
        event.preventDefault()
        event.stopPropagation()
        event.stopImmediatePropagation()
        return false
      }

      // Check for Ctrl+Alt+Shift+0 to clear entire rundown
      // Note: when Shift+0 is pressed, event.key is ')' but event.code is 'Digit0'
      if (event.ctrlKey && event.altKey && event.shiftKey && (event.key === ')' || event.code === 'Digit0')) {
        console.log('🚨 Clear rundown shortcut triggered!')
        event.preventDefault()
        this.showClearRundownConfirmation()
      }
    },

    // Show clear rundown confirmation modal
    showClearRundownConfirmation() {
      console.log('Clear rundown shortcut triggered')
      this.showClearRundownModal = true
    },

    // Cancel clear rundown
    cancelClearRundown() {
      this.showClearRundownModal = false
    },

    // Execute clear entire rundown
    async confirmClearRundown() {
      this.clearRundownInProgress = true

      try {
        console.log('🚨 Clearing entire rundown for episode:', this.episode)

        // Debug authentication tokens
        const authToken = localStorage.getItem('auth_token') || localStorage.getItem('token')
        const apiKey = localStorage.getItem('api_key')
        console.log('🔐 Auth token:', authToken ? `${authToken.substring(0, 20)}...` : 'NONE')
        console.log('🔑 API key:', apiKey ? `${apiKey.substring(0, 20)}...` : 'NONE')

        const apiUrl = `/api/episodes/${this.episode}/rundown/clear`
        console.log('📡 API URL:', apiUrl)

        // Call API to clear all rundown items and files
        const response = await fetch(apiUrl, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
            'X-API-Key': apiKey
          }
        })

        console.log('📊 Response status:', response.status, response.statusText)
        console.log('📋 Response headers:', [...response.headers.entries()])

        if (!response.ok) {
          // Get detailed error information
          let errorMessage = `HTTP ${response.status}: ${response.statusText}`
          try {
            const errorBody = await response.text()
            console.log('❌ Error response body:', errorBody)
            errorMessage += `\nDetails: ${errorBody}`
          } catch (parseError) {
            console.log('⚠️ Could not parse error response:', parseError)
          }
          throw new Error(errorMessage)
        }

        const result = await response.json()
        console.log('Rundown cleared successfully:', result)

        // Clear local state
        this.selectedItemIndices.clear()
        this.selectedRegionIds.clear()
        this.isMultiSelectMode = false

        // Emit event to parent to reload rundown
        this.$emit('rundown-cleared')

        // Close modal
        this.showClearRundownModal = false

      } catch (error) {
        console.error('Error clearing rundown:', error)
        alert('Failed to clear rundown. Please try again.')
      } finally {
        this.clearRundownInProgress = false
      }
    },

    // Helper method to get item by global index
    getItemByGlobalIndex(globalIndex) {
      let currentIndex = 0
      for (const region of this.regions) {
        for (const item of region.items) {
          if (currentIndex === globalIndex) {
            return item
          }
          currentIndex++
        }
      }
      return null
    },

    // Helper method to get region by ID
    getRegionById(regionId) {
      return this.regions.find(region => region.id === regionId)
    },

    // Request new AssetID for a rundown item
    async requestNewItemAssetID(item) {
      try {
        console.log('Requesting new AssetID for rundown item:', item)

        const response = await fetch('/assetid/regenerate', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
          },
          body: JSON.stringify({
            old_asset_id: item.asset_id,
            entity_type: 'segment',
            reason: 'user_requested_item_regeneration',
            context: {
              item_slug: item.slug,
              item_type: item.type,
              item_id: item.id
            }
          })
        })

        if (!response.ok) {
          throw new Error(`Server error: ${response.status}`)
        }

        const result = await response.json()
        console.log('✅ AssetID regenerated successfully:', result)

        // Update the item with new AssetID
        item.asset_id = result.new_asset_id

        // Show success message
        this.flashMessage = `AssetID regenerated: ${result.old_asset_id} → ${result.new_asset_id}`
        this.showFlashMessage = true

        // Emit event to parent to save the updated item
        this.$emit('item-assetid-updated', {
          item: item,
          oldAssetId: result.old_asset_id,
          newAssetId: result.new_asset_id
        })

        // Force reactive update of the rundown display
        this.$forceUpdate()

        // Emit global refresh event
        this.$emit('assetid-regenerated', {
          entityType: 'segment',
          oldAssetId: result.old_asset_id,
          newAssetId: result.new_asset_id,
          affectedItem: item
        })

      } catch (error) {
        console.error('❌ Failed to regenerate AssetID:', error)
        this.flashMessage = `Failed to regenerate AssetID: ${error.message}`
        this.showFlashMessage = true
      }
    },

    // Cancel all selections and exit multi-select mode
    cancelAllSelections() {
      // Clear all multi-selections
      this.selectedItemIndices.clear()
      this.selectedRegionIds.clear()
      this.isMultiSelectMode = false

      // Clear single selections
      this.selectedRegionId = null
      this.$emit('select-item', -1)

      console.log('✅ All selections cancelled - multi-select mode disabled')
    }
  }
}
</script>

<style scoped>
/* GLOBAL RULE: Eliminate all rounded corners in rundown panel */
.rundown-panel *,
.rundown-panel {
  border-radius: 0 !important;
}

/* Region header styles - slim headers integrated in list view with solid background */
.region-header-slim {
  margin-bottom: 1em; /* 1em internal padding at bottom of region header */
  margin-top: 8px; /* Small gap between regions */
  padding: 2px; /* Match wrapper padding for alignment */
  border: none !important; /* Remove all borders */
  border-left: none !important; /* Remove individual header border - using container border instead */
  border-radius: 0 !important; /* Remove border radius */
}

/* Break regions have reduced height (margins handled by consistent spacing rules below) */
.region-header-slim.break-region {
  height: 60%; /* 60% of normal height */
  overflow: hidden; /* Ensure content doesn't expand beyond reduced height */
  /* Margins handled by consistent spacing rules below */
}

/* SIMPLIFIED APPROACH - work with existing flat structure */

/* Removed - replaced by consistent spacing rules below */

/* First region header has no top margin */
.region-header-slim:first-child {
  margin-top: 0 !important;
}

/* All rundown items have zero margins by default */
.rundown-item-wrapper {
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}

/* Break region items specifically - no margins and no separators */
.rundown-item-wrapper.break-region-item {
  margin-top: 0 !important;
  margin-bottom: 0 !important;
}

/* Remove hairline separators between break region items */
.rundown-item-wrapper.break-region-item .rundown-item-card {
  border-bottom: none !important;
}

.region-header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1px 12px 1px 12px; /* Reduced top and bottom padding for tighter spacing */
  font-size: 0.8rem; /* Reduced from 0.875rem (14px) to 0.8rem (~12.8px) - smaller but above item font */
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-weight: 300; /* Helvetica Light */
  border: none !important; /* Remove all borders */
  border-radius: 0 !important; /* Remove border radius */
}

.region-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.region-header-right {
  display: flex;
  align-items: center;
}

.region-name {
  text-transform: uppercase;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-weight: 300; /* Light weight */
  font-size: 0.8rem; /* Match region header font size - reduced from calc(0.9rem + 0.2em) */
}

.region-type-chip {
  font-size: 0.65rem;
  height: 18px;
}

.region-duration {
  font-family: 'Roboto Mono', monospace;
  font-size: calc(11px + 0.2em);
  font-weight: bold;
  color: inherit;
  white-space: nowrap;
  margin-left: 8px;
  transform: translateX(-9em); /* Shift left by 9em (original -6em + additional -3em) */
}

.region-duration-inline {
  font-family: 'Roboto Mono', monospace;
  font-size: calc(11px + 0.2em);
  font-weight: 300; /* Light weight instead of bold */
  color: inherit;
  white-space: nowrap;
  margin-left: 4px; /* Small space after the colon */
  opacity: 0.8; /* Slightly transparent for lighter appearance */
}

/* Rundown item wrapper with solid region background color - ZERO spacing between items */
.rundown-item-wrapper {
  margin: 0; /* No margins on individual items */
  padding: 0; /* No padding on individual items */
  border-left: none !important; /* Remove individual item border - using container border instead */
  background-color: color-mix(in srgb, var(--region-color, #f5f5f5) 8%, transparent); /* Match region background, not header */
}

/* Override Vuetify card underlay/overlay to prevent background interference */
.rundown-item-wrapper .v-card__underlay,
.rundown-item-wrapper .v-card__overlay {
  background-color: transparent !important;
  opacity: 0 !important;
}

/* Ensure rundown item card has no interfering background layers */
.rundown-item-card .v-card__underlay,
.rundown-item-card .v-card__overlay {
  background-color: transparent !important;
  opacity: 0 !important;
}

/* Force the item wrapper to use light background during all states */
.rundown-item-wrapper {
  background-color: color-mix(in srgb, var(--region-color, #f5f5f5) 8%, transparent) !important;
}

/* Remove break region item styling - only affecting header text */

/* No padding between rundown items */
.rundown-item-wrapper:last-child {
  padding-bottom: 0; /* No padding to maintain zero spacing between items */
}

/* Collapsed break region items - COMPLETELY HIDDEN */
.rundown-item-wrapper.collapsed-break-item {
  height: 0 !important;
  overflow: hidden !important;
  opacity: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  transform: scaleY(0) !important;
  transform-origin: top;
  transition: all 0.3s ease;
}

/* Alternative approach - display none for complete hiding */
.rundown-item-wrapper.collapsed-break-item .rundown-item-card {
  display: none !important;
}

/* CRITICAL: Override collapse when region is selected - allow expansion */
.rundown-item-wrapper.collapsed-break-item.region-item-selected {
  height: auto !important;
  opacity: 1 !important;
  transform: scaleY(1) !important;
  overflow: visible !important;
  transition: all 0.3s ease !important;
}

.rundown-item-wrapper.collapsed-break-item.region-item-selected .rundown-item-card {
  display: flex !important;
}

/* Extra high specificity rule to ensure expansion works */
.rundown-panel .rundown-item-wrapper.collapsed-break-item.region-item-selected {
  height: auto !important;
  opacity: 1 !important;
  transform: scaleY(1) !important;
  overflow: visible !important;
}

.rundown-panel .rundown-item-wrapper.collapsed-break-item.region-item-selected .rundown-item-card {
  display: flex !important;
}

/* Remove all rounded corners per user requirement */
.rundown-panel .v-card,
.rundown-panel .v-card-title,
.rundown-item-card,
.region-header-content {
  border-radius: 0 !important;
}

/* Allow v-card to overflow horizontally for extended rows */
.rundown-panel .v-card {
  overflow-x: visible !important;
  overflow-y: auto !important;
}

/* Also remove rounded corners from any child elements */
.rundown-item-card *,
.region-header-content * {
  border-radius: 0 !important;
}

.list-view {
  /* Keep existing list view styles */
}
.rundown-panel {
  position: sticky !important;
  top: 0 !important;
  height: 100vh; /* Full viewport height - reach bottom no matter what */
  border-right: none; /* Remove border */
  overflow-y: hidden; /* Prevent vertical overflow issues */
  overflow-x: visible; /* Allow items to extend beyond right edge */
  display: flex;
  flex-direction: column;
  z-index: 15 !important; /* Above editor panel (z-index: 10) so rows can overhang */
}

.rundown-title {
  border-bottom: none; /* Remove border */
  min-height: 56px;
}

.rundown-toolbar {
  border-bottom: none; /* Remove border */
}

.rundown-content {
  flex: 1; /* Take up remaining space */
  overflow-y: visible; /* No internal scroll - page scrolls */
  overflow-x: hidden; /* Prevent horizontal scrolling during drag */
  min-height: 0; /* Allow flex item to shrink */
}

.rundown-headers {
  display: grid;
  grid-template-columns: 50px 60px 1fr;
  gap: 8px;
  padding: 8px 12px 8px 12px;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  color: var(--v-medium-emphasis-opacity);
  border-bottom: none; /* Remove border */
  position: relative;
  transform: translateX(25px); /* Match data row positioning */
}

/* Position duration header absolutely too */
.rundown-headers .header-duration {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  text-align: left;
}

.rundown-panel.narrow .rundown-headers {
  grid-template-columns: 40px 40px 1fr;
  padding: 6px 8px;
  font-size: 10px;
  font-weight: normal;
  gap: 6px;
  transform: translateX(15px); /* Match narrow mode data row positioning */
}

.compact-rundown-row {
  display: grid;
  grid-template-columns: 50px 60px 1fr;
  gap: 0px 8px;
  padding: 0px 90px 0px 0px; /* Right padding to make room for absolute duration and delete button */
  align-items: center;
  font-size: 11px;
  font-family: 'Roboto Mono', monospace;
  height: 100%;
  min-height: 2.5em;
}

.rundown-panel.narrow .compact-rundown-row {
  grid-template-columns: 40px 40px 1fr;
  padding: 0px 50px 0px 0px; /* Right padding for duration display in narrow mode */
  font-size: 11px;
  gap: 0px 6px;
  height: 100%;
  min-height: 2.5em;
  align-items: center;
}

/* Index Number Cell with semi-transparent white background */
.index-number-cell {
  background-color: rgba(255, 255, 255, 0.09);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0;
  height: 100%;
  align-self: stretch;
  border-left: none;
  border-top: none;
  border-bottom: none;
  min-width: 50px; /* Ensure consistent width for largest possible numbers */
  position: relative;
}

/* Red status indicator for non-production items */
.status-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 5px;
  background-color: #ff0000 !important;
  border-radius: 0 !important; /* No rounded corners */
  z-index: 100;
}

.rundown-panel.narrow .index-number-cell {
  min-width: 40px; /* Slightly smaller for narrow mode */
}

.index-number {
  font-weight: normal;
  text-align: center;
  font-size: calc(9px + 0.2em);
  color: inherit;
  line-height: 1;
}

.type-label {
  font-weight: normal;
  font-size: 8px;
  text-align: left;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  height: 100%;
  padding-left: 4px;
  margin-right: 10px;
  width: 75px;
  min-width: 75px;
  max-width: 75px;
  flex-shrink: 0;
}

.slug-column {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 100%;
  height: auto; /* Allow height to grow with content */
  overflow: visible; /* Show wrapping text */
}
.slug-text {
  font-weight: normal;
  overflow: visible;
  white-space: normal; /* Allow wrapping */
  word-wrap: break-word;
  line-height: 1.2;
}

.duration-display {
  position: absolute;
  right: 50px; /* Pulled left to be visible with row overhang */
  top: 50%;
  transform: translateY(-50%);
  font-family: 'Roboto Mono', monospace;
  font-size: calc(9px + 0.2em);
  color: inherit;
  white-space: nowrap;
  transition: right 0.3s ease;
  z-index: 5;
}

/* Duration positioning for selected items - keep same position */
.selected-item .duration-display {
  right: 50px; /* Pulled left to be visible with row overhang */
}

/* During drag, all durations maintain position */
.rundown-items-container:has(.chosen-item) .duration-display {
  right: 50px !important;
}

/* Ensure the row container can contain absolute positioned duration */
.rundown-item-card {
  position: relative;
  border-radius: 0 !important;
  transition: background-color 0.3s ease;
  transform: translateX(25px); /* Restore indentation */
  min-height: 2.5em;
  display: flex;
  align-items: center;
  margin: 0 !important; /* Force eliminate any margins */
  padding: 0 !important; /* Force eliminate any padding */
  border: none; /* Remove default card borders that add spacing */
  width: calc(100% + 20px); /* Extend beyond region right edge */
  max-width: none; /* Remove width constraints to allow overhang */
}

/* Force no indentation during any drag operation */
.rundown-items-container:has(.chosen-item) .rundown-item-card {
  transform: translateX(25px) !important; /* Force all items to stay indented during drag */
}

.rundown-item-card:hover:not(.selected-item) {
  transform: translateX(0) translateY(-1px); /* No indentation on hover */
  box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
  transition: box-shadow 0.2s ease;
}

.selected-item {
  border: 2px solid var(--v-primary-base) !important;
  transform: translateX(0) !important; /* No indent when selected */
  width: calc(100% + 20px) !important; /* Extend beyond region right edge */
  max-width: none !important; /* Override any container width restrictions */
  margin-right: 0 !important;
  height: 75px;
  transition:
    background-color 0.3s ease,
    height 0.3s ease 0.1s;
  z-index: 10;
  margin-top: 0 !important; /* Remove top margin */
  margin-bottom: 0 !important; /* Remove bottom margin */
  margin-left: 0 !important; /* Remove left margin */
  display: flex;
  align-items: flex-start;
  overflow: visible !important; /* Ensure extended width is visible */
}

/* Override: Force selected items to stay indented during drag */
.rundown-items-container:has(.chosen-item) .selected-item {
  transform: translateX(25px) !important;
}

/* Narrow mode selected item width compensation */
.rundown-panel.narrow .selected-item {
  width: calc(100% + 15px) !important; /* Extend width to compensate for narrow mode leftward movement */
  margin-right: -15px !important; /* Pull right edge back to original position for narrow mode */
}

/* Narrow mode selected item text styling */
.rundown-panel.narrow .selected-item .index-number {
  font-weight: bold;
}

.rundown-panel.narrow .selected-item .type-label {
  font-weight: bold;
  align-self: start;
  align-items: flex-start;
  justify-content: flex-start;
  text-decoration: underline;
  margin-top: 3px;
  margin-bottom: 3px;
  padding-top: 0;
  font-size: 10px;
}

.rundown-panel.narrow .selected-item .slug-column {
  align-self: start;
  margin-top: 3px;
  margin-bottom: 3px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}

.rundown-panel.narrow .selected-item .slug-text {
  font-size: 11px;
  font-weight: bold;
  text-decoration: underline;
  align-self: flex-start;
}

.rundown-panel.narrow .selected-item .word-count-display {
  font-size: 8px;
  font-weight: normal;
  color: #000000;
  margin-top: 5px;
  text-decoration: none;
}

.rundown-panel.narrow .selected-item .duration-display {
  font-weight: bold;
  top: 5px;
  transform: translateY(0);
  text-decoration: underline;
  margin-bottom: 3px;
}

.rundown-panel.narrow .selected-item .compact-rundown-row {
  align-items: start;
}

/* Wide mode (expanded) selected item text styling */
.selected-item .index-number-cell {
  align-items: center;
  background-color: rgba(255, 255, 255, 0.39);
}

.selected-item .index-number {
  font-weight: bold;
  font-size: 15pt;
  margin-top: 5px;
}

.selected-item .type-label {
  align-self: flex-start;
  align-items: flex-start;
  justify-content: flex-start;
  height: auto;
  padding-top: 0;
  font-weight: bold;
  font-size: 10pt;
  margin-top: 5px;
  width: 106px;
  min-width: 106px;
  max-width: 106px;
  text-decoration: underline;
}

.selected-item .slug-column {
  align-self: flex-start;
  justify-content: flex-start;
  margin-top: 5px;
}

.selected-item .slug-text {
  font-weight: bold;
  font-size: 10pt;
  margin-left: 20px;
  text-transform: uppercase;
  text-decoration: underline;
}

.selected-item .duration-display {
  top: 5px;
  transform: translateY(0);
  font-weight: bold;
  font-size: calc(9px + 0.2em);
  margin-top: 5px;
  text-decoration: underline;
}

.selected-item .compact-rundown-row {
  align-items: flex-start;
  padding-top: 5px;
}

.selected-item .item-menu-btn-right {
  left: -10px;
  right: auto;
  top: 50%;
  transform: translateY(-50%);
  margin-right: 5px;
}

/* Generating item - purple throbbing border */
.generating-item {
  border: 7px solid #9C27B0 !important; /* Purple border */
  animation: throb 1.5s ease-in-out infinite !important;
}

@keyframes throb {
  0%, 100% {
    border-color: #9C27B0;
    box-shadow: 0 0 0 0 rgba(156, 39, 176, 0.7);
  }
  50% {
    border-color: #BA68C8;
    box-shadow: 0 0 20px 5px rgba(156, 39, 176, 0.4);
  }
}

.editing-item {
  border: 2px solid var(--v-warning-base) !important;
}

.rundown-items-container {
  height: calc(100vh - 120px); /* Account for panel header and other UI elements */
  overflow-y: auto;
  overflow-x: visible; /* Allow items to extend beyond right edge */
}

/* Enhanced narrow mode styling */
.rundown-panel.narrow .rundown-title {
  min-height: 48px;
}

.rundown-panel.narrow .rundown-toolbar {
  padding: 4px;
}

.rundown-panel.narrow .index-number {
  font-size: 10px;
  font-weight: normal;
}

.rundown-panel.narrow .type-label {
  font-size: 8px;
  font-weight: normal;
  width: 20px;
  min-width: 20px;
  max-width: 20px;
  margin-right: 0;
}

.rundown-panel.narrow .slug-text {
  font-size: 9px;
  font-weight: normal;
}

.rundown-panel.narrow .rundown-item-card {
  margin: 0 !important; /* Eliminate all margins for seamless items */
  transform: translateX(15px); /* Restore narrow mode indentation */
  transition: background-color 0.3s ease;
  width: calc(100% + 20px); /* Extend beyond region right edge */
  max-width: none; /* Remove width constraints */
}

.rundown-panel.narrow .rundown-item-card:hover {
  transform: translateX(15px) translateY(-0.5px);
  transition: box-shadow 0.2s ease;
}

/* Narrow mode drag override */
.rundown-panel.narrow .rundown-items-container:has(.chosen-item) .rundown-item-card {
  transform: translateX(15px) !important;
}

.rundown-panel.narrow .rundown-items-container:has(.chosen-item) .selected-item {
  transform: translateX(15px) !important;
}


/* New Region Button Styling */
.new-region-button-container {
  display: flex;
  justify-content: flex-end;
  padding: 8px 12px;
  margin-top: 0;
  background-color: transparent;
}

.new-region-btn {
  font-weight: 600;
  letter-spacing: 0.5px;
  border-radius: 0 !important;
}

/* Remove rounded corners from all toolbar buttons */
.rundown-toolbar .v-btn {
  border-radius: 0 !important;
}

/* NEW: Split Toolbar Layout with Fixed Options Menu */
.rundown-toolbar-split {
  border-bottom: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-main-grid {
  display: grid;
  gap: 3px;
  flex: 1;
  grid-template-columns: repeat(3, 1fr);
  align-items: stretch;
}

.toolbar-options-fixed {
  flex-shrink: 0;
  min-width: 70px;
}

.toolbar-btn-tile {
  border-radius: 0 !important;
  min-height: 28px !important; /* 25% smaller than standard 36px */
  font-size: 10px !important; /* Smaller font size */
  flex: 1;
  width: 100% !important;
  justify-self: stretch;
  display: flex !important;
  align-items: center;
  justify-content: center;
  padding: 0 4px !important;
}

.toolbar-btn-tile .btn-text-tiny {
  font-size: 9px !important;
  line-height: 1.1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
}

.options-btn-fixed {
  border-radius: 0 !important;
  min-height: 28px !important;
  font-size: 10px !important;
  width: 100% !important;
  display: flex !important;
  align-items: center;
  justify-content: center;
  padding: 0 4px !important;
  box-shadow: 0 2px 4px rgba(255, 152, 0, 0.3) !important; /* Orange glow */
}

.options-btn-fixed .btn-text-tiny {
  font-size: 9px !important;
  line-height: 1.1;
  white-space: nowrap;
  font-weight: 600;
}

/* Narrow panel adjustments */
.rundown-panel.narrow .toolbar-main-grid {
  grid-template-columns: repeat(2, 1fr);
  gap: 2px;
}

.rundown-panel.narrow .toolbar-btn-tile {
  min-height: 24px !important;
  font-size: 8px !important;
  padding: 0 2px !important;
}

.rundown-panel.narrow .toolbar-btn-tile .btn-text-tiny {
  font-size: 7px !important;
}

.rundown-panel.narrow .options-btn-fixed {
  min-height: 24px !important;
  font-size: 8px !important;
  padding: 0 2px !important;
}

.rundown-panel.narrow .options-btn-fixed .btn-text-tiny {
  font-size: 7px !important;
}

/* Hamburger menu button - positioned between duration and right edge */
.item-menu-btn-right {
  position: absolute;
  right: 12px; /* Moved left from edge */
  top: 50%;
  transform: translateY(-50%);
  z-index: 15; /* Above duration */
}
/* Legacy delete button (backup) */
.item-delete-btn-right {
  position: absolute;
  right: 12px; /* Match hamburger menu position */
  top: 50%;
  transform: translateY(-50%);
  z-index: 15; /* Above duration */
}

/* Narrow mode adjustments */
.rundown-panel.narrow .duration-display {
  right: 12px; /* Position on far right in narrow mode */
  font-size: 10px; /* Slightly larger for readability */
  margin-right: 8px;
}

.rundown-panel.narrow .selected-item .duration-display {
  right: 12px; /* Keep consistent in narrow mode */
  font-size: 10px;
  margin-right: 8px;
}

.rundown-panel.narrow .rundown-items-container:has(.chosen-item) .duration-display {
  right: 12px !important;
  font-size: 10px;
  margin-right: 8px;
}

.rundown-panel.narrow .header-duration {
  right: 70px; /* Align header with data in narrow mode */
}

.rundown-panel.narrow .item-menu-btn-right,
.rundown-panel.narrow .item-delete-btn-right {
  display: none; /* Hide menu buttons in narrow mode to make room for duration */
}

/* Legacy delete button (backup) */
.item-delete-btn {
  position: absolute;
  right: 12px; /* Match updated position */
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
}

/* Modal Button Layout */
.region-type-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  align-items: center;
}

.region-type-btn {
  flex: 1;
  font-weight: 600;
  min-height: 48px;
}

/* Placeholder Item Styling */
.placeholder-item {
  border: 2px dashed rgba(var(--v-primary-base), 0.5) !important;
  background-color: rgba(var(--v-primary-base), 0.05) !important;
  opacity: 0.8;
  position: relative;
}

.placeholder-item::before {
  content: '✏️';
  position: absolute;
  top: 4px;
  right: 8px;
  font-size: 12px;
  opacity: 0.7;
}

.placeholder-item .slug-text {
  font-style: italic;
  font-weight: 500;
}

/* Draggable Container Styling */
.draggable-container {
  width: 100%;
}

/* SIMPLE MARGIN REMOVAL FOR RUNDOWN ITEMS */
.rundown-item-wrapper,
.rundown-item-card {
  margin: 0;
  padding: 0;
}

/* HAIRLINE SEPARATORS: Add very thin border between rundown items */
.rundown-item-card {
  border-bottom: 0.5px solid rgba(255, 255, 255, 0.08) !important;
  box-shadow: none !important; /* Remove any default card shadows */
  outline: none !important; /* Remove any default outlines */
}

/* Remove separator on last item in region to avoid double borders */
.rundown-item-wrapper:last-child .rundown-item-card {
  border-bottom: none !important;
}

/* Keep it simple - just basic spacing control */

/* CRITICAL: Ensure rundown items remain interactive */
.rundown-item-card,
.rundown-item-wrapper,
.region-header-slim {
  pointer-events: auto !important;
  cursor: pointer !important;
}

/* Ensure draggable items remain draggable */
.rundown-item-card {
  cursor: grab !important;
}

.rundown-item-card:active {
  cursor: grabbing !important;
}

/* Vue Draggable Styling */

/* Ghost item - shown while dragging */
.ghost-item {
  opacity: 0.8;
  background: v-bind('getDroplineBackground()') !important;
  border: 2px dashed v-bind('getDroplineColor()') !important;
  color: v-bind('getDroplineTextColor()') !important;
  transform: rotate(2deg); /* Just rotation, no indent */
  transition: all 0.2s ease;
  min-height: 12px; /* Minimum height for visibility */
  margin: 2px 0 !important; /* Small margin to create visible drop zone */
}

/* CRITICAL: Hide region headers in ghost when dragging individual items */
.ghost-item .region-header-slim {
  display: none !important; /* Don't show region headers in item ghost */
}

/* Only show the rundown item card in the ghost */
.ghost-item .rundown-item-wrapper {
  background: transparent !important;
  border: none !important;
}

.ghost-item .rundown-item-card {
  background: v-bind('getDroplineBackground()') !important;
  border: 2px dashed v-bind('getDroplineColor()') !important;
  color: v-bind('getDroplineTextColor()') !important;
}

/* SIMPLE GHOST FIX: Just hide ghosts before region headers */
.ghost-item:has(+ .region-header-slim) {
  display: none;
}

/* Removed redundant ghost item styling - now handled above */


/* Chosen item - item being dragged */
.chosen-item {
  opacity: 0.8;
  transform: scale(1.02); /* Just scale, no indent */
  box-shadow: 0 8px 16px rgba(0,0,0,0.2) !important;
  z-index: 1000;
  cursor: grabbing !important;
}

/* Drag item - visual feedback during drag */
.drag-item {
  transform: rotate(3deg) scale(1.05); /* Just effects, no indent */
  opacity: 0.9;
}

/* Draggable items have grab cursor */
.rundown-item-card {
  cursor: grab;
  transition: all 0.2s ease;
}

/* Disable transitions during drag operations to prevent jumping */
.sortable-drag * {
  transition: none !important;
}

/* Alternative: disable transitions when any draggable operation is happening */
.rundown-items-container:has(.chosen-item) .rundown-item-card:not(.chosen-item) {
  transition: none !important;
}

/* Prevent shake during click interactions by temporarily disabling all transitions */
.rundown-items-container:has(.rundown-item-card:active) * {
  transition: none !important;
}

/* Also disable transitions during the brief moment after click */
.rundown-items-container.clicking * {
  transition: none !important;
}

.rundown-item-card:hover {
  cursor: grab;
}

.rundown-item-card:active {
  cursor: grabbing;
}

/* Region drag and drop visual feedback */
.region-dragging {
  opacity: 0.8;
  transform: scale(1.3) !important; /* Oversized region header during drag */
  cursor: grabbing !important;
  z-index: 1000;
  transition: transform 0.2s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important; /* Dramatic shadow */
}

/* Collapse all rundown items in the region being dragged */
.rundown-item-wrapper.collapsed-during-region-drag {
  height: 0 !important;
  overflow: hidden !important;
  opacity: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  transform: scaleY(0) !important;
  transform-origin: top;
  transition: all 0.2s ease;
}

.rundown-item-wrapper.collapsed-during-region-drag .rundown-item-card {
  display: none !important;
}

.region-compatible-drop {
  background-color: #fff3cd !important; /* Light yellow background */
  box-shadow: 0 0 0 3px #ffc107 !important; /* Thicker yellow border */
  transform: scale(1.05) !important; /* Slightly enlarged to show drop target */
  transition: all 0.2s ease;
  z-index: 500; /* Bring drop targets forward */
}

.region-incompatible {
  opacity: 0.3 !important; /* Gray out incompatible regions */
  transition: all 0.2s ease;
}

.region-hover-target {
  background-color: #ffeaa7 !important; /* Brighter yellow on hover */
  box-shadow: 0 0 0 4px #f39c12 !important; /* Orange border for active hover */
  transform: scale(1.08) !important; /* More dramatic scale */
  transition: all 0.1s ease;
  z-index: 600; /* Highest priority for active hover */
}

/* Make region headers draggable with grab cursor */
.region-header-slim {
  cursor: grab;
  transition: all 0.3s ease; /* Smooth transition for margins and colors */
}

.region-header-slim:hover {
  cursor: grab;
  transform: translateY(-1px);
}

.region-header-slim:active {
  cursor: grabbing;
}

/* Selected region styling with animated margins */
.region-selected {
  box-shadow: 0 0 0 3px v-bind('getSelectionColor()') !important; /* Selection color border */
  border-radius: 0 !important; /* No rounded corners */
  transform: scale(1.02); /* Slight scale for emphasis */
  z-index: 5; /* Bring selected region to front */
}

/* Enhanced transition for margin animations */
.region-header-slim,
.region-header-content {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); /* Material Design easing */
}

/* Selected region item styling */
.region-item-selected {
  opacity: 0.95; /* Slight transparency to show selection */
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); /* Smooth animation */
}

.region-item-selected .rundown-item-card {
  border: 1px solid rgba(var(--v-theme-primary), 0.2) !important; /* Subtle border */
  box-shadow: 0 1px 3px rgba(var(--v-theme-primary), 0.1) !important; /* Subtle shadow */
}

/* Default spacing for all regions, enhanced when selected - OVERRIDDEN ABOVE */
.region-header-slim {
  /* margin-top: 0.5em; DISABLED - using 1em consistent spacing instead */
  margin-bottom: 0;
  transition: margin-top 0.2s cubic-bezier(0.4, 0, 0.2, 1); /* Smooth transition for all margin changes */
}

/* Region selection margins for visual separation - 3em spacing for selected regions */
.region-header-slim.selected-region-start {
  margin-top: 3em !important; /* 3em top margin for selected region */
}

/* NEW: Animated spacing for region containing selected item - ONLY affects region headers */
.region-header-slim.selected-item-region-start {
  margin-top: 2em; /* Top margin for region containing selected item */
  transition: margin-top 0.2s cubic-bezier(0.4, 0, 0.2, 1); /* Faster transition to reduce shake */
}

/* Make sure individual items in selected-item regions still have ZERO margins */
.rundown-item-wrapper.selected-item-region-end .rundown-item-card,
.region-header-slim.selected-item-region-start + .rundown-item-wrapper .rundown-item-card {
  margin: 0 !important;
}

/* Adjust drag container to account for selected region margins during drag operations */
.rundown-items-container:has(.chosen-item) .region-header-slim.selected-region-start {
  margin-top: 0 !important; /* Force remove all margins during drag */
  padding-top: 3em !important; /* Use padding instead during drag operations */
}

/* Region end spacing - only applied to region end items when selected */

.rundown-item-wrapper.selected-region-end {
  margin-bottom: 3em !important; /* 3em bottom margin for selected region */
  transition: margin-bottom 0.2s cubic-bezier(0.4, 0, 0.2, 1); /* Smooth transition */
}

/* NEW: Bottom margin for region containing selected item */
.rundown-item-wrapper.selected-item-region-end {
  margin-bottom: 2em; /* Bottom margin for region containing selected item */
  transition: margin-bottom 0.2s cubic-bezier(0.4, 0, 0.2, 1); /* Faster transition to reduce shake */
}

/* Adjust drag container to account for selected region bottom margins during drag operations */
.rundown-items-container:has(.chosen-item) .rundown-item-wrapper.selected-region-end {
  margin-bottom: 0 !important; /* Force remove all margins during drag */
  padding-bottom: 3em !important; /* Use padding instead during drag operations */
}

/* NEW: Disable item region spacing during drag operations */
.rundown-items-container:has(.chosen-item) .region-header-slim.selected-item-region-start {
  margin-top: 0 !important; /* Remove margin during drag */
  padding-top: 2em !important; /* Use padding instead during drag operations */
}

.rundown-items-container:has(.chosen-item) .rundown-item-wrapper.selected-item-region-end {
  margin-bottom: 0 !important; /* Remove margin during drag */
  padding-bottom: 2em !important; /* Use padding instead during drag operations */
}

/* NEW: Hierarchical Region Structure CSS */

/* Region containers */
.region-container {
  margin-bottom: 1rem;
  border-radius: 0 !important; /* No rounded corners */
  background-color: color-mix(in srgb, var(--region-color, #f5f5f5) 8%, transparent);
  border-left: 7px solid var(--region-color, #666) !important; /* Thinner left border spanning entire region */
  margin-left: 0; /* Ensure bar reaches left edge */
  padding-left: 0; /* Ensure bar reaches left edge */
  overflow: visible !important; /* Allow items to overflow region boundary */
}

.region-container.region-break {
  margin-bottom: 0.5rem; /* Smaller margin for break regions */
}

/* Hidden regions styling - remove backgrounds and collapse whitespace */
.region-container.regions-hidden {
  background-color: transparent !important; /* Remove region background */
  border-left: none !important; /* Remove region border */
  margin-bottom: 1px !important; /* Minimal hairline spacing */
  margin-top: 0 !important; /* Remove top margin */
  padding: 0 !important; /* Remove all padding */
}

/* Remove region items background when regions are hidden */
.region-container.regions-hidden .region-items {
  background-color: transparent !important; /* Remove region items background */
  padding: 0 !important; /* Remove padding */
  margin: 0 !important; /* Remove margins */
}

/* Remove any region header styling when regions are hidden (backup) */
.region-container.regions-hidden .region-header {
  display: none !important; /* Force hide region headers */
}

/* Selected region styling - fill entire region container */
.region-container.region-selected {
  background-color: v-bind('getSelectionColor()') !important;
  border: none !important; /* Remove any borders */
  border-left: 7px solid var(--region-color, #666) !important; /* Preserve thinner left border on selected regions */
  border-radius: 0 !important; /* No rounded corners */
  margin-top: 3em !important; /* Push neighboring regions above away */
  margin-bottom: 3em !important; /* Push neighboring regions below away */
}

/* Selected region header - inherit container background */
.region-container.region-selected .region-header {
  background-color: transparent !important; /* Let container background show through */
  border-left: none !important; /* Remove left border on selected regions */
}

/* Selected region items - inherit container background */
.region-container.region-selected .region-items {
  background-color: transparent !important; /* Let container background show through */
}

/* Selected region item cards - keep original item colors */
.region-container.region-selected .rundown-item-card {
  /* Removed background-color and color overrides to preserve original item styling */
}

/* Region headers in hierarchical structure */
.region-header {
  padding: 0.2rem 1rem; /* Further reduced padding for tighter spacing */
  margin-left: 5px; /* Gap between sidebar and header content */
  border-left: none !important; /* Remove individual header border - using container border instead */
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem; /* Match region-header-content font size */
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-weight: 300; /* Helvetica Light */
  align-items: center;
  min-height: 0.9rem; /* 50% of 1.8rem for compact headers */
}

.region-header.break-region {
  padding: 0.15rem 1rem; /* Further reduced padding for break regions */
}

/* Collapsed break regions - 50% height */
.region-container.region-break.region-collapsed .region-header {
  padding: 0.15rem 1rem; /* Further reduced padding for collapsed break regions */
  min-height: 0.7rem; /* 50% of 1.4rem for collapsed break regions */
}

.region-header-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.region-header-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Region items containers */
.region-items {
  padding: 0.5rem 1rem 1rem 1rem; /* Add internal padding: top, right, bottom, left */
  margin-left: 5px; /* Gap between sidebar and items content - align with header */
  background-color: color-mix(in srgb, var(--region-color, #f5f5f5) 8%, transparent) !important; /* Ensure consistent light background */
  overflow: visible !important; /* Allow items to extend beyond region boundary */
}

.region-items.break-region-items {
  padding: 0.25rem 0.75rem 0.75rem 0.75rem; /* Slightly less padding for break regions */
}

/* Items within regions */
.region-items .rundown-item-wrapper {
  margin: 0; /* No margin between items in same region */
}

/* Fix left whitespace - draggable container should inherit region color */
.region-items .items-draggable {
  background-color: color-mix(in srgb, var(--region-color, #f5f5f5) 8%, transparent) !important;
  border-radius: 0 !important; /* No rounded corners */
}

/* Enhanced Draggable Ghost States - restore full drag behaviors */
.ghost-region {
  opacity: 0.6;
  background: v-bind('getDroplineBackground()') !important;
  border: 2px dashed v-bind('getDroplineColor()') !important;
  transform: rotate(1deg);
}

.chosen-region {
  transform: scale(1.05) !important;
  box-shadow: 0 8px 16px rgba(0,0,0,0.3) !important;
  z-index: 1000;
  opacity: 0.9;
  cursor: grabbing !important;
}

.drag-region {
  opacity: 0.7;
  transform: rotate(2deg) scale(1.02);
}

.ghost-item {
  opacity: 0.6;
  background: v-bind('getDroplineBackground()') !important;
  border: 2px dashed v-bind('getDroplineColor()') !important;
  transform: rotate(2deg);
  min-height: 12px;
  margin: 2px 0 !important;
}

.chosen-item {
  transform: scale(1.02) !important;
  box-shadow: 0 8px 16px rgba(0,0,0,0.2) !important;
  z-index: 1000;
  opacity: 0.8;
  cursor: grabbing !important;
}

.drag-item {
  opacity: 0.9;
  transform: rotate(3deg) scale(1.05);
}

/* Additional drag feedback classes */
.currently-dragging {
  border: 2px solid var(--v-primary-base) !important;
  background: rgba(var(--v-primary-rgb), 0.1) !important;
}

.currently-dragging-region {
  border: 3px solid var(--v-accent-base) !important;
  background: rgba(var(--v-accent-rgb), 0.15) !important;
  transform: scale(1.02) !important;
}

/* Enhanced drop zone feedback */
.sortable-drop-zone {
  min-height: 8px;
  background: v-bind('getDroplineColor()');
  border-radius: 0 !important; /* No rounded corners */
  margin: 4px 0;
  opacity: 0.7;
}

/* New region button */
.new-region-button-container {
  margin-top: 1rem;
  text-align: center;
}

.add-region-btn {
  opacity: 0.7;
}

.add-region-btn:hover {
  opacity: 1;
}

/* SIMPLIFIED SPACING SOLUTION - Works with existing flat structure */

/* Consistent spacing between regions - achieved via region headers */
.region-header-slim {
  margin-top: 1.0rem !important; /* Consistent 1.0rem spacing above each region */
  margin-bottom: 0 !important; /* No space below headers */
}

/* First region has no top margin */
.region-header-slim:first-child {
  margin-top: 0 !important;
}

/* Collapsed regions get consistent spacing regardless of type */
.region-header-slim.region-collapsed {
  margin-top: 1.0rem !important; /* Same spacing for all collapsed regions */
  height: auto !important; /* Override any height restrictions */
  padding: 0.3rem 1rem !important; /* Consistent small padding for collapsed regions */
}

/* Ensure consistent spacing for all region types when not collapsed */
.region-header-slim.break-region:not(.region-collapsed) {
  margin-top: 1.0rem !important; /* Same as other regions when expanded */
  height: auto !important; /* Override any height restrictions */
  padding: 0.5rem 1rem !important; /* Normal padding when expanded */
}

/* All rundown items have zero margins */
.rundown-item-wrapper {
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  padding: 0 !important;
}

/* Break region items - no separators between items */
.rundown-item-wrapper.break-region-item .rundown-item-card {
  border-bottom: none !important;
}

/* Non-break region items - thin separators */
.rundown-item-wrapper:not(.break-region-item) .rundown-item-card {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
}

/* Remove separator on last item */
.rundown-item-wrapper:last-child .rundown-item-card {
  border-bottom: none !important;
}

/* Multi-selection styles using designated selection color */
.multi-selected-item {
  border: 2px solid v-bind('getSelectionColor()') !important;
  background-color: color-mix(in srgb, v-bind('getSelectionColor()') 15%, transparent) !important;
  position: relative;
}

.multi-selected-item::before {
  content: '✓';
  position: absolute;
  top: 4px;
  right: 4px;
  color: v-bind('getSelectionColor()');
  font-weight: bold;
  font-size: 12px;
  z-index: 10;
}

.multi-selected-region {
  border: 2px solid v-bind('getSelectionColor()') !important;
  background-color: color-mix(in srgb, v-bind('getSelectionColor()') 15%, transparent) !important;
  position: relative;
}

.multi-selected-region::before {
  content: '✓';
  position: absolute;
  top: 4px;
  right: 4px;
  color: v-bind('getSelectionColor()');
  font-weight: bold;
  font-size: 12px;
  z-index: 10;
}

/* Override selected item styling when in multi-select mode */
.multi-selected-item.selected-item {
  border: 2px solid v-bind('getSelectionColor()') !important;
  background-color: v-bind('getSelectionColor()') !important;
  color: v-bind('getSelectionTextColor()') !important;
}
</style>
