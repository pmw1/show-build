<template>
  <v-card class="pa-0">
    <v-row no-gutters class="fill-height">
      <!-- Vertical Tabs on Left -->
      <v-col cols="3" class="border-r">
        <v-tabs
          v-model="generationSubTab"
          direction="vertical"
          color="primary"
          class="generation-vertical-tabs"
        >
          <v-tab value="real-content" prepend-icon="mdi-creation">
            Real Content
            <v-chip size="x-small" color="success" class="ml-2">Production</v-chip>
          </v-tab>
          <v-tab value="test-content" prepend-icon="mdi-test-tube">
            Test Content
            <v-chip size="x-small" color="warning" class="ml-2">Dev</v-chip>
          </v-tab>
          <v-tab value="fsq-generator" prepend-icon="mdi-format-quote-close">
            FSQ Quote Generator
          </v-tab>
          <v-tab value="scripts" prepend-icon="mdi-script-text">
            Scripts
          </v-tab>
          <v-tab value="llm-routing" prepend-icon="mdi-robot">
            AI/LLM Routing
          </v-tab>
          <v-tab value="media-assets" prepend-icon="mdi-folder-image">
            Media Assets
          </v-tab>
        </v-tabs>
      </v-col>

      <!-- Tab Content on Right -->
      <v-col cols="9">
        <v-tabs-window v-model="generationSubTab" class="pa-6">

          <!-- Real Content Generator -->
          <v-tabs-window-item value="real-content">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-creation</v-icon>
              Real Content Generator
            </h3>
            <p class="text-body-2 mb-4">Configure AI-assisted content generation for production scripts.</p>

            <!-- Show Identity Section -->
            <v-card variant="outlined" class="mb-4">
              <v-expansion-panels v-model="showIdentityPanel">
                <v-expansion-panel
                  value="identity"
                  :class="[
                    'show-identity-panel',
                    `show-identity-${showIdentityStatus}`
                  ]"
                >
                  <v-expansion-panel-title>
                    <div class="d-flex align-center flex-grow-1">
                      <v-icon class="mr-2">mdi-bullseye-arrow</v-icon>
                      <span class="text-subtitle-1 font-weight-medium">Show Identity</span>
                      <v-spacer />
                      <v-chip
                        v-if="showIdentityStatus === 'complete'"
                        size="x-small"
                        color="success"
                        class="mr-2"
                      >
                        Configured
                      </v-chip>
                      <v-chip
                        v-else-if="showIdentityStatus === 'partial'"
                        size="x-small"
                        color="warning"
                        class="mr-2"
                      >
                        Incomplete
                      </v-chip>
                      <v-chip
                        v-else
                        size="x-small"
                        color="error"
                        class="mr-2"
                      >
                        Not Set
                      </v-chip>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <p class="text-caption text-grey mb-3">
                      This context is automatically included in all LLM prompts to ensure consistent, on-brand content generation.
                    </p>
                    <v-text-field
                      v-model="realContentSettings.showIdentity.name"
                      label="Show Name"
                      hint="The name of the show (used in {{show_name}} template variable)"
                      persistent-hint
                      variant="outlined"
                      density="compact"
                      class="mb-3"
                    />
                    <v-textarea
                      v-model="realContentSettings.showIdentity.thesis"
                      label="Show Thesis / Mission"
                      hint="The core purpose, perspective, or objective of the show. What is it about? What does it stand for?"
                      persistent-hint
                      variant="outlined"
                      density="compact"
                      auto-grow
                      rows="4"
                      class="mb-3"
                    />
                    <v-textarea
                      v-model="realContentSettings.showIdentity.tone"
                      label="Tone & Voice"
                      hint="How should content sound? (e.g., skeptical, irreverent, fact-based, conversational)"
                      persistent-hint
                      variant="outlined"
                      density="compact"
                      auto-grow
                      rows="3"
                      class="mb-3"
                    />
                    <v-textarea
                      v-model="realContentSettings.showIdentity.audience"
                      label="Target Audience"
                      hint="Who is this show for? What do they care about?"
                      persistent-hint
                      variant="outlined"
                      density="compact"
                      auto-grow
                      rows="3"
                    />
                    <div class="d-flex justify-end mt-3">
                      <v-btn
                        color="primary"
                        variant="tonal"
                        size="small"
                        @click="saveShowIdentity"
                        :loading="savingShowIdentity"
                      >
                        <v-icon left size="small">mdi-content-save</v-icon>
                        Save Show Identity
                      </v-btn>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
            </v-card>

            <!-- Tone Generation Section -->
            <v-card variant="outlined" class="mb-4" :class="collapsedSections.tone ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.tone ? 'mb-0' : 'mb-3'" @click="collapsedSections.tone = !collapsedSections.tone" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.tone ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon class="mr-2">mdi-palette-swatch</v-icon>
                Tone Generation
              </h4>
              <div v-show="!collapsedSections.tone">

              <!-- Tone Palette -->
              <h6 class="text-subtitle-2 mb-2">Tone Palette</h6>
              <p class="text-caption text-grey mb-2">
                The closed set of tones the classifier will choose from. Add, remove, or rename to match your show's editorial voice.
              </p>

              <div class="d-flex flex-wrap ga-2 mb-3">
                <v-chip
                  v-for="(tone, index) in realContentSettings.tonePalette"
                  :key="tone + index"
                  closable
                  size="small"
                  color="primary"
                  variant="tonal"
                  @click:close="removeTone(index)"
                >
                  {{ tone }}
                </v-chip>
                <v-alert
                  v-if="realContentSettings.tonePalette.length === 0"
                  type="warning"
                  variant="tonal"
                  density="compact"
                  class="mb-0"
                >
                  Tone palette is empty. Add at least one tone so the classifier has something to pick from.
                </v-alert>
              </div>

              <v-row dense align="center" class="mb-3">
                <v-col cols="9">
                  <v-text-field
                    v-model="newToneInput"
                    label="Add a new tone"
                    placeholder="e.g. sardonic"
                    variant="outlined"
                    density="compact"
                    hide-details
                    @keyup.enter="addTone"
                  />
                </v-col>
                <v-col cols="3">
                  <v-btn
                    color="primary"
                    variant="tonal"
                    block
                    prepend-icon="mdi-plus"
                    :disabled="!newToneInput.trim()"
                    @click="addTone"
                  >
                    Add
                  </v-btn>
                </v-col>
              </v-row>

              <v-divider class="my-3" />

              <!-- Model & Temperature -->
              <h6 class="text-subtitle-2 mb-2">Classification Settings</h6>

              <v-select
                v-model="realContentSettings.toneGeneration.model"
                :items="ollamaModelOptions"
                label="LLM Model"
                variant="outlined"
                density="compact"
                hint="Model used for tone classification. Leave empty to use global default."
                persistent-hint
                clearable
                class="mb-3"
              />

              <v-slider
                v-model.number="realContentSettings.toneGeneration.temperature"
                label="Temperature"
                min="0"
                max="1"
                step="0.05"
                thumb-label="always"
                color="primary"
                class="mb-3"
                hint="Lower = more consistent classification. Higher = more varied."
                persistent-hint
              />

              <v-divider class="my-3" />

              <!-- Prompt Template -->
              <h6 class="text-subtitle-2 mb-2">Classification Prompt</h6>

              <v-card variant="tonal" color="grey-darken-3" class="pa-3 mb-3">
                <div class="d-flex align-center mb-2">
                  <v-icon size="small" class="mr-2">mdi-code-braces</v-icon>
                  <span class="text-caption font-weight-medium">Available Template Variables</span>
                </div>
                <div class="template-vars-grid">
                  <div class="var-group">
                    <span class="var-label">Segment Info</span>
                    <div class="d-flex flex-wrap ga-1">
                      <v-chip size="small" variant="flat" color="#546E7A" @click="insertToneVariable('{{segment_title}}')" class="cursor-pointer insert-chip"><span v-pre>{{segment_title}}</span></v-chip>
                      <v-chip size="small" variant="flat" color="#546E7A" @click="insertToneVariable('{{segment_type}}')" class="cursor-pointer insert-chip"><span v-pre>{{segment_type}}</span></v-chip>
                      <v-chip size="small" variant="flat" color="#546E7A" @click="insertToneVariable('{{segment_content}}')" class="cursor-pointer insert-chip"><span v-pre>{{segment_content}}</span></v-chip>
                    </div>
                  </div>
                  <div class="var-group">
                    <span class="var-label text-pink">Palette</span>
                    <div class="d-flex flex-wrap ga-1">
                      <v-chip size="small" variant="flat" color="#880E4F" @click="insertToneVariable('{{tone_palette}}')" class="cursor-pointer insert-chip"><span v-pre>{{tone_palette}}</span></v-chip>
                    </div>
                  </div>
                </div>
              </v-card>

              <v-textarea
                ref="tonePromptTextarea"
                v-model="realContentSettings.toneGeneration.prompt"
                label="Tone Classification Prompt"
                variant="outlined"
                density="compact"
                auto-grow
                rows="6"
                hint="The prompt sent to the LLM to classify segment tone. Use {{variables}} for dynamic content."
                persistent-hint
                class="mb-3"
              />

              <div class="d-flex justify-space-between align-center mt-3">
                <v-btn
                  variant="text"
                  size="small"
                  prepend-icon="mdi-restore"
                  @click="resetTonePaletteToDefaults"
                >
                  Reset palette to defaults
                </v-btn>
                <v-btn
                  color="primary"
                  variant="tonal"
                  size="small"
                  prepend-icon="mdi-content-save"
                  :loading="savingTonePalette"
                  @click="saveTonePalette"
                >
                  Save Tone Generation
                </v-btn>
              </div>
              </div>
            </v-card>

            <!-- Description Generation Section -->
            <v-card variant="outlined" class="mb-4" :class="collapsedSections.descriptions ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.descriptions ? 'mb-0' : 'mb-3'" @click="collapsedSections.descriptions = !collapsedSections.descriptions" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.descriptions ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon class="mr-2">mdi-text-box-outline</v-icon>
                Description Generation
              </h4>
              <div v-show="!collapsedSections.descriptions">
              <v-expansion-panels variant="accordion" multiple v-model="descriptionPanels">
                <!-- Episode Description -->
                <v-expansion-panel value="episode" class="desc-panel-episode">
                  <v-expansion-panel-title>
                    <div class="d-flex align-center flex-grow-1">
                      <v-icon class="mr-2" size="small">mdi-movie-open</v-icon>
                      <span>Episode Description</span>
                      <v-spacer />
                      <v-chip
                        v-if="realContentSettings.episodeDescription.enabled"
                        size="x-small"
                        color="success"
                        class="mr-2"
                      >
                        Enabled
                      </v-chip>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-switch
                      v-model="realContentSettings.episodeDescription.enabled"
                      label="Enable Episode Description Generation"
                      color="primary"
                      density="compact"
                      class="mb-2"
                    />

                    <!-- Collapsed state when disabled -->
                    <v-alert
                      v-if="!realContentSettings.episodeDescription.enabled"
                      type="info"
                      variant="tonal"
                      density="compact"
                    >
                      Enable to configure episode description generation settings
                    </v-alert>

                    <!-- Expanded settings when enabled -->
                    <div v-if="realContentSettings.episodeDescription.enabled">
                      <v-divider class="my-3" />

                      <!-- Show Identity Injection -->
                      <v-checkbox
                        v-model="realContentSettings.episodeDescription.injectShowIdentity"
                        label="Inject Show Identity"
                        hint="Include show thesis, tone, and audience context in the prompt"
                        persistent-hint
                        density="compact"
                        hide-details="auto"
                        class="mb-3"
                        :disabled="!realContentSettings.showIdentity.thesis"
                      />
                      <v-alert
                        v-if="!realContentSettings.showIdentity.thesis"
                        type="warning"
                        variant="tonal"
                        density="compact"
                        class="mb-3"
                      >
                        <small>Configure Show Identity above to enable injection</small>
                      </v-alert>

                      <!-- Include (if exists) -->
                      <h6 class="text-subtitle-2 mb-2">Include (if exists)</h6>
                      <p class="text-caption text-grey mb-2">Select which available information to include in the generated description</p>

                      <v-row dense class="mb-3">
                        <v-col cols="4">
                          <v-checkbox
                            v-model="realContentSettings.episodeDescription.includeTitle"
                            label="Show Title"
                            density="compact"
                            hide-details
                          />
                        </v-col>
                        <v-col cols="4">
                          <v-checkbox
                            v-model="realContentSettings.episodeDescription.includeGuestInfo"
                            label="Guest Name/Info"
                            density="compact"
                            hide-details
                          />
                        </v-col>
                        <v-col cols="4">
                          <v-checkbox
                            v-model="realContentSettings.episodeDescription.mentionSpeaker"
                            label="Speaker Mention"
                            density="compact"
                            hide-details
                          />
                        </v-col>
                      </v-row>

                      <!-- Item Types - Dynamically loaded from itemTypes.js config -->
                      <div class="mb-3">
                        <span class="text-body-2 font-weight-medium">Include content from Item types:</span>
                        <p class="text-caption text-grey mt-1 mb-0">Checked types are included in <code>segment_summaries</code> and must have descriptions before the episode description will auto-generate.</p>
                        <v-row class="mt-2" dense>
                          <v-col
                            v-for="itemType in availableItemTypes"
                            :key="itemType.value"
                            cols="4"
                          >
                            <v-checkbox
                              v-model="realContentSettings.episodeDescription.itemTypes[itemType.value]"
                              :label="itemType.title"
                              density="compact"
                              hide-details
                            >
                              <template v-slot:label>
                                <div class="d-flex align-center">
                                  <v-icon size="x-small" :color="itemType.color" class="mr-1">{{ itemType.icon }}</v-icon>
                                  <span>{{ itemType.title }}</span>
                                </div>
                              </template>
                            </v-checkbox>
                          </v-col>
                        </v-row>
                      </div>

                      <v-divider class="my-3" />

                      <!-- Generation Options -->
                      <h6 class="text-subtitle-2 mb-2">Generation Options</h6>

                      <v-switch
                        v-model="realContentSettings.episodeDescription.weightSegmentDescriptions"
                        label="Weight Segment Descriptions more heavily"
                        color="primary"
                        density="compact"
                        hint="Prioritize segment descriptions when generating episode summary"
                        persistent-hint
                        class="mb-2"
                      />

                      <v-switch
                        v-model="realContentSettings.episodeDescription.exposeSpecialInstructions"
                        label="Expose special instructions text field"
                        color="primary"
                        density="compact"
                        hint="Show a text field for custom generation instructions when generating"
                        persistent-hint
                        class="mb-2"
                      />

                      <v-switch
                        v-model="realContentSettings.episodeDescription.allowInteractiveIteration"
                        label="Allow interactive iteration"
                        color="primary"
                        density="compact"
                        hint="Enable regeneration with feedback after initial generation"
                        persistent-hint
                        class="mb-3"
                      />

                      <v-divider class="my-3" />

                      <!-- Editorial Priority Order -->
                      <h6 class="text-subtitle-2 mb-2">Editorial Priority Order</h6>
                      <p class="text-caption text-grey mb-2">
                        Drag to reorder. This defines the order of editorial importance — NOT lineup position. The LLM will weight its description accordingly.
                      </p>
                      <draggable
                        :list="realContentSettings.episodeDescription.priorityOrder"
                        item-key="id"
                        handle=".priority-drag-handle"
                        class="priority-order-list mb-2"
                        @end="markEpisodeDescDirty"
                      >
                        <template #item="{ element, index }">
                          <div class="priority-order-item d-flex align-center">
                            <v-icon class="priority-drag-handle mr-2" size="small" color="grey">mdi-drag-vertical</v-icon>
                            <v-chip size="small" color="primary" variant="tonal" class="mr-2" style="min-width: 24px; justify-content: center;">{{ index + 1 }}</v-chip>
                            <span class="priority-order-label flex-grow-1">{{ element.label }}</span>
                            <v-chip size="x-small" variant="flat" :color="element.color || '#757575'" class="mr-2" style="border-radius: 2px; color: white;">{{ element.tag }}</v-chip>
                            <v-btn icon size="x-small" variant="text" color="grey" @click="removePriorityOrderItem(index)">
                              <v-icon size="small">mdi-close</v-icon>
                            </v-btn>
                          </div>
                        </template>
                      </draggable>
                      <div class="d-flex ga-2 align-center mb-3">
                        <v-text-field
                          v-model="newPriorityTag"
                          placeholder="New tag (e.g. investigation)"
                          variant="outlined"
                          density="compact"
                          hide-details
                          style="max-width: 200px;"
                          @keydown.enter.prevent="addPriorityOrderItem"
                        />
                        <v-text-field
                          v-model="newPriorityLabel"
                          placeholder="Label (e.g. Investigation Piece)"
                          variant="outlined"
                          density="compact"
                          hide-details
                          style="max-width: 250px;"
                          @keydown.enter.prevent="addPriorityOrderItem"
                        />
                        <v-btn size="small" color="primary" variant="tonal" @click="addPriorityOrderItem" :disabled="!newPriorityTag">
                          <v-icon size="small" class="mr-1">mdi-plus</v-icon> Add
                        </v-btn>
                      </div>

                      <v-divider class="my-3" />

                      <!-- LLM Preference Order -->
                      <h6 class="text-subtitle-2 mb-2">LLM Preference Order</h6>
                      <p class="text-caption text-grey mb-3">
                        Set the order of LLMs to try for episode description generation. The system will attempt each in order until one succeeds.
                      </p>

                      <div class="llm-preference-list mb-3">
                        <v-row
                          v-for="(pref, index) in realContentSettings.episodeDescription.llmPreferenceOrder"
                          :key="index"
                          align="center"
                          dense
                          class="mb-2"
                        >
                          <v-col cols="1" class="text-center">
                            <v-chip size="small" color="primary" variant="tonal">{{ index + 1 }}</v-chip>
                          </v-col>
                          <v-col cols="8">
                            <v-select
                              v-model="realContentSettings.episodeDescription.llmPreferenceOrder[index]"
                              :items="allAvailableLLMs"
                              item-title="title"
                              item-value="value"
                              label="Select LLM"
                              variant="outlined"
                              density="compact"
                              hide-details
                            >
                              <template v-slot:item="{ item, props }">
                                <v-list-item v-bind="props">
                                  <template v-slot:prepend>
                                    <v-icon size="small">{{ item.raw.icon }}</v-icon>
                                  </template>
                                </v-list-item>
                              </template>
                            </v-select>
                          </v-col>
                          <v-col cols="3" class="d-flex justify-end">
                            <v-btn
                              icon
                              size="x-small"
                              variant="text"
                              :disabled="index === 0"
                              @click="moveLLMPreferenceUp(index)"
                            >
                              <v-icon size="small">mdi-arrow-up</v-icon>
                            </v-btn>
                            <v-btn
                              icon
                              size="x-small"
                              variant="text"
                              :disabled="index === realContentSettings.episodeDescription.llmPreferenceOrder.length - 1"
                              @click="moveLLMPreferenceDown(index)"
                            >
                              <v-icon size="small">mdi-arrow-down</v-icon>
                            </v-btn>
                            <v-btn
                              icon
                              size="x-small"
                              variant="text"
                              color="error"
                              @click="removeLLMPreference(index)"
                            >
                              <v-icon size="small">mdi-close</v-icon>
                            </v-btn>
                          </v-col>
                        </v-row>

                        <v-btn
                          variant="tonal"
                          color="primary"
                          size="small"
                          prepend-icon="mdi-plus"
                          @click="addLLMPreference"
                          class="mt-2"
                        >
                          Add LLM
                        </v-btn>

                        <v-alert
                          v-if="realContentSettings.episodeDescription.llmPreferenceOrder.length === 0"
                          type="info"
                          variant="tonal"
                          density="compact"
                          class="mt-2"
                        >
                          No LLM preferences set. Click "Add LLM" to configure the preference order.
                        </v-alert>
                      </div>

                      <v-divider class="my-3" />

                      <!-- Generation Prompt -->
                      <h6 class="text-subtitle-2 mb-2">Generation Prompt</h6>

                      <!-- Available Template Variables -->
                      <v-card variant="tonal" color="grey-darken-3" class="pa-3 mb-3">
                        <div class="d-flex align-center mb-2">
                          <v-icon size="small" class="mr-2">mdi-code-braces</v-icon>
                          <span class="text-caption font-weight-medium">Available Template Variables</span>
                          <v-spacer />
                          <v-btn
                            size="x-small"
                            variant="text"
                            @click="generateDefaultEpisodePrompt"
                          >
                            Generate Default
                          </v-btn>
                        </div>
                        <div class="template-vars-grid">
                          <!-- Episode Info -->
                          <div class="var-group">
                            <span class="var-label">Episode Info</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="small" variant="flat" color="#546E7A" @click="insertVariable('{{episode_number}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{episode_number}}</span>
                              </v-chip>
                              <v-chip size="small" variant="flat" color="#546E7A" @click="insertVariable('{{show_name}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{show_name}}</span>
                              </v-chip>
                              <v-chip size="small" variant="flat" color="#546E7A" @click="insertVariable('{{air_date}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{air_date}}</span>
                              </v-chip>
                              <v-chip size="small" variant="flat" color="#546E7A" @click="insertVariable('{{duration}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{duration}}</span>
                              </v-chip>
                            </div>
                          </div>

                          <!-- Title (conditional) -->
                          <div v-if="realContentSettings.episodeDescription.includeTitle" class="var-group">
                            <span class="var-label text-blue">Title</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="small" variant="flat" color="#1565C0" @click="insertVariable('{{title}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{title}}</span>
                              </v-chip>
                            </div>
                          </div>

                          <!-- Guest Info (conditional) -->
                          <div v-if="realContentSettings.episodeDescription.includeGuestInfo" class="var-group">
                            <span class="var-label text-teal">Guest Info</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="small" variant="flat" color="#00695C" @click="insertVariable('{{guest_names}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{guest_names}}</span>
                              </v-chip>
                              <v-chip size="small" variant="flat" color="#00695C" @click="insertVariable('{{guest_bios}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{guest_bios}}</span>
                              </v-chip>
                            </div>
                          </div>

                          <!-- Speaker (conditional) -->
                          <div v-if="realContentSettings.episodeDescription.mentionSpeaker" class="var-group">
                            <span class="var-label text-orange">Speaker</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="small" variant="flat" color="#E65100" @click="insertVariable('{{speaker_name}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{speaker_name}}</span>
                              </v-chip>
                              <v-chip size="small" variant="flat" color="#E65100" @click="insertVariable('{{host_name}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{host_name}}</span>
                              </v-chip>
                            </div>
                          </div>

                          <!-- Content -->
                          <div class="var-group">
                            <span class="var-label text-green">Content</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="small" variant="flat" color="#2E7D32" @click="insertVariable('{{segment_summaries}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{segment_summaries}}</span>
                              </v-chip>
                              <v-chip v-if="realContentSettings.episodeDescription.weightSegmentDescriptions" size="small" variant="flat" color="#6A1B9A" @click="insertVariable('{{weighted_content}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{weighted_content}}</span>
                              </v-chip>
                            </div>
                          </div>

                          <!-- Show Identity -->
                          <div v-if="realContentSettings.episodeDescription.injectShowIdentity" class="var-group">
                            <span class="var-label text-purple">Show Identity</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="small" variant="flat" color="#6A1B9A" @click="insertVariable('{{show_thesis}}')" class="cursor-pointer insert-chip"><span v-pre>{{show_thesis}}</span></v-chip>
                              <v-chip size="small" variant="flat" color="#6A1B9A" @click="insertVariable('{{show_tone}}')" class="cursor-pointer insert-chip"><span v-pre>{{show_tone}}</span></v-chip>
                              <v-chip size="small" variant="flat" color="#6A1B9A" @click="insertVariable('{{show_audience}}')" class="cursor-pointer insert-chip"><span v-pre>{{show_audience}}</span></v-chip>
                            </div>
                          </div>

                          <!-- Topics & Quotes -->
                          <div class="var-group">
                            <span class="var-label">Topics & Quotes</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="small" variant="flat" color="#4E342E" @click="insertVariable('{{topics}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{topics}}</span>
                              </v-chip>
                              <v-chip size="small" variant="flat" color="#4E342E" @click="insertVariable('{{key_quotes}}')" class="cursor-pointer insert-chip">
                                <span v-pre>{{key_quotes}}</span>
                              </v-chip>
                            </div>
                          </div>
                        </div>
                        <p class="text-caption text-grey mt-2 mb-0">
                          <v-icon size="x-small">mdi-information-outline</v-icon>
                          Click a variable to insert it. Colored chips are enabled by your selections above.
                        </p>
                      </v-card>

                      <!-- Conditional Logic Blocks -->
                      <v-card variant="tonal" color="grey-darken-4" class="pa-3 mb-3">
                        <div class="d-flex align-center mb-2">
                          <v-icon size="small" class="mr-2">mdi-code-brackets</v-icon>
                          <span class="text-caption font-weight-medium">Conditional Logic Blocks</span>
                          <v-spacer />
                          <v-btn
                            size="x-small"
                            variant="text"
                            color="grey"
                            @click="showConditionalHelp = !showConditionalHelp"
                          >
                            <v-icon size="small" class="mr-1">mdi-help-circle-outline</v-icon>
                            {{ showConditionalHelp ? 'Hide' : 'Show' }} Reference
                          </v-btn>
                        </div>

                        <!-- Expandable Help Reference -->
                        <v-expand-transition>
                          <v-card v-if="showConditionalHelp" variant="outlined" color="grey-darken-3" class="mb-3 pa-3">
                            <div class="text-caption mb-2">
                              <strong>Syntax:</strong> <code>{% if condition %}your content here{% endif %}</code>
                            </div>
                            <v-divider class="my-2" />
                            <v-table density="compact" class="conditional-help-table">
                              <thead>
                                <tr>
                                  <th class="text-left">Condition</th>
                                  <th class="text-left">True When</th>
                                </tr>
                              </thead>
                              <tbody>
                                <tr class="text-cyan">
                                  <td><code>include_title</code></td>
                                  <td>Show Title checkbox is enabled AND episode has a title</td>
                                </tr>
                                <tr class="text-cyan">
                                  <td><code>include_guest_info</code></td>
                                  <td>Guest Name/Info checkbox is enabled AND episode has guest data</td>
                                </tr>
                                <tr class="text-cyan">
                                  <td><code>mention_speaker</code></td>
                                  <td>Speaker Mention checkbox is enabled AND host/speaker is defined</td>
                                </tr>
                                <tr class="text-amber">
                                  <td><code>has_segments</code></td>
                                  <td>Episode contains segment-type rundown items</td>
                                </tr>
                                <tr class="text-amber">
                                  <td><code>has_interviews</code></td>
                                  <td>Episode contains interview-type rundown items</td>
                                </tr>
                                <tr class="text-amber">
                                  <td><code>weight_segments</code></td>
                                  <td>Weight Segment Descriptions option is enabled</td>
                                </tr>
                                <tr class="text-purple">
                                  <td><code>has_show_identity</code></td>
                                  <td>Show Identity has thesis, tone, or audience configured</td>
                                </tr>
                                <tr class="text-red">
                                  <td><code>has_breaking</code></td>
                                  <td>A segment is tagged "breaking"</td>
                                </tr>
                                <tr class="text-red">
                                  <td><code>has_main_feature</code></td>
                                  <td>A segment is tagged "main-feature"</td>
                                </tr>
                                <tr class="text-red">
                                  <td><code>has_top_story</code></td>
                                  <td>A segment is tagged "top-story"</td>
                                </tr>
                                <tr class="text-red">
                                  <td><code>has_deep_dive</code></td>
                                  <td>A segment is tagged "deep-dive"</td>
                                </tr>
                                <tr class="text-pink">
                                  <td><code>has_quotes</code></td>
                                  <td>Episode has key quotes extracted from content</td>
                                </tr>
                                <tr class="text-pink">
                                  <td><code>has_topics</code></td>
                                  <td>Episode has topics/tags assigned</td>
                                </tr>
                                <tr class="text-pink">
                                  <td><code>has_guest</code></td>
                                  <td>Episode has a guest assigned</td>
                                </tr>
                                <tr class="text-pink">
                                  <td><code>has_guest_bio</code></td>
                                  <td>Episode has a guest bio filled in</td>
                                </tr>
                                <tr class="text-pink">
                                  <td><code>has_air_date</code></td>
                                  <td>Episode has an air date set</td>
                                </tr>
                                <tr class="text-pink">
                                  <td><code>has_duration</code></td>
                                  <td>Episode has a calculated or assigned duration</td>
                                </tr>
                              </tbody>
                            </v-table>
                            <div class="text-caption text-grey mt-2">
                              <v-icon size="x-small">mdi-lightbulb-outline</v-icon>
                              Tip: Combine conditionals with variables, e.g., <code>{% if has_quotes %}Notable quotes: {{key_quotes}}{% endif %}</code>
                            </div>
                          </v-card>
                        </v-expand-transition>
                        <div class="template-vars-grid">
                          <!-- Include Options -->
                          <div class="var-group">
                            <span class="var-label text-cyan">Include Options</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="cyan"
                                @click="insertConditional('include_title', 'Include the episode title {{title}} in the description.')"
                                class="cursor-pointer"
                              >
                                if include_title
                              </v-chip>
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="cyan"
                                @click="insertConditional('include_guest_info', 'Feature the guest(s): {{guest_names}}.')"
                                class="cursor-pointer"
                              >
                                if include_guest_info
                              </v-chip>
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="cyan"
                                @click="insertConditional('mention_speaker', 'Hosted by {{host_name}}.')"
                                class="cursor-pointer"
                              >
                                if mention_speaker
                              </v-chip>
                            </div>
                          </div>

                          <!-- Content Types -->
                          <div class="var-group">
                            <span class="var-label text-amber">Content Types</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="amber"
                                @click="insertConditional('has_segments', 'Cover these segments: {{segment_titles}}.')"
                                class="cursor-pointer"
                              >
                                if has_segments
                              </v-chip>
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="amber"
                                @click="insertConditional('has_interviews', 'Highlight the interview content.')"
                                class="cursor-pointer"
                              >
                                if has_interviews
                              </v-chip>
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="amber"
                                @click="insertConditional('weight_segments', 'Emphasize segment descriptions: {{weighted_content}}.')"
                                class="cursor-pointer"
                              >
                                if weight_segments
                              </v-chip>
                            </div>
                          </div>

                          <!-- Editorial Priority Tags -->
                          <div class="var-group">
                            <span class="var-label text-red">Priority Tags</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="flat" color="red" @click="insertConditional('has_breaking', 'BREAKING: This episode includes breaking news coverage.')" class="cursor-pointer">
                                if has_breaking
                              </v-chip>
                              <v-chip size="x-small" variant="flat" color="red-darken-3" @click="insertConditional('has_main_feature', 'The main feature of this episode: {{main_feature_summary}}.')" class="cursor-pointer">
                                if has_main_feature
                              </v-chip>
                              <v-chip size="x-small" variant="flat" color="deep-orange" @click="insertConditional('has_top_story', 'Top story: {{top_story_summary}}.')" class="cursor-pointer">
                                if has_top_story
                              </v-chip>
                              <v-chip size="x-small" variant="flat" color="blue" @click="insertConditional('has_deep_dive', 'Includes a deep-dive analysis.')" class="cursor-pointer">
                                if has_deep_dive
                              </v-chip>
                            </div>
                          </div>

                          <!-- Data Availability -->
                          <div class="var-group">
                            <span class="var-label text-pink">Data Checks</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="purple"
                                @click="insertConditional('has_show_identity', 'Show thesis: {{show_thesis}}\nTone: {{show_tone}}\nAudience: {{show_audience}}')"
                                class="cursor-pointer"
                              >
                                if has_show_identity
                              </v-chip>
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="pink"
                                @click="insertConditional('has_quotes', 'Include notable quotes: {{key_quotes}}.')"
                                class="cursor-pointer"
                              >
                                if has_quotes
                              </v-chip>
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="pink"
                                @click="insertConditional('has_topics', 'Topics covered: {{topics}}.')"
                                class="cursor-pointer"
                              >
                                if has_topics
                              </v-chip>
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="pink"
                                @click="insertConditional('has_guest', 'Featuring guest {{guest_names}}.')"
                                class="cursor-pointer"
                              >
                                if has_guest
                              </v-chip>
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="pink"
                                @click="insertConditional('has_guest_bio', 'Guest bio: {{guest_bios}}.')"
                                class="cursor-pointer"
                              >
                                if has_guest_bio
                              </v-chip>
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="pink"
                                @click="insertConditional('has_air_date', 'Airing {{air_date}}.')"
                                class="cursor-pointer"
                              >
                                if has_air_date
                              </v-chip>
                              <v-chip
                                size="x-small"
                                variant="flat"
                                color="pink"
                                @click="insertConditional('has_duration', 'Runtime: {{duration}}.')"
                                class="cursor-pointer"
                              >
                                if has_duration
                              </v-chip>
                            </div>
                          </div>
                        </div>
                        <p class="text-caption text-grey mt-2 mb-0">
                          <v-icon size="x-small">mdi-information-outline</v-icon>
                          Click to insert conditional block. Edit the content inside {% if %}...{% endif %} as needed.
                        </p>
                      </v-card>

                      <v-textarea
                        ref="episodePromptTextarea"
                        v-model="realContentSettings.episodeDescription.prompt"
                        label="Default Prompt Template"
                        variant="outlined"
                        density="compact"
                        rows="9"
                        hint="Custom prompt for generating episode descriptions. Use {{variables}} and {% if condition %}...{% endif %} blocks."
                        persistent-hint
                        class="mb-3"
                      />

                      <!-- Length Settings -->
                      <v-row>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="realContentSettings.episodeDescription.minLength"
                            label="Min Length"
                            type="number"
                            variant="outlined"
                            density="compact"
                            suffix="chars"
                          />
                        </v-col>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="realContentSettings.episodeDescription.maxLength"
                            label="Max Length"
                            type="number"
                            variant="outlined"
                            density="compact"
                            suffix="chars"
                          />
                        </v-col>
                      </v-row>

                      <!-- Model Selection -->
                      <v-select
                        v-model="realContentSettings.episodeDescription.model"
                        :items="ollamaModelOptions"
                        label="LLM Model"
                        variant="outlined"
                        density="compact"
                        hint="Model used for episode description generation. Leave empty to use global default."
                        persistent-hint
                        clearable
                        class="mb-3"
                      />

                      <!-- Temperature -->
                      <v-slider
                        v-model.number="realContentSettings.episodeDescription.temperature"
                        label="Temperature"
                        min="0"
                        max="1"
                        step="0.05"
                        thumb-label="always"
                        color="primary"
                        class="mb-2"
                        hint="Lower = more deterministic/consistent. Higher = more creative/varied."
                        persistent-hint
                      />

                      <v-divider class="my-4" />

                      <!-- Save Button -->
                      <div class="d-flex justify-end">
                        <v-btn
                          color="primary"
                          variant="elevated"
                          @click="saveEpisodeDescriptionSettings"
                          :loading="savingEpisodeDescription"
                          prepend-icon="mdi-content-save"
                        >
                          Save Episode Description Settings
                        </v-btn>
                      </div>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Segment Description -->
                <v-expansion-panel value="segment" class="desc-panel-segment">
                  <v-expansion-panel-title>
                    <div class="d-flex align-center flex-grow-1">
                      <v-icon class="mr-2" size="small">mdi-script-text-outline</v-icon>
                      <span>Segment Description</span>
                      <v-spacer />
                      <v-chip
                        v-if="realContentSettings.segmentDescription.enabled"
                        size="x-small"
                        color="success"
                        class="mr-2"
                      >
                        Enabled
                      </v-chip>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-switch
                      v-model="realContentSettings.segmentDescription.enabled"
                      label="Enable Segment Description Generation"
                      color="primary"
                      density="compact"
                      class="mb-2"
                    />

                    <!-- Collapsed state when disabled -->
                    <v-alert
                      v-if="!realContentSettings.segmentDescription.enabled"
                      type="info"
                      variant="tonal"
                      density="compact"
                    >
                      Enable to configure segment description generation settings
                    </v-alert>

                    <!-- Expanded settings when enabled -->
                    <div v-if="realContentSettings.segmentDescription.enabled">
                      <v-divider class="my-3" />

                      <!-- Show Identity Injection -->
                      <v-checkbox
                        v-model="realContentSettings.segmentDescription.injectShowIdentity"
                        label="Inject Show Identity"
                        hint="Include show thesis, tone, and audience context in the prompt"
                        persistent-hint
                        density="compact"
                        hide-details="auto"
                        class="mb-3"
                        :disabled="!realContentSettings.showIdentity.thesis"
                      />
                      <v-alert
                        v-if="!realContentSettings.showIdentity.thesis"
                        type="warning"
                        variant="tonal"
                        density="compact"
                        class="mb-3"
                      >
                        <small>Configure Show Identity above to enable injection</small>
                      </v-alert>

                      <!-- Core Options -->
                      <h6 class="text-subtitle-2 mb-2">Content Options</h6>
                      <v-checkbox
                        v-model="realContentSettings.segmentDescription.includeFullText"
                        label="Include full text of segment"
                        hint="Send the complete segment script content to the LLM"
                        persistent-hint
                        density="compact"
                        hide-details="auto"
                        class="mb-2"
                      />
                      <v-checkbox
                        v-model="realContentSettings.segmentDescription.includeAdjacentContext"
                        label="Include adjacent segment context"
                        hint="Provide titles/summaries of surrounding segments for better context"
                        persistent-hint
                        density="compact"
                        hide-details="auto"
                        class="mb-2"
                      />

                      <v-divider class="my-3" />

                      <!-- Interaction Options -->
                      <h6 class="text-subtitle-2 mb-2">Interaction Options</h6>
                      <v-checkbox
                        v-model="realContentSettings.segmentDescription.exposeSpecialInstructions"
                        label="Expose special instructions"
                        hint="Show a text field to provide custom instructions per generation"
                        persistent-hint
                        density="compact"
                        hide-details="auto"
                        class="mb-2"
                      />
                      <v-checkbox
                        v-model="realContentSettings.segmentDescription.allowInteractiveIteration"
                        label="Allow interactive iteration"
                        hint="Enable back-and-forth refinement of generated descriptions"
                        persistent-hint
                        density="compact"
                        hide-details="auto"
                        class="mb-2"
                      />

                      <v-divider class="my-3" />

                      <!-- Generation Prompt -->
                      <h6 class="text-subtitle-2 mb-2">Generation Prompt</h6>

                      <!-- Available Template Variables -->
                      <v-card variant="tonal" color="grey-darken-3" class="pa-3 mb-3">
                        <div class="d-flex align-center mb-2">
                          <v-icon size="small" class="mr-2">mdi-code-braces</v-icon>
                          <span class="text-caption font-weight-medium">Available Template Variables</span>
                          <v-spacer />
                          <v-btn
                            size="x-small"
                            variant="text"
                            @click="generateDefaultSegmentPrompt"
                          >
                            Generate Default
                          </v-btn>
                        </div>
                        <div class="template-vars-grid">
                          <!-- Segment Core -->
                          <div class="var-group">
                            <span class="var-label text-blue">Segment Core</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="flat" color="blue" @click="insertVariable('{{segment_title}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_title}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="blue" @click="insertVariable('{{segment_slug}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_slug}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="blue" @click="insertVariable('{{segment_type}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_type}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="blue" @click="insertVariable('{{segment_duration}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_duration}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="blue" @click="insertVariable('{{segment_order}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_order}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="blue" @click="insertVariable('{{segment_priority}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_priority}}</span></v-chip>
                            </div>
                          </div>

                          <!-- Segment Content -->
                          <div v-if="realContentSettings.segmentDescription.includeFullText" class="var-group">
                            <span class="var-label text-green">Segment Content</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="flat" color="green" @click="insertVariable('{{segment_content}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_content}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="green" @click="insertVariable('{{segment_cues}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_cues}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="green" @click="insertVariable('{{segment_current_description}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_current_description}}</span></v-chip>
                            </div>
                          </div>

                          <!-- People & Tags -->
                          <div class="var-group">
                            <span class="var-label text-teal">People & Tags</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="flat" color="teal" @click="insertVariable('{{segment_speaker}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_speaker}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="teal" @click="insertVariable('{{segment_guests}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_guests}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="teal" @click="insertVariable('{{segment_tags}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_tags}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="teal" @click="insertVariable('{{segment_resources}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_resources}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="teal" @click="insertVariable('{{segment_customer}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_customer}}</span></v-chip>
                            </div>
                          </div>

                          <!-- Tone -->
                          <div class="var-group">
                            <span class="var-label text-pink">Tone</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="flat" color="pink" @click="insertVariable('{{segment_tone}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_tone}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="pink" @click="insertVariable('{{segment_tone_rationale}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_tone_rationale}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="pink" @click="insertVariable('{{segment_tone_confidence}}', 'segment')" class="cursor-pointer"><span v-pre>{{segment_tone_confidence}}</span></v-chip>
                            </div>
                          </div>

                          <!-- Adjacent Context -->
                          <div v-if="realContentSettings.segmentDescription.includeAdjacentContext" class="var-group">
                            <span class="var-label text-amber">Adjacent Context</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="flat" color="amber" @click="insertVariable('{{adjacent_previous}}', 'segment')" class="cursor-pointer"><span v-pre>{{adjacent_previous}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="amber" @click="insertVariable('{{adjacent_next}}', 'segment')" class="cursor-pointer"><span v-pre>{{adjacent_next}}</span></v-chip>
                            </div>
                          </div>

                          <!-- Episode Context -->
                          <div class="var-group">
                            <span class="var-label">Episode Context</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="outlined" @click="insertVariable('{{show_name}}', 'segment')" class="cursor-pointer"><span v-pre>{{show_name}}</span></v-chip>
                              <v-chip size="x-small" variant="outlined" @click="insertVariable('{{episode_number}}', 'segment')" class="cursor-pointer"><span v-pre>{{episode_number}}</span></v-chip>
                              <v-chip size="x-small" variant="outlined" @click="insertVariable('{{episode_title}}', 'segment')" class="cursor-pointer"><span v-pre>{{episode_title}}</span></v-chip>
                              <v-chip size="x-small" variant="outlined" @click="insertVariable('{{air_date}}', 'segment')" class="cursor-pointer"><span v-pre>{{air_date}}</span></v-chip>
                              <v-chip size="x-small" variant="outlined" @click="insertVariable('{{host_name}}', 'segment')" class="cursor-pointer"><span v-pre>{{host_name}}</span></v-chip>
                            </div>
                          </div>

                          <!-- Show Identity -->
                          <div v-if="realContentSettings.segmentDescription.injectShowIdentity" class="var-group">
                            <span class="var-label text-purple">Show Identity</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="flat" color="purple" @click="insertVariable('{{show_thesis}}', 'segment')" class="cursor-pointer"><span v-pre>{{show_thesis}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="purple" @click="insertVariable('{{show_tone}}', 'segment')" class="cursor-pointer"><span v-pre>{{show_tone}}</span></v-chip>
                              <v-chip size="x-small" variant="flat" color="purple" @click="insertVariable('{{show_audience}}', 'segment')" class="cursor-pointer"><span v-pre>{{show_audience}}</span></v-chip>
                            </div>
                          </div>
                        </div>
                        <p class="text-caption text-grey mt-2 mb-0">
                          <v-icon size="x-small">mdi-information-outline</v-icon>
                          Click a variable to insert it into the prompt. Colored chips are enabled by your selections above.
                        </p>
                      </v-card>

                      <!-- Conditional Logic Blocks -->
                      <v-card variant="tonal" color="grey-darken-4" class="pa-3 mb-3">
                        <div class="d-flex align-center mb-2">
                          <v-icon size="small" class="mr-2">mdi-code-brackets</v-icon>
                          <span class="text-caption font-weight-medium">Conditional Logic Blocks</span>
                        </div>
                        <div class="template-vars-grid">
                          <div class="var-group">
                            <span class="var-label text-cyan">Segment Flags</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="flat" color="cyan" @click="insertConditional('has_full_text', 'Full segment content:\n{{segment_content}}', 'segment')" class="cursor-pointer">if has_full_text</v-chip>
                              <v-chip size="x-small" variant="flat" color="cyan" @click="insertConditional('has_adjacent_context', 'Adjacent context:\nPrevious: {{adjacent_previous}}\nNext: {{adjacent_next}}', 'segment')" class="cursor-pointer">if has_adjacent_context</v-chip>
                              <v-chip size="x-small" variant="flat" color="cyan" @click="insertConditional('has_speaker', 'Speaker: {{segment_speaker}}', 'segment')" class="cursor-pointer">if has_speaker</v-chip>
                              <v-chip size="x-small" variant="flat" color="cyan" @click="insertConditional('has_guests', 'Guests: {{segment_guests}}', 'segment')" class="cursor-pointer">if has_guests</v-chip>
                              <v-chip size="x-small" variant="flat" color="cyan" @click="insertConditional('has_tags', 'Tags: {{segment_tags}}', 'segment')" class="cursor-pointer">if has_tags</v-chip>
                              <v-chip size="x-small" variant="flat" color="cyan" @click="insertConditional('has_tone', 'Editorial tone: {{segment_tone}} — {{segment_tone_rationale}}', 'segment')" class="cursor-pointer">if has_tone</v-chip>
                              <v-chip size="x-small" variant="flat" color="cyan" @click="insertConditional('inject_show_identity', 'Show identity — Thesis: {{show_thesis}} / Tone: {{show_tone}} / Audience: {{show_audience}}', 'segment')" class="cursor-pointer">if inject_show_identity</v-chip>
                            </div>
                          </div>
                        </div>
                      </v-card>

                      <!-- Model Selection -->
                      <v-select
                        v-model="realContentSettings.segmentDescription.model"
                        :items="ollamaModelOptions"
                        label="LLM Model"
                        variant="outlined"
                        density="compact"
                        hint="Model used for segment description generation. Leave empty to use global default."
                        persistent-hint
                        clearable
                        class="mb-3"
                      />

                      <!-- Temperature -->
                      <v-slider
                        v-model.number="realContentSettings.segmentDescription.temperature"
                        label="Temperature"
                        min="0"
                        max="1"
                        step="0.05"
                        thumb-label="always"
                        color="primary"
                        class="mb-3"
                        hint="Lower = more deterministic/consistent. Higher = more creative/varied."
                        persistent-hint
                      />

                      <v-textarea
                        ref="segmentPromptTextarea"
                        v-model="realContentSettings.segmentDescription.prompt"
                        label="Default Prompt Template"
                        variant="outlined"
                        density="compact"
                        auto-grow
                        rows="9"
                        hint="Custom prompt for generating segment descriptions. Use {{variables}} and {% if condition %}...{% endif %} blocks."
                        persistent-hint
                        class="mb-3"
                      />

                      <v-divider class="my-4" />

                      <div class="d-flex justify-end">
                        <v-btn
                          :color="segmentDescriptionDirty ? 'primary' : 'success'"
                          variant="elevated"
                          :loading="savingSegmentDescription"
                          :disabled="!segmentDescriptionDirty && !savingSegmentDescription"
                          :prepend-icon="segmentDescriptionDirty ? 'mdi-content-save' : 'mdi-check-circle'"
                          @click="saveSegmentDescriptionSettings"
                        >
                          {{ segmentDescriptionDirty ? 'Save Segment Description Settings' : 'Synchronized' }}
                        </v-btn>
                      </div>
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Image Description -->
                <v-expansion-panel value="image" class="desc-panel-image">
                  <v-expansion-panel-title>
                    <div class="d-flex align-center">
                      <v-icon class="mr-2" size="small">mdi-image-text</v-icon>
                      <span>Image Description</span>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-switch
                      v-model="realContentSettings.imageDescription.enabled"
                      label="Enable Image Description Generation"
                      color="primary"
                      density="compact"
                      class="mb-2"
                    />
                    <v-textarea
                      v-model="realContentSettings.imageDescription.prompt"
                      label="Generation Prompt"
                      variant="outlined"
                      density="compact"
                      rows="3"
                      hint="Custom prompt for generating image alt text and descriptions"
                      persistent-hint
                      :disabled="!realContentSettings.imageDescription.enabled"
                    />
                    <v-switch
                      v-model="realContentSettings.imageDescription.includeAltText"
                      label="Generate ALT text for accessibility"
                      color="primary"
                      density="compact"
                      :disabled="!realContentSettings.imageDescription.enabled"
                    />
                  </v-expansion-panel-text>
                </v-expansion-panel>
              </v-expansion-panels>
              </div>
            </v-card>

            <!-- Social Media Section -->
            <v-card variant="outlined" class="mb-4" :class="collapsedSections.social ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.social ? 'mb-0' : 'mb-3'" @click="collapsedSections.social = !collapsedSections.social" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.social ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon class="mr-2">mdi-share-variant</v-icon>
                Social Media
              </h4>
              <div v-show="!collapsedSections.social">
              <p class="text-body-2 text-grey mb-4">
                Configure AI-generated content for social media platforms. Enable platforms to reveal their settings.
              </p>

              <v-expansion-panels variant="accordion" multiple v-model="socialMediaPanels">
                <!-- X (Twitter) -->
                <v-expansion-panel value="x">
                  <v-expansion-panel-title>
                    <div class="d-flex align-center flex-grow-1">
                      <v-icon class="mr-2" size="small">mdi-twitter</v-icon>
                      <span>X (Twitter)</span>
                      <v-spacer />
                      <v-switch
                        v-model="realContentSettings.socialMedia.x.enabled"
                        color="primary"
                        density="compact"
                        hide-details
                        @click.stop
                        class="mr-2"
                      />
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-alert v-if="!realContentSettings.socialMedia.x.enabled" type="warning" variant="tonal" density="compact" class="mb-3">
                      Enable X integration above to configure settings
                    </v-alert>
                    <div :class="{ 'disabled-section': !realContentSettings.socialMedia.x.enabled }">
                      <v-textarea
                        v-model="realContentSettings.socialMedia.x.defaultPrompt"
                        label="Default Post Prompt"
                        variant="outlined"
                        density="compact"
                        rows="2"
                        hint="Template prompt for generating X posts"
                        persistent-hint
                        :disabled="!realContentSettings.socialMedia.x.enabled"
                        class="mb-3"
                      />
                      <v-row>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="realContentSettings.socialMedia.x.maxLength"
                            label="Max Post Length"
                            type="number"
                            variant="outlined"
                            density="compact"
                            suffix="chars"
                            :disabled="!realContentSettings.socialMedia.x.enabled"
                          />
                        </v-col>
                        <v-col cols="6">
                          <v-switch
                            v-model="realContentSettings.socialMedia.x.includeHashtags"
                            label="Auto-generate hashtags"
                            color="primary"
                            density="compact"
                            :disabled="!realContentSettings.socialMedia.x.enabled"
                          />
                        </v-col>
                      </v-row>
                      <v-switch
                        v-model="realContentSettings.socialMedia.x.includeThreads"
                        label="Enable thread generation for long content"
                        color="primary"
                        density="compact"
                        :disabled="!realContentSettings.socialMedia.x.enabled"
                      />
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Meta/Facebook -->
                <v-expansion-panel value="meta">
                  <v-expansion-panel-title>
                    <div class="d-flex align-center flex-grow-1">
                      <v-icon class="mr-2" size="small">mdi-facebook</v-icon>
                      <span>Meta / Facebook</span>
                      <v-spacer />
                      <v-switch
                        v-model="realContentSettings.socialMedia.meta.enabled"
                        color="primary"
                        density="compact"
                        hide-details
                        @click.stop
                        class="mr-2"
                      />
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-alert v-if="!realContentSettings.socialMedia.meta.enabled" type="warning" variant="tonal" density="compact" class="mb-3">
                      Enable Meta integration above to configure settings
                    </v-alert>
                    <div :class="{ 'disabled-section': !realContentSettings.socialMedia.meta.enabled }">
                      <v-textarea
                        v-model="realContentSettings.socialMedia.meta.defaultPrompt"
                        label="Default Post Prompt"
                        variant="outlined"
                        density="compact"
                        rows="2"
                        hint="Template prompt for generating Facebook posts"
                        persistent-hint
                        :disabled="!realContentSettings.socialMedia.meta.enabled"
                        class="mb-3"
                      />
                      <v-row>
                        <v-col cols="6">
                          <v-select
                            v-model="realContentSettings.socialMedia.meta.postType"
                            :items="['Standard Post', 'Story', 'Reel Caption', 'Event Description']"
                            label="Default Post Type"
                            variant="outlined"
                            density="compact"
                            :disabled="!realContentSettings.socialMedia.meta.enabled"
                          />
                        </v-col>
                        <v-col cols="6">
                          <v-switch
                            v-model="realContentSettings.socialMedia.meta.includeEmoji"
                            label="Include emojis"
                            color="primary"
                            density="compact"
                            :disabled="!realContentSettings.socialMedia.meta.enabled"
                          />
                        </v-col>
                      </v-row>
                      <v-switch
                        v-model="realContentSettings.socialMedia.meta.crossPostInstagram"
                        label="Generate Instagram-compatible version"
                        color="primary"
                        density="compact"
                        :disabled="!realContentSettings.socialMedia.meta.enabled"
                      />
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- Substack -->
                <v-expansion-panel value="substack">
                  <v-expansion-panel-title>
                    <div class="d-flex align-center flex-grow-1">
                      <v-icon class="mr-2" size="small">mdi-newspaper-variant</v-icon>
                      <span>Substack</span>
                      <v-spacer />
                      <v-switch
                        v-model="realContentSettings.socialMedia.substack.enabled"
                        color="primary"
                        density="compact"
                        hide-details
                        @click.stop
                        class="mr-2"
                      />
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                    <v-alert v-if="!realContentSettings.socialMedia.substack.enabled" type="warning" variant="tonal" density="compact" class="mb-3">
                      Enable Substack integration above to configure settings
                    </v-alert>
                    <div :class="{ 'disabled-section': !realContentSettings.socialMedia.substack.enabled }">
                      <v-textarea
                        v-model="realContentSettings.socialMedia.substack.defaultPrompt"
                        label="Default Article Prompt"
                        variant="outlined"
                        density="compact"
                        rows="2"
                        hint="Template prompt for generating Substack content"
                        persistent-hint
                        :disabled="!realContentSettings.socialMedia.substack.enabled"
                        class="mb-3"
                      />
                      <v-row>
                        <v-col cols="6">
                          <v-select
                            v-model="realContentSettings.socialMedia.substack.contentType"
                            :items="['Full Article', 'Newsletter Teaser', 'Show Notes', 'Episode Recap']"
                            label="Default Content Type"
                            variant="outlined"
                            density="compact"
                            :disabled="!realContentSettings.socialMedia.substack.enabled"
                          />
                        </v-col>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="realContentSettings.socialMedia.substack.targetWordCount"
                            label="Target Word Count"
                            type="number"
                            variant="outlined"
                            density="compact"
                            suffix="words"
                            :disabled="!realContentSettings.socialMedia.substack.enabled"
                          />
                        </v-col>
                      </v-row>
                      <v-switch
                        v-model="realContentSettings.socialMedia.substack.includeTimestamps"
                        label="Include episode timestamps"
                        color="primary"
                        density="compact"
                        :disabled="!realContentSettings.socialMedia.substack.enabled"
                      />
                    </div>
                  </v-expansion-panel-text>
                </v-expansion-panel>

                <!-- More Coming Soon -->
                <v-expansion-panel disabled>
                  <v-expansion-panel-title>
                    <div class="d-flex align-center text-grey">
                      <v-icon class="mr-2" size="small" color="grey">mdi-plus-circle-outline</v-icon>
                      <span>More platforms coming soon...</span>
                    </div>
                  </v-expansion-panel-title>
                </v-expansion-panel>
              </v-expansion-panels>
              </div>
            </v-card>

            <!-- Production Content Features (existing) -->
            <v-card variant="outlined" class="mb-4" :class="collapsedSections.production ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.production ? 'mb-0' : 'mb-3'" @click="collapsedSections.production = !collapsedSections.production" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.production ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon class="mr-2">mdi-text-box-check</v-icon>
                Production Content Features
              </h4>
              <div v-show="!collapsedSections.production">
              <v-list density="compact">
                <v-list-item prepend-icon="mdi-script-text-outline">
                  <v-list-item-title>Segment Intros & Outros</v-list-item-title>
                  <v-list-item-subtitle>Generate professional transitions between segments</v-list-item-subtitle>
                </v-list-item>
                <v-list-item prepend-icon="mdi-bullhorn">
                  <v-list-item-title>Promotional Copy</v-list-item-title>
                  <v-list-item-subtitle>Create on-brand promotional content and CTAs</v-list-item-subtitle>
                </v-list-item>
                <v-list-item prepend-icon="mdi-format-quote-close">
                  <v-list-item-title>Quote Formatting</v-list-item-title>
                  <v-list-item-subtitle>Intelligently format and split quotes for display</v-list-item-subtitle>
                </v-list-item>
                <v-list-item prepend-icon="mdi-clipboard-check">
                  <v-list-item-title>Approval Workflows</v-list-item-title>
                  <v-list-item-subtitle>Review and approve AI-generated content before use</v-list-item-subtitle>
                </v-list-item>
              </v-list>
              </div>
            </v-card>

            <!-- Save Button -->
            <v-btn
              color="primary"
              variant="elevated"
              @click="saveRealContentSettings"
              :loading="savingRealContent"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Real Content Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Test Content Generator -->
          <v-tabs-window-item value="test-content">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-test-tube</v-icon>
              Test Content Generator
            </h3>
            <p class="text-body-2 mb-4">
              Generate placeholder script content using local LLM for development and testing purposes.
            </p>

            <v-alert type="warning" variant="tonal" class="mb-6">
              <strong>Development Tool:</strong> This generates placeholder content for testing layouts and workflows.
              Not intended for production use.
            </v-alert>

            <v-card variant="outlined" class="mb-4" :class="collapsedSections.testKeyboard ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.testKeyboard ? 'mb-0' : 'mb-3'" @click="collapsedSections.testKeyboard = !collapsedSections.testKeyboard" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.testKeyboard ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon class="mr-2">mdi-keyboard</v-icon>
                Keyboard Shortcut
              </h4>
              <div v-show="!collapsedSections.testKeyboard">
              <v-card-text class="pa-0">
                <p class="text-body-2 mb-2">
                  Triggered by <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>Shift</kbd>+<kbd>[1-9]</kbd> where the number is paragraph count.
                </p>
                <v-alert type="info" variant="tonal" density="compact">
                  <strong>How it works:</strong> Select a rundown item, press the hotkey, and the LLM will generate broadcast-style script content based on the segment type and duration.
                </v-alert>
              </v-card-text>
              </div>
            </v-card>

            <v-card variant="outlined" class="mb-4" :class="collapsedSections.testModel ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.testModel ? 'mb-0' : 'mb-3'" @click="collapsedSections.testModel = !collapsedSections.testModel" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.testModel ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon class="mr-2">mdi-robot</v-icon>
                LLM Model Selection
              </h4>
              <div v-show="!collapsedSections.testModel">
              <v-card-text class="pa-0">
                <v-row>
                  <v-col cols="6">
                    <v-select
                      v-model="testContentService"
                      :items="testContentServiceOptions"
                      label="Service"
                      variant="outlined"
                      density="comfortable"
                      hint="Which LLM service to use"
                      persistent-hint
                    />
                  </v-col>
                  <v-col cols="6">
                    <v-select
                      v-model="testContentModel"
                      :items="testContentModelOptions"
                      label="Model"
                      variant="outlined"
                      density="comfortable"
                      :disabled="!testContentService || testContentService === 'auto'"
                      hint="Specific model for content generation"
                      persistent-hint
                    />
                  </v-col>
                </v-row>
                <v-row class="mt-4">
                  <v-col cols="12">
                    <v-btn
                      color="primary"
                      variant="elevated"
                      @click="saveTestContentSettings"
                      :loading="savingTestContent"
                    >
                      <v-icon left>mdi-content-save</v-icon>
                      Save Model Selection
                    </v-btn>
                    <v-btn
                      variant="text"
                      class="ml-2"
                      @click="resetTestContentToDefaults"
                    >
                      Reset to Defaults
                    </v-btn>
                  </v-col>
                </v-row>
              </v-card-text>
              </div>
            </v-card>

            <v-card variant="outlined" :class="collapsedSections.testOllama ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.testOllama ? 'mb-0' : 'mb-3'" @click="collapsedSections.testOllama = !collapsedSections.testOllama" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.testOllama ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon class="mr-2">mdi-server</v-icon>
                Available Ollama Models
              </h4>
              <div v-show="!collapsedSections.testOllama">
              <v-card-text class="pa-0">
                <v-chip-group>
                  <v-chip
                    v-for="model in availableOllamaModels"
                    :key="model"
                    size="small"
                    :color="testContentModel === model ? 'primary' : 'default'"
                    @click="selectOllamaModel(model)"
                  >
                    {{ model }}
                  </v-chip>
                </v-chip-group>
                <p v-if="!availableOllamaModels.length" class="text-grey mt-2">
                  Loading models from Ollama server...
                </p>
              </v-card-text>
              </div>
            </v-card>
          </v-tabs-window-item>

          <!-- FSQ Quote Generator -->
          <v-tabs-window-item value="fsq-generator">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-format-quote-close</v-icon>
              FSQ Quote Generator
            </h3>
            <p class="text-body-2 mb-4">Configure settings for Full Screen Quote generation and preview.</p>

            <v-card variant="tonal" color="deep-purple" class="mb-4" :class="collapsedSections.fsqPreview ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.fsqPreview ? 'mb-0' : 'mb-3'" @click="collapsedSections.fsqPreview = !collapsedSections.fsqPreview" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.fsqPreview ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon left class="mr-2">mdi-video</v-icon>
                Preview Background Video
              </h4>
              <div v-show="!collapsedSections.fsqPreview">
              <v-text-field
                v-model="localSettings.fsq_background_video"
                label="Background Video Path"
                placeholder="/assets/preview-background.mp4"
                variant="outlined"
                density="comfortable"
                hint="Path to compressed video for FSQ modal preview (1920x1080 → 640x360, ~1MB)"
                persistent-hint
              />

              <v-alert type="info" variant="tonal" class="mt-4">
                <v-alert-title>Compressed Preview</v-alert-title>
                The preview uses an ultra-compressed version of your branded background.
                Current: <code>{{ localSettings.fsq_background_video }}</code>
              </v-alert>
              </div>
            </v-card>

            <v-card variant="tonal" color="deep-purple" class="mb-4" :class="collapsedSections.fsqStyle ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.fsqStyle ? 'mb-0' : 'mb-3'" @click="collapsedSections.fsqStyle = !collapsedSections.fsqStyle" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.fsqStyle ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon left class="mr-2">mdi-palette</v-icon>
                Default FSQ Style
              </h4>
              <div v-show="!collapsedSections.fsqStyle">
              <v-row>
                <v-col cols="6">
                  <v-select
                    v-model="localSettings.fsq_default_alignment"
                    :items="alignmentOptions"
                    label="Default Text Alignment"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="6">
                  <v-select
                    v-model="localSettings.fsq_default_font"
                    :items="fontOptions"
                    label="Default Font Family"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
              </v-row>

              <v-slider
                v-model="localSettings.fsq_default_font_size"
                label="Default Font Size"
                min="10"
                max="50"
                step="1"
                thumb-label
                hint="Default font size for new FSQ quotes (10-50px)"
                persistent-hint
              >
                <template v-slot:append>
                  <v-chip size="small" color="primary">
                    {{ localSettings.fsq_default_font_size }}px
                  </v-chip>
                </template>
              </v-slider>
              </div>
            </v-card>

            <v-card variant="outlined" class="mb-4" :class="collapsedSections.fsqOptions ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.fsqOptions ? 'mb-0' : 'mb-3'" @click="collapsedSections.fsqOptions = !collapsedSections.fsqOptions" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.fsqOptions ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon left class="mr-2">mdi-cog</v-icon>
                Generation Options
              </h4>
              <div v-show="!collapsedSections.fsqOptions">
              <v-checkbox
                v-model="localSettings.fsq_include_attribution_by_default"
                label="Include attribution by default"
                hint="When enabled, the attribution radio button will be pre-selected to 'Include Attribution'"
                persistent-hint
                density="comfortable"
              />
              </div>
            </v-card>

            <v-card variant="outlined" class="mb-4" :class="collapsedSections.fsqFormatting ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.fsqFormatting ? 'mb-0' : 'mb-3'" @click="collapsedSections.fsqFormatting = !collapsedSections.fsqFormatting" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.fsqFormatting ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon left class="mr-2">mdi-format-quote-close</v-icon>
                Quote Formatting Rules
              </h4>
              <div v-show="!collapsedSections.fsqFormatting">
              <v-checkbox
                v-model="localSettings.fsq_strip_exterior_quotes"
                label="Strip exterior quotes during processing"
                hint="Remove surrounding quotation marks from input text (recommended for consistency)"
                persistent-hint
                density="comfortable"
                class="mb-2"
              />

              <v-checkbox
                v-model="localSettings.fsq_regenerate_exterior_quotes"
                label="Regenerate exterior quotes at render"
                hint="Add quotation marks back when rendering the quote (usually not needed for FSQ graphics)"
                persistent-hint
                density="comfortable"
                class="mb-2"
              />

              <v-checkbox
                v-model="localSettings.fsq_normalize_interior_quotes"
                label="Normalize interior quotes to single quotes"
                hint="Convert nested quotes inside the text to single quotes (American English style)"
                persistent-hint
                density="comfortable"
                class="mb-8"
              />

              <v-select
                v-model="localSettings.fsq_attribution_dash_style"
                label="Attribution Dash Style"
                :items="attributionDashOptions"
                variant="outlined"
                density="comfortable"
                hint="Character used before attribution/source"
                persistent-hint
              >
                <template v-slot:prepend-inner>
                  <v-icon>mdi-minus</v-icon>
                </template>
              </v-select>
              </div>
            </v-card>

            <v-card elevation="2" class="mb-4">
              <v-card-title class="bg-indigo-lighten-1 text-white section-toggle" @click="collapsedSections.fsqSplitting = !collapsedSections.fsqSplitting" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.fsqSplitting ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon class="mr-2">mdi-scissors-cutting</v-icon>
                FSQ Quote Splitting Rules
              </v-card-title>

              <div v-show="!collapsedSections.fsqSplitting">
              <v-card-text class="pt-4">
                <v-alert type="info" variant="tonal" density="compact" class="mb-4">
                  Configure how AI determines when and where to split long quotes for optimal TV display
                </v-alert>

                <!-- Primary Controls: Screen Capacity -->
                <div class="text-subtitle-2 mb-3 font-weight-bold">Screen Capacity Limits</div>

                <v-row>
                  <v-col cols="6">
                    <v-text-field
                      v-model.number="localSettings.fsq_max_lines"
                      label="Max Lines Per Screen"
                      type="number"
                      min="3"
                      max="8"
                      variant="outlined"
                      density="compact"
                      hint="Maximum lines before split (3-8)"
                      persistent-hint
                      prepend-inner-icon="mdi-format-line-spacing"
                    >
                      <template v-slot:append-inner>
                        <span class="text-caption text-grey mr-1">lines</span>
                        <v-tooltip location="top" max-width="400">
                          <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                          </template>
                          <div class="pa-2">
                            <div class="text-subtitle-2 mb-2">Maximum Lines Per Screen</div>
                            <div class="text-body-2 mb-2">
                              Controls the maximum number of text lines displayed on a single full-screen quote before the AI considers splitting it.
                            </div>
                            <div class="text-body-2 mb-2">
                              <strong>Recommended values:</strong>
                            </div>
                            <ul class="text-body-2 mb-2">
                              <li><strong>3-4 lines:</strong> Best for maximum readability on TV (viewer sitting 8-10 feet away)</li>
                              <li><strong>5-6 lines:</strong> Good balance between content and readability</li>
                              <li><strong>7-8 lines:</strong> Maximum before quotes feel cluttered or overwhelming</li>
                            </ul>
                            <div class="text-body-2">
                              <strong>How it works:</strong> This value is multiplied by "Characters Per Line" to calculate the total character limit for a single screen.
                            </div>
                          </div>
                        </v-tooltip>
                      </template>
                    </v-text-field>
                  </v-col>

                  <v-col cols="6">
                    <v-text-field
                      v-model.number="localSettings.fsq_chars_per_line"
                      label="Characters Per Line"
                      type="number"
                      min="40"
                      max="90"
                      variant="outlined"
                      density="compact"
                      hint="Average characters at default font (40-90)"
                      persistent-hint
                      prepend-inner-icon="mdi-format-text"
                    >
                      <template v-slot:append-inner>
                        <span class="text-caption text-grey mr-1">chars</span>
                        <v-tooltip location="top" max-width="400">
                          <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                          </template>
                          <div class="pa-2">
                            <div class="text-subtitle-2 mb-2">Characters Per Line</div>
                            <div class="text-body-2 mb-2">
                              Defines the approximate number of characters that fit comfortably on one line at the default font size for 1920x1080 full-screen display.
                            </div>
                            <div class="text-body-2 mb-2">
                              <strong>Typography guidelines:</strong>
                            </div>
                            <ul class="text-body-2 mb-2">
                              <li><strong>40-50 chars:</strong> Optimal for TV viewing from 8-10 feet, excellent readability</li>
                              <li><strong>50-60 chars:</strong> Good balance, standard for most quotes</li>
                              <li><strong>60-75 chars:</strong> Still readable but approaching the limit</li>
                              <li><strong>75-90 chars:</strong> Maximum - viewers may lose their place between lines</li>
                            </ul>
                            <div class="text-body-2">
                              <strong>Note:</strong> This is based on average character width. Words with more narrow letters (like "illill") fit more per line than wide letters (like "WWWWW").
                            </div>
                          </div>
                        </v-tooltip>
                      </template>
                    </v-text-field>
                  </v-col>
                </v-row>

                <v-divider class="my-4"></v-divider>

                <!-- Secondary Controls: Split Behavior -->
                <div class="text-subtitle-2 mb-3 font-weight-bold">Split Behavior</div>

                <v-row>
                  <v-col cols="6">
                    <v-text-field
                      v-model.number="localSettings.fsq_min_second_screen"
                      label="Minimum Second Screen Length"
                      type="number"
                      min="40"
                      max="150"
                      variant="outlined"
                      density="compact"
                      hint="Prevents orphan text (40-150 chars)"
                      persistent-hint
                      prepend-inner-icon="mdi-text-box-remove-outline"
                    >
                      <template v-slot:append-inner>
                        <span class="text-caption text-grey mr-1">chars</span>
                        <v-tooltip location="top" max-width="450">
                          <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                          </template>
                          <div class="pa-2">
                            <div class="text-subtitle-2 mb-2">Minimum Second Screen Length (Orphan Prevention)</div>
                            <div class="text-body-2 mb-2">
                              Prevents creating a second screen with very little text ("orphan" text) that looks awkward or unprofessional.
                            </div>
                            <div class="text-body-2 mb-2">
                              <strong>How it works:</strong>
                            </div>
                            <div class="text-body-2 mb-2">
                              If splitting at the max limit would leave less than this value on the second screen, the AI will instead split closer to the middle to balance the content evenly.
                            </div>
                            <div class="text-body-2 mb-2">
                              <strong>Example with Max=250, Min=80:</strong>
                            </div>
                            <ul class="text-body-2 mb-2">
                              <li><strong>280 char quote:</strong> Normal split at 250 would leave only 30 chars (too short). System splits at 140/140 instead.</li>
                              <li><strong>400 char quote:</strong> Split at 250 leaves 150 chars (adequate). Normal split applies.</li>
                            </ul>
                            <div class="text-body-2 mb-2">
                              <strong>Recommended values:</strong>
                            </div>
                            <ul class="text-body-2">
                              <li><strong>60-70 chars:</strong> Aggressive - allows shorter second screens (~1 line)</li>
                              <li><strong>80-100 chars:</strong> Recommended - ensures ~1.5-2 lines minimum</li>
                              <li><strong>100-150 chars:</strong> Conservative - guarantees substantial second screen</li>
                            </ul>
                          </div>
                        </v-tooltip>
                      </template>
                    </v-text-field>
                  </v-col>

                  <v-col cols="6">
                    <v-select
                      v-model="localSettings.fsq_split_strategy"
                      label="Split Strategy"
                      :items="splitStrategyOptions"
                      variant="outlined"
                      density="compact"
                      hint="How to handle borderline quotes"
                      persistent-hint
                      prepend-inner-icon="mdi-call-split"
                    >
                      <template v-slot:append-inner>
                        <v-tooltip location="top" max-width="450">
                          <template v-slot:activator="{ props }">
                            <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                          </template>
                          <div class="pa-2">
                            <div class="text-subtitle-2 mb-2">Split Strategy</div>
                            <div class="text-body-2 mb-2">
                              Controls how the AI decides when and where to split quotes that are close to the character limit.
                            </div>
                            <div class="text-body-2 mb-2">
                              <strong>Strategy Options:</strong>
                            </div>
                            <ul class="text-body-2 mb-2">
                              <li class="mb-1">
                                <strong>Smart Balance (Recommended):</strong> Uses intelligent logic - splits at max limit for long quotes, but balances quotes near the threshold to prevent orphans. Best overall approach.
                              </li>
                              <li class="mb-1">
                                <strong>Always Balance:</strong> Always splits quotes near the middle point, even if one screen could fit. More conservative, ensures similar-length screens.
                              </li>
                              <li class="mb-1">
                                <strong>Strict Limit:</strong> Always splits exactly at the max character limit, no balancing. May create short second screens.
                              </li>
                              <li class="mb-1">
                                <strong>AI Decides:</strong> Lets the AI service make all split decisions without using your threshold settings. Most flexible but least predictable.
                              </li>
                            </ul>
                            <div class="text-body-2">
                              <strong>Recommendation:</strong> Use "Smart Balance" for the best combination of readability and orphan prevention.
                            </div>
                          </div>
                        </v-tooltip>
                      </template>
                    </v-select>
                  </v-col>
                </v-row>

                <v-divider class="my-4"></v-divider>

                <!-- Tertiary Controls: Fine-tuning -->
                <v-expansion-panels variant="accordion" class="mb-3">
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <v-icon class="mr-2">mdi-tune</v-icon>
                      Advanced Split Tuning
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-row>
                        <v-col cols="6">
                          <v-text-field
                            v-model.number="localSettings.fsq_balance_threshold_percent"
                            label="Balance Threshold"
                            type="number"
                            min="10"
                            max="50"
                            suffix="%"
                            variant="outlined"
                            density="compact"
                            hint="Extra capacity % before forcing split"
                            persistent-hint
                          >
                            <template v-slot:append-inner>
                              <v-tooltip location="top" max-width="450">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                                </template>
                                <div class="pa-2">
                                  <div class="text-subtitle-2 mb-2">Balance Threshold Percentage</div>
                                  <div class="text-body-2 mb-2">
                                    Defines the "gray zone" where quotes are close enough to the limit that balancing makes more sense than strict splitting.
                                  </div>
                                  <div class="text-body-2 mb-2">
                                    <strong>How it works:</strong>
                                  </div>
                                  <div class="text-body-2 mb-2">
                                    This percentage is added to your minimum second screen value to create a threshold. Quotes within this range will be balanced instead of split at the max limit.
                                  </div>
                                  <div class="text-body-2 mb-2">
                                    <strong>Calculation:</strong> Balance Threshold = Max Screen 1 + (Min Second Screen × Percent)
                                  </div>
                                  <div class="text-body-2 mb-2">
                                    <strong>Example with 30%:</strong>
                                  </div>
                                  <ul class="text-body-2 mb-2">
                                    <li>Max Screen 1: 250 chars</li>
                                    <li>Min Second: 80 chars</li>
                                    <li>Balance Threshold: 250 + (80 × 0.30) = 274 chars</li>
                                    <li>Quotes 251-274 chars → balanced split</li>
                                    <li>Quotes 275+ chars → standard split at 250</li>
                                  </ul>
                                  <div class="text-body-2">
                                    <strong>Higher %</strong> = larger gray zone, more balancing. <strong>Lower %</strong> = stricter adherence to max limit.
                                  </div>
                                </div>
                              </v-tooltip>
                            </template>
                          </v-text-field>
                        </v-col>

                        <v-col cols="6">
                          <div class="d-flex align-center">
                            <v-switch
                              v-model="localSettings.fsq_prefer_sentence_boundaries"
                              label="Prefer Sentence Boundaries"
                              color="primary"
                              density="compact"
                              hint="Split at periods/punctuation when possible"
                              persistent-hint
                              hide-details="auto"
                            ></v-switch>
                            <v-tooltip location="top" max-width="400">
                              <template v-slot:activator="{ props }">
                                <v-icon v-bind="props" size="small" color="info" class="ml-2">mdi-information</v-icon>
                              </template>
                              <div class="pa-2">
                                <div class="text-subtitle-2 mb-2">Prefer Sentence Boundaries</div>
                                <div class="text-body-2 mb-2">
                                  When enabled, the AI will try to split quotes at natural sentence endings (periods, exclamation points, question marks) rather than in the middle of a sentence.
                                </div>
                                <div class="text-body-2 mb-2">
                                  <strong>Benefits:</strong>
                                </div>
                                <ul class="text-body-2 mb-2">
                                  <li>More natural reading flow - complete thoughts on each screen</li>
                                  <li>Viewers can absorb complete ideas before moving to next screen</li>
                                  <li>Professional presentation quality</li>
                                </ul>
                                <div class="text-body-2 mb-2">
                                  <strong>How it works:</strong> The AI searches within ±50 characters of the target split point for sentence-ending punctuation.
                                </div>
                                <div class="text-body-2">
                                  <strong>Recommendation:</strong> Keep this enabled for best readability.
                                </div>
                              </div>
                            </v-tooltip>
                          </div>
                        </v-col>
                      </v-row>

                      <v-row class="mt-2">
                        <v-col cols="6">
                          <div class="d-flex align-center">
                            <v-switch
                              v-model="localSettings.fsq_allow_mid_sentence_split"
                              label="Allow Mid-Sentence Splits"
                              color="primary"
                              density="compact"
                              hint="Split at commas/clauses if needed"
                              persistent-hint
                              hide-details="auto"
                            ></v-switch>
                            <v-tooltip location="top" max-width="400">
                              <template v-slot:activator="{ props }">
                                <v-icon v-bind="props" size="small" color="info" class="ml-2">mdi-information</v-icon>
                              </template>
                              <div class="pa-2">
                                <div class="text-subtitle-2 mb-2">Allow Mid-Sentence Splits</div>
                                <div class="text-body-2 mb-2">
                                  When enabled, if no sentence boundary is found near the split point, the AI can split at commas, semicolons, or dashes (natural pause points within sentences).
                                </div>
                                <div class="text-body-2 mb-2">
                                  <strong>Fallback hierarchy:</strong>
                                </div>
                                <ol class="text-body-2 mb-2">
                                  <li>Sentence endings (. ! ?) - within ±50 chars</li>
                                  <li>Clause breaks (, ; -) - within ±30 chars (if enabled)</li>
                                  <li>Word boundaries (spaces) - within ±20 chars</li>
                                  <li>Exact position (last resort)</li>
                                </ol>
                                <div class="text-body-2 mb-2">
                                  <strong>When to use:</strong> Enable for long, complex sentences where waiting for a period would exceed limits by too much.
                                </div>
                                <div class="text-body-2">
                                  <strong>Trade-off:</strong> More flexible splitting vs. potentially breaking mid-thought.
                                </div>
                              </div>
                            </v-tooltip>
                          </div>
                        </v-col>

                        <v-col cols="6">
                          <v-select
                            v-model="localSettings.fsq_overflow_handling"
                            label="Overflow Handling"
                            :items="overflowOptions"
                            variant="outlined"
                            density="compact"
                            hint="What to do with very long quotes"
                            persistent-hint
                          >
                            <template v-slot:append-inner>
                              <v-tooltip location="top" max-width="400">
                                <template v-slot:activator="{ props }">
                                  <v-icon v-bind="props" size="small" color="info">mdi-information</v-icon>
                                </template>
                                <div class="pa-2">
                                  <div class="text-subtitle-2 mb-2">Overflow Handling</div>
                                  <div class="text-body-2 mb-2">
                                    Controls what happens when quotes are extremely long and would require more than 2 screens.
                                  </div>
                                  <div class="text-body-2 mb-2">
                                    <strong>Options:</strong>
                                  </div>
                                  <ul class="text-body-2 mb-2">
                                    <li class="mb-1">
                                      <strong>Multiple Segments (Recommended):</strong> Creates 3, 4, or more FSQ screens as needed. Best for preserving complete quotes.
                                    </li>
                                    <li class="mb-1">
                                      <strong>Compress Text:</strong> Attempts to fit quote by reducing font size or line spacing. May impact readability.
                                    </li>
                                    <li class="mb-1">
                                      <strong>Truncate with Ellipsis:</strong> Cuts quote short with "..." to fit 2 screens max. Use only when full quote isn't essential.
                                    </li>
                                  </ul>
                                  <div class="text-body-2">
                                    <strong>Recommendation:</strong> Use "Multiple Segments" to preserve quote integrity.
                                  </div>
                                </div>
                              </v-tooltip>
                            </template>
                          </v-select>
                        </v-col>
                      </v-row>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>

                <!-- Live Calculation Display -->
                <v-card variant="tonal" color="indigo-lighten-5" class="pa-4">
                  <div class="text-subtitle-2 mb-2 font-weight-bold">
                    <v-icon size="small" class="mr-1">mdi-calculator</v-icon>
                    Live Split Calculation
                  </div>

                  <v-row dense>
                    <v-col cols="4">
                      <div class="text-caption text-grey">Max Screen 1</div>
                      <div class="text-h6 text-primary">
                        {{ maxCharsScreen1 }}
                        <span class="text-caption">chars</span>
                      </div>
                    </v-col>

                    <v-col cols="4">
                      <div class="text-caption text-grey">Balance Threshold</div>
                      <div class="text-h6 text-orange">
                        {{ balanceThreshold }}
                        <span class="text-caption">chars</span>
                      </div>
                    </v-col>

                    <v-col cols="4">
                      <div class="text-caption text-grey">Min Screen 2</div>
                      <div class="text-h6 text-green">
                        {{ localSettings.fsq_min_second_screen || 80 }}
                        <span class="text-caption">chars</span>
                      </div>
                    </v-col>
                  </v-row>

                  <v-divider class="my-3"></v-divider>

                  <!-- Visual Split Ranges -->
                  <div class="text-caption mb-2">Quote Length Behavior:</div>
                  <div class="split-behavior-guide">
                    <div class="behavior-range single">
                      <v-chip size="small" color="green" class="mr-2">Single Screen</v-chip>
                      <span class="text-caption">0 - {{ maxCharsScreen1 }} chars</span>
                    </div>
                    <div class="behavior-range balanced mt-1">
                      <v-chip size="small" color="orange" class="mr-2">Balanced Split</v-chip>
                      <span class="text-caption">
                        {{ maxCharsScreen1 + 1 }} - {{ balanceThreshold }} chars
                      </span>
                    </div>
                    <div class="behavior-range standard mt-1">
                      <v-chip size="small" color="blue" class="mr-2">Standard Split</v-chip>
                      <span class="text-caption">{{ balanceThreshold + 1 }}+ chars</span>
                    </div>
                  </div>
                </v-card>

                <!-- Example/Test Section -->
                <v-divider class="my-4"></v-divider>

                <v-expansion-panels variant="accordion">
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <v-icon class="mr-2">mdi-test-tube</v-icon>
                      Test Your Settings
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-textarea
                        v-model="testQuote"
                        label="Paste a test quote"
                        variant="outlined"
                        rows="3"
                        placeholder="Enter a quote to see how it would be split..."
                        @input="previewSplit"
                      ></v-textarea>

                      <div v-if="splitPreview" class="mt-3">
                        <v-alert :type="splitPreview.type" variant="tonal" density="compact">
                          <div class="text-subtitle-2 mb-1">
                            {{ splitPreview.title }}
                          </div>
                          <div class="text-caption">
                            Quote length: <strong>{{ testQuote.length }}</strong> chars |
                            Strategy: <strong>{{ splitPreview.strategy }}</strong> |
                            Segments: <strong>{{ splitPreview.segments.length }}</strong>
                          </div>
                        </v-alert>

                        <div v-for="(segment, idx) in splitPreview.segments" :key="idx" class="mt-2">
                          <v-card variant="outlined" class="pa-3">
                            <div class="text-caption text-grey mb-1">Screen {{ idx + 1 }}/{{ splitPreview.segments.length }}</div>
                            <div class="quote-preview">{{ segment }}</div>
                            <div class="text-caption text-grey mt-1">{{ segment.length }} characters</div>
                          </v-card>
                        </div>
                      </div>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>

              </v-card-text>
              </div>
            </v-card>
          </v-tabs-window-item>

          <!-- Scripts -->
          <v-tabs-window-item value="scripts">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-script-text</v-icon>
              Script Generation Settings
            </h3>
            <p class="text-body-2 mb-4">Configure settings for different script format outputs.</p>

            <v-expansion-panels variant="accordion" multiple>
              <!-- Host/Anchor Script Settings -->
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <div class="d-flex align-center">
                    <v-icon class="mr-2" color="primary">mdi-microphone</v-icon>
                    <span class="text-subtitle-1">Host/Anchor Script</span>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <p class="text-caption mb-3">Settings for the primary on-camera talent script format</p>

                  <v-row>
                    <v-col cols="6">
                      <v-switch
                        v-model="localSettings.script_host_include_cues"
                        label="Include Cue Blocks"
                        hint="Show [[CUE:...]] blocks in host script"
                        persistent-hint
                        density="comfortable"
                        color="primary"
                      />
                    </v-col>
                    <v-col cols="6">
                      <v-switch
                        v-model="localSettings.script_host_include_timestamps"
                        label="Include Timestamps"
                        hint="Show timing markers for segments"
                        persistent-hint
                        density="comfortable"
                        color="primary"
                      />
                    </v-col>
                  </v-row>

                  <v-divider class="my-4" />

                  <!-- Typography Settings -->
                  <h5 class="text-subtitle-2 mb-3">Typography Settings</h5>

                  <!-- Script Text -->
                  <v-row align="center" class="mb-2">
                    <v-col cols="4">
                      <span class="text-body-2">Script Text</span>
                    </v-col>
                    <v-col cols="4">
                      <v-select
                        v-model="localSettings.script_host_text_size"
                        :items="scriptFontSizeOptions"
                        label="Size"
                        variant="outlined"
                        density="compact"
                        hide-details
                      />
                    </v-col>
                    <v-col cols="4">
                      <div class="d-flex align-center">
                        <v-menu :close-on-content-click="false">
                          <template v-slot:activator="{ props }">
                            <v-btn
                              v-bind="props"
                              :color="localSettings.script_host_text_color || '#000000'"
                              size="small"
                              variant="flat"
                              class="color-picker-btn"
                            >
                              <v-icon size="small">mdi-palette</v-icon>
                            </v-btn>
                          </template>
                          <v-color-picker
                            v-model="localSettings.script_host_text_color"
                            mode="hex"
                            hide-inputs
                          />
                        </v-menu>
                        <span class="text-caption ml-2">{{ localSettings.script_host_text_color || '#000000' }}</span>
                      </div>
                    </v-col>
                  </v-row>

                  <!-- Segment Header -->
                  <v-row align="center" class="mb-2">
                    <v-col cols="4">
                      <span class="text-body-2">Segment Header</span>
                    </v-col>
                    <v-col cols="4">
                      <v-select
                        v-model="localSettings.script_host_segment_header_size"
                        :items="scriptFontSizeOptions"
                        label="Size"
                        variant="outlined"
                        density="compact"
                        hide-details
                      />
                    </v-col>
                    <v-col cols="4">
                      <div class="d-flex align-center">
                        <v-menu :close-on-content-click="false">
                          <template v-slot:activator="{ props }">
                            <v-btn
                              v-bind="props"
                              :color="localSettings.script_host_segment_header_color || '#1976D2'"
                              size="small"
                              variant="flat"
                              class="color-picker-btn"
                            >
                              <v-icon size="small">mdi-palette</v-icon>
                            </v-btn>
                          </template>
                          <v-color-picker
                            v-model="localSettings.script_host_segment_header_color"
                            mode="hex"
                            hide-inputs
                          />
                        </v-menu>
                        <span class="text-caption ml-2">{{ localSettings.script_host_segment_header_color || '#1976D2' }}</span>
                      </div>
                    </v-col>
                  </v-row>

                  <!-- Block Header -->
                  <v-row align="center" class="mb-2">
                    <v-col cols="4">
                      <span class="text-body-2">Block Header</span>
                    </v-col>
                    <v-col cols="4">
                      <v-select
                        v-model="localSettings.script_host_block_header_size"
                        :items="scriptFontSizeOptions"
                        label="Size"
                        variant="outlined"
                        density="compact"
                        hide-details
                      />
                    </v-col>
                    <v-col cols="4">
                      <div class="d-flex align-center">
                        <v-menu :close-on-content-click="false">
                          <template v-slot:activator="{ props }">
                            <v-btn
                              v-bind="props"
                              :color="localSettings.script_host_block_header_color || '#FF5722'"
                              size="small"
                              variant="flat"
                              class="color-picker-btn"
                            >
                              <v-icon size="small">mdi-palette</v-icon>
                            </v-btn>
                          </template>
                          <v-color-picker
                            v-model="localSettings.script_host_block_header_color"
                            mode="hex"
                            hide-inputs
                          />
                        </v-menu>
                        <span class="text-caption ml-2">{{ localSettings.script_host_block_header_color || '#FF5722' }}</span>
                      </div>
                    </v-col>
                  </v-row>

                  <v-divider class="my-4" />

                  <!-- Line Height -->
                  <v-row>
                    <v-col cols="6">
                      <v-select
                        v-model="localSettings.script_host_line_height"
                        :items="lineHeightOptions"
                        label="Line Height"
                        variant="outlined"
                        density="comfortable"
                        hint="Line spacing for readability"
                        persistent-hint
                      />
                    </v-col>
                  </v-row>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <!-- Director Script Settings -->
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <div class="d-flex align-center">
                    <v-icon class="mr-2" color="secondary">mdi-video-vintage</v-icon>
                    <span class="text-subtitle-1">Director Script</span>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <p class="text-caption mb-3">Settings for technical direction and production notes</p>

                  <v-row>
                    <v-col cols="6">
                      <v-switch
                        v-model="localSettings.script_director_include_technical_notes"
                        label="Include Technical Notes"
                        hint="Show camera angles, lighting cues, etc."
                        persistent-hint
                        density="comfortable"
                        color="secondary"
                      />
                    </v-col>
                    <v-col cols="6">
                      <v-switch
                        v-model="localSettings.script_director_include_timecodes"
                        label="Include Timecodes"
                        hint="Show precise timing for all segments"
                        persistent-hint
                        density="comfortable"
                        color="secondary"
                      />
                    </v-col>
                  </v-row>

                  <v-row>
                    <v-col cols="12">
                      <v-switch
                        v-model="localSettings.script_director_include_media_list"
                        label="Include Media Asset List"
                        hint="Append full list of media assets referenced in show"
                        persistent-hint
                        density="comfortable"
                        color="secondary"
                      />
                    </v-col>
                  </v-row>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <!-- Prompter Operator Script Settings -->
              <v-expansion-panel>
                <v-expansion-panel-title>
                  <div class="d-flex align-center">
                    <v-icon class="mr-2" color="info">mdi-monitor-eye</v-icon>
                    <span class="text-subtitle-1">Prompter Operator Script</span>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <p class="text-caption mb-3">Settings for teleprompter display and operation</p>

                  <v-row>
                    <v-col cols="6">
                      <v-switch
                        v-model="localSettings.script_prompter_strip_all_cues"
                        label="Strip All Cues"
                        hint="Remove [[CUE:...]] blocks for clean prompter display"
                        persistent-hint
                        density="comfortable"
                        color="info"
                      />
                    </v-col>
                    <v-col cols="6">
                      <v-switch
                        v-model="localSettings.script_prompter_large_text"
                        label="Large Text Mode"
                        hint="Optimize for large display readability"
                        persistent-hint
                        density="comfortable"
                        color="info"
                      />
                    </v-col>
                  </v-row>

                  <v-row>
                    <v-col cols="6">
                      <v-select
                        v-model="localSettings.script_prompter_scroll_speed"
                        :items="scrollSpeedOptions"
                        label="Default Scroll Speed"
                        variant="outlined"
                        density="comfortable"
                        hint="Recommended scroll speed (WPM based)"
                        persistent-hint
                      />
                    </v-col>
                    <v-col cols="6">
                      <v-switch
                        v-model="localSettings.script_prompter_pause_markers"
                        label="Include Pause Markers"
                        hint="Show [PAUSE] indicators for timing"
                        persistent-hint
                        density="comfortable"
                        color="info"
                      />
                    </v-col>
                  </v-row>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <!-- Future Generic Scripts (Greyed Out) -->
              <v-expansion-panel disabled>
                <v-expansion-panel-title>
                  <div class="d-flex align-center text-grey">
                    <v-icon class="mr-2" color="grey">mdi-file-document-outline</v-icon>
                    <span class="text-subtitle-1">Generic Script 1</span>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <p class="text-caption text-grey-lighten-1">Custom script format (Coming Soon)</p>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel disabled>
                <v-expansion-panel-title>
                  <div class="d-flex align-center text-grey">
                    <v-icon class="mr-2" color="grey">mdi-file-document-outline</v-icon>
                    <span class="text-subtitle-1">Generic Script 2</span>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <p class="text-caption text-grey-lighten-1">Custom script format (Coming Soon)</p>
                </v-expansion-panel-text>
              </v-expansion-panel>

              <v-expansion-panel disabled>
                <v-expansion-panel-title>
                  <div class="d-flex align-center text-grey">
                    <v-icon class="mr-2" color="grey">mdi-file-document-outline</v-icon>
                    <span class="text-subtitle-1">Generic Script 3</span>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <p class="text-caption text-grey-lighten-1">Custom script format (Coming Soon)</p>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-tabs-window-item>

          <!-- LLM Routing -->
          <v-tabs-window-item value="llm-routing">
            <LLMRoutingSettings
              v-model="llmSettings"
              @save="handleLLMSave"
            />
          </v-tabs-window-item>

          <!-- Media Assets -->
          <v-tabs-window-item value="media-assets">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-folder-image</v-icon>
              Media Assets
            </h3>
            <p class="text-body-2 mb-4">Configure paths to shared media library for backgrounds, graphics, and audio.</p>

            <v-card variant="tonal" color="primary" class="mb-4" :class="collapsedSections.mediaRoot ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.mediaRoot ? 'mb-0' : 'mb-3'" @click="collapsedSections.mediaRoot = !collapsedSections.mediaRoot" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.mediaRoot ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                <v-icon left class="mr-2">mdi-folder-image</v-icon>
                Media Assets Root
              </h4>
              <div v-show="!collapsedSections.mediaRoot">
              <v-text-field
                v-model="localSettings.mediaAssetsPath"
                label="Media Assets Path"
                placeholder="/mnt/sync/disaffected/media assets"
                variant="outlined"
                density="comfortable"
                hint="Root path for all shared media assets"
                persistent-hint
              />
              </div>
            </v-card>

            <v-card variant="outlined" class="mb-4" :class="collapsedSections.mediaCategories ? 'pa-2' : 'pa-4'">
              <h4 class="text-subtitle-1 d-flex align-center section-toggle" :class="collapsedSections.mediaCategories ? 'mb-0' : 'mb-3'" @click="collapsedSections.mediaCategories = !collapsedSections.mediaCategories" style="cursor: pointer;">
                <v-icon class="mr-2" size="small">{{ collapsedSections.mediaCategories ? 'mdi-chevron-right' : 'mdi-chevron-down' }}</v-icon>
                Media Asset Categories
              </h4>
              <div v-show="!collapsedSections.mediaCategories">
              <v-list density="compact">
                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-video</v-icon>
                  </template>
                  <v-list-item-title>Video Assets</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.mediaAssetsPath }}/video/</v-list-item-subtitle>
                </v-list-item>

                <v-list-subheader>Video Subcategories</v-list-subheader>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-video-outline</v-icon>
                  </template>
                  <v-list-item-subtitle>Backgrounds: {{ localSettings.mediaAssetsPath }}/video/backgrounds/</v-list-item-subtitle>
                </v-list-item>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-video-outline</v-icon>
                  </template>
                  <v-list-item-subtitle>Templates: {{ localSettings.mediaAssetsPath }}/video/templates/</v-list-item-subtitle>
                </v-list-item>

                <v-divider class="my-2" />

                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-music</v-icon>
                  </template>
                  <v-list-item-title>Audio Assets</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.mediaAssetsPath }}/audio/</v-list-item-subtitle>
                </v-list-item>

                <v-list-subheader>Audio Subcategories</v-list-subheader>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-music-note</v-icon>
                  </template>
                  <v-list-item-subtitle>Music: {{ localSettings.mediaAssetsPath }}/audio/music/</v-list-item-subtitle>
                </v-list-item>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-waveform</v-icon>
                  </template>
                  <v-list-item-subtitle>SFX: {{ localSettings.mediaAssetsPath }}/audio/sfx/</v-list-item-subtitle>
                </v-list-item>

                <v-divider class="my-2" />

                <v-list-item>
                  <template #prepend>
                    <v-icon>mdi-image</v-icon>
                  </template>
                  <v-list-item-title>Graphics Assets</v-list-item-title>
                  <v-list-item-subtitle>{{ localSettings.mediaAssetsPath }}/graphics/</v-list-item-subtitle>
                </v-list-item>

                <v-list-subheader>Graphics Subcategories</v-list-subheader>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-format-quote-close</v-icon>
                  </template>
                  <v-list-item-subtitle>FSQ Templates: {{ localSettings.mediaAssetsPath }}/graphics/fsq-templates/</v-list-item-subtitle>
                </v-list-item>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-text-box</v-icon>
                  </template>
                  <v-list-item-subtitle>Lower Thirds: {{ localSettings.mediaAssetsPath }}/graphics/lower-thirds/</v-list-item-subtitle>
                </v-list-item>
                <v-list-item class="pl-8">
                  <template #prepend>
                    <v-icon size="small">mdi-transition</v-icon>
                  </template>
                  <v-list-item-subtitle>Transitions: {{ localSettings.mediaAssetsPath }}/graphics/transitions/</v-list-item-subtitle>
                </v-list-item>
              </v-list>
              </div>
            </v-card>

            <v-alert type="success" variant="tonal">
              <v-alert-title>Source Video</v-alert-title>
              Current background source: <code>/mnt/sync/disaffected/media assets/video/backgrounds/background-branded-slow.mp4</code>
            </v-alert>
          </v-tabs-window-item>

        </v-tabs-window>
      </v-col>
    </v-row>

    <!-- Save Button (Fixed at bottom of card) -->
    <v-card-actions class="px-4 pb-4 border-t">
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="save" variant="elevated">
        <v-icon left>mdi-content-save</v-icon>
        Save Generation Settings
      </v-btn>
    </v-card-actions>

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
  </v-card>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick, getCurrentInstance } from 'vue';
import LLMRoutingSettings from './LLMRoutingSettings.vue' // eslint-disable-line no-unused-vars
import { CORE_ITEM_TYPES, getAllItemTypes } from '@/config/itemTypes'
import { useUserPrefs } from '@/composables/useUserPrefs'

const _userPrefs = useUserPrefs()

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      fsqBackgroundVideo: '/assets/preview-background.mp4',
      fsqDefaultAlignment: 'left',
      fsqDefaultFont: 'sans-serif',
      fsqDefaultFontSize: 30,
      fsqIncludeAttributionByDefault: true,
      fsqMaxLines: 4,
      fsqCharsPerLine: 70,
      templateLibraryPath: '/mnt/sync/disaffected/templates',
      mediaAssetsPath: '/mnt/sync/disaffected/media assets'
    })
  }
});

