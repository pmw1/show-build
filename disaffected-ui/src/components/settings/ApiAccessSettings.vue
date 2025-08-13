<template>
  <v-card class="pa-4">
    <v-card-title class="text-h6 mb-4">
      <v-icon left>mdi-api</v-icon>
      API Access Configuration
    </v-card-title>
    
    <v-card-text>
      <p class="mb-6 text-body-2">
        Configure API access for AI services, cloud storage, communication tools, and integrations.
        All credentials are securely stored and encrypted. Enable only the services you plan to use.
      </p>

      <!-- Quick Setup Guide -->
      <v-alert
        type="info"
        variant="tonal"
        class="mb-6"
        closable
      >
        <v-alert-title>Getting Started</v-alert-title>
        <ul class="mt-2">
          <li>Start with AI services (OpenAI, Claude) for content generation</li>
          <li>Add cloud storage (Google Drive, OneDrive) for file management</li>
          <li>Configure communication (Slack, Discord) for notifications</li>
          <li>Test connections before enabling services</li>
        </ul>
      </v-alert>

      <!-- AI & ML Services Section -->
      <v-expansion-panels class="mb-4" multiple v-model="expandedPanels">
        
        <!-- Local AI Services -->
        <v-expansion-panel value="local-ai">
          <v-expansion-panel-title>
            <v-icon left class="mr-3">mdi-brain</v-icon>
            Local AI Services
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row>
              <!-- Ollama Configuration -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">Ollama</v-card-title>
                  <v-text-field
                    v-model="configs.ollama.host"
                    label="Host URL"
                    placeholder="http://localhost:11434"
                    persistent-hint
                    hint="Local Ollama instance endpoint"
                  />
                  <v-text-field
                    v-model="configs.ollama.apiKey"
                    label="API Key (optional)"
                    type="password"
                    placeholder="Enter API key if required"
                  />
                  <v-switch
                    v-model="configs.ollama.enabled"
                    label="Enable Ollama integration"
                    color="primary"
                  />
                </v-card>
              </v-col>

              <!-- Whisper Configuration -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">Whisper (Local)</v-card-title>
                  <v-text-field
                    v-model="configs.whisper.host"
                    label="Host URL"
                    placeholder="http://localhost:9000"
                    persistent-hint
                    hint="Local Whisper transcription endpoint"
                  />
                  <v-text-field
                    v-model="configs.whisper.endpoint"
                    label="Transcription Endpoint"
                    placeholder="/v1/audio/transcriptions"
                  />
                  <v-switch
                    v-model="configs.whisper.enabled"
                    label="Enable Whisper transcription"
                    color="primary"
                  />
                </v-card>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- Cloud AI Services -->
        <v-expansion-panel value="cloud-ai">
          <v-expansion-panel-title>
            <v-icon left class="mr-3">mdi-cloud-braces</v-icon>
            Cloud AI Services
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row>
              <!-- OpenAI -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">OpenAI (ChatGPT)</v-card-title>
                  <v-text-field
                    v-model="configs.openai.apiKey"
                    label="API Key"
                    type="password"
                    placeholder="sk-..."
                    persistent-hint
                    hint="Your OpenAI API key"
                  />
                  <v-text-field
                    v-model="configs.openai.organization"
                    label="Organization ID (optional)"
                    placeholder="org-..."
                  />
                  <v-switch
                    v-model="configs.openai.enabled"
                    label="Enable OpenAI integration"
                    color="primary"
                  />
                  <v-btn
                    v-if="configs.openai.apiKey"
                    color="primary"
                    variant="outlined"
                    size="small"
                    class="mt-2"
                    @click="testConnection('openai')"
                  >
                    <v-icon left>mdi-connection</v-icon>
                    Test Connection
                  </v-btn>
                </v-card>
              </v-col>

              <!-- Anthropic Claude -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">Anthropic (Claude)</v-card-title>
                  <v-text-field
                    v-model="configs.anthropic.apiKey"
                    label="API Key"
                    type="password"
                    placeholder="sk-ant-..."
                    persistent-hint
                    hint="Your Anthropic API key"
                  />
                  <v-switch
                    v-model="configs.anthropic.enabled"
                    label="Enable Claude integration"
                    color="primary"
                  />
                  <v-btn
                    v-if="configs.anthropic.apiKey"
                    color="primary"
                    variant="outlined"
                    size="small"
                    class="mt-2"
                    @click="testConnection('anthropic')"
                  >
                    <v-icon left>mdi-connection</v-icon>
                    Test Connection
                  </v-btn>
                </v-card>
              </v-col>

              <!-- Google Gemini -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">Google Gemini</v-card-title>
                  <v-text-field
                    v-model="configs.gemini.apiKey"
                    label="API Key"
                    type="password"
                    placeholder="AI..."
                    persistent-hint
                    hint="Your Google AI API key"
                  />
                  <v-switch
                    v-model="configs.gemini.enabled"
                    label="Enable Gemini integration"
                    color="primary"
                  />
                </v-card>
              </v-col>

              <!-- X/Grok -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">X (Grok)</v-card-title>
                  <v-text-field
                    v-model="configs.grok.apiKey"
                    label="API Key"
                    type="password"
                    placeholder="xai-..."
                    persistent-hint
                    hint="Your X AI API key"
                  />
                  <v-switch
                    v-model="configs.grok.enabled"
                    label="Enable Grok integration"
                    color="primary"
                  />
                </v-card>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- Google Services -->
        <v-expansion-panel value="google-services">
          <v-expansion-panel-title>
            <v-icon left class="mr-3">mdi-google</v-icon>
            Google Services
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row>
              <!-- Google Drive & Calendar -->
              <v-col cols="12">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">Google Drive & Calendar</v-card-title>
                  <v-text-field
                    v-model="configs.google.clientId"
                    label="Client ID"
                    placeholder="Your Google OAuth Client ID"
                    persistent-hint
                    hint="From Google Cloud Console"
                  />
                  <v-text-field
                    v-model="configs.google.clientSecret"
                    label="Client Secret"
                    type="password"
                    placeholder="Your Google OAuth Client Secret"
                  />
                  <v-textarea
                    v-model="configs.google.serviceAccount"
                    label="Service Account JSON (optional)"
                    placeholder="Paste service account JSON for server-to-server auth"
                    rows="4"
                    auto-grow
                  />
                  <v-switch
                    v-model="configs.google.driveEnabled"
                    label="Enable Google Drive integration"
                    color="primary"
                  />
                  <v-switch
                    v-model="configs.google.calendarEnabled"
                    label="Enable Google Calendar integration"
                    color="primary"
                  />
                  <v-btn
                    v-if="configs.google.clientId"
                    color="primary"
                    variant="outlined"
                    class="mt-2 mr-2"
                    @click="authorizeGoogle"
                  >
                    <v-icon left>mdi-account-check</v-icon>
                    Authorize Google Access
                  </v-btn>
                  <v-btn
                    v-if="configs.google.clientId"
                    color="secondary"
                    variant="outlined"
                    class="mt-2"
                    @click="testConnection('google')"
                  >
                    <v-icon left>mdi-connection</v-icon>
                    Test Connection
                  </v-btn>
                </v-card>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- Media & Content Services -->
        <v-expansion-panel value="media-services">
          <v-expansion-panel-title>
            <v-icon left class="mr-3">mdi-video-box</v-icon>
            Media & Content Services
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row>
              <!-- YouTube API -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">YouTube API</v-card-title>
                  <v-text-field
                    v-model="configs.youtube.apiKey"
                    label="API Key"
                    type="password"
                    placeholder="Your YouTube Data API key"
                    persistent-hint
                    hint="For video uploads and management"
                  />
                  <v-text-field
                    v-model="configs.youtube.clientId"
                    label="OAuth Client ID"
                    placeholder="Your OAuth 2.0 Client ID"
                  />
                  <v-switch
                    v-model="configs.youtube.enabled"
                    label="Enable YouTube integration"
                    color="primary"
                  />
                </v-card>
              </v-col>

              <!-- Vimeo API -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">Vimeo API</v-card-title>
                  <v-text-field
                    v-model="configs.vimeo.accessToken"
                    label="Access Token"
                    type="password"
                    placeholder="Your Vimeo access token"
                    persistent-hint
                    hint="For video hosting and management"
                  />
                  <v-switch
                    v-model="configs.vimeo.enabled"
                    label="Enable Vimeo integration"
                    color="primary"
                  />
                </v-card>
              </v-col>

              <!-- AWS S3 -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">AWS S3</v-card-title>
                  <v-text-field
                    v-model="configs.aws.accessKeyId"
                    label="Access Key ID"
                    placeholder="Your AWS Access Key ID"
                  />
                  <v-text-field
                    v-model="configs.aws.secretAccessKey"
                    label="Secret Access Key"
                    type="password"
                    placeholder="Your AWS Secret Access Key"
                  />
                  <v-text-field
                    v-model="configs.aws.region"
                    label="Region"
                    placeholder="us-east-1"
                  />
                  <v-text-field
                    v-model="configs.aws.bucket"
                    label="S3 Bucket Name"
                    placeholder="your-bucket-name"
                  />
                  <v-switch
                    v-model="configs.aws.enabled"
                    label="Enable AWS S3 integration"
                    color="primary"
                  />
                </v-card>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- Communication & Notifications -->
        <v-expansion-panel value="communication">
          <v-expansion-panel-title>
            <v-icon left class="mr-3">mdi-message-alert</v-icon>
            Communication & Notifications
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row>
              <!-- Slack -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">Slack</v-card-title>
                  <v-text-field
                    v-model="configs.slack.botToken"
                    label="Bot Token"
                    type="password"
                    placeholder="xoxb-..."
                    persistent-hint
                    hint="Your Slack bot token"
                  />
                  <v-text-field
                    v-model="configs.slack.webhookUrl"
                    label="Webhook URL (optional)"
                    placeholder="https://hooks.slack.com/services/..."
                  />
                  <v-switch
                    v-model="configs.slack.enabled"
                    label="Enable Slack integration"
                    color="primary"
                  />
                </v-card>
              </v-col>

              <!-- Discord -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">Discord</v-card-title>
                  <v-text-field
                    v-model="configs.discord.botToken"
                    label="Bot Token"
                    type="password"
                    placeholder="Your Discord bot token"
                  />
                  <v-text-field
                    v-model="configs.discord.webhookUrl"
                    label="Webhook URL (optional)"
                    placeholder="https://discord.com/api/webhooks/..."
                  />
                  <v-switch
                    v-model="configs.discord.enabled"
                    label="Enable Discord integration"
                    color="primary"
                  />
                </v-card>
              </v-col>

              <!-- Twilio -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">Twilio</v-card-title>
                  <v-text-field
                    v-model="configs.twilio.accountSid"
                    label="Account SID"
                    placeholder="AC..."
                    persistent-hint
                    hint="For SMS and voice notifications"
                  />
                  <v-text-field
                    v-model="configs.twilio.authToken"
                    label="Auth Token"
                    type="password"
                    placeholder="Your Twilio auth token"
                  />
                  <v-text-field
                    v-model="configs.twilio.phoneNumber"
                    label="From Phone Number"
                    placeholder="+1234567890"
                  />
                  <v-switch
                    v-model="configs.twilio.enabled"
                    label="Enable Twilio integration"
                    color="primary"
                  />
                </v-card>
              </v-col>

              <!-- Email Services -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">Email Services</v-card-title>
                  <v-select
                    v-model="configs.email.provider"
                    :items="emailProviders"
                    label="Email Provider"
                    item-title="name"
                    item-value="value"
                  />
                  <v-text-field
                    v-model="configs.email.apiKey"
                    label="API Key"
                    type="password"
                    placeholder="Your email service API key"
                  />
                  <v-text-field
                    v-model="configs.email.fromEmail"
                    label="From Email Address"
                    placeholder="noreply@yourapp.com"
                  />
                  <v-switch
                    v-model="configs.email.enabled"
                    label="Enable email notifications"
                    color="primary"
                  />
                </v-card>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>

        <!-- Development & Automation -->
        <v-expansion-panel value="development">
          <v-expansion-panel-title>
            <v-icon left class="mr-3">mdi-code-braces</v-icon>
            Development & Automation
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row>
              <!-- GitHub -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">GitHub</v-card-title>
                  <v-text-field
                    v-model="configs.github.accessToken"
                    label="Personal Access Token"
                    type="password"
                    placeholder="ghp_..."
                    persistent-hint
                    hint="For repository management"
                  />
                  <v-text-field
                    v-model="configs.github.organization"
                    label="Default Organization (optional)"
                    placeholder="your-org"
                  />
                  <v-switch
                    v-model="configs.github.enabled"
                    label="Enable GitHub integration"
                    color="primary"
                  />
                </v-card>
              </v-col>

              <!-- Webhooks -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">Webhooks</v-card-title>
                  <v-text-field
                    v-model="configs.webhooks.endpoint"
                    label="Webhook Endpoint"
                    placeholder="https://your-app.com/webhook"
                    persistent-hint
                    hint="For external integrations"
                  />
                  <v-text-field
                    v-model="configs.webhooks.secret"
                    label="Webhook Secret"
                    type="password"
                    placeholder="Secret for signing payloads"
                  />
                  <v-switch
                    v-model="configs.webhooks.enabled"
                    label="Enable webhooks"
                    color="primary"
                  />
                </v-card>
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>

      <!-- Save Button -->
      <v-row class="mt-6">
        <v-col class="text-center">
          <v-btn
            color="primary"
            @click="saveSettings"
            :loading="saving"
            size="large"
          >
            <v-icon left>mdi-content-save</v-icon>
            Save API Configuration
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'save'])

