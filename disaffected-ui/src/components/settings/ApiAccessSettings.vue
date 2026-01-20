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

      <!-- Services & API Section -->
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

                  <!-- Service Account Authentication (Recommended) -->
                  <v-alert type="info" variant="tonal" class="mb-4">
                    <strong>Service Account (Recommended):</strong> For server-to-server access, just paste the Service Account JSON below. No Client ID or Secret needed.
                  </v-alert>

                  <v-textarea
                    v-model="configs.google.serviceAccount"
                    label="Service Account JSON"
                    placeholder="Paste your service account JSON credentials here"
                    rows="6"
                    auto-grow
                    persistent-hint
                    hint="Get this from Google Cloud Console > IAM & Admin > Service Accounts"
                  />

                  <v-divider class="my-4"></v-divider>

                  <!-- Drive Configuration -->
                  <v-text-field
                    v-model="configs.google.sharedDriveId"
                    label="Shared Drive ID (Optional)"
                    placeholder="0AF_fwnbR8F-9Uk9PVA"
                    persistent-hint
                    hint="Restrict operations to specific Shared Drive"
                  />

                  <v-text-field
                    v-model="configs.google.episodesFolderId"
                    label="Episodes Root Folder ID"
                    placeholder="1AbC_2DeFgHiJkLmN3oPqRsTuV4wXyZ5"
                    persistent-hint
                    hint="Paste folder ID or full Google Drive URL - ID will be extracted automatically"
                    @blur="extractFolderId('episodesFolderId')"
                  />

                  <v-alert type="info" variant="tonal" class="mt-2 mb-4">
                    <div class="text-body-2">
                      <strong>How to find Folder ID:</strong>
                      <ol class="mt-2">
                        <li>Open the episodes folder in Google Drive</li>
                        <li>Copy the folder ID from the URL: <code>drive.google.com/drive/folders/<strong>FOLDER_ID_HERE</strong></code></li>
                        <li>Paste the ID above</li>
                      </ol>
                      <div class="mt-2">
                        <strong>Important:</strong> This folder should contain episode directories (0244, 0243, etc.) just like your local Syncthing storage.
                      </div>
                    </div>
                  </v-alert>

                  <v-combobox
                    v-model="configs.google.allowedFolders"
                    label="Allowed Folders (Optional)"
                    placeholder="Add folder names to whitelist"
                    multiple
                    chips
                    clearable
                    persistent-hint
                    hint="Leave empty for full access, or specify folder names to restrict operations"
                  />

                  <v-combobox
                    v-model="configs.google.excludedFolders"
                    label="Excluded Folders"
                    placeholder="Add folder names to blacklist"
                    multiple
                    chips
                    clearable
                    persistent-hint
                    hint="Folders to exclude from all operations (e.g., temporary-files, logs, sync-*, .blackmagicsync-v2)"
                    class="mt-4"
                  />

                  <v-divider class="my-4"></v-divider>

                  <!-- OAuth Credentials (Optional) -->
                  <v-expansion-panels variant="accordion" class="mb-4">
                    <v-expansion-panel>
                      <v-expansion-panel-title>
                        <span class="text-caption">OAuth Credentials (Optional - for user login flows)</span>
                      </v-expansion-panel-title>
                      <v-expansion-panel-text>
                        <v-text-field
                          v-model="configs.google.clientId"
                          label="Client ID (Optional)"
                          placeholder="Your Google OAuth Client ID"
                          persistent-hint
                          hint="Only needed for OAuth user authentication"
                        />
                        <v-text-field
                          v-model="configs.google.clientSecret"
                          label="Client Secret (Optional)"
                          type="password"
                          placeholder="Your Google OAuth Client Secret"
                        />
                      </v-expansion-panel-text>
                    </v-expansion-panel>
                  </v-expansion-panels>

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
                    v-if="configs.google.serviceAccount"
                    color="primary"
                    variant="outlined"
                    class="mt-2"
                    @click="testConnection('google')"
                  >
                    <v-icon left>mdi-connection</v-icon>
                    Test Drive Connection
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

              <!-- X/Twitter API -->
              <v-col cols="12">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">
                    <v-icon left size="small">mdi-twitter</v-icon>
                    X/Twitter API
                  </v-card-title>
                  <v-alert type="info" variant="tonal" density="compact" class="mb-3">
                    For rich tweet previews, social media archival, and posting tweets
                  </v-alert>

                  <!-- Server-Level Access (Bearer Token) -->
                  <v-card variant="tonal" class="mb-4 pa-3">
                    <div class="text-subtitle-2 mb-2">
                      <v-icon size="small" class="mr-1">mdi-server</v-icon>
                      Server-Level Access (Read Public Tweets)
                    </div>
                    <v-text-field
                      v-model="configs.twitter.bearerToken"
                      label="Bearer Token"
                      type="password"
                      placeholder="Your Twitter API Bearer Token"
                      persistent-hint
                      hint="For reading public tweets and scratchpad link previews"
                      density="compact"
                    />
                    <v-text-field
                      v-model="configs.twitter.apiKey"
                      label="API Key (optional)"
                      type="text"
                      placeholder="Your Twitter API Key"
                      density="compact"
                      class="mt-2"
                      autocomplete="off"
                    />
                    <v-text-field
                      v-model="configs.twitter.apiSecret"
                      label="API Secret (optional)"
                      type="text"
                      placeholder="Your Twitter API Secret"
                      density="compact"
                      class="mt-2"
                      autocomplete="off"
                    />
                    <v-btn
                      v-if="configs.twitter.bearerToken"
                      color="primary"
                      variant="outlined"
                      size="small"
                      class="mt-2"
                      @click="testConnection('twitter')"
                    >
                      <v-icon left>mdi-connection</v-icon>
                      Test Connection
                    </v-btn>
                  </v-card>

                  <!-- User-Level OAuth (Post Tweets, Manage Account) -->
                  <v-card variant="tonal" class="pa-3">
                    <div class="text-subtitle-2 mb-2">
                      <v-icon size="small" class="mr-1">mdi-account-circle</v-icon>
                      User-Level OAuth (Post Tweets & Manage Account)
                    </div>

                    <!-- Connection Status -->
                    <v-alert
                      v-if="twitterOAuthStatus.connected"
                      type="success"
                      variant="tonal"
                      density="compact"
                      class="mb-3"
                    >
                      <div class="d-flex align-center">
                        <v-avatar size="32" class="mr-3">
                          <v-img :src="twitterOAuthStatus.profileImage || 'https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png'" />
                        </v-avatar>
                        <div class="flex-grow-1">
                          <div class="font-weight-medium">{{ twitterOAuthStatus.name }}</div>
                          <div class="text-caption">@{{ twitterOAuthStatus.username }}</div>
                        </div>
                        <v-btn
                          size="small"
                          variant="text"
                          color="error"
                          @click="disconnectTwitterOAuth"
                        >
                          Disconnect
                        </v-btn>
                      </div>
                    </v-alert>

                    <!-- Connect Button -->
                    <v-btn
                      v-if="!twitterOAuthStatus.connected"
                      color="primary"
                      @click="initiateTwitterOAuth"
                      :loading="twitterOAuthLoading"
                      block
                      class="mb-3"
                    >
                      <v-icon left>mdi-twitter</v-icon>
                      Connect Twitter Account
                    </v-btn>

                    <!-- Manual OAuth Flow (Firewall-Friendly) -->
                    <v-expand-transition>
                      <v-card
                        v-if="showTwitterOAuthManual"
                        variant="outlined"
                        class="pa-3"
                      >
                        <v-alert type="info" density="compact" class="mb-3">
                          <strong>Step 1:</strong> Open this URL in your browser and authorize the app
                        </v-alert>
                        <v-text-field
                          :model-value="twitterAuthUrl"
                          label="Authorization URL"
                          readonly
                          density="compact"
                        >
                          <template v-slot:append>
                            <v-btn
                              icon="mdi-open-in-new"
                              size="small"
                              variant="text"
                              @click="openTwitterAuthUrl"
                            />
                            <v-btn
                              icon="mdi-content-copy"
                              size="small"
                              variant="text"
                              @click="copyToClipboard(twitterAuthUrl)"
                            />
                          </template>
                        </v-text-field>

                        <v-alert type="info" density="compact" class="mt-3 mb-3">
                          <strong>Step 2:</strong> After authorizing, copy the code shown and paste it below
                        </v-alert>
                        <v-text-field
                          v-model="twitterAuthCode"
                          label="Authorization Code"
                          placeholder="Paste the authorization code from Twitter"
                          density="compact"
                        />

                        <v-btn
                          color="primary"
                          @click="completeTwitterOAuth"
                          :disabled="!twitterAuthCode"
                          :loading="twitterOAuthLoading"
                          block
                          class="mt-2"
                        >
                          Complete Connection
                        </v-btn>

                        <v-btn
                          variant="text"
                          size="small"
                          @click="cancelTwitterOAuth"
                          block
                          class="mt-2"
                        >
                          Cancel
                        </v-btn>
                      </v-card>
                    </v-expand-transition>
                  </v-card>

                  <v-switch
                    v-model="configs.twitter.enabled"
                    label="Enable Twitter/X integration"
                    color="primary"
                    class="mt-3"
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

              <!-- Asterisk -->
              <v-col cols="12" md="6">
                <v-card variant="outlined" class="pa-4">
                  <v-card-title class="text-subtitle-1">Asterisk PBX</v-card-title>
                  <v-text-field
                    v-model="configs.asterisk.host"
                    label="Asterisk Host"
                    placeholder="192.168.1.100"
                    persistent-hint
                    hint="Asterisk server IP or hostname"
                  />
                  <v-text-field
                    v-model="configs.asterisk.amiPort"
                    label="AMI Port"
                    placeholder="5038"
                    persistent-hint
                    hint="Asterisk Manager Interface port"
                  />
                  <v-text-field
                    v-model="configs.asterisk.amiUsername"
                    label="AMI Username"
                    placeholder="admin"
                  />
                  <v-text-field
                    v-model="configs.asterisk.amiSecret"
                    label="AMI Secret"
                    type="password"
                    placeholder="Your AMI password"
                  />
                  <v-text-field
                    v-model="configs.asterisk.conferenceContext"
                    label="Conference Context"
                    placeholder="conferences"
                    persistent-hint
                    hint="Dialplan context for conferences"
                  />
                  <v-text-field
                    v-model="configs.asterisk.recordingsPath"
                    label="Recordings Path"
                    placeholder="/var/spool/asterisk/monitor"
                    persistent-hint
                    hint="Where Asterisk stores recordings"
                  />
                  <v-switch
                    v-model="configs.asterisk.enabled"
                    label="Enable Asterisk integration"
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

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['update:modelValue', 'save'])

