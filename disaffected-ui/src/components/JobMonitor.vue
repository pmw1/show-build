<template>
  <div class="job-monitor">
    <!-- Celery Jobs Icon Button -->
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
        </v-tooltip>
      </v-btn>
    </v-badge>

    <!-- Celery Jobs Panel -->
    <Teleport to="body">
      <v-navigation-drawer
        v-model="panelOpen"
        temporary
        location="right"
        width="480"
        class="job-panel"
        :scrim="true"
        style="position: fixed !important; z-index: 9000 !important;"
      >
      <v-card elevation="0">
        <v-card-title class="d-flex align-center bg-primary text-white">
          <v-icon start>mdi-briefcase-outline</v-icon>
          <span class="ml-2">Celery Jobs</span>
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
              color="white"
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

        <v-card-text class="pa-0" style="max-height: calc(100vh - 250px); overflow-y: auto;">
          <v-tabs-window v-model="activeTab">
            <!-- Active Jobs Tab -->
            <v-tabs-window-item value="active">
              <v-list v-if="activeJobs.length > 0" density="compact">
                <v-list-item
                  v-for="job in activeJobs"
                  :key="job.task_id"
                  class="job-item"
                >
                  <template v-slot:prepend>
                    <v-icon
                      :color="getStatusColor(job)"
                      :class="{ 'rotating': job.status === 'running' }"
                    >
                      {{ getJobIcon(job) }}
                    </v-icon>
                  </template>

                  <v-list-item-title class="d-flex align-center">
                    <strong>{{ job.display_name }}</strong>
                    <v-chip
                      size="x-small"
                      class="ml-2"
                      :color="getStatusColor(job)"
                    >
                      {{ job.status }}
                    </v-chip>
                    <v-chip
                      size="x-small"
                      class="ml-1"
                      :color="getCategoryColor(job.category)"
                      variant="outlined"
                    >
                      {{ job.category }}
                    </v-chip>
                  </v-list-item-title>

                  <v-list-item-subtitle>
                    <div v-if="job.episode">Episode {{ job.episode }}</div>
                    <div v-if="job.queue" class="text-caption">Queue: {{ job.queue }}</div>
                    <v-progress-linear
                      v-if="job.progress != null && job.status === 'running'"
                      :model-value="job.progress"
                      color="primary"
                      class="my-1"
                      height="6"
                      rounded
                    ></v-progress-linear>
                    <div v-if="job.stage" class="text-caption text-primary font-weight-medium">
                      {{ job.stage }}
                    </div>
                    <div class="text-caption mt-1">
                      Started {{ getTimeAgo(job.created_at) }}
                    </div>
                  </v-list-item-subtitle>
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
                  :key="job.task_id"
                  class="job-item"
                >
                  <template v-slot:prepend>
                    <v-icon :color="job.status === 'completed' ? 'success' : 'error'">
                      {{ job.status === 'completed' ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                    </v-icon>
                  </template>

                  <v-list-item-title class="d-flex align-center">
                    <strong>{{ job.display_name }}</strong>
                    <v-chip
                      size="x-small"
                      class="ml-2"
                      :color="job.status === 'completed' ? 'success' : 'error'"
                    >
                      {{ job.status }}
                    </v-chip>
                    <v-chip
                      size="x-small"
                      class="ml-1"
                      :color="getCategoryColor(job.category)"
                      variant="outlined"
                    >
                      {{ job.category }}
                    </v-chip>
                  </v-list-item-title>

                  <v-list-item-subtitle>
                    <div v-if="job.episode">Episode {{ job.episode }}</div>
                    <div v-if="job.result_summary" class="text-caption mt-1 result-text">
                      {{ job.result_summary }}
                    </div>
                    <div class="text-caption mt-1">
                      {{ getTimeAgo(job.updated_at) }}
                    </div>
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
            variant="text"
            color="error"
            @click="handleClear"
            :disabled="recentJobs.length === 0"
          >
            <v-icon start>mdi-delete-sweep</v-icon>
            Clear
          </v-btn>
          <v-btn
            size="small"
            variant="text"
            @click="fetchActiveJobs(); fetchRecentJobs();"
          >
            <v-icon start>mdi-refresh</v-icon>
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
      recentFailureCount,
      hasIssues,
      fetchActiveJobs,
      fetchRecentJobs,
      clearJobs,
      startPolling,
      stopPolling,
      getTimeAgo,
      getStatusColor,
      getCategoryColor
    } = useJobMonitor()

    const togglePanel = () => {
      panelOpen.value = !panelOpen.value
    }

    const badgeColor = computed(() => {
      if (hasIssues.value) return 'warning'
      if (activeJobCount.value > 0) return 'primary'
      return 'grey'
    })

    const getJobIcon = (job) => {
      if (job.status === 'pending') return 'mdi-clock-outline'
      if (job.status === 'running') return 'mdi-cog'
      return 'mdi-help-circle'
    }

    const handleClear = async () => {
      await clearJobs()
    }

    onMounted(() => {
      startPolling()
    })

    onBeforeUnmount(() => {
      stopPolling()
    })

    return {
      panelOpen,
      activeTab,
      activeJobs,
      recentJobs,
      isPolling,
      activeJobCount,
      recentFailureCount,
      hasIssues,
      badgeColor,
      togglePanel,
      fetchActiveJobs,
      fetchRecentJobs,
      clearJobs,
      getTimeAgo,
      getStatusColor,
      getCategoryColor,
      getJobIcon,
      handleClear
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

.result-text {
  color: rgba(0, 0, 0, 0.6);
  font-style: italic;
  max-width: 350px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
