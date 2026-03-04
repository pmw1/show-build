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
                    <v-textarea
                      v-model="realContentSettings.showIdentity.thesis"
                      label="Show Thesis / Mission"
                      hint="The core purpose, perspective, or objective of the show. What is it about? What does it stand for?"
                      persistent-hint
                      variant="outlined"
                      density="compact"
                      rows="3"
                      class="mb-3"
                    />
                    <v-textarea
                      v-model="realContentSettings.showIdentity.tone"
                      label="Tone & Voice"
                      hint="How should content sound? (e.g., skeptical, irreverent, fact-based, conversational)"
                      persistent-hint
                      variant="outlined"
                      density="compact"
                      rows="2"
                      class="mb-3"
                    />
                    <v-textarea
                      v-model="realContentSettings.showIdentity.audience"
                      label="Target Audience"
                      hint="Who is this show for? What do they care about?"
                      persistent-hint
                      variant="outlined"
                      density="compact"
                      rows="2"
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

            <!-- Descriptions Section -->
            <v-card variant="outlined" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon class="mr-2">mdi-text-box-outline</v-icon>
                Descriptions
              </h4>
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
                              <v-chip size="x-small" variant="outlined" @click="insertVariable('{{episode_number}}')" class="cursor-pointer">
                                {{episode_number}}
                              </v-chip>
                              <v-chip size="x-small" variant="outlined" @click="insertVariable('{{show_name}}')" class="cursor-pointer">
                                {{show_name}}
                              </v-chip>
                              <v-chip size="x-small" variant="outlined" @click="insertVariable('{{air_date}}')" class="cursor-pointer">
                                {{air_date}}
                              </v-chip>
                              <v-chip size="x-small" variant="outlined" @click="insertVariable('{{duration}}')" class="cursor-pointer">
                                {{duration}}
                              </v-chip>
                            </div>
                          </div>

                          <!-- Title (conditional) -->
                          <div v-if="realContentSettings.episodeDescription.includeTitle" class="var-group">
                            <span class="var-label text-blue">Title</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="flat" color="blue" @click="insertVariable('{{title}}')" class="cursor-pointer">
                                {{title}}
                              </v-chip>
                            </div>
                          </div>

                          <!-- Guest Info (conditional) -->
                          <div v-if="realContentSettings.episodeDescription.includeGuestInfo" class="var-group">
                            <span class="var-label text-teal">Guest Info</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="flat" color="teal" @click="insertVariable('{{guest_names}}')" class="cursor-pointer">
                                {{guest_names}}
                              </v-chip>
                              <v-chip size="x-small" variant="flat" color="teal" @click="insertVariable('{{guest_bios}}')" class="cursor-pointer">
                                {{guest_bios}}
                              </v-chip>
                            </div>
                          </div>

                          <!-- Speaker (conditional) -->
                          <div v-if="realContentSettings.episodeDescription.mentionSpeaker" class="var-group">
                            <span class="var-label text-orange">Speaker</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="flat" color="orange" @click="insertVariable('{{speaker_name}}')" class="cursor-pointer">
                                {{speaker_name}}
                              </v-chip>
                              <v-chip size="x-small" variant="flat" color="orange" @click="insertVariable('{{host_name}}')" class="cursor-pointer">
                                {{host_name}}
                              </v-chip>
                            </div>
                          </div>

                          <!-- Content -->
                          <div class="var-group">
                            <span class="var-label text-green">Content</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="flat" color="green" @click="insertVariable('{{segment_summaries}}')" class="cursor-pointer">
                                {{segment_summaries}}
                              </v-chip>
                              <v-chip size="x-small" variant="flat" color="green" @click="insertVariable('{{segment_titles}}')" class="cursor-pointer">
                                {{segment_titles}}
                              </v-chip>
                              <v-chip v-if="realContentSettings.episodeDescription.weightSegmentDescriptions" size="x-small" variant="flat" color="purple" @click="insertVariable('{{weighted_content}}')" class="cursor-pointer">
                                {{weighted_content}}
                              </v-chip>
                            </div>
                          </div>

                          <!-- Topics & Quotes -->
                          <div class="var-group">
                            <span class="var-label">Topics & Quotes</span>
                            <div class="d-flex flex-wrap ga-1">
                              <v-chip size="x-small" variant="outlined" @click="insertVariable('{{topics}}')" class="cursor-pointer">
                                {{topics}}
                              </v-chip>
                              <v-chip size="x-small" variant="outlined" @click="insertVariable('{{key_quotes}}')" class="cursor-pointer">
                                {{key_quotes}}
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
                                <tr class="text-pink">
                                  <td><code>has_quotes</code></td>
                                  <td>Episode has key quotes extracted from content</td>
                                </tr>
                                <tr class="text-pink">
                                  <td><code>has_topics</code></td>
                                  <td>Episode has topics/tags assigned</td>
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

                          <!-- Data Availability -->
                          <div class="var-group">
                            <span class="var-label text-pink">Data Checks</span>
                            <div class="d-flex flex-wrap ga-1">
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
            </v-card>

            <!-- Social Media Section -->
            <v-card variant="outlined" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon class="mr-2">mdi-share-variant</v-icon>
                Social Media
              </h4>
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
            </v-card>

            <!-- Production Content Features (existing) -->
            <v-card variant="outlined" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon class="mr-2">mdi-text-box-check</v-icon>
                Production Content Features
              </h4>
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

            <v-card variant="outlined" class="pa-4 mb-4">
              <v-card-title class="text-subtitle-1 pa-0 mb-3">
                <v-icon class="mr-2">mdi-keyboard</v-icon>
                Keyboard Shortcut
              </v-card-title>
              <v-card-text class="pa-0">
                <p class="text-body-2 mb-2">
                  Triggered by <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>Shift</kbd>+<kbd>[1-9]</kbd> where the number is paragraph count.
                </p>
                <v-alert type="info" variant="tonal" density="compact">
                  <strong>How it works:</strong> Select a rundown item, press the hotkey, and the LLM will generate broadcast-style script content based on the segment type and duration.
                </v-alert>
              </v-card-text>
            </v-card>

            <v-card variant="outlined" class="pa-4 mb-4">
              <v-card-title class="text-subtitle-1 pa-0 mb-3">
                <v-icon class="mr-2">mdi-robot</v-icon>
                LLM Model Selection
              </v-card-title>
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
            </v-card>

            <v-card variant="outlined" class="pa-4">
              <v-card-title class="text-subtitle-1 pa-0 mb-3">
                <v-icon class="mr-2">mdi-server</v-icon>
                Available Ollama Models
              </v-card-title>
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
            </v-card>
          </v-tabs-window-item>

          <!-- FSQ Quote Generator -->
          <v-tabs-window-item value="fsq-generator">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-format-quote-close</v-icon>
              FSQ Quote Generator
            </h3>
            <p class="text-body-2 mb-4">Configure settings for Full Screen Quote generation and preview.</p>

            <v-card variant="tonal" color="deep-purple" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-video</v-icon>
                Preview Background Video
              </h4>
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
            </v-card>

            <v-card variant="tonal" color="deep-purple" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-palette</v-icon>
                Default FSQ Style
              </h4>
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
            </v-card>

            <v-card variant="outlined" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-cog</v-icon>
                Generation Options
              </h4>
              <v-checkbox
                v-model="localSettings.fsq_include_attribution_by_default"
                label="Include attribution by default"
                hint="When enabled, the attribution radio button will be pre-selected to 'Include Attribution'"
                persistent-hint
                density="comfortable"
              />
            </v-card>

            <v-card variant="outlined" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-format-quote-close</v-icon>
                Quote Formatting Rules
              </h4>

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
            </v-card>

            <v-card elevation="2" class="mb-4">
              <v-card-title class="bg-indigo-lighten-1 text-white">
                <v-icon class="mr-2">mdi-scissors-cutting</v-icon>
                FSQ Quote Splitting Rules
              </v-card-title>

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

            <v-card variant="tonal" color="primary" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-folder-image</v-icon>
                Media Assets Root
              </h4>
              <v-text-field
                v-model="localSettings.mediaAssetsPath"
                label="Media Assets Path"
                placeholder="/mnt/sync/disaffected/media assets"
                variant="outlined"
                density="comfortable"
                hint="Root path for all shared media assets"
                persistent-hint
              />
            </v-card>

            <v-card variant="outlined" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3">Media Asset Categories</h4>
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