const emit = defineEmits(['update:modelValue', 'save']);

const instance = getCurrentInstance();
const $axios = instance.appContext.config.globalProperties.$axios;

// Template refs
const episodePromptTextarea = ref(null)
const segmentPromptTextarea = ref(null)
const tonePromptTextarea = ref(null)

// Reactive state
const generationSubTab = ref('real-content');
// Real Content Generator settings
const showIdentityPanel = ref(null);
const descriptionPanels = ref([]);
const socialMediaPanels = ref([]);
const savingRealContent = ref(false);
const savingEpisodeDescription = ref(false);
const savingSegmentDescription = ref(false);
// Tracks whether segmentDescription has unsaved edits since the last save.
// `false` = synchronized; `true` = dirty. The first `watch` tick fires on
// initial load, so we gate it with `segmentDescriptionWatchReady` to avoid
// marking the panel dirty the moment the component mounts.
const segmentDescriptionDirty = ref(false);
const segmentDescriptionWatchReady = ref(false);
const savingShowIdentity = ref(false);
const savingTonePalette = ref(false);

// Collapsible sections — all expanded by default
const collapsedSections = ref({})
const showConditionalHelp = ref(false);
const newToneInput = ref('');

// Default tone palette seeded for a show with Disaffected's editorial voice.
// Users can add, remove, or reset to these defaults from the Tone Palette
// settings section.
const DEFAULT_TONE_PALETTE = Object.freeze([
  'serious',
  'somber',
  'skeptical',
  'irreverent',
  'sarcastic',
  'lighthearted',
  'urgent',
  'analytical',
  'mocking'
]);