const configs = computed({
  get: () => props.modelValue || {},
  set: (value) => emit('update:modelValue', value)
})

const expandedPanels = ref([])
const saving = ref(false)

// Snackbar state
const snackbar = ref({
  show: false,
  message: '',
  color: 'success',
  timeout: 5000
})

const showSnackbar = (message, color = 'success') => {
  snackbar.value.message = message
  snackbar.value.color = color
  snackbar.value.show = true
}

// Twitter OAuth state
const twitterOAuthStatus = ref({
  connected: false,
  username: '',
  name: '',
  profileImage: ''
})
const twitterOAuthLoading = ref(false)
const showTwitterOAuthManual = ref(false)
const twitterAuthUrl = ref('')
const twitterAuthCode = ref('')
const twitterAuthState = ref('') // OAuth state parameter

const emailProviders = [
  { name: 'SendGrid', value: 'sendgrid' },
  { name: 'Mailgun', value: 'mailgun' },
  { name: 'AWS SES', value: 'ses' },
  { name: 'Postmark', value: 'postmark' },
  { name: 'SparkPost', value: 'sparkpost' }
]

// Extract Google Drive folder ID from URL if user pastes full URL
function extractFolderId(fieldName) {
  const value = configs.value.google[fieldName]
  if (!value) return

  // Check if it looks like a URL
  if (value.includes('drive.google.com')) {
    // Extract ID from URL patterns:
    // https://drive.google.com/drive/folders/FOLDER_ID
    // https://drive.google.com/drive/folders/FOLDER_ID?usp=sharing
    const match = value.match(/folders\/([a-zA-Z0-9_-]+)/)
    if (match && match[1]) {
      configs.value.google[fieldName] = match[1]
    }
  }
}

