<template>
  <div class="job-monitor">
    <!-- Job Monitor Icon Button -->
    <v-badge
      :content="activeJobCount"
      :color="badgeColor"
      overlap
      :model-value="activeJobCount > 0"
    >
      <v-btn
        icon
        @click="togglePanel"
        :color="hasIssues ? 'warning' : 'primary'"
      >
        <v-icon>
          {{ isPolling ? 'mdi-cog-sync' : 'mdi-briefcase-outline' }}
        </v-icon>
        <v-tooltip activator="parent" location="bottom">
          {{ activeJobCount }} active job{{ activeJobCount !== 1 ? 's' : '' }}
          <span v-if="stalledJobCount > 0"> ({{ stalledJobCount }} stalled)</span>
        </v-tooltip>
      </v-btn>
    </v-badge>

    <!-- Job Monitor Panel (teleported to body to escape stacking context) -->
    <Teleport to="body">
      <v-navigation-drawer
        v-model="panelOpen"
        temporary
        location="right"
        width="450"
        class="job-panel"
        :scrim="true"
        style="position: fixed !important; z-index: 9000 !important;"
      >
      <v-card elevation="0">
        <v-card-title class="d-flex align-center bg-primary text-white">
          <v-icon left>mdi-briefcase-outline</v-icon>
          <span class="ml-2">Job Monitor</span>
          <v-spacer></v-spacer>
          <v-btn
            icon
            size="small"
            @click="panelOpen = false"
          >
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>

        <v-divider></v-divider>

        <v-tabs v-model="activeTab" bg-color="primary">
          <v-tab value="active">
            Active
            <v-chip
              v-if="activeJobCount > 0"
              size="small"
              class="ml-2"
              :color="hasIssues ? 'warning' : 'primary'"
            >
              {{ activeJobCount }}
            </v-chip>
          </v-tab>
          <v-tab value="recent">
            Recent
            <v-chip
              v-if="recentFailureCount > 0"
              size="small"
              class="ml-2"
              color="error"
            >
              {{ recentFailureCount }} failed
            </v-chip>
          </v-tab>
        </v-tabs>

        <v-card-text class="pa-0" style="max-height: calc(100vh - 200px); overflow-y: auto;">
          <v-tabs-window v-model="activeTab">
            <!-- Active Jobs Tab -->
            <v-tabs-window-item value="active">
              <v-list v-if="activeJobs.length > 0" density="compact">
                <v-list-item
                  v-for="job in activeJobs"
                  :key="job.job_id"
                  class="job-item"
                >
                  <template v-slot:prepend>
                    <v-icon
                      :color="getStatusColor(job)"
                      :class="{ 'rotating': job.status === 'processing' && !job.is_stalled }"
                    >
                      {{ getJobIcon(job) }}
                    </v-icon>
                  </template>

                  <v-list-item-title>
                    <strong>{{ job.slug }}</strong>
                    <v-chip
                      size="x-small"
                      class="ml-2"
                      :color="getStatusColor(job)"
                    >
                      {{ job.is_stalled ? 'STALLED' : job.status }}
                    </v-chip>
                  </v-list-item-title>

                  <v-list-item-subtitle>
                    <div>Episode {{ job.episode }} • {{ getPhaseDisplayName(job.current_phase) }}</div>
                    <div class="text-caption mt-1">
                      Started {{ getTimeAgo(job.created_at) }} • Updated {{ getTimeAgo(job.updated_at) }}
                    </div>
                    <div v-if="job.error_message" class="error-box mt-2 pa-2">
                      <div class="error-title">
                        <v-icon size="small" color="error">mdi-alert-circle</v-icon>
                        <strong class="ml-1">Error:</strong>
                      </div>
                      <div class="error-message">{{ job.error_message }}</div>
                    </div>
                    <v-expansion-panels v-if="job.error_message || job.is_stalled" class="mt-2" density="compact">
                      <v-expansion-panel>
                        <v-expansion-panel-title class="text-caption">
                          Debug Info
                        </v-expansion-panel-title>
                        <v-expansion-panel-text class="text-caption">
                          <div><strong>Job ID:</strong> {{ job.job_id }}</div>
                          <div><strong>Asset ID:</strong> {{ job.asset_id }}</div>
                          <div><strong>Celery Task:</strong> {{ job.celery_task_id }}</div>
                          <div><strong>Phase:</strong> {{ job.current_phase }}</div>
                          <div><strong>Created:</strong> {{ new Date(job.created_at).toLocaleString() }}</div>
                          <div><strong>Updated:</strong> {{ new Date(job.updated_at).toLocaleString() }}</div>
                        </v-expansion-panel-text>
                      </v-expansion-panel>
                    </v-expansion-panels>
                  </v-list-item-subtitle>

                  <template v-slot:append>
                    <v-btn
                      v-if="job.is_stalled"
                      icon
                      size="small"
                      color="warning"
                      @click="markAsFailedAndRefresh(job)"
                    >
                      <v-icon>mdi-alert-circle</v-icon>
                      <v-tooltip activator="parent">Mark as failed</v-tooltip>
                    </v-btn>
                  </template>
                </v-list-item>
              </v-list>

              <div v-else class="pa-4 text-center text-grey">
                <v-icon size="64" color="grey-lighten-1">mdi-check-circle-outline</v-icon>
                <div class="mt-2">No active jobs</div>
              </div>
            </v-tabs-window-item>

            <!-- Recent Jobs Tab -->
            <v-tabs-window-item value="recent">
              <v-list v-if="recentJobs.length > 0" density="compact">
                <v-list-item
                  v-for="job in recentJobs"
                  :key="job.job_id"
                  class="job-item"
                >
                  <template v-slot:prepend>
                    <v-icon :color="job.status === 'completed' ? 'success' : 'error'">
                      {{ job.status === 'completed' ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                    </v-icon>
                  </template>

                  <v-list-item-title>
                    <strong>{{ job.slug }}</strong>
                    <v-chip
                      size="x-small"
                      class="ml-2"
                      :color="job.status === 'completed' ? 'success' : 'error'"
                    >
                      {{ job.status }}
                    </v-chip>
                  </v-list-item-title>

                  <v-list-item-subtitle>
                    <div>Episode {{ job.episode }}</div>
                    <div class="text-caption mt-1">
                      Completed {{ getTimeAgo(job.updated_at) }}
                    </div>
                    <div v-if="job.error_message" class="error-box mt-2 pa-2">
                      <div class="error-title">
                        <v-icon size="small" color="error">mdi-alert-circle</v-icon>
                        <strong class="ml-1">Error:</strong>
                      </div>
                      <div class="error-message">{{ job.error_message }}</div>
                    </div>
                    <v-expansion-panels v-if="job.error_message" class="mt-2" density="compact">
                      <v-expansion-panel>
                        <v-expansion-panel-title class="text-caption">
                          Debug Info
                        </v-expansion-panel-title>
                        <v-expansion-panel-text class="text-caption">
                          <div><strong>Job ID:</strong> {{ job.job_id }}</div>
                          <div><strong>Asset ID:</strong> {{ job.asset_id }}</div>
                          <div><strong>Celery Task:</strong> {{ job.celery_task_id }}</div>
                          <div><strong>Phase:</strong> {{ job.current_phase }}</div>
                          <div><strong>Created:</strong> {{ new Date(job.created_at).toLocaleString() }}</div>
                          <div><strong>Completed:</strong> {{ new Date(job.updated_at).toLocaleString() }}</div>
                        </v-expansion-panel-text>
                      </v-expansion-panel>
                    </v-expansion-panels>
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>

              <div v-else class="pa-4 text-center text-grey">
                <v-icon size="64" color="grey-lighten-1">mdi-history</v-icon>
                <div class="mt-2">No recent jobs</div>
              </div>
            </v-tabs-window-item>
          </v-tabs-window>
        </v-card-text>

        <v-divider></v-divider>

        <v-card-actions>
          <v-chip size="small" :color="isPolling ? 'success' : 'grey'">
            <v-icon size="small" start>
              {{ isPolling ? 'mdi-radio-tower' : 'mdi-sleep' }}
            </v-icon>
            {{ isPolling ? 'Live' : 'Paused' }}
          </v-chip>
          <v-spacer></v-spacer>
          <v-btn
            size="small"
            @click="fetchActiveJobs(); fetchRecentJobs();"
          >
            <v-icon left>mdi-refresh</v-icon>
            Refresh
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-navigation-drawer>
    </Teleport>
  </div>
</template>

<script>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useJobMonitor } from '../composables/useJobMonitor.js'

export default {
  name: 'JobMonitor',

  setup() {
    const panelOpen = ref(false)
    const activeTab = ref('active')

    const {
      activeJobs,
      recentJobs,
      isPolling,
      activeJobCount,
      stalledJobCount,
      recentFailureCount,
      hasIssues,
      fetchActiveJobs,
      fetchRecentJobs,
      startPolling,
      stopPolling,
      getTimeAgo,
      getPhaseDisplayName,
      getStatusColor
    } = useJobMonitor()

    const togglePanel = () => {
      panelOpen.value = !panelOpen.value
    }

    const badgeColor = computed(() => {
      if (stalledJobCount.value > 0) return 'warning'
      if (activeJobCount.value > 0) return 'primary'
      return 'grey'
    })

    const getJobIcon = (job) => {
      if (job.is_stalled) return 'mdi-alert-circle'
      if (job.status === 'queued') return 'mdi-clock-outline'
      if (job.status === 'processing') return 'mdi-cog'
      return 'mdi-help-circle'
    }

    const markAsFailedAndRefresh = async (job) => {
      // TODO: Add API endpoint to mark job as failed
      console.log('Mark as failed:', job.job_id)
      await fetchActiveJobs()
    }

    onMounted(() => {
      startPolling()
    })

    onBeforeUnmount(() => {
      stopPolling()
    })

    return {
      // State
      panelOpen,
      activeTab,
      activeJobs,
      recentJobs,
      isPolling,

      // Computed
      activeJobCount,
      stalledJobCount,
      recentFailureCount,
      hasIssues,
      badgeColor,

      // Methods
      togglePanel,
      fetchActiveJobs,
      fetchRecentJobs,
      getTimeAgo,
      getPhaseDisplayName,
      getStatusColor,
      getJobIcon,
      markAsFailedAndRefresh
    }
  }
}
</script>

<style scoped>
.job-monitor {
  display: inline-block;
}

.job-panel {
  z-index: 9000 !important;
}

.job-item {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.job-item:last-child {
  border-bottom: none;
}

.error-text {
  color: #f44336;
  font-size: 0.75rem;
  font-style: italic;
}

.error-box {
  background-color: rgba(244, 67, 54, 0.1);
  border-left: 3px solid #f44336;
  border-radius: 4px;
}

.error-title {
  display: flex;
  align-items: center;
  font-size: 0.75rem;
  margin-bottom: 4px;
}

.error-message {
  font-size: 0.75rem;
  color: #d32f2f;
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-word;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.rotating {
  animation: rotate 2s linear infinite;
}
</style>

<style>
/* Non-scoped styles for Vuetify navigation drawer */
.v-navigation-drawer.job-panel {
  z-index: 9000 !important;
}
</style>
