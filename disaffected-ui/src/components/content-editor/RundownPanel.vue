<template>
  <div
    :class="['rundown-panel', panelWidth === 'narrow' ? 'narrow' : 'wide']"
    :style="{ ...rundownPanelCssVars, width: panelWidthValue, height: panelHeightValue }"
  >
    <!-- Tab-shaped control buttons on right edge -->
    <div class="tab-controls-right">
      <v-btn
        icon
        size="small"
        @click="$emit('toggle-width')"
        class="tab-btn"
      >
        <v-icon>{{ panelWidth === 'narrow' ? 'mdi-arrow-expand-horizontal' : 'mdi-arrow-collapse-horizontal' }}</v-icon>
      </v-btn>
      <v-btn
        icon
        size="small"
        @click="$emit('close')"
        class="tab-btn"
      >
        <v-icon>mdi-close</v-icon>
      </v-btn>
    </div>

    <v-card class="rundown-card" flat>
      <!-- Rundown Header -->
      <v-card-title class="d-flex align-center pa-2 rundown-title">
        <span class="text-h6">Rundown</span>
        <v-spacer></v-spacer>
        <v-btn icon size="x-small" variant="text" @click="$emit('toggle-width')" :title="panelWidth === 'narrow' ? 'Expand' : 'Narrow'">
          <v-icon size="small">{{ panelWidth === 'narrow' ? 'mdi-arrow-expand-horizontal' : 'mdi-arrow-collapse-horizontal' }}</v-icon>
        </v-btn>
        <v-btn icon size="x-small" variant="text" @click="$emit('close')" title="Close">
          <v-icon size="small">mdi-close</v-icon>
        </v-btn>
        <div class="trt-box-wrapper ml-2" :title="'Total rundown duration'">
          <div class="trt-label">TRT</div>
          <div class="trt-value">{{ computedTotalDuration }}</div>
        </div>
      </v-card-title>
      
      <v-divider style="border-width: 0.5px; opacity: 0.3;"></v-divider>
      
      <!-- Rundown Toolbar - Split Layout with Fixed Options Menu -->
      <div class="rundown-toolbar-split pa-1" style="background-color: rgb(var(--v-theme-surface));">
        <!-- Main Toolbar Grid (left side) -->
        <div class="toolbar-main-grid">
          <!-- New Item Button -->
          <v-btn
            size="x-small"
            variant="outlined"
            @click="$emit('new-item')"
            class="toolbar-btn-tile toolbar-btn-success"
          >
            <v-icon size="small">mdi-plus-circle</v-icon>
            <span class="btn-text-tiny">New Item</span>
            <v-tooltip activator="parent" location="bottom">
              Add New Rundown Item (Ctrl+Shift+N)
            </v-tooltip>
          </v-btn>

          <!-- Delete Selected Button -->
          <v-btn
            size="x-small"
            variant="outlined"
            @click="handleDeleteSelected"
            :disabled="!hasSelections"
            class="toolbar-btn-tile toolbar-btn-error"
          >
            <v-icon size="small">mdi-trash-can-outline</v-icon>
            <span class="btn-text-tiny">Delete ({{ totalSelectionsCount }})</span>
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

          <!-- Join Selected Button (visible when 2+ items are Ctrl-selected) -->
          <v-btn
            v-if="selectedItemIndices.size >= 2"
            size="x-small"
            variant="outlined"
            @click="joinFromMultiSelect"
            class="toolbar-btn-tile toolbar-btn-join"
          >
            <v-icon size="small">mdi-set-merge</v-icon>
            <span class="btn-text-tiny">Join ({{ selectedItemIndices.size }})</span>
            <v-tooltip activator="parent" location="bottom">
              Join {{ selectedItemIndices.size }} selected items into one segment
            </v-tooltip>
          </v-btn>

          <!-- View Regions Toggle Button -->
          <v-btn
            size="x-small"
            variant="outlined"
            @click="toggleRegionsVisibility"
            :class="['toolbar-btn-tile', showRegions ? 'toolbar-btn-info' : 'toolbar-btn-grey']"
          >
            <v-icon size="small">{{ showRegions ? 'mdi-view-grid' : 'mdi-view-list' }}</v-icon>
            <span class="btn-text-tiny">Regions</span>
            <v-tooltip activator="parent" location="bottom">
              {{ showRegions ? 'Hide Regions (Alt+Shift+R)' : 'Show Regions (Alt+Shift+R)' }}
            </v-tooltip>
          </v-btn>

          <!-- Options Menu -->
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                size="x-small"
                variant="outlined"
                v-bind="props"
                class="toolbar-btn-tile toolbar-btn-warning"
              >
                <v-icon size="small">mdi-cog-outline</v-icon>
                <span class="btn-text-tiny">Options</span>
                <v-tooltip activator="parent" location="bottom">Rundown Options</v-tooltip>
              </v-btn>
            </template>
            <v-list density="compact">
              <v-list-item @click="$emit('refresh-rundown')">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-refresh</v-icon>
                </template>
                <v-list-item-title>Refresh Rundown</v-list-item-title>
                <v-list-item-subtitle>Reload from database</v-list-item-subtitle>
              </v-list-item>
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
              <v-list-item @click="$emit('recalculate-durations')">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-timer-refresh-outline</v-icon>
                </template>
                <v-list-item-title>Recalculate Durations</v-list-item-title>
                <v-list-item-subtitle>Recalculate all item durations from content</v-list-item-subtitle>
              </v-list-item>
              <v-list-item @click="$emit('show-script-compare-modal')">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-compare-horizontal</v-icon>
                </template>
                <v-list-item-title>Compare Script</v-list-item-title>
                <v-list-item-subtitle>Diff against exported Google Doc</v-list-item-subtitle>
              </v-list-item>
              <v-list-item @click="$emit('initiate-join')">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-set-merge</v-icon>
                </template>
                <v-list-item-title>Join Segments</v-list-item-title>
                <v-list-item-subtitle>Merge 2+ items into one (Ctrl+Shift+J)</v-list-item-subtitle>
              </v-list-item>
              <v-divider></v-divider>
              <v-list-item @click="openEpisodeRollbackModal">
                <template v-slot:prepend>
                  <v-icon size="small">mdi-backup-restore</v-icon>
                </template>
                <v-list-item-title>Episode Rollback</v-list-item-title>
                <v-list-item-subtitle>Restore entire episode from snapshot</v-list-item-subtitle>
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
            @end="handleRegionDragEndWrapper"
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
                    @end="handleItemDragEndWrapper"
                    @change="handleItemChangeWrapper"
                  >
                    <template #item="{ element: item }">
                      <div class="rundown-item-wrapper">
                      <!-- Join placement gap indicator (before each item) -->
                      <div
                        v-if="joinPlacementMode"
                        class="join-placement-gap"
                        :class="{ 'join-placement-gap-hover': joinHoverGapIndex === getItemGlobalIndex(item) }"
                        @mouseenter="joinHoverGapIndex = getItemGlobalIndex(item)"
                        @mouseleave="joinHoverGapIndex = -1"
                        @click.stop="$emit('join-place', getItemGlobalIndex(item))"
                      >
                        <div class="join-gap-line"></div>
                        <div class="join-gap-label" v-if="joinHoverGapIndex === getItemGlobalIndex(item)">
                          <v-icon size="x-small" color="deep-purple-lighten-2">mdi-arrow-right-bold</v-icon>
                          Drop here
                        </div>
                      </div>
                      <v-card
                        flat
                        :class="[
                          'rundown-item-card',
                          { 'selected-item': getItemGlobalIndex(item) === selectedItemIndex && !joinSelectMode },
                          { 'multi-selected-item': selectedItemIndices.has(getItemGlobalIndex(item)) },
                          { 'join-selected-item': joinSelectMode && joinSelectedIds.has(item.asset_id || item.id) },
                          { 'editing-item': getItemGlobalIndex(item) === editingItemIndex },
                          { 'placeholder-item': item.isPlaceholder },
                          { 'region-item-selected': isItemRegionSelected(item) },
                          { 'generating-item': getItemGlobalIndex(item) === generatingItemIndex },
                          { 'needs-attention-item': itemHasNeedsAttention(item) },
                          llmState ? llmState.getVisualClass('item', item.id) : ''
                        ]"
                        :style="Object.assign({},
                          {
                            backgroundColor: (joinSelectMode && joinSelectedIds.has(item.asset_id || item.id))
                              ? 'rgba(103, 58, 183, 0.35)'
                              : (itemHasNeedsAttention(item) ? needsAttentionColor : (getItemGlobalIndex(item) === selectedItemIndex ? getSelectionColor() : getBackgroundColorForItem(item?.type || 'unknown'))),
                            color: (joinSelectMode && joinSelectedIds.has(item.asset_id || item.id))
                              ? '#E1BEE7'
                              : (itemHasNeedsAttention(item) ? '#FFFFFF' : (getItemGlobalIndex(item) === selectedItemIndex ? getSelectionTextColor() : getTextColorForItem(item?.type || 'unknown')))
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
                            <div class="type-label">
                              {{ (item?.type || 'UNKNOWN').toUpperCase().substring(0, 3) }}
                              <v-icon
                                v-if="item?.is_library_item || item?.source === 'library'"
                                size="x-small"
                                color="amber"
                                class="library-badge"
                                title="Library Content"
                              >mdi-library</v-icon>
                            </div>

                            <!-- Slug + presence avatars (other users on this segment) -->
                            <div class="slug-column">
                              <div :class="['slug-text', { 'blink-attention': itemHasNeedsAttention(item) }]">{{ itemHasNeedsAttention(item) ? `**${truncateSlug(item?.slug || '', panelWidth)}**` : truncateSlug(item?.slug || '', panelWidth) }}</div>
                              <!-- Content character count — paragraphs + FSQ quotes + SOT transcripts only. -->
                              <div class="content-char-count" :title="`${getContentCharCount(item)} content characters`">{{ getContentCharCount(item) }}</div>
                              <div v-if="panelWidth === 'narrow' && getItemGlobalIndex(item) === selectedItemIndex" class="word-count-display">
                                WC: {{ getWordCount(item) }}
                              </div>
                            </div>
                            <div v-if="presentUsersFor(item).length > 0" class="presence-stack">
                              <v-avatar
                                v-for="u in presentUsersFor(item)"
                                :key="u.id"
                                :color="u.chip_color || 'primary'"
                                size="18"
                                class="presence-avatar"
                                :title="`${u.display_name || u.username} is here`"
                              >
                                <v-img v-if="u.profile_picture" :src="u.profile_picture" />
                                <span v-else class="presence-initials">{{ avatarInitials(u) }}</span>
                              </v-avatar>
                            </div>

                            <!-- Duration (Right side) -->
                            <div class="duration-display">
                              {{ formatDurationShort(getEffectiveItemDuration(item)) }}
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
                                    {{ item?.is_library_item || item?.source === 'library' ? 'Remove from Rundown' : 'Delete Item' }}
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
                            <span
                              v-if="getItemGlobalIndex(item) === selectedItemIndex"
                              class="history-link-row"
                            >
                              <span v-if="historyStats[item.id]" class="history-stats">
                                <span>{{ historyStats[item.id].count }} revisions</span>
                                <span>oldest: {{ historyStats[item.id].oldest }}</span>
                                <span>largest: {{ historyStats[item.id].largest }}</span>
                              </span>
                              <a
                                href="#"
                                class="history-link"
                                @click.stop.prevent="openRollbackModal(item)"
                              >[view revisions]</a>
                            </span>
                          </div>
                        </v-card>
                      </div>
                    </template>
                  </draggable>
                </div>
              </div>
            </template>
          </draggable>

          <!-- Last placement gap (after all items) -->
          <div
            v-if="joinPlacementMode && items && items.length > 0"
            class="join-placement-gap join-placement-gap-last"
            :class="{ 'join-placement-gap-hover': joinHoverGapIndex === items.length }"
            @mouseenter="joinHoverGapIndex = items.length"
            @mouseleave="joinHoverGapIndex = -1"
            @click.stop="$emit('join-place', items.length)"
          >
            <div class="join-gap-line"></div>
            <div class="join-gap-label" v-if="joinHoverGapIndex === items.length">
              <v-icon size="x-small" color="deep-purple-lighten-2">mdi-arrow-right-bold</v-icon>
              Drop here
            </div>
          </div>

        </div>

        <!-- Join Select Mode Action Bar -->
        <div v-if="joinSelectMode" class="join-select-bar">
          <span class="join-select-count">
            <v-icon size="small" class="mr-1">mdi-set-merge</v-icon>
            {{ joinSelectedIds.size }} item{{ joinSelectedIds.size !== 1 ? 's' : '' }} selected
          </span>
          <v-spacer />
          <v-btn size="small" variant="text" @click="cancelJoinSelect" class="mr-1">Cancel</v-btn>
          <v-btn
            size="small"
            color="deep-purple"
            variant="elevated"
            :disabled="joinSelectedIds.size < 2"
            @click="confirmJoinSelect"
          >Continue</v-btn>
        </div>

        <!-- Join Placement Mode Info Bar -->
        <div v-if="joinPlacementMode" class="join-placement-bar">
          <v-icon size="small" class="mr-1" color="deep-purple-lighten-2">mdi-cursor-move</v-icon>
          <span>Click a gap to place the merged segment</span>
          <v-spacer />
          <v-btn size="small" variant="text" @click="$emit('cancel-join')">Cancel</v-btn>
        </div>

        <!-- Empty state -->
        <div v-if="!items || items.length === 0" class="text-center py-8">
          <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-playlist-remove</v-icon>
          <p class="text-h6 text-grey-lighten-1">No rundown items found</p>
          <p class="text-caption text-grey">Switch to Rundown Manager to add items</p>
        </div>
        </div> <!-- End list-view -->

        <!-- Master Duration Footer -->
        <div v-if="items && items.length > 0" class="master-duration-footer-wrapper">
          <div class="trt-box-wrapper">
            <div class="trt-label">TRT</div>
            <div class="trt-value">{{ computedTotalDuration }}</div>
          </div>
          <div class="master-duration-items-count-bottom">
            {{ items.length }} {{ items.length === 1 ? 'item' : 'items' }}
          </div>
        </div>

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

    <!-- Revision History Modal -->
    <v-dialog v-model="rollbackDialog" max-width="800" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-history</v-icon>
          Revision History: {{ rollbackItem?.slug || rollbackItem?.title || 'Segment' }}
          <v-spacer />
          <v-btn icon size="small" @click="rollbackDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text style="max-height: 500px; overflow-y: auto;">
          <div class="d-flex align-center ga-1 mb-3 flex-wrap">
            <span class="text-caption text-grey mr-1">Show only:</span>
            <v-btn-toggle v-model="historyFilter" density="compact" variant="outlined" divided color="primary">
              <v-btn value="all" size="x-small">All</v-btn>
              <v-btn value="auto" size="x-small">Autosaves</v-btn>
              <v-btn value="manual" size="x-small">Manual</v-btn>
              <v-btn value="30m" size="x-small">30 min</v-btn>
              <v-btn value="60m" size="x-small">60 min</v-btn>
              <v-btn value="1d" size="x-small">1 day</v-btn>
            </v-btn-toggle>
          </div>
          <div v-if="rollbackLoading" class="text-center pa-8">
            <v-progress-circular indeterminate color="primary" />
            <p class="mt-2">Loading revisions...</p>
          </div>
          <div v-else-if="filteredRollbackSnapshots.length === 0" class="text-center pa-8 text-grey">
            No revisions match the current filter.
          </div>
          <v-table v-else dense class="history-table">
            <thead>
              <tr>
                <th>Ago</th>
                <th>Date / Time</th>
                <th>Source</th>
                <th>Chars</th>
                <th>Size</th>
                <th>Preview</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(snap, idx) in filteredRollbackSnapshots"
                :key="snap.filename + snap.restore_type"
                :class="{ 'history-row-even': idx % 2 === 0, 'history-row-odd': idx % 2 !== 0 }"
              >
                <td class="text-no-wrap history-cell">{{ formatTimeAgo(snap.modified) }}</td>
                <td class="text-no-wrap history-cell history-date">{{ formatSnapshotDate(snap.modified) }}</td>
                <td class="history-cell">
                  <v-chip
                    :color="snap.source === 'manual' ? 'blue' : 'grey'"
                    size="x-small"
                    label
                  >{{ snap.source }}</v-chip>
                </td>
                <td class="history-cell">{{ snap.content_length || '—' }}</td>
                <td class="history-cell">{{ snap.size_bytes ? (snap.size_bytes / 1024).toFixed(1) + ' KB' : '—' }}</td>
                <td class="text-truncate history-cell" style="max-width: 200px;">{{ snap.preview || '' }}</td>
                <td class="text-no-wrap history-cell">
                  <v-btn
                    size="x-small"
                    variant="text"
                    color="primary"
                    @click="previewSnapshot(snap)"
                  >preview</v-btn>
                  <v-btn
                    size="x-small"
                    variant="text"
                    color="warning"
                    @click="restoreSnapshot(snap)"
                    :loading="restoringSnapshot === snap.filename"
                  >restore</v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Episode Rollback Modal -->
    <v-dialog v-model="episodeRollbackDialog" max-width="850" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-backup-restore</v-icon>
          Episode Rollback: {{ episode }}
          <v-spacer />
          <v-btn icon size="small" @click="episodeRollbackDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text style="max-height: 500px; overflow-y: auto;">
          <v-alert type="warning" variant="tonal" class="mb-4" density="compact">
            Episode rollback restores <strong>all segments</strong> and their order to the state at the snapshot time.
          </v-alert>
          <div v-if="episodeRollbackLoading" class="text-center pa-8">
            <v-progress-circular indeterminate color="primary" />
            <p class="mt-2">Loading episode snapshots...</p>
          </div>
          <div v-else-if="episodeRollbackSnapshots.length === 0" class="text-center pa-8 text-grey">
            No episode snapshots found.
          </div>
          <v-table v-else dense>
            <thead>
              <tr>
                <th>Date / Time</th>
                <th>Items</th>
                <th>Total Size</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="snap in episodeRollbackSnapshots" :key="snap.filename">
                <td class="text-no-wrap">{{ formatSnapshotDate(snap.modified) }}</td>
                <td>{{ snap.item_count || '—' }}</td>
                <td>{{ (snap.size_bytes / 1024).toFixed(1) }} KB</td>
                <td class="text-no-wrap">
                  <v-btn
                    size="x-small"
                    variant="text"
                    color="primary"
                    @click="previewEpisodeSnapshot(snap)"
                  >preview</v-btn>
                  <v-btn
                    size="x-small"
                    variant="text"
                    color="warning"
                    @click="restoreEpisodeSnapshot(snap)"
                    :loading="restoringEpisode === snap.filename"
                  >restore</v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Episode Snapshot Preview Modal -->
    <v-dialog v-model="episodePreviewDialog" max-width="750" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-eye</v-icon>
          Episode Snapshot Preview
          <v-spacer />
          <v-btn icon size="small" @click="episodePreviewDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text style="max-height: 500px; overflow-y: auto;">
          <div v-for="(item, idx) in episodePreviewItems" :key="idx" class="mb-4">
            <h4 class="text-subtitle-2">[{{ item.order }}] {{ item.title }}</h4>
            <p class="text-caption text-grey mb-1">{{ item.type }} | {{ (item.script_content || '').length }} chars</p>
            <div v-html="item.script_content" class="snapshot-preview-content" style="border-left: 2px solid #555; padding-left: 12px;" />
            <v-divider class="mt-3" />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="warning"
            @click="restoreEpisodeSnapshot(episodePreviewSnap)"
            :loading="restoringEpisode === episodePreviewSnap?.filename"
          >
            <v-icon left>mdi-restore</v-icon>
            Restore Entire Episode
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snapshot Preview Modal -->
    <v-dialog v-model="previewDialog" max-width="700" scrollable>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-eye</v-icon>
          Snapshot Preview
          <v-spacer />
          <v-btn icon size="small" @click="previewDialog = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text style="max-height: 500px; overflow-y: auto;">
          <div v-html="previewContent" class="snapshot-preview-content" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            color="warning"
            @click="restoreSnapshot(previewSnap)"
            :loading="restoringSnapshot === previewSnap?.filename"
          >
            <v-icon left>mdi-restore</v-icon>
            Restore This Version
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { themeColorMap, getColorValue, resolveVuetifyColor, getTextColorForBackground, loadColorsFromDatabase } from '@/utils/themeColorMap'
import { useRegions } from '@/composables/useRegions'
import { useUserPrefs } from '@/composables/useUserPrefs'
import { useMessages } from '@/composables/useMessages'
import { watch } from 'vue'
import { useRundownDragDrop } from '@/composables/useRundownDragDrop'
import draggable from 'vuedraggable' // eslint-disable-line no-unused-vars

const emit = defineEmits([
  'close',
  'toggle-width',
  'save',
  'new-item',
  'delete-selected',
  'sync-order',
  'export',
  'refresh',
  'refresh-rundown',
  'restore-revision',
  'toggle-options',
  'select-item',
  'edit-item',
  'reorder-items',
  'create-region',
  'delete-region',
  'rundown-cleared',
  'select-region',
  'recalculate-durations',
  'show-script-compare-modal',
  'initiate-join',
  'join-items-selected',
  'cancel-join',
  'join-place',
  'delete-item',
  'move-region-to-unassigned',
  'item-assetid-updated',
  'assetid-regenerated',
])

const props = defineProps({
  panelWidth: {
    type: String,
    default: 'wide',
    validator: (value) => ['narrow', 'wide'].includes(value)
  },
  panelHeight: {
    type: Number,
    default: null
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
  },
  joinSelectMode: {
    type: Boolean,
    default: false
  },
  joinPlacementMode: {
    type: Boolean,
    default: false
  },
  joinMergedItem: {
    type: Object,
    default: null
  },
  episode: {
    type: [String, Number],
    default: null
  }
})

// --- Composables ---
const { groupItemsIntoRegions, getRegionColor } = useRegions()
const {
  isDragging, // eslint-disable-line no-unused-vars
  isDraggingRegion, // eslint-disable-line no-unused-vars
  draggedRegionType, // eslint-disable-line no-unused-vars
  draggedRegionId, // eslint-disable-line no-unused-vars
  hoveredRegionId, // eslint-disable-line no-unused-vars
  determineRegionType,
  handleRegionDragStart,
  handleRegionDragEnd,
  handleItemDragStart,
  handleItemDragEnd,
  allowMove,
  handleItemChange
} = useRundownDragDrop()

// --- For $forceUpdate replacement ---
const forceUpdateKey = ref(0) // eslint-disable-line no-unused-vars

// --- Reactive state (data) ---
const showNewRegionModal = ref(false)
const selectedRegionType = ref(null) // eslint-disable-line no-unused-vars
const newRegionName = ref('') // eslint-disable-line no-unused-vars
const showDeleteRegionDialog = ref(false)
const regionToDelete = ref(null)
const selectedRegionId = ref(null)
const flashMessage = ref('')
const showFlashMessage = ref(false)

// Multi-selection support
const selectedItemIndices = ref(new Set())
const selectedRegionIds = ref(new Set())
const isMultiSelectMode = ref(false)

// Deletion confirmation modal
const showDeleteConfirmModal = ref(false)
const deletionInProgress = ref(false)
const pendingDeletion = ref(null)

// Clear entire rundown modal
const showClearRundownModal = ref(false)
const clearRundownInProgress = ref(false)

// Region visibility toggle — initial value reads the user's preference
// (or true by default). Subsequent changes auto-persist to /api/user/prefs
// so the user's last choice sticks across sessions and devices.
const _userPrefs = useUserPrefs()
const showRegions = ref(_userPrefs.get('rundown.showRegions', true))

// ──────────────────────────────────────────────────────────────────
// Public presence — show avatars on rundown items other users are
// currently editing. Source of truth: /api/users (polled in App.vue).
// ──────────────────────────────────────────────────────────────────
const _messagesApi = useMessages()

function _currentMe() {
  try {
    const me = JSON.parse(localStorage.getItem('user-data') || '{}')
    return { id: me?.id ?? null, username: me?.username ?? null }
  } catch { return { id: null, username: null } }
}

function presentUsersFor(item) {
  if (!item) return []
  const itemId = item.asset_id || item.id
  if (!itemId) return []
  const { id: myId, username: myUsername } = _currentMe()
  return (_messagesApi.users.value || []).filter(u =>
    (myId == null || String(u.id) !== String(myId))
    && (myUsername == null || u.username !== myUsername)
    && u.online
    && u.current_location?.segment_id != null
    && String(u.current_location.segment_id) === String(itemId)
  )
}

function avatarInitials(u) {
  const name = u.display_name || u.username || ''
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return (parts[0]?.slice(0, 2) || '??').toUpperCase()
}

watch(showRegions, (v) => {
  _userPrefs.set('rundown.showRegions', !!v)
})

// If the prefs cache hydrates after this ref initialized (e.g. a fresh
// login mid-session), pick up the stored value.
watch(() => _userPrefs.cache.value['rundown.showRegions'], (v) => {
  if (typeof v === 'boolean' && v !== showRegions.value) showRegions.value = v
})

// Color reactivity trigger
const colorLoadTrigger = ref(0)

// Rollback modal (segment)
const rollbackDialog = ref(false)
const rollbackItem = ref(null)
const rollbackSnapshots = ref([])
const rollbackLoading = ref(false)
const restoringSnapshot = ref(null)
const previewDialog = ref(false)
const previewContent = ref('')
const previewSnap = ref(null)
// History stats per item (keyed by item id)
const historyStats = ref({})
const historyFilter = ref('all')

// Rollback modal (episode)
const episodeRollbackDialog = ref(false)
const episodeRollbackSnapshots = ref([])
const episodeRollbackLoading = ref(false)
const restoringEpisode = ref(null)
const episodePreviewDialog = ref(false)
const episodePreviewItems = ref([])
const episodePreviewSnap = ref(null)

// Join mode state
const joinSelectedIds = ref(new Set())
const joinHoverGapIndex = ref(-1)

// --- Computed ---
const filteredRollbackSnapshots = computed(() => {
  const f = historyFilter.value
  if (!f || f === 'all') return rollbackSnapshots.value

  // Source filters
  if (f === 'auto') return rollbackSnapshots.value.filter(s => s.source === 'auto')
  if (f === 'manual') return rollbackSnapshots.value.filter(s => s.source === 'manual')

  // Time-bucket filters: show one revision per bucket, pick largest by bytes
  let bucketMs
  if (f === '30m') bucketMs = 30 * 60 * 1000
  else if (f === '60m') bucketMs = 60 * 60 * 1000
  else if (f === '1d') bucketMs = 24 * 60 * 60 * 1000
  else return rollbackSnapshots.value

  const buckets = {}
  for (const snap of rollbackSnapshots.value) {
    const ts = new Date(snap.modified).getTime()
    const key = Math.floor(ts / bucketMs)
    const sz = snap.size_bytes || snap.content_length || 0
    if (!buckets[key] || sz > (buckets[key].size_bytes || buckets[key].content_length || 0)) {
      buckets[key] = snap
    }
  }
  return Object.values(buckets).sort((a, b) => new Date(b.modified) - new Date(a.modified))
})

const totalDurationSeconds = computed(() => {
  if (!props.items || props.items.length === 0) return 0
  let totalSeconds = 0
  props.items.forEach(item => {
    if (item.duration) {
      totalSeconds += parseDurationToSeconds(item.duration)
    }
  })
  return totalSeconds
})

const computedTotalDuration = computed(() => {
  const ts = totalDurationSeconds.value
  const h = Math.floor(ts / 3600)
  const m = Math.floor((ts % 3600) / 60)
  const s = ts % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
})

const durationThemeClass = computed(() => { // eslint-disable-line no-unused-vars
  const secs = totalDurationSeconds.value
  if (secs >= 3600) return 'duration-over'       // >= 1:00:00 red
  if (secs >= 3300) return 'duration-target'      // >= 0:55:00 green
  return 'duration-under'                          // < 0:50:00 blue
})

const panelWidthValue = computed(() => {
  return props.panelWidth === 'narrow' ? '300px' : '442px'
})

const panelHeightValue = computed(() => {
  return props.panelHeight ? `${props.panelHeight}px` : '100vh'
})

// Get needs-attention color from settings for flagged items
const needsAttentionColor = computed(() => {
  // Reference colorLoadTrigger to ensure re-computation when colors are loaded
  // eslint-disable-next-line no-unused-vars
  const _trigger = colorLoadTrigger.value
  const colorName = getColorValue('needs-attention') || 'orange-lighten-3'
  return resolveVuetifyColor(colorName) || '#FFCC80'
})

// Get needs-attention border color (solid) for rundown items
const needsAttentionBorderColor = computed(() => { // eslint-disable-line no-unused-vars
  return needsAttentionColor.value
})

// CSS variables for dynamic theming of needs-attention items
const rundownPanelCssVars = computed(() => {
  const hexColor = needsAttentionColor.value
  const r = parseInt(hexColor.slice(1, 3), 16)
  const g = parseInt(hexColor.slice(3, 5), 16)
  const b = parseInt(hexColor.slice(5, 7), 16)
  return {
    '--needs-attention-border': needsAttentionBorderColor.value,
    '--needs-attention-bg-light': `rgba(${r}, ${g}, ${b}, 0.15)`
  }
})

const safeItems = computed(() => {
  return props.items || []
})

const localItems = computed({ // eslint-disable-line no-unused-vars
  get() {
    return safeItems.value
  },
  set(/* newValue */) {
    // This will be called when vue.draggable reorders items
    // We don't need to do anything here as the parent manages the data
  }
})

const regions = computed(() => {
  return groupItemsIntoRegions(safeItems.value)
})

// Convert hierarchical regions back to flat array for parent compatibility
const flatItemsFromRegions = computed(() => {
  if (!regions.value) return []

  const flatItems = []
  regions.value.forEach(region => {
    region.items.forEach(item => {
      // Remove regionId when flattening to avoid circular references
      // eslint-disable-next-line no-unused-vars
      const { regionId, ...cleanItem } = item
      flatItems.push(cleanItem)
    })
  })
  return flatItems
})

// Create a flat array of items with region headers interspersed
const itemsWithHeaders = computed(() => { // eslint-disable-line no-unused-vars
  if (!regions.value.length) return []

  const result = []
  let blockCounter = 0
  let breakCounter = 0

  regions.value.forEach((region, regionIndex) => {
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
    const regionColor = getRegionColor(region.type)
    console.log(`[DEBUG] Region ${region.type} color:`, regionColor)
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
        regionColor: getRegionColor(region.type)
      })
    })

    // Add new region button after the last region
    if (regionIndex === regions.value.length - 1) {
      result.push({
        isNewRegionButton: true,
        id: 'new-region-button'
      })
    }
  })

  return result
})