const realContentSettings = ref({
  showIdentity: {
    name: 'Disaffected',
    thesis: '',
    tone: '',
    audience: ''
  },
  tonePalette: [...DEFAULT_TONE_PALETTE],
  toneGeneration: {
    model: '',
    temperature: 0.1,
    prompt: 'Classify the editorial tone of this broadcast segment. Choose exactly ONE tone from this list: {{tone_palette}}.\n\nRespond ONLY with valid JSON: {"tone": "<chosen tone>", "confidence": <0.0-1.0>, "rationale": "<one sentence>"}\n\nSegment title: {{segment_title}}\nSegment type: {{segment_type}}\n\nFull segment content:\n{{segment_content}}'
  },
  episodeDescription: {
    enabled: true,
    injectShowIdentity: true,
    prompt: 'Generate a compelling episode description that captures the key topics, guests, and takeaways.',
    minLength: 100,
    maxLength: 500,
    temperature: 0.4,
    model: '',
    includeTitle: true,
    includeGuestInfo: true,
    itemTypes: {
      segment: true,
      interview: true
    },
    weightSegmentDescriptions: true,
    mentionSpeaker: true,
    exposeSpecialInstructions: true,
    allowInteractiveIteration: true,
    llmPreferenceOrder: [],
    priorityOrder: [
      { id: 1, tag: 'breaking', label: 'Breaking News', color: '#c62828' },
      { id: 2, tag: 'top-story', label: 'Top Story', color: '#d32f2f' },
      { id: 3, tag: 'main-feature', label: 'Main Feature', color: '#b71c1c' },
      { id: 4, tag: 'second-feature', label: 'Second Feature', color: '#e64a19' },
      { id: 5, tag: 'third-feature', label: 'Third Feature', color: '#f57c00' },
      { id: 6, tag: 'deep-dive', label: 'Deep Dive', color: '#1565c0' },
      { id: 7, tag: 'kicker', label: 'Kicker', color: '#43a047' }
    ]
  },
  segmentDescription: {
    enabled: true,
    injectShowIdentity: true,
    includeFullText: true,
    includeAdjacentContext: false,
    exposeSpecialInstructions: false,
    allowInteractiveIteration: false,
    temperature: 0.4,
    model: '',
    prompt: 'Write a concise, engaging description for the "{{segment_title}}" segment of {{show_name}} Episode {{episode_number}}.\n\nSegment type: {{segment_type}}\nDuration: {{segment_duration}}\n\n{% if has_tone %}Editorial tone: {{segment_tone}} — {{segment_tone_rationale}}\nWrite the description in that tone.\n\n{% endif %}Content:\n{{segment_content}}\n\n{% if has_adjacent_context %}Adjacent context:\nPrevious: {{adjacent_previous}}\nNext: {{adjacent_next}}\n\n{% endif %}Requirements:\n- 2-3 sentences\n- Capture the key idea and why it matters\n- Match the segment tone, show voice, and audience'
  },
  imageDescription: {
    enabled: false,
    prompt: 'Generate descriptive alt text for this image suitable for accessibility and SEO.',
    includeAltText: true
  },
  socialMedia: {
    x: {
      enabled: false,
      defaultPrompt: 'Create an engaging tweet about this content with relevant hashtags.',
      maxLength: 280,
      includeHashtags: true,
      includeThreads: false
    },
    meta: {
      enabled: false,
      defaultPrompt: 'Create an engaging Facebook post about this content.',
      postType: 'Standard Post',
      includeEmoji: true,
      crossPostInstagram: false
    },
    substack: {
      enabled: false,
      defaultPrompt: 'Create newsletter content summarizing this episode.',
      contentType: 'Show Notes',
      targetWordCount: 500,
      includeTimestamps: true
    }
  }
});