const configs = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const expandedPanels = ref([])
const saving = ref(false)

const emailProviders = [
  { name: 'SendGrid', value: 'sendgrid' },
  { name: 'Mailgun', value: 'mailgun' },
  { name: 'AWS SES', value: 'ses' },
  { name: 'Postmark', value: 'postmark' },
  { name: 'SparkPost', value: 'sparkpost' }
]

async function testConnection(service) {
  try {
    const response = await fetch(`/api/settings/test/${service}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(configs.value[service])
    })
    
    if (response.ok) {
      alert(`${service} connection successful!`)
    } else {
      throw new Error('Connection failed')
    }
  } catch (error) {
    console.error(`Error testing ${service} connection:`, error)
    alert(`Failed to connect to ${service}`)
  }
}

function authorizeGoogle() {
  // Google OAuth flow - would typically redirect to Google
  console.log('Starting Google OAuth flow...')
  // Implementation would involve redirecting to Google OAuth endpoint
}

async function saveSettings() {
  saving.value = true
  try {
    const response = await fetch('/api/settings/api-configs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(configs.value)
    })

    if (response.ok) {
      emit('save', configs.value)
      alert('API configuration saved successfully')
    } else {
      throw new Error('Failed to save configuration')
    }
  } catch (error) {
    console.error('Error saving API configuration:', error)
    alert('Failed to save API configuration')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.v-expansion-panel-title {
  font-weight: 500;
}

.v-card--outlined {
  border: 1px solid rgba(0, 0, 0, 0.12);
}
</style>