// Available region types for the modal
const availableRegionTypes = computed(() => {
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
})

// Get the region ID that contains the currently selected item
const selectedItemRegionId = computed(() => {
  if (props.selectedItemIndex === -1 || !safeItems.value[props.selectedItemIndex]) {
    return null
  }
  const selectedItem = safeItems.value[props.selectedItemIndex]
  return getRegionIdForItem(selectedItem)
})

// Multi-selection computed properties
const hasMultipleSelections = computed(() => {
  return selectedItemIndices.value.size > 0 || selectedRegionIds.value.size > 0
})

const hasSelections = computed(() => {
  return hasMultipleSelections.value || props.selectedItemIndex !== -1 || selectedRegionId.value !== null
})

const totalSelectionsCount = computed(() => {
  const multiCount = selectedItemIndices.value.size + selectedRegionIds.value.size
  // When no multi-selections but a single item or region is selected, count it
  if (multiCount === 0 && props.selectedItemIndex !== -1) return 1
  if (multiCount === 0 && selectedRegionId.value) return 1
  return multiCount
})

const selectionSummary = computed(() => {
  const items = selectedItemIndices.value.size
  const regionsCount = selectedRegionIds.value.size

  if (items === 0 && regionsCount === 0) return 'None'
  if (items === 0) return `${regionsCount} region${regionsCount === 1 ? '' : 's'}`
  if (regionsCount === 0) return `${items} item${items === 1 ? '' : 's'}`
  return `${items} item${items === 1 ? '' : 's'} & ${regionsCount} region${regionsCount === 1 ? '' : 's'}`
})

