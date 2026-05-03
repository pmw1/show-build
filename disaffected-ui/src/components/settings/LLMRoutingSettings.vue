<template>
  <v-card class="pa-0">
    <v-row no-gutters class="fill-height">
      <!-- Vertical Tabs on Left -->
      <v-col cols="3" class="border-r">
        <v-tabs
          v-model="routingSubTab"
          direction="vertical"
          color="primary"
          class="routing-vertical-tabs"
        >
          <v-tab value="task-routing" prepend-icon="mdi-network">
            Task Routing
          </v-tab>
          <v-tab value="prompt-library" prepend-icon="mdi-message-text">
            Custom User Prompts
          </v-tab>
          <v-tab value="performance" prepend-icon="mdi-speedometer">
            Performance
          </v-tab>
        </v-tabs>
      </v-col>

      <!-- Tab Content on Right -->
      <v-col cols="9">
        <v-tabs-window v-model="routingSubTab" class="pa-6">

          <!-- Task Routing -->
          <v-tabs-window-item value="task-routing">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-network</v-icon>
              LLM Task Routing
            </h3>
            <p class="text-body-2 mb-4">Configure which LLM service handles specific tasks for optimal performance and cost.</p>

            <!-- Routing Rules -->
            <v-card variant="outlined" class="mb-4">
              <v-card-title class="text-subtitle-1 d-flex align-center">
                <v-icon left class="mr-2">mdi-routes</v-icon>
                Task Assignments
              </v-card-title>
              <v-card-text>
                <v-list density="compact" v-if="localSettings && localSettings.routing">
                  <!-- Quote Splitting -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Quote Splitting</v-list-item-title>
                    <v-row dense>
                      <v-col cols="6">
                        <v-select
                          v-model="quoteSplittingService"
                          :items="availableServices"
                          label="Service"
                          variant="outlined"
                          density="compact"
                          @update:model-value="updateTaskService('quoteSplitting')"
                        />
                      </v-col>
                      <v-col cols="6">
                        <v-select
                          v-model="quoteSplittingModel"
                          :items="getModelsForService(quoteSplittingService)"
                          label="Model"
                          variant="outlined"
                          density="compact"
                          :disabled="!quoteSplittingService || quoteSplittingService === 'auto'"
                          @update:model-value="updateTaskModel('quoteSplitting')"
                        />
                      </v-col>
                    </v-row>
                    <div class="text-caption text-grey mt-1">Intelligently split long quotes at sentence boundaries</div>
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- Slug Generation -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Slug Generation</v-list-item-title>
                    <v-row dense>
                      <v-col cols="6">
                        <v-select
                          v-model="slugGenerationService"
                          :items="availableServices"
                          label="Service"
                          variant="outlined"
                          density="compact"
                          @update:model-value="updateTaskService('slugGeneration')"
                        />
                      </v-col>
                      <v-col cols="6">
                        <v-select
                          v-model="slugGenerationModel"
                          :items="getModelsForService(slugGenerationService)"
                          label="Model"
                          variant="outlined"
                          density="compact"
                          :disabled="!slugGenerationService || slugGenerationService === 'auto'"
                          @update:model-value="updateTaskModel('slugGeneration')"
                        />
                      </v-col>
                    </v-row>
                    <div class="text-caption text-grey mt-1">Generate SEO-friendly slugs from content</div>
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- Script Summarization -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Script Summarization</v-list-item-title>
                    <v-row dense>
                      <v-col cols="6">
                        <v-select
                          v-model="scriptSummaryService"
                          :items="availableServices"
                          label="Service"
                          variant="outlined"
                          density="compact"
                          @update:model-value="updateTaskService('scriptSummary')"
                        />
                      </v-col>
                      <v-col cols="6">
                        <v-select
                          v-model="scriptSummaryModel"
                          :items="getModelsForService(scriptSummaryService)"
                          label="Model"
                          variant="outlined"
                          density="compact"
                          :disabled="!scriptSummaryService || scriptSummaryService === 'auto'"
                          @update:model-value="updateTaskModel('scriptSummary')"
                        />
                      </v-col>
                    </v-row>
                    <div class="text-caption text-grey mt-1">Generate summaries of scripts and segments</div>
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- Title Generation -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Title Generation</v-list-item-title>
                    <v-row dense>
                      <v-col cols="6">
                        <v-select
                          v-model="titleGenerationService"
                          :items="availableServices"
                          label="Service"
                          variant="outlined"
                          density="compact"
                          @update:model-value="updateTaskService('titleGeneration')"
                        />
                      </v-col>
                      <v-col cols="6">
                        <v-select
                          v-model="titleGenerationModel"
                          :items="getModelsForService(titleGenerationService)"
                          label="Model"
                          variant="outlined"
                          density="compact"
                          :disabled="!titleGenerationService || titleGenerationService === 'auto'"
                          @update:model-value="updateTaskModel('titleGeneration')"
                        />
                      </v-col>
                    </v-row>
                    <div class="text-caption text-grey mt-1">Generate compelling titles for episodes and segments</div>
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- Content Expansion -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Content Expansion</v-list-item-title>
                    <v-row dense>
                      <v-col cols="6">
                        <v-select
                          v-model="contentExpansionService"
                          :items="availableServices"
                          label="Service"
                          variant="outlined"
                          density="compact"
                          @update:model-value="updateContentExpansionModel"
                        />
                      </v-col>
                      <v-col cols="6">
                        <v-select
                          v-model="contentExpansionModel"
                          :items="getModelsForService(contentExpansionService)"
                          label="Model"
                          variant="outlined"
                          density="compact"
                          :disabled="!contentExpansionService || contentExpansionService === 'auto'"
                          @update:model-value="updateContentExpansion"
                        />
                      </v-col>
                    </v-row>
                    <div class="text-caption text-grey mt-1">Expand brief notes into full script content</div>
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- Entity Extraction -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Entity Extraction</v-list-item-title>
                    <v-row dense>
                      <v-col cols="6">
                        <v-select
                          v-model="entityExtractionService"
                          :items="availableServices"
                          label="Service"
                          variant="outlined"
                          density="compact"
                          @update:model-value="updateTaskService('entityExtraction')"
                        />
                      </v-col>
                      <v-col cols="6">
                        <v-select
                          v-model="entityExtractionModel"
                          :items="getModelsForService(entityExtractionService)"
                          label="Model"
                          variant="outlined"
                          density="compact"
                          :disabled="!entityExtractionService || entityExtractionService === 'auto'"
                          @update:model-value="updateTaskModel('entityExtraction')"
                        />
                      </v-col>
                    </v-row>
                    <div class="text-caption text-grey mt-1">Extract people, organizations, locations from content</div>
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- People Search -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">People Search</v-list-item-title>
                    <v-row dense>
                      <v-col cols="6">
                        <v-select
                          v-model="peopleSearchService"
                          :items="availableServices"
                          label="Service"
                          variant="outlined"
                          density="compact"
                          @update:model-value="updateTaskService('peopleSearch')"
                        />
                      </v-col>
                      <v-col cols="6">
                        <v-select
                          v-model="peopleSearchModel"
                          :items="getModelsForService(peopleSearchService)"
                          label="Model"
                          variant="outlined"
                          density="compact"
                          :disabled="!peopleSearchService || peopleSearchService === 'auto'"
                          @update:model-value="updateTaskModel('peopleSearch')"
                        />
                      </v-col>
                    </v-row>
                    <div class="text-caption text-grey mt-1">Search and identify people mentioned in content</div>
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- Social Search -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Social Search</v-list-item-title>
                    <v-row dense>
                      <v-col cols="6">
                        <v-select
                          v-model="socialSearchService"
                          :items="availableServices"
                          label="Service"
                          variant="outlined"
                          density="compact"
                          @update:model-value="updateTaskService('socialSearch')"
                        />
                      </v-col>
                      <v-col cols="6">
                        <v-select
                          v-model="socialSearchModel"
                          :items="getModelsForService(socialSearchService)"
                          label="Model"
                          variant="outlined"
                          density="compact"
                          :disabled="!socialSearchService || socialSearchService === 'auto'"
                          @update:model-value="updateTaskModel('socialSearch')"
                        />
                      </v-col>
                    </v-row>
                    <div class="text-caption text-grey mt-1">Find social media profiles and related content</div>
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- Tweet Composing -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Tweet Composing</v-list-item-title>
                    <v-row dense>
                      <v-col cols="6">
                        <v-select
                          v-model="tweetComposingService"
                          :items="availableServices"
                          label="Service"
                          variant="outlined"
                          density="compact"
                          @update:model-value="updateTaskService('tweetComposing')"
                        />
                      </v-col>
                      <v-col cols="6">
                        <v-select
                          v-model="tweetComposingModel"
                          :items="getModelsForService(tweetComposingService)"
                          label="Model"
                          variant="outlined"
                          density="compact"
                          :disabled="!tweetComposingService || tweetComposingService === 'auto'"
                          @update:model-value="updateTaskModel('tweetComposing')"
                        />
                      </v-col>
                    </v-row>
                    <div class="text-caption text-grey mt-1">Generate engaging social media posts</div>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>

            <!-- Fallback Strategy -->
            <v-card variant="tonal" color="warning" class="pa-4" v-if="localSettings && localSettings.routing">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-backup-restore</v-icon>
                Fallback Strategy
              </h4>
              <v-checkbox
                v-model="localSettings.routing.enableFallback"
                label="Enable automatic fallback"
                hint="If primary service fails, automatically try alternative services"
                persistent-hint
                density="compact"
              />
              <v-select
                v-if="localSettings.routing.enableFallback"
                v-model="localSettings.routing.fallbackOrder"
                :items="fallbackOrderOptions"
                label="Fallback Priority Order"
                variant="outlined"
                density="compact"
                class="mt-3"
                hint="Order of services to try if primary fails"
                persistent-hint
                multiple
                chips
              />
            </v-card>
          </v-tabs-window-item>

          <!-- Custom User Prompts -->
          <v-tabs-window-item value="prompt-library">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-message-text</v-icon>
              Custom User Prompts
            </h3>
            <p class="text-body-2 mb-4">Create and manage your own reusable prompt templates for AI tasks. These are stored locally and specific to your user account.</p>

            <v-alert type="info" variant="tonal" class="mb-4">
              <strong>Note:</strong> This is different from <strong>LLM Prompts</strong> in the AI & LLM section.
              Custom User Prompts are personal templates you create for your own use, while LLM Prompts (admin-only) override system-wide AI operations.

              <div class="mt-2">
                <strong>⚠️ Work in Progress:</strong> Custom prompt invocation via keyboard shortcuts (Ctrl+Alt+Shift+[1-9]) is not yet implemented.
                Currently, these templates are stored but cannot be triggered in the editor.
              </div>
            </v-alert>

            <!-- Prompt List -->
            <v-row>
              <v-col cols="12">
                <v-btn color="primary" @click="showNewPromptDialog = true" class="mb-4">
                  <v-icon left>mdi-plus</v-icon>
                  New Custom Prompt
                </v-btn>
              </v-col>
            </v-row>

            <!-- Group prompts by category -->
            <div v-for="category in promptCategoriesWithPrompts" :key="category.value" class="mb-6">
              <h4 class="text-subtitle-1 font-weight-bold mb-3 d-flex align-center">
                <v-icon :color="getCategoryColor(category.value)" class="mr-2">
                  {{ getPromptIcon(category.value) }}
                </v-icon>
                {{ category.title }}
              </h4>

              <v-expansion-panels v-model="expandedPrompts" multiple>
                <v-expansion-panel
                  v-for="(prompt, index) in getPromptsForCategory(category.value)"
                  :key="index"
                  :value="index"
                >
                  <v-expansion-panel-title>
                    <div class="d-flex flex-column flex-grow-1">
                      <div class="d-flex align-center">
                        <strong>{{ prompt.name }}</strong>
                        <v-spacer />
                        <v-chip
                          v-if="!prompt.enabled"
                          size="small"
                          color="grey"
                          class="mr-2"
                        >
                          Disabled
                        </v-chip>
                      </div>
                      <div class="text-caption text-medium-emphasis mt-1">
                        {{ getPromptInvocation(prompt) }}
                      </div>
                    </div>
                  </v-expansion-panel-title>
                  <v-expansion-panel-text>
                  <v-row>
                    <v-col cols="12">
                      <v-text-field
                        v-model="prompt.name"
                        label="Prompt Name"
                        variant="outlined"
                        density="compact"
                        class="mb-2"
                      />
                    </v-col>
                    <v-col cols="6">
                      <v-select
                        v-model="prompt.category"
                        :items="promptCategories"
                        label="Category"
                        variant="outlined"
                        density="compact"
                      />
                    </v-col>
                    <v-col cols="6">
                      <v-select
                        v-model="prompt.preferredService"
                        :items="llmServiceOptions"
                        label="Preferred Service"
                        variant="outlined"
                        density="compact"
                      />
                    </v-col>
                    <v-col cols="12">
                      <v-textarea
                        v-model="prompt.template"
                        label="Prompt Template"
                        rows="8"
                        variant="outlined"
                        hint="Use {variable} for dynamic values. Available: {quote}, {script}, {title}, {speaker}, {duration}"
                        persistent-hint
                      />
                    </v-col>
                    <v-col cols="12">
                      <v-row>
                        <v-col cols="4">
                          <v-slider
                            v-model="prompt.temperature"
                            label="Temperature"
                            min="0"
                            max="2"
                            step="0.1"
                            thumb-label
                            density="compact"
                          >
                            <template v-slot:append>
                              <v-chip size="small">{{ prompt.temperature }}</v-chip>
                            </template>
                          </v-slider>
                        </v-col>
                        <v-col cols="4">
                          <v-slider
                            v-model="prompt.maxTokens"
                            label="Max Tokens"
                            min="50"
                            max="4000"
                            step="50"
                            thumb-label
                            density="compact"
                          >
                            <template v-slot:append>
                              <v-chip size="small">{{ prompt.maxTokens }}</v-chip>
                            </template>
                          </v-slider>
                        </v-col>
                        <v-col cols="4">
                          <v-switch
                            v-model="prompt.enabled"
                            label="Enabled"
                            color="success"
                            density="compact"
                          />
                        </v-col>
                      </v-row>
                    </v-col>
                    <v-col cols="12" class="d-flex justify-end">
                      <v-btn color="error" variant="text" @click="deletePrompt(index)">
                        <v-icon left>mdi-delete</v-icon>
                        Delete
                      </v-btn>
                      <v-btn color="primary" variant="text" @click="testPrompt(prompt)" class="ml-2">
                        <v-icon left>mdi-test-tube</v-icon>
                        Test
                      </v-btn>
                    </v-col>
                  </v-row>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
            </div>
          </v-tabs-window-item>

          <!-- Performance Monitoring -->
          <v-tabs-window-item value="performance">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-speedometer</v-icon>
              Performance Monitoring
            </h3>
            <p class="text-body-2 mb-4">Track LLM usage, response times, and costs.</p>

            <v-row>
              <!-- Response Time -->
              <v-col cols="12" md="4">
                <v-card variant="tonal" color="info">
                  <v-card-text>
                    <div class="text-overline mb-1">Avg Response Time</div>
                    <div class="text-h4">{{ performanceStats.avgResponseTime }}ms</div>
                    <v-progress-linear
                      :model-value="(performanceStats.avgResponseTime / 5000) * 100"
                      color="info"
                      class="mt-2"
                    />
                  </v-card-text>
                </v-card>
              </v-col>

              <!-- Total Requests -->
              <v-col cols="12" md="4">
                <v-card variant="tonal" color="success">
                  <v-card-text>
                    <div class="text-overline mb-1">Total Requests</div>
                    <div class="text-h4">{{ performanceStats.totalRequests }}</div>
                    <div class="text-caption mt-2">{{ performanceStats.successRate }}% success rate</div>
                  </v-card-text>
                </v-card>
              </v-col>

              <!-- Estimated Cost -->
              <v-col cols="12" md="4">
                <v-card variant="tonal" color="warning">
                  <v-card-text>
                    <div class="text-overline mb-1">Estimated Cost (30 days)</div>
                    <div class="text-h4">${{ performanceStats.estimatedCost.toFixed(2) }}</div>
                    <div class="text-caption mt-2">Based on usage patterns</div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- Service Breakdown -->
            <v-card variant="outlined" class="mt-4">
              <v-card-title class="text-subtitle-1">Service Usage Breakdown</v-card-title>
              <v-card-text>
                <v-list density="compact">
                  <v-list-item v-for="service in performanceStats.serviceBreakdown" :key="service.name">
                    <template #prepend>
                      <v-icon :color="service.color">{{ service.icon }}</v-icon>
                    </template>
                    <v-list-item-title>{{ service.name }}</v-list-item-title>
                    <v-list-item-subtitle>
                      {{ service.requests }} requests | Avg: {{ service.avgTime }}ms | ${{ service.cost.toFixed(2) }}
                    </v-list-item-subtitle>
                    <template #append>
                      <v-chip size="small" :color="service.status === 'active' ? 'success' : 'grey'">
                        {{ service.status }}
                      </v-chip>
                    </template>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>

            <!-- Reset Stats -->
            <v-row class="mt-4">
              <v-col cols="12">
                <v-btn color="warning" variant="outlined" @click="resetPerformanceStats">
                  <v-icon left>mdi-refresh</v-icon>
                  Reset Statistics
                </v-btn>
              </v-col>
            </v-row>
          </v-tabs-window-item>

        </v-tabs-window>
      </v-col>
    </v-row>

    <!-- Save Button (Fixed at bottom of card) -->
    <v-card-actions class="px-4 pb-4 border-t">
      <v-spacer></v-spacer>
      <v-btn color="primary" @click="save" variant="elevated">
        <v-icon left>mdi-content-save</v-icon>
        Save LLM Settings
      </v-btn>
    </v-card-actions>

    <!-- New Custom Prompt Dialog -->
    <v-dialog v-model="showNewPromptDialog" max-width="800">
      <v-card>
        <v-card-title>Create New Custom Prompt</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newPrompt.name"
            label="Prompt Name"
            variant="outlined"
            class="mb-3"
          />
          <v-select
            v-model="newPrompt.category"
            :items="promptCategories"
            label="Category"
            variant="outlined"
            class="mb-3"
          />
          <v-textarea
            v-model="newPrompt.template"
            label="Prompt Template"
            rows="10"
            variant="outlined"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showNewPromptDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="addNewPrompt">Add Prompt</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup>
