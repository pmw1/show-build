<template>
  <div class="metafactory-view fill-height d-flex flex-column pa-2">
    <!-- Header -->
    <div class="d-flex align-center mb-2 px-2">
      <div>
        <h2 class="text-h5 font-weight-bold mb-0">MetaFactory</h2>
        <p class="text-caption text-medium-emphasis mb-0">
          Metadata extraction and content intelligence tools
        </p>
      </div>
    </div>

    <!-- Main Content with Tabs -->
    <div class="flex-grow-1 d-flex flex-column" style="min-height: 0;">
        <v-card class="flex-grow-1 d-flex flex-column" style="min-height: 0;">
          <!-- Tabs Navigation -->
          <v-tabs v-model="activeTab" color="primary" bg-color="surface">
            <v-tab value="extract-meta">
              <v-icon start>mdi-brain</v-icon>
              Extract Meta
            </v-tab>
            <v-tab value="episode-context">
              <v-icon start>mdi-file-document-outline</v-icon>
              Episode Context
            </v-tab>
            <!-- Future tabs can be added here -->
            <!--
            <v-tab value="entity-manager">
              <v-icon start>mdi-account-group</v-icon>
              Entity Manager
            </v-tab>
            -->
          </v-tabs>
          <v-divider />

          <!-- Tab Content -->
          <v-window v-model="activeTab" class="flex-grow-1" style="min-height: 0;">
            <!-- Extract Meta Tab -->
            <v-window-item value="extract-meta" class="fill-height">
              <MetaExtraction :episode="currentEpisode" />
            </v-window-item>

            <!-- Episode Context Tab -->
            <v-window-item value="episode-context" class="fill-height">
              <div class="pa-4 fill-height overflow-y-auto">
                <!-- Episode Status Banner -->
                <v-alert v-if="!currentEpisode" type="info" variant="tonal" prominent class="mb-4">
                  <v-alert-title>No Episode Selected</v-alert-title>
                  Select an episode from the header to view episode context.
                </v-alert>

                <template v-if="currentEpisode">
                  <div class="d-flex align-center mb-4">
                    <v-btn
                      color="primary"
                      variant="flat"
                      prepend-icon="mdi-refresh"
                      @click="loadEpisodeContext"
                      :loading="loadingContext"
                    >
                      Load Episode Context
                    </v-btn>
                    <v-spacer />
                    <v-chip
                      v-if="episodeContext"
                      color="info"
                      variant="tonal"
                      size="small"
                    >
                      {{ episodeContext.segment_count }} segments aggregated
                    </v-chip>
                  </div>

                  <v-alert
                    v-if="!episodeContext"
                    type="info"
                    variant="tonal"
                    class="mb-4"
                  >
                    Click "Load Episode Context" to aggregate LLM data from all segments into template variables.
                  </v-alert>

                  <template v-if="episodeContext">
                    <!-- Template Variables -->
                    <v-card variant="outlined" class="mb-4">
                      <v-card-title class="text-subtitle-1">
                        <v-icon start>mdi-code-braces</v-icon>
                        Template Variables
                      </v-card-title>
                      <v-card-text>
                        <v-row>
                          <v-col cols="12" md="6">
                            <div class="variable-block">
                              <div class="variable-label">{{guest_names}}</div>
                              <div class="variable-value">
                                {{ episodeContext.template_variables?.guest_names || 'No guests extracted' }}
                              </div>
                            </div>
                          </v-col>
                          <v-col cols="12" md="6">
                            <div class="variable-block">
                              <div class="variable-label">{{topics}}</div>
                              <div class="variable-value">
                                {{ episodeContext.template_variables?.topics || 'No topics extracted' }}
                              </div>
                            </div>
                          </v-col>
                          <v-col cols="12" md="6">
                            <div class="variable-block">
                              <div class="variable-label">{{organizations}}</div>
                              <div class="variable-value">
                                {{ episodeContext.template_variables?.organizations || 'No organizations extracted' }}
                              </div>
                            </div>
                          </v-col>
                          <v-col cols="12" md="6">
                            <div class="variable-block">
                              <div class="variable-label">{{segment_summaries}}</div>
                              <div class="variable-value text-truncate">
                                {{ (episodeContext.template_variables?.segment_summaries || 'No summaries').substring(0, 150) }}...
                              </div>
                            </div>
                          </v-col>
                        </v-row>
                      </v-card-text>
                    </v-card>

                    <!-- Aggregated Entities -->
                    <v-row>
                      <v-col cols="12" md="4">
                        <v-card variant="outlined">
                          <v-card-title class="text-subtitle-1">
                            <v-icon start color="blue">mdi-account-group</v-icon>
                            People ({{ episodeContext.aggregated?.all_people?.length || 0 }})
                          </v-card-title>
                          <v-card-text>
                            <v-chip
                              v-for="person in (episodeContext.aggregated?.all_people || []).slice(0, 10)"
                              :key="person.name"
                              size="small"
                              class="ma-1"
                              color="blue"
                              variant="tonal"
                            >
                              {{ person.name }}
                              <span v-if="person.role" class="text-caption ms-1">({{ person.role }})</span>
                            </v-chip>
                            <div v-if="!episodeContext.aggregated?.all_people?.length" class="text-medium-emphasis">
                              No people extracted
                            </div>
                          </v-card-text>
                        </v-card>
                      </v-col>
                      <v-col cols="12" md="4">
                        <v-card variant="outlined">
                          <v-card-title class="text-subtitle-1">
                            <v-icon start color="purple">mdi-domain</v-icon>
                            Organizations ({{ episodeContext.aggregated?.all_organizations?.length || 0 }})
                          </v-card-title>
                          <v-card-text>
                            <v-chip
                              v-for="org in (episodeContext.aggregated?.all_organizations || []).slice(0, 10)"
                              :key="org.name"
                              size="small"
                              class="ma-1"
                              color="purple"
                              variant="tonal"
                            >
                              {{ org.name }}
                            </v-chip>
                            <div v-if="!episodeContext.aggregated?.all_organizations?.length" class="text-medium-emphasis">
                              No organizations extracted
                            </div>
                          </v-card-text>
                        </v-card>
                      </v-col>
                      <v-col cols="12" md="4">
                        <v-card variant="outlined">
                          <v-card-title class="text-subtitle-1">
                            <v-icon start color="teal">mdi-tag-multiple</v-icon>
                            Topics ({{ episodeContext.aggregated?.all_topics?.length || 0 }})
                          </v-card-title>
                          <v-card-text>
                            <v-chip
                              v-for="topic in (episodeContext.aggregated?.all_topics || []).slice(0, 15)"
                              :key="topic"
                              size="small"
                              class="ma-1"
                              color="teal"
                              variant="tonal"
                            >
                              {{ topic }}
                            </v-chip>
                            <div v-if="!episodeContext.aggregated?.all_topics?.length" class="text-medium-emphasis">
                              No topics extracted
                            </div>
                          </v-card-text>
                        </v-card>
                      </v-col>
                    </v-row>

                    <!-- Key Quotes -->
                    <v-card variant="outlined" class="mt-4" v-if="episodeContext.aggregated?.all_quotes?.length">
                      <v-card-title class="text-subtitle-1">
                        <v-icon start color="amber">mdi-format-quote-close</v-icon>
                        Key Quotes ({{ episodeContext.aggregated?.all_quotes?.length || 0 }})
                      </v-card-title>
                      <v-card-text>
                        <v-list density="compact">
                          <v-list-item
                            v-for="(quote, idx) in episodeContext.aggregated?.all_quotes?.slice(0, 5)"
                            :key="idx"
                          >
                            <template v-slot:prepend>
                              <v-icon color="amber" size="small">mdi-format-quote-open</v-icon>
                            </template>
                            <v-list-item-title class="text-wrap font-italic">
                              "{{ quote }}"
                            </v-list-item-title>
                          </v-list-item>
                        </v-list>
                      </v-card-text>
                    </v-card>
                  </template>
                </template>
              </div>
            </v-window-item>
          </v-window>
        </v-card>
      </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useSegmentLLMData } from '@/composables/useSegmentLLMData'
