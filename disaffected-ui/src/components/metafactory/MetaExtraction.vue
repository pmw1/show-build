<template>
  <div class="meta-extraction fill-height d-flex flex-column">
    <!-- Episode Status Banner -->
    <v-alert v-if="!currentEpisode" type="info" variant="tonal" prominent class="ma-2">
      <v-alert-title>No Episode Selected</v-alert-title>
      Select an episode from the header to use metadata extraction tools.
    </v-alert>

    <!-- Main Three-Column Layout -->
    <div v-if="currentEpisode" class="flex-grow-1 d-flex ga-2 pa-2" style="min-height: 0;">
      <!-- LEFT COLUMN: Rundown Items List -->
      <div class="left-column d-flex flex-column" style="min-height: 0; flex: 0 0 350px; max-width: 350px;">
        <v-card class="flex-grow-1 d-flex flex-column rundown-panel-card" style="min-height: 0;">
          <v-card-title class="d-flex align-center py-2 flex-grow-0 rundown-title">
            <span class="text-subtitle-1 font-weight-bold">Rundown</span>
            <v-spacer />
            <v-chip size="x-small" color="primary" variant="tonal">
              {{ currentEpisode }}
            </v-chip>
            <v-btn
              icon
              variant="text"
              size="x-small"
              class="ml-1"
              @click="refreshData"
              :loading="loading"
            >
              <v-icon size="small">mdi-refresh</v-icon>
              <v-tooltip activator="parent" location="top">Refresh</v-tooltip>
            </v-btn>
          </v-card-title>
          <v-divider />

          <!-- Stats Bar -->
          <div class="px-3 py-1 bg-grey-darken-4 d-flex align-center ga-2 flex-grow-0 stats-bar">
            <v-chip size="x-small" color="grey" variant="flat">
              {{ filteredRundownItems.length }}
            </v-chip>
            <v-chip size="x-small" color="success" variant="tonal">
              <v-icon start size="x-small">mdi-check-circle</v-icon>
              {{ extractedCount }}
            </v-chip>
            <v-chip v-if="staleSegments.length > 0" size="x-small" color="warning" variant="tonal">
              <v-icon start size="x-small">mdi-alert-circle</v-icon>
              {{ staleSegments.length }}
            </v-chip>
            <v-chip size="x-small" color="grey" variant="tonal">
              <v-icon start size="x-small">mdi-circle-outline</v-icon>
              {{ pendingCount }}
            </v-chip>
          </div>
          <v-divider />

          <!-- Scrollable Items List -->
          <v-card-text class="flex-grow-1 pa-0 overflow-y-auto rundown-list" style="min-height: 0;">
            <!-- Column Headers -->
            <div v-if="filteredRundownItems.length > 0" class="rundown-headers">
              <div class="header-index">#</div>
              <div class="header-type">Type</div>
              <div class="header-slug">Slug</div>
              <div class="header-duration">Dur</div>
            </div>

            <!-- Rundown Items with Draggable (visual only - index numbers don't change) -->
            <draggable
              v-if="filteredRundownItems.length > 0"
              v-model="localDisplayOrder"
              tag="div"
              item-key="id"
              :animation="200"
              class="rundown-items-container"
              ghost-class="ghost-item"
              chosen-class="chosen-item"
              drag-class="drag-item"
            >
              <template #item="{ element: item }">
                <div
                  class="rundown-item-row"
                  :class="{
                    'selected-item': selectedItemId === item.id,
                    'llm-completed': item.llm_status === 'completed',
                    'llm-stale': item.llm_status === 'stale'
                  }"
                  :style="{
                    '--item-bg-color': getBackgroundColorForItem(item.type),
                    '--item-text-color': getTextColorForItem(item.type),
                    '--selection-color': getSelectionColor(),
                    backgroundColor: selectedItemId === item.id ? getSelectionColor() : getBackgroundColorForItem(item.type),
                    color: selectedItemId === item.id ? getSelectionTextColor() : getTextColorForItem(item.type)
                  }"
                  @click="selectItem(item)"
                >
                  <!-- Index Number Cell - always shows original order from database -->
                  <div class="index-cell">
                    <div
                      v-if="item.status && item.status !== 'production'"
                      class="status-indicator"
                      :title="`Status: ${item.status}`"
                    ></div>
                    <div class="llm-status-dot" :class="'status-' + (item.llm_status || 'none')"></div>
                    <span class="index-number">{{ item.order || item.order_in_rundown || '—' }}</span>
                  </div>

                  <!-- Type Label -->
                  <div class="type-cell">
                    <span class="type-label">{{ (item.type || 'UNK').toUpperCase().substring(0, 3) }}</span>
                  </div>

                  <!-- Slug -->
                  <div class="slug-cell">
                    <span class="slug-text">{{ item.slug || item.title || 'Untitled' }}</span>
                  </div>

                  <!-- Duration -->
                  <div class="duration-cell">
                    {{ formatDurationCompact(item.duration) }}
                  </div>

                  <!-- Extract Button -->
                  <div class="action-cell">
                    <v-btn
                      v-if="item.llm_status !== 'completed'"
                      icon
                      variant="text"
                      size="x-small"
                      density="compact"
                      @click.stop="extractSingle(item)"
                      :loading="extractingItems.has(item.id)"
                    >
                      <v-icon size="14">mdi-brain</v-icon>
                    </v-btn>
                  </div>
                </div>
              </template>
            </draggable>

            <div v-else-if="loading" class="d-flex justify-center align-center pa-8">
              <v-progress-circular indeterminate color="primary" />
            </div>

            <div v-else class="d-flex flex-column align-center pa-8 text-medium-emphasis">
              <v-icon size="48" class="mb-2">mdi-file-document-outline</v-icon>
              <span>No rundown items found</span>
            </div>
          </v-card-text>
        </v-card>
      </div>

      <!-- MIDDLE COLUMN: Metadata Display (flex-grow) -->
      <div class="middle-column flex-grow-1 d-flex flex-column" style="min-height: 0; min-width: 300px;">
        <!-- When NO Segment Selected: Simple instruction -->
        <template v-if="!selectedItem">
          <div class="flex-grow-1 d-flex flex-column align-center justify-center text-medium-emphasis">
            <v-icon size="48" class="mb-3">mdi-cursor-default-click</v-icon>
            <div class="text-body-1">Select a segment to view metadata</div>
          </div>
        </template>

        <!-- When Segment IS Selected: Metadata Display -->
        <template v-else>
          <v-card class="flex-grow-1 d-flex flex-column" style="min-height: 0;">
            <v-card-title class="d-flex align-center py-3 flex-grow-0">
              <v-icon
                :color="getTypeColor(selectedItem.item_type)"
                class="mr-2"
              >
                {{ getTypeIcon(selectedItem.item_type) }}
              </v-icon>
              <span class="text-truncate">{{ selectedItem.title || 'Untitled' }}</span>
              <v-spacer />
              <v-btn
                icon
                variant="text"
                size="small"
                @click="clearSelection"
              >
                <v-icon>mdi-close</v-icon>
                <v-tooltip activator="parent" location="top">Close</v-tooltip>
              </v-btn>
            </v-card-title>
            <v-divider />

            <!-- Segment Actions Bar -->
            <div class="px-4 py-2 bg-grey-darken-4 d-flex align-center ga-2 flex-grow-0">
              <v-chip
                :color="getStatusColor(selectedItem.llm_status)"
                size="small"
                variant="flat"
              >
                <v-icon start size="x-small">{{ getStatusIcon(selectedItem.llm_status) }}</v-icon>
                {{ selectedItem.llm_status || 'none' }}
              </v-chip>
              <v-spacer />
              <v-btn
                color="primary"
                variant="tonal"
                size="small"
                prepend-icon="mdi-brain"
                @click="extractSingle(selectedItem)"
                :loading="extractingItems.has(selectedItem.id)"
              >
                {{ selectedItem.llm_status === 'completed' ? 'Re-extract' : 'Extract' }}
              </v-btn>
            </div>
            <v-divider />

            <!-- Scrollable Masonry Grid -->
            <v-card-text class="flex-grow-1 overflow-y-auto pa-4" style="min-height: 0;">
              <template v-if="selectedItem.llm_data">
                <!-- Card 1: Summary & Description -->
                <v-card variant="outlined" class="mb-4 metadata-card">
                  <v-card-title class="text-subtitle-1 py-2">
                    <v-icon start size="small" color="blue">mdi-text-box-outline</v-icon>
                    Summary & Description
                  </v-card-title>
                  <v-divider />
                  <v-card-text>
                    <div class="mb-4">
                      <div class="text-caption font-weight-bold text-uppercase mb-1">Summary</div>
                      <div class="text-body-2">
                        {{ selectedItem.llm_data.llm_summary || 'No summary extracted' }}
                      </div>
                    </div>
                    <div>
                      <div class="text-caption font-weight-bold text-uppercase mb-1">Description</div>
                      <div class="text-body-2">
                        {{ selectedItem.llm_data.llm_description || 'No description extracted' }}
                      </div>
                    </div>
                  </v-card-text>
                </v-card>

                <!-- Card 2: Mentioned Entities (Unified Table) -->
                <v-card variant="outlined" class="mb-4 metadata-card">
                  <v-card-title class="text-subtitle-1 py-2 d-flex align-center">
                    <v-icon start size="small" color="primary">mdi-account-details</v-icon>
                    Mentioned Entities
                    <v-chip size="x-small" class="ml-2" color="primary" variant="tonal">
                      {{ allEntities.length }}
                    </v-chip>
                  </v-card-title>
                  <v-divider />
                  <v-card-text class="pa-0">
                    <div v-if="allEntities.length" class="entity-table">
                      <!-- Table Header -->
                      <div class="entity-header">
                        <div class="entity-col entity-type-col">Type</div>
                        <div class="entity-col entity-name-col">Name</div>
                        <div class="entity-col entity-relation-col">Relation to Story</div>
                        <div class="entity-col entity-handle-col">X Handle</div>
                      </div>
                      <!-- Table Rows -->
                      <div
                        v-for="(entity, idx) in allEntities"
                        :key="idx"
                        class="entity-row"
                        :class="'entity-type-' + entity.entityType"
                      >
                        <div class="entity-col entity-type-col">
                          <v-icon size="14" class="mr-1" :color="getEntityColor(entity.entityType)">
                            {{ getEntityIcon(entity.entityType) }}
                          </v-icon>
                          <span class="entity-type-label">{{ entity.entityType }}</span>
                        </div>
                        <div class="entity-col entity-name-col">
                          <span class="entity-name">{{ entity.name }}</span>
                          <v-chip
                            v-if="entity.role || entity.type"
                            size="x-small"
                            class="ml-1"
                            variant="outlined"
                          >
                            {{ entity.role || entity.type }}
                          </v-chip>
                        </div>
                        <div class="entity-col entity-relation-col">
                          {{ entity.relation_to_story || entity.relationToStory || entity.context || '—' }}
                        </div>
                        <div class="entity-col entity-handle-col">
                          <a
                            v-if="entity.x_handle || entity.twitter_handle || entity.handle"
                            :href="'https://x.com/' + (entity.x_handle || entity.twitter_handle || entity.handle).replace('@', '')"
                            target="_blank"
                            class="x-handle-link"
                            @click.stop
                          >
                            @{{ (entity.x_handle || entity.twitter_handle || entity.handle).replace('@', '') }}
                          </a>
                          <span v-else class="text-medium-emphasis">—</span>
                        </div>
                      </div>
                    </div>
                    <div v-else class="text-medium-emphasis text-center py-6">
                      <v-icon size="32">mdi-account-search</v-icon>
                      <div class="text-caption mt-2">No entities extracted</div>
                    </div>
                  </v-card-text>
                </v-card>

                <!-- Card 3: Topics & Key Quotes -->
                <v-card variant="outlined" class="mb-4 metadata-card">
                  <v-card-title class="text-subtitle-1 py-2 d-flex align-center">
                    <v-icon start size="small" color="amber">mdi-tag-multiple</v-icon>
                    Topics & Key Quotes
                  </v-card-title>
                  <v-divider />
                  <v-card-text>
                    <!-- Topics -->
                    <div class="mb-4">
                      <div class="text-caption font-weight-bold text-uppercase mb-2">Topics</div>
                      <div v-if="selectedItem.llm_data.extracted_topics?.length" class="d-flex flex-wrap ga-1">
                        <v-chip
                          v-for="topic in selectedItem.llm_data.extracted_topics"
                          :key="topic"
                          size="small"
                          color="teal"
                          variant="tonal"
                        >
                          {{ topic }}
                        </v-chip>
                      </div>
                      <div v-else class="text-medium-emphasis text-caption">
                        No topics extracted
                      </div>
                    </div>

                    <!-- Key Quotes -->
                    <div>
                      <div class="text-caption font-weight-bold text-uppercase mb-2">Key Quotes</div>
                      <div v-if="selectedItem.llm_data.key_quotes?.length">
                        <div
                          v-for="(quote, idx) in selectedItem.llm_data.key_quotes"
                          :key="idx"
                          class="quote-block mb-2"
                        >
                          <v-icon size="small" color="amber" class="mr-1">mdi-format-quote-open</v-icon>
                          <span class="font-italic">"{{ quote }}"</span>
                        </div>
                      </div>
                      <div v-else class="text-medium-emphasis text-caption">
                        No key quotes extracted
                      </div>
                    </div>
                  </v-card-text>
                </v-card>

                <!-- Metadata Footer -->
                <v-card variant="tonal" color="grey-darken-3" class="mt-4">
                  <v-card-text class="d-flex flex-wrap ga-3 text-caption">
                    <span>
                      <v-icon size="x-small" class="mr-1">mdi-robot</v-icon>
                      Model: {{ selectedItem.llm_data.extraction_model || 'unknown' }}
                    </span>
                    <span>
                      <v-icon size="x-small" class="mr-1">mdi-gauge</v-icon>
                      Confidence: {{ ((selectedItem.llm_data.confidence_score || 0) * 100).toFixed(0) }}%
                    </span>
                    <span>
                      <v-icon size="x-small" class="mr-1">mdi-clock-outline</v-icon>
                      Extracted: {{ formatDate(selectedItem.llm_data.extraction_timestamp) }}
                    </span>
                  </v-card-text>
                </v-card>
              </template>

              <!-- No LLM Data State -->
              <template v-else>
                <div class="d-flex flex-column align-center pt-8 text-medium-emphasis">
                  <v-icon size="64" class="mb-4">mdi-brain</v-icon>
                  <div class="text-h6 mb-2">No Metadata Extracted</div>
                  <div class="text-body-2 mb-4 text-center">
                    Extract metadata from this segment to see<br/>
                    people, organizations, topics, and key quotes.
                  </div>
                  <v-btn
                    color="primary"
                    variant="flat"
                    prepend-icon="mdi-brain"
                    @click="extractSingle(selectedItem)"
                    :loading="extractingItems.has(selectedItem.id)"
                  >
                    Extract Now
                  </v-btn>
                </div>
              </template>
            </v-card-text>
          </v-card>
        </template>
      </div>

      <!-- RIGHT COLUMN: Raw Script View -->
      <div class="right-column d-flex flex-column" style="min-height: 0; flex: 0 0 400px; max-width: 400px;">
        <v-card class="flex-grow-1 d-flex flex-column" style="min-height: 0;">
          <v-card-title class="d-flex align-center py-2 flex-grow-0">
            <v-icon class="mr-2" size="small">mdi-script-text</v-icon>
            <span class="text-subtitle-1">Script Content</span>
          </v-card-title>
          <v-divider />

          <!-- Script Content -->
          <v-card-text class="flex-grow-1 pa-0 overflow-y-auto script-viewer" style="min-height: 0;">
            <template v-if="selectedItem">
              <!-- Script Header Info -->
              <div class="script-header pa-3 bg-grey-darken-4">
                <div class="d-flex align-center ga-2 mb-1">
                  <v-chip
                    size="x-small"
                    :style="{
                      backgroundColor: getItemBackgroundColor(selectedItem.type),
                      color: getItemTextColor(selectedItem.type)
                    }"
                  >
                    {{ (selectedItem.type || 'unknown').toUpperCase() }}
                  </v-chip>
                  <span class="text-caption text-medium-emphasis">
                    {{ selectedItem.duration || '--:--' }}
                  </span>
                </div>
                <div class="text-subtitle-2 font-weight-bold">
                  {{ selectedItem.slug || selectedItem.title || 'Untitled' }}
                </div>
              </div>
              <v-divider />

              <!-- Raw Script Content with Colorized Cues -->
              <div class="script-content pa-3">
                <div
                  v-if="selectedItem.script || selectedItem.script_content"
                  class="script-text"
                  v-html="processedScriptContent"
                ></div>
                <div v-else class="text-medium-emphasis text-center py-8">
                  <v-icon size="48" class="mb-2">mdi-text-box-remove-outline</v-icon>
                  <div class="text-body-2">No script content</div>
                </div>
              </div>
            </template>

            <!-- No Selection State -->
            <template v-else>
              <div class="d-flex flex-column justify-center align-center fill-height text-medium-emphasis pa-4">
                <v-icon size="48" class="mb-2">mdi-cursor-default-click</v-icon>
                <div class="text-body-2 text-center">
                  Select an item from the rundown<br/>to view its script content
                </div>
              </div>
            </template>
          </v-card-text>
        </v-card>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useSegmentLLMData } from '@/composables/useSegmentLLMData'
