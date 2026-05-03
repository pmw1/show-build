<template>
  <v-container fluid class="pa-0">
    <v-row class="header-row ma-0">
      <v-col cols="12" class="pa-0">
        <!-- Full-width Episode Title Bar -->
        <div class="episode-title-bar-fullwidth">
          <div class="episode-title-bar-content">
            <div class="episode-selector-container">
              <span class="episode-label-above">Episode</span>
              <EpisodeSelector
                :episodes="episodes"
                :current-episode="selectedEpisode"
                :loading="loading"
                :disabled="loading"
                @episode-changed="handleEpisodeChange"
                button-class="episode-select-titlebar"
              />
            </div>
            <div class="title-bar-actions">
              <v-btn 
                color="white" 
                variant="text" 
                size="small"
                @click="toggleEpisodeDetails"
                class="toggle-details-btn"
              >
                <v-icon size="16" :class="{ 'rotate-180': showEpisodeDetails }">mdi-chevron-down</v-icon>
                {{ showEpisodeDetails ? 'Hide Episode Details' : 'Show Episode Details' }}
              </v-btn>
              <v-btn 
                color="white" 
                variant="text" 
                size="small"
                @click="saveEpisodeInfo"
                :disabled="!episodeInfo || updatingEpisode"
                :loading="updatingEpisode"
                class="save-commit-btn"
              >
                <v-icon start size="16">mdi-content-save</v-icon>
                Save & Commit
              </v-btn>
            </div>
          </div>
        </div>
        
        <!-- Episode Info Card with proper margins -->
        <div class="episode-info-section">
          <div class="d-flex align-center justify-space-between mb-1">
            <h2 class="text-h5 font-weight-bold">Rundown Editor</h2>
          </div>
          
          <v-card class="episode-info-card" variant="outlined">
            
            <!-- Collapsible Episode Details -->
            <v-expand-transition>
              <v-card-text v-show="showEpisodeDetails" class="pa-5">
                <v-row no-gutters>
                  <!-- Left column -->
                  <v-col cols="4" class="pr-4">
                    <div class="inline-edit-field">
                      <label class="field-label">Title:</label>
                      <v-text-field
                        v-model="inlineEpisodeInfo.title"
                        variant="solo"
                        density="compact"
                        hide-details
                        class="inline-input title-input"
                        placeholder="Episode title"
                      />
                    </div>
                    <div class="inline-edit-field">
                      <label class="field-label">Subtitle:</label>
                      <v-text-field
                        v-model="inlineEpisodeInfo.subtitle"
                        variant="solo"
                        density="compact"
                        hide-details
                        class="inline-input"
                        placeholder="Subtitle"
                      />
                    </div>
                    <div class="inline-edit-field">
                      <label class="field-label">Guests:</label>
                      <v-text-field
                        v-model="inlineEpisodeInfo.guest"
                        variant="solo"
                        density="compact"
                        hide-details
                        class="inline-input"
                        placeholder="guests, comma separated"
                      />
                    </div>
                    <div class="inline-edit-field">
                      <label class="field-label">Tags:</label>
                      <v-text-field
                        v-model="inlineEpisodeInfo.tags"
                        variant="solo"
                        density="compact"
                        hide-details
                        class="inline-input"
                        placeholder="tags, comma separated"
                      />
                    </div>
                  </v-col>
                  
                  <!-- Middle column -->
                  <v-col cols="4" class="px-3">
                    <div class="inline-edit-field">
                      <label class="field-label">Status:</label>
                      <v-select
                        v-model="inlineEpisodeInfo.status"
                        variant="solo"
                        density="compact"
                        hide-details
                        class="inline-input"
                        :items="[
                          { title: 'Draft', value: 'draft' },
                          { title: 'Production', value: 'production' },
                          { title: 'Ready', value: 'ready' },
                          { title: 'Archived', value: 'archived' }
                        ]"
                      />
                    </div>
                    <div class="inline-edit-field">
                      <label class="field-label">Air Date:</label>
                      <v-text-field
                        v-model="inlineEpisodeInfo.airdate"
                        variant="solo"
                        density="compact"
                        hide-details
                        type="date"
                        class="inline-input"
                      />
                    </div>
                    <div class="inline-edit-field">
                      <label class="field-label">Duration:</label>
                      <v-text-field
                        v-model="inlineEpisodeInfo.duration"
                        variant="solo"
                        density="compact"
                        hide-details
                        class="inline-input"
                        placeholder="HH:MM:SS"
                      />
                    </div>
                  </v-col>

                  <!-- Right column - Compact Stats -->
                  <v-col cols="2" class="pl-4">
                    <div class="status-table-container">
                      <h3 class="status-table-title">Stats</h3>
                      <v-table density="compact" class="status-table-embedded">
                        <tbody>
                          <tr>
                            <td class="text-caption font-weight-medium">Segments:</td>
                            <td class="text-caption">{{ segmentCount }}</td>
                          </tr>
                          <tr>
                            <td class="text-caption font-weight-medium">Transitions:</td>
                            <td class="text-caption">{{ transCount }}</td>
                          </tr>
                          <tr>
                            <td class="text-caption font-weight-medium">Promos:</td>
                            <td class="text-caption">{{ promoCount }}</td>
                          </tr>
                          <tr>
                            <td class="text-caption font-weight-medium">Adverts:</td>
                            <td class="text-caption">{{ advertCount }}</td>
                          </tr>
                          <tr>
                            <td class="text-caption font-weight-medium">CTAs:</td>
                            <td class="text-caption">{{ ctaCount }}</td>
                          </tr>
                        </tbody>
                      </v-table>
                    </div>
                  </v-col>

                  <!-- Empty space for future content -->
                  <v-col cols="2" class="pl-4">
                    <!-- Reserved for future content -->
                  </v-col>
                </v-row>
              </v-card-text>
            </v-expand-transition>
          </v-card>
        </div>
      </v-col>
    </v-row>

    <!-- Controls row -->
    <v-row class="controls-row mb-4">
      <v-col cols="12" class="d-flex align-end justify-end gap-2">
        <!-- Action buttons -->
        <v-btn 
          color="success" 
          variant="outlined" 
          @click="showAddItemDialog = true" 
          :disabled="loading || !selectedEpisode"
          class="mr-2"
        >
          <v-icon start>mdi-plus</v-icon>
          Add New Item
        </v-btn>

        <v-btn 
          color="info" 
          variant="outlined" 
          @click="refreshData" 
          :disabled="loading"
          class="mr-2"
        >
          <v-icon start>mdi-refresh</v-icon>
          Refresh
        </v-btn>

        <v-btn 
          color="error" 
          variant="outlined" 
          @click="revertChanges" 
          :disabled="loading || segments.length === 0"
          style="display: none;"
        >
          <v-icon start>mdi-undo</v-icon>
          Revert
        </v-btn>

        <v-btn 
          color="primary" 
          variant="outlined" 
          @click="compileRundown" 
          :disabled="loading || segments.length === 0"
        >
          <v-icon start>mdi-cog</v-icon>
          Compile
        </v-btn>

        <v-btn 
          color="secondary" 
          variant="outlined" 
          class="ml-2" 
          @click="printRundown" 
          :disabled="loading || segments.length === 0"
        >
          <v-icon start>mdi-printer</v-icon>
          Print
        </v-btn>

        <v-btn 
          color="success" 
          class="ml-2" 
          @click="saveChanges" 
          :disabled="loading || segments.length === 0"
        >
          <v-icon start>mdi-content-save</v-icon>
          Save & Commit
        </v-btn>
      </v-col>
    </v-row>

    <!-- Selected Item Actions Row -->
    <v-row v-if="selectedItem" class="mb-4">
      <v-col cols="12">
        <v-card variant="outlined" class="selected-item-actions-compact">
          <div class="d-flex align-center justify-space-between h-100">
            <!-- Left section: Index and selection info -->
            <div class="d-flex align-center">
              <!-- Far left: Index number -->
              <div class="index-display">
                {{ (segments.findIndex(item => item.filename === selectedItem.filename) + 1) * 10 }}
              </div>
              
              <!-- Selection info -->
              <div class="d-flex align-center ml-3">
                <v-icon color="primary" size="16">mdi-cursor-pointer</v-icon>
                <span class="text-caption font-weight-medium ml-1">Selected:</span>
                <v-chip 
                  :style="getItemBackgroundStyle(selectedItem.type)"
                  size="x-small" 
                  class="ml-2 compact-chip"
                >
                  {{ selectedItem.type?.toUpperCase() || 'UNKNOWN' }}
                </v-chip>
                <span class="ml-2 text-body-2 selected-slug">{{ (selectedItem.slug || '').toLowerCase() }}</span>
              </div>
            </div>
            
            <!-- Right side: Action buttons -->
            <div class="d-flex align-center" style="gap: 0.5em;">
              <v-btn 
                color="primary" 
                variant="flat" 
                size="small"
                class="compact-btn"
                @click="editSelectedItem"
              >
                <v-icon start size="14">mdi-pencil</v-icon>
                Edit
              </v-btn>
              <v-btn 
                color="secondary" 
                variant="flat" 
                size="small"
                class="compact-btn"
                @click="duplicateSelectedItem"
              >
                <v-icon start size="14">mdi-content-copy</v-icon>
                Duplicate
              </v-btn>
              <v-btn 
                color="warning" 
                variant="flat" 
                size="small"
                class="compact-btn"
                @click="moveSelectedItem"
              >
                <v-icon start size="14">mdi-arrow-up-down</v-icon>
                Move
              </v-btn>
              <v-btn 
                color="error" 
                variant="outlined" 
                size="small"
                class="compact-btn"
                @click="deleteSelectedItem"
              >
                <v-icon start size="14">mdi-delete</v-icon>
                Delete
              </v-btn>
              <v-tooltip bottom>
                <template v-slot:activator="{ props }">
                  <v-btn 
                    v-bind="props"
                    color="info" 
                    variant="flat" 
                    size="small"
                    class="compact-btn"
                    icon
                  >
                    <v-icon size="14">mdi-keyboard</v-icon>
                  </v-btn>
                </template>
                <div class="pa-2">
                  <div><strong>Keyboard Shortcuts:</strong></div>
                  <div>↑/↓ - Navigate items</div>
                  <div>Enter - Edit</div>
                  <div>Ctrl+D - Duplicate</div>
                  <div>Delete - Remove</div>
                  <div>Esc - Clear selection</div>
                </div>
              </v-tooltip>
              <v-btn 
                color="grey" 
                variant="outlined" 
                size="small"
                class="compact-btn close-btn"
                @click="clearSelection"
              >
                <v-icon size="14">mdi-close</v-icon>
              </v-btn>
            </div>
          </div>
        </v-card>
      </v-col>
    </v-row>
    <!-- Rundown list -->
    <v-card-text @click="handleContainerClick">
      <div>
        <v-fade-transition>
          <div v-if="loading" class="text-center">
            <v-progress-circular 
              indeterminate 
              color="primary"
              size="64"
            />
            <p class="mt-2">Loading rundown...</p>
          </div>
        </v-fade-transition>

        <v-alert
          v-if="!loading && segments.length === 0"
          type="warning"
          outlined
          class="text-center"
        >
          No segments found for episode {{ selectedEpisode }}. 
          Check /mnt/sync/disaffected/episodes/{{ selectedEpisode }}/rundown/ for .md files.
        </v-alert>

        <v-virtual-scroll
          v-if="segments && segments.length > 0"
          :items="segments"
          :item-height="46"
          height="600"
        >
          <template v-slot:default="{ item, index }">
            <v-card
              :class="['elevation-1', 'rundown-item-card', 'mb-1', { 'selected-item': selectedItemIndex === index, 'editing-item': editingItemIndex === index }]"
              :style="{ ...getItemBackgroundStyle(item.type), cursor: 'pointer' }"
              @click="$emit('select-item', index)"
              @dblclick="$emit('edit-item', index)"
            >
              <div class="compact-rundown-row" :style="{ color: getTextColorForItem(item?.type || 'unknown') }">
                <div class="index-number">{{ (index + 1) * 10 }}</div>
                <div class="type-label">{{ (item?.type || 'UNKNOWN').toUpperCase() }}</div>
                <div class="slug-text">{{ (item?.slug || '').toLowerCase() }}</div>
                <div v-if="rundownPanelWidth === 'wide'" class="duration-display">{{ formatDuration(item?.duration || '0:00') }}</div>
              </div>
            </v-card>
          </template>
        </v-virtual-scroll>
        
        <!-- Empty state when no segments but not loading -->
        <div v-else-if="!loading && segments && segments.length === 0" class="text-center py-8">
          <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-playlist-remove</v-icon>
          <p class="text-h6 text-grey-lighten-1">No rundown items found</p>
          <p class="text-caption text-grey">Click "Add New Item" to get started</p>
        </div>
      </div>
    </v-card-text>

    <!-- Add dialogs after v-container -->
    <v-dialog v-model="showUnavailableDialog" max-width="400">
      <v-card>
        <v-card-title>Unavailable</v-card-title>
        <v-card-text>
          This feature is not yet available. Talk to Kevin about when it will be ready.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="primary" @click="showUnavailableDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showCompileDialog" max-width="400">
      <v-card>
        <v-card-title>Compile Script</v-card-title>
        <v-card-text>
          <v-radio-group v-model="compileTarget">
            <v-radio label="Director" value="director"></v-radio>
            <v-radio label="Host" value="host"></v-radio>
            <v-radio label="Prompter Operator" value="prompter"></v-radio>
          </v-radio-group>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="showCompileDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="handleCompile">Compile</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="showPrintDialog" max-width="400">
      <v-card>
        <v-card-title>Print for</v-card-title>
        <v-card-text>
          <v-radio-group v-model="printTarget">
            <v-radio label="Director" value="director"></v-radio>
            <v-radio label="Host" value="host"></v-radio>
            <v-radio label="Prompter Operator" value="prompter"></v-radio>
          </v-radio-group>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="showPrintDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="handlePrint">Print</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Add New Rundown Item Dialog -->
    <v-dialog v-model="showAddItemDialog" max-width="700" persistent>
      <v-card class="add-item-dialog">
        <v-card-title class="add-item-header">
          <div class="header-content">
            <v-icon class="header-icon" size="28">mdi-plus-circle</v-icon>
            <span class="header-text">Add New Rundown Item</span>
          </div>
        </v-card-title>
        
        <v-divider class="header-divider"></v-divider>
        
        <v-card-text class="add-item-content">
          <v-container fluid class="pa-0">
            <!-- Essential Information Section -->
            <div class="form-section">
              <h3 class="section-title">
                <v-icon size="20" class="section-icon">mdi-information</v-icon>
                Essential Information
              </h3>
              <v-row>
                <v-col cols="12">
                  <v-text-field
                    v-model="newItem.slug"
                    label="Slug"
                    variant="outlined"
                    required
                    :rules="[v => !!v || 'Slug is required']"
                    hint="Short identifier for this item (e.g., 'intro-segment')"
                    prepend-inner-icon="mdi-tag"
                    class="required-field"
                  />
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="newItem.title"
                    label="Title"
                    variant="outlined"
                    required
                    :rules="[v => !!v || 'Title is required']"
                    prepend-inner-icon="mdi-format-title"
                    class="required-field"
                  />
                </v-col>
                <v-col cols="6">
                  <v-select
                    v-model="newItem.type"
                    :items="itemTypes"
                    label="Type"
                    variant="outlined"
                    required
                    :rules="[v => !!v || 'Type is required']"
                    prepend-inner-icon="mdi-shape"
                    class="required-field"
                  />
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    v-model="newItem.duration"
                    label="Duration"
                    variant="outlined"
                    placeholder="00:05:30"
                    prepend-inner-icon="mdi-clock-outline"
                    hint="Format: HH:MM:SS"
                  />
                </v-col>
              </v-row>
            </div>

            <!-- Additional Details Section -->
            <div class="form-section">
              <h3 class="section-title">
                <v-icon size="20" class="section-icon">mdi-text-box</v-icon>
                Additional Details
                <span class="optional-badge">Optional</span>
              </h3>
              <v-row>
                <v-col cols="12">
                  <v-textarea
                    v-model="newItem.description"
                    label="Description"
                    variant="outlined"
                    rows="3"
                    auto-grow
                    hint="Brief description of this rundown item"
                    prepend-inner-icon="mdi-text"
                  />
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    v-model="newItem.guests"
                    label="Guests"
                    variant="outlined"
                    hint="Guest names (if applicable)"
                    prepend-inner-icon="mdi-account-multiple"
                  />
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    v-model="newItem.tags"
                    label="Tags"
                    variant="outlined"
                    hint="Comma-separated tags"
                    prepend-inner-icon="mdi-tag-multiple"
                  />
                </v-col>
              </v-row>
            </div>
          </v-container>
        </v-card-text>
        
        <v-divider class="footer-divider"></v-divider>
        
        <v-card-actions class="add-item-actions">
          <div class="action-info">
            <v-icon size="16" class="info-icon">mdi-information-outline</v-icon>
            <span class="info-text">Item will be added to episode {{ selectedEpisode }}</span>
          </div>
          <v-spacer></v-spacer>
          <v-btn 
            color="error" 
            variant="outlined"
            @click="cancelAddItem"
            :disabled="creatingItem"
            class="action-btn"
          >
            <v-icon start>mdi-close</v-icon>
            Cancel
          </v-btn>
          <v-btn 
            color="success" 
            variant="elevated"
            @click="createNewItem"
            :disabled="!isNewItemValid || creatingItem"
            :loading="creatingItem"
            class="action-btn create-btn"
          >
            <v-icon start>mdi-plus</v-icon>
            Create Item
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Edit Episode Info Dialog -->
    <v-dialog v-model="showEditEpisodeDialog" max-width="800" persistent>
      <v-card class="edit-episode-dialog">
        <v-card-title class="edit-episode-header">
          <div class="header-content">
            <v-icon class="header-icon" size="28">mdi-television</v-icon>
            <span class="header-text">Edit Episode Information</span>
          </div>
        </v-card-title>
        
        <v-divider class="header-divider"></v-divider>
        
        <v-card-text class="edit-episode-content">
          <v-container fluid class="pa-0">
            <!-- Basic Information Section -->
            <div class="form-section">
              <h3 class="section-title">
                <v-icon size="20" class="section-icon">mdi-information</v-icon>
                Basic Information
              </h3>
              <v-row>
                <v-col cols="8">
                  <v-text-field
                    v-model="editableEpisodeInfo.title"
                    label="Episode Title"
                    variant="outlined"
                    prepend-inner-icon="mdi-format-title"
                  />
                </v-col>
                <v-col cols="4">
                  <v-text-field
                    v-model="editableEpisodeInfo.duration"
                    label="Duration"
                    variant="outlined"
                    placeholder="01:00:00"
                    prepend-inner-icon="mdi-clock-outline"
                    hint="Format: HH:MM:SS"
                  />
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="editableEpisodeInfo.subtitle"
                    label="Subtitle"
                    variant="outlined"
                    prepend-inner-icon="mdi-subtitles"
                  />
                </v-col>
              </v-row>
            </div>

            <!-- Production Details Section -->
            <div class="form-section">
              <h3 class="section-title">
                <v-icon size="20" class="section-icon">mdi-calendar</v-icon>
                Production Details
              </h3>
              <v-row>
                <v-col cols="6">
                  <v-text-field
                    v-model="editableEpisodeInfo.airdate"
                    label="Air Date"
                    variant="outlined"
                    type="datetime-local"
                    prepend-inner-icon="mdi-calendar"
                  />
                </v-col>
                <v-col cols="6">
                  <v-select
                    v-model="editableEpisodeInfo.status"
                    label="Status"
                    variant="outlined"
                    :items="[
                      { title: 'Draft', value: 'draft' },
                      { title: 'In Review', value: 'review' },
                      { title: 'Production', value: 'production' },
                      { title: 'Ready', value: 'ready' },
                      { title: 'Archived', value: 'archived' }
                    ]"
                    prepend-inner-icon="mdi-progress-check"
                  />
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    v-model="editableEpisodeInfo.guest"
                    label="Guests"
                    variant="outlined"
                    prepend-inner-icon="mdi-account-multiple"
                  />
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    v-model="editableEpisodeInfo.slug"
                    label="Slug"
                    variant="outlined"
                    prepend-inner-icon="mdi-link"
                  />
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="editableEpisodeInfo.tags"
                    label="Tags"
                    variant="outlined"
                    hint="Comma-separated tags"
                    prepend-inner-icon="mdi-tag-multiple"
                  />
                </v-col>
              </v-row>
            </div>
          </v-container>
        </v-card-text>
        
        <v-divider class="footer-divider"></v-divider>
        
        <v-card-actions class="edit-episode-actions">
          <div class="action-info">
            <v-icon size="16" class="info-icon">mdi-information-outline</v-icon>
            <span class="info-text">Changes will be saved to episode {{ selectedEpisode }} info.md</span>
          </div>
          <v-spacer></v-spacer>
          <v-btn 
            color="error" 
            variant="outlined"
            @click="cancelEpisodeEdit"
            :disabled="updatingEpisode"
            class="action-btn"
          >
            <v-icon start>mdi-close</v-icon>
            Cancel
          </v-btn>
          <v-btn 
            color="success" 
            variant="elevated"
            @click="saveEpisodeChanges"
            :disabled="updatingEpisode"
            :loading="updatingEpisode"
            class="action-btn save-btn"
          >
            <v-icon start>mdi-content-save</v-icon>
            Save Changes
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>

  <!-- Add this right after your v-container closing tag -->
  <div
    v-if="showClickOverlay"
    class="click-overlay"
    :class="{ 'single': clickType === 'single', 'double': clickType === 'double' }"
  >
    {{ clickType === 'single' ? 'SINGLE CLICK' : 'DOUBLE CLICK' }}
  </div>

  <!-- Snackbar for messages -->
  <v-snackbar
    v-model="snackbar.show"
    :color="snackbar.color"
    :timeout="snackbar.timeout"
    location="bottom"
  >
    {{ snackbar.message }}
    <template v-slot:actions>
      <v-btn variant="text" @click="snackbar.show = false">Close</v-btn>
    </template>
  </v-snackbar>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, getCurrentInstance } from 'vue'