import { ref, computed, watch, onMounted, getCurrentInstance } from 'vue';

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
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
    })
  }
});

const emit = defineEmits(['update:modelValue', 'save']);

const instance = getCurrentInstance(); // eslint-disable-line no-unused-vars

// Reactive state
const routingSubTab = ref('task-routing');
const expandedPrompts = ref([]);
const showNewPromptDialog = ref(false);
const localSettings = ref(props.modelValue ? JSON.parse(JSON.stringify(props.modelValue)) : {
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
const newPrompt = ref({
  name: '',
  category: 'content',
  template: '',
  preferredService: 'auto',
  temperature: 0.7,
  maxTokens: 500,
  enabled: true
});
const llmServiceOptions = ref([]); // eslint-disable-line no-unused-vars
const ollamaModels = ref([]); // eslint-disable-line no-unused-vars
const enabledCloudServices = ref([]); // eslint-disable-line no-unused-vars
const availableServices = ref([
  { title: 'Auto (Smart Routing)', value: 'auto' }
]);
const serviceModels = ref({
  ollama: [],
  openai: [],
  anthropic: [],
  gemini: [],
  grok: []
});
// Separate service/model selections for each task type
const contentExpansionService = ref('auto');
const contentExpansionModel = ref(null);
const entityExtractionService = ref('auto');
const entityExtractionModel = ref(null);
const peopleSearchService = ref('auto');
const peopleSearchModel = ref(null);
const socialSearchService = ref('auto');
const socialSearchModel = ref(null);
const tweetComposingService = ref('auto');
const tweetComposingModel = ref(null);
const quoteSplittingService = ref('auto');
const quoteSplittingModel = ref(null);
const slugGenerationService = ref('auto');
const slugGenerationModel = ref(null);
const scriptSummaryService = ref('auto');
const scriptSummaryModel = ref(null);
const titleGenerationService = ref('auto');
const titleGenerationModel = ref(null);
const fallbackOrderOptions = [
  { title: 'Ollama (Local)', value: 'ollama' },
  { title: 'OpenAI', value: 'openai' },
  { title: 'Anthropic', value: 'anthropic' },
  { title: 'Gemini', value: 'gemini' },
  { title: 'Grok', value: 'grok' }
];
const promptCategories = [
  { title: 'Content Generation', value: 'content' },
  { title: 'Analysis', value: 'analysis' },
  { title: 'Summarization', value: 'summarization' },
  { title: 'Formatting', value: 'formatting' },
  { title: 'Research', value: 'research' },
  { title: 'Development', value: 'development' }
];
const performanceStats = ref({
  avgResponseTime: 0,
  totalRequests: 0,
  successRate: 0,
  estimatedCost: 0,
  serviceBreakdown: []
});

// Task type service/model ref maps for dynamic access
const taskServiceRefs = {
  contentExpansion: contentExpansionService,
  contentExpansionModel: contentExpansionModel,
  entityExtraction: entityExtractionService,
  entityExtractionModel: entityExtractionModel,
  peopleSearch: peopleSearchService,
  peopleSearchModel: peopleSearchModel,
  socialSearch: socialSearchService,
  socialSearchModel: socialSearchModel,
  tweetComposing: tweetComposingService,
  tweetComposingModel: tweetComposingModel,
  quoteSplitting: quoteSplittingService,
  quoteSplittingModel: quoteSplittingModel,
  slugGeneration: slugGenerationService,
  slugGenerationModel: slugGenerationModel,
  scriptSummary: scriptSummaryService,
  scriptSummaryModel: scriptSummaryModel,
  titleGeneration: titleGenerationService,
  titleGenerationModel: titleGenerationModel
};

// Watch
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    localSettings.value = JSON.parse(JSON.stringify(newVal))
  }
}, { deep: true });