import { getColorValue, resolveVuetifyColor, getTextColorForBackground } from '@/utils/themeColorMap'
import draggable from 'vuedraggable'
import axios from 'axios'

export default {
  name: 'MetaExtraction',

  components: {
    draggable
  },

  props: {
    episode: {
      type: String,
      default: null
    }
  },

  setup(props) {
    const {
      getLLMData,
      extractLLMData,
      batchExtract,
      getStaleSegments
    } = useSegmentLLMData()

    // State
    const currentEpisode = ref(props.episode)
    const rundownItems = ref([])
    const loading = ref(false)
    const selectedItemId = ref(null)
    const extractingItems = ref(new Set())
    const batchExtracting = ref(false)
    const checkingStale = ref(false)
    const staleSegments = ref([])

    // Meta extraction settings - item types eligible for extraction
    const eligibleItemTypes = ref([
      'segment', 'coldopen', 'interview', 'tease', 'pkg', 'vox', 'sot', 'nat'
    ])

    // Local display order for visual drag-and-drop (doesn't affect actual rundown order)
    const localDisplayOrder = ref([])

    // Watch for prop changes - immediate: true ensures we catch the initial value
    watch(() => props.episode, (newEpisode) => {
      if (newEpisode && newEpisode !== currentEpisode.value) {
        currentEpisode.value = newEpisode
        selectedItemId.value = null
        loadRundownItems()
        staleSegments.value = []
      }
    }, { immediate: true })

    // Also check sessionStorage for episode changes (fallback)
    function checkEpisode() {
      const stored = sessionStorage.getItem('currentEpisode')
      if (stored !== currentEpisode.value && !props.episode) {
        currentEpisode.value = stored
        selectedItemId.value = null
        if (stored) {
          loadRundownItems()
          staleSegments.value = []
        }
      }
    }

    // Load meta extraction settings
    async function loadExtractionSettings() {
      try {
        const response = await axios.get('/api/settings/meta_extraction', {
          headers: getAuthHeaders()
        })
        if (response.data?.item_types) {
          eligibleItemTypes.value = response.data.item_types
        }
      } catch (error) {
        console.error('Failed to load meta extraction settings:', error)
        // Keep defaults on error
      }
    }

    // Computed - filter items based on eligible types
    const filteredRundownItems = computed(() => {
      return rundownItems.value.filter(item => {
        const itemType = (item.type || item.type || '').toLowerCase()
        return eligibleItemTypes.value.includes(itemType)
      })
    })

    const selectedItem = computed(() => {
      if (!selectedItemId.value) return null
      return rundownItems.value.find(item => item.id === selectedItemId.value) || null
    })

    const segmentCount = computed(() => {
      return filteredRundownItems.value.length
    })

    const extractedCount = computed(() => {
      return filteredRundownItems.value.filter(item => item.llm_status === 'completed').length
    })

    const pendingCount = computed(() => {
      return filteredRundownItems.value.filter(item => item.llm_status === 'none' || !item.llm_status).length
    })

    // Combined entities list for unified table display
    const allEntities = computed(() => {
      if (!selectedItem.value?.llm_data) return []

      const entities = []
      const llmData = selectedItem.value.llm_data

      // Add people
      if (llmData.extracted_people?.length) {
        for (const person of llmData.extracted_people) {
          entities.push({
            entityType: 'Person',
            name: person.name,
            role: person.role,
            relation_to_story: person.relation_to_story || person.relationToStory || person.context,
            x_handle: person.x_handle || person.twitter_handle || person.handle,
            ...person
          })
        }
      }

      // Add organizations
      if (llmData.extracted_organizations?.length) {
        for (const org of llmData.extracted_organizations) {
          entities.push({
            entityType: 'Organization',
            name: org.name,
            type: org.type,
            relation_to_story: org.relation_to_story || org.relationToStory || org.context,
            x_handle: org.x_handle || org.twitter_handle || org.handle,
            ...org
          })
        }
      }

      // Add institutions
      if (llmData.extracted_institutions?.length) {
        for (const inst of llmData.extracted_institutions) {
          entities.push({
            entityType: 'Institution',
            name: inst.name,
            type: inst.type,
            relation_to_story: inst.relation_to_story || inst.relationToStory || inst.context,
            x_handle: inst.x_handle || inst.twitter_handle || inst.handle,
            ...inst
          })
        }
      }

      return entities
    })

    // Sync localDisplayOrder with filteredRundownItems for visual-only drag-and-drop
    watch(filteredRundownItems, (newItems) => {
      localDisplayOrder.value = [...newItems]
    }, { immediate: true })

    // Processed script content with colorized cue blocks
    const processedScriptContent = computed(() => {
      if (!selectedItem.value) return ''
      const rawContent = selectedItem.value.script || selectedItem.value.script_content || ''
      if (!rawContent) return ''

      // Parse and colorize cue blocks
      // Pattern: <!-- Begin Cue -->...[Type: XXX]...<!-- End Cue -->
      const cueBlockPattern = /<!-- Begin Cue -->([\s\S]*?)<!-- End Cue -->/g

      // Get episode number for building image paths - pad to 4 digits
      const rawEpisodeNum = currentEpisode.value || ''
      const episodeNum = rawEpisodeNum.toString().padStart(4, '0')

      return rawContent.replace(cueBlockPattern, (match, cueContent) => {
        // Extract cue type from [Type: XXX] field
        const typeMatch = cueContent.match(/\[Type:\s*([^\]]+)\]/i)
        const cueType = typeMatch ? typeMatch[1].trim().toLowerCase() : 'unknown'
        const cueTypeUpper = cueType.toUpperCase()

        // Extract other key fields
        const slugMatch = cueContent.match(/\[Slug:\s*([^\]]+)\]/i)
        const durationMatch = cueContent.match(/\[Duration:\s*([^\]]+)\]/i)
        const labelMatch = cueContent.match(/\[Label:\s*([^\]]+)\]/i)
        const thumbnailMatch = cueContent.match(/\[ThumbnailURL?:\s*([^\]]+)\]/i)
        const mediaUrlMatch = cueContent.match(/\[MediaURL?:\s*([^\]]+)\]/i)

        // Extract embedded image tag for GFX/IMG (handles both single and double quotes)
        const imgMatch = cueContent.match(/<img[^>]+src=["']([^"']+)["'][^>]*>/i)

        const slug = slugMatch ? slugMatch[1].trim() : ''
        const duration = durationMatch ? durationMatch[1].trim() : ''
        const label = labelMatch ? labelMatch[1].trim() : slug

        // Get color for this cue type
        const bgColor = getBackgroundColorForItem(cueType)
        const textColor = getTextColorForBackground(bgColor)

        // Build colorized cue block with media
        const displayLabel = label || slug || cueTypeUpper

        // Helper to fix relative paths - converts to absolute episode paths
        const fixPath = (path) => {
          if (!path || path === 'Pending...' || path.trim() === '') return ''
          // Remove any quotes that might be left
          path = path.replace(/["']/g, '')
          // Convert relative paths to absolute
          if (path.startsWith('../assets/')) {
            return `/episodes/${episodeNum}/assets/${path.replace('../assets/', '')}`
          }
          if (path.startsWith('./assets/')) {
            return `/episodes/${episodeNum}/assets/${path.replace('./assets/', '')}`
          }
          if (path.startsWith('assets/')) {
            return `/episodes/${episodeNum}/${path}`
          }
          if (!path.startsWith('/') && !path.startsWith('http')) {
            return `/episodes/${episodeNum}/${path}`
          }
          return path
        }

        // Determine image source based on cue type
        let imageHtml = ''
        const imageCueTypes = ['gfx', 'img', 'image', 'graphic', 'quote']

        // Get image source - try img tag first, then mediaUrl
        let imageSrc = ''
        if (imgMatch) {
          imageSrc = imgMatch[1]
        } else if (mediaUrlMatch) {
          imageSrc = mediaUrlMatch[1].trim()
        }

        // For image-type cues, always try to show the image
        if (imageCueTypes.includes(cueType) && imageSrc) {
          imageSrc = fixPath(imageSrc)
          imageHtml = `<img src="${imageSrc}" class="cue-image" alt="${displayLabel}">`
        } else if (thumbnailMatch && thumbnailMatch[1].trim()) {
          // For video cues, use thumbnail if available
          const thumbnailSrc = fixPath(thumbnailMatch[1].trim())
          imageHtml = `<img src="${thumbnailSrc}" class="cue-thumbnail" alt="${displayLabel}">`
        }

        // Build compact HTML
        const durationHtml = duration && duration !== 'Pending...' ? `<span class="cue-dur">${duration}</span>` : ''

        // Always show the image container for image-type cues (even if loading fails, CSS will handle it)
        const showImageContainer = imageCueTypes.includes(cueType) || imageHtml

        return `<div class="cue-block cue-${cueType}" style="background:${bgColor};color:${textColor}">${showImageContainer ? `<div class="cue-img">${imageHtml || '<span class="cue-img-placeholder">IMG</span>'}</div>` : ''}<div class="cue-info"><span class="cue-type">${cueTypeUpper}</span><span class="cue-slug">${displayLabel}</span>${durationHtml}</div></div>`
      })
    })

    // Methods
    function getAuthHeaders() {
      const token = localStorage.getItem('auth-token')
      return token ? { 'Authorization': `Bearer ${token}` } : {}
    }

    async function loadRundownItems() {
      if (!currentEpisode.value) return

      loading.value = true
      try {
        const response = await axios.get(`/api/episodes/${currentEpisode.value}/rundown`, {
          headers: getAuthHeaders()
        })

        if (response.data) {
          const items = response.data.items || response.data || []

          // Load LLM data for each item
          for (const item of items) {
            const llmResult = await getLLMData(item.id, true)
            item.llm_status = llmResult?.has_data
              ? (llmResult.stale ? 'stale' : 'completed')
              : 'none'
            item.llm_data = llmResult?.data || null
          }

          rundownItems.value = items
        }
      } catch (error) {
        console.error('Failed to load rundown items:', error)
      } finally {
        loading.value = false
      }
    }

    async function checkAllStale() {
      if (!currentEpisode.value) return

      checkingStale.value = true
      try {
        const stale = await getStaleSegments(currentEpisode.value)
        staleSegments.value = stale

        // Update items with stale status
        for (const item of rundownItems.value) {
          const isStale = stale.some(s => s.rundown_item_id === item.id)
          if (isStale && item.llm_status !== 'none') {
            item.llm_status = 'stale'
          }
        }
      } catch (error) {
        console.error('Failed to check stale status:', error)
      } finally {
        checkingStale.value = false
      }
    }

    async function extractSingle(item) {
      extractingItems.value.add(item.id)
      try {
        const result = await extractLLMData(item.id, {
          model: 'mistral:7b',
          force: false,
          notify: true
        })

        if (result) {
          item.llm_status = 'completed'
          item.llm_data = result.data
        }
      } catch (error) {
        console.error('Extraction failed:', error)
      } finally {
        extractingItems.value.delete(item.id)
      }
    }

    async function extractAll() {
      if (filteredRundownItems.value.length === 0) return

      batchExtracting.value = true
      try {
        const itemIds = filteredRundownItems.value.map(item => item.id)
        await batchExtract(itemIds, { model: 'mistral:7b' })

        // Reload data
        await loadRundownItems()
      } catch (error) {
        console.error('Batch extraction failed:', error)
      } finally {
        batchExtracting.value = false
      }
    }

    async function extractAllStale() {
      if (staleSegments.value.length === 0) return

      batchExtracting.value = true
      try {
        const itemIds = staleSegments.value.map(s => s.rundown_item_id)
        await batchExtract(itemIds, { model: 'mistral:7b', force: true })

        // Reload data
        await loadRundownItems()
        staleSegments.value = []
      } catch (error) {
        console.error('Batch extraction failed:', error)
      } finally {
        batchExtracting.value = false
      }
    }

    function selectItem(item) {
      selectedItemId.value = item.id
    }

    function onItemSelect(selected) {
      selectedItemId.value = selected[0] || null
    }

    function clearSelection() {
      selectedItemId.value = null
    }

    function refreshData() {
      loadRundownItems()
      staleSegments.value = []
    }

    function getTypeIcon(type) {
      const icons = {
        segment: 'mdi-text-box',
        interview: 'mdi-account-voice',
        discussion: 'mdi-forum',
        pkg: 'mdi-package-variant',
        vox: 'mdi-microphone',
        sot: 'mdi-message-video',
        nat: 'mdi-nature',
        ad: 'mdi-advertisements',
        promo: 'mdi-bullhorn',
        trans: 'mdi-transition',
        bump: 'mdi-music',
        sting: 'mdi-music-note'
      }
      return icons[type?.toLowerCase()] || 'mdi-file-document'
    }

    function getTypeColor(type) {
      const colors = {
        segment: 'primary',
        interview: 'blue',
        discussion: 'indigo',
        pkg: 'cyan',
        vox: 'teal',
        sot: 'green',
        nat: 'light-green',
        ad: 'amber',
        promo: 'orange',
        trans: 'grey',
        bump: 'purple',
        sting: 'pink'
      }
      return colors[type?.toLowerCase()] || 'grey'
    }

    function getStatusColor(status) {
      const colors = {
        completed: 'success',
        stale: 'warning',
        processing: 'info',
        failed: 'error',
        none: 'grey-darken-2'
      }
      return colors[status] || 'grey-darken-2'
    }

    function getStatusIconColor(status) {
      const colors = {
        completed: 'white',
        stale: 'black',
        processing: 'white',
        failed: 'white',
        none: 'grey'
      }
      return colors[status] || 'grey'
    }

    function getStatusIcon(status) {
      const icons = {
        completed: 'mdi-check',
        stale: 'mdi-alert',
        processing: 'mdi-loading',
        failed: 'mdi-close',
        none: 'mdi-circle-outline'
      }
      return icons[status] || 'mdi-circle-outline'
    }

    function formatDate(dateStr) {
      if (!dateStr) return 'Never'
      return new Date(dateStr).toLocaleString()
    }

    function formatDurationCompact(duration) {
      if (!duration) return '--:--'
      // Handle various duration formats
      const str = String(duration)
      // If it's already in MM:SS or HH:MM:SS format
      if (str.includes(':')) {
        const parts = str.split(':')
        if (parts.length >= 2) {
          // Return MM:SS format
          const mins = parts.length === 3 ? parts[1] : parts[0]
          const secs = parts.length === 3 ? parts[2] : parts[1]
          return `${mins}:${secs.substring(0, 2)}`
        }
      }
      return str.substring(0, 5)
    }

    // Color functions matching RundownPanel style
    function getBackgroundColorForItem(type) {
      if (!type) return 'rgba(158, 158, 158, 0.15)'
      const colorValue = getColorValue(type.toLowerCase()) || 'grey'
      const resolvedColor = resolveVuetifyColor(colorValue)
      return resolvedColor
    }

    function getTextColorForItem(type) {
      if (!type) return '#ffffff'
      // Get the background color and calculate readable text color
      const bgColor = getBackgroundColorForItem(type)
      return getTextColorForBackground(bgColor)
    }

    function getSelectionColor() {
      const selectionValue = getColorValue('selection') || 'warning'
      return resolveVuetifyColor(selectionValue)
    }

    function getSelectionTextColor() {
      // Get text color for selection background
      const selectionBg = getSelectionColor()
      return getTextColorForBackground(selectionBg)
    }

    // Legacy aliases for backwards compatibility
    function getItemBackgroundColor(itemType) {
      return getBackgroundColorForItem(itemType)
    }

    function getItemTextColor(itemType) {
      return getTextColorForItem(itemType)
    }

    // Entity type helpers for unified table
    function getEntityIcon(entityType) {
      const icons = {
        'Person': 'mdi-account',
        'Organization': 'mdi-domain',
        'Institution': 'mdi-bank'
      }
      return icons[entityType] || 'mdi-help-circle'
    }

    function getEntityColor(entityType) {
      const colors = {
        'Person': 'blue',
        'Organization': 'purple',
        'Institution': 'teal'
      }
      return colors[entityType] || 'grey'
    }

    // Setup interval to check for episode changes (fallback for sessionStorage)
    let episodeCheckInterval = null

    onMounted(async () => {
      // Load extraction settings first
      await loadExtractionSettings()

      if (props.episode) {
        currentEpisode.value = props.episode
        loadRundownItems()
      } else {
        checkEpisode()
        episodeCheckInterval = setInterval(checkEpisode, 1000)
      }
    })

    onUnmounted(() => {
      if (episodeCheckInterval) {
        clearInterval(episodeCheckInterval)
      }
    })

    return {
      // State
      currentEpisode,
      rundownItems,
      filteredRundownItems,
      eligibleItemTypes,
      loading,
      selectedItemId,
      selectedItem,
      extractingItems,
      batchExtracting,
      checkingStale,
      staleSegments,
      localDisplayOrder,

      // Computed
      segmentCount,
      extractedCount,
      pendingCount,
      processedScriptContent,
      allEntities,

      // Methods
      loadRundownItems,
      loadExtractionSettings,
      checkAllStale,
      extractSingle,
      extractAll,
      extractAllStale,
      selectItem,
      onItemSelect,
      clearSelection,
      refreshData,
      getTypeIcon,
      getTypeColor,
      getStatusColor,
      getStatusIconColor,
      getStatusIcon,
      formatDate,
      formatDurationCompact,
      // Color functions
      getBackgroundColorForItem,
      getTextColorForItem,
      getSelectionColor,
      getSelectionTextColor,
      getItemBackgroundColor,
      getItemTextColor,
      // Entity helpers
      getEntityIcon,
      getEntityColor
    }
  }
}
</script>