import EpisodeSelector from "./EpisodeSelector.vue" // eslint-disable-line no-unused-vars
import axios from "axios"
import { getColorValue, resolveVuetifyColor } from '../utils/themeColorMap'

const emit = defineEmits(['select-item', 'edit-item']) // eslint-disable-line no-unused-vars

// Get vuetify instance
const instance = getCurrentInstance()
const vuetifyInstance = computed(() => instance?.proxy?.$vuetify)

// Template ref
const rundownList = ref(null) // eslint-disable-line no-unused-vars

// Undefined in original Options API (used in template but never declared)
const selectedItemIndex = ref(null) // eslint-disable-line no-unused-vars
const editingItemIndex = ref(null) // eslint-disable-line no-unused-vars
const rundownPanelWidth = ref(null) // eslint-disable-line no-unused-vars

// Data
const segments = ref([])
const selectedEpisode = ref(null)
const episodes = ref([])
const episodeInfo = ref(null)
const selectedItem = ref(null)
const loading = ref(false)
const isDragging = ref(false)
const draggedIndex = ref(null)
const dragOverIndex = ref(null)
const dragError = ref(null) // eslint-disable-line no-unused-vars
const showUnavailableDialog = ref(false)
const showCompileDialog = ref(false)
const showPrintDialog = ref(false)
const showAddItemDialog = ref(false)
const showEditEpisodeDialog = ref(false)
const compileTarget = ref('director')
const printTarget = ref('director')
const singleClickActive = ref(false)
const doubleClickActive = ref(false)
let clickTimer = null
const showClickOverlay = ref(false)
const clickType = ref('')
const creatingItem = ref(false)
const updatingEpisode = ref(false)
const showEpisodeDetails = ref(false)
const editableEpisodeInfo = ref({
  title: '',
  subtitle: '',
  duration: '',
  guest: '',
  tags: '',
  slug: '',
  status: '',
  airdate: ''
})
const inlineEpisodeInfo = ref({
  title: '',
  subtitle: '',
  duration: '',
  guest: '',
  tags: '',
  slug: '',
  status: '',
  airdate: ''
})
const newItem = ref({
  title: '',
  type: 'segment',
  slug: '',
  duration: '00:05:30',
  description: '',
  guests: '',
  tags: ''
})
const itemTypes = ref([ // eslint-disable-line no-unused-vars
  { title: 'Segment', value: 'segment' },
  { title: 'Advertisement', value: 'ad' },
  { title: 'Promo', value: 'promo' },
  { title: 'Call to Action', value: 'cta' },
  { title: 'Transition', value: 'trans' },
  { title: 'Unknown', value: 'unknown' }
])
const snackbar = ref({
  show: false,
  message: '',
  color: 'success',
  timeout: 4000
})