import MetaExtraction from '@/components/metafactory/MetaExtraction.vue'

export default {
  name: 'MetaFactoryView',

  components: {
    MetaExtraction
  },

  setup() {
    const { getEpisodeLLMContext } = useSegmentLLMData()

    // State
    const currentEpisode = ref(null)
    const activeTab = ref('extract-meta')
    const episodeContext = ref(null)
    const loadingContext = ref(false)

    // Methods
    async function loadEpisodeContext() {
      if (!currentEpisode.value) return

      loadingContext.value = true
      try {
        const context = await getEpisodeLLMContext(currentEpisode.value)
        episodeContext.value = context
      } catch (error) {
        console.error('Failed to load episode context:', error)
      } finally {
        loadingContext.value = false
      }
    }

    // Watch for episode changes via sessionStorage
    function checkEpisode() {
      const stored = sessionStorage.getItem('currentEpisode')
      if (stored !== currentEpisode.value) {
        currentEpisode.value = stored
        episodeContext.value = null
      }
    }

    // Setup interval to check for episode changes
    let episodeCheckInterval = null

    onMounted(() => {
      checkEpisode()
      episodeCheckInterval = setInterval(checkEpisode, 1000)
    })

    onUnmounted(() => {
      if (episodeCheckInterval) {
        clearInterval(episodeCheckInterval)
      }
    })

    return {
      // State
      currentEpisode,
      activeTab,
      episodeContext,
      loadingContext,

      // Methods
      loadEpisodeContext
    }
  }
}
</script>

<style scoped>
.metafactory-view {
  width: 100%;
  max-width: 100%;
}

.fill-height {
  height: 100%;
}

.variable-block {
  background: rgba(0, 0, 0, 0.03);
  border-radius: 8px;
  padding: 12px;
}

.variable-label {
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  color: #1976d2;
  font-weight: 600;
  margin-bottom: 4px;
}

.variable-value {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.7);
}

.v-theme--dark .variable-block {
  background: rgba(255, 255, 255, 0.05);
}

.v-theme--dark .variable-value {
  color: rgba(255, 255, 255, 0.7);
}
</style>
