        <!-- NEW: Hierarchical Region Structure -->
        <div class="rundown-regions-container" style="min-height: 20px;">
          <!-- Region-level draggable -->
          <draggable
            v-model="regions"
            tag="div"
            :item-key="region => region.id"
            :animation="200"
            class="regions-draggable"
            ghost-class="ghost-region"
            chosen-class="chosen-region"
            drag-class="drag-region"
            @start="handleRegionDragStart"
            @end="handleRegionDragEnd"
          >
            <template #item="{ element: region }">
              <div
                class="region-container"
                :class="{
                  'region-break': region.type === 'break',
                  'region-selected': selectedRegionId === region.id,
                  'region-collapsed': shouldCollapseRegion(region)
                }"
                :style="{
                  '--region-color': resolveVuetifyColor(getRegionColor(region.type))
                }"
              >
                <!-- Region Header -->
                <div
                  class="region-header"
                  :class="{
                    'break-region': region.type === 'break'
                  }"
                  :style="{
                    backgroundColor: selectedRegionId === region.id ? getSelectionColor() : resolveVuetifyColor(getRegionColor(region.type)),
                    color: selectedRegionId === region.id ? getSelectionTextColor() : getTextColorForBackground(resolveVuetifyColor(getRegionColor(region.type)))
                  }"
                  @click="handleRegionSelect(region)"
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

                        <v-list-item @click="handleDuplicateRegion(region)">
                          <v-list-item-title>Duplicate Region</v-list-item-title>
                          <template v-slot:prepend>
                            <v-icon size="small">mdi-content-copy</v-icon>
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

                    <!-- Delete button when region is selected -->
                    <v-btn
                      v-if="selectedRegionId === region.id"
                      icon
                      size="small"
                      variant="text"
                      color="error"
                      class="ml-auto"
                      @click.stop="handleSelectedRegionDelete(region)"
                      :style="{ color: 'red' }"
                    >
                      <v-icon size="default">mdi-delete</v-icon>
                      <v-tooltip activator="parent" location="bottom">
                        Delete Selected Region
                      </v-tooltip>
                    </v-btn>
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
                    @start="handleItemDragStart"
                    @end="handleItemDragEnd"
                    @change="handleItemChange"
                  >
                    <template #item="{ element: item }">
                      <div class="rundown-item-wrapper">
                        <v-card
                          flat
                          :class="[
                            'rundown-item-card',
                            { 'selected-item': getItemGlobalIndex(item) === selectedItemIndex },
                            { 'editing-item': getItemGlobalIndex(item) === editingItemIndex },
                            { 'placeholder-item': item.isPlaceholder }
                          ]"
                          :style="{
                            backgroundColor: getItemGlobalIndex(item) === selectedItemIndex ? getSelectionColor() : getBackgroundColorForItem(item?.type || 'unknown'),
                            color: getItemGlobalIndex(item) === selectedItemIndex ? getSelectionTextColor() : getTextColorForItem(item?.type || 'unknown')
                          }"
                          @click="handleItemSelect(item)"
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
                            <div class="type-label">{{ (item?.type || 'UNKNOWN').toUpperCase() }}</div>

                            <!-- Slug (Bold) -->
                            <div class="slug-text">{{ (item?.slug || '').toLowerCase() }}</div>

                            <!-- Duration (Right side) -->
                            <div v-if="panelWidth === 'wide'" class="duration-display">
                              {{ formatDuration(item?.duration || '0:00') }}
                            </div>

                            <!-- Delete button for selected item -->
                            <v-btn
                              v-if="getItemGlobalIndex(item) === selectedItemIndex"
                              icon
                              size="small"
                              variant="text"
                              color="error"
                              class="item-delete-btn-right"
                              @click.stop="handleItemDelete(item)"
                              :style="{ color: 'red' }"
                            >
                              <v-icon size="default">mdi-delete</v-icon>
                              <v-tooltip activator="parent" location="bottom">
                                Delete Selected Item
                              </v-tooltip>
                            </v-btn>
                          </div>
                        </v-card>
                      </div>
                    </template>
                  </draggable>
                </div>
              </div>
            </template>
          </draggable>

          <!-- Add New Region Button -->
          <div class="new-region-button-container">
            <v-btn
              variant="outlined"
              color="primary"
              size="small"
              @click="createNewRegion"
              class="add-region-btn"
            >
              <v-icon left>mdi-plus</v-icon>
              Add New Region
            </v-btn>
          </div>
        </div>