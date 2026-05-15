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
            <v-spacer />
            <v-btn
              color="primary"
              variant="tonal"
              size="x-small"
              prepend-icon="mdi-brain"
              :disabled="filteredRundownItems.length === 0"
              :loading="batchExtracting"
              @click="rerunPhase1All"
            >
              Phase 1 ({{ filteredRundownItems.length }})
            </v-btn>
            <v-btn
              color="purple"
              variant="tonal"
              size="x-small"
              prepend-icon="mdi-creation"
              :disabled="phase2EligibleItems.length === 0"
              :loading="phase2BatchRunning"
              @click="triggerPhase2Batch"
            >
              Phase 2 ({{ phase2EligibleItems.length }})
            </v-btn>
            <v-btn
              v-if="phase2CompletedCount > 0"
              color="purple"
              variant="text"
              size="x-small"
              prepend-icon="mdi-refresh"
              :loading="phase2BatchRunning"
              @click="rerunPhase2All"
              title="Re-run Phase 2 on every segment that already has Phase 2 data"
            >
              Re-run P2 ({{ phase2CompletedCount }})
            </v-btn>
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

                  <!-- Extract Buttons (Phase 1 + Phase 2 always side-by-side) -->
                  <div class="action-cell">
                    <v-btn
                      icon
                      variant="text"
                      size="x-small"
                      density="compact"
                      :color="item.llm_status === 'completed' ? 'success' : 'default'"
                      @click.stop="extractSingle(item)"
                      :loading="extractingItems.has(item.id)"
                    >
                      <v-icon size="14">mdi-brain</v-icon>
                      <v-tooltip activator="parent" location="left">
                        {{ item.llm_status === 'completed' ? 'Re-run Phase 1' : 'Run Phase 1 (Ollama)' }}
                      </v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="x-small"
                      density="compact"
                      :color="phase2StatusOf(item) === 'completed' ? 'purple' : 'default'"
                      :disabled="item.llm_status !== 'completed' && phase2StatusOf(item) !== 'completed'"
                      :loading="phase2Pending.has(item.id)"
                      @click.stop="triggerPhase2(item)"
                    >
                      <v-icon size="14">mdi-creation</v-icon>
                      <v-tooltip activator="parent" location="left">
                        {{
                          item.llm_status !== 'completed' ? 'Phase 1 must complete first'
                          : phase2StatusOf(item) === 'completed' ? 'Re-run Phase 2 (Grok)'
                          : 'Run Phase 2 (Grok)'
                        }}
                      </v-tooltip>
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
                {{ selectedItem.llm_status === 'completed' ? 'Re-extract Phase 1' : 'Extract Phase 1' }}
              </v-btn>
              <v-btn
                color="purple"
                variant="tonal"
                size="small"
                prepend-icon="mdi-creation"
                :disabled="selectedItem.llm_status !== 'completed' || phase2Pending.has(selectedItem.id)"
                :loading="phase2Pending.has(selectedItem.id)"
                @click="triggerPhase2(selectedItem)"
              >
                {{ phase2StatusOf(selectedItem) === 'completed' ? 'Re-run Phase 2 (Grok)' : 'Run Phase 2 (Grok)' }}
              </v-btn>
              <v-chip
                v-if="phase2StatusOf(selectedItem) && phase2StatusOf(selectedItem) !== 'not_started'"
                :color="phase2ChipColor(phase2StatusOf(selectedItem))"
                size="small"
                variant="flat"
              >
                <v-icon start size="x-small">{{ phase2ChipIcon(phase2StatusOf(selectedItem)) }}</v-icon>
                Phase 2: {{ phase2StatusOf(selectedItem) }}
              </v-chip>
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
                    <table v-if="allEntities.length" class="entity-table">
                      <thead>
                        <tr>
                          <th class="entity-type-col">Type</th>
                          <th class="entity-name-col">Name</th>
                          <th class="entity-role-col">Role / Sub-type</th>
                          <th class="entity-relation-col">Relation to Story</th>
                          <th class="entity-handle-col">X Handle</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="(entity, idx) in allEntities"
                          :key="idx"
                          :class="['entity-row-clickable', 'entity-type-' + entity.entityType]"
                          @click="openEntityModal(entity)"
                        >
                          <td class="entity-type-col">
                            <v-icon size="14" class="mr-1" :color="getEntityColor(entity.entityType)">
                              {{ getEntityIcon(entity.entityType) }}
                            </v-icon>
                            <span class="entity-type-label">{{ entity.entityType }}</span>
                          </td>
                          <td class="entity-name-col">
                            <span class="entity-name">{{ entity.name }}</span>
                            <v-icon
                              v-if="entity.has_phase2"
                              size="12"
                              color="purple"
                              class="ml-1"
                              :title="entity.added_by_phase2 ? 'Added by Phase 2 (Grok)' : 'Enriched by Phase 2 (Grok)'"
                            >mdi-creation</v-icon>
                          </td>
                          <td class="entity-role-col">
                            <v-chip
                              v-if="entity.role || entity.type"
                              size="x-small"
                              variant="outlined"
                            >
                              {{ entity.role || entity.type }}
                            </v-chip>
                            <span v-else class="text-medium-emphasis">—</span>
                          </td>
                          <td class="entity-relation-col">
                            {{ entity.relation_to_story || entity.relationToStory || entity.context || '—' }}
                          </td>
                          <td class="entity-handle-col">
                            <a
                              v-if="entity.x_handle || entity.twitter_handle || entity.handle"
                              :href="'https://x.com/' + (entity.x_handle || entity.twitter_handle || entity.handle).replace('@', '')"
                              target="_blank"
                              class="x-handle-link"
                              @click.stop
                            >
                              @{{ (entity.x_handle || entity.twitter_handle || entity.handle).replace('@', '') }}
                              <v-icon
                                v-if="entity.x_verified"
                                size="12"
                                color="info"
                                class="ml-1"
                                title="Verified via X API"
                              >mdi-check-decagram</v-icon>
                            </a>
                            <span v-else class="text-medium-emphasis">—</span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
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

    <!-- Entity detail modal (Phase 2 enriched view) -->
    <v-dialog v-model="entityModalOpen" max-width="780" scrollable>
      <v-card v-if="entityModalEntity">
        <v-card-title class="d-flex align-center py-3">
          <v-avatar
            v-if="entityModalAvatar"
            size="32"
            class="mr-2"
          >
            <v-img :src="entityModalAvatar" />
          </v-avatar>
          <v-icon
            v-else
            start
            :color="getEntityColor(entityModalEntity.entityType)"
          >{{ getEntityIcon(entityModalEntity.entityType) }}</v-icon>
          <span class="text-truncate">{{ entityModalEntity.name }}</span>
          <v-chip
            v-if="entityModalEnriched"
            color="purple"
            size="small"
            variant="tonal"
            class="ml-2"
          >
            <v-icon start size="x-small">mdi-creation</v-icon>
            Phase 2
          </v-chip>
          <v-chip
            v-else
            color="grey"
            size="small"
            variant="tonal"
            class="ml-2"
          >Phase 1 only</v-chip>
          <v-spacer />
          <v-btn icon variant="text" size="small" @click="entityModalOpen = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4" style="max-height: 70vh;">
          <!-- If Phase 2 hasn't run on this segment -->
          <v-alert
            v-if="!entityModalEnriched && phase2StatusOf(selectedItem) !== 'completed'"
            type="info"
            variant="tonal"
            class="mb-4"
            density="compact"
          >
            Phase 2 enrichment hasn't run on this segment yet. Click <strong>Run Phase 2 (Grok)</strong> in the segment toolbar to fetch verified roles, social handles, bios, and timeline data.
          </v-alert>

          <!-- Verified role / what we do -->
          <div class="mb-3">
            <div class="text-caption font-weight-bold text-uppercase mb-1">
              {{ entityModalEntity.entityType === 'Person' ? 'Current Role (Verified)' : 'What We Do' }}
            </div>
            <div class="text-body-2">
              {{
                entityModalEnriched?.current_role_verified
                  || entityModalEnriched?.what_we_do
                  || entityModalEntity.role
                  || entityModalEntity.type
                  || '—'
              }}
            </div>
          </div>

          <!-- Bio / what we do (long form) -->
          <div v-if="entityModalEnriched?.bio_short || entityModalEnriched?.what_we_do" class="mb-3">
            <div class="text-caption font-weight-bold text-uppercase mb-1">Bio</div>
            <div class="text-body-2">
              {{ entityModalEnriched.bio_short || entityModalEnriched.what_we_do }}
            </div>
          </div>

          <!-- Pronunciation -->
          <div v-if="entityModalEnriched?.pronunciation" class="mb-3">
            <div class="text-caption font-weight-bold text-uppercase mb-1">Pronunciation</div>
            <div class="text-body-2 font-italic">{{ entityModalEnriched.pronunciation }}</div>
          </div>

          <!-- Org/Institution-specific facts -->
          <v-row v-if="entityModalEntity.entityType !== 'Person'" dense class="mb-2">
            <v-col v-if="entityModalEnriched?.founded_year" cols="6">
              <div class="text-caption font-weight-bold text-uppercase">Founded</div>
              <div class="text-body-2">{{ entityModalEnriched.founded_year }}</div>
            </v-col>
            <v-col v-if="entityModalEnriched?.headquarters" cols="6">
              <div class="text-caption font-weight-bold text-uppercase">HQ</div>
              <div class="text-body-2">{{ entityModalEnriched.headquarters }}</div>
            </v-col>
            <v-col v-if="entityModalEnriched?.parent_org" cols="6">
              <div class="text-caption font-weight-bold text-uppercase">Parent</div>
              <div class="text-body-2">{{ entityModalEnriched.parent_org }}</div>
            </v-col>
            <v-col v-if="entityModalEnriched?.jurisdiction" cols="6">
              <div class="text-caption font-weight-bold text-uppercase">Jurisdiction</div>
              <div class="text-body-2">{{ entityModalEnriched.jurisdiction }}</div>
            </v-col>
          </v-row>

          <!-- Founders -->
          <div v-if="entityModalEnriched?.founders?.length" class="mb-3">
            <div class="text-caption font-weight-bold text-uppercase mb-1">Founders</div>
            <div class="text-body-2">{{ entityModalEnriched.founders.join(', ') }}</div>
          </div>

          <!-- Current leadership -->
          <div v-if="entityModalEnriched?.current_leadership?.length" class="mb-3">
            <div class="text-caption font-weight-bold text-uppercase mb-1">Leadership</div>
            <div class="text-body-2">
              <div v-for="(lead, i) in entityModalEnriched.current_leadership" :key="i">
                {{ lead.name }} <span class="text-medium-emphasis">— {{ lead.title }}</span>
              </div>
            </div>
          </div>

          <!-- Current head (institutions) -->
          <div v-if="entityModalEnriched?.current_head?.name" class="mb-3">
            <div class="text-caption font-weight-bold text-uppercase mb-1">Current Head</div>
            <div class="text-body-2">
              {{ entityModalEnriched.current_head.name }}
              <span class="text-medium-emphasis">— {{ entityModalEnriched.current_head.title }}</span>
            </div>
          </div>

          <!-- Refined relation to story -->
          <div class="mb-3">
            <div class="text-caption font-weight-bold text-uppercase mb-1">Relation to Story</div>
            <div class="text-body-2">
              {{
                entityModalEnriched?.relation_to_story_refined
                  || entityModalEntity.relation_to_story
                  || entityModalEntity.relationToStory
                  || entityModalEntity.context
                  || '—'
              }}
            </div>
          </div>

          <!-- Conflicts of interest -->
          <v-alert
            v-if="entityModalEnriched?.conflicts_with_story"
            type="warning"
            variant="tonal"
            density="compact"
            class="mb-3"
          >
            <strong>Possible conflict of interest:</strong> {{ entityModalEnriched.conflicts_with_story }}
          </v-alert>

          <!-- Social handles -->
          <div class="mb-3">
            <div class="text-caption font-weight-bold text-uppercase mb-2">Social Handles</div>
            <div v-if="hasAnySocialHandle(entityModalEnriched)" class="d-flex flex-wrap ga-2">
              <a
                v-for="link in renderedSocialLinks(entityModalEnriched)"
                :key="link.platform"
                :href="link.url"
                target="_blank"
                class="social-pill"
                :class="{ 'social-pill-verified': link.verified }"
              >
                <v-icon size="14" class="mr-1">{{ link.icon }}</v-icon>
                {{ link.label }}
                <v-icon v-if="link.verified" size="14" color="info" class="ml-1">mdi-check-decagram</v-icon>
              </a>
            </div>
            <div v-else class="text-medium-emphasis text-body-2">
              No verified handles
              <span v-if="entityModalEntity.x_handle">— Phase 1 had: <a :href="'https://x.com/' + entityModalEntity.x_handle.replace('@','')" target="_blank">@{{ entityModalEntity.x_handle.replace('@','') }}</a></span>
            </div>
          </div>

          <!-- X profile detail block (only when X-API verified) -->
          <v-card
            v-if="entityModalEnriched?.x_verified && entityModalEnriched?.x_profile"
            variant="outlined"
            class="mb-3"
          >
            <v-card-text class="py-3">
              <div class="d-flex align-center mb-2">
                <v-icon size="16" color="info" class="mr-1">mdi-check-decagram</v-icon>
                <span class="text-caption font-weight-bold text-uppercase">X Profile (verified via API)</span>
              </div>
              <div class="text-body-2 mb-1" v-if="entityModalEnriched.x_profile.description">
                {{ entityModalEnriched.x_profile.description }}
              </div>
              <div class="text-caption text-medium-emphasis d-flex flex-wrap ga-3">
                <span v-if="entityModalEnriched.x_profile.public_metrics">
                  {{ formatCount(entityModalEnriched.x_profile.public_metrics.followers_count) }} followers
                </span>
                <span v-if="entityModalEnriched.x_profile.public_metrics">
                  {{ formatCount(entityModalEnriched.x_profile.public_metrics.tweet_count) }} posts
                </span>
                <span v-if="entityModalEnriched.x_profile.location">
                  📍 {{ entityModalEnriched.x_profile.location }}
                </span>
                <span v-if="entityModalEnriched.x_profile.created_at">
                  Joined {{ entityModalEnriched.x_profile.created_at.slice(0, 10) }}
                </span>
              </div>
            </v-card-text>
          </v-card>

          <!-- Recent activity -->
          <div v-if="entityModalEnriched?.recent_activity?.length" class="mb-3">
            <div class="text-caption font-weight-bold text-uppercase mb-1">Recent Activity</div>
            <ul class="recent-activity">
              <li v-for="(act, i) in entityModalEnriched.recent_activity" :key="i">
                <span class="recent-date">{{ act.date }}</span>
                <span class="ml-2">{{ act.event }}</span>
                <a v-if="act.source_url" :href="act.source_url" target="_blank" class="ml-2">[source]</a>
              </li>
            </ul>
          </div>

          <!-- Reference links -->
          <div v-if="entityModalEnriched?.wikipedia_url || entityModalEnriched?.image_url || entityModalEnriched?.logo_url" class="mb-2">
            <div class="text-caption font-weight-bold text-uppercase mb-1">References</div>
            <a v-if="entityModalEnriched?.wikipedia_url" :href="entityModalEnriched.wikipedia_url" target="_blank" class="mr-3">Wikipedia</a>
            <a v-if="entityModalEnriched?.image_url" :href="entityModalEnriched.image_url" target="_blank" class="mr-3">Image</a>
            <a v-if="entityModalEnriched?.logo_url" :href="entityModalEnriched.logo_url" target="_blank">Logo</a>
          </div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useSegmentLLMData } from '@/composables/useSegmentLLMData'
