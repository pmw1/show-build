<template>
  <v-container fluid class="setup-container">
    <v-row justify="center">
      <v-col cols="12" lg="10" xl="8">
        <v-card class="pa-6">
          <v-card-title class="text-h4 text-center mb-6">
            <v-icon large class="mr-3">mdi-database-cog</v-icon>
            Show-Build System Setup
          </v-card-title>
          
          <v-stepper v-model="currentStep" alt-labels>
            <v-stepper-header>
              <v-stepper-item 
                :complete="currentStep > 1" 
                :value="1"
                title="Database Configuration"
                subtitle="Primary database settings"
              />
              <v-divider />
              <v-stepper-item 
                :complete="currentStep > 2" 
                :value="2" 
                title="Site Configuration"
                subtitle="Multi-site redundancy"
              />
              <v-divider />
              <v-stepper-item 
                :complete="currentStep > 3" 
                :value="3" 
                title="Network Setup"
                subtitle="WireGuard and connectivity"
              />
              <v-divider />
              <v-stepper-item 
                :value="4" 
                title="Verification"
                subtitle="Test connections"
              />
            </v-stepper-header>

            <v-stepper-window>
              <!-- Step 1: Database Configuration -->
              <v-stepper-window-item :value="1">
                <v-card flat>
                  <v-card-title class="text-h5 mb-4">
                    <v-icon class="mr-2">mdi-database</v-icon>
                    Primary Database Configuration
                    <v-icon 
                      v-if="connectionState !== 'unknown'"
                      :color="connectionState === 'success' ? 'green' : 'red'"
                      class="ml-2"
                    >
                      mdi-circle
                    </v-icon>
                  </v-card-title>
                  
                  <!-- Error Alert -->
                  <v-alert 
                    v-if="connectionState === 'failed' && connectionStatus"
                    type="error" 
                    variant="tonal"
                    class="mb-4"
                    closable
                    @click:close="connectionState = 'unknown'"
                  >
                    <v-alert-title>Connection Failed</v-alert-title>
                    {{ connectionStatus.message }}
                  </v-alert>
                  
                  <v-alert 
                    type="info" 
                    variant="tonal"
                    class="mb-4"
                  >
                    Configure the primary PostgreSQL database connection. This will be saved to your local filesystem for the frontend to access.
                  </v-alert>

                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="databaseConfig.host"
                        label="Database Host"
                        placeholder="localhost or IP address"
                        prepend-icon="mdi-server"
                        :rules="[rules.required]"
                      />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model.number="databaseConfig.port"
                        label="Database Port"
                        placeholder="5432"
                        prepend-icon="mdi-ethernet"
                        type="number"
                        :rules="[rules.required, rules.port]"
                      />
                    </v-col>
                  </v-row>

                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="databaseConfig.database"
                        label="Database Name"
                        placeholder="showbuild"
                        prepend-icon="mdi-database"
                        :rules="[rules.required]"
                      />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="databaseConfig.username"
                        label="Username"
                        placeholder="showbuild"
                        prepend-icon="mdi-account"
                        :rules="[rules.required]"
                      />
                    </v-col>
                  </v-row>

                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="databaseConfig.password"
                        label="Password"
                        :type="showPassword ? 'text' : 'password'"
                        prepend-icon="mdi-lock"
                        :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                        @click:append="showPassword = !showPassword"
                        :rules="[rules.required]"
                      />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-switch
                        v-model="databaseConfig.ssl"
                        label="Enable SSL"
                        color="primary"
                        inset
                      />
                    </v-col>
                  </v-row>

                  <v-divider class="my-6" />

                  <v-card-subtitle class="text-h6 mb-4">Connection Test</v-card-subtitle>
                  <div class="d-flex align-center gap-4">
                    <v-btn
                      color="primary"
                      @click="testDatabaseConnection"
                      :loading="testingConnection"
                      prepend-icon="mdi-connection"
                    >
                      Test Connection
                    </v-btn>
                    <v-chip
                      v-if="connectionStatus"
                      :color="connectionStatus.success ? 'success' : 'error'"
                      variant="elevated"
                    >
                      <v-icon start>{{ connectionStatus.success ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
                      {{ connectionStatus.message }}
                    </v-chip>
                  </div>
                </v-card>
              </v-stepper-window-item>

              <!-- Step 2: Site Configuration -->
              <v-stepper-window-item :value="2">
                <v-card flat>
                  <v-card-title class="text-h5 mb-4">
                    <v-icon class="mr-2">mdi-map-marker-multiple</v-icon>
                    Multi-Site Configuration
                  </v-card-title>

                  <v-alert 
                    type="info" 
                    variant="tonal"
                    class="mb-4"
                  >
                    Configure redundant database servers across multiple sites. Primary site: Ravena, NY.
                  </v-alert>

                  <!-- Primary Site -->
                  <v-card variant="outlined" class="mb-4">
                    <v-card-title class="bg-primary">
                      <v-icon class="mr-2">mdi-crown</v-icon>
                      Primary Site - Ravena, NY
                    </v-card-title>
                    <v-card-text>
                      <v-row>
                        <v-col cols="12" md="4">
                          <v-text-field
                            v-model="siteConfigs.ravena.ip"
                            label="Server IP Address"
                            prepend-icon="mdi-ip"
                            :rules="[rules.required, rules.ip]"
                          />
                        </v-col>
                        <v-col cols="12" md="4">
                          <v-text-field
                            v-model="siteConfigs.ravena.wireguardIp"
                            label="WireGuard IP"
                            placeholder="10.0.1.1"
                            prepend-icon="mdi-vpn"
                            :rules="[rules.required, rules.ip]"
                          />
                        </v-col>
                        <v-col cols="12" md="4">
                          <v-switch
                            v-model="siteConfigs.ravena.enabled"
                            label="Enable Site"
                            color="primary"
                            inset
                          />
                        </v-col>
                      </v-row>
                    </v-card-text>
                  </v-card>

                  <!-- Replica Sites -->
                  <v-card variant="outlined" class="mb-4" v-for="site in replicaSites" :key="site.key">
                    <v-card-title>
                      <v-icon class="mr-2">mdi-server-network</v-icon>
                      {{ site.name }}
                    </v-card-title>
                    <v-card-text>
                      <v-row>
                        <v-col cols="12" md="3">
                          <v-text-field
                            v-model="siteConfigs[site.key].ip"
                            label="Server IP Address"
                            prepend-icon="mdi-ip"
                            :rules="siteConfigs[site.key].enabled ? [rules.required, rules.ip] : []"
                          />
                        </v-col>
                        <v-col cols="12" md="3">
                          <v-text-field
                            v-model="siteConfigs[site.key].wireguardIp"
                            :label="`WireGuard IP (${site.subnet})`"
                            prepend-icon="mdi-vpn"
                            :rules="siteConfigs[site.key].enabled ? [rules.required, rules.ip] : []"
                          />
                        </v-col>
                        <v-col cols="12" md="3">
                          <v-select
                            v-model="siteConfigs[site.key].replicationMode"
                            label="Replication Mode"
                            :items="replicationModes"
                            prepend-icon="mdi-database-sync"
                          />
                        </v-col>
                        <v-col cols="12" md="3">
                          <v-switch
                            v-model="siteConfigs[site.key].enabled"
                            label="Enable Site"
                            color="primary"
                            inset
                          />
                        </v-col>
                      </v-row>
                    </v-card-text>
                  </v-card>
                </v-card>
              </v-stepper-window-item>

              <!-- Step 3: Network Setup -->
              <v-stepper-window-item :value="3">
                <v-card flat>
                  <v-card-title class="text-h5 mb-4">
                    <v-icon class="mr-2">mdi-vpn</v-icon>
                    WireGuard Network Configuration
                  </v-card-title>

                  <v-alert 
                    type="warning" 
                    variant="tonal"
                    class="mb-4"
                  >
                    WireGuard VPN must be configured between all sites before enabling replication.
                  </v-alert>

                  <v-row>
                    <v-col cols="12" md="6">
                      <v-textarea
                        v-model="networkConfig.publicKey"
                        label="WireGuard Public Key"
                        placeholder="Enter your WireGuard public key"
                        prepend-icon="mdi-key"
                        rows="3"
                        :rules="[rules.required]"
                      />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-textarea
                        v-model="networkConfig.privateKey"
                        label="WireGuard Private Key"
                        placeholder="Enter your WireGuard private key"
                        prepend-icon="mdi-key-variant"
                        rows="3"
                        :rules="[rules.required]"
                      />
                    </v-col>
                  </v-row>

                  <v-row>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model.number="networkConfig.listenPort"
                        label="Listen Port"
                        placeholder="51820"
                        prepend-icon="mdi-ethernet"
                        type="number"
                        :rules="[rules.required, rules.port]"
                      />
                    </v-col>
                    <v-col cols="12" md="6">
                      <v-text-field
                        v-model="networkConfig.endpoint"
                        label="Public Endpoint"
                        placeholder="your-domain.com:51820"
                        prepend-icon="mdi-web"
                      />
                    </v-col>
                  </v-row>

                  <v-divider class="my-6" />

                  <v-card-subtitle class="text-h6 mb-4">Peer Connectivity Test</v-card-subtitle>
                  <v-data-table
                    :headers="peerHeaders"
                    :items="peerTests"
                    item-key="site"
                    class="elevation-1"
                  >
                    <template #[`item.status`]="{ item }">
                      <v-chip
                        :color="item.status === 'Connected' ? 'success' : item.status === 'Connecting...' ? 'warning' : 'error'"
                        size="small"
                      >
                        {{ item.status }}
                      </v-chip>
                    </template>
                    <template #[`item.actions`]="{ item }">
                      <v-btn
                        size="small"
                        color="primary"
                        @click="testPeerConnection(item.site)"
                        :loading="testingPeers[item.site]"
                      >
                        Test
                      </v-btn>
                    </template>
                  </v-data-table>
                </v-card>
              </v-stepper-window-item>

              <!-- Step 4: Verification -->
              <v-stepper-window-item :value="4">
                <v-card flat>
                  <v-card-title class="text-h5 mb-4">
                    <v-icon class="mr-2">mdi-check-circle</v-icon>
                    System Verification
                  </v-card-title>

                  <v-alert 
                    type="success" 
                    variant="tonal"
                    class="mb-4"
                    v-if="verificationComplete && verificationSuccess"
                  >
                    All systems configured successfully! Your multi-site database redundancy is ready.
                  </v-alert>

                  <v-alert 
                    type="error" 
                    variant="tonal"
                    class="mb-4"
                    v-if="verificationComplete && !verificationSuccess"
                  >
                    Some configurations need attention. Please review the status below.
                  </v-alert>

                  <v-card variant="outlined">
                    <v-card-title>System Status</v-card-title>
                    <v-card-text>
                      <v-list>
                        <v-list-item
                          v-for="check in verificationChecks"
                          :key="check.name"
                          :prepend-icon="check.status === 'success' ? 'mdi-check-circle' : check.status === 'warning' ? 'mdi-alert' : 'mdi-close-circle'"
                          :color="check.status === 'success' ? 'success' : check.status === 'warning' ? 'warning' : 'error'"
                        >
                          <v-list-item-title>{{ check.name }}</v-list-item-title>
                          <v-list-item-subtitle>{{ check.message }}</v-list-item-subtitle>
                        </v-list-item>
                      </v-list>
                    </v-card-text>
                  </v-card>

                  <div class="text-center mt-6">
                    <v-btn
                      color="primary"
                      size="large"
                      @click="runVerification"
                      :loading="verifying"
                      prepend-icon="mdi-play"
                    >
                      Run Full Verification
                    </v-btn>
                  </div>
                </v-card>
              </v-stepper-window-item>
            </v-stepper-window>

            <!-- Navigation Buttons -->
            <v-card-actions class="justify-space-between pa-6">
              <v-btn
                variant="outlined"
                @click="previousStep"
                :disabled="currentStep === 1"
                prepend-icon="mdi-chevron-left"
              >
                Previous
              </v-btn>

              <v-btn
                color="primary"
                @click="nextStep"
                :disabled="!canProceed"
                :append-icon="currentStep === 4 ? 'mdi-check' : 'mdi-chevron-right'"
              >
                {{ currentStep === 4 ? 'Complete Setup' : 'Next' }}
              </v-btn>
            </v-card-actions>
          </v-stepper>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showUrgentFlash } from '@/composables/useUrgentFlash'

const router = useRouter()

// Step management
const currentStep = ref(1)

// Form data
const databaseConfig = ref({
  host: 'postgres',
  port: 5432,
  database: 'showbuild',
  username: 'showbuild',
  password: 'showbuild',
  ssl: false
})

const siteConfigs = ref({
  ravena: {
    ip: '',
    wireguardIp: '10.0.1.1',
    enabled: true,
    role: 'primary'
  },
  burlington: {
    ip: '',
    wireguardIp: '10.0.2.1',
    enabled: false,
    replicationMode: 'async',
    role: 'replica'
  },
  montpelier: {
    ip: '',
    wireguardIp: '10.0.3.1',
    enabled: false,
    replicationMode: 'async',
    role: 'replica'
  },
  nantucket: {
    ip: '',
    wireguardIp: '10.0.4.1',
    enabled: false,
    replicationMode: 'async',
    role: 'replica'
  },
  tucson: {
    ip: '',
    wireguardIp: '10.0.5.1',
    enabled: false,
    replicationMode: 'async',
    role: 'replica'
  }
})

const networkConfig = ref({
  publicKey: '',
  privateKey: '',
  listenPort: 51820,
  endpoint: ''
})

// UI state
const showPassword = ref(false)
const testingConnection = ref(false)
const connectionStatus = ref(null)
const connectionState = ref('unknown') // 'unknown', 'success', 'failed'
const testingPeers = ref({})
const verifying = ref(false)
const verificationComplete = ref(false)
const verificationSuccess = ref(false)

// Static data
const replicaSites = [
  { key: 'burlington', name: 'Burlington, VT', subnet: '10.0.2.x' },
  { key: 'montpelier', name: 'Montpelier, VT', subnet: '10.0.3.x' },
  { key: 'nantucket', name: 'Nantucket, MA', subnet: '10.0.4.x' },
  { key: 'tucson', name: 'Tucson, AZ', subnet: '10.0.5.x' }
]

const replicationModes = [
  { title: 'Asynchronous', value: 'async' },
  { title: 'Synchronous', value: 'sync' },
  { title: 'Logical', value: 'logical' }
]

const peerHeaders = [
  { title: 'Site', key: 'site' },
  { title: 'IP Address', key: 'ip' },
  { title: 'Status', key: 'status' },
  { title: 'Latency', key: 'latency' },
  { title: 'Actions', key: 'actions', sortable: false }
]

const peerTests = computed(() => {
  return Object.keys(siteConfigs.value)
    .filter(key => siteConfigs.value[key].enabled && key !== 'ravena')
    .map(key => ({
      site: key,
      ip: siteConfigs.value[key].wireguardIp,
      status: 'Not tested',
      latency: '-'
    }))
})

const verificationChecks = ref([
  { name: 'Database Connection', status: 'pending', message: 'Waiting for verification...' },
  { name: 'WireGuard Network', status: 'pending', message: 'Waiting for verification...' },
  { name: 'Site Connectivity', status: 'pending', message: 'Waiting for verification...' },
  { name: 'Replication Setup', status: 'pending', message: 'Waiting for verification...' },
  { name: 'Configuration Storage', status: 'pending', message: 'Waiting for verification...' }
])

// Validation rules
const rules = {
  required: value => !!value || 'This field is required',
  port: value => (value > 0 && value <= 65535) || 'Invalid port number',
  ip: value => {
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/
    return ipRegex.test(value) || 'Invalid IP address'
  }
}

// Computed properties
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 1:
      return connectionStatus.value && connectionStatus.value.success
    case 2:
      return true // Can proceed even if no replica sites are enabled
    case 3:
      return networkConfig.value.publicKey && networkConfig.value.privateKey
    case 4:
      return verificationComplete.value
    default:
      return false
  }
})