<style scoped>
.meta-extraction {
  height: 100%;
  width: 100%;
}

.fill-height {
  height: 100%;
}

.left-column {
  min-width: 300px;
}

.middle-column {
  min-width: 300px;
}

.right-column {
  min-width: 350px;
}

/* GLOBAL RULE: Eliminate rounded corners in rundown panel */
.rundown-panel-card *,
.rundown-panel-card {
  border-radius: 0 !important;
}

.rundown-title {
  border-bottom: none;
  min-height: 40px;
}

.stats-bar {
  font-size: 11px;
}

/* Rundown List Styling */
.rundown-list {
  background: rgb(var(--v-theme-surface));
}

.rundown-headers {
  display: grid;
  grid-template-columns: 60px 50px 1fr 50px 32px;
  gap: 4px;
  padding: 6px 8px;
  font-weight: 600;
  font-size: 10px;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  position: sticky;
  top: 0;
  background: rgb(var(--v-theme-surface));
  z-index: 1;
}

.rundown-items-container {
  padding: 2px;
}

/* RundownPanel-style item row */
.rundown-item-row {
  display: grid;
  grid-template-columns: 60px 50px 1fr 50px 32px;
  gap: 4px;
  align-items: center;
  padding: 0;
  margin: 0;
  min-height: 2.5em;
  cursor: pointer;
  border-bottom: 0.5px solid rgba(255, 255, 255, 0.08);
  transition: background-color 0.2s ease, transform 0.2s ease;
  position: relative;
}