import { getColorValue, resolveVuetifyColor, getTextColorForBackground } from '@/utils/themeColorMap'
import draggable from 'vuedraggable'
import axios from 'axios'
import { useToast } from 'vue-toastification'

const toast = useToast()

const props = defineProps({
  episode: {
    type: String,
    default: null
  }
})

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

// ===== Phase 2 (async Grok enrichment) state =====
// In-flight set: rundown item db_ids whose Phase 2 button is currently
// awaiting the network roundtrip OR is being polled for completion.
const phase2Pending = ref(new Set())
// Active polling timers keyed by db_id so we can cancel on unmount/switch.
const phase2PollTimers = new Map()
// Batch run flag (single shared spinner for the toolbar button).
const phase2BatchRunning = ref(false)

// ===== Entity detail modal state =====
const entityModalOpen = ref(false)
const entityModalEntity = ref(null)
// Resolved Phase 2 entry for the open entity (computed at click time).
const entityModalEnriched = ref(null)

// Meta extraction settings - item types eligible for extraction
const eligibleItemTypes = ref([
  'segment', 'coldopen', 'interview', 'tease', 'pkg', 'vox', 'sot', 'nat'
])
// Autorun flags pulled from the same /api/settings/meta_extraction endpoint.
// Phase 1 autorun fires extractSingle on every llm_status==='none' row
// after a rundown loads; Phase 2 autorun is server-side (chained inside
// the Phase 1 extractor) and we just respect its state here.
const autorunPhase1 = ref(false)
const autorunPhase2 = ref(false)

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
    autorunPhase1.value = !!response.data?.autorun_phase1
    autorunPhase2.value = !!response.data?.autorun_phase2
  } catch (error) {
    console.error('Failed to load meta extraction settings:', error)
    // Keep defaults on error
  }
}