// Methods
async function testDatabaseConnection() {
  testingConnection.value = true
  connectionStatus.value = null

  try {
    const response = await fetch('/api/setup/test-database', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(databaseConfig.value)
    })

    const result = await response.json()
    connectionStatus.value = {
      success: result.success,
      message: result.message || (result.success ? 'Connection successful' : 'Connection failed')
    }
    
    if (!result.success) {
      showUrgentFlash("LOSER", "red")
      connectionState.value = 'failed'
    } else {
      showUrgentFlash("WINNER!", "green")
      connectionState.value = 'success'
    }
  } catch (error) {
    connectionStatus.value = {
      success: false,
      message: 'Network error: ' + error.message
    }
    showUrgentFlash("LOSER", "red")
    connectionState.value = 'failed'
  } finally {
    testingConnection.value = false
  }
}

async function testPeerConnection(site) {
  testingPeers.value[site] = true
  
  try {
    const config = siteConfigs.value[site]
    const response = await fetch('/api/setup/test-peer', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ip: config.wireguardIp,
        site: site
      })
    })

    const result = await response.json()
    
    // Update peer test results
    const peer = peerTests.value.find(p => p.site === site)
    if (peer) {
      peer.status = result.success ? 'Connected' : 'Failed'
      peer.latency = result.latency || '-'
    }
  } catch (error) {
    console.error(`Failed to test peer ${site}:`, error)
  } finally {
    testingPeers.value[site] = false
  }
}