async function testConnection(service) {
  try {
    // Special handling for Google Drive
    if (service === 'google') {
      const response = await fetch('/api/drive/test', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        showSnackbar(`${data.message} (${data.sample_files.length} files found)`, 'success')
      } else {
        const error = await response.json()
        throw new Error(error.detail || 'Connection failed')
      }
    } else {
      // Generic test for other services
      const response = await fetch(`/api/settings/test/${service}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
        },
        body: JSON.stringify(configs.value[service])
      })

      if (response.ok) {
        showSnackbar(`${service} connection successful!`, 'success')
      } else {
        throw new Error('Connection failed')
      }
    }
  } catch (error) {
    console.error(`Error testing ${service} connection:`, error)
    showSnackbar(`Failed to connect to ${service}: ${error.message}`, 'error')
  }
}

// Twitter OAuth functions
async function checkTwitterOAuthStatus() {
  try {
    const response = await fetch('/api/twitter/status', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
      }
    })

    if (response.ok) {
      const data = await response.json()
      twitterOAuthStatus.value = {
        connected: data.connected,
        username: data.username || '',
        name: data.name || '',
        profileImage: data.profile_image_url || ''
      }
    }
  } catch (error) {
    console.error('Error checking Twitter OAuth status:', error)
  }
}

async function initiateTwitterOAuth() {
  twitterOAuthLoading.value = true
  try {
    const response = await fetch('/api/twitter/auth/url', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
      }
    })

    if (response.ok) {
      const data = await response.json()
      twitterAuthUrl.value = data.auth_url
      twitterAuthState.value = data.state
      showTwitterOAuthManual.value = true
    } else {
      throw new Error('Failed to get authorization URL')
    }
  } catch (error) {
    console.error('Error initiating Twitter OAuth:', error)
    showSnackbar('Failed to initiate Twitter OAuth: ' + error.message, 'error')
  } finally {
    twitterOAuthLoading.value = false
  }
}

function openTwitterAuthUrl() {
  window.open(twitterAuthUrl.value, '_blank')
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    showSnackbar('Copied to clipboard!', 'success')
  }).catch(() => {
    showSnackbar('Failed to copy to clipboard', 'error')
  })
}

async function completeTwitterOAuth() {
  twitterOAuthLoading.value = true
  try {
    const response = await fetch('/api/twitter/manual-callback', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        code: twitterAuthCode.value,
        state: twitterAuthState.value
      })
    })

    if (response.ok) {
      const data = await response.json()
      twitterOAuthStatus.value = {
        connected: true,
        username: data.username || '',
        name: data.name || '',
        profileImage: data.profile_image_url || ''
      }
      showTwitterOAuthManual.value = false
      twitterAuthCode.value = ''
      showSnackbar('Twitter account connected successfully!', 'success')
    } else {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to complete OAuth')
    }
  } catch (error) {
    console.error('Error completing Twitter OAuth:', error)
    showSnackbar('Failed to connect Twitter account: ' + error.message, 'error')
  } finally {
    twitterOAuthLoading.value = false
  }
}

function cancelTwitterOAuth() {
  showTwitterOAuthManual.value = false
  twitterAuthCode.value = ''
  twitterAuthUrl.value = ''
  twitterAuthState.value = ''
}

async function disconnectTwitterOAuth() {
  if (!confirm('Are you sure you want to disconnect your Twitter account?')) {
    return
  }

  try {
    const response = await fetch('/api/twitter/disconnect', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
      }
    })

    if (response.ok) {
      twitterOAuthStatus.value = {
        connected: false,
        username: '',
        name: '',
        profileImage: ''
      }
      showSnackbar('Twitter account disconnected', 'success')
    } else {
      throw new Error('Failed to disconnect')
    }
  } catch (error) {
    console.error('Error disconnecting Twitter:', error)
    showSnackbar('Failed to disconnect Twitter account: ' + error.message, 'error')
  }
}

onMounted(() => {
  // Check Twitter OAuth status on mount
  checkTwitterOAuthStatus()
})


async function saveSettings() {
  saving.value = true
  try {
    // Transform the flat configs structure to the hierarchical API structure
    const apiConfigStructure = {
      preproduction: {
        ai_services: {
          ollama: configs.value.ollama,
          openai: configs.value.openai,
          anthropic: configs.value.anthropic,
          gemini: configs.value.gemini,
          grok: configs.value.grok,
          stabilityAi: configs.value.stabilityAi,
          elevenLabs: configs.value.elevenLabs
        },
        storage: {
          google: configs.value.google,
          aws: configs.value.aws
        },
        communication: {
          slack: configs.value.slack,
          discord: configs.value.discord,
          twilio: configs.value.twilio,
          email: configs.value.email,
          asterisk: configs.value.asterisk
        }
      },
      promotion: {
        social_media: {
          youtube: configs.value.youtube,
          vimeo: configs.value.vimeo,
          twitter: configs.value.twitter
        }
      },
      development: {
        github: configs.value.github,
        webhooks: configs.value.webhooks
      }
    }

    const response = await fetch('/api/settings/api-configs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
      },
      body: JSON.stringify({ config: apiConfigStructure })
    })

    if (response.ok) {
      emit('save', configs.value)
      showSnackbar('API configuration saved successfully', 'success')
    } else {
      throw new Error('Failed to save configuration')
    }
  } catch (error) {
    console.error('Error saving API configuration:', error)
    showSnackbar('Failed to save API configuration', 'error')
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