// Fire Phase 1 (extractSingle) on every eligible item that hasn't been
// extracted yet. Sequenced — not parallel — so the local Ollama doesn't
// get hammered by 20 simultaneous requests, and so any per-item failure
// doesn't tear down the whole sweep.
async function autoRunPhase1Sweep() {
  if (!autorunPhase1.value) return
  const pending = filteredRundownItems.value.filter(it =>
    it.llm_status === 'none' || !it.llm_status
  )
  if (pending.length === 0) return
  toast.info(`Auto-running Phase 1 on ${pending.length} segment${pending.length === 1 ? '' : 's'}.`, { timeout: 4000 })
  for (const item of pending) {
    try {
      await extractSingle(item)
    } catch (err) {
      console.error('autorun phase 1 failed for', item.id, err)
    }
  }
  if (autorunPhase2.value) {
    toast.info('Phase 2 will follow automatically (server-side chain).', { timeout: 4000 })
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

const segmentCount = computed(() => { // eslint-disable-line no-unused-vars
  return filteredRundownItems.value.length
})

const extractedCount = computed(() => {
  return filteredRundownItems.value.filter(item => item.llm_status === 'completed').length
})

const pendingCount = computed(() => {
  return filteredRundownItems.value.filter(item => item.llm_status === 'none' || !item.llm_status).length
})

// Combined entities list for unified table display.
//
// Phase 2 (Grok) data SHADOWS Phase 1 (Ollama) for the three fields the
// table displays: role/title, relation_to_story, x_handle. We also union
// Phase 2-only entities (Phase 2 routinely finds 3-4× more) so the table
// reflects the full enriched view once Phase 2 has run.
const allEntities = computed(() => {
  if (!selectedItem.value?.llm_data) return []

  const llmData = selectedItem.value.llm_data
  const phase2 = llmData.phase2_data || {}

  // Build a name→Phase 2 entry index per entity bucket. Lower-case for
  // case-insensitive merging (Grok occasionally varies casing).
  const indexByName = (arr) => {
    const map = new Map()
    for (const e of (arr || [])) {
      if (e?.name) map.set(String(e.name).toLowerCase(), e)
    }
    return map
  }
  const p2People = indexByName(phase2.people)
  const p2Orgs = indexByName(phase2.organizations)
  const p2Insts = indexByName(phase2.institutions)

  // Pull Phase 2 overrides for a single entity (or null if not enriched).
  // Returns an object with the canonical display fields the table reads.
  const overlay = (phase2Entry) => {
    if (!phase2Entry) return null
    const xHandleP2 = phase2Entry.social_handles?.x
    return {
      role: phase2Entry.current_role_verified || null,
      type: phase2Entry.current_role_verified || null,
      relation_to_story: phase2Entry.relation_to_story_refined || null,
      x_handle: (xHandleP2 && xHandleP2 !== 'null') ? xHandleP2 : null,
      x_verified: !!phase2Entry.x_verified,
      phase2: phase2Entry,
    }
  }

  const seen = new Set()
  const entities = []

  // First pass: every Phase 1 entity, with Phase 2 overlay merged on top.
  const consume = (phase1List, entityType, phase2Map) => {
    for (const p1 of (phase1List || [])) {
      if (!p1?.name) continue
      const key = `${entityType}::${String(p1.name).toLowerCase()}`
      seen.add(key)
      const ov = overlay(phase2Map.get(String(p1.name).toLowerCase()))
      const baseRole = p1.role || p1.type
      const baseRelation = p1.relation_to_story || p1.relationToStory || p1.context
      const baseHandle = p1.x_handle || p1.twitter_handle || p1.handle
      entities.push({
        entityType,
        name: p1.name,
        // Phase 2 wins where present, else Phase 1.
        role: ov?.role || baseRole || null,
        type: ov?.type || p1.type || null,
        relation_to_story: ov?.relation_to_story || baseRelation || null,
        x_handle: ov?.x_handle || baseHandle || null,
        x_verified: ov?.x_verified || false,
        has_phase2: !!ov,
        ...p1,
        // Re-apply override fields after spread so they win.
        ...(ov ? {
          role: ov.role || baseRole || null,
          type: ov.type || p1.type || null,
          relation_to_story: ov.relation_to_story || baseRelation || null,
          x_handle: ov.x_handle || baseHandle || null,
          x_verified: ov.x_verified,
          has_phase2: true,
        } : {})
      })
    }
  }
  consume(llmData.extracted_people, 'Person', p2People)
  consume(llmData.extracted_organizations, 'Organization', p2Orgs)
  consume(llmData.extracted_institutions, 'Institution', p2Insts)

  // Second pass: Phase 2-only entities (Phase 1 missed them entirely).
  const consumeP2Only = (phase2Map, entityType) => {
    for (const [nameKey, p2] of phase2Map.entries()) {
      const key = `${entityType}::${nameKey}`
      if (seen.has(key)) continue
      const xHandle = p2.social_handles?.x
      entities.push({
        entityType,
        name: p2.name,
        role: p2.current_role_verified || null,
        type: p2.current_role_verified || null,
        relation_to_story: p2.relation_to_story_refined || null,
        x_handle: (xHandle && xHandle !== 'null') ? xHandle : null,
        x_verified: !!p2.x_verified,
        has_phase2: true,
        added_by_phase2: true,
      })
    }
  }
  consumeP2Only(p2People, 'Person')
  consumeP2Only(p2Orgs, 'Organization')
  consumeP2Only(p2Insts, 'Institution')

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
      // NOTE: rundown endpoint maps item.id = asset_id (string) for legacy compat;
      // the integer DB id needed by /api/segments/* is in item.db_id.
      for (const item of items) {
        const llmResult = await getLLMData(item.db_id, true)
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

  // After the rundown is fully loaded, kick the Phase 1 autorun sweep
  // (no-op when the setting is off). Fire-and-forget — runs in background.
  autoRunPhase1Sweep()
}

async function checkAllStale() { // eslint-disable-line no-unused-vars
  if (!currentEpisode.value) return

  checkingStale.value = true
  try {
    const stale = await getStaleSegments(currentEpisode.value)
    staleSegments.value = stale

    // Update items with stale status
    for (const item of rundownItems.value) {
      const isStale = stale.some(s => s.rundown_item_id === item.db_id)
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
    const result = await extractLLMData(item.db_id, {
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

// ===== Phase 2 (async Grok enrichment) =====

function phase2StatusOf(item) {
  return item?.llm_data?.phase2_status || 'not_started'
}

// Items where Phase 1 is done but Phase 2 hasn't been kicked off yet.
const phase2EligibleItems = computed(() => {
  return filteredRundownItems.value.filter(it => {
    if (it.llm_status !== 'completed') return false
    const s = phase2StatusOf(it)
    return s === 'not_started' || s === 'failed'
  })
})

// Items that already have a successful Phase 2 result (used by "Re-run P2 (N)").
const phase2CompletedCount = computed(() => {
  return filteredRundownItems.value.filter(it => phase2StatusOf(it) === 'completed').length
})

async function _runPhase2OnList(items, label) {
  if (items.length === 0) return
  phase2BatchRunning.value = true
  toast.info(`${label} — queueing ${items.length} segment${items.length === 1 ? '' : 's'} for Grok.`, { timeout: 5000 })
  let queued = 0
  for (const item of items) {
    try {
      await axios.post(`/api/segments/${item.db_id}/phase2`, {}, {
        headers: getAuthHeaders()
      })
      phase2Pending.value.add(item.id)
      pollPhase2Status(item)
      queued += 1
    } catch (err) {
      console.error('Phase 2 batch trigger failed for item', item.db_id, err)
    }
  }
  phase2BatchRunning.value = false
  if (queued < items.length) {
    toast.warning(`Queued ${queued} of ${items.length} — see console for failures.`)
  }
}

async function triggerPhase2Batch() {
  await _runPhase2OnList(phase2EligibleItems.value, 'Phase 2')
}

async function rerunPhase2All() {
  const items = filteredRundownItems.value.filter(it => phase2StatusOf(it) === 'completed')
  if (items.length === 0) {
    toast.info('No Phase 2-completed segments to re-run.')
    return
  }
  await _runPhase2OnList(items, 'Re-run Phase 2')
}

async function rerunPhase1All() {
  const items = filteredRundownItems.value
  if (items.length === 0) return
  batchExtracting.value = true
  toast.info(`Re-running Phase 1 (Ollama) on ${items.length} segment${items.length === 1 ? '' : 's'}.`, { timeout: 5000 })
  try {
    const itemIds = items.map(it => it.db_id)
    await batchExtract(itemIds, { force: true })
    await loadRundownItems()
    toast.success(`Phase 1 re-extraction complete (${items.length} segment${items.length === 1 ? '' : 's'}).`)
  } catch (err) {
    console.error('Phase 1 batch re-run failed:', err)
    toast.error(`Phase 1 re-run failed: ${err.message || err}`)
  } finally {
    batchExtracting.value = false
  }
}

function phase2ChipColor(status) {
  return ({
    queued: 'amber',
    running: 'amber',
    completed: 'purple',
    failed: 'error',
  })[status] || 'grey'
}

function phase2ChipIcon(status) {
  return ({
    queued: 'mdi-progress-clock',
    running: 'mdi-progress-clock',
    completed: 'mdi-creation',
    failed: 'mdi-alert-circle',
  })[status] || 'mdi-help-circle'
}

async function triggerPhase2(item) {
  if (!item || phase2Pending.value.has(item.id)) return
  if (item.llm_status !== 'completed') {
    toast.warning('Phase 1 must complete first before Phase 2 can run.')
    return
  }
  phase2Pending.value.add(item.id)
  try {
    await axios.post(`/api/segments/${item.db_id}/phase2`, {}, {
      headers: getAuthHeaders()
    })
    toast.info('Phase 2 enrichment started — Grok is verifying entities. This usually takes 30–90 seconds.', { timeout: 6000 })
    pollPhase2Status(item)
  } catch (err) {
    console.error('Phase 2 trigger failed:', err)
    toast.error(`Could not start Phase 2: ${err.response?.data?.detail || err.message}`)
    phase2Pending.value.delete(item.id)
  }
}

function pollPhase2Status(item) {
  // Clear any prior timer for this item
  if (phase2PollTimers.has(item.id)) {
    clearInterval(phase2PollTimers.get(item.id))
  }
  const intervalMs = 3500
  let elapsed = 0
  const maxElapsedMs = 5 * 60 * 1000  // 5 min hard ceiling

  const tick = async () => {
    elapsed += intervalMs
    try {
      const resp = await axios.get(`/api/segments/${item.db_id}/phase2`, {
        headers: getAuthHeaders()
      })
      const data = resp.data
      // Persist phase2 fields onto item.llm_data so the UI reflects status.
      if (item.llm_data) {
        item.llm_data.phase2_status = data.phase2_status
        item.llm_data.phase2_data = data.phase2_data || {}
        item.llm_data.phase2_completed_at = data.phase2_completed_at
        item.llm_data.phase2_started_at = data.phase2_started_at
        item.llm_data.phase2_model = data.phase2_model
        item.llm_data.phase2_error = data.phase2_error
      }
      if (data.phase2_status === 'completed') {
        clearInterval(phase2PollTimers.get(item.id))
        phase2PollTimers.delete(item.id)
        phase2Pending.value.delete(item.id)
        toast.success(`Phase 2 enrichment complete (${data.phase2_model || 'grok'}).`)
      } else if (data.phase2_status === 'failed') {
        clearInterval(phase2PollTimers.get(item.id))
        phase2PollTimers.delete(item.id)
        phase2Pending.value.delete(item.id)
        toast.error(`Phase 2 failed: ${data.phase2_error || 'unknown error'}`)
      } else if (elapsed >= maxElapsedMs) {
        clearInterval(phase2PollTimers.get(item.id))
        phase2PollTimers.delete(item.id)
        phase2Pending.value.delete(item.id)
        toast.warning('Phase 2 is taking longer than expected. Refresh to check status later.')
      }
    } catch (err) {
      console.error('Phase 2 poll failed:', err)
    }
  }
  const timer = setInterval(tick, intervalMs)
  phase2PollTimers.set(item.id, timer)
}

// ===== Entity modal helpers =====

function findPhase2Entry(entity) {
  const p2 = selectedItem.value?.llm_data?.phase2_data || {}
  const buckets = {
    Person: p2.people,
    Organization: p2.organizations,
    Institution: p2.institutions,
  }
  const list = buckets[entity.entityType] || []
  return list.find(e => (e?.name || '').toLowerCase() === (entity.name || '').toLowerCase()) || null
}

function openEntityModal(entity) {
  entityModalEntity.value = entity
  entityModalEnriched.value = findPhase2Entry(entity)
  entityModalOpen.value = true
}

function hasAnySocialHandle(enriched) {
  if (!enriched?.social_handles) return false
  return Object.values(enriched.social_handles).some(v => v && String(v).trim() !== '' && v !== 'null')
}

function renderedSocialLinks(enriched) {
  const handles = enriched?.social_handles || {}
  const xVerified = !!enriched?.x_verified
  const platforms = [
    { key: 'x',         label: 'X',         icon: 'mdi-alpha-x-circle', urlFn: h => `https://x.com/${stripAt(h)}` },
    { key: 'bluesky',   label: 'Bluesky',   icon: 'mdi-cloud',          urlFn: h => `https://bsky.app/profile/${stripAt(h)}` },
    { key: 'facebook',  label: 'Facebook',  icon: 'mdi-facebook',       urlFn: h => `https://facebook.com/${stripAt(h)}` },
    { key: 'instagram', label: 'Instagram', icon: 'mdi-instagram',      urlFn: h => `https://instagram.com/${stripAt(h)}` },
    { key: 'youtube',   label: 'YouTube',   icon: 'mdi-youtube',        urlFn: h => `https://youtube.com/${stripAt(h, true)}` },
    { key: 'tiktok',    label: 'TikTok',    icon: 'mdi-music-note',     urlFn: h => `https://tiktok.com/@${stripAt(h)}` },
    { key: 'mastodon',  label: 'Mastodon',  icon: 'mdi-mastodon',       urlFn: h => mastodonUrl(h) },
    { key: 'threads',   label: 'Threads',   icon: 'mdi-at',             urlFn: h => `https://threads.net/@${stripAt(h)}` },
  ]
  return platforms
    .map(p => {
      const v = handles[p.key]
      if (!v || v === 'null') return null
      return {
        platform: p.key,
        label: `${p.label}: ${v}`,
        icon: p.icon,
        url: p.urlFn(v),
        verified: p.key === 'x' && xVerified,
      }
    })
    .filter(Boolean)
}

// Prefer the verified X-API profile photo, then Grok-suggested image_url.
const entityModalAvatar = computed(() => {
  const e = entityModalEnriched.value
  if (!e) return null
  if (e.x_verified && e.x_profile?.profile_image_url) {
    // X returns "_normal" sized URL; upgrade to "_400x400" when possible.
    return e.x_profile.profile_image_url.replace('_normal', '_400x400')
  }
  return e.image_url || e.logo_url || null
})

function formatCount(n) {
  const num = Number(n)
  if (!Number.isFinite(num)) return ''
  if (num >= 1_000_000) return (num / 1_000_000).toFixed(1).replace(/\.0$/, '') + 'M'
  if (num >= 1_000) return (num / 1_000).toFixed(1).replace(/\.0$/, '') + 'K'
  return String(num)
}

function stripAt(handle, keepAtForYoutube = false) {
  if (!handle) return ''
  const s = String(handle).trim()
  if (keepAtForYoutube && s.startsWith('@')) return s
  return s.startsWith('@') ? s.slice(1) : s
}

function mastodonUrl(h) {
  // h is "@user@instance"
  const s = String(h).trim().replace(/^@/, '')
  const parts = s.split('@')
  if (parts.length === 2) return `https://${parts[1]}/@${parts[0]}`
  return `https://mastodon.social/@${parts[0] || s}`
}

async function extractAll() { // eslint-disable-line no-unused-vars
  if (filteredRundownItems.value.length === 0) return

  batchExtracting.value = true
  try {
    const itemIds = filteredRundownItems.value.map(item => item.db_id)
    await batchExtract(itemIds, {})

    // Reload data
    await loadRundownItems()
  } catch (error) {
    console.error('Batch extraction failed:', error)
  } finally {
    batchExtracting.value = false
  }
}

async function extractAllStale() { // eslint-disable-line no-unused-vars
  if (staleSegments.value.length === 0) return

  batchExtracting.value = true
  try {
    const itemIds = staleSegments.value.map(s => s.rundown_item_id)
    await batchExtract(itemIds, { force: true })

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

function onItemSelect(selected) { // eslint-disable-line no-unused-vars
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

function getStatusIconColor(status) { // eslint-disable-line no-unused-vars
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
  for (const t of phase2PollTimers.values()) clearInterval(t)
  phase2PollTimers.clear()
})
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
  border-collapse: collapse;
  table-layout: fixed;
}

.entity-table thead th {
  padding: 8px 12px;
  background: rgba(var(--v-theme-on-surface), 0.06);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.6);
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  text-align: left;
  vertical-align: middle;
}

.entity-table tbody tr {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  transition: background 0.15s;
}

.entity-table tbody tr:hover {
  background: rgba(var(--v-theme-on-surface), 0.04);
}

.entity-table tbody tr.entity-row-clickable {
  cursor: pointer;
}

.entity-table tbody tr.entity-row-clickable:hover {
  background: rgba(var(--v-theme-primary), 0.06);
}

/* ============================================
   Entity detail modal
   ============================================ */
.social-pill {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  font-size: 12px;
  border-radius: 999px;
  background: rgba(var(--v-theme-primary), 0.08);
  color: rgb(var(--v-theme-on-surface));
  text-decoration: none;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
}

.social-pill:hover {
  background: rgba(var(--v-theme-primary), 0.16);
  text-decoration: none;
}

.social-pill-verified {
  border-color: rgba(var(--v-theme-info), 0.6);
  background: rgba(var(--v-theme-info), 0.10);
}

.recent-activity {
  list-style: none;
  padding-left: 0;
  margin: 0;
}

.recent-activity li {
  padding: 4px 0;
  font-size: 13px;
  border-bottom: 1px dashed rgba(var(--v-theme-on-surface), 0.08);
}

.recent-activity li:last-child {
  border-bottom: none;
}

.recent-date {
  font-family: 'Roboto Mono', monospace;
  font-size: 11px;
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.entity-table tbody tr:last-child {
  border-bottom: none;
}

.entity-table tbody td {
  padding: 10px 12px;
  vertical-align: middle;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.87);
}

.entity-table .entity-type-col {
  width: 110px;
  white-space: nowrap;
}

.entity-table .entity-name-col {
  width: auto;
}

.entity-table .entity-role-col {
  width: 140px;
  white-space: nowrap;
}

.entity-table .entity-relation-col {
  width: auto;
  color: rgba(var(--v-theme-on-surface), 0.7);
}

.entity-table .entity-handle-col {
  width: 130px;
  white-space: nowrap;
}

.entity-type-label {
  font-size: 11px;
  font-weight: 500;
  text-transform: capitalize;
}

.entity-name {
  font-weight: 600;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
  max-width: 100%;
  vertical-align: middle;
}

.entity-table .entity-relation-col {
  white-space: normal;
  overflow: hidden;
  text-overflow: ellipsis;
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
.entity-table tbody tr.entity-type-Person td:first-child {
  border-left: 3px solid #2196F3;
}

.entity-table tbody tr.entity-type-Organization td:first-child {
  border-left: 3px solid #9C27B0;
}

.entity-table tbody tr.entity-type-Institution td:first-child {
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