const deletionSummary = computed(() => {
  if (!pendingDeletion.value) {
    return { title: '', details: [], count: 0 }
  }

  const { regions: delRegions = [], items: delItems = [] } = pendingDeletion.value
  const details = []
  let count = 0

  // Add regions to deletion summary
  delRegions.forEach(region => {
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
  delItems.forEach(item => {
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
  const regionCount = delRegions.length
  const itemCount = delItems.length

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
})

// Check if all break regions are collapsed
const allBreaksCollapsed = computed(() => {
  const breakRegions = regions.value.filter(region => region.type === 'break')
  if (breakRegions.length === 0) return false
  return breakRegions.every(region => region.isCollapsed === true)
})

// --- Methods ---

// Check if an item's script content contains any needs-attention flagged segments
function itemHasNeedsAttention(item) {
  // API returns script_content as 'script' field in rundown list response
  const scriptContent = item?.script || item?.script_content
  if (!item || !scriptContent) {
    return false
  }
  // Check for paragraph flags (data-needs-attention="true")
  const hasParagraphFlag = scriptContent.includes('data-needs-attention="true"')
  // Check for cue flags (NeedsAttention: true or NeedsAttention:true)
  const hasCueFlag = /NeedsAttention:\s*true/i.test(scriptContent)
  const result = hasParagraphFlag || hasCueFlag
  return result
}

// Get effective duration for an item (item.duration is authoritative after recalculation)
function getEffectiveItemDuration(item) {
  let totalSeconds = parseDurationToSeconds(item?.duration)
  if (totalSeconds === 0) return '0:00'
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

// Parse any duration string (HH:MM:SS:FF, HH:MM:SS, MM:SS) to seconds
function parseDurationToSeconds(duration) {
  if (!duration) return 0
  const parts = String(duration).split(':').map(Number)
  if (parts.length === 4) {
    return (parts[0] || 0) * 3600 + (parts[1] || 0) * 60 + (parts[2] || 0)
  } else if (parts.length === 3) {
    return (parts[0] || 0) * 3600 + (parts[1] || 0) * 60 + (parts[2] || 0)
  } else if (parts.length === 2) {
    return (parts[0] || 0) * 60 + (parts[1] || 0)
  }
  return 0
}

// Region visibility toggle
function toggleRegionsVisibility() {
  showRegions.value = !showRegions.value
  console.log(`Regions ${showRegions.value ? 'shown' : 'hidden'}`)
}

// Handle refresh with flash message
function handleRefresh() { // eslint-disable-line no-unused-vars
  // Show flash message
  flashMessage.value = 'Refreshing'
  showFlashMessage.value = true

  // Emit refresh event
  emit('refresh')

  // Hide flash message after 2 seconds
  setTimeout(() => {
    showFlashMessage.value = false
  }, 2000)
}

// NEW: Methods for hierarchical structure (future use)
function calculateRegionDuration(region) {
  if (!region.items || region.items.length === 0) {
    return region.estimatedDuration || '00:00:00'
  }

  let totalSeconds = 0
  region.items.forEach(item => {
    totalSeconds += parseDurationToSeconds(item.duration)
  })

  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

function shouldCollapseRegion(region) {
  // All regions (including break regions) follow their isCollapsed state
  // Break regions stay expanded once opened until explicitly collapsed
  return region.isCollapsed
}

function toggleAllBreaksExpansion() {
  // Find all break regions
  const breakRegions = regions.value.filter(region => region.type === 'break')
  if (breakRegions.length === 0) return

  // Determine target state - if all are collapsed, expand them; otherwise collapse all
  const shouldExpand = allBreaksCollapsed.value

  // Toggle all break regions to the target state
  breakRegions.forEach(region => {
    region.isCollapsed = !shouldExpand
  })

  console.log(`${shouldExpand ? 'Expanded' : 'Collapsed'} ${breakRegions.length} break regions`)
}

function toggleRegionCollapse(region) {
  // Toggle the collapse state of a specific region
  const newState = !region.isCollapsed
  region.isCollapsed = newState

  console.log(`${newState ? 'Collapsed' : 'Expanded'} region: ${region.name}`)
}

function getItemGlobalIndex(item) {
  // Find the global index of an item across all regions
  let globalIndex = 0
  for (const region of regions.value) {
    const itemIndex = region.items.findIndex(i => i.id === item.id)
    if (itemIndex !== -1) {
      return globalIndex + itemIndex
    }
    globalIndex += region.items.length
  }
  return -1
}

// Check if an item's parent region is selected
function isItemRegionSelected(item) {
  if (!selectedRegionId.value || !item) return false

  // Find which region this item belongs to
  for (const region of regions.value) {
    const itemIndex = region.items.findIndex(i => i.id === item.id)
    if (itemIndex !== -1) {
      return region.id === selectedRegionId.value
    }
  }
  return false
}

function getTextColorForItem(type) {
  const colorMapping = themeColorMap[type] || themeColorMap.unknown
  // The themeColorMap now calculates text color dynamically based on contrast
  return colorMapping.textColor || '#ffffff'
}

function getBackgroundColorForItem(type) {
  const colorValue = getColorValue(type.toLowerCase()) || 'grey'
  const resolvedColor = resolveVuetifyColor(colorValue)
  return resolvedColor
}

function getSelectionColor() {
  const selectionValue = getColorValue('Selection-interface') || 'orange'
  const resolvedColor = resolveVuetifyColor(selectionValue)
  console.log('🎨 Selection Color Debug:', {
    raw: selectionValue,
    resolved: resolvedColor,
    key: 'Selection-interface'
  })
  return resolvedColor
}

function getSelectionTextColor() {
  // Use the theme system's contrast logic for selection background
  const colorMapping = themeColorMap['Selection-interface'] || themeColorMap.unknown
  return colorMapping.textColor || '#000000'
}

function formatDuration(duration) { // eslint-disable-line no-unused-vars
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
}

function formatDurationShort(duration) {
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
}

function truncateSlug(slug, pWidth) {
  // Truncate slug to 17 characters or nearest word boundary not exceeding 20 chars
  if (!slug) return ''

  const lowerSlug = slug.toLowerCase()

  // In expanded mode, apply truncation logic
  if (pWidth === 'wide' && lowerSlug.length > 20) {
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
}

/**
 * Count the characters of *content* in an item — only the things a human
 * actually types. Used as a quick visual to spot truncation/data-loss in
 * a row at a glance (Kevin requested 2026-05-09 after several silent
 * truncation events). NOT a word count, NOT a save-size — just the raw
 * meaningful content.
 *
 * Counts:
 *   - text inside <p>...</p> paragraphs
 *   - text inside FSQ cue [Quote: ...]
 *   - text inside SOT cue [Transcription: ...]
 *
 * Excludes:
 *   - YAML frontmatter
 *   - HTML tags (just their text content is kept)
 *   - cue block plumbing other than the two fields above
 *   - whitespace-only lines
 */
function getContentCharCount(item) {
  // API returns script_content as 'script' in the rundown list response.
  const raw = item?.script || item?.script_content
  if (!raw) return 0
  let total = 0

  // Strip YAML frontmatter so it doesn't leak into the paragraph match.
  const body = raw.replace(/^---[\s\S]*?---\n?/m, '')

  // 1) Paragraph bodies — <p ...>text</p>
  const pRegex = /<p\b[^>]*>([\s\S]*?)<\/p>/gi
  let m
  while ((m = pRegex.exec(body)) !== null) {
    const inner = m[1].replace(/<[^>]*>/g, '').replace(/&nbsp;/gi, ' ')
    total += inner.trim().length
  }

  // 2) FSQ Quote and SOT Transcription fields inside cue blocks. The values
  //    can span newlines until the next [Field:] or <!-- End Cue -->.
  // Cue blocks: <!-- Begin Cue --> ... <!-- End Cue -->
  const cueRegex = /<!--\s*Begin Cue\s*-->([\s\S]*?)<!--\s*End Cue\s*-->/gi
  let cueMatch
  while ((cueMatch = cueRegex.exec(body)) !== null) {
    const block = cueMatch[1]
    // Match [Quote:  ...] or [Transcription: ...] up to the next [Field:] or end.
    const fieldRegex = /\[(Quote|Transcription)\s*:\s*([\s\S]*?)\](?=\s*(?:\[[A-Za-z][\w ]*\s*:|<!--\s*End Cue\s*-->))/gi
    let fm
    while ((fm = fieldRegex.exec(block)) !== null) {
      total += fm[2].trim().length
    }
  }

  return total
}

function getWordCount(item) {
  // Calculate word count from script_content, excluding code blocks but counting FSQ quotes.
  // API returns script_content as 'script' in the rundown list response.
  let content = item?.script || item?.script_content
  if (!content) return 0

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
}

// Dropline color methods for ghost item styling
function getDroplineColor() { // eslint-disable-line no-unused-vars
  const droplineValue = getColorValue('dropline') || 'green-lighten-4'
  return resolveVuetifyColor(droplineValue)
}

function getDroplineBackground() { // eslint-disable-line no-unused-vars
  const droplineValue = getColorValue('dropline') || 'green-lighten-4'
  const baseColor = resolveVuetifyColor(droplineValue)
  // Convert to rgba with low opacity for background
  const rgb = baseColor.match(/\w\w/g)?.map(hex => parseInt(hex, 16))
  return rgb ? `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.2)` : 'rgba(200, 230, 201, 0.2)'
}

function getDroplineTextColor() { // eslint-disable-line no-unused-vars
  const droplineValue = getColorValue('dropline') || 'green-lighten-4'
  const baseColor = resolveVuetifyColor(droplineValue)
  // Use slightly more opaque version for text
  const rgb = baseColor.match(/\w\w/g)?.map(hex => parseInt(hex, 16))
  return rgb ? `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.8)` : 'rgba(200, 230, 201, 0.8)'
}

// Helper method to get the original index of an item in the safeItems array (0-based)
function getItemIndex(item) {
  return safeItems.value.findIndex(i => i.id === item.id)
}

// Get a light background color for region items
function getRegionBackgroundColor(regionColor) { // eslint-disable-line no-unused-vars
  const resolvedColor = resolveVuetifyColor(regionColor)
  // Convert hex to RGB and apply low opacity
  const rgb = resolvedColor.match(/\w\w/g)?.map(hex => parseInt(hex, 16))
  return rgb ? `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, 0.08)` : 'rgba(0, 0, 0, 0.05)'
}

// Get a darker variant of the region color for headers
function getRegionHeaderColor(regionColor) {
  console.log(`[DEBUG] getRegionHeaderColor input:`, regionColor)

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

  const resolvedColor = resolveVuetifyColor(darkerColor)
  console.log(`[DEBUG] getRegionHeaderColor output: ${darkerColor} -> ${resolvedColor}`)
  return resolvedColor
}

// Region handler methods
function handleEditRegion(regionHeader) {
  console.log('Edit region:', regionHeader.regionName)
  // TODO: Implement region editing
}

function handleDuplicateRegion(regionHeader) { // eslint-disable-line no-unused-vars
  console.log('Duplicate region:', regionHeader.regionName)
  // TODO: Implement region duplication
}

function handleDeleteRegion(element) {
  // Find the region that this element belongs to
  const region = getRegionForItem(element)
  if (!region) {
    console.error('Could not find region for element:', element)
    return
  }

  console.log('Delete region:', region)

  // Store the region data for the confirmation dialog
  regionToDelete.value = {
    region: region,
    element: element,
    regionName: getRegionHeaderName(element),
    itemCount: region.items.length
  }

  // Show confirmation dialog
  showDeleteRegionDialog.value = true
}

function confirmDeleteRegion() {
  if (!regionToDelete.value) return

  const { region, regionName, itemCount, isSelectedRegionDeletion } = regionToDelete.value

  if (isSelectedRegionDeletion) {
    console.log(`Moving items from region "${regionName}" to unassigned region`)

    // Emit event to parent to handle moving items to unassigned region
    emit('move-region-to-unassigned', {
      regionId: region.id,
      regionType: region.type,
      regionName: regionName,
      items: region.items,
      itemIds: region.items.map(item => item.id)
    })
  } else {
    console.log(`Deleting region "${regionName}" with ${itemCount} items`)

    // Emit event to parent to handle the actual deletion
    emit('delete-region', {
      regionId: region.id,
      regionType: region.type,
      regionName: regionName,
      items: region.items,
      itemIds: region.items.map(item => item.id)
    })
  }

  // Close dialog and reset
  cancelDeleteRegion()
}

function cancelDeleteRegion() {
  showDeleteRegionDialog.value = false
  regionToDelete.value = null
}

// Calculate total duration for a region
function getRegionTotalDuration(regionId) { // eslint-disable-line no-unused-vars
  // Find the region from our grouped data
  const region = regions.value.find(r => r.id === regionId)
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
}

// New Region Modal Methods
function getRegionNamePlaceholder(regionType) {
  const existingRegions = regions.value.filter(r => r.type === regionType)
  const nextNumber = existingRegions.length + 1

  if (regionType === 'block') {
    return `Block ${String.fromCharCode(64 + nextNumber)}` // A, B, C...
  } else if (regionType === 'break') {
    return `Break ${nextNumber}`
  }
  return `${regionType} ${nextNumber}`
}

function closeNewRegionModal() {
  showNewRegionModal.value = false
  selectedRegionType.value = null
  newRegionName.value = ''
}


function createRegionOfType(regionType) {
  // Generate default name for the region type
  const regionName = getRegionNamePlaceholder(regionType)

  // Emit an event to parent to handle region creation
  emit('create-region', {
    type: regionType,
    name: regionName
  })

  console.log(`Creating new ${regionType} region: ${regionName}`)

  closeNewRegionModal()
}

// Helper method to determine if an item should be collapsed
function shouldCollapseItem(element) { // eslint-disable-line no-unused-vars
  // If collapse setting is disabled, never collapse
  if (!props.collapseBreakRegions) return false

  // Don't collapse if no element
  if (!element) return false

  // Check if this element is in a break region by region type OR region name
  const regionType = element.regionType || determineRegionType(element)

  // Get region info to check name as well
  const region = getRegionForItem(element)
  const isBreakRegion = (regionType === 'break') ||
                       (region && region.type === 'break') ||
                       (region && region.name && region.name.toLowerCase().includes('break'))

  // Only collapse break regions
  if (!isBreakRegion) return false

  // Don't collapse if this specific region is explicitly selected (clicked on region header)
  const rId = getRegionIdForItem(element)
  const shouldCollapse = selectedRegionId.value !== rId

  // Debug logging for break region expansion issues
  if (isBreakRegion) {
    console.log(`Break region collapse check - Element: ${element.slug}, RegionId: ${rId}, SelectedRegionId: ${selectedRegionId.value}, ShouldCollapse: ${shouldCollapse}`)
  }

  // ALWAYS collapse break regions by default, even if an individual item is selected
  // The region will only expand if the user explicitly clicks the region header
  return shouldCollapse
}

// Helper methods for draggable template
function shouldShowRegionHeader(element) {
  if (!element || !safeItems.value) return false

  const currentIndex = safeItems.value.findIndex(item => item.id === element.id)
  if (currentIndex === 0) return true // Always show header for first item

  const previousItem = safeItems.value[currentIndex - 1]
  if (!previousItem) return true

  // Show header if region type changes
  const currentRegionType = element.regionType || determineRegionType(element)
  const previousRegionType = previousItem.regionType || determineRegionType(previousItem)

  return currentRegionType !== previousRegionType
}

function getRegionHeaderName(element) {
  const regionType = element.regionType || determineRegionType(element)

  // Count how many regions of this type exist before this item
  let counter = 1
  const currentIndex = safeItems.value.findIndex(item => item.id === element.id)

  for (let i = 0; i < currentIndex; i++) {
    const itemRegionType = safeItems.value[i].regionType || determineRegionType(safeItems.value[i])
    if (itemRegionType === regionType) {
      // Check if this is a region boundary (first item of its type in sequence)
      const prevIndex = i - 1
      if (prevIndex < 0) {
        counter++
      } else {
        const prevRegionType = safeItems.value[prevIndex].regionType || determineRegionType(safeItems.value[prevIndex])
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
}

function getRegionDurationForItem(element) { // eslint-disable-line no-unused-vars
  const regionType = element.regionType || determineRegionType(element)

  // Find all items of the same region type that are consecutive
  const currentIndex = safeItems.value.findIndex(item => item.id === element.id)
  let regionItems = [element]

  // Find consecutive items of the same region type
  for (let i = currentIndex + 1; i < safeItems.value.length; i++) {
    const itemRegionType = safeItems.value[i].regionType || determineRegionType(safeItems.value[i])
    if (itemRegionType === regionType) {
      regionItems.push(safeItems.value[i])
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
}

function isLastItem(element) { // eslint-disable-line no-unused-vars
  if (!safeItems.value || safeItems.value.length === 0) return false
  const lastItem = safeItems.value[safeItems.value.length - 1]
  return lastItem && lastItem.id === element.id
}

// Region lookup helpers (used by selection/display methods)
function getRegionIdForItem(element) {
  const regs = regions.value
  for (const region of regs) {
    if (region.items.some(item => item.id === element.id)) {
      return region.id
    }
  }
  return null
}

function getRegionForItem(element) {
  const regs = regions.value
  return regs.find(region =>
    region.items.some(item => item.id === element.id)
  )
}

// Check if this element shows a region header for a selected region
function isSelectedRegionStart(element) { // eslint-disable-line no-unused-vars
  return shouldShowRegionHeader(element) &&
         selectedRegionId.value === getRegionIdForItem(element)
}

// Check if this is the last item in a selected region
function isSelectedRegionEnd(element) { // eslint-disable-line no-unused-vars
  if (selectedRegionId.value !== getRegionIdForItem(element)) {
    return false
  }

  const currentIndex = safeItems.value.findIndex(item => item.id === element.id)
  const nextIndex = currentIndex + 1

  // It's the last item if there's no next item, or the next item is in a different region
  if (nextIndex >= safeItems.value.length) {
    return true
  }

  const nextElement = safeItems.value[nextIndex]
  const nextRegionId = getRegionIdForItem(nextElement)

  return nextRegionId !== selectedRegionId.value
}

// Check if this element shows a region header for the region containing selected item
function isSelectedItemRegionStart(element) { // eslint-disable-line no-unused-vars
  return shouldShowRegionHeader(element) &&
         selectedItemRegionId.value === getRegionIdForItem(element)
}

// Check if this is the last item in the region containing selected item
function isSelectedItemRegionEnd(element) { // eslint-disable-line no-unused-vars
  if (selectedItemRegionId.value !== getRegionIdForItem(element)) {
    return false
  }

  const currentIndex = safeItems.value.findIndex(item => item.id === element.id)
  const nextIndex = currentIndex + 1

  // It's the last item if there's no next item, or the next item is in a different region
  if (nextIndex >= safeItems.value.length) {
    return true
  }

  const nextElement = safeItems.value[nextIndex]
  const nextRegionId = getRegionIdForItem(nextElement)

  return nextRegionId !== selectedItemRegionId.value
}


function handleItemDelete(element) {
  const itemIndex = getItemIndex(element)
  const item = safeItems.value[itemIndex]

  // Emit event to parent to handle the actual deletion
  emit('delete-item', {
    itemIndex: itemIndex,
    item: item,
    itemId: item.id,
    slug: item.slug || item.title || 'Unnamed Item'
  })

  console.log('Item delete requested:', item)
}

function handleItemDoubleClick(element) {
  const itemIndex = getItemIndex(element)
  const item = safeItems.value[itemIndex]

  showFlashMessage.value = false // Hide any existing message
  flashMessage.value = `Double-clicked rundown item: "${item?.slug || item?.title || 'Unnamed Item'}" (Index: ${itemIndex})`
  showFlashMessage.value = true

  // Auto-hide flash message after 3 seconds
  setTimeout(() => {
    showFlashMessage.value = false
  }, 3000)

  console.log('Item double-clicked:', item)
}

function handleRegionDoubleClick(element) {
  const regionName = getRegionHeaderName(element)
  const rId = getRegionIdForItem(element)

  showFlashMessage.value = false // Hide any existing message
  flashMessage.value = `Double-clicked region: "${regionName}" (ID: ${rId})`
  showFlashMessage.value = true

  // Auto-hide flash message after 3 seconds
  setTimeout(() => {
    showFlashMessage.value = false
  }, 3000)

  console.log('Region double-clicked:', regionName, rId)
}

function handleSelectedRegionDelete(element) { // eslint-disable-line no-unused-vars
  // Use the same logic as the existing region deletion but with different messaging
  const region = getRegionForItem(element)
  if (!region) {
    console.error('Could not find region for element:', element)
    return
  }

  console.log('Delete selected region:', region)

  // Store the region data for the confirmation dialog
  regionToDelete.value = {
    region: region,
    element: element,
    regionName: getRegionHeaderName(element),
    itemCount: region.items.length,
    isSelectedRegionDeletion: true // Flag to indicate this is from the selected region delete button
  }

  // Show confirmation dialog
  showDeleteRegionDialog.value = true
}

// Drag handlers — delegate to useRundownDragDrop composable
// handleRegionDragStart is provided directly by composable (no ctx needed)
// handleRegionDragEnd, handleItemDragEnd, handleItemChange need a ctx object
function handleRegionDragEndWrapper(evt) {
  handleRegionDragEnd(evt, {
    regions: regions.value,
    flatItemsFromRegions: flatItemsFromRegions.value,
    emit: emit
  })
}
// handleItemDragStart is provided directly by composable (no ctx needed)
function handleItemDragEndWrapper(evt) {
  handleItemDragEnd(evt, {
    regions: regions.value,
    flatItemsFromRegions: flatItemsFromRegions.value,
    emit: emit
  })
}
// allowMove is provided directly by composable (no ctx needed)
function handleItemChangeWrapper(evt) {
  handleItemChange(evt, {
    regions: regions.value,
    flatItemsFromRegions: flatItemsFromRegions.value,
    emit: emit
  })
}

// Update region selection for hierarchical structure
function handleRegionSelect(region, event) {
  const isCtrlClick = event && (event.ctrlKey || event.metaKey)

  if (isCtrlClick) {
    // Multi-selection mode with Ctrl+click
    isMultiSelectMode.value = true

    if (selectedRegionIds.value.has(region.id)) {
      // Remove from multi-selection if already selected
      selectedRegionIds.value.delete(region.id)
    } else {
      // Add to multi-selection
      selectedRegionIds.value.add(region.id)
    }
  } else {
    // Normal single selection mode
    if (isMultiSelectMode.value) {
      // Clear all multi-selections first
      selectedRegionIds.value.clear()
      selectedItemIndices.value.clear()
      isMultiSelectMode.value = false
    }

    // Clear item selection when selecting a region
    emit('select-item', -1)

    // Toggle selection: if already selected, deselect; otherwise select
    if (selectedRegionId.value === region.id) {
      selectedRegionId.value = null
      emit('select-region', null) // Emit deselection
      // For break regions, toggle collapsed state when clicking on selected region
      if (region.type === 'break') {
        region.isCollapsed = !region.isCollapsed
      }
    } else {
      selectedRegionId.value = region.id
      emit('select-region', region) // Emit selection with region data
      // For break regions, expand when selected
      if (region.type === 'break') {
        region.isCollapsed = false
      }
    }
  }

  console.log('Region selected:', region.id, 'Ctrl+click:', isCtrlClick, 'Multi-selections:', selectedRegionIds.value.size)
}

// Update item selection for hierarchical structure
function handleItemSelect(item, event) {
  // Join placement mode — clicking a gap places the item, clicking an item does nothing
  if (props.joinPlacementMode) {
    return
  }

  const itemIndex = getItemGlobalIndex(item)

  // Join select mode — every click toggles selection (no Ctrl required)
  if (props.joinSelectMode) {
    const itemId = item.asset_id || item.id
    if (joinSelectedIds.value.has(itemId)) {
      joinSelectedIds.value.delete(itemId)
    } else {
      joinSelectedIds.value.add(itemId)
    }
    // Force reactivity
    joinSelectedIds.value = new Set(joinSelectedIds.value)
    return
  }

  const isCtrlClick = event && (event.ctrlKey || event.metaKey)

  if (isCtrlClick) {
    // Multi-selection mode with Ctrl+click
    isMultiSelectMode.value = true

    if (selectedItemIndices.value.has(itemIndex)) {
      // Remove from multi-selection if already selected
      selectedItemIndices.value.delete(itemIndex)
    } else {
      // Add to multi-selection
      selectedItemIndices.value.add(itemIndex)
    }
  } else {
    // Normal single selection mode
    if (isMultiSelectMode.value) {
      // Clear all multi-selections first
      selectedRegionIds.value.clear()
      selectedItemIndices.value.clear()
      isMultiSelectMode.value = false
    }

    // Clear region selection when selecting an item
    selectedRegionId.value = null

    // Toggle selection: if already selected, deselect; otherwise select
    if (props.selectedItemIndex === itemIndex) {
      emit('select-item', -1) // Deselect by passing -1
    } else {
      emit('select-item', itemIndex) // Select the item
    }
  }

  console.log('Item selected:', item.slug, 'index:', itemIndex, 'Ctrl+click:', isCtrlClick, 'Multi-selections:', selectedItemIndices.value.size)

  // Lazy-load history stats for selected item
  if (!isCtrlClick && item && item.id && !historyStats.value[item.id]) {
    fetchHistoryStats(item)
  }
}

async function fetchHistoryStats(item) {
  if (!props.episode || !item?.id) return
  try {
    const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
    const headers = { 'Authorization': `Bearer ${token}` }
    let totalCount = 0
    let oldestDate = null
    let largestSize = 0

    // Fetch filesystem snapshots (endpoint expects numeric item_id)
    const numericId = Number(item.id)
    const fsRes = !isNaN(numericId) ? await fetch(`/api/episodes/${props.episode}/history/segments/${numericId}`, { headers }) : null
    if (fsRes && fsRes.ok) {
      const fsData = await fsRes.json()
      const snaps = fsData.snapshots || []
      totalCount += snaps.length
      for (const s of snaps) {
        if (s.modified && (!oldestDate || new Date(s.modified) < new Date(oldestDate))) oldestDate = s.modified
        if (s.size_bytes > largestSize) largestSize = s.size_bytes
      }
    }

    // Fetch DB versions
    const assetId = item.asset_id || item.AssetID
    if (assetId) {
      const dbRes = await fetch(`/api/episodes/rundown-item/${assetId}/versions`, { headers })
      if (dbRes.ok) {
        const dbData = await dbRes.json()
        const vers = dbData.versions || []
        totalCount += vers.length
        for (const v of vers) {
          if (v.created_at && (!oldestDate || new Date(v.created_at) < new Date(oldestDate))) oldestDate = v.created_at
          const sz = v.content_length || 0
          if (sz > largestSize) largestSize = sz
        }
      }
    }

    let oldestStr = '—'
    if (oldestDate) {
      const days = Math.floor((Date.now() - new Date(oldestDate).getTime()) / (24 * 60 * 60 * 1000))
      oldestStr = days === 0 ? 'today' : days === 1 ? '1 day ago' : `${days} days ago`
    }
    const largestStr = largestSize > 1024 ? (largestSize / 1024).toFixed(0) + 'kb' : largestSize + 'b'
    historyStats.value[item.id] = { count: totalCount, oldest: oldestStr, largest: largestStr }
  } catch {
    // Silent fail — stats are non-critical
  }
}

// Create new region button handler
function createNewRegion() {
  console.log('Create new region clicked')
  showNewRegionModal.value = true
}

// Enhanced delete selected functionality - now uses modal
function handleDeleteSelected() {
  try {
    if (isMultiSelectMode.value && hasMultipleSelections.value) {
      // Multi-selection deletion
      const delRegions = []
      const delItems = []

      // Collect region objects
      for (const rId of selectedRegionIds.value) {
        const region = regions.value.find(r => r.id === rId)
        if (region) delRegions.push(region)
      }

      // Collect item objects
      for (const itemIndex of selectedItemIndices.value) {
        const item = getItemByGlobalIndex(itemIndex)
        if (item) delItems.push(item)
      }

      showDeletionModal({ type: 'multi', regions: delRegions, items: delItems })

    } else if (selectedRegionId.value) {
      // Single region deletion
      const region = regions.value.find(r => r.id === selectedRegionId.value)
      if (region) {
        showDeletionModal({ type: 'region', regions: [region], items: [] })
      }
    } else if (props.selectedItemIndex !== -1) {
      // Single item deletion
      const item = getItemByGlobalIndex(props.selectedItemIndex)
      if (item) {
        showDeletionModal({ type: 'item', regions: [], items: [item] })
      }
    }
  } catch (error) {
    console.error('Error preparing deletion:', error)
  }
}

// Show deletion confirmation modal
function showDeletionModal(deletionData) {
  pendingDeletion.value = deletionData
  showDeleteConfirmModal.value = true
}

// Cancel deletion
function cancelDeletion() {
  showDeleteConfirmModal.value = false
  pendingDeletion.value = null
  deletionInProgress.value = false
}

// Confirm and execute deletion
async function confirmDeletion() {
  if (!pendingDeletion.value) return

  deletionInProgress.value = true

  try {
    const { regions: delRegions, items: delItems } = pendingDeletion.value

    // Delete all selected regions first
    for (const region of delRegions) {
      const regionName = region.name || region.type || `Region ${region.id}`
      console.log('Deleting region:', regionName)
      emit('delete-region', region)
    }

    // Delete all selected items
    for (const item of delItems) {
      console.log('Deleting item:', item.slug || item.title || item.id)
      emit('delete-item', item)
    }

    // Clear all selections
    selectedRegionIds.value.clear()
    selectedItemIndices.value.clear()
    isMultiSelectMode.value = false
    selectedRegionId.value = null
    emit('select-item', -1)

    // Close modal
    cancelDeletion()

  } catch (error) {
    console.error('Error executing deletion:', error)
    deletionInProgress.value = false
  }
}

// Keyboard event handler
function handleKeydown(event) {
  // Ctrl+Shift+R - Refresh/Reload rundown data
  if (event.ctrlKey && event.shiftKey && event.key === 'R') {
    event.preventDefault()
    event.stopPropagation()
    emit('refresh')
    return
  }

  // Alt+Shift+R - Toggle regions visibility
  if (event.altKey && event.shiftKey && event.key === 'R') {
    event.preventDefault()
    event.stopPropagation()
    toggleRegionsVisibility()
    return
  }

  // Esc cancels multi-select / region selections, but never closes the
  // currently open segment in the editor.
  if (event.key === 'Escape') {
    if (isMultiSelectMode.value || hasMultipleSelections.value || selectedRegionId.value !== null) {
      console.log('🚫 Esc pressed: Cancelling multi-select / region selections')
      cancelMultiAndRegionSelections()
      event.preventDefault()
      event.stopPropagation()
      event.stopImmediatePropagation()
      return false
    }

    // No multi-select state to clear — swallow ESC so it doesn't trigger any
    // default browser/route behavior, but leave the open segment alone.
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
    showClearRundownConfirmation()
  }
}

// Show clear rundown confirmation modal
function showClearRundownConfirmation() {
  console.log('Clear rundown shortcut triggered')
  showClearRundownModal.value = true
}

// Cancel clear rundown
function cancelClearRundown() {
  showClearRundownModal.value = false
}

// Execute clear entire rundown
async function confirmClearRundown() {
  clearRundownInProgress.value = true

  try {
    console.log('🚨 Clearing entire rundown for episode:', props.episode)

    // Debug authentication tokens
    const authToken = localStorage.getItem('auth-token') || localStorage.getItem('token')
    const apiKey = localStorage.getItem('api_key')
    console.log('🔐 Auth token:', authToken ? `${authToken.substring(0, 20)}...` : 'NONE')
    console.log('🔑 API key:', apiKey ? `${apiKey.substring(0, 20)}...` : 'NONE')

    const apiUrl = `/api/episodes/${props.episode}/rundown/clear`
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
    selectedItemIndices.value.clear()
    selectedRegionIds.value.clear()
    isMultiSelectMode.value = false

    // Emit event to parent to reload rundown
    emit('rundown-cleared')

    // Close modal
    showClearRundownModal.value = false

  } catch (error) {
    console.error('Error clearing rundown:', error)
    alert('Failed to clear rundown. Please try again.')
  } finally {
    clearRundownInProgress.value = false
  }
}

// Helper method to get item by global index
function getItemByGlobalIndex(globalIndex) {
  let currentIndex = 0
  for (const region of regions.value) {
    for (const item of region.items) {
      if (currentIndex === globalIndex) {
        return item
      }
      currentIndex++
    }
  }
  return null
}

// Helper method to get region by ID
function getRegionById(regionId) {
  return regions.value.find(region => region.id === regionId)
}

// Request new AssetID for a rundown item
async function requestNewItemAssetID(item) {
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
    flashMessage.value = `AssetID regenerated: ${result.old_asset_id} → ${result.new_asset_id}`
    showFlashMessage.value = true

    // Emit event to parent to save the updated item
    emit('item-assetid-updated', {
      item: item,
      oldAssetId: result.old_asset_id,
      newAssetId: result.new_asset_id
    })

    // Force reactive update of the rundown display (replaces this.$forceUpdate())
    forceUpdateKey.value++

    // Emit global refresh event
    emit('assetid-regenerated', {
      entityType: 'segment',
      oldAssetId: result.old_asset_id,
      newAssetId: result.new_asset_id,
      affectedItem: item
    })

  } catch (error) {
    console.error('❌ Failed to regenerate AssetID:', error)
    flashMessage.value = `Failed to regenerate AssetID: ${error.message}`
    showFlashMessage.value = true
  }
}

// Cancel all selections and exit multi-select mode
function cancelMultiAndRegionSelections() {
  // Clear multi-item + region selections only. Do NOT emit select-item -1:
  // the currently open segment in the editor must remain open.
  selectedItemIndices.value.clear()
  selectedRegionIds.value.clear()
  isMultiSelectMode.value = false
  selectedRegionId.value = null

  console.log('✅ Multi-select / region selections cancelled (open segment preserved)')
}

// Rollback methods
async function openRollbackModal(item) {
  rollbackItem.value = item
  rollbackDialog.value = true
  rollbackLoading.value = true
  rollbackSnapshots.value = []

  const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
  const headers = { 'Authorization': `Bearer ${token}` }
  const combined = []

  try {
    // 1. Load filesystem snapshots (autosave)
    const fsRes = await fetch(`/api/episodes/${props.episode}/history/segments/${item.id}`, { headers })
    if (fsRes.ok) {
      const fsData = await fsRes.json()
      for (const snap of fsData.snapshots) {
        try {
          const detailRes = await fetch(`/api/episodes/${props.episode}/history/segments/${item.id}/${snap.filename}`, { headers })
          if (detailRes.ok) {
            const detail = await detailRes.json()
            const rawContent = detail.content || ''
            const textOnly = rawContent.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
            snap.preview = textOnly.substring(0, 80) + (textOnly.length > 80 ? '...' : '')
            snap.content_length = detail.frontmatter?.content_length || rawContent.length
            snap.full_content = rawContent
          }
        } catch {
          snap.preview = ''
        }
        snap.source = 'auto'
        snap.restore_type = 'file'
        combined.push(snap)
      }
    }

    // 2. Load DB version history (manual saves)
    const assetId = item.asset_id || item.AssetID
    if (assetId) {
      const dbRes = await fetch(`/api/episodes/rundown-item/${assetId}/versions`, { headers })
      if (dbRes.ok) {
        const dbData = await dbRes.json()
        for (const ver of (dbData.versions || [])) {
          combined.push({
            filename: `v${ver.version_number}`,
            modified: ver.created_at,
            size_bytes: (ver.content_length || 0),
            content_length: ver.content_length,
            preview: '',
            source: ver.change_type === 'autosave' ? 'auto' : 'manual',
            restore_type: 'db',
            version_number: ver.version_number,
            asset_id: assetId,
            full_content: null // loaded on preview
          })
        }
      }
    }

    // Sort all entries by date, newest first
    combined.sort((a, b) => new Date(b.modified) - new Date(a.modified))
    rollbackSnapshots.value = combined
  } catch (e) {
    console.error('Failed to load history:', e)
  } finally {
    rollbackLoading.value = false
  }
}

function formatSnapshotDate(isoString) {
  if (!isoString) return '—'
  const d = new Date(isoString)
  return d.toLocaleString(undefined, {
    month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  })
}

function formatTimeAgo(isoString) {
  if (!isoString) return '—'
  const now = Date.now()
  const then = new Date(isoString).getTime()
  const diffSec = Math.floor((now - then) / 1000)
  if (diffSec < 60) return `${diffSec}s`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h`
  const diffDays = Math.floor(diffHr / 24)
  return `${diffDays}d`
}

function stripFrontmatter(text) {
  if (!text) return text
  // Strip YAML frontmatter (---\n...\n---)
  const match = text.match(/^---\s*\n[\s\S]*?\n---\s*\n?/)
  return match ? text.slice(match[0].length).trim() : text
}

function markdownToHtml(md) {
  if (!md) return ''
  let html = md
  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>')
  // Bold and italic
  html = html.replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>')
  // Blockquotes
  html = html.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
  // Horizontal rules
  html = html.replace(/^---$/gm, '<hr>')
  html = html.replace(/^\*\*\*$/gm, '<hr>')
  // Unordered lists
  html = html.replace(/^[-*] (.+)$/gm, '<li>$1</li>')
  // Ordered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
  // Paragraphs - wrap lines not already in tags
  html = html.split('\n\n').map(block => {
    block = block.trim()
    if (!block) return ''
    if (block.startsWith('<')) return block
    return '<p>' + block.replace(/\n/g, '<br>') + '</p>'
  }).join('\n')
  return html
}

function renderPreviewContent(rawContent) {
  if (!rawContent) return '<p style="color:#999">No content</p>'
  // Strip frontmatter first
  let content = stripFrontmatter(rawContent)
  // Check if content is primarily HTML (has block-level tags)
  if (/<(?:p|div|h[1-6]|ul|ol|blockquote|table|br)\b/i.test(content)) {
    return content
  }
  // Otherwise convert markdown to HTML
  return markdownToHtml(content)
}

async function previewSnapshot(snap) {
  if (snap.restore_type === 'db' && !snap.full_content) {
    // Lazy-load DB version content
    try {
      const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
      const res = await fetch(`/api/episodes/rundown-item/${snap.asset_id}/versions/${snap.version_number}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        snap.full_content = data.script_content || ''
        snap.content_length = data.content_length || snap.full_content.length
        const textOnly = snap.full_content.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
        snap.preview = textOnly.substring(0, 80) + (textOnly.length > 80 ? '...' : '')
      }
    } catch (e) {
      console.error('Failed to load version content:', e)
    }
  }
  previewSnap.value = snap
  previewContent.value = renderPreviewContent(snap.full_content || snap.preview || '')
  previewDialog.value = true
}

async function restoreSnapshot(snap) {
  if (!snap) return

  restoringSnapshot.value = snap.filename
  try {
    const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
    let response

    if (snap.restore_type === 'db') {
      // Restore from DB version history
      response = await fetch(`/api/episodes/rundown-item/${snap.asset_id}/versions/${snap.version_number}/restore`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
    } else {
      // Restore from filesystem snapshot
      response = await fetch(`/api/episodes/${props.episode}/history/segments/restore/${snap.filename}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
    }

    if (response.ok) {
      rollbackDialog.value = false
      previewDialog.value = false
      emit('refresh-rundown')
      flashMessage.value = `Segment restored from ${snap.source} ${snap.restore_type === 'db' ? 'version' : 'snapshot'}`
      showFlashMessage.value = true
    } else {
      const err = await response.text()
      alert(`Restore failed: ${err}`)
    }
  } catch (e) {
    alert(`Restore failed: ${e.message}`)
  } finally {
    restoringSnapshot.value = null
  }
}

// Episode-level rollback methods
function joinFromMultiSelect() {
  // Gather item objects from the multi-selected indices
  const selectedItems = []
  for (const idx of selectedItemIndices.value) {
    if (props.items[idx]) {
      selectedItems.push(props.items[idx])
    }
  }
  if (selectedItems.length < 2) return

  // Clear multi-select state
  selectedItemIndices.value.clear()
  isMultiSelectMode.value = false

  // Emit to parent — this skips the join-select phase and goes straight to snapshot + config
  emit('join-items-selected', selectedItems)
}

function cancelJoinSelect() {
  joinSelectedIds.value = new Set()
  emit('cancel-join')
}

function confirmJoinSelect() {
  // Gather the actual item objects for the selected IDs
  const selectedItems = props.items.filter(item => {
    const itemId = item.asset_id || item.id
    return joinSelectedIds.value.has(itemId)
  })
  emit('join-items-selected', selectedItems)
}

function resetJoinState() {
  joinSelectedIds.value = new Set()
  joinHoverGapIndex.value = -1
}

async function openEpisodeRollbackModal() {
  episodeRollbackDialog.value = true
  episodeRollbackLoading.value = true
  episodeRollbackSnapshots.value = []

  try {
    const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
    const response = await fetch(`/api/episodes/${props.episode}/history/episode`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (response.ok) {
      const data = await response.json()
      // Enrich with item count from detail
      const enriched = []
      for (const snap of data.snapshots) {
        try {
          const detailRes = await fetch(`/api/episodes/${props.episode}/history/episode/${snap.filename}`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          if (detailRes.ok) {
            const detail = await detailRes.json()
            snap.item_count = detail.frontmatter?.item_count || detail.items?.length || 0
            snap.items = detail.items || []
          }
        } catch {
          snap.item_count = 0
        }
        enriched.push(snap)
      }
      episodeRollbackSnapshots.value = enriched
    }
  } catch (e) {
    console.error('Failed to load episode snapshots:', e)
  } finally {
    episodeRollbackLoading.value = false
  }
}

function previewEpisodeSnapshot(snap) {
  episodePreviewSnap.value = snap
  episodePreviewItems.value = snap.items || []
  episodePreviewDialog.value = true
}

async function restoreEpisodeSnapshot(snap) {
  if (!snap || !snap.filename) return

  restoringEpisode.value = snap.filename
  try {
    const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
    const response = await fetch(`/api/episodes/${props.episode}/history/episode/restore/${snap.filename}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (response.ok) {
      const result = await response.json()
      episodeRollbackDialog.value = false
      episodePreviewDialog.value = false
      emit('refresh-rundown')
      flashMessage.value = `Episode restored: ${result.items_restored} items`
      showFlashMessage.value = true
    } else {
      const err = await response.text()
      alert(`Episode restore failed: ${err}`)
    }
  } catch (e) {
    alert(`Episode restore failed: ${e.message}`)
  } finally {
    restoringEpisode.value = null
  }
}

// --- Lifecycle ---
onMounted(async () => {
  // Load color configuration from database
  try {
    await loadColorsFromDatabase('default')
    console.log('Colors loaded successfully in RundownPanel')
    // Increment trigger to force re-computation of color-dependent computed properties
    colorLoadTrigger.value++
  } catch (error) {
    console.warn('Failed to load colors in RundownPanel, using defaults:', error)
  }

  // Add keyboard listener for clear rundown shortcut - use capture phase for higher priority
  document.addEventListener('keydown', handleKeydown, true)
})

onBeforeUnmount(() => {
  // Clean up keyboard listener
  document.removeEventListener('keydown', handleKeydown, true)
})

// --- Expose methods that parent accesses via $refs ---
defineExpose({
  resetJoinState
})
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
  /* Per-user knob: rundown row text size (Settings → Editor Display) */
  font-size: var(--editor-rundown-font-size, inherit);
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
  /* height is set dynamically via inline style from panelHeight prop */
  max-height: 100vh;
  border-right: none; /* Remove border */
  overflow-y: hidden; /* Panel itself doesn't scroll — .rundown-content does */
  overflow-x: visible; /* Allow items to extend beyond right edge */
  display: flex;
  flex-direction: column;
  flex-shrink: 0; /* Never shrink - maintain width regardless of editor content */
  z-index: 15 !important; /* Above editor panel (z-index: 10) so rows can overhang */
  align-self: flex-start; /* Required for sticky to work in flex container */
}

.rundown-card {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0; /* Allow flex shrink */
  overflow: hidden;
}

.rundown-title {
  border-bottom: none; /* Remove border */
  min-height: 56px;
  flex-shrink: 0; /* Never shrink — stays visible */
}

.rundown-toolbar {
  border-bottom: none; /* Remove border */
}

.rundown-content {
  flex: 1; /* Take up remaining space */
  overflow-y: auto; /* Internal scroll within the sticky panel */
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
  border-bottom: none;
  position: relative;
  transform: translateX(25px);
  background: rgba(0, 0, 0, 0.04);
}

/* Position duration header to align with duration values in rows */
.rundown-headers .header-duration {
  position: absolute;
  right: 50px;
  top: 50%;
  transform: translateY(-50%);
  text-align: right;
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

/* (status-indicator hidden for needs-attention items - see main needs-attention styles below) */

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
  font-size: 12px;
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

.library-badge {
  margin-left: 4px;
  opacity: 0.9;
}

.slug-column {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 100%;
  height: auto; /* Allow height to grow with content */
  overflow: visible; /* Show wrapping text */
}

/* Presence avatars: small overlapping circles to the right of the slug,
   indicating other users currently editing this segment. */
.presence-stack {
  display: inline-flex;
  align-items: center;
  margin-left: 6px;
  flex-shrink: 0;
}
.presence-stack .presence-avatar {
  margin-left: -6px;
  border: 1.5px solid #fff;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.15);
}
.presence-stack .presence-avatar:first-child {
  margin-left: 0;
}
.presence-initials {
  font-size: 9px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0;
}
.slug-text {
  font-weight: normal;
  font-size: 1.2em;
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
  font-size: 14px;
  color: inherit;
  white-space: nowrap;
  transition: right 0.3s ease;
  z-index: 5;
}

/* Duration positioning for selected items - offset by 25px to compensate for translateX(0) vs translateX(25px) */
.selected-item .duration-display {
  right: 25px;
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
  font-size: 15px;
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

/* Content-character count badge — shown under every slug, all sizes.
   Tiny, low-contrast so it doesn't compete with slug; useful for spotting
   truncation at a glance. */
.content-char-count {
  font-size: 10px;
  font-weight: 500;
  color: #000;
  margin-top: 1px;
  letter-spacing: 0.02em;
  text-decoration: none;
  text-align: left;
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
  font-size: 14px;
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
  flex-shrink: 0; /* Never shrink — stays visible above scrolling content */
}

.toolbar-main-grid {
  display: grid;
  gap: 6px;
  flex: 1;
  grid-template-columns: repeat(4, 1fr);
  align-items: stretch;
}

.toolbar-options-fixed {
  flex-shrink: 0;
  min-width: 70px;
}

.toolbar-btn-tile {
  border-radius: 0 !important;
  height: 22px !important;
  min-height: 22px !important;
  font-size: 10px !important;
  flex: 1;
  width: 100% !important;
  justify-self: stretch;
  display: flex !important;
  flex-direction: row !important;
  align-items: center;
  justify-content: center;
  padding: 2px 6px !important;
  gap: 4px;
  background-color: #ffffff !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
  border-width: 2px !important;
  transition: all 0.2s ease !important;
}

.toolbar-btn-tile:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15) !important;
}

.toolbar-btn-tile .v-icon {
  margin-bottom: 2px !important;
  margin-right: 0 !important;
}

.toolbar-btn-tile .btn-text-tiny {
  font-size: 11px !important;
  line-height: 1.1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 600;
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

/* Button color variants - white background with colored text/borders */
.toolbar-btn-success {
  border-color: #4caf50 !important;
  color: #2e7d32 !important;
}
.toolbar-btn-success:hover {
  background-color: #f1f8e9 !important;
  border-color: #2e7d32 !important;
}

.toolbar-btn-error {
  border-color: #f44336 !important;
  color: #c62828 !important;
}
.toolbar-btn-error:hover {
  background-color: #ffebee !important;
  border-color: #c62828 !important;
}
.toolbar-btn-error:disabled {
  border-color: #bdbdbd !important;
  color: #9e9e9e !important;
  background-color: #fafafa !important;
}

.toolbar-btn-info {
  border-color: #2196f3 !important;
  color: #1565c0 !important;
}
.toolbar-btn-info:hover {
  background-color: #e3f2fd !important;
  border-color: #1565c0 !important;
}

.toolbar-btn-grey {
  border-color: #9e9e9e !important;
  color: #616161 !important;
}
.toolbar-btn-grey:hover {
  background-color: #f5f5f5 !important;
  border-color: #616161 !important;
}

.toolbar-btn-warning {
  border-color: #ff9800 !important;
  color: #e65100 !important;
}
.toolbar-btn-warning:hover {
  background-color: #fff3e0 !important;
  border-color: #e65100 !important;
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
  gap: 4px;
}

.rundown-panel.narrow .toolbar-btn-tile {
  min-height: 40px !important;
  height: 40px !important;
  font-size: 10px !important;
  padding: 4px 6px !important;
  border-radius: 0 !important;
}

.rundown-panel.narrow .toolbar-btn-tile .btn-text-tiny {
  font-size: 10px !important;
  letter-spacing: 0.2px;
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

/* Needs-attention item styling - uses color from settings */
.needs-attention-item {
  border-left: none !important;
  position: relative;
  margin-left: 0 !important;
}

/* Hide the regular status-indicator for needs-attention items (only show ::before bar) */
.needs-attention-item .status-indicator {
  display: none !important;
}

/* Large attention bar on left side - 40px using needs-attention color from settings */
.needs-attention-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 40px;
  background-color: var(--needs-attention-border, #FFCC80);
  z-index: 5;
}

/* Adjust content to not overlap the large bar */
.needs-attention-item .compact-rundown-row {
  margin-left: 36px;
}

/* Blinking animation for needs-attention slug text */
.blink-attention {
  animation: blink-text 1s ease-in-out infinite;
}

@keyframes blink-text {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
}

/* Override needs-attention when item is selected — keep attention color, add selection border */
.needs-attention-item.selected-item {
  border-left: none !important;
  outline: 6px solid var(--selection-color, #1976D2) !important;
  outline-offset: -6px;
  z-index: 10;
}

/* Tab-shaped control buttons on right edge of RundownPanel */
.tab-controls-right {
  position: absolute;
  right: -32px;
  top: 50vh;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 2px;
  z-index: 1000;
}

.tab-btn {
  border-radius: 0 !important;
  background-color: rgba(25, 118, 210, 0.9) !important;
  color: white !important;
  box-shadow: 2px 2px 8px rgba(0, 0, 0, 0.3) !important;
  transition: all 0.2s ease !important;
  width: 32px !important;
  height: 40px !important;
}

.tab-btn:hover {
  background-color: rgba(25, 118, 210, 1) !important;
  transform: translateX(4px) !important;
  box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.4) !important;
}

.tab-btn .v-icon {
  color: white !important;
}

/* Master Duration - Header Badge */
.trt-box-wrapper {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
}
.trt-label {
  background: #000000;
  color: #ffffff;
  font-size: 9px;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
  letter-spacing: 1px;
  padding: 1px 8px;
  border-radius: 0;
  line-height: 1.3;
  text-align: center;
  width: 100%;
}
.trt-value {
  background: #ffffff;
  color: #000000;
  font-size: 16px;
  font-weight: 800;
  font-family: 'Roboto Mono', monospace;
  letter-spacing: 0.5px;
  padding: 2px 10px;
  border: 2px solid #000000;
  border-top: none;
  border-radius: 0;
  white-space: nowrap;
  line-height: 1.3;
}

.rundown-panel.narrow .trt-value {
  font-size: 12px;
  padding: 1px 6px;
}
.rundown-panel.narrow .trt-label {
  font-size: 7px;
  padding: 1px 6px;
}

/* Master Duration - Footer (matches TRT header style) */
.master-duration-footer-wrapper {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  padding: 6px 0 6px 10px;
  margin-top: 4px;
}

.master-duration-footer-wrapper .trt-box-wrapper {
  margin-bottom: 4px;
}

.master-duration-items-count-bottom {
  font-size: 10px;
  color: rgba(0, 0, 0, 0.5);
  font-family: 'Roboto Mono', monospace;
  margin-top: 2px;
}

.history-link-row {
  position: absolute;
  bottom: 2px;
  right: 27px;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0;
  text-align: right;
  padding: 0;
}
.history-stats {
  color: rgba(0, 0, 0, 0.7);
  font-size: 8px;
  font-family: 'Roboto Mono', monospace;
  pointer-events: none;
  user-select: none;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  line-height: 1.25;
}
.history-link {
  color: rgba(0, 0, 0, 0.85) !important;
  text-decoration: none !important;
  cursor: pointer;
  font-weight: 500;
  letter-spacing: 0.3px;
  font-size: 9px;
  font-family: 'Roboto Mono', monospace;
}
.history-link:hover {
  color: #000000 !important;
}

.history-table th {
  font-size: 11px !important;
  padding: 4px 8px !important;
  white-space: nowrap;
}
.history-cell {
  font-size: 11px !important;
  padding: 2px 8px !important;
  height: 28px !important;
  line-height: 28px !important;
}
.history-date {
  font-size: 10px !important;
  opacity: 0.8;
}
.history-row-even {
  background-color: rgba(255, 255, 255, 0.03);
}
.history-row-odd {
  background-color: rgba(255, 255, 255, 0.08);
}

.snapshot-preview-content {
  font-family: 'Georgia', 'Times New Roman', serif;
  font-size: 14px;
  line-height: 1.8;
  color: #e0e0e0;
  padding: 12px 16px;
  background: #1e1e1e;
  border-radius: 4px;
}
.snapshot-preview-content h1 {
  font-size: 1.6em;
  margin: 1em 0 0.5em;
  font-weight: 700;
  color: #fff;
  border-bottom: 1px solid #444;
  padding-bottom: 4px;
}
.snapshot-preview-content h2 {
  font-size: 1.3em;
  margin: 1em 0 0.4em;
  font-weight: 600;
  color: #fff;
}
.snapshot-preview-content h3 {
  font-size: 1.1em;
  margin: 0.8em 0 0.3em;
  font-weight: 600;
  color: #ddd;
}
.snapshot-preview-content p {
  margin-bottom: 1em;
  text-indent: 0;
}
.snapshot-preview-content ul,
.snapshot-preview-content ol {
  margin-bottom: 1em;
  padding-left: 1.8em;
}
.snapshot-preview-content li {
  margin-bottom: 0.3em;
}
.snapshot-preview-content blockquote {
  border-left: 3px solid #666;
  padding-left: 14px;
  margin: 1em 0;
  color: #aaa;
  font-style: italic;
}
.snapshot-preview-content strong,
.snapshot-preview-content b {
  font-weight: 700;
  color: #fff;
}
.snapshot-preview-content em,
.snapshot-preview-content i {
  font-style: italic;
}
.snapshot-preview-content hr {
  border: none;
  border-top: 1px solid #444;
  margin: 1.2em 0;
}
.snapshot-preview-content a {
  color: #64B5F6;
  text-decoration: underline;
}
.snapshot-preview-content pre,
.snapshot-preview-content code {
  background: #2a2a2a;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Roboto Mono', monospace;
  font-size: 0.9em;
}
.snapshot-preview-content pre {
  padding: 10px 14px;
  margin: 1em 0;
  overflow-x: auto;
}
.snapshot-preview-content table {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}
.snapshot-preview-content th,
.snapshot-preview-content td {
  border: 1px solid #444;
  padding: 6px 10px;
  text-align: left;
}
.snapshot-preview-content th {
  background: #2a2a2a;
  font-weight: 600;
}

/* ── Join Mode Styles ── */

.toolbar-btn-join {
  border-color: rgba(103, 58, 183, 0.5) !important;
  color: #CE93D8 !important;
}

.toolbar-btn-join:hover {
  background: rgba(103, 58, 183, 0.15) !important;
}

.join-selected-item {
  outline: 2px solid rgba(103, 58, 183, 0.7) !important;
  outline-offset: -2px;
}

.join-select-bar,
.join-placement-bar {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background: rgba(103, 58, 183, 0.15);
  border-top: 1px solid rgba(103, 58, 183, 0.3);
  font-size: 12px;
  position: sticky;
  bottom: 0;
  z-index: 5;
}

.join-select-count {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #CE93D8;
}

.join-placement-gap {
  height: 8px;
  margin: 0 4px;
  position: relative;
  cursor: pointer;
  transition: height 0.15s ease;
}

.join-placement-gap:hover,
.join-placement-gap-hover {
  height: 32px;
}

.join-gap-line {
  position: absolute;
  left: 8px;
  right: 8px;
  top: 50%;
  height: 2px;
  background: rgba(103, 58, 183, 0.3);
  border-radius: 1px;
  transition: background 0.15s, height 0.15s;
}

.join-placement-gap:hover .join-gap-line,
.join-placement-gap-hover .join-gap-line {
  background: rgba(103, 58, 183, 0.8);
  height: 3px;
  box-shadow: 0 0 8px rgba(103, 58, 183, 0.4);
}

.join-gap-label {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 10px;
  font-weight: 600;
  color: #CE93D8;
  background: rgba(30, 30, 30, 0.9);
  padding: 2px 10px;
  border-radius: 10px;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
  pointer-events: none;
}

.join-placement-gap-last {
  margin-top: 2px;
  margin-bottom: 4px;
}
</style>