// Computed
const segmentCount = computed(() => {
  return segments.value.filter(item => item.type === 'segment').length
})
const promoCount = computed(() => {
  return segments.value.filter(item => item.type === 'promo').length
})
const advertCount = computed(() => {
  return segments.value.filter(item => item.type === 'ad').length
})
const transCount = computed(() => {
  return segments.value.filter(item => item.type === 'trans').length
})
const ctaCount = computed(() => {
  return segments.value.filter(item => item.type === 'cta').length
})
const isNewItemValid = computed(() => {
  return newItem.value.title.trim() &&
         newItem.value.slug.trim() &&
         newItem.value.type
})
const modalThemeColor = computed(() => {
  if (!newItem.value.type) {
    return 'primary' // Default blue theme
  }
  const color = getColorValue(newItem.value.type.toLowerCase())

  // Map colormap values to valid Vuetify theme colors
  const colorMapping = {
    'purple-accent': 'purple',
    'blue-accent': 'blue',
    'green-accent': 'green',
    'red-accent': 'red',
    'yellow-accent': 'yellow',
    'grey-light': 'grey',
    'purple': 'purple',
    'blue': 'blue',
    'green': 'green',
    'red': 'red',
    'yellow': 'yellow',
    'grey': 'grey',
    'indigo': 'indigo',
    'teal': 'teal',
    'cyan': 'cyan',
    'pink': 'pink',
    'orange': 'orange'
  }

  return colorMapping[color] || 'primary'
})
const modalThemeColorRgb = computed(() => { // eslint-disable-line no-unused-vars
  const colorName = modalThemeColor.value

  // Use direct color values to ensure they always work
  const directColors = {
    'purple': '#9C27B0',
    'blue': '#2196F3',
    'green': '#4CAF50',
    'red': '#F44336',
    'yellow': '#FFC107',
    'grey': '#9E9E9E',
    'indigo': '#3F51B5',
    'teal': '#009688',
    'cyan': '#00BCD4',
    'pink': '#E91E63',
    'orange': '#FF9800',
    'primary': '#1976D2'
  }

  return directColors[colorName] || directColors['primary']
})

// Methods
function showSnackbar(message, color = 'success') {
  snackbar.value.message = message
  snackbar.value.color = color
  snackbar.value.show = true
}

function loadEpisodeFromSession() {
  const savedEpisodeId = sessionStorage.getItem('currentEpisodeId')
  if (savedEpisodeId && episodes.value.length > 0) {
    const episode = episodes.value.find(e => e.id === parseInt(savedEpisodeId))
    if (episode) {
      selectedEpisode.value = episode.value
    } else {
      // Fallback to the latest episode if saved one isn't in the list
      selectLatestEpisode()
    }
  } else if (episodes.value.length > 0) {
    selectLatestEpisode()
  }

  if (selectedEpisode.value) {
    loadEpisode(selectedEpisode.value)
  }
}

function selectLatestEpisode() {
  const latestEpisode = episodes.value.reduce((latest, current) => {
    return (latest.id > current.id) ? latest : current
  })
  selectedEpisode.value = latestEpisode.value
  sessionStorage.setItem('currentEpisodeId', latestEpisode.id)
}

async function handleEpisodeChange(newEpisode) {
  if (newEpisode && newEpisode.value !== selectedEpisode.value) {
    selectedEpisode.value = newEpisode.value
    sessionStorage.setItem('currentEpisodeId', newEpisode.id)
    await loadEpisode(newEpisode.value)
  }
}

async function fetchEpisodes() {
  loading.value = true
  try {
    const response = await axios.get('/api/episodes')

    // The API returns { episodes: [...] }
    const episodesData = response.data.episodes || []
    episodes.value = episodesData.map(ep => ({
      id: ep.id,
      title: ep.title || `Episode ${ep.episode_number}`,
      // Use episode_number for the value, padded to 4 digits
      value: ep.episode_number ? ep.episode_number.padStart(4, '0') : ep.id
    }))

    // After fetching, determine the initial episode
    loadEpisodeFromSession()

  } catch (err) { // eslint-disable-line no-unused-vars
    // console.error("Failed to fetch episodes:", err)
  } finally {
    loading.value = false
  }
}

