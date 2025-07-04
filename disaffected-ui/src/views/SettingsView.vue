<template>
  <v-container fluid class="pa-4">
    <v-row>
      <v-col>
        <h2 class="text-h4 font-weight-bold mb-6">Settings</h2>
      </v-col>
    </v-row>

    <!-- Settings Tabs -->
    <v-row>
      <v-col>
        <v-tabs v-model="activeTab" color="primary" class="mb-4">
          <v-tab value="colors">Color Configuration</v-tab>
          <v-tab value="api">API Access</v-tab>
          <v-tab value="interface">Interface</v-tab>
          <v-tab value="rundown">Rundown</v-tab>
          <v-tab value="system">System</v-tab>
        </v-tabs>

        <v-tabs-window v-model="activeTab">
          <!-- Color Configuration Tab -->
          <v-tabs-window-item value="colors">
            <v-card class="pa-4">
              <v-card-title class="text-h6 mb-4">
                <v-icon left>mdi-palette</v-icon>
                Color Configuration
              </v-card-title>
              <v-card-text>
                <p class="mb-4 text-body-2">
                  Configure colors for rundown items and interface elements. 
                  Changes are applied immediately and saved automatically.
                </p>
                <ColorSelector />
              </v-card-text>
            </v-card>
          </v-tabs-window-item>

          <!-- API Access Tab -->
          <v-tabs-window-item value="api">
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
                              v-model="apiConfigs.ollama.host"
                              label="Host URL"
                              placeholder="http://localhost:11434"
                              persistent-hint
                              hint="Local Ollama instance endpoint"
                            />
                            <v-text-field
                              v-model="apiConfigs.ollama.apiKey"
                              label="API Key (optional)"
                              type="password"
                              placeholder="Enter API key if required"
                            />
                            <v-switch
                              v-model="apiConfigs.ollama.enabled"
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
                              v-model="apiConfigs.whisper.host"
                              label="Host URL"
                              placeholder="http://localhost:9000"
                              persistent-hint
                              hint="Local Whisper transcription endpoint"
                            />
                            <v-text-field
                              v-model="apiConfigs.whisper.endpoint"
                              label="Transcription Endpoint"
                              placeholder="/v1/audio/transcriptions"
                            />
                            <v-switch
                              v-model="apiConfigs.whisper.enabled"
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
                              v-model="apiConfigs.openai.apiKey"
                              label="API Key"
                              type="password"
                              placeholder="sk-..."
                              persistent-hint
                              hint="Your OpenAI API key"
                            />
                            <v-text-field
                              v-model="apiConfigs.openai.organization"
                              label="Organization ID (optional)"
                              placeholder="org-..."
                            />
                            <v-switch
                              v-model="apiConfigs.openai.enabled"
                              label="Enable OpenAI integration"
                              color="primary"
                            />
                            <v-btn
                              v-if="apiConfigs.openai.apiKey"
                              color="primary"
                              variant="outlined"
                              size="small"
                              class="mt-2"
                              @click="testApiConnection('openai')"
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
                              v-model="apiConfigs.anthropic.apiKey"
                              label="API Key"
                              type="password"
                              placeholder="sk-ant-..."
                              persistent-hint
                              hint="Your Anthropic API key"
                            />
                            <v-switch
                              v-model="apiConfigs.anthropic.enabled"
                              label="Enable Claude integration"
                              color="primary"
                            />
                            <v-btn
                              v-if="apiConfigs.anthropic.apiKey"
                              color="primary"
                              variant="outlined"
                              size="small"
                              class="mt-2"
                              @click="testApiConnection('anthropic')"
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
                              v-model="apiConfigs.gemini.apiKey"
                              label="API Key"
                              type="password"
                              placeholder="AI..."
                              persistent-hint
                              hint="Your Google AI API key"
                            />
                            <v-switch
                              v-model="apiConfigs.gemini.enabled"
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
                              v-model="apiConfigs.grok.apiKey"
                              label="API Key"
                              type="password"
                              placeholder="xai-..."
                              persistent-hint
                              hint="Your X AI API key"
                            />
                            <v-switch
                              v-model="apiConfigs.grok.enabled"
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
                              v-model="apiConfigs.google.clientId"
                              label="Client ID"
                              placeholder="Your Google OAuth Client ID"
                              persistent-hint
                              hint="From Google Cloud Console"
                            />
                            <v-text-field
                              v-model="apiConfigs.google.clientSecret"
                              label="Client Secret"
                              type="password"
                              placeholder="Your Google OAuth Client Secret"
                            />
                            <v-textarea
                              v-model="apiConfigs.google.serviceAccount"
                              label="Service Account JSON (optional)"
                              placeholder="Paste service account JSON for server-to-server auth"
                              rows="4"
                              auto-grow
                            />
                            <v-switch
                              v-model="apiConfigs.google.driveEnabled"
                              label="Enable Google Drive integration"
                              color="primary"
                            />
                            <v-switch
                              v-model="apiConfigs.google.calendarEnabled"
                              label="Enable Google Calendar integration"
                              color="primary"
                            />
                            <v-btn
                              v-if="apiConfigs.google.clientId"
                              color="primary"
                              variant="outlined"
                              class="mt-2 mr-2"
                              @click="authorizeGoogle"
                            >
                              <v-icon left>mdi-account-check</v-icon>
                              Authorize Google Access
                            </v-btn>
                            <v-btn
                              v-if="apiConfigs.google.clientId"
                              color="secondary"
                              variant="outlined"
                              class="mt-2"
                              @click="testApiConnection('google')"
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
                              v-model="apiConfigs.youtube.apiKey"
                              label="API Key"
                              type="password"
                              placeholder="Your YouTube Data API key"
                              persistent-hint
                              hint="For video uploads and management"
                            />
                            <v-text-field
                              v-model="apiConfigs.youtube.clientId"
                              label="OAuth Client ID"
                              placeholder="Your OAuth 2.0 Client ID"
                            />
                            <v-switch
                              v-model="apiConfigs.youtube.enabled"
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
                              v-model="apiConfigs.vimeo.accessToken"
                              label="Access Token"
                              type="password"
                              placeholder="Your Vimeo access token"
                              persistent-hint
                              hint="For video hosting and management"
                            />
                            <v-switch
                              v-model="apiConfigs.vimeo.enabled"
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
                              v-model="apiConfigs.aws.accessKeyId"
                              label="Access Key ID"
                              placeholder="Your AWS Access Key ID"
                            />
                            <v-text-field
                              v-model="apiConfigs.aws.secretAccessKey"
                              label="Secret Access Key"
                              type="password"
                              placeholder="Your AWS Secret Access Key"
                            />
                            <v-text-field
                              v-model="apiConfigs.aws.region"
                              label="Region"
                              placeholder="us-east-1"
                            />
                            <v-text-field
                              v-model="apiConfigs.aws.bucket"
                              label="S3 Bucket Name"
                              placeholder="your-bucket-name"
                            />
                            <v-switch
                              v-model="apiConfigs.aws.enabled"
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
                              v-model="apiConfigs.slack.botToken"
                              label="Bot Token"
                              type="password"
                              placeholder="xoxb-..."
                              persistent-hint
                              hint="Your Slack bot token"
                            />
                            <v-text-field
                              v-model="apiConfigs.slack.webhookUrl"
                              label="Webhook URL (optional)"
                              placeholder="https://hooks.slack.com/services/..."
                            />
                            <v-switch
                              v-model="apiConfigs.slack.enabled"
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
                              v-model="apiConfigs.discord.botToken"
                              label="Bot Token"
                              type="password"
                              placeholder="Your Discord bot token"
                            />
                            <v-text-field
                              v-model="apiConfigs.discord.webhookUrl"
                              label="Webhook URL (optional)"
                              placeholder="https://discord.com/api/webhooks/..."
                            />
                            <v-switch
                              v-model="apiConfigs.discord.enabled"
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
                              v-model="apiConfigs.twilio.accountSid"
                              label="Account SID"
                              placeholder="AC..."
                              persistent-hint
                              hint="For SMS and voice notifications"
                            />
                            <v-text-field
                              v-model="apiConfigs.twilio.authToken"
                              label="Auth Token"
                              type="password"
                              placeholder="Your Twilio auth token"
                            />
                            <v-text-field
                              v-model="apiConfigs.twilio.phoneNumber"
                              label="From Phone Number"
                              placeholder="+1234567890"
                            />
                            <v-switch
                              v-model="apiConfigs.twilio.enabled"
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
                              v-model="apiConfigs.email.provider"
                              :items="emailProviders"
                              label="Email Provider"
                              item-title="name"
                              item-value="value"
                            />
                            <v-text-field
                              v-model="apiConfigs.email.apiKey"
                              label="API Key"
                              type="password"
                              placeholder="Your email service API key"
                            />
                            <v-text-field
                              v-model="apiConfigs.email.fromEmail"
                              label="From Email Address"
                              placeholder="noreply@yourapp.com"
                            />
                            <v-switch
                              v-model="apiConfigs.email.enabled"
                              label="Enable email notifications"
                              color="primary"
                            />
                          </v-card>
                        </v-col>
                      </v-row>
                    </v-expansion-panel-text>
                  </v-expansion-panel>

                  <!-- Cloud Storage & Productivity -->
                  <v-expansion-panel value="cloud-storage">
                    <v-expansion-panel-title>
                      <v-icon left class="mr-3">mdi-cloud-upload</v-icon>
                      Cloud Storage & Productivity
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-row>
                        <!-- Note: Google Services are in their own section above -->
                        <v-col cols="12">
                          <v-alert type="info" variant="tonal">
                            Google Drive and Calendar integration is configured in the Google Services section above.
                            Additional cloud storage services can be added here as needed.
                          </v-alert>
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
                              v-model="apiConfigs.github.accessToken"
                              label="Personal Access Token"
                              type="password"
                              placeholder="ghp_..."
                              persistent-hint
                              hint="For repository management"
                            />
                            <v-text-field
                              v-model="apiConfigs.github.organization"
                              label="Default Organization (optional)"
                              placeholder="your-org"
                            />
                            <v-switch
                              v-model="apiConfigs.github.enabled"
                              label="Enable GitHub integration"
                              color="primary"
                            />
                          </v-card>
                        </v-col>

                        <!-- GitLab -->
                        <v-col cols="12" md="6">
                          <v-card variant="outlined" class="pa-4">
                            <v-card-title class="text-subtitle-1">GitLab</v-card-title>
                            <v-text-field
                              v-model="apiConfigs.gitlab.accessToken"
                              label="Personal Access Token"
                              type="password"
                              placeholder="glpat-..."
                            />
                            <v-text-field
                              v-model="apiConfigs.gitlab.baseUrl"
                              label="GitLab Instance URL"
                              placeholder="https://gitlab.com"
                            />
                            <v-switch
                              v-model="apiConfigs.gitlab.enabled"
                              label="Enable GitLab integration"
                              color="primary"
                            />
                          </v-card>
                        </v-col>

                        <!-- Zapier -->
                        <v-col cols="12" md="6">
                          <v-card variant="outlined" class="pa-4">
                            <v-card-title class="text-subtitle-1">Zapier</v-card-title>
                            <v-text-field
                              v-model="apiConfigs.zapier.webhookUrl"
                              label="Webhook URL"
                              placeholder="https://hooks.zapier.com/hooks/catch/..."
                              persistent-hint
                              hint="For workflow automation"
                            />
                            <v-switch
                              v-model="apiConfigs.zapier.enabled"
                              label="Enable Zapier integration"
                              color="primary"
                            />
                          </v-card>
                        </v-col>

                        <!-- Webhooks -->
                        <v-col cols="12" md="6">
                          <v-card variant="outlined" class="pa-4">
                            <v-card-title class="text-subtitle-1">Custom Webhooks</v-card-title>
                            <div v-for="(webhook, index) in apiConfigs.webhooks" :key="index" class="mb-3 pa-2 border rounded">
                              <v-row>
                                <v-col cols="8">
                                  <v-text-field
                                    v-model="webhook.url"
                                    label="Webhook URL"
                                    placeholder="https://your-endpoint.com/webhook"
                                    dense
                                  />
                                </v-col>
                                <v-col cols="3">
                                  <v-select
                                    v-model="webhook.event"
                                    :items="webhookEvents"
                                    label="Event"
                                    dense
                                  />
                                </v-col>
                                <v-col cols="1" class="d-flex align-center">
                                  <v-btn
                                    color="error"
                                    variant="text"
                                    size="small"
                                    @click="removeWebhook(index)"
                                  >
                                    <v-icon>mdi-delete</v-icon>
                                  </v-btn>
                                </v-col>
                              </v-row>
                            </div>
                            <v-btn
                              color="primary"
                              variant="outlined"
                              size="small"
                              @click="addWebhook"
                            >
                              <v-icon left>mdi-plus</v-icon>
                              Add Webhook
                            </v-btn>
                          </v-card>
                        </v-col>
                      </v-row>
                    </v-expansion-panel-text>
                  </v-expansion-panel>

                  <!-- Specialized AI Services -->
                  <v-expansion-panel value="specialized-ai">
                    <v-expansion-panel-title>
                      <v-icon left class="mr-3">mdi-robot</v-icon>
                      Specialized AI Services
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-row>
                        <!-- Stability AI -->
                        <v-col cols="12" md="6">
                          <v-card variant="outlined" class="pa-4">
                            <v-card-title class="text-subtitle-1">Stability AI</v-card-title>
                            <v-text-field
                              v-model="apiConfigs.stabilityAi.apiKey"
                              label="API Key"
                              type="password"
                              placeholder="sk-..."
                              persistent-hint
                              hint="For image generation and editing"
                            />
                            <v-switch
                              v-model="apiConfigs.stabilityAi.enabled"
                              label="Enable Stability AI integration"
                              color="primary"
                            />
                          </v-card>
                        </v-col>

                        <!-- ElevenLabs -->
                        <v-col cols="12" md="6">
                          <v-card variant="outlined" class="pa-4">
                            <v-card-title class="text-subtitle-1">ElevenLabs</v-card-title>
                            <v-text-field
                              v-model="apiConfigs.elevenLabs.apiKey"
                              label="API Key"
                              type="password"
                              placeholder="Your ElevenLabs API key"
                              persistent-hint
                              hint="For AI voice synthesis"
                            />
                            <v-switch
                              v-model="apiConfigs.elevenLabs.enabled"
                              label="Enable ElevenLabs integration"
                              color="primary"
                            />
                          </v-card>
                        </v-col>

                        <!-- Deepgram - Removed for research -->
                        <!-- <v-col cols="12" md="6">
                          <v-card variant="outlined" class="pa-4">
                            <v-card-title class="text-subtitle-1">Deepgram</v-card-title>
                            <p class="text-caption mb-2">Advanced speech-to-text transcription</p>
                            <v-alert type="info" variant="tonal" class="mb-3">
                              Research this service before enabling
                            </v-alert>
                          </v-card>
                        </v-col> -->
                      </v-row>
                    </v-expansion-panel-text>
                  </v-expansion-panel>

                  <!-- Custom & Generic APIs -->
                  <v-expansion-panel value="custom-apis">
                    <v-expansion-panel-title>
                      <v-icon left class="mr-3">mdi-cog</v-icon>
                      Custom & Generic APIs
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-row>
                        <v-col cols="12">
                          <v-card variant="outlined" class="pa-4">
                            <v-card-title class="text-subtitle-1">Generic API Endpoints</v-card-title>
                            <p class="text-body-2 mb-4">Configure custom API endpoints for specialized services</p>
                            
                            <div v-for="(endpoint, index) in apiConfigs.customEndpoints" :key="index" class="mb-4 pa-3 border rounded">
                              <v-row>
                                <v-col cols="12" md="3">
                                  <v-text-field
                                    v-model="endpoint.name"
                                    label="Service Name"
                                    placeholder="My Custom API"
                                  />
                                </v-col>
                                <v-col cols="12" md="4">
                                  <v-text-field
                                    v-model="endpoint.url"
                                    label="Base URL"
                                    placeholder="https://api.example.com"
                                  />
                                </v-col>
                                <v-col cols="12" md="3">
                                  <v-text-field
                                    v-model="endpoint.apiKey"
                                    label="API Key"
                                    type="password"
                                    placeholder="API Key"
                                  />
                                </v-col>
                                <v-col cols="12" md="2" class="d-flex align-center">
                                  <v-btn
                                    color="error"
                                    variant="outlined"
                                    size="small"
                                    @click="removeCustomEndpoint(index)"
                                  >
                                    <v-icon>mdi-delete</v-icon>
                                  </v-btn>
                                </v-col>
                              </v-row>
                              <v-row>
                                <v-col cols="12">
                                  <v-textarea
                                    v-model="endpoint.customPrompt"
                                    label="Custom Prompt Template (optional)"
                                    placeholder="Custom prompt template for this service..."
                                    rows="2"
                                    auto-grow
                                  />
                                </v-col>
                              </v-row>
                            </div>
                            
                            <v-btn
                              color="primary"
                              variant="outlined"
                              @click="addCustomEndpoint"
                            >
                              <v-icon left>mdi-plus</v-icon>
                              Add Custom Endpoint
                            </v-btn>
                          </v-card>
                        </v-col>
                      </v-row>
                    </v-expansion-panel-text>
                  </v-expansion-panel>

                </v-expansion-panels>

                <!-- Save Button -->
                <v-row class="mt-4">
                  <v-col class="text-center">
                    <v-btn
                      color="primary"
                      size="large"
                      @click="saveApiConfigs"
                      :loading="savingApiConfigs"
                    >
                      <v-icon left>mdi-content-save</v-icon>
                      Save API Configuration
                    </v-btn>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-tabs-window-item>

          <!-- Interface Tab -->
          <v-tabs-window-item value="interface">
            <v-card class="pa-4">
              <v-card-title class="text-h6 mb-4">
                <v-icon left>mdi-monitor</v-icon>
                Interface Settings
              </v-card-title>
              <v-card-text>
                <p class="text-body-2 mb-4">Interface configuration options will be added here.</p>
                <!-- Future interface settings will go here -->
                <v-alert type="info" variant="tonal">
                  Interface settings coming soon...
                </v-alert>
              </v-card-text>
            </v-card>
          </v-tabs-window-item>

          <!-- Rundown Tab -->
          <v-tabs-window-item value="rundown">
            <v-card class="pa-4">
              <v-card-title class="text-h6 mb-4">
                <v-icon left>mdi-format-list-bulleted</v-icon>
                Rundown Settings
              </v-card-title>
              <v-card-text>
                <p class="text-body-2 mb-4">Configure rundown behavior and defaults.</p>
                <!-- Future rundown settings will go here -->
                <v-alert type="info" variant="tonal">
                  Rundown settings coming soon...
                </v-alert>
              </v-card-text>
            </v-card>
          </v-tabs-window-item>

          <!-- System Tab -->
          <v-tabs-window-item value="system">
            <v-card class="pa-4">
              <v-card-title class="text-h6 mb-4">
                <v-icon left>mdi-cog</v-icon>
                System Settings
              </v-card-title>
              <v-card-text>
                <p class="text-body-2 mb-4">System-wide configuration options.</p>
                <!-- Future system settings will go here -->
                <v-alert type="info" variant="tonal">
                  System settings coming soon...
                </v-alert>
              </v-card-text>
            </v-card>
          </v-tabs-window-item>
        </v-tabs-window>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import ColorSelector from '@/components/ColorSelector.vue'