// Computed
const promptCategoriesWithPrompts = computed(() => {
  if (!localSettings.value || !localSettings.value.prompts) {
    return []
  }
  return promptCategories.filter(category => {
    return localSettings.value.prompts.some(p => p.category === category.value)
  })
});

// Methods
function getPromptsForCategory(category) {
  if (!localSettings.value || !localSettings.value.prompts) {
    return []
  }
  return localSettings.value.prompts.filter(p => p.category === category)
}

function getPromptInvocation(prompt) {
  if (prompt.name.includes('Segment Generator (Tease)')) {
    return 'Invoked: Ctrl+Alt+Shift+[1-9] in tease segments'
  } else if (prompt.name.includes('Segment Generator (Cold Open)')) {
    return 'Invoked: Ctrl+Alt+Shift+[1-9] in coldopen segments'
  } else if (prompt.name.includes('Segment Generator (Standard)')) {
    return 'Invoked: Ctrl+Alt+Shift+[1-9] in standard segments'
  } else if (prompt.name.includes('Quote Splitter')) {
    return 'Invoked: Automatically when splitting long FSQ quotes'
  } else if (prompt.name.includes('Slug Generator')) {
    return 'Invoked: Automatically when generating URL slugs'
  } else if (prompt.name.includes('Script Summarizer')) {
    return 'Invoked: Via summarize button in content editor'
  } else {
    return 'Custom prompt - invocation depends on implementation'
  }
}