async function fetchEpisodeInfo(episodeId) {
  if (!episodeId) return

  try {
    const response = await axios.get(
      `/api/episodes/${episodeId}/info`
    )

    episodeInfo.value = response.data.info

    // Also populate inline editing fields
    populateInlineEpisodeInfo()
  } catch (err) { // eslint-disable-line no-unused-vars
    episodeInfo.value = null
    clearInlineEpisodeInfo()
  }
}

function populateInlineEpisodeInfo() {
  if (episodeInfo.value) {
    inlineEpisodeInfo.value = {
      title: episodeInfo.value.title || '',
      subtitle: episodeInfo.value.subtitle || '',
      duration: episodeInfo.value.duration || '',
      guest: episodeInfo.value.guest || '',
      tags: Array.isArray(episodeInfo.value.tags) ? episodeInfo.value.tags.join(', ') : (episodeInfo.value.tags || ''),
      slug: episodeInfo.value.slug || '',
      status: episodeInfo.value.status || '',
      airdate: episodeInfo.value.airdate || ''
    }
  }
}

async function loadEpisode(episodeId) {
  if (!episodeId) return

  loading.value = true
  try {
    // Fetch both rundown segments and episode info in parallel
    const [rundownResponse] = await Promise.all([
      axios.get(`/api/episodes/${episodeId}/rundown`),
      fetchEpisodeInfo(episodeId)
    ])

    if (rundownResponse.data && Array.isArray(rundownResponse.data.items)) {
        segments.value = rundownResponse.data.items.map((item, index) => ({
        ...item,
        filename: item.filename || `item-${index}-${Date.now()}`, // Ensure filename always exists
        id: item.id || `item-${Math.random().toString(36).substr(2, 9)}`
      })).filter(item => item.filename && item.filename.trim() !== '')
    } else {
        segments.value = []
    }
  } catch (err) { // eslint-disable-line no-unused-vars
    segments.value = []
  } finally {
    loading.value = false
  }
}

async function saveChanges() {
  try {
    const payload = { segments: segments.value.map(segment => ({ filename: segment.filename })) }
    await axios.post(
      `/api/episodes/${selectedEpisode.value}/reorder`,
      payload
    )
    showSnackbar("Rundown reordered successfully!")
  } catch (err) {
    showSnackbar("Failed to save rundown: " + err.message, "error")
  }
}

function revertChanges() {
  showUnavailableDialog.value = true
}

function compileRundown() {
  showCompileDialog.value = true
}

function handleCompile() {
  showCompileDialog.value = false
  // Implement actual compilation
}

function printRundown() {
  showPrintDialog.value = true
}

function handlePrint() {
  showPrintDialog.value = false
  // Implement actual printing
}

// Selection management methods
function clearSelection() {
  selectedItem.value = null
}

function editSelectedItem() {
  if (!selectedItem.value) return
  // TODO: Implement edit functionality - could open a modal or navigate to edit page
  showSnackbar(`Edit functionality for "${selectedItem.value.slug}" will be implemented soon!`, "info")
}

function duplicateSelectedItem() {
  if (!selectedItem.value) return
  // TODO: Create a copy of the selected item
  showSnackbar(`Duplicate functionality for "${selectedItem.value.slug}" will be implemented soon!`, "info")
}

function moveSelectedItem() {
  if (!selectedItem.value) return
  // TODO: Implement move to specific position functionality
  showSnackbar(`Move functionality for "${selectedItem.value.slug}" will be implemented soon!`, "info")
}

async function deleteSelectedItem() {
  if (!selectedItem.value) return

  const confirmed = confirm(`Are you sure you want to delete "${selectedItem.value.slug}"?`)
  if (!confirmed) return

  try {
    // TODO: Implement actual delete API call

    // For now, just remove from local array
    const index = segments.value.findIndex(item =>
      item.filename === selectedItem.value.filename
    )
    if (index !== -1) {
      segments.value.splice(index, 1)
      selectedItem.value = null
      showSnackbar('Item deleted successfully! (Note: This is currently local only)')
    }
  } catch (error) {
    showSnackbar('Failed to delete item: ' + error.message, 'error')
  }
}

// New item creation methods
async function createNewItem() {
  if (!isNewItemValid.value) return

  creatingItem.value = true
  try {
    const response = await axios.post(
      `/api/episodes/${selectedEpisode.value}/item`,
      newItem.value
    )

    // Show success message
    showSnackbar(`Successfully created: ${response.data.filename}`)

    // Reset form and close dialog
    resetNewItemForm()
    showAddItemDialog.value = false

    // Reload the rundown to show the new item
    await loadEpisode(selectedEpisode.value)

  } catch (err) {
    showSnackbar("Failed to create new rundown item: " + (err.response?.data?.detail || err.message), "error")
  } finally {
    creatingItem.value = false
  }
}

function cancelAddItem() {
  resetNewItemForm()
  showAddItemDialog.value = false
}

function resetNewItemForm() {
  newItem.value = {
    title: '',
    type: 'segment',
    slug: '',
    duration: '00:05:30',
    description: '',
    guests: '',
    tags: ''
  }
}

function resolveTypeClass(type) { // eslint-disable-line no-unused-vars
  if (!type || type === 'unknown') {
    return 'bg-grey-light'
  }

  const normalizedType = type.toLowerCase()

  const color = getColorValue(normalizedType)
  const cssClass = `bg-${color}`

  return cssClass
}

function getItemBackgroundStyle(type) {
  if (!type || type === 'unknown') {
    return { backgroundColor: '#F5F5F5' } // grey-light fallback
  }

  const normalizedType = type.toLowerCase()
  const colorName = getColorValue(normalizedType)
  const backgroundColor = resolveVuetifyColor(colorName, vuetifyInstance.value)

  return { backgroundColor }
}

function dragStart() { // eslint-disable-line no-unused-vars
  isDragging.value = true
  const dragLightColor = getColorValue('draglight')
  const highlightColor = getColorValue('highlight')
  const droplineColor = getColorValue('dropline')  // Add dropline color

  // Set all CSS custom properties
  document.documentElement.style.setProperty('--highlight-color', `rgb(var(--v-theme-${highlightColor}))`)
  document.documentElement.style.setProperty('--draglight-color', `rgb(var(--v-theme-${dragLightColor}))`)
  document.documentElement.style.setProperty('--dropline-color', `rgb(var(--v-theme-${droplineColor}))`)

  // Force a reflow to ensure animation triggers consistently
  requestAnimationFrame(() => {
    document.body.offsetHeight // eslint-disable-line no-unused-expressions
  })
}

function dragEnd() { // eslint-disable-line no-unused-vars
  isDragging.value = false

  // Force animation reset
  requestAnimationFrame(() => {
    document.body.offsetHeight // eslint-disable-line no-unused-expressions
  })
}

function handleDragChange(/*evt*/) { // eslint-disable-line no-unused-vars
  // Validate new order if needed
}

function handleSingleClick(item) { // eslint-disable-line no-unused-vars
  clearTimeout(clickTimer)
  clickTimer = setTimeout(() => {
    if (!doubleClickActive.value) {

      // Set selected item
      selectedItem.value = item

      // Visual feedback
      singleClickActive.value = true
      clickType.value = 'single'
      showClickOverlay.value = true
      setTimeout(() => {
        singleClickActive.value = false
        showClickOverlay.value = false
      }, 300)
    }
  }, 200)
}

function handleDoubleClick(item) { // eslint-disable-line no-unused-vars
  clearTimeout(clickTimer)
  doubleClickActive.value = true

  // Select the item and open edit
  selectedItem.value = item

  // Show visual feedback
  clickType.value = 'double'
  showClickOverlay.value = true

  // Quick edit action (for now just call edit)
  setTimeout(() => {
    editSelectedItem()
    doubleClickActive.value = false
    showClickOverlay.value = false
  }, 200)
}

// Handle clicks on empty space to clear selection
function handleContainerClick(event) {
  // Only clear selection if clicking on the container itself, not child elements
  if (event.target === event.currentTarget) {
    clearSelection()
  }
}

// Keyboard shortcuts
function handleKeydown(event) {
  // Only handle shortcuts when not typing in inputs
  if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
    return
  }

  if (!selectedItem.value) return

  switch (event.key) {
    case 'Delete':
    case 'Backspace':
      event.preventDefault()
      deleteSelectedItem()
      break
    case 'Enter':
      event.preventDefault()
      editSelectedItem()
      break
    case 'Escape':
      event.preventDefault()
      clearSelection()
      break
    case 'd':
      if (event.ctrlKey || event.metaKey) {
        event.preventDefault()
        duplicateSelectedItem()
      }
      break
    case 'ArrowUp':
      event.preventDefault()
      selectPreviousItem()
      break
    case 'ArrowDown':
      event.preventDefault()
      selectNextItem()
      break
  }
}

// Navigation methods
function selectPreviousItem() {
  if (!selectedItem.value || segments.value.length === 0) return

  const currentIndex = segments.value.findIndex(item =>
    item.filename === selectedItem.value.filename
  )

  if (currentIndex > 0) {
    selectedItem.value = segments.value[currentIndex - 1]
  }
}

function selectNextItem() {
  if (!selectedItem.value || segments.value.length === 0) return

  const currentIndex = segments.value.findIndex(item =>
    item.filename === selectedItem.value.filename
  )

  if (currentIndex < segments.value.length - 1) {
    selectedItem.value = segments.value[currentIndex + 1]
  }
}