export default {
  name: 'SettingsView',
  components: {
    ColorSelector
  },
  data() {
    return {
      activeTab: 'colors', // Start with the color configuration tab
      expandedPanels: [],
      apiConfigs: {
        ollama: {
          host: '',
          apiKey: '',
          enabled: false
        },
        whisper: {
          host: '',
          endpoint: '',
          enabled: false
        },
        openai: {
          apiKey: '',
          organization: '',
          enabled: false
        },
        anthropic: {
          apiKey: '',
          enabled: false
        },
        gemini: {
          apiKey: '',
          enabled: false
        },
        grok: {
          apiKey: '',
          enabled: false
        },
        google: {
          clientId: '',
          clientSecret: '',
          serviceAccount: '',
          driveEnabled: false,
          calendarEnabled: false
        },
        youtube: {
          apiKey: '',
          clientId: '',
          enabled: false
        },
        vimeo: {
          accessToken: '',
          enabled: false
        },
        aws: {
          accessKeyId: '',
          secretAccessKey: '',
          region: '',
          bucket: '',
          enabled: false
        },
        slack: {
          botToken: '',
          webhookUrl: '',
          enabled: false
        },
        discord: {
          botToken: '',
          webhookUrl: '',
          enabled: false
        },
        twilio: {
          accountSid: '',
          authToken: '',
          phoneNumber: '',
          enabled: false
        },
        email: {
          provider: '',
          apiKey: '',
          fromEmail: '',
          enabled: false
        },
        github: {
          accessToken: '',
          organization: '',
          enabled: false
        },
        gitlab: {
          accessToken: '',
          baseUrl: 'https://gitlab.com',
          enabled: false
        },
        zapier: {
          webhookUrl: '',
          enabled: false
        },
        stabilityAi: {
          apiKey: '',
          enabled: false
        },
        elevenLabs: {
          apiKey: '',
          enabled: false
        },
        webhooks: [],
        customEndpoints: []
      },
      savingApiConfigs: false,
      emailProviders: [
        { name: 'SendGrid', value: 'sendgrid' },
        { name: 'Mailgun', value: 'mailgun' },
        { name: 'AWS SES', value: 'ses' },
        { name: 'SMTP', value: 'smtp' },
        { name: 'Postmark', value: 'postmark' }
      ],
      webhookEvents: [
        'rundown.created',
        'rundown.updated',
        'rundown.deleted',
        'item.created',
        'item.updated',
        'item.deleted',
        'export.completed',
        'system.error'
      ]
    }
  },
  methods: {
    authorizeGoogle() {
      // Google authorization logic - opens OAuth flow
      console.log('Starting Google OAuth authorization...')
      // Implementation would redirect to Google OAuth
    },
    addCustomEndpoint() {
      this.apiConfigs.customEndpoints.push({
        name: '',
        url: '',
        apiKey: '',
        customPrompt: ''
      })
    },
    removeCustomEndpoint(index) {
      this.apiConfigs.customEndpoints.splice(index, 1)
    },
    addWebhook() {
      this.apiConfigs.webhooks.push({
        url: '',
        event: ''
      })
    },
    removeWebhook(index) {
      this.apiConfigs.webhooks.splice(index, 1)
    },
    async saveApiConfigs() {
      this.savingApiConfigs = true
      try {
        // Convert Vue data structure to backend structure
        const backendConfig = {
          preproduction: {
            ai_services: {
              ollama: this.apiConfigs.ollama,
              whisper: this.apiConfigs.whisper,
              openai: this.apiConfigs.openai,
              anthropic: this.apiConfigs.anthropic,
              gemini: this.apiConfigs.gemini,
              grok: this.apiConfigs.grok,
              stabilityAi: this.apiConfigs.stabilityAi,
              elevenLabs: this.apiConfigs.elevenLabs
            },
            storage: {
              google: this.apiConfigs.google,
              aws: this.apiConfigs.aws
            },
            communication: {
              slack: this.apiConfigs.slack,
              discord: this.apiConfigs.discord,
              twilio: this.apiConfigs.twilio,
              email: this.apiConfigs.email
            }
          },
          promotion: {
            social_media: {
              youtube: this.apiConfigs.youtube,
              vimeo: this.apiConfigs.vimeo
            }
          },
          development: {
            github: this.apiConfigs.github,
            gitlab: this.apiConfigs.gitlab,
            zapier: this.apiConfigs.zapier,
            webhooks: this.apiConfigs.webhooks,
            customEndpoints: this.apiConfigs.customEndpoints
          }
        }

        const response = await fetch('/api/settings/api-configs', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.$store.state.auth.token}`
          },
          body: JSON.stringify({ config: backendConfig })
        })
        
        const result = await response.json()
        
        if (response.ok && result.success) {
          this.$toast.success('API configurations saved successfully!')
        } else {
          throw new Error(result.message || 'Failed to save configurations')
        }
      } catch (error) {
        console.error('Error saving API configs:', error)
        this.$toast.error('Failed to save API configurations. Please try again.')
      } finally {
        this.savingApiConfigs = false
      }
    },
    async loadApiConfigs() {
      try {
        const response = await fetch('/api/settings/api-configs', {
          headers: {
            'Authorization': `Bearer ${this.$store.state.auth.token}`
          }
        })
        
        if (response.ok) {
          const result = await response.json()
          if (result.success && result.data) {
            // Convert backend structure to Vue data structure
            const config = result.data
            
            // Pre-production services
            if (config.preproduction?.ai_services) {
              Object.assign(this.apiConfigs, {
                ollama: config.preproduction.ai_services.ollama || this.apiConfigs.ollama,
                whisper: config.preproduction.ai_services.whisper || this.apiConfigs.whisper,
                openai: config.preproduction.ai_services.openai || this.apiConfigs.openai,
                anthropic: config.preproduction.ai_services.anthropic || this.apiConfigs.anthropic,
                gemini: config.preproduction.ai_services.gemini || this.apiConfigs.gemini,
                grok: config.preproduction.ai_services.grok || this.apiConfigs.grok,
                stabilityAi: config.preproduction.ai_services.stabilityAi || this.apiConfigs.stabilityAi,
                elevenLabs: config.preproduction.ai_services.elevenLabs || this.apiConfigs.elevenLabs
              })
            }
            
            if (config.preproduction?.storage) {
              Object.assign(this.apiConfigs, {
                google: config.preproduction.storage.google || this.apiConfigs.google,
                aws: config.preproduction.storage.aws || this.apiConfigs.aws
              })
            }
            
            if (config.preproduction?.communication) {
              Object.assign(this.apiConfigs, {
                slack: config.preproduction.communication.slack || this.apiConfigs.slack,
                discord: config.preproduction.communication.discord || this.apiConfigs.discord,
                twilio: config.preproduction.communication.twilio || this.apiConfigs.twilio,
                email: config.preproduction.communication.email || this.apiConfigs.email
              })
            }
            
            // Promotion services
            if (config.promotion?.social_media) {
              Object.assign(this.apiConfigs, {
                youtube: config.promotion.social_media.youtube || this.apiConfigs.youtube,
                vimeo: config.promotion.social_media.vimeo || this.apiConfigs.vimeo
              })
            }
            
            // Development services
            if (config.development) {
              Object.assign(this.apiConfigs, {
                github: config.development.github || this.apiConfigs.github,
                gitlab: config.development.gitlab || this.apiConfigs.gitlab,
                zapier: config.development.zapier || this.apiConfigs.zapier,
                webhooks: config.development.webhooks || this.apiConfigs.webhooks,
                customEndpoints: config.development.customEndpoints || this.apiConfigs.customEndpoints
              })
            }
          }
        }
      } catch (error) {
        console.error('Error loading API configs:', error)
        // Continue with default empty configs
      }
    },
    async testApiConnection(service) {
      try {
        const response = await fetch(`/api/settings/test/${service}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${this.$store.state.auth.token}`
          }
        })
        
        const result = await response.json()
        
        if (response.ok && result.success) {
          this.$toast.success(`${service} connection successful!`)
          return true
        } else {
          this.$toast.error(result.message || `${service} connection failed`)
          return false
        }
      } catch (error) {
        console.error(`Error testing ${service}:`, error)
        this.$toast.error(`Failed to test ${service} connection`)
        return false
      }
    }
  },
  async mounted() {
    // Load existing API configurations when component mounts
    await this.loadApiConfigs()
  }
}
</script>

<style scoped>
.v-tabs {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.v-card {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}
</style>