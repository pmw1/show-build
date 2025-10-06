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
            Prompt Library
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
                <v-list density="compact">
                  <!-- Quote Splitting -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Quote Splitting</v-list-item-title>
                    <v-select
                      v-model="localSettings.routing.quoteSplitting"
                      :items="llmServiceOptions"
                      label="Preferred Service"
                      variant="outlined"
                      density="compact"
                      hint="Intelligently split long quotes at sentence boundaries"
                      persistent-hint
                    />
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- Slug Generation -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Slug Generation</v-list-item-title>
                    <v-select
                      v-model="localSettings.routing.slugGeneration"
                      :items="llmServiceOptions"
                      label="Preferred Service"
                      variant="outlined"
                      density="compact"
                      hint="Generate SEO-friendly slugs from content"
                      persistent-hint
                    />
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- Script Summarization -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Script Summarization</v-list-item-title>
                    <v-select
                      v-model="localSettings.routing.scriptSummary"
                      :items="llmServiceOptions"
                      label="Preferred Service"
                      variant="outlined"
                      density="compact"
                      hint="Generate summaries of scripts and segments"
                      persistent-hint
                    />
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- Title Generation -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Title Generation</v-list-item-title>
                    <v-select
                      v-model="localSettings.routing.titleGeneration"
                      :items="llmServiceOptions"
                      label="Preferred Service"
                      variant="outlined"
                      density="compact"
                      hint="Generate compelling titles for episodes and segments"
                      persistent-hint
                    />
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- Content Expansion -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Content Expansion</v-list-item-title>
                    <v-select
                      v-model="localSettings.routing.contentExpansion"
                      :items="llmServiceOptions"
                      label="Preferred Service"
                      variant="outlined"
                      density="compact"
                      hint="Expand brief notes into full script content"
                      persistent-hint
                    />
                  </v-list-item>

                  <v-divider class="my-2" />

                  <!-- Fact Checking -->
                  <v-list-item>
                    <v-list-item-title class="font-weight-bold mb-2">Fact Checking</v-list-item-title>
                    <v-select
                      v-model="localSettings.routing.factChecking"
                      :items="llmServiceOptions"
                      label="Preferred Service"
                      variant="outlined"
                      density="compact"
                      hint="Verify facts and claims in content"
                      persistent-hint
                    />
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>

            <!-- Fallback Strategy -->
            <v-card variant="tonal" color="warning" class="pa-4">
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

          <!-- Prompt Library -->
          <v-tabs-window-item value="prompt-library">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-message-text</v-icon>
              Prompt Library
            </h3>
            <p class="text-body-2 mb-4">Create and manage reusable prompts for different AI tasks.</p>

            <!-- Prompt List -->
            <v-row>
              <v-col cols="12">
                <v-btn color="primary" @click="showNewPromptDialog = true" class="mb-4">
                  <v-icon left>mdi-plus</v-icon>
                  New Prompt
                </v-btn>
              </v-col>
            </v-row>

            <v-expansion-panels v-model="expandedPrompts">
              <v-expansion-panel
                v-for="(prompt, index) in localSettings.prompts"
                :key="index"
                :value="index"
              >
                <v-expansion-panel-title>
                  <v-icon left class="mr-3">{{ getPromptIcon(prompt.category) }}</v-icon>
                  <strong>{{ prompt.name }}</strong>
                  <v-spacer />
                  <v-chip size="small" :color="getCategoryColor(prompt.category)" class="mr-2">
                    {{ prompt.category }}
                  </v-chip>
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

    <!-- New Prompt Dialog -->
    <v-dialog v-model="showNewPromptDialog" max-width="800">
      <v-card>
        <v-card-title>Create New Prompt</v-card-title>
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