function calculateBacktime(currentIndex) { // eslint-disable-line no-unused-vars
  // Calculate backtime: total show duration minus cumulative duration up to current index
  if (!episodeInfo.value || !episodeInfo.value.duration) {
    // Fallback to old behavior if no episode info
    let totalSeconds = 0
    try {
      for (let i = currentIndex; i < segments.value.length; i++) {
        const duration = segments.value[i].duration || '00:00:00'
        totalSeconds += parseDurationToSeconds(duration)
      }
    } catch (error) { // eslint-disable-line no-unused-vars
      return '00:00:00'
    }
    return formatSecondsToTime(totalSeconds)
  }

  try {
    // Get total show duration in seconds
    const totalShowSeconds = parseDurationToSeconds(episodeInfo.value.duration)

    // Calculate cumulative duration of all segments up to (but not including) current index
    let cumulativeSeconds = 0
    for (let i = 0; i < currentIndex; i++) {
      const duration = segments.value[i].duration || '00:00:00'
      cumulativeSeconds += parseDurationToSeconds(duration)
    }

    // Backtime = total show duration - cumulative duration up to current item
    const backtimeSeconds = totalShowSeconds - cumulativeSeconds

    return formatSecondsToTime(Math.max(0, backtimeSeconds))
  } catch (error) { // eslint-disable-line no-unused-vars
    return '00:00:00'
  }
}

function parseDurationToSeconds(duration) {
  // Parse duration string (HH:MM:SS or MM:SS) to total seconds
  if (!duration || duration === 'N/A') return 0

  // Convert to string if it's not already
  const durationStr = String(duration)

  const parts = durationStr.split(':')
  if (parts.length === 3) {
    // HH:MM:SS format
    return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2])
  } else if (parts.length === 2) {
    // MM:SS format
    return parseInt(parts[0]) * 60 + parseInt(parts[1])
  }
  return 0
}

function formatSecondsToTime(totalSeconds) {
  // Format seconds back to HH:MM:SS
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60

  return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

async function refreshData() {

  try {
    loading.value = true

    // Save current order mapping (filename -> position in current segments array)
    const currentOrder = new Map()
    segments.value.forEach((segment, index) => {
      if (segment.filename) {
        currentOrder.set(segment.filename, index)
      }
    })

    // Clear current selection
    selectedItem.value = null

    // Fetch fresh episode list
    await fetchEpisodes()

    // If we have a selected episode, reload its data while preserving order
    if (selectedEpisode.value) {
      await loadEpisodePreservingOrder(selectedEpisode.value, currentOrder)
    }

    // Show success feedback
    nextTick(() => {
      // Do nothing
    })

  } catch (error) { // eslint-disable-line no-unused-vars
    // console.error('Error during data refresh:', error)
  } finally {
    loading.value = false
  }
}

async function loadEpisodePreservingOrder(episodeId, currentOrder) {
  if (!episodeId) return

  try {
    // Fetch both rundown segments and episode info in parallel
    const [rundownResponse] = await Promise.all([
      axios.get(`/api/episodes/${episodeId}/rundown`),
      fetchEpisodeInfo(episodeId)
    ])

    // Process the fresh data
    const freshSegments = rundownResponse.data.map((entry, index) => ({
      ...entry.metadata,
      filename: entry.filename || `item-${index}-${Date.now()}`,
      type: entry.metadata?.type || 'unknown',
      slug: entry.metadata?.slug || 'Untitled',
      id: entry.metadata?.id || `id-${index}`,
      duration: entry.metadata?.duration || 'N/A'
    })).filter(item => item.filename && item.filename.trim() !== '')

    // If we have a current order to preserve, sort the fresh data accordingly
    if (currentOrder && currentOrder.size > 0) {

      // Separate items that exist in current order vs new items
      const orderedItems = []
      const newItems = []

      freshSegments.forEach(item => {
        if (currentOrder.has(item.filename)) {
          orderedItems.push({
            item,
            originalIndex: currentOrder.get(item.filename)
          })
        } else {
          newItems.push(item)
        }
      })

      // Sort ordered items by their original position
      orderedItems.sort((a, b) => a.originalIndex - b.originalIndex)

      // Combine: preserved order items first, then new items at the end
      segments.value = [
        ...orderedItems.map(entry => entry.item),
        ...newItems
      ]

    } else {
      // No previous order to preserve, use fresh order
      segments.value = freshSegments
    }

  } catch (err) { // eslint-disable-line no-unused-vars
    // Fallback to regular load
    await loadEpisode(episodeId)
  }
}

function toggleEpisodeDetails() {
  showEpisodeDetails.value = !showEpisodeDetails.value
}

// Color and theme management methods
function updateSelectionColors() {
  // Update CSS custom properties for selection colors
  const selectionColor = getColorValue('primary') || 'blue'
  document.documentElement.style.setProperty('--selection-color', `rgb(var(--v-theme-${selectionColor}))`)

  const droplineColor = getColorValue('yellow') || 'warning'
  document.documentElement.style.setProperty('--dropline-color', `rgb(var(--v-theme-${droplineColor}))`)
}

function updateModalTheme() {
  // Update modal theme colors if needed
  const themeColor = getColorValue('surface') || 'background'
  document.documentElement.style.setProperty('--modal-bg', `rgb(var(--v-theme-${themeColor}))`)
}

function getTextColorForItem(type) {
  if (!type || type === 'unknown') {
    return '#666'
  }
  const normalizedType = type.toLowerCase()
  const color = getColorValue(normalizedType)
  const isDarkBackground = ['purple-accent', 'blue-accent', 'indigo-accent', 'red-accent'].includes(color)
  return isDarkBackground ? '#ffffff' : '#000000'
}

function formatDuration(duration) {
  // Format duration for display
  if (!duration || duration === 'N/A') return '00:00'
  return duration
}

// Drag and drop event handlers
function handleDragStart(event, index) { // eslint-disable-line no-unused-vars
  draggedIndex.value = index
  isDragging.value = true
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/html', event.target.innerHTML)

  // Add visual feedback
  event.target.style.opacity = '0.5'

  // Store the dragged item data
  event.dataTransfer.setData('draggedIndex', index.toString())
}

function handleDragEnd(event) { // eslint-disable-line no-unused-vars
  draggedIndex.value = null
  dragOverIndex.value = null
  isDragging.value = false

  // Reset visual feedback
  event.target.style.opacity = '1'

  // Clean up any drag-over styling
  const draggableItems = rundownList.value?.querySelectorAll('.draggable-item')
  if (draggableItems) {
    draggableItems.forEach(item => {
      item.classList.remove('drag-over-top', 'drag-over-bottom')
    })
  }
}

function handleDragOver(event) { // eslint-disable-line no-unused-vars
  if (event.preventDefault) {
    event.preventDefault() // Allow drop
  }
  event.dataTransfer.dropEffect = 'move'
  return false
}

function handleDragEnter(event, index) { // eslint-disable-line no-unused-vars
  if (draggedIndex.value === null) return

  dragOverIndex.value = index

  // Add visual feedback for drop zone
  const rect = event.currentTarget.getBoundingClientRect()
  const midpoint = rect.top + rect.height / 2

  // Clear previous indicators
  const draggableItems = rundownList.value?.querySelectorAll('.draggable-item')
  if (draggableItems) {
    draggableItems.forEach(item => {
      item.classList.remove('drag-over-top', 'drag-over-bottom')
    })
  }

  // Add new indicator
  if (event.clientY < midpoint) {
    event.currentTarget.classList.add('drag-over-top')
  } else {
    event.currentTarget.classList.add('drag-over-bottom')
  }
}

function handleDragLeave(event) { // eslint-disable-line no-unused-vars
  // Remove visual feedback when leaving
  event.currentTarget.classList.remove('drag-over-top', 'drag-over-bottom')
}

function handleDrop(event, dropIndex) { // eslint-disable-line no-unused-vars
  if (event.stopPropagation) {
    event.stopPropagation() // Stop propagation
  }

  if (draggedIndex.value === null || draggedIndex.value === dropIndex) {
    return false
  }

  // Get the position (before or after)
  const rect = event.currentTarget.getBoundingClientRect()
  const midpoint = rect.top + rect.height / 2
  const insertAfter = event.clientY >= midpoint

  // Calculate the actual insertion index
  let targetIndex = dropIndex
  if (insertAfter && dropIndex >= draggedIndex.value) {
    targetIndex = dropIndex
  } else if (insertAfter) {
    targetIndex = dropIndex + 1
  } else if (!insertAfter && dropIndex > draggedIndex.value) {
    targetIndex = dropIndex - 1
  } else {
    targetIndex = dropIndex
  }

  // Perform the reorder
  const draggedItem = segments.value[draggedIndex.value]
  const newSegments = [...segments.value]

  // Remove the dragged item
  newSegments.splice(draggedIndex.value, 1)

  // Insert at new position
  if (draggedIndex.value < targetIndex) {
    newSegments.splice(targetIndex, 0, draggedItem)
  } else {
    newSegments.splice(targetIndex, 0, draggedItem)
  }

  // Update the segments array
  segments.value = newSegments

  // Clean up
  draggedIndex.value = null
  dragOverIndex.value = null

  // Clean up visual indicators
  const draggableItems = rundownList.value?.querySelectorAll('.draggable-item')
  if (draggableItems) {
    draggableItems.forEach(item => {
      item.classList.remove('drag-over-top', 'drag-over-bottom')
    })
  }

  return false
}

function clearInlineEpisodeInfo() {
  inlineEpisodeInfo.value = {
    title: '',
    subtitle: '',
    duration: '',
    guest: '',
    tags: '',
    slug: '',
    status: '',
    airdate: ''
  }
}

async function saveEpisodeInfo() {
  if (!episodeInfo.value || !selectedEpisode.value) return

  updatingEpisode.value = true
  try {
    // Prepare the data
    const updateData = {
      ...inlineEpisodeInfo.value,
      tags: inlineEpisodeInfo.value.tags ? inlineEpisodeInfo.value.tags.split(',').map(t => t.trim()) : []
    }

    // Save the episode info
    await axios.put(`/api/episodes/${selectedEpisode.value}/info`, updateData)

    // Update local episodeInfo
    episodeInfo.value = { ...episodeInfo.value, ...updateData }

    showSnackbar('Episode information saved successfully!')
  } catch (error) {
    showSnackbar('Failed to save episode information: ' + error.message, 'error')
  } finally {
    updatingEpisode.value = false
  }
}

function cancelEpisodeEdit() { // eslint-disable-line no-unused-vars
  // Reset to original values
  populateInlineEpisodeInfo()
  showEditEpisodeDialog.value = false
}

async function saveEpisodeChanges() { // eslint-disable-line no-unused-vars
  updatingEpisode.value = true
  try {
    // Similar to saveEpisodeInfo but for the dialog
    const updateData = {
      ...editableEpisodeInfo.value,
      tags: editableEpisodeInfo.value.tags ? editableEpisodeInfo.value.tags.split(',').map(t => t.trim()) : []
    }

    await axios.put(`/api/episodes/${selectedEpisode.value}/info`, updateData)

    // Update both local states
    episodeInfo.value = { ...episodeInfo.value, ...updateData }
    populateInlineEpisodeInfo()

    showEditEpisodeDialog.value = false
    showSnackbar('Episode information updated successfully!')
  } catch (error) {
    showSnackbar('Failed to update episode information: ' + error.message, 'error')
  } finally {
    updatingEpisode.value = false
  }
}

// created() logic - runs immediately in <script setup>
// Initialize colors
const highlightColor = getColorValue('highlight') // eslint-disable-line no-unused-vars
document.documentElement.style.setProperty('--highlight-color', `rgb(var(--v-theme-${highlightColor}))`)
updateSelectionColors()

// Initialize modal theme
updateModalTheme()

// Add keyboard event listeners
document.addEventListener('keydown', handleKeydown)

// Lifecycle hooks
onMounted(() => {
  fetchEpisodes()  // This will now also trigger loading the episode from session
})

onBeforeUnmount(() => {
  // Clean up keyboard event listeners
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
/*============================================================
  🛡️ PROTECTED: CORE RUNDOWN STYLES - DO NOT MODIFY 
============================================================*/

/* Force square corners */
.v-card,
.v-card.elevation-1,
:deep(.v-card),
:deep(.v-card__text) {
  border-radius: 0 !important;
}

/* Core layout structure */
.rundown-row {
  min-height: 46px !important;
  max-height: 46px !important;
  width: 100%;
  margin: 0;
}

.type-col {
  width: 120px !important;
  min-width: 120px !important;
  max-width: 120px !important;
}

/* Cell styling */
.type-cell {
  height: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0;
  padding: 0;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(0, 0, 0, 0.1);
}

.index-number {
  font-size: 0.85rem;
  font-weight: 700;
  opacity: 0.9;
  font-family: monospace;
  min-width: 35px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  color: rgba(255, 255, 255, 0.95);
  z-index: 1;
}

/* Drag and drop states */
.sortable-chosen {
  background: var(--draglight-color) !important;
  cursor: grabbing !important;
  transform: translateX(-35px) !important;
  z-index: 100;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2) !important;
  color: rgba(0, 0, 0, 0.87) !important;  /* Add high contrast for dragged item */
}

.sortable-chosen .index-number {
  color: rgba(255, 255, 255, 0.95) !important;  /* Keep index number white */
}

.sortable-chosen .type-label,
.sortable-chosen .slug-text,
.sortable-chosen .duration-box {
  color: rgba(0, 0, 0, 0.87) !important;  /* Ensure text is dark for contrast */
}

.sortable-ghost {
  opacity: 0.5;
  background: var(--highlight-color) !important;
  border: 2px dashed var(--dropline-color) !important;
}

.sortable-drag {
  opacity: 0.3;
}

/* Hover states */
.v-card.elevation-1:hover:not(.dragging):not(.sortable-chosen) {
  background: var(--highlight-color) !important;
  cursor: grab;
  color: rgba(0, 0, 0, 0.87) !important;
}

/*============================================================
  🛡️ END PROTECTED CORE STYLES
============================================================*/

/* Safe to modify styles below this line */

/* Adjust container padding */
:deep(.v-container) {
  padding: 0 !important;
}

/* Remove card text padding */
:deep(.v-card-text) {
  padding: 0 !important;
}

/* Update header row and controls row to match */
.header-row,
.controls-row {
  background: rgba(0, 0, 0, 0.03);
  padding: 8px 16px;  /* Consistent padding */
  margin: 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  width: 100%;
}

/* Update controls row styling */
.controls-row {
  margin: 0;
  padding: 0 !important;
  width: 100%;
  background: transparent;
  border: none;
}

/* Update button styling in the scoped styles section */
.controls-row .v-btn {
  --v-btn-height: 40px !important;  /* Increased from 28px to match v-select */
  font-size: 0.875rem !important;   /* Slightly larger font */
  letter-spacing: 0.25px !important;
  padding: 0 16px !important;       /* Increased padding */
}

.controls-row .v-btn .v-icon {
  font-size: 18px !important;       /* Slightly larger icons */
  margin-right: 4px !important;     /* Space between icon and text */
}

/* Update episode select to ensure consistent height */
:deep(.episode-select .v-field) {
  background: white !important;
  border: 2px solid rgb(var(--v-theme-primary)) !important;
  border-radius: 4px !important;
  height: 40px !important;
  min-height: 40px !important;
}

:deep(.episode-select .v-field__input) {
  min-height: 40px !important;  /* Removed the extra '0' */
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  font-size: 1.25rem !important;
  font-weight: 500 !important;
  color: rgb(var(--v-theme-primary)) !important;  /* Blue text */
}

:deep(.episode-select .v-field__field .v-label) {
  position: absolute !important;
  top: -32px !important;
  left: 0 !important;
  transform: none !important;
  font-size: 0.75rem !important;
  color: rgb(var(--v-theme-primary)) !important;  /* Blue label */
  background: transparent !important;
  z-index: 1 !important;
  margin: 0 !important;
  padding: 0 !important;
  transition: none !important;
}

/* Update dropdown icon color */
:deep(.episode-select .v-field__append-inner) {
  color: rgb(var(--v-theme-primary)) !important;  /* Blue dropdown arrow */
}

/* Update just the status table styling */
.status-table {
  background: transparent !important;
  margin: 0 !important;
  padding: 0 !important;
  min-width: 180px !important;
}

.status-table :deep(td) {
  height: 16px !important;
  padding: 0 !important;
  border: none !important;
  white-space: nowrap !important;
  text-align: left !important;
}

/* Minimal spacing between value and label */
.status-table :deep(td:last-child) {
  padding-left: 4px !important;
}

/* Header styling */
.status-table :deep(th) {
  padding: 0 0 2px 0 !important;
}

/* Make rows full width */
.rundown-row {
  min-height: 46px !important;
  max-height: 46px !important;
  width: 100%;
  margin: 0;
}

/* Adjust layout sizes */
.rundown-row {
  min-height: 46px !important;  /* Increased from 42px by 10% */
  max-height: 46px !important;
}

.type-col {
  width: 120px !important;     /* Adjusted for horizontal layout */
  min-width: 120px !important;
  max-width: 120px !important;
}

/* Update type cell and index number styling */
.type-cell {
  height: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 0;                /* Remove gap between index and type */
  padding: 0;
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(0, 0, 0, 0.1);
}

.index-number {
  font-size: 0.85rem;
  font-weight: 700;            /* Increased to 700 for bolder index numbers */
  opacity: 0.9;
  font-family: monospace;
  min-width: 35px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 0;
  color: rgba(255, 255, 255, 0.95);
  z-index: 1;
}

/* Type label specific styling */
.type-label {
  font-size: 0.75rem !important;  /* Smaller size */
  font-weight: 400 !important;    /* Normal weight */
  flex-grow: 1 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 0 !important;
  height: 100% !important;
}

/* Slug text specific styling */
.slug-text {
  font-size: 1.05rem !important;  /* Larger size */
  font-weight: 700 !important;    /* Bold weight */
  flex-grow: 1 !important;
  padding: 0 12px !important;
  display: flex !important;
  align-items: center !important;
}

.content-cell {
  padding: 0;  /* Remove padding from content cell */
  height: 100%;
  display: flex;
  align-items: stretch;  /* Changed to stretch for full height */
  justify-content: space-between;
}

.duration-box {
  font-size: 0.9rem;  /* Increased from 0.8rem */
  font-family: monospace;
  background: rgba(0, 0, 0, 0.1);
  padding: 0 12px;
  white-space: nowrap;
  width: 100px;  /* Set fixed width instead of min-width */
  display: flex;
  align-items: center;
  justify-content: center;
  border-left: 1px solid rgba(0, 0, 0, 0.05);  /* Optional subtle separator */
  overflow: hidden;
  text-overflow: ellipsis;
}

.backtime-box {
  font-size: 0.9rem;
  font-family: monospace;
  background: rgba(0, 0, 0, 0.15);  /* Slightly darker background */
  padding: 0 12px;
  white-space: nowrap;
  width: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-left: 1px solid rgba(0, 0, 0, 0.05);
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;  /* Slightly bolder for distinction */
}

/* Enhanced transition effects */
.v-scale-transition-enter-active,
.v-scale-transition-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.v-scale-transition-enter-from,
.v-scale-transition-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* Clean up hover state and improve text contrast */
.v-card.elevation-1:hover:not(.dragging):not(.sortable-chosen) {
  background: var(--highlight-color) !important;
  cursor: grab;
  transform: translateZ(0);
  color: rgba(0, 0, 0, 0.87) !important;  /* Add high contrast text */
}

/* Add specific contrast for light/dark backgrounds on hover */
.v-card.elevation-1:hover[class*="bg-light"]:not(.dragging):not(.sortable-chosen) {
  color: rgba(0, 0, 0, 0.87) !important;
}

.v-card.elevation-1:hover[class*="bg-dark"]:not(.dragging):not(.sortable-chosen),
.v-card.elevation-1:hover.bg-blue-accent:not(.dragging):not(.sortable-chosen),
.v-card.elevation-1:hover.bg-purple-accent:not(.dragging):not(.sortable-chosen),
.v-card.elevation-1:hover.bg-indigo-accent:not(.dragging):not(.sortable-chosen) {
  color: rgba(255, 255, 255, 0.95) !important;
}

/* Base card state */
.v-card {
  transform: translateX(0);
  transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.4, 1), 
              border 0.2s ease,
              box-shadow 0.2s ease;
  will-change: transform;
}

/* Selected item styling */
.selected-item {
  border: 3px solid var(--selection-color, #FF7043) !important;
  box-shadow: 0 4px 16px var(--selection-color-alpha, rgba(255, 112, 67, 0.3)) !important;
  transform: translateX(-8px) scale(1.02) !important;
  position: relative;
  z-index: 10;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.selected-item::before {
  content: '';
  position: absolute;
  left: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 60%;
  background: var(--selection-color, #FF7043);
  border-radius: 0 2px 2px 0;
}

/* Dragged item */
.sortable-chosen {
  background: var(--draglight-color) !important;
  cursor: grabbing !important;
  transform: translateX(-35px) !important;
  z-index: 100;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2) !important;
  color: rgba(0, 0, 0, 0.87) !important;  /* Add high contrast for dragged item */
}

.sortable-chosen .index-number {
  color: rgba(255, 255, 255, 0.95) !important;  /* Keep index number white */
}

.sortable-chosen .type-label,
.sortable-chosen .slug-text,
.sortable-chosen .duration-box {
  color: rgba(0, 0, 0, 0.87) !important;  /* Ensure text is dark for contrast */
}

/* Ghost placeholder */
.sortable-ghost {
  opacity: 0.5;
  background: var(--highlight-color) !important;
  border: 2px dashed var(--dropline-color) !important;
}

/* Hide drag clone */
.sortable-drag {
  opacity: 0.3;
}

/* Update header row and layout styles */
.header-row {
  margin: 0 !important;
}

.episode-title-bar-fullwidth {
  background: #1976d2;
  color: white;
  width: 100vw;
  position: relative;
  left: 50%;
  right: 50%;
  margin-left: -50vw;
  margin-right: -50vw;
  padding: 12px 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.episode-title-bar-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.episode-selector-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.episode-label-above {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: rgba(255, 255, 255, 0.9);
  text-transform: uppercase;
}

.title-bar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toggle-details-btn,
.save-commit-btn {
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  opacity: 0.9;
  transition: opacity 0.2s ease;
  height: 32px !important;
  min-width: 100px !important;
}

.toggle-details-btn:hover,
.save-commit-btn:hover {
  opacity: 1;
}

.rotate-180 {
  transform: rotate(180deg);
  transition: transform 0.3s ease;
}

.episode-info-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  margin-top: 16px;
}

/* Rundown specific styles */
.rundown-manager {
  background: #f4f6f8;
  border-radius: 8px;
  overflow: hidden;
  margin-top: 16px;
}

.rundown-header {
  background: #1976d2;
  color: white;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rundown-title {
  font-size: 1.25rem;
  font-weight: 500;
  margin: 0;
}

.rundown-item-card {
  transition: background-color 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
  border-left: 4px solid transparent;
}

.rundown-item-card.selected-item {
  background-color: #1976D2; /* Example color for selected item */
  color: white;
  border-left-color: #FFC107; /* Example highlight color */
}

.rundown-item-card.editing-item {
  box-shadow: 0 0 8px rgba(255, 193, 7, 0.8); /* Example glow effect */
}

.compact-rundown-row {
  display: flex;
  align-items: center;
  padding: 0 8px;
  height: 40px;
}

.index-number {
  font-weight: bold;
  width: 40px;
  text-align: center;
}

.type-label {
  font-weight: 500;
  width: 60px;
  text-transform: uppercase;
}

.slug-text {
  flex-grow: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.duration-display {
  width: 80px;
  text-align: right;
}
</style>

<style>
/* Global styles - no scoping */
/* Modal styles stay the same */
.v-overlay__content:where(.v-dialog) {
  border: 10px solid black !important;
  border-radius: 0 !important;
  overflow: hidden !important;
}

/* Episode selector dropdown menu styling */
.episode-select-menu {
  margin-top: 4px !important;
  border: none !important;
  border-radius: 4px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
  background: rgb(var(--v-theme-primary)) !important;
  overflow: hidden !important;
}

.episode-select-menu .v-list {
  background: rgb(var(--v-theme-primary)) !important;
  padding: 4px !important;
  min-width: 75px !important;
}

.episode-select-menu .v-list-item {
  min-height: 36px !important;
  font-size: 1.1rem !important;
  padding: 0 12px !important;
  color: white !important;
  text-align: left !important;     /* Changed from center to left */
  display: flex !important;
  align-items: center !important;
}

/* Custom scrollbar styling */
.episode-select-menu ::-webkit-scrollbar {
  width: 8px !important;
}

.episode-select-menu ::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1) !important;
}

.episode-select-menu ::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3) !important;
  border-radius: 4px !important;
}

.episode-select-menu ::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5) !important;
}