async function runVerification() {
  verifying.value = true
  verificationComplete.value = false
  
  try {
    const response = await fetch('/api/setup/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        database: databaseConfig.value,
        sites: siteConfigs.value,
        network: networkConfig.value
      })
    })

    const result = await response.json()
    verificationChecks.value = result.checks || verificationChecks.value
    verificationSuccess.value = result.success
    verificationComplete.value = true

    if (result.success) {
      // Save configuration to local filesystem
      await saveConfiguration()
    }
  } catch (error) {
    console.error('Verification failed:', error)
    verificationComplete.value = true
    verificationSuccess.value = false
  } finally {
    verifying.value = false
  }
}

async function saveConfiguration() {
  try {
    const config = {
      database: databaseConfig.value,
      sites: siteConfigs.value,
      network: networkConfig.value,
      timestamp: new Date().toISOString()
    }

    const response = await fetch('/api/setup/save-config', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config)
    })

    if (!response.ok) {
      throw new Error('Failed to save configuration')
    }

    console.log('Configuration saved successfully')
  } catch (error) {
    console.error('Failed to save configuration:', error)
  }
}

function nextStep() {
  if (currentStep.value < 4) {
    currentStep.value++
  } else if (verificationSuccess.value) {
    // Complete setup and redirect to main application
    router.push('/')
  }
}

function previousStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

// Load existing configuration if available
async function loadExistingConfig() {
  try {
    const response = await fetch('/api/setup/load-config')
    if (response.ok) {
      const config = await response.json()
      if (config.database) databaseConfig.value = { ...databaseConfig.value, ...config.database }
      if (config.sites) siteConfigs.value = { ...siteConfigs.value, ...config.sites }
      if (config.network) networkConfig.value = { ...networkConfig.value, ...config.network }
    }
  } catch (error) {
    console.log('No existing configuration found')
  }
}

onMounted(() => {
  loadExistingConfig()
})
</script>

<style scoped>
.setup-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.v-stepper {
  background: transparent;
}

.v-card {
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
}

/* Move database config text field labels up - step 1 only */
:deep(.v-stepper-window-item:nth-child(1) .v-text-field label) {
  transform: translateY(-2em) !important;
}
:deep(.v-stepper-window-item:nth-child(1) .v-text-field .v-field-label) {
  transform: translateY(-2em) !important;
}
/* Special handling for password field only */
:deep(.v-stepper-window-item:nth-child(1) .v-text-field:has(input[type="password"]) label) {
  transform: translateY(-3em) !important;
}

/* Connection status chip styling */
:deep(.v-chip) {
  border-radius: 0 !important;
  margin-left: 2em !important;
}
</style>