<script>
export default {
  name: 'LLMRoutingSettings',
  props: {
    modelValue: {
      type: Object,
      default: () => ({
        routing: {
          quoteSplitting: 'auto',
          slugGeneration: 'auto',
          scriptSummary: 'auto',
          titleGeneration: 'auto',
          contentExpansion: 'auto',
          factChecking: 'auto',
          enableFallback: true,
          fallbackOrder: ['ollama', 'openai', 'anthropic', 'gemini', 'grok']
        },
        prompts: []
      })
    }
  },
  emits: ['update:modelValue', 'save'],
  data() {
    return {
      routingSubTab: 'task-routing',
      expandedPrompts: [],
      showNewPromptDialog: false,
      localSettings: JSON.parse(JSON.stringify(this.modelValue)),
      newPrompt: {
        name: '',
        category: 'content',
        template: '',
        preferredService: 'auto',
        temperature: 0.7,
        maxTokens: 500,
        enabled: true
      },
      llmServiceOptions: [
        { title: 'Auto (Smart Routing)', value: 'auto' },
        { title: 'Ollama (Local)', value: 'ollama' },
        { title: 'OpenAI (GPT-4)', value: 'openai' },
        { title: 'Anthropic (Claude)', value: 'anthropic' },
        { title: 'Google Gemini', value: 'gemini' },
        { title: 'xAI (Grok)', value: 'grok' }
      ],
      fallbackOrderOptions: [
        { title: 'Ollama (Local)', value: 'ollama' },
        { title: 'OpenAI', value: 'openai' },
        { title: 'Anthropic', value: 'anthropic' },
        { title: 'Gemini', value: 'gemini' },
        { title: 'Grok', value: 'grok' }
      ],
      promptCategories: [
        { title: 'Content Generation', value: 'content' },
        { title: 'Analysis', value: 'analysis' },
        { title: 'Summarization', value: 'summarization' },
        { title: 'Formatting', value: 'formatting' },
        { title: 'Research', value: 'research' }
      ],
      performanceStats: {
        avgResponseTime: 0,
        totalRequests: 0,
        successRate: 0,
        estimatedCost: 0,
        serviceBreakdown: []
      }
    }
  },
  watch: {
    modelValue: {
      handler(newVal) {
        this.localSettings = JSON.parse(JSON.stringify(newVal))
      },
      deep: true
    }
  },
  mounted() {
    this.loadPerformanceStats()
    this.initializeDefaultPrompts()
  },
  methods: {
    save() {
      this.$emit('update:modelValue', this.localSettings)
      this.$emit('save', this.localSettings)
    },
    addNewPrompt() {
      this.localSettings.prompts.push({ ...this.newPrompt })
      this.showNewPromptDialog = false
      this.newPrompt = {
        name: '',
        category: 'content',
        template: '',
        preferredService: 'auto',
        temperature: 0.7,
        maxTokens: 500,
        enabled: true
      }
    },
    deletePrompt(index) {
      this.localSettings.prompts.splice(index, 1)
    },
    testPrompt(prompt) {
      console.log('Testing prompt:', prompt)
      // TODO: Implement prompt testing
    },
    getPromptIcon(category) {
      const icons = {
        content: 'mdi-file-document-edit',
        analysis: 'mdi-chart-line',
        summarization: 'mdi-format-list-bulleted',
        formatting: 'mdi-format-paint',
        research: 'mdi-magnify'
      }
      return icons[category] || 'mdi-message-text'
    },
    getCategoryColor(category) {
      const colors = {
        content: 'blue',
        analysis: 'green',
        summarization: 'orange',
        formatting: 'purple',
        research: 'teal'
      }
      return colors[category] || 'grey'
    },
    loadPerformanceStats() {
      // Load from localStorage or API
      const saved = localStorage.getItem('llm-performance-stats')
      if (saved) {
        this.performanceStats = JSON.parse(saved)
      } else {
        this.performanceStats = {
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
    },
    resetPerformanceStats() {
      this.performanceStats = {
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
      localStorage.setItem('llm-performance-stats', JSON.stringify(this.performanceStats))
    },
    initializeDefaultPrompts() {
      if (this.localSettings.prompts.length === 0) {
        this.localSettings.prompts = [
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
          }
        ]
      }
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

.routing-vertical-tabs {
  height: 100%;
}
</style>