/* Selected Item Actions - Compact Version */
.selected-item-actions-compact {
  background: linear-gradient(135deg, #fffbf0, #fff9e6) !important;
  border: 2px solid var(--selection-color, #FF7043) !important;
  border-radius: 6px !important;
  animation: slide-in-from-top 0.3s ease-out;
  height: 48px !important;
  min-height: 48px !important;
  max-height: 48px !important;
  padding: 0 16px !important;
  overflow: hidden !important;
}

.selected-item-actions-compact > div {
  width: 100% !important;
}

.selected-item-actions-compact .index-display {
  font-family: monospace;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--selection-color, #FF7043);
  background: rgba(var(--selection-color-rgb, 255, 112, 67), 0.1);
  border: 2px solid var(--selection-color, #FF7043);
  border-radius: 4px;
  padding: 4px 8px;
  margin-right: 12px;
  min-width: 40px;
  text-align: center;
  line-height: 1;
}

.selected-item-actions-compact .compact-chip {
  font-weight: 600;
  letter-spacing: 0.5px;
  height: 20px !important;
  font-size: 0.7rem !important;
  min-height: 20px !important;
}

.selected-item-actions-compact .selected-slug {
  font-weight: 500;
  font-size: 0.875rem !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.selected-item-actions-compact .compact-btn {
  height: 32px !important;
  min-height: 32px !important;
  padding: 0 12px !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  text-transform: none !important;
  letter-spacing: 0.25px !important;
  min-width: auto !important;
}

.selected-item-actions-compact .compact-btn.close-btn {
  width: 32px !important;
  min-width: 32px !important;
  padding: 0 !important;
}

.selected-item-actions-compact .compact-btn .v-icon {
  margin-right: 4px !important;
}

.selected-item-actions-compact .v-divider--vertical {
  opacity: 0.4;
  background-color: rgba(var(--v-theme-outline), 0.6);
}

@keyframes slide-in-from-top {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity:  1;
    transform: translateY(0);
  }
}

/* Episode Info Inline Editing Styles */
.episode-info-section {
  margin-bottom: 6px;
}

.episode-info-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  overflow: hidden;
}

.episode-title-bar {
  background: #1976d2;
  color: white;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.episode-selector-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.episode-label {
  font-size: 1.1rem;
   font-weight: 600;
  letter-spacing: 0.5px;
  white-space: nowrap;
  line-height: 1.2;
}

.episode-select-titlebar {
  width: 200px;
}

.episode-select-titlebar :deep(.v-field) {
  background-color: rgba(255, 255, 255, 0.15) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: white !important;
  min-height: 28px !important;
}

.episode-select-titlebar :deep(.v-field__input) {
  color: white !important;
  font-weight: 600;
  font-size: 1rem;
  min-height: 24px !important;
  padding: 4px 12px !important;
  display: flex;
  align-items: center;
}

.episode-select-titlebar :deep(.v-field__field) {
  padding: 0 !important;
  display: flex;
  align-items: center;
}

.episode-select-titlebar :deep(.v-field__append-inner) {
  color: white !important;
}

.episode-select-titlebar :deep(.v-field--focused) {
  background-color: rgba(255, 255, 255, 0.25) !important;
}

.save-commit-btn {
  font-size: 0.75rem;
  font-weight: 500;
  opacity: 0.9;
  transition: opacity 0.2s ease;
}

.save-commit-btn:hover {
  opacity: 1;
}

.inline-edit-field {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
}

.inline-edit-field .field-label {
  min-width: 45px;
  font-weight: 600;
  font-size: 0.8rem;
  color: #555;
  display: flex;
  align-items: center;
  height: 32px;
  text-align: right;
  justify-content: flex-end;
  line-height: 1;
  padding-left: 16px;
  padding-right: 12px;
  margin-top: 0.4em;
}

.inline-edit-field .field-value {
  font-size: 0.8rem;
  color: #333;
  font-weight: 500;
  display: flex;
  align-items: center;
  height: 32px;
  line-height: 1.2;
}

.inline-edit-field .inline-input {
  flex: 1;
}

.inline-edit-field .inline-input:not(.title-input) :deep(.v-field) {
  background-color: #e3f2fd !important;
  border: none !important;
  box-shadow: none !important;
  min-height: 32px !important;
  font-size: 0.8rem;
}

.inline-edit-field .inline-input:not(.title-input) :deep(.v-field__input) {
  min-height: 28px !important;
  padding: 6px 12px !important;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  line-height: 1;
}

.inline-edit-field .inline-input:not(.title-input) :deep(.v-field__field) {
  padding: 0 !important;
  display: flex;
  align-items: center;
}

.inline-edit-field .inline-input:not(.title-input) :deep(.v-field--focused) {
  background-color: #e3f2fd !important;
}

.inline-edit-field .title-input :deep(.v-field) {
  background-color: #e3f2fd !important;
  border: none !important;
   box-shadow: none !important;
  min-height:  32px !important;
  font-size: 0.9rem;
}

.inline-edit-field .title-input :deep(.v-field__input) {
  min-height: 28px !important;
  padding: 6px 12px !important;
  font-size: 0.9rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  line-height: 1;
}

.inline-edit-field .title-input :deep(.v-field__field) {
  padding: 0 !important;
  display: flex;
  align-items: center;
}

.inline-edit-field .title-input :deep(.v-field--focused) {
  background-color: #e3f2fd !important;
}

/* Status table container in episode info card */
.status-table-container {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 8px;
  height: fit-content;
}

.status-table-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #555;
  margin-bottom: 6px;
  text-align: center;
}

.status-table-embedded {
  background: transparent;
  border: none;
}

.status-table-embedded tbody tr td {
  padding: 1px 3px !important;
  border-bottom: 1px solid #eee;
  font-size: 0.7rem !important;
}

.status-table-embedded tbody tr:last-child td {
  border-bottom: none;
}

/* Drag and drop styles */
.rundown-list-container {
  position: relative;
}

.draggable-item {
  position: relative;
  transition: transform 0.2s ease;
}

.draggable-item.drag-over-top::before {
  content: '';
  position: absolute;
  top: -2px;
  left: 0;
  right: 0;
  height: 4px;
  background: #2196F3;
  border-radius: 2px;
  z-index: 100;
}

.draggable-item.drag-over-bottom::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  right: 0;
  height: 4px;
  background: #2196F3;
  border-radius: 2px;
  z-index: 100;
}

.rundown-item-card.dragging {
  opacity: 0.5;
  transform: scale(0.95);
}

.rundown-item-card.drag-over {
  background: rgba(33, 150, 243, 0.1) !important;
}

.rundown-item-card[draggable="true"]:hover {
  cursor: grab;
}

.rundown-item-card[draggable="true"]:active {
  cursor: grabbing;
}
</style>

<style>
/* Global styles - no scoping */
/* Modal styles stay the same */
.v-overlay__content:where(.v-dialog) {
  border: 10px solid black !important;
  border-radius: 0 !important;
  overflow: hidden !important;
}

/* Episode selector dropdown menu styling */
.episode-select-menu {
  margin-top: 4px !important;
  border: none !important;
  border-radius: 4px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
  background: rgb(var(--v-theme-primary)) !important;
  overflow: hidden !important;
}

.episode-select-menu .v-list {
  background: rgb(var(--v-theme-primary)) !important;
  padding: 4px !important;
  min-width: 75px !important;
}

.episode-select-menu .v-list-item {
  min-height: 36px !important;
  font-size: 1.1rem !important;
  padding: 0 12px !important;
  color: white !important;
  text-align: left !important;     /* Changed from center to left */
  display: flex !important;
  align-items: center !important;
}

/* Custom scrollbar styling */
.episode-select-menu ::-webkit-scrollbar {
  width: 8px !important;
}

.episode-select-menu ::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1) !important;
}