.rundown-item-row:hover:not(.selected-item) {
  transform: translateX(-8px);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}

/* Selected item - matches RundownPanel behavior */
.rundown-item-row.selected-item {
  z-index: 10;
  transform: translateX(-15px);
  min-height: 55px;
  border: 2px solid var(--selection-color, #FF9800);
  box-shadow: 0 4px 12px rgba(0,0,0,0.25);
  transition: all 0.2s ease;
  /* Background color set via inline style using getSelectionColor() */
}

.rundown-item-row.selected-item .index-cell {
  background-color: rgba(255, 255, 255, 0.25);
}

.rundown-item-row.selected-item .index-number {
  font-weight: bold;
  font-size: 13px;
}

.rundown-item-row.selected-item .type-label {
  font-weight: bold;
  font-size: 12px;
}

.rundown-item-row.selected-item .slug-text {
  font-weight: bold;
  font-size: 13px;
}

.rundown-item-row.llm-completed .index-cell::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: rgb(var(--v-theme-success));
}

.rundown-item-row.llm-stale .index-cell::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: rgb(var(--v-theme-warning));
}

/* Index Cell - matches RundownPanel index-number-cell */
.index-cell {
  background-color: rgba(255, 255, 255, 0.09);
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-width: 60px;
  position: relative;
  gap: 4px;
  padding: 0 4px;
}