const availableLLMServices = [
  { title: 'Ollama (Local)', value: 'ollama', icon: 'mdi-server' },
  { title: 'OpenAI', value: 'openai', icon: 'mdi-robot' },
  { title: 'Anthropic', value: 'anthropic', icon: 'mdi-head-cog' },
  { title: 'Gemini', value: 'gemini', icon: 'mdi-google' },
  { title: 'Grok', value: 'grok', icon: 'mdi-twitter' }
];

const llmServiceModels = ref({
  ollama: [],
  openai: [
    { title: 'GPT-4o', value: 'gpt-4o' },
    { title: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
    { title: 'GPT-4', value: 'gpt-4' },
    { title: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' }
  ],
  anthropic: [
    { title: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022' },
    { title: 'Claude 3 Opus', value: 'claude-3-opus-20240229' },
    { title: 'Claude 3 Haiku', value: 'claude-3-haiku-20240307' }
  ],
  gemini: [
    { title: 'Gemini 2.0 Flash', value: 'gemini-2.0-flash' },
    { title: 'Gemini 1.5 Pro', value: 'gemini-1.5-pro' },
    { title: 'Gemini 1.5 Flash', value: 'gemini-1.5-flash' }
  ],
  grok: [
    { title: 'Grok 4', value: 'grok-4-latest' },
    { title: 'Grok 3', value: 'grok-3' }
  ]
});

// Test Content Generator settings
const testContentService = ref('ollama');
const testContentModel = ref('llama3:latest');
const savingTestContent = ref(false);
const availableOllamaModels = ref([]);
const ollamaModelOptions = computed(() => availableOllamaModels.value.map(m => ({ title: m, value: m })))
const testContentServiceOptions = [
  { title: 'Auto (Smart Routing)', value: 'auto' },
  { title: 'Ollama (Local)', value: 'ollama' },
  { title: 'OpenAI', value: 'openai' },
  { title: 'Anthropic', value: 'anthropic' },
  { title: 'Gemini', value: 'gemini' },
  { title: 'Grok', value: 'grok' }
];
const testContentModelOptions = ref([]);

const localSettings = ref({
  ...props.modelValue,
  fsq_min_second_screen: props.modelValue.fsq_min_second_screen || 80,
  fsq_split_strategy: props.modelValue.fsq_split_strategy || 'smart',
  fsq_balance_threshold_percent: props.modelValue.fsq_balance_threshold_percent || 30,
  fsq_prefer_sentence_boundaries: props.modelValue.fsq_prefer_sentence_boundaries !== undefined ? props.modelValue.fsq_prefer_sentence_boundaries : true,
  fsq_allow_mid_sentence_split: props.modelValue.fsq_allow_mid_sentence_split !== undefined ? props.modelValue.fsq_allow_mid_sentence_split : false,
  fsq_overflow_handling: props.modelValue.fsq_overflow_handling || 'multi_segment',
  fsq_strip_exterior_quotes: props.modelValue.fsq_strip_exterior_quotes !== undefined ? props.modelValue.fsq_strip_exterior_quotes : true,
  fsq_regenerate_exterior_quotes: props.modelValue.fsq_regenerate_exterior_quotes !== undefined ? props.modelValue.fsq_regenerate_exterior_quotes : false,
  fsq_normalize_interior_quotes: props.modelValue.fsq_normalize_interior_quotes !== undefined ? props.modelValue.fsq_normalize_interior_quotes : true,
  fsq_attribution_dash_style: props.modelValue.fsq_attribution_dash_style || 'regular',
  script_host_include_cues: props.modelValue.script_host_include_cues !== undefined ? props.modelValue.script_host_include_cues : true,
  script_host_include_timestamps: props.modelValue.script_host_include_timestamps !== undefined ? props.modelValue.script_host_include_timestamps : false,
  script_host_font_size: props.modelValue.script_host_font_size || '14pt',
  script_host_line_height: props.modelValue.script_host_line_height || '1.5',
  script_host_text_size: props.modelValue.script_host_text_size || '12pt',
  script_host_text_color: props.modelValue.script_host_text_color || '#000000',
  script_host_segment_header_size: props.modelValue.script_host_segment_header_size || '18pt',
  script_host_segment_header_color: props.modelValue.script_host_segment_header_color || '#1976D2',
  script_host_block_header_size: props.modelValue.script_host_block_header_size || '24pt',
  script_host_block_header_color: props.modelValue.script_host_block_header_color || '#FF5722',
  script_director_include_technical_notes: props.modelValue.script_director_include_technical_notes !== undefined ? props.modelValue.script_director_include_technical_notes : true,
  script_director_include_timecodes: props.modelValue.script_director_include_timecodes !== undefined ? props.modelValue.script_director_include_timecodes : true,
  script_director_include_media_list: props.modelValue.script_director_include_media_list !== undefined ? props.modelValue.script_director_include_media_list : true,
  script_prompter_strip_all_cues: props.modelValue.script_prompter_strip_all_cues !== undefined ? props.modelValue.script_prompter_strip_all_cues : true,
  script_prompter_large_text: props.modelValue.script_prompter_large_text !== undefined ? props.modelValue.script_prompter_large_text : true,
  script_prompter_scroll_speed: props.modelValue.script_prompter_scroll_speed || '160',
  script_prompter_pause_markers: props.modelValue.script_prompter_pause_markers !== undefined ? props.modelValue.script_prompter_pause_markers : false
});

const llmSettings = ref({
  routing: {
    quoteSplitting: 'auto',
    slugGeneration: 'auto',
    scriptSummary: 'auto',
    titleGeneration: 'auto',
    contentExpansion: 'auto',
    entityExtraction: 'auto',
    peopleSearch: 'auto',
    socialSearch: 'auto',
    tweetComposing: 'auto',
    factChecking: 'auto',
    enableFallback: true,
    fallbackOrder: ['ollama', 'openai', 'anthropic', 'gemini', 'grok']
  },
  prompts: []
});

const alignmentOptions = [
  { title: 'Left Aligned', value: 'left' },
  { title: 'Centered', value: 'centered' },
  { title: 'Right Aligned', value: 'right' }
];
const fontOptions = [
  { title: 'Sans Serif (Helvetica)', value: 'sans-serif' },
  { title: 'Serif (Georgia)', value: 'serif' },
  { title: 'Monospace (Courier)', value: 'monospace' }
];
const splitStrategyOptions = [
  { title: 'Smart Balance (Recommended)', value: 'smart' },
  { title: 'Always Balance', value: 'always_balance' },
  { title: 'Strict Limit', value: 'strict_limit' },
  { title: 'AI Decides', value: 'ai_only' }
];
const attributionDashOptions = [
  { title: 'Regular Dash (\u2014)', value: 'regular' },
  { title: 'Em Dash (\u2014)', value: 'emdash' },
  { title: 'No Dash (just space)', value: 'none' }
];
const overflowOptions = [
  { title: 'Multiple Segments', value: 'multi_segment' },
  { title: 'Compress Text', value: 'compress' },
  { title: 'Truncate with Ellipsis', value: 'truncate' }
];
const fontSizeOptions = [ // eslint-disable-line no-unused-vars
  { title: '12pt (Small)', value: '12pt' },
  { title: '14pt (Medium)', value: '14pt' },
  { title: '16pt (Large)', value: '16pt' },
  { title: '18pt (Extra Large)', value: '18pt' },
  { title: '20pt (Huge)', value: '20pt' }
];
const scriptFontSizeOptions = [
  { title: '10pt', value: '10pt' },
  { title: '11pt', value: '11pt' },
  { title: '12pt', value: '12pt' },
  { title: '14pt', value: '14pt' },
  { title: '16pt', value: '16pt' },
  { title: '18pt', value: '18pt' },
  { title: '20pt', value: '20pt' },
  { title: '22pt', value: '22pt' },
  { title: '24pt', value: '24pt' },
  { title: '28pt', value: '28pt' },
  { title: '32pt', value: '32pt' },
  { title: '36pt', value: '36pt' }
];
const lineHeightOptions = [
  { title: 'Single (1.0)', value: '1.0' },
  { title: 'Compact (1.2)', value: '1.2' },
  { title: 'Normal (1.5)', value: '1.5' },
  { title: 'Double (2.0)', value: '2.0' },
  { title: 'Triple (3.0)', value: '3.0' }
];
const scrollSpeedOptions = [
  { title: 'Very Slow (120 WPM)', value: '120' },
  { title: 'Slow (140 WPM)', value: '140' },
  { title: 'Normal (160 WPM)', value: '160' },
  { title: 'Fast (180 WPM)', value: '180' },
  { title: 'Very Fast (200 WPM)', value: '200' }
];
const testQuote = ref('');
const splitPreview = ref(null);
const snackbar = ref({
  show: false,
  message: '',
  color: 'error',
  timeout: 5000
});

// Computed
const isShowIdentityComplete = computed(() => { // eslint-disable-line no-unused-vars
  const identity = realContentSettings.value?.showIdentity || {}
  return !!(identity.thesis && identity.tone && identity.audience)
});

const showIdentityStatus = computed(() => {
  const identity = realContentSettings.value?.showIdentity || {}
  const filled = [identity.thesis, identity.tone, identity.audience].filter(v => v && v.trim()).length
  if (filled === 3) return 'complete'
  if (filled > 0) return 'partial'
  return 'empty'
});

const maxCharsScreen1 = computed(() => {
  return (localSettings.value.fsq_max_lines || 5) * (localSettings.value.fsq_chars_per_line || 50)
});

const balanceThreshold = computed(() => {
  const maxChars = maxCharsScreen1.value
  const minSecond = localSettings.value.fsq_min_second_screen || 80
  const percent = (localSettings.value.fsq_balance_threshold_percent || 30) / 100
  return Math.round(maxChars + (minSecond * percent))
});

const availableItemTypes = computed(() => {
  return getAllItemTypes()
});

const coreItemTypes = computed(() => { // eslint-disable-line no-unused-vars
  return CORE_ITEM_TYPES
});

const allAvailableLLMs = computed(() => {
  const llms = []
  availableLLMServices.forEach(service => {
    const models = llmServiceModels.value[service.value] || []
    if (models.length > 0) {
      models.forEach(model => {
        llms.push({
          title: `${service.title} - ${model.title}`,
          value: `${service.value}:${model.value}`,
          service: service.value,
          model: model.value,
          icon: service.icon
        })
      })
    } else {
      llms.push({
        title: `${service.title} (Auto)`,
        value: `${service.value}:auto`,
        service: service.value,
        model: 'auto',
        icon: service.icon
      })
    }
  })
  return llms
});

// Watchers
watch(() => props.modelValue, (newVal) => {
  localSettings.value = { ...newVal }
}, { deep: true });

watch(testContentService, () => {
  updateTestContentModelOptions()
});

// Initialize itemTypes from CORE_ITEM_TYPES config (equivalent to created() hook)
const defaultEnabledTypes = ['segment', 'interview']
CORE_ITEM_TYPES.forEach(type => {
  realContentSettings.value.episodeDescription.itemTypes[type.value] = defaultEnabledTypes.includes(type.value)
});

// Methods
function showSnackbar(message, color = 'error') {
  snackbar.value.message = message
  snackbar.value.color = color
  snackbar.value.show = true
}

function save() {
  emit('update:modelValue', localSettings.value)
  emit('save', localSettings.value)
}

async function saveShowIdentity() {
  savingShowIdentity.value = true
  try {
    await $axios.post('/settings/show_identity', {
      key: 'show_identity',
      value: realContentSettings.value.showIdentity
    })
    showSnackbar('Show identity saved successfully', 'success')
  } catch (error) {
    console.error('Failed to save show identity:', error)
    showSnackbar('Failed to save show identity', 'error')
  } finally {
    savingShowIdentity.value = false
  }
}

// --- Tone Palette -----------------------------------------------------------
function addTone() {
  const raw = (newToneInput.value || '').trim()
  if (!raw) return
  // Normalize: lowercase, collapse whitespace. Prevents duplicate entries
  // that differ only by casing/spacing.
  const normalized = raw.toLowerCase().replace(/\s+/g, ' ')
  const existing = realContentSettings.value.tonePalette.map(t => t.toLowerCase())
  if (existing.includes(normalized)) {
    showSnackbar(`"${normalized}" is already in the palette`, 'warning')
    newToneInput.value = ''
    return
  }
  realContentSettings.value.tonePalette.push(normalized)
  newToneInput.value = ''
}

function removeTone(index) {
  realContentSettings.value.tonePalette.splice(index, 1)
}

function resetTonePaletteToDefaults() {
  realContentSettings.value.tonePalette = [...DEFAULT_TONE_PALETTE]
  showSnackbar('Tone palette reset to defaults', 'success')
}

async function saveTonePalette() {
  savingTonePalette.value = true
  try {
    // localStorage stays as the offline cache + sync surface for components
    // (MetadataPanel etc.) that read it directly.
    localStorage.setItem('real-content-settings', JSON.stringify(realContentSettings.value))
    localStorage.setItem('real-content-settings-version', String(REAL_CONTENT_SETTINGS_VERSION))
    // Per-user pref is the source of truth across devices.
    _userPrefs.set('content.editor', realContentSettings.value)

    // Persist tone generation settings to backend
    const tg = realContentSettings.value.toneGeneration
    await Promise.all([
      fetch('/api/settings/generation-prompts/tone_classification/prompt', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: tg.prompt || '' })
      }),
      fetch('/api/settings/generation-prompts/tone_classification/model', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: tg.model || '' })
      }),
      fetch('/api/settings/generation-prompts/tone_classification/temperature', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: String(tg.temperature ?? 0.1) })
      })
    ])

    showSnackbar('Tone generation settings saved', 'success')
  } catch (error) {
    console.error('Failed to save tone generation:', error)
    showSnackbar('Failed to save tone generation settings', 'error')
  } finally {
    savingTonePalette.value = false
  }
}

async function loadShowIdentity() {
  try {
    const response = await $axios.get('/settings/show_identity')
    if (response.data && response.data.value) {
      realContentSettings.value.showIdentity = {
        ...realContentSettings.value.showIdentity,
        ...response.data.value
      }
      console.log('Loaded show identity from database')
    }
  } catch (error) { // eslint-disable-line no-unused-vars
    console.warn('No show identity found in database, using defaults')
  }
}

async function loadLLMSettings() {
  try {
    const response = await $axios.get('/settings/llm_routing')
    if (response.data && response.data.value) {
      llmSettings.value = response.data.value
      console.log('Loaded LLM routing settings from database:', llmSettings.value)
    }
  } catch (error) {
    console.warn('Failed to load LLM settings from database, using defaults:', error)
  }
}

async function handleLLMSave(settings) {
  llmSettings.value = settings

  try {
    await $axios.post('/settings/llm_routing', {
      key: 'llm_routing',
      value: settings,
      category: 'generation'
    })
    console.log('LLM routing settings saved to database:', settings)

    emit('save', localSettings.value)
  } catch (error) {
    console.error('Failed to save LLM settings to database:', error)
    showSnackbar('Failed to save LLM routing settings')
  }
}

function previewSplit() {
  if (!testQuote.value) {
    splitPreview.value = null
    return
  }

  const config = {
    maxChars: maxCharsScreen1.value,
    minSecond: localSettings.value.fsq_min_second_screen || 80,
    balanceThreshold: balanceThreshold.value
  }

  const length = testQuote.value.length

  if (length <= config.maxChars) {
    splitPreview.value = {
      type: 'success',
      title: 'Fits on single screen',
      strategy: 'Single Screen',
      segments: [testQuote.value]
    }
  } else if (length <= config.balanceThreshold) {
    const mid = Math.floor(length / 2)
    const splitPoint = findSplitPoint(testQuote.value, mid)
    splitPreview.value = {
      type: 'warning',
      title: 'Will be balanced split',
      strategy: 'Balanced',
      segments: [
        testQuote.value.substring(0, splitPoint).trim(),
        testQuote.value.substring(splitPoint).trim()
      ]
    }
  } else {
    const splitPoint = findSplitPoint(testQuote.value, config.maxChars)
    const remainder = testQuote.value.substring(splitPoint).trim()

    if (remainder.length < config.minSecond) {
      splitPreview.value = {
        type: 'error',
        title: 'Would create orphan text - will rebalance',
        strategy: 'Forced Balance',
        segments: [
          testQuote.value.substring(0, Math.floor(length / 2)).trim(),
          testQuote.value.substring(Math.floor(length / 2)).trim()
        ]
      }
    } else {
      splitPreview.value = {
        type: 'info',
        title: 'Will be standard split',
        strategy: 'Standard',
        segments: [
          testQuote.value.substring(0, splitPoint).trim(),
          remainder
        ]
      }
    }
  }
}

function findSplitPoint(text, target) {
  if (!localSettings.value.fsq_prefer_sentence_boundaries) {
    return target
  }

  const sentences = ['. ', '! ', '? ']
  for (const punct of sentences) {
    const idx = text.lastIndexOf(punct, target)
    if (idx > target - 50 && idx < target + 50) {
      return idx + 2
    }
  }

  if (localSettings.value.fsq_allow_mid_sentence_split) {
    const clauses = [', ', '; ', ' - ']
    for (const punct of clauses) {
      const idx = text.lastIndexOf(punct, target)
      if (idx > target - 30 && idx < target + 30) {
        return idx + 2
      }
    }
  }

  const spaceIdx = text.lastIndexOf(' ', target)
  if (spaceIdx > target - 20) {
    return spaceIdx + 1
  }

  return target
}

async function loadTestContentSettings() {
  const saved = localStorage.getItem('llm-routing-settings')
  if (saved) {
    try {
      const settings = JSON.parse(saved)
      const contentExpansion = settings.routing?.contentExpansion || 'auto'
      if (contentExpansion === 'auto') {
        testContentService.value = 'auto'
        testContentModel.value = null
      } else if (contentExpansion.includes(':')) {
        const parts = contentExpansion.split(':')
        testContentService.value = parts[0]
        testContentModel.value = parts.slice(1).join(':')
      } else {
        testContentService.value = contentExpansion
        testContentModel.value = null
      }
      if (settings.ollamaModels?.contentExpansion) {
        testContentModel.value = settings.ollamaModels.contentExpansion
      }
    } catch (e) {
      console.error('Failed to parse llm-routing-settings:', e)
    }
  }
}

async function loadOllamaModels() {
  try {
    const response = await fetch('/api/llm/ollama/models', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      availableOllamaModels.value = data.models?.map(m => m.name) || []
      llmServiceModels.value.ollama = availableOllamaModels.value.map(m => ({
        title: m,
        value: m
      }))
      console.log('Loaded Ollama models:', availableOllamaModels.value)
      updateTestContentModelOptions()
    } else {
      loadFallbackModels()
    }
  } catch (e) {
    console.error('Failed to load Ollama models:', e)
    loadFallbackModels()
  }
}

function loadFallbackModels() {
  availableOllamaModels.value = [
    'llama3:latest',
    'mistral:7b',
    'deepseek-r1:8b',
    'Qwen2.5-Coder:7b',
    'codellama:34b'
  ]
  llmServiceModels.value.ollama = availableOllamaModels.value.map(m => ({
    title: m,
    value: m
  }))
  updateTestContentModelOptions()
}

function updateTestContentModelOptions() {
  if (testContentService.value === 'ollama') {
    testContentModelOptions.value = availableOllamaModels.value.map(m => ({
      title: m,
      value: m
    }))
  } else if (testContentService.value === 'openai') {
    testContentModelOptions.value = [
      { title: 'GPT-4', value: 'gpt-4' },
      { title: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
      { title: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' }
    ]
  } else if (testContentService.value === 'anthropic') {
    testContentModelOptions.value = [
      { title: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022' },
      { title: 'Claude 3 Opus', value: 'claude-3-opus-20240229' },
      { title: 'Claude 3 Haiku', value: 'claude-3-haiku-20240307' }
    ]
  } else if (testContentService.value === 'gemini') {
    testContentModelOptions.value = [
      { title: 'Gemini 2.0 Flash', value: 'gemini-2.0-flash' },
      { title: 'Gemini 1.5 Pro', value: 'gemini-1.5-pro' }
    ]
  } else if (testContentService.value === 'grok') {
    testContentModelOptions.value = [
      { title: 'Grok 4', value: 'grok-4-latest' },
      { title: 'Grok 3', value: 'grok-3' }
    ]
  } else {
    testContentModelOptions.value = []
  }
}

function selectOllamaModel(model) {
  testContentService.value = 'ollama'
  testContentModel.value = model
  updateTestContentModelOptions()
}

function saveTestContentSettings() {
  savingTestContent.value = true

  let settings = {}
  const saved = localStorage.getItem('llm-routing-settings')
  if (saved) {
    try {
      settings = JSON.parse(saved)
    } catch (e) { // eslint-disable-line no-unused-vars
      settings = {}
    }
  }

  if (!settings.routing) settings.routing = {}
  if (!settings.ollamaModels) settings.ollamaModels = {}

  if (testContentService.value === 'auto') {
    settings.routing.contentExpansion = 'auto'
  } else if (testContentModel.value) {
    settings.routing.contentExpansion = `${testContentService.value}:${testContentModel.value}`
    if (testContentService.value === 'ollama') {
      settings.ollamaModels.contentExpansion = testContentModel.value
    }
  } else {
    settings.routing.contentExpansion = testContentService.value
  }

  localStorage.setItem('llm-routing-settings', JSON.stringify(settings))
  _userPrefs.set('llm.routing', settings)

  console.log('Test Content Generator settings saved:', {
    service: testContentService.value,
    model: testContentModel.value,
    routing: settings.routing.contentExpansion
  })

  showSnackbar('Test content settings saved', 'success')

  setTimeout(() => {
    savingTestContent.value = false
  }, 500)
}

function resetTestContentToDefaults() {
  testContentService.value = 'ollama'
  testContentModel.value = 'llama3:latest'
  updateTestContentModelOptions()
  saveTestContentSettings()
}

function insertToneVariable(variable) {
  const comp = tonePromptTextarea.value
  const el = comp?.$el?.querySelector('textarea') || null
  const slot = realContentSettings.value.toneGeneration
  const current = slot.prompt || ''
  if (el && el === document.activeElement) {
    const start = el.selectionStart
    const end = el.selectionEnd
    slot.prompt = current.substring(0, start) + variable + current.substring(end)
    nextTick(() => { el.selectionStart = el.selectionEnd = start + variable.length; el.focus() })
  } else {
    slot.prompt = current + (current ? ' ' : '') + variable
    nextTick(() => { if (el) el.focus() })
  }
}

// --- Priority Order drag-and-drop ---
const newPriorityTag = ref('')
const newPriorityLabel = ref('')

function addPriorityOrderItem() {
  const tag = (newPriorityTag.value || '').trim().toLowerCase().replace(/\s+/g, '-')
  const label = (newPriorityLabel.value || '').trim() || tag
  if (!tag) return
  const list = realContentSettings.value.episodeDescription.priorityOrder
  if (list.some(p => p.tag === tag)) return
  list.push({ id: Date.now(), tag, label, color: '#757575' })
  newPriorityTag.value = ''
  newPriorityLabel.value = ''
}

function removePriorityOrderItem(index) {
  realContentSettings.value.episodeDescription.priorityOrder.splice(index, 1)
}

function markEpisodeDescDirty() {
  // Trigger reactivity after drag
  realContentSettings.value.episodeDescription.priorityOrder = [...realContentSettings.value.episodeDescription.priorityOrder]
}

function addLLMPreference() {
  realContentSettings.value.episodeDescription.llmPreferenceOrder.push('')
}

function removeLLMPreference(index) {
  realContentSettings.value.episodeDescription.llmPreferenceOrder.splice(index, 1)
}

function moveLLMPreferenceUp(index) {
  if (index > 0) {
    const prefs = realContentSettings.value.episodeDescription.llmPreferenceOrder
    const temp = prefs[index]
    prefs[index] = prefs[index - 1]
    prefs[index - 1] = temp
  }
}

function moveLLMPreferenceDown(index) {
  const prefs = realContentSettings.value.episodeDescription.llmPreferenceOrder
  if (index < prefs.length - 1) {
    const temp = prefs[index]
    prefs[index] = prefs[index + 1]
    prefs[index + 1] = temp
  }
}

function getLLMDisplayName(value) { // eslint-disable-line no-unused-vars
  if (!value) return 'Select LLM...'
  const llm = allAvailableLLMs.value.find(l => l.value === value)
  return llm ? llm.title : value
}

function promptTarget(target) {
  // Map a target key ('episode' | 'segment') to the right settings slot.
  return target === 'segment'
    ? realContentSettings.value.segmentDescription
    : realContentSettings.value.episodeDescription
}

function getPromptTextarea(target) {
  const comp = target === 'segment' ? segmentPromptTextarea.value : episodePromptTextarea.value
  if (!comp) return null
  // Vuetify v-textarea: the actual <textarea> is nested inside
  return comp.$el?.querySelector('textarea') || null
}

function insertAtCursor(text, target = 'episode') {
  const slot = promptTarget(target)
  const el = getPromptTextarea(target)
  const currentPrompt = slot.prompt || ''

  if (el && el === document.activeElement) {
    // Insert at cursor position
    const start = el.selectionStart
    const end = el.selectionEnd
    slot.prompt = currentPrompt.substring(0, start) + text + currentPrompt.substring(end)
    // Restore cursor after the inserted text
    nextTick(() => {
      el.selectionStart = el.selectionEnd = start + text.length
      el.focus()
    })
  } else {
    // No cursor — append
    slot.prompt = currentPrompt + (currentPrompt ? '\n' : '') + text
    // Focus the textarea after insert
    nextTick(() => { if (el) el.focus() })
  }
}

function insertVariable(variable, target = 'episode') {
  insertAtCursor(variable, target)
}

function insertConditional(condition, defaultContent, target = 'episode') {
  const block = `{% if ${condition} %}${defaultContent}{% endif %}`
  insertAtCursor(block, target)
}

function generateDefaultSegmentPrompt() {
  const s = realContentSettings.value.segmentDescription
  let prompt = 'Write a concise, engaging description for the "{{segment_title}}" segment of {{show_name}} Episode {{episode_number}}.\n\n'
  prompt += 'Segment type: {{segment_type}}\n'
  prompt += 'Duration: {{segment_duration}}\n'
  if (s.injectShowIdentity) {
    prompt += '\nShow identity:\n- Thesis: {{show_thesis}}\n- Tone: {{show_tone}}\n- Audience: {{show_audience}}\n'
  }
  // Tone is always injected when available — it's the most editorially
  // important signal for matching the segment's voice. Guarded by `has_tone`
  // so the block disappears cleanly when the classifier hasn't run yet.
  prompt += '\n{% if has_tone %}Editorial tone: {{segment_tone}} — {{segment_tone_rationale}}\nWrite the description in that tone.\n{% endif %}'
  if (s.includeFullText) {
    prompt += '\nFull segment content:\n{{segment_content}}\n'
  }
  if (s.includeAdjacentContext) {
    prompt += '\nAdjacent context:\nPrevious segment: {{adjacent_previous}}\nNext segment: {{adjacent_next}}\n'
  }
  prompt += '\nRequirements:\n- 2-3 sentences\n- Capture the key idea and why it matters\n- Match the segment tone, show voice, and audience'
  realContentSettings.value.segmentDescription.prompt = prompt
}

function generateDefaultEpisodePrompt() {
  const settings = realContentSettings.value.episodeDescription
  let prompt = 'Generate a compelling episode description for {{show_name}} Episode {{episode_number}}'

  if (settings.includeTitle) {
    prompt += ' titled "{{title}}"'
  }

  prompt += '.\n\n'

  if (settings.includeGuestInfo) {
    prompt += 'Featured guests: {{guest_names}}\n'
    prompt += 'Guest background: {{guest_bios}}\n\n'
  }

  if (settings.mentionSpeaker) {
    prompt += 'Hosted by {{host_name}}.\n\n'
  }

  prompt += 'Episode content summary:\n{{segment_summaries}}\n\n'

  if (settings.weightSegmentDescriptions) {
    prompt += 'Key weighted content:\n{{weighted_content}}\n\n'
  }

  prompt += 'Main topics covered: {{topics}}\n\n'

  prompt += 'Requirements:\n'
  prompt += `- Length: ${settings.minLength}-${settings.maxLength} characters\n`
  prompt += '- Tone: Professional, engaging, informative\n'
  prompt += '- Include key takeaways and highlights\n'
  prompt += '- Optimized for search and social sharing'

  realContentSettings.value.episodeDescription.prompt = prompt
}

// Informational only — bumped when defaults change so we can log/trace
// migrations. We NEVER wipe user-saved values on a version mismatch; the
// load path always deep-merges the saved blob over the current defaults so
// any new default fields appear while user-overridden values are preserved.
const REAL_CONTENT_SETTINGS_VERSION = 5

async function loadRealContentSettings() {
  // Per-user pref wins. Fall back to localStorage on first migration.
  const fromPrefs = _userPrefs.get('content.editor', null)
  if (fromPrefs && typeof fromPrefs === 'object') {
    realContentSettings.value = deepMerge(realContentSettings.value, fromPrefs)
    localStorage.setItem('real-content-settings', JSON.stringify(realContentSettings.value))
    localStorage.setItem('real-content-settings-version', String(REAL_CONTENT_SETTINGS_VERSION))
    console.log('Loaded real content settings (per-user pref):', realContentSettings.value)
  } else {
    const saved = localStorage.getItem('real-content-settings')
    if (!saved) {
      localStorage.setItem('real-content-settings', JSON.stringify(realContentSettings.value))
      localStorage.setItem('real-content-settings-version', String(REAL_CONTENT_SETTINGS_VERSION))
    } else {
      try {
        const settings = JSON.parse(saved)
        realContentSettings.value = deepMerge(realContentSettings.value, settings)
        localStorage.setItem('real-content-settings-version', String(REAL_CONTENT_SETTINGS_VERSION))
        // Migrate legacy localStorage value forward into the per-user pref.
        _userPrefs.set('content.editor', realContentSettings.value)
        console.log('Loaded real content settings (migrated from localStorage):', realContentSettings.value)
      } catch (e) {
        console.error('Failed to parse real-content-settings:', e)
      }
    }
  }

  // Sync prompts from backend (authoritative source for Celery sweeper)
  try {
    const resp = await fetch('/api/settings/generation-prompts')
    if (resp.ok) {
      const data = await resp.json()
      if (data.prompts?.segment_description?.prompt) {
        realContentSettings.value.segmentDescription.prompt = data.prompts.segment_description.prompt
        if (data.prompts.segment_description.temperature !== undefined) {
          realContentSettings.value.segmentDescription.temperature = parseFloat(data.prompts.segment_description.temperature) || 0.4
        }
        if (data.prompts.segment_description.model) {
          realContentSettings.value.segmentDescription.model = data.prompts.segment_description.model
        }
        console.log('Loaded segment description settings from backend')
      }
      if (data.prompts?.episode_description) {
        const ep = data.prompts.episode_description
        if (ep.prompt) realContentSettings.value.episodeDescription.prompt = ep.prompt
        if (ep.enabled !== undefined) realContentSettings.value.episodeDescription.enabled = ep.enabled === 'true'
        if (ep.item_types) {
          try { realContentSettings.value.episodeDescription.itemTypes = JSON.parse(ep.item_types) } catch (e) { /* ignore */ }
        }
        if (ep.min_length) realContentSettings.value.episodeDescription.minLength = parseInt(ep.min_length) || 100
        if (ep.max_length) realContentSettings.value.episodeDescription.maxLength = parseInt(ep.max_length) || 500
        if (ep.priority_order) {
          try { realContentSettings.value.episodeDescription.priorityOrder = JSON.parse(ep.priority_order) } catch (e) { /* ignore */ }
        }
        if (ep.temperature !== undefined) realContentSettings.value.episodeDescription.temperature = parseFloat(ep.temperature) || 0.4
        if (ep.model) realContentSettings.value.episodeDescription.model = ep.model
        console.log('Loaded episode description settings from backend')
      }
      if (data.prompts?.tone_classification) {
        const tc = data.prompts.tone_classification
        if (tc.prompt) realContentSettings.value.toneGeneration.prompt = tc.prompt
        if (tc.model) realContentSettings.value.toneGeneration.model = tc.model
        if (tc.temperature !== undefined) realContentSettings.value.toneGeneration.temperature = parseFloat(tc.temperature) || 0.1
        console.log('Loaded tone classification settings from backend')
      }
    }
  } catch (e) {
    console.warn('Could not load generation prompts from backend:', e)
  }
}

function deepMerge(target, source) {
  const result = { ...target }
  for (const key in source) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      result[key] = deepMerge(target[key] || {}, source[key])
    } else {
      result[key] = source[key]
    }
  }
  return result
}

async function saveEpisodeDescriptionSettings() {
  savingEpisodeDescription.value = true

  localStorage.setItem('real-content-settings', JSON.stringify(realContentSettings.value))
  localStorage.setItem('real-content-settings-version', String(REAL_CONTENT_SETTINGS_VERSION))

  // Persist all episode description settings to backend for Celery sweeper
  try {
    const settings = realContentSettings.value.episodeDescription
    const saves = [
      fetch('/api/settings/generation-prompts/episode_description/prompt', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: settings.prompt || '' })
      }),
      fetch('/api/settings/generation-prompts/episode_description/enabled', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: String(settings.enabled) })
      }),
      fetch('/api/settings/generation-prompts/episode_description/item_types', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: JSON.stringify(settings.itemTypes || {}) })
      }),
      fetch('/api/settings/generation-prompts/episode_description/min_length', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: String(settings.minLength || 100) })
      }),
      fetch('/api/settings/generation-prompts/episode_description/max_length', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: String(settings.maxLength || 500) })
      }),
      fetch('/api/settings/generation-prompts/episode_description/priority_order', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: JSON.stringify(settings.priorityOrder || []) })
      }),
      fetch('/api/settings/generation-prompts/episode_description/temperature', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: String(settings.temperature ?? 0.4) })
      }),
      fetch('/api/settings/generation-prompts/episode_description/model', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: settings.model || '' })
      })
    ]
    await Promise.all(saves)
    console.log('Episode description settings synced to backend')
  } catch (e) {
    console.warn('Failed to sync episode settings to backend:', e)
  }

  console.log('Episode Description settings saved:', realContentSettings.value.episodeDescription)

  showSnackbar('Episode description settings saved', 'success')

  setTimeout(() => {
    savingEpisodeDescription.value = false
  }, 500)
}

async function saveSegmentDescriptionSettings() {
  savingSegmentDescription.value = true

  localStorage.setItem('real-content-settings', JSON.stringify(realContentSettings.value))
  localStorage.setItem('real-content-settings-version', String(REAL_CONTENT_SETTINGS_VERSION))

  // Persist prompt to backend so the Celery sweeper uses it
  try {
    const prompt = realContentSettings.value.segmentDescription.prompt || ''
    await Promise.all([
      fetch('/api/settings/generation-prompts/segment_description/prompt', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: prompt })
      }),
      fetch('/api/settings/generation-prompts/segment_description/temperature', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: String(realContentSettings.value.segmentDescription.temperature ?? 0.4) })
      }),
      fetch('/api/settings/generation-prompts/segment_description/model', {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: realContentSettings.value.segmentDescription.model || '' })
      })
    ])
    console.log('Segment description settings synced to backend')
  } catch (e) {
    console.warn('Failed to sync prompt to backend:', e)
  }

  console.log('Segment Description settings saved:', realContentSettings.value.segmentDescription)

  showSnackbar('Segment description settings saved', 'success')

  // Mark the panel as synchronized. The deep watcher on segmentDescription
  // will flip it back to dirty the next time the user edits anything here.
  segmentDescriptionDirty.value = false

  setTimeout(() => {
    savingSegmentDescription.value = false
  }, 500)
}

function saveRealContentSettings() {
  savingRealContent.value = true

  localStorage.setItem('real-content-settings', JSON.stringify(realContentSettings.value))
  localStorage.setItem('real-content-settings-version', String(REAL_CONTENT_SETTINGS_VERSION))

  console.log('Real Content settings saved:', realContentSettings.value)

  showSnackbar('Real content settings saved', 'success')

  setTimeout(() => {
    savingRealContent.value = false
  }, 500)
}

// Lifecycle
onMounted(() => {
  loadLLMSettings()
  loadTestContentSettings()
  loadOllamaModels()
  loadRealContentSettings()
  loadShowIdentity()
  // Arm the segment-description dirty watcher AFTER the initial load so
  // the restored values don't count as "user edits".
  nextTick(() => {
    segmentDescriptionWatchReady.value = true
  })
});

// Mark segmentDescription dirty on any user-facing change. Any save clears
// the flag. The ready gate prevents the load path from tripping this.
watch(
  () => realContentSettings.value.segmentDescription,
  () => {
    if (!segmentDescriptionWatchReady.value) return
    segmentDescriptionDirty.value = true
  },
  { deep: true }
)
</script>

<style scoped>
.border-r {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.border-t {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.generation-vertical-tabs {
  height: 100%;
}

.v-card {
  border-radius: 8px;
}

.disabled-section {
  opacity: 0.5;
  pointer-events: none;
}

.color-picker-btn {
  min-width: 36px !important;
  width: 36px;
  height: 36px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.color-picker-btn .v-icon {
  color: white;
  text-shadow: 0 0 2px rgba(0, 0, 0, 0.5);
}

/* Description panel background colors */
.desc-panel-episode {
  background: rgba(33, 150, 243, 0.08) !important;
}

.desc-panel-segment {
  background: rgba(76, 175, 80, 0.08) !important;
}

.desc-panel-image {
  background: rgba(156, 39, 176, 0.08) !important;
}

.desc-panel-episode :deep(.v-expansion-panel-title),
.desc-panel-segment :deep(.v-expansion-panel-title),
.desc-panel-image :deep(.v-expansion-panel-title) {
  background: transparent;
}

/* Show Identity status colors */
.show-identity-complete {
  background: rgba(76, 175, 80, 0.15) !important;
}

.show-identity-partial {
  background: rgba(255, 193, 7, 0.15) !important;
}

.show-identity-empty {
  background: rgba(244, 67, 54, 0.15) !important;
}

.show-identity-panel :deep(.v-expansion-panel-title) {
  background: transparent;
}

.cursor-pointer {
  cursor: pointer;
}

.cursor-pointer:hover {
  opacity: 0.85;
  transform: scale(1.03);
}

/* Insertion chips — larger, square corners, high contrast white text */
.template-vars-grid :deep(.v-chip),
.template-vars-grid + .template-vars-grid :deep(.v-chip) {
  border-radius: 2px !important;
  font-size: 0.8rem !important;
  height: 26px !important;
  font-weight: 600 !important;
  letter-spacing: 0.2px;
  color: white !important;
}

.insert-chip :deep(.v-chip__content) {
  color: white !important;
}

/* Priority order drag list */
.priority-order-list {
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  padding: 4px;
}

.priority-order-item {
  padding: 4px 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  cursor: default;
}

.priority-order-item:last-child {
  border-bottom: none;
}

.priority-order-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.priority-drag-handle {
  cursor: grab;
}

.priority-drag-handle:active {
  cursor: grabbing;
}

.priority-order-label {
  font-size: 0.82rem;
  font-weight: 500;
}

/* Template variables grid */
.template-vars-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.var-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.var-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.7;
}

.conditional-help-table {
  background: transparent !important;
  font-size: 12px;
}

.conditional-help-table th {
  font-size: 11px !important;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 8px 12px !important;
}

.conditional-help-table td {
  padding: 6px 12px !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.conditional-help-table code {
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
}

.section-toggle:hover {
  opacity: 0.8;
}
</style>