.episode-select-menu ::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3) !important;
  border-radius: 4px !important;
}

.episode-select-menu ::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5) !important;
}

/* Selected Item Actions - Compact Version */
.selected-item-actions-compact {
  background: linear-gradient(135deg, #fffbf0, #fff9e6) !important;
  border: 2px solid var(--selection-color, #FF7043) !important;
  border-radius: 6px !important;
  animation: slide-in-from-top 0.3s ease-out;
  height: 48px !important;
  min-height: 48px !important;
  max-height: 48px !important;
  padding: 0 16px !important;
  overflow: hidden !important;
}

.selected-item-actions-compact > div {
  width: 100% !important;
}

.selected-item-actions-compact .index-display {
  font-family: monospace;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--selection-color, #FF7043);
  background: rgba(var(--selection-color-rgb, 255, 112, 67), 0.1);
  border: 2px solid var(--selection-color, #FF7043);
  border-radius: 4px;
  padding: 4px 8px;
  margin-right: 12px;
  min-width: 40px;
  text-align: center;
  line-height: 1;
}

.selected-item-actions-compact .compact-chip {
  font-weight: 600;
  letter-spacing: 0.5px;
  height: 20px !important;
  font-size: 0.7rem !important;
  min-height: 20px !important;
}

.selected-item-actions-compact .selected-slug {
  font-weight: 500;
  font-size: 0.875rem !important;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.selected-item-actions-compact .compact-btn {
  height: 32px !important;
  min-height: 32px !important;
  padding: 0 12px !important;
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  text-transform: none !important;
  letter-spacing: 0.25px !important;
  min-width: auto !important;
}

.selected-item-actions-compact .compact-btn.close-btn {
  width: 32px !important;
  min-width: 32px !important;
  padding: 0 !important;
}

.selected-item-actions-compact .compact-btn .v-icon {
  margin-right: 4px !important;
}

.selected-item-actions-compact .v-divider--vertical {
  opacity: 0.4;
  background-color: rgba(var(--v-theme-outline), 0.6);
}

@keyframes slide-in-from-top {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity:  1;
    transform: translateY(0);
  }
}

/* Episode Info Inline Editing Styles */
.episode-info-section {
  margin-bottom: 6px;
}

.episode-info-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  overflow: hidden;
}

.episode-title-bar {
  background: #1976d2;
  color: white;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.episode-selector-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.episode-label {
  font-size: 1.1rem;
   font-weight: 600;
  letter-spacing: 0.5px;
  white-space: nowrap;
  line-height: 1.2;
}

.episode-select-titlebar {
  width: 200px;
}

.episode-select-titlebar :deep(.v-field) {
  background-color: rgba(255, 255, 255, 0.15) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: white !important;
  min-height: 28px !important;
}

.episode-select-titlebar :deep(.v-field__input) {
  color: white !important;
  font-weight: 600;
  font-size: 1rem;
  min-height: 24px !important;
  padding: 4px 12px !important;
  display: flex;
  align-items: center;
}

.episode-select-titlebar :deep(.v-field__field) {
  padding: 0 !important;
  display: flex;
  align-items: center;
}

.episode-select-titlebar :deep(.v-field__append-inner) {
  color: white !important;
}

.episode-select-titlebar :deep(.v-field--focused) {
  background-color: rgba(255, 255, 255, 0.25) !important;
}

.save-commit-btn {
  font-size: 0.75rem;
  font-weight: 500;
  opacity: 0.9;
  transition: opacity 0.2s ease;
}

.save-commit-btn:hover {
  opacity: 1;
}

.inline-edit-field {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
}

.inline-edit-field .field-label {
  min-width: 45px;
  font-weight: 600;
  font-size: 0.8rem;
  color: #555;
  display: flex;
  align-items: center;
  height: 32px;
  text-align: right;
  justify-content: flex-end;
  line-height: 1;
  padding-left: 16px;
  padding-right: 12px;
  margin-top: 0.4em;
}

.inline-edit-field .field-value {
  font-size: 0.8rem;
  color: #333;
  font-weight: 500;
  display: flex;
  align-items: center;
  height: 32px;
  line-height: 1.2;
}

.inline-edit-field .inline-input {
  flex: 1;
}

.inline-edit-field .inline-input:not(.title-input) :deep(.v-field) {
  background-color: #e3f2fd !important;
  border: none !important;
  box-shadow: none !important;
  min-height: 32px !important;
  font-size: 0.8rem;
}

.inline-edit-field .inline-input:not(.title-input) :deep(.v-field__input) {
  min-height: 28px !important;
  padding: 6px 12px !important;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  line-height: 1;
}

.inline-edit-field .inline-input:not(.title-input) :deep(.v-field__field) {
  padding: 0 !important;
  display: flex;
  align-items: center;
}

.inline-edit-field .inline-input:not(.title-input) :deep(.v-field--focused) {
  background-color: #e3f2fd !important;
}

.inline-edit-field .title-input :deep(.v-field) {
  background-color: #e3f2fd !important;
  border: none !important;
   box-shadow: none !important;
  min-height:  32px !important;
  font-size: 0.9rem;
}

.inline-edit-field .title-input :deep(.v-field__input) {
  min-height: 28px !important;
  padding: 6px 12px !important;
  font-size: 0.9rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  line-height: 1;
}

.inline-edit-field .title-input :deep(.v-field__field) {
  padding: 0 !important;
  display: flex;
  align-items: center;
}

.inline-edit-field .title-input :deep(.v-field--focused) {
  background-color: #e3f2fd !important;
}

/* Status table container in episode info card */
.status-table-container {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 8px;
  height: fit-content;
}

.status-table-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #555;
  margin-bottom: 6px;
  text-align: center;
}

.status-table-embedded {
  background: transparent;
  border: none;
}

.status-table-embedded tbody tr td {
  padding: 1px 3px !important;
  border-bottom: 1px solid #eee;
  font-size: 0.7rem !important;
}

.status-table-embedded tbody tr:last-child td {
  border-bottom: none;
}
</style>