.status-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background-color: #ff0000;
  z-index: 100;
}

.index-number {
  font-weight: normal;
  font-size: 11px;
  font-family: 'Roboto Mono', monospace;
  color: inherit;
}

.llm-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.llm-status-dot.status-completed {
  background: rgb(var(--v-theme-success));
  box-shadow: 0 0 4px rgb(var(--v-theme-success));
}

.llm-status-dot.status-stale {
  background: rgb(var(--v-theme-warning));
  box-shadow: 0 0 4px rgb(var(--v-theme-warning));
}

.llm-status-dot.status-processing {
  background: rgb(var(--v-theme-info));
  animation: pulse 1s infinite;
}

.llm-status-dot.status-failed {
  background: rgb(var(--v-theme-error));
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Type Cell */
.type-cell {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  padding-left: 4px;
}

.type-label {
  font-weight: normal;
  font-size: 11px;
  font-family: 'Roboto Mono', monospace;
}

/* Slug Cell */
.slug-cell {
  min-width: 0;
  overflow: hidden;
  display: flex;
  align-items: center;
}

.slug-text {
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Duration Cell */
.duration-cell {
  font-size: 11px;
  font-family: 'Roboto Mono', monospace;
  text-align: right;
  padding-right: 4px;
}

/* Action Cell */
.action-cell {
  display: flex;
  justify-content: center;
  opacity: 0.5;
  transition: opacity 0.15s;
}

.rundown-item-row:hover .action-cell {
  opacity: 1;
}

/* Drag-and-drop animation classes */
.ghost-item {
  opacity: 0.5;
  background: rgba(var(--v-theme-primary), 0.2) !important;
  border: 2px dashed rgba(var(--v-theme-primary), 0.5) !important;
}

.chosen-item {
  opacity: 0.9;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
  cursor: grabbing;
}

.drag-item {
  opacity: 0;
}

.rundown-items-container > * {
  cursor: grab;
}

.rundown-items-container > *:active {
  cursor: grabbing;
}

.episode-stats-card {
  background: linear-gradient(135deg, rgba(25, 118, 210, 0.1) 0%, rgba(25, 118, 210, 0.02) 100%);
}

.metadata-card {
  border-color: rgba(255, 255, 255, 0.1);
}

.quote-block {
  padding: 8px 12px;
  background: rgba(255, 193, 7, 0.1);
  border-left: 3px solid #ffc107;
  border-radius: 4px;
}

.batch-actions {
  max-width: 400px;
  margin: 0 auto;
}

/* Make v-list-item clickable cursor */
.v-list-item {
  cursor: pointer;
}

/* Hover effect for list items */
.v-list-item:hover {
  background: rgba(var(--v-theme-primary), 0.05);
}

/* Script Viewer Styling */
.script-viewer {
  background: rgb(var(--v-theme-surface));
}

.script-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.script-content {
  font-size: 13px;
  line-height: 1.6;
}

.script-text {
  color: rgba(255, 255, 255, 0.9);
}

.script-text :deep(p) {
  margin-bottom: 12px;
}

.script-text :deep(p:last-child) {
  margin-bottom: 0;
}

.script-text :deep(p.josh),
.script-text :deep(p.host) {
  color: #90CAF9;
  font-weight: 500;
}

.script-text :deep(p.guest) {
  color: #A5D6A7;
  font-style: italic;
}

.script-text :deep(strong),
.script-text :deep(b) {
  color: #FFF;
  font-weight: 600;
}

.script-text :deep(em),
.script-text :deep(i) {
  font-style: italic;
  color: rgba(255, 255, 255, 0.8);
}

/* ============================================
   Entity Table Styles
   ============================================ */
.entity-table {
  width: 100%;
}

.entity-header {
  display: grid;
  grid-template-columns: 100px 1fr 1fr 120px;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.entity-row {
  display: grid;
  grid-template-columns: 100px 1fr 1fr 120px;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background 0.15s;
}

.entity-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

.entity-row:last-child {
  border-bottom: none;
}

.entity-col {
  display: flex;
  align-items: center;
  min-width: 0;
}

.entity-type-col {
  gap: 4px;
}

.entity-type-label {
  font-size: 11px;
  font-weight: 500;
  text-transform: capitalize;
}

.entity-name-col {
  gap: 6px;
}

.entity-name {
  font-weight: 600;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.entity-relation-col {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.entity-handle-col {
  font-size: 12px;
}

.x-handle-link {
  color: #1DA1F2;
  text-decoration: none;
  font-weight: 500;
}

.x-handle-link:hover {
  text-decoration: underline;
}

/* Entity type row colors (subtle left border) */
.entity-row.entity-type-Person {
  border-left: 3px solid #2196F3;
}

.entity-row.entity-type-Organization {
  border-left: 3px solid #9C27B0;
}

.entity-row.entity-type-Institution {
  border-left: 3px solid #009688;
}

/* ============================================
   Cue Block Styles (Simplified - no nested borders)
   ============================================ */
.script-text :deep(.cue-block) {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  margin: 8px 0;
  font-family: 'Roboto Mono', monospace;
  font-size: 11px;
  /* Simple left accent, no full border */
  border-left: 3px solid currentColor;
  background: rgba(0, 0, 0, 0.15);
}

/* Cue image container */
.script-text :deep(.cue-img) {
  flex-shrink: 0;
  width: 60px;
  height: 40px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.script-text :deep(.cue-image),
.script-text :deep(.cue-thumbnail) {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.script-text :deep(.cue-img-placeholder) {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 600;
}

/* Cue info - inline layout */
.script-text :deep(.cue-info) {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.script-text :deep(.cue-type) {
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  background: rgba(0, 0, 0, 0.2);
  flex-shrink: 0;
}

.script-text :deep(.cue-slug) {
  flex: 1;
  font-size: 11px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.script-text :deep(.cue-dur) {
  font-size: 10px;
  opacity: 0.6;
  flex-shrink: 0;
}

/* GFX cues with larger images */
.script-text :deep(.cue-gfx) .cue-img {
  width: 70px;
  height: 44px;
}

/* Legacy cue marker support - simplified */
.script-text :deep([class*="cue"]:not(.cue-block):not(.cue-img):not(.cue-info):not(.cue-type):not(.cue-slug):not(.cue-dur):not(.cue-image):not(.cue-thumbnail)),
.script-text :deep(.cue-marker) {
  background: rgba(255, 193, 7, 0.1);
  border-left: 3px solid #FFC107;
  padding: 6px 10px;
  margin: 6px 0;
  font-family: 'Roboto Mono', monospace;
  font-size: 11px;
}
</style>