<script>
import LLMRoutingSettings from './LLMRoutingSettings.vue'
import { CORE_ITEM_TYPES, getAllItemTypes } from '@/config/itemTypes'

export default {
  name: 'GenerationSettings',
  components: {
    LLMRoutingSettings
  },
  props: {
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
  },
  emits: ['update:modelValue', 'save'],
  data() {
    return {
      generationSubTab: 'real-content',
      // Real Content Generator settings
      showIdentityPanel: null,
      descriptionPanels: [],
      socialMediaPanels: [],
      savingRealContent: false,
      savingEpisodeDescription: false,
      savingShowIdentity: false,
      showConditionalHelp: false,
      realContentSettings: {
        showIdentity: {
          thesis: '',
          tone: '',
          audience: ''
        },
        episodeDescription: {
          enabled: false,
          injectShowIdentity: true,
          prompt: 'Generate a compelling episode description that captures the key topics, guests, and takeaways.',
          minLength: 100,
          maxLength: 500,
          // Content Sources
          includeTitle: true,
          includeGuestInfo: true,
          // itemTypes will be initialized dynamically in created() hook
          itemTypes: {},
          // Generation Options
          weightSegmentDescriptions: true,
          mentionSpeaker: true,
          exposeSpecialInstructions: false,
          allowInteractiveIteration: false,
          // LLM Preference Order
          llmPreferenceOrder: []
        },
        segmentDescription: {
          enabled: false,
          injectShowIdentity: true,
          // Content Options
          includeFullText: true,
          includeAdjacentContext: false,
          // Interaction Options
          exposeSpecialInstructions: false,
          allowInteractiveIteration: false
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
      },
      // Available LLM services and models for preference order
      availableLLMServices: [
        { title: 'Ollama (Local)', value: 'ollama', icon: 'mdi-server' },
        { title: 'OpenAI', value: 'openai', icon: 'mdi-robot' },
        { title: 'Anthropic', value: 'anthropic', icon: 'mdi-head-cog' },
        { title: 'Gemini', value: 'gemini', icon: 'mdi-google' },
        { title: 'Grok', value: 'grok', icon: 'mdi-twitter' }
      ],
      llmServiceModels: {
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
      },
      // Test Content Generator settings
      testContentService: 'ollama',
      testContentModel: 'llama3:latest',
      savingTestContent: false,
      availableOllamaModels: [],
      testContentServiceOptions: [
        { title: 'Auto (Smart Routing)', value: 'auto' },
        { title: 'Ollama (Local)', value: 'ollama' },
        { title: 'OpenAI', value: 'openai' },
        { title: 'Anthropic', value: 'anthropic' },
        { title: 'Gemini', value: 'gemini' },
        { title: 'Grok', value: 'grok' }
      ],
      testContentModelOptions: [],
      localSettings: {
        ...this.modelValue,
        // Initialize new FSQ split settings with defaults if not present (using snake_case to match backend)
        fsq_min_second_screen: this.modelValue.fsq_min_second_screen || 80,
        fsq_split_strategy: this.modelValue.fsq_split_strategy || 'smart',
        fsq_balance_threshold_percent: this.modelValue.fsq_balance_threshold_percent || 30,
        fsq_prefer_sentence_boundaries: this.modelValue.fsq_prefer_sentence_boundaries !== undefined ? this.modelValue.fsq_prefer_sentence_boundaries : true,
        fsq_allow_mid_sentence_split: this.modelValue.fsq_allow_mid_sentence_split !== undefined ? this.modelValue.fsq_allow_mid_sentence_split : false,
        fsq_overflow_handling: this.modelValue.fsq_overflow_handling || 'multi_segment',
        // Initialize new FSQ formatting settings with defaults
        fsq_strip_exterior_quotes: this.modelValue.fsq_strip_exterior_quotes !== undefined ? this.modelValue.fsq_strip_exterior_quotes : true,
        fsq_regenerate_exterior_quotes: this.modelValue.fsq_regenerate_exterior_quotes !== undefined ? this.modelValue.fsq_regenerate_exterior_quotes : false,
        fsq_normalize_interior_quotes: this.modelValue.fsq_normalize_interior_quotes !== undefined ? this.modelValue.fsq_normalize_interior_quotes : true,
        fsq_attribution_dash_style: this.modelValue.fsq_attribution_dash_style || 'regular',
        // Initialize Script settings with defaults
        script_host_include_cues: this.modelValue.script_host_include_cues !== undefined ? this.modelValue.script_host_include_cues : true,
        script_host_include_timestamps: this.modelValue.script_host_include_timestamps !== undefined ? this.modelValue.script_host_include_timestamps : false,
        script_host_font_size: this.modelValue.script_host_font_size || '14pt',
        script_host_line_height: this.modelValue.script_host_line_height || '1.5',
        // Typography settings for Host Script
        script_host_text_size: this.modelValue.script_host_text_size || '12pt',
        script_host_text_color: this.modelValue.script_host_text_color || '#000000',
        script_host_segment_header_size: this.modelValue.script_host_segment_header_size || '18pt',
        script_host_segment_header_color: this.modelValue.script_host_segment_header_color || '#1976D2',
        script_host_block_header_size: this.modelValue.script_host_block_header_size || '24pt',
        script_host_block_header_color: this.modelValue.script_host_block_header_color || '#FF5722',
        script_director_include_technical_notes: this.modelValue.script_director_include_technical_notes !== undefined ? this.modelValue.script_director_include_technical_notes : true,
        script_director_include_timecodes: this.modelValue.script_director_include_timecodes !== undefined ? this.modelValue.script_director_include_timecodes : true,
        script_director_include_media_list: this.modelValue.script_director_include_media_list !== undefined ? this.modelValue.script_director_include_media_list : true,
        script_prompter_strip_all_cues: this.modelValue.script_prompter_strip_all_cues !== undefined ? this.modelValue.script_prompter_strip_all_cues : true,
        script_prompter_large_text: this.modelValue.script_prompter_large_text !== undefined ? this.modelValue.script_prompter_large_text : true,
        script_prompter_scroll_speed: this.modelValue.script_prompter_scroll_speed || '160',
        script_prompter_pause_markers: this.modelValue.script_prompter_pause_markers !== undefined ? this.modelValue.script_prompter_pause_markers : false
      },
      llmSettings: {
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
      },
      alignmentOptions: [
        { title: 'Left Aligned', value: 'left' },
        { title: 'Centered', value: 'centered' },
        { title: 'Right Aligned', value: 'right' }
      ],
      fontOptions: [
        { title: 'Sans Serif (Helvetica)', value: 'sans-serif' },
        { title: 'Serif (Georgia)', value: 'serif' },
        { title: 'Monospace (Courier)', value: 'monospace' }
      ],
      splitStrategyOptions: [
        { title: 'Smart Balance (Recommended)', value: 'smart' },
        { title: 'Always Balance', value: 'always_balance' },
        { title: 'Strict Limit', value: 'strict_limit' },
        { title: 'AI Decides', value: 'ai_only' }
      ],
      attributionDashOptions: [
        { title: 'Regular Dash (—)', value: 'regular' },
        { title: 'Em Dash (—)', value: 'emdash' },
        { title: 'No Dash (just space)', value: 'none' }
      ],
      overflowOptions: [
        { title: 'Multiple Segments', value: 'multi_segment' },
        { title: 'Compress Text', value: 'compress' },
        { title: 'Truncate with Ellipsis', value: 'truncate' }
      ],
      fontSizeOptions: [
        { title: '12pt (Small)', value: '12pt' },
        { title: '14pt (Medium)', value: '14pt' },
        { title: '16pt (Large)', value: '16pt' },
        { title: '18pt (Extra Large)', value: '18pt' },
        { title: '20pt (Huge)', value: '20pt' }
      ],
      scriptFontSizeOptions: [
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
      ],
      lineHeightOptions: [
        { title: 'Single (1.0)', value: '1.0' },
        { title: 'Compact (1.2)', value: '1.2' },
        { title: 'Normal (1.5)', value: '1.5' },
        { title: 'Double (2.0)', value: '2.0' },
        { title: 'Triple (3.0)', value: '3.0' }
      ],
      scrollSpeedOptions: [
        { title: 'Very Slow (120 WPM)', value: '120' },
        { title: 'Slow (140 WPM)', value: '140' },
        { title: 'Normal (160 WPM)', value: '160' },
        { title: 'Fast (180 WPM)', value: '180' },
        { title: 'Very Fast (200 WPM)', value: '200' }
      ],
      testQuote: '',
      splitPreview: null,
      snackbar: {
        show: false,
        message: '',
        color: 'error',
        timeout: 5000
      }
    }
  },
  computed: {
    isShowIdentityComplete() {
      const identity = this.realContentSettings?.showIdentity || {}
      return !!(identity.thesis && identity.tone && identity.audience)
    },
    showIdentityStatus() {
      const identity = this.realContentSettings?.showIdentity || {}
      const filled = [identity.thesis, identity.tone, identity.audience].filter(v => v && v.trim()).length
      if (filled === 3) return 'complete'
      if (filled > 0) return 'partial'
      return 'empty'
    },
    maxCharsScreen1() {
      return (this.localSettings.fsq_max_lines || 5) * (this.localSettings.fsq_chars_per_line || 50)
    },
    balanceThreshold() {
      const maxChars = this.maxCharsScreen1
      const minSecond = this.localSettings.fsq_min_second_screen || 80
      const percent = (this.localSettings.fsq_balance_threshold_percent || 30) / 100
      return Math.round(maxChars + (minSecond * percent))
    },
    // Get available rundown item types from config
    availableItemTypes() {
      // Use getAllItemTypes to include both core and custom types
      return getAllItemTypes()
    },
    // Core item types only (for reference)
    coreItemTypes() {
      return CORE_ITEM_TYPES
    },
    // Build flat list of all available LLMs for preference dropdown
    allAvailableLLMs() {
      const llms = []
      this.availableLLMServices.forEach(service => {
        const models = this.llmServiceModels[service.value] || []
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
          // Service without specific models (or models not loaded yet)
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
    }
  },
  watch: {
    modelValue: {
      handler(newVal) {
        this.localSettings = { ...newVal }
      },
      deep: true
    },
    testContentService() {
      this.updateTestContentModelOptions()
    }
  },
  created() {
    // Initialize itemTypes from CORE_ITEM_TYPES config
    // Default: segment, interview, coldopen enabled; others disabled
    const defaultEnabledTypes = ['segment', 'interview', 'coldopen']
    CORE_ITEM_TYPES.forEach(type => {
      this.realContentSettings.episodeDescription.itemTypes[type.value] = defaultEnabledTypes.includes(type.value)
    })
  },
  mounted() {
    this.loadLLMSettings()
    this.loadTestContentSettings()
    this.loadOllamaModels()
    this.loadRealContentSettings()
    this.loadShowIdentity()
  },
  methods: {
    showSnackbar(message, color = 'error') {
      this.snackbar.message = message
      this.snackbar.color = color
      this.snackbar.show = true
    },
    save() {
      this.$emit('update:modelValue', this.localSettings)
      this.$emit('save', this.localSettings)
    },
    async saveShowIdentity() {
      this.savingShowIdentity = true
      try {
        await this.$axios.post('/settings/show_identity', {
          key: 'show_identity',
          value: this.realContentSettings.showIdentity
        })
        this.showSnackbar('Show identity saved successfully', 'success')
      } catch (error) {
        console.error('Failed to save show identity:', error)
        this.showSnackbar('Failed to save show identity', 'error')
      } finally {
        this.savingShowIdentity = false
      }
    },
    async loadShowIdentity() {
      try {
        const response = await this.$axios.get('/settings/show_identity')
        if (response.data && response.data.value) {
          this.realContentSettings.showIdentity = {
            ...this.realContentSettings.showIdentity,
            ...response.data.value
          }
          console.log('✅ Loaded show identity from database')
        }
      } catch (error) {
        console.warn('No show identity found in database, using defaults')
      }
    },
    async loadLLMSettings() {
      // Load LLM settings from database
      try {
        const response = await this.$axios.get('/settings/llm_routing')
        if (response.data && response.data.value) {
          this.llmSettings = response.data.value
          console.log('✅ Loaded LLM routing settings from database:', this.llmSettings)
        }
      } catch (error) {
        console.warn('Failed to load LLM settings from database, using defaults:', error)
      }
    },
    async handleLLMSave(settings) {
      this.llmSettings = settings

      // Save to database
      try {
        await this.$axios.post('/settings/llm_routing', {
          key: 'llm_routing',
          value: settings,
          category: 'generation'
        })
        console.log('✅ LLM routing settings saved to database:', settings)

        // Show success notification
        this.$emit('save', this.localSettings)
      } catch (error) {
        console.error('❌ Failed to save LLM settings to database:', error)
        this.showSnackbar('Failed to save LLM routing settings')
      }
    },

    // Preview split behavior for test quote
    previewSplit() {
      if (!this.testQuote) {
        this.splitPreview = null
        return
      }

      const config = {
        maxChars: this.maxCharsScreen1,
        minSecond: this.localSettings.fsq_min_second_screen || 80,
        balanceThreshold: this.balanceThreshold
      }

      const length = this.testQuote.length

      if (length <= config.maxChars) {
        this.splitPreview = {
          type: 'success',
          title: '✓ Fits on single screen',
          strategy: 'Single Screen',
          segments: [this.testQuote]
        }
      } else if (length <= config.balanceThreshold) {
        const mid = Math.floor(length / 2)
        // Find nearest sentence boundary
        const splitPoint = this.findSplitPoint(this.testQuote, mid)
        this.splitPreview = {
          type: 'warning',
          title: '⚖️ Will be balanced split',
          strategy: 'Balanced',
          segments: [
            this.testQuote.substring(0, splitPoint).trim(),
            this.testQuote.substring(splitPoint).trim()
          ]
        }
      } else {
        const splitPoint = this.findSplitPoint(this.testQuote, config.maxChars)
        const remainder = this.testQuote.substring(splitPoint).trim()

        // Check if remainder is too short (orphan)
        if (remainder.length < config.minSecond) {
          this.splitPreview = {
            type: 'error',
            title: '⚠️ Would create orphan text - will rebalance',
            strategy: 'Forced Balance',
            segments: [
              this.testQuote.substring(0, Math.floor(length / 2)).trim(),
              this.testQuote.substring(Math.floor(length / 2)).trim()
            ]
          }
        } else {
          this.splitPreview = {
            type: 'info',
            title: '✂️ Will be standard split',
            strategy: 'Standard',
            segments: [
              this.testQuote.substring(0, splitPoint).trim(),
              remainder
            ]
          }
        }
      }
    },

    // Find best split point near target position
    findSplitPoint(text, target) {
      if (!this.localSettings.fsq_prefer_sentence_boundaries) {
        return target
      }

      // Try to find sentence boundaries first
      const sentences = ['. ', '! ', '? ']
      for (const punct of sentences) {
        const idx = text.lastIndexOf(punct, target)
        if (idx > target - 50 && idx < target + 50) {
          return idx + 2
        }
      }

      // If mid-sentence splits allowed, try commas/semicolons
      if (this.localSettings.fsq_allow_mid_sentence_split) {
        const clauses = [', ', '; ', ' - ']
        for (const punct of clauses) {
          const idx = text.lastIndexOf(punct, target)
          if (idx > target - 30 && idx < target + 30) {
            return idx + 2
          }
        }
      }

      // Fallback to word boundary
      const spaceIdx = text.lastIndexOf(' ', target)
      if (spaceIdx > target - 20) {
        return spaceIdx + 1
      }

      return target
    },

    // Test Content Generator methods
    async loadTestContentSettings() {
      const saved = localStorage.getItem('llm-routing-settings')
      if (saved) {
        try {
          const settings = JSON.parse(saved)
          const contentExpansion = settings.routing?.contentExpansion || 'auto'
          if (contentExpansion === 'auto') {
            this.testContentService = 'auto'
            this.testContentModel = null
          } else if (contentExpansion.includes(':')) {
            const parts = contentExpansion.split(':')
            this.testContentService = parts[0]
            this.testContentModel = parts.slice(1).join(':')
          } else {
            this.testContentService = contentExpansion
            this.testContentModel = null
          }
          if (settings.ollamaModels?.contentExpansion) {
            this.testContentModel = settings.ollamaModels.contentExpansion
          }
        } catch (e) {
          console.error('Failed to parse llm-routing-settings:', e)
        }
      }
    },

    async loadOllamaModels() {
      try {
        const response = await fetch('/api/llm/ollama/models', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
          }
        })
        if (response.ok) {
          const data = await response.json()
          this.availableOllamaModels = data.models?.map(m => m.name) || []
          // Also populate llmServiceModels.ollama for preference dropdowns
          this.llmServiceModels.ollama = this.availableOllamaModels.map(m => ({
            title: m,
            value: m
          }))
          console.log('📋 Loaded Ollama models:', this.availableOllamaModels)
          this.updateTestContentModelOptions()
        } else {
          this.loadFallbackModels()
        }
      } catch (e) {
        console.error('Failed to load Ollama models:', e)
        this.loadFallbackModels()
      }
    },

    loadFallbackModels() {
      this.availableOllamaModels = [
        'llama3:latest',
        'mistral:7b',
        'deepseek-r1:8b',
        'Qwen2.5-Coder:7b',
        'codellama:34b'
      ]
      // Also populate llmServiceModels.ollama for preference dropdowns
      this.llmServiceModels.ollama = this.availableOllamaModels.map(m => ({
        title: m,
        value: m
      }))
      this.updateTestContentModelOptions()
    },

    updateTestContentModelOptions() {
      if (this.testContentService === 'ollama') {
        this.testContentModelOptions = this.availableOllamaModels.map(m => ({
          title: m,
          value: m
        }))
      } else if (this.testContentService === 'openai') {
        this.testContentModelOptions = [
          { title: 'GPT-4', value: 'gpt-4' },
          { title: 'GPT-4 Turbo', value: 'gpt-4-turbo' },
          { title: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' }
        ]
      } else if (this.testContentService === 'anthropic') {
        this.testContentModelOptions = [
          { title: 'Claude 3.5 Sonnet', value: 'claude-3-5-sonnet-20241022' },
          { title: 'Claude 3 Opus', value: 'claude-3-opus-20240229' },
          { title: 'Claude 3 Haiku', value: 'claude-3-haiku-20240307' }
        ]
      } else if (this.testContentService === 'gemini') {
        this.testContentModelOptions = [
          { title: 'Gemini 2.0 Flash', value: 'gemini-2.0-flash' },
          { title: 'Gemini 1.5 Pro', value: 'gemini-1.5-pro' }
        ]
      } else if (this.testContentService === 'grok') {
        this.testContentModelOptions = [
          { title: 'Grok 4', value: 'grok-4-latest' },
          { title: 'Grok 3', value: 'grok-3' }
        ]
      } else {
        this.testContentModelOptions = []
      }
    },

    selectOllamaModel(model) {
      this.testContentService = 'ollama'
      this.testContentModel = model
      this.updateTestContentModelOptions()
    },

    saveTestContentSettings() {
      this.savingTestContent = true

      let settings = {}
      const saved = localStorage.getItem('llm-routing-settings')
      if (saved) {
        try {
          settings = JSON.parse(saved)
        } catch (e) {
          settings = {}
        }
      }

      if (!settings.routing) settings.routing = {}
      if (!settings.ollamaModels) settings.ollamaModels = {}

      if (this.testContentService === 'auto') {
        settings.routing.contentExpansion = 'auto'
      } else if (this.testContentModel) {
        settings.routing.contentExpansion = `${this.testContentService}:${this.testContentModel}`
        if (this.testContentService === 'ollama') {
          settings.ollamaModels.contentExpansion = this.testContentModel
        }
      } else {
        settings.routing.contentExpansion = this.testContentService
      }

      localStorage.setItem('llm-routing-settings', JSON.stringify(settings))

      console.log('✅ Test Content Generator settings saved:', {
        service: this.testContentService,
        model: this.testContentModel,
        routing: settings.routing.contentExpansion
      })

      this.showSnackbar('Test content settings saved', 'success')

      setTimeout(() => {
        this.savingTestContent = false
      }, 500)
    },

    resetTestContentToDefaults() {
      this.testContentService = 'ollama'
      this.testContentModel = 'llama3:latest'
      this.updateTestContentModelOptions()
      this.saveTestContentSettings()
    },

    // LLM Preference Order methods
    addLLMPreference() {
      // Add a new empty preference slot
      this.realContentSettings.episodeDescription.llmPreferenceOrder.push('')
    },

    removeLLMPreference(index) {
      this.realContentSettings.episodeDescription.llmPreferenceOrder.splice(index, 1)
    },

    moveLLMPreferenceUp(index) {
      if (index > 0) {
        const prefs = this.realContentSettings.episodeDescription.llmPreferenceOrder
        const temp = prefs[index]
        prefs[index] = prefs[index - 1]
        prefs[index - 1] = temp
      }
    },

    moveLLMPreferenceDown(index) {
      const prefs = this.realContentSettings.episodeDescription.llmPreferenceOrder
      if (index < prefs.length - 1) {
        const temp = prefs[index]
        prefs[index] = prefs[index + 1]
        prefs[index + 1] = temp
      }
    },

    getLLMDisplayName(value) {
      if (!value) return 'Select LLM...'
      const llm = this.allAvailableLLMs.find(l => l.value === value)
      return llm ? llm.title : value
    },

    // Template variable methods
    insertVariable(variable) {
      // Insert variable at cursor position or append to end
      const currentPrompt = this.realContentSettings.episodeDescription.prompt || ''
      this.realContentSettings.episodeDescription.prompt = currentPrompt + (currentPrompt ? ' ' : '') + variable
    },

    insertConditional(condition, defaultContent) {
      // Insert a conditional logic block
      const block = `{% if ${condition} %}${defaultContent}{% endif %}`
      const currentPrompt = this.realContentSettings.episodeDescription.prompt || ''
      this.realContentSettings.episodeDescription.prompt = currentPrompt + (currentPrompt ? '\n' : '') + block
    },

    generateDefaultEpisodePrompt() {
      const settings = this.realContentSettings.episodeDescription
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

      this.realContentSettings.episodeDescription.prompt = prompt
    },

    // Real Content Generator methods
    loadRealContentSettings() {
      const saved = localStorage.getItem('real-content-settings')
      if (saved) {
        try {
          const settings = JSON.parse(saved)
          // Deep merge with defaults to handle new fields
          this.realContentSettings = this.deepMerge(this.realContentSettings, settings)
          console.log('✅ Loaded real content settings:', this.realContentSettings)
        } catch (e) {
          console.error('Failed to parse real-content-settings:', e)
        }
      }
    },

    deepMerge(target, source) {
      const result = { ...target }
      for (const key in source) {
        if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
          result[key] = this.deepMerge(target[key] || {}, source[key])
        } else {
          result[key] = source[key]
        }
      }
      return result
    },

    saveEpisodeDescriptionSettings() {
      this.savingEpisodeDescription = true

      // Save just the episode description portion to localStorage
      localStorage.setItem('real-content-settings', JSON.stringify(this.realContentSettings))

      console.log('✅ Episode Description settings saved:', this.realContentSettings.episodeDescription)

      this.showSnackbar('Episode description settings saved', 'success')

      setTimeout(() => {
        this.savingEpisodeDescription = false
      }, 500)
    },

    saveRealContentSettings() {
      this.savingRealContent = true

      localStorage.setItem('real-content-settings', JSON.stringify(this.realContentSettings))

      console.log('✅ Real Content settings saved:', this.realContentSettings)

      this.showSnackbar('Real content settings saved', 'success')

      setTimeout(() => {
        this.savingRealContent = false
      }, 500)
    }
  }
}
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
  opacity: 0.8;
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
</style>