async function loadAvailableModels() {
  try {
    const $axios = instance.appContext.config.globalProperties.$axios;
    const services = [
      { title: 'Auto (Smart Routing)', value: 'auto' },
      { title: 'Ollama (Local)', value: 'ollama' },
      { title: 'OpenAI', value: 'openai' },
      { title: 'Google Gemini', value: 'gemini' },
      { title: 'xAI (Grok)', value: 'grok' }
    ]

    // Fetch Ollama models if available
    try {
      const ollamaResponse = await $axios.get('/llm/ollama/models')
      if (ollamaResponse.data.models && ollamaResponse.data.models.length > 0) {
        serviceModels.value.ollama = ollamaResponse.data.models.map(m => ({
          title: m.name,
          value: m.name
        }))
      }
    } catch (e) {
      console.warn('Ollama models not available:', e)
    }

    // Define models for all cloud services (always available)
    serviceModels.value.openai = [
      { title: 'GPT-4 Turbo', value: 'gpt-4-turbo-preview' },
      { title: 'GPT-4', value: 'gpt-4' },
      { title: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' },
      { title: 'GPT-3.5 Turbo 16k', value: 'gpt-3.5-turbo-16k' }
    ]

    serviceModels.value.gemini = [
      { title: 'Gemini 2.0 Flash', value: 'gemini-2.0-flash' },
      { title: 'Gemini Pro', value: 'gemini-pro' },
      { title: 'Gemini Pro Vision', value: 'gemini-pro-vision' }
    ]

    serviceModels.value.grok = [
      { title: 'Grok 4 Latest', value: 'grok-4-latest' },
      { title: 'Grok Beta', value: 'grok-beta' }
    ]

    availableServices.value = services

    // Parse existing task type settings
    const taskTypes = ['contentExpansion', 'entityExtraction', 'peopleSearch', 'socialSearch', 'tweetComposing']
    taskTypes.forEach(taskType => {
      if (localSettings.value && localSettings.value.routing && localSettings.value.routing[taskType]) {
        const [service, model] = localSettings.value.routing[taskType].split(':')
        taskServiceRefs[taskType].value = service || 'auto'
        taskServiceRefs[`${taskType}Model`].value = model || null
      }
    })
  } catch (error) {
    console.error('Failed to load available models:', error)
  }
}

function getModelsForService(service) {
  if (!service || service === 'auto') {
    return []
  }
  const models = serviceModels.value[service] || []
  console.log(`getModelsForService(${service}):`, models)
  return models
}

function updateContentExpansionModel() {
  // Reset model when service changes
  contentExpansionModel.value = null
  if (localSettings.value && localSettings.value.routing && contentExpansionService.value === 'auto') {
    localSettings.value.routing.contentExpansion = 'auto'
  }
}

function updateContentExpansion() {
  if (!localSettings.value || !localSettings.value.routing) return

  if (contentExpansionService.value === 'auto') {
    localSettings.value.routing.contentExpansion = 'auto'
  } else if (contentExpansionModel.value) {
    localSettings.value.routing.contentExpansion = `${contentExpansionService.value}:${contentExpansionModel.value}`
  }
}

function updateTaskService(taskType) {
  if (!localSettings.value || !localSettings.value.routing) return

  // Reset model when service changes
  taskServiceRefs[`${taskType}Model`].value = null
  const service = taskServiceRefs[taskType].value

  if (service === 'auto') {
    localSettings.value.routing[taskType] = 'auto'
  }
}

function updateTaskModel(taskType) {
  if (!localSettings.value || !localSettings.value.routing) return

  const service = taskServiceRefs[taskType].value
  const model = taskServiceRefs[`${taskType}Model`].value

  if (service === 'auto') {
    localSettings.value.routing[taskType] = 'auto'
  } else if (model) {
    localSettings.value.routing[taskType] = `${service}:${model}`
  }
}

function save() {
  emit('update:modelValue', localSettings.value)
  emit('save', localSettings.value)
}

function addNewPrompt() {
  localSettings.value.prompts.push({ ...newPrompt.value })
  showNewPromptDialog.value = false
  newPrompt.value = {
    name: '',
    category: 'content',
    template: '',
    preferredService: 'auto',
    temperature: 0.7,
    maxTokens: 500,
    enabled: true
  }
}

function deletePrompt(index) {
  localSettings.value.prompts.splice(index, 1)
}

function testPrompt(prompt) {
  console.log('Testing prompt:', prompt)
  // TODO: Implement prompt testing
}

function getPromptIcon(category) {
  const icons = {
    content: 'mdi-file-document-edit',
    analysis: 'mdi-chart-line',
    summarization: 'mdi-format-list-bulleted',
    formatting: 'mdi-format-paint',
    research: 'mdi-magnify',
    development: 'mdi-code-braces'
  }
  return icons[category] || 'mdi-message-text'
}

function getCategoryColor(category) {
  const colors = {
    content: 'blue',
    analysis: 'green',
    summarization: 'orange',
    formatting: 'purple',
    research: 'teal',
    development: 'red'
  }
  return colors[category] || 'grey'
}

function loadPerformanceStats() {
  const saved = localStorage.getItem('llm-performance-stats')
  if (saved) {
    performanceStats.value = JSON.parse(saved)
  } else {
    performanceStats.value = {
      avgResponseTime: 1240,
      totalRequests: 0,
      successRate: 0,
      estimatedCost: 0,
      serviceBreakdown: [
        { name: 'Ollama', icon: 'mdi-server', color: 'green', requests: 0, avgTime: 0, cost: 0, status: 'inactive' },
        { name: 'OpenAI', icon: 'mdi-robot', color: 'blue', requests: 0, avgTime: 0, cost: 0, status: 'inactive' },
        { name: 'Anthropic', icon: 'mdi-brain', color: 'purple', requests: 0, avgTime: 0, cost: 0, status: 'inactive' },
        { name: 'Gemini', icon: 'mdi-google', color: 'orange', requests: 0, avgTime: 0, cost: 0, status: 'inactive' },
        { name: 'Grok', icon: 'mdi-twitter', color: 'cyan', requests: 0, avgTime: 0, cost: 0, status: 'inactive' }
      ]
    }
  }
}

function resetPerformanceStats() {
  performanceStats.value = {
    avgResponseTime: 0,
    totalRequests: 0,
    successRate: 0,
    estimatedCost: 0,
    serviceBreakdown: [
      { name: 'Ollama', icon: 'mdi-server', color: 'green', requests: 0, avgTime: 0, cost: 0, status: 'inactive' },
      { name: 'OpenAI', icon: 'mdi-robot', color: 'blue', requests: 0, avgTime: 0, cost: 0, status: 'inactive' },
      { name: 'Anthropic', icon: 'mdi-brain', color: 'purple', requests: 0, avgTime: 0, cost: 0, status: 'inactive' },
      { name: 'Gemini', icon: 'mdi-google', color: 'orange', requests: 0, avgTime: 0, cost: 0, status: 'inactive' },
      { name: 'Grok', icon: 'mdi-twitter', color: 'cyan', requests: 0, avgTime: 0, cost: 0, status: 'inactive' }
    ]
  }
  localStorage.setItem('llm-performance-stats', JSON.stringify(performanceStats.value))
}

function initializeDefaultPrompts() {
  if (!localSettings.value) {
    return
  }
  if (!localSettings.value.prompts) {
    localSettings.value.prompts = []
  }
  if (localSettings.value.prompts.length === 0) {
    localSettings.value.prompts = [
      {
        name: 'Quote Splitter',
        category: 'formatting',
        preferredService: 'auto',
        temperature: 0.3,
        maxTokens: 500,
        enabled: true,
        template: 'Split this quote into segments of maximum {maxWords} words each. Maintain natural sentence boundaries and preserve meaning:\n\n"{quote}"\n\nReturn ONLY a JSON array of strings.'
      },
      {
        name: 'Slug Generator',
        category: 'formatting',
        preferredService: 'auto',
        temperature: 0.5,
        maxTokens: 50,
        enabled: true,
        template: 'Generate a short, SEO-friendly slug (5-8 words max) for this text. Use lowercase, hyphens, no special characters:\n\n"{title}"\n\nReturn ONLY the slug.'
      },
      {
        name: 'Script Summarizer',
        category: 'summarization',
        preferredService: 'auto',
        temperature: 0.7,
        maxTokens: 200,
        enabled: true,
        template: 'Summarize this script segment in 2-3 sentences:\n\n{script}\n\nFocus on key points and main message.'
      },
      {
        name: 'Segment Generator (Tease)',
        category: 'development',
        preferredService: 'ollama',
        temperature: 0.8,
        maxTokens: 1000,
        enabled: true,
        template: 'RUNDOWN ITEM TYPE DEFINITIONS:\n- Cold Open: Opening hook before any intro/music. Grabs attention instantly with compelling question, shocking statement, or intriguing scenario. Sets episode tone. No explanations - just hook. 30-90 seconds.\n- Tease: Preview of upcoming segments to keep listeners engaged. Builds curiosity without spoiling details. References specific upcoming topics. Brief and energetic. Appears before breaks or at show start.\n- Segment: Main content blocks. In-depth discussion, analysis, interviews, storytelling. Educational yet engaging. Conversational tone. 5-15 minutes.\n- Ad: Commercial advertisement with sponsor name, product description, benefits, pricing, clear call-to-action.\n- Promo: Promotional content for the show, network shows, events, or membership offers.\n\nYOU ARE WRITING: TEASE\n\nWrite a {duration}-minute podcast tease/preview for a true crime podcast that examines manipulation tactics and abuse dynamics common to Cluster B personality disorders (narcissistic, borderline, antisocial, histrionic).\n\nThis tease should hook listeners and preview what\'s coming up in the show.{upcomingSegments}\n\nWrite {paragraphs} short, punchy paragraphs that build anticipation.\n\nStyle requirements:\n- Create urgency and intrigue\n- Tease topics without spoiling details\n- Use vivid, compelling language\n- Build curiosity about upcoming segments\n- Keep it brief and energetic\n\nCRITICAL FORMATTING:\n- Separate each paragraph with TWO newlines (blank line between paragraphs)\n- Format: Plain paragraph text, ready to paste into script\n- No titles, no metadata, just the tease content\n\nDO NOT include any introductory text like "Here is the tease" - start IMMEDIATELY with the first paragraph of actual content.\n\nGenerate the tease now:'
      },
      {
        name: 'Segment Generator (Cold Open)',
        category: 'development',
        preferredService: 'ollama',
        temperature: 0.8,
        maxTokens: 1500,
        enabled: true,
        template: 'RUNDOWN ITEM TYPE DEFINITIONS:\n- Cold Open: Opening hook before any intro/music. Grabs attention instantly with compelling question, shocking statement, or intriguing scenario. Sets episode tone. No explanations - just hook. 30-90 seconds.\n- Tease: Preview of upcoming segments to keep listeners engaged. Builds curiosity without spoiling details. References specific upcoming topics. Brief and energetic. Appears before breaks or at show start.\n- Segment: Main content blocks. In-depth discussion, analysis, interviews, storytelling. Educational yet engaging. Conversational tone. 5-15 minutes.\n- Ad: Commercial advertisement with sponsor name, product description, benefits, pricing, clear call-to-action.\n- Promo: Promotional content for the show, network shows, events, or membership offers.\n\nYOU ARE WRITING: COLD OPEN\n\nWrite a {duration}-minute cold open for a true crime podcast that examines manipulation tactics and abuse dynamics common to Cluster B personality disorders (narcissistic, borderline, antisocial, histrionic).\n\nA cold open should immediately grab attention with a compelling hook - a powerful question, shocking statement, or intriguing scenario.\n\nWrite {paragraphs} paragraphs.\n\nStyle requirements:\n- Start with maximum impact - hook listeners instantly\n- Create immediate tension or curiosity\n- Use vivid, cinematic language\n- Set the tone for the episode\n- Don\'t explain everything - leave them wanting more\n\nCRITICAL FORMATTING:\n- Separate each paragraph with TWO newlines (blank line between paragraphs)\n- Format: Plain paragraph text, ready to paste into script\n- No titles, no metadata, just the cold open content\n\nDO NOT include any introductory text - start IMMEDIATELY with the hook.\n\nGenerate the cold open now:'
      },
      {
        name: 'Segment Generator (Standard)',
        category: 'development',
        preferredService: 'ollama',
        temperature: 0.8,
        maxTokens: 2000,
        enabled: true,
        template: 'RUNDOWN ITEM TYPE DEFINITIONS:\n- Cold Open: Opening hook before any intro/music. Grabs attention instantly with compelling question, shocking statement, or intriguing scenario. Sets episode tone. No explanations - just hook. 30-90 seconds.\n- Tease: Preview of upcoming segments to keep listeners engaged. Builds curiosity without spoiling details. References specific upcoming topics. Brief and energetic. Appears before breaks or at show start.\n- Segment: Main content blocks. In-depth discussion, analysis, interviews, storytelling. Educational yet engaging. Conversational tone. 5-15 minutes.\n- Ad: Commercial advertisement with sponsor name, product description, benefits, pricing, clear call-to-action.\n- Promo: Promotional content for the show, network shows, events, or membership offers.\n\nYOU ARE WRITING: SEGMENT\n\nWrite a {duration}-minute podcast segment for a true crime podcast that examines manipulation tactics and abuse dynamics common to Cluster B personality disorders (narcissistic, borderline, antisocial, histrionic).\n\nWrite {paragraphs} paragraphs.\n\nStyle requirements:\n- Speak directly to podcast listeners in conversational, engaging tone\n- Use real psychological concepts but fictional case examples\n- Include specific manipulation tactics (gaslighting, love-bombing, triangulation, DARVO, hoovering)\n- Reference clinical patterns while remaining accessible\n- Maintain journalistic credibility and empathy for victims\n- DO NOT use real names or identify real cases\n\nCRITICAL FORMATTING:\n- Separate each paragraph with TWO newlines (blank line between paragraphs)\n- Example format:\n  First paragraph text here.\n\n  Second paragraph text here.\n\n  Third paragraph text here.\n\nFormat: Plain paragraph text, ready to paste into script. No titles, no metadata, just the segment content with blank lines between paragraphs.\n\nDO NOT include any introductory text like "Here is the podcast segment" or "Here you go" - start IMMEDIATELY with the first paragraph of actual content.\n\nGenerate the segment now:'
      }
    ]
  }
}

// Lifecycle
onMounted(async () => {
  await loadAvailableModels()
  loadPerformanceStats()
  initializeDefaultPrompts()
});
</script>

<style scoped>
.border-r {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.border-t {
  border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.routing-vertical-tabs {
  height: 100%;
}
</style>
