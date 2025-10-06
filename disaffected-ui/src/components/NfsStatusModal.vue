<template>
  <v-dialog v-model="dialog" max-width="800">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" :color="nfsStatusColor">mdi-harddisk-plus</v-icon>
        NFS & Worker Status
        <v-spacer></v-spacer>
        <v-btn icon size="small" @click="dialog = false">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text>
        <!-- NFS Status Section -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-1">
            <v-icon class="mr-2" :color="nfsStatusColor">mdi-server-network</v-icon>
            NFS Server Status
          </v-card-title>
          <v-card-text>
            <v-row dense>
              <v-col cols="12" md="6">
                <div class="text-caption text-grey">Status</div>
                <div class="text-body-2">
                  <v-chip :color="nfsStatusColor" size="small" class="mr-2">
                    {{ nfsStatusText }}
                  </v-chip>
                </div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="text-caption text-grey">Mount Point</div>
                <div class="text-body-2 font-monospace">
                  {{ nfsData.mount_point || '/mnt/sync' }}
                </div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="text-caption text-grey">Read Access</div>
                <div class="text-body-2">
                  <v-icon
                    :color="nfsData.readable ? 'success' : 'error'"
                    size="small"
                  >
                    {{ nfsData.readable ? 'mdi-check-circle' : 'mdi-close-circle' }}
                  </v-icon>
                  {{ nfsData.readable ? 'OK' : 'Failed' }}
                </div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="text-caption text-grey">Write Access</div>
                <div class="text-body-2">
                  <v-icon
                    :color="nfsData.writable ? 'success' : 'error'"
                    size="small"
                  >
                    {{ nfsData.writable ? 'mdi-check-circle' : 'mdi-close-circle' }}
                  </v-icon>
                  {{ nfsData.writable ? 'OK' : 'Failed' }}
                </div>
              </v-col>
              <v-col cols="12" v-if="nfsData.error">
                <v-alert type="warning" density="compact">
                  {{ nfsData.error }}
                </v-alert>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- Celery Workers Section -->
        <v-card variant="outlined">
          <v-card-title class="text-subtitle-1">
            <v-icon class="mr-2" :color="workersStatusColor">mdi-cog-box</v-icon>
            Celery Workers
            <v-chip size="x-small" class="ml-2" :color="workersStatusColor">
              {{ workerCount }} active
            </v-chip>
          </v-card-title>
          <v-card-text>
            <div v-if="workerCount === 0">
              <v-alert type="info" density="compact">
                No workers currently active
              </v-alert>
            </div>
            <v-list v-else density="compact">
              <v-list-item
                v-for="(worker, index) in workers"
                :key="index"
                class="worker-item"
              >
                <template v-slot:prepend>
                  <v-icon color="success">mdi-check-circle</v-icon>
                </template>
                <v-list-item-title class="font-monospace">
                  {{ worker }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  {{ getWorkerDetails(worker) }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>

        <!-- Redis Status Section -->
        <v-card variant="outlined" class="mt-4">
          <v-card-title class="text-subtitle-1">
            <v-icon class="mr-2" :color="redisStatusColor">mdi-database</v-icon>
            Redis Broker
          </v-card-title>
          <v-card-text>
            <v-row dense>
              <v-col cols="12" md="6">
                <div class="text-caption text-grey">Connection</div>
                <div class="text-body-2">
                  <v-chip :color="redisStatusColor" size="small">
                    {{ redisData.connected ? 'Connected' : 'Disconnected' }}
                  </v-chip>
                </div>
              </v-col>
              <v-col cols="12" md="6" v-if="redisData.latency">
                <div class="text-caption text-grey">Latency</div>
                <div class="text-body-2">
                  {{ redisData.latency }}ms
                </div>
              </v-col>
              <v-col cols="12" v-if="redisData.error">
                <v-alert type="error" density="compact">
                  {{ redisData.error }}
                </v-alert>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-card-text>

      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" variant="text" @click="dialog = false">
          Close
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSystemHealth } from '@/composables/useSystemHealth'

const dialog = ref(false)
const { health } = useSystemHealth()

// NFS computed properties
const nfsData = computed(() => health.value.services?.nfs || {})

const nfsStatusColor = computed(() => {
  const status = nfsData.value.status
  if (status === 'connected') return 'success'
  if (status === 'warning') return 'warning'
  return 'error'
})

const nfsStatusText = computed(() => {
  const status = nfsData.value.status
  if (status === 'connected') return 'Connected'
  if (status === 'warning') return 'Issues Detected'
  if (status === 'error') return 'Disconnected'
  return 'Unknown'
})

// Workers computed properties
const workers = computed(() => health.value.services?.celery?.workers || [])
const workerCount = computed(() => workers.value.length)

const workersStatusColor = computed(() => {
  if (workerCount.value > 0) return 'success'
  return 'error'
})

// Redis computed properties
const redisData = computed(() => health.value.services?.redis || {})

const redisStatusColor = computed(() => {
  if (redisData.value.connected) return 'success'
  return 'error'
})

// Helper function to parse worker name
function getWorkerDetails(workerName) {
  // Example: "media@kairo" -> "Queue: media, Host: kairo"
  const parts = workerName.split('@')
  if (parts.length === 2) {
    return `Queue: ${parts[0]}, Host: ${parts[1]}`
  }
  return 'Active worker'
}

// Expose open method
function open() {
  dialog.value = true
}

defineExpose({
  open
})
</script>

<style scoped>
.font-monospace {
  font-family: 'Courier New', Courier, monospace;
}

.worker-item {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.worker-item:last-child {
  border-bottom: none;
}
</style>
