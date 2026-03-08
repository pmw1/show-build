<template>
  <v-card class="pa-0">
    <v-row no-gutters class="fill-height">
      <!-- Vertical Tabs on Left -->
      <v-col cols="3" class="border-r">
        <v-tabs
          v-model="systemSubTab"
          direction="vertical"
          color="primary"
          class="system-vertical-tabs"
        >
          <v-tab value="media-storage" prepend-icon="mdi-folder-multiple">
            Media Storage Locations
          </v-tab>
          <v-tab value="database" prepend-icon="mdi-database">
            Database
          </v-tab>
          <v-tab value="performance" prepend-icon="mdi-speedometer">
            Performance
          </v-tab>
          <v-tab value="backup" prepend-icon="mdi-backup-restore">
            Backup & Recovery
          </v-tab>
          <v-tab value="maintenance" prepend-icon="mdi-wrench">
            Maintenance
          </v-tab>
          <v-tab value="cold-storage" prepend-icon="mdi-snowflake">
            Cold Storage
          </v-tab>
          <v-tab value="archive" prepend-icon="mdi-archive">
            Archive
          </v-tab>
          <v-tab value="voice" prepend-icon="mdi-microphone">
            Voice Services
          </v-tab>
          <v-tab value="mp3-encoding" prepend-icon="mdi-music">
            MP3 Encoding
          </v-tab>
          <v-tab value="deployments" prepend-icon="mdi-cloud-upload">
            Deployments
          </v-tab>
        </v-tabs>
      </v-col>

      <!-- Tab Content on Right -->
      <v-col cols="9">
        <v-tabs-window v-model="systemSubTab" class="pa-6">
          
          <!-- Media Storage Locations -->
          <v-tabs-window-item value="media-storage">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-folder-multiple</v-icon>
              Media Storage Locations
            </h3>
            <p class="text-body-2 mb-4">Configure where media files are stored on the server filesystem.</p>
            
            <!-- Show Root Configuration -->
            <v-card variant="tonal" color="primary" class="pa-4 mb-4">
              <h4 class="text-subtitle-1 mb-3 d-flex align-center">
                <v-icon left class="mr-2">mdi-home-circle</v-icon>
                Show Root Directory
              </h4>
              <v-text-field
                v-model="systemSettings.showRoot"
                label="Show Root Path"
                placeholder="/mnt/sync/disaffected"
                persistent-hint
                hint="Main show directory - all other paths will be relative to this unless manually overridden"
                prepend-icon="mdi-folder-home"
                variant="outlined"
                density="comfortable"
                class="mb-2"
                @input="updateDerivedPaths"
              />
              <v-alert type="info" variant="text" density="compact" class="mt-2">
                Setting this will automatically configure all paths below. You can override individual paths if needed.
              </v-alert>
            </v-card>
            
            <v-divider class="mb-4" />
            
            <h4 class="text-subtitle-1 mb-3">Directory Structure</h4>
            <p class="text-caption mb-3">These paths are automatically set based on Show Root but can be manually overridden.</p>
            
            <!-- Episodes and Media Assets -->
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="systemSettings.episodesPath"
                  label="Episodes Folder"
                  :placeholder="derivedPaths.episodes"
                  persistent-hint
                  :hint="episodesPathHint"
                  prepend-icon="mdi-television-classic"
                  :variant="systemSettings.episodesPath && systemSettings.episodesPath !== derivedPaths.episodes ? 'outlined' : 'filled'"
                >
                  <template v-slot:append-inner v-if="systemSettings.episodesPath && systemSettings.episodesPath !== derivedPaths.episodes">
                    <v-tooltip text="Reset to default">
                      <template v-slot:activator="{ props }">
                        <v-btn
                          v-bind="props"
                          icon="mdi-refresh"
                          size="x-small"
                          variant="text"
                          @click="systemSettings.episodesPath = derivedPaths.episodes"
                        />
                      </template>
                    </v-tooltip>
                  </template>
                </v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="systemSettings.mediaAssetsPath"
                  label="Media Assets"
                  :placeholder="derivedPaths.mediaAssets"
                  persistent-hint
                  :hint="mediaAssetsPathHint"
                  prepend-icon="mdi-folder-star"
                  :variant="systemSettings.mediaAssetsPath && systemSettings.mediaAssetsPath !== derivedPaths.mediaAssets ? 'outlined' : 'filled'"
                >
                  <template v-slot:append-inner v-if="systemSettings.mediaAssetsPath && systemSettings.mediaAssetsPath !== derivedPaths.mediaAssets">
                    <v-tooltip text="Reset to default">
                      <template v-slot:activator="{ props }">
                        <v-btn
                          v-bind="props"
                          icon="mdi-refresh"
                          size="x-small"
                          variant="text"
                          @click="systemSettings.mediaAssetsPath = derivedPaths.mediaAssets"
                        />
                      </template>
                    </v-tooltip>
                  </template>
                </v-text-field>
              </v-col>
            </v-row>
            
            <!-- Uploads and Process -->
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="systemSettings.uploadsPath"
                  label="Uploads (Locked)"
                  :placeholder="derivedPaths.uploads"
                  persistent-hint
                  :hint="uploadsPathHint"
                  prepend-icon="mdi-cloud-upload-outline"
                  :variant="systemSettings.uploadsPath && systemSettings.uploadsPath !== derivedPaths.uploads ? 'outlined' : 'filled'"
                >
                  <template v-slot:append-inner>
                    <v-icon color="warning" size="small">mdi-lock</v-icon>
                    <v-tooltip text="Reset to default" v-if="systemSettings.uploadsPath && systemSettings.uploadsPath !== derivedPaths.uploads">
                      <template v-slot:activator="{ props }">
                        <v-btn
                          v-bind="props"
                          icon="mdi-refresh"
                          size="x-small"
                          variant="text"
                          @click="systemSettings.uploadsPath = derivedPaths.uploads"
                          class="ml-2"
                        />
                      </template>
                    </v-tooltip>
                  </template>
                </v-text-field>
              </v-col>
            </v-row>

            <!-- Process folder -->
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="systemSettings.processPath"
                  label="Process (Media Conversions & Automations)"
                  :placeholder="derivedPaths.process"
                  persistent-hint
                  :hint="processPathHint"
                  prepend-icon="mdi-cog-transfer"
                  :variant="systemSettings.processPath && systemSettings.processPath !== derivedPaths.process ? 'outlined' : 'filled'"
                >
                  <template v-slot:append-inner v-if="systemSettings.processPath && systemSettings.processPath !== derivedPaths.process">
                    <v-tooltip text="Reset to default">
                      <template v-slot:activator="{ props }">
                        <v-btn
                          v-bind="props"
                          icon="mdi-refresh"
                          size="x-small"
                          variant="text"
                          @click="systemSettings.processPath = derivedPaths.process"
                        />
                      </template>
                    </v-tooltip>
                  </template>
                </v-text-field>
              </v-col>
            </v-row>
            
            <v-divider class="my-4" />
            
            <h4 class="text-subtitle-1 mb-3">Current Structure Preview</h4>
            <v-card variant="outlined" class="pa-3 mb-4">
              <pre class="text-body-2">{{ mediaStructurePreview }}</pre>
            </v-card>
            
            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingSystem"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Media Paths
            </v-btn>
          </v-tabs-window-item>

          <!-- Database Settings -->
          <v-tabs-window-item value="database">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-database</v-icon>
              Database Configuration
            </h3>
            <p class="text-body-2 mb-4">Configure database connection and settings.</p>
            
            <v-select
              v-model="systemSettings.databaseType"
              :items="['PostgreSQL', 'MySQL', 'SQLite', 'MongoDB']"
              label="Database Type"
              class="mb-4"
            />
            
            <v-row v-if="systemSettings.databaseType !== 'SQLite'">
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="systemSettings.databaseHost"
                  label="Host"
                  placeholder="localhost"
                  prepend-icon="mdi-server"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="systemSettings.databasePort"
                  label="Port"
                  placeholder="5432"
                  type="number"
                  prepend-icon="mdi-ethernet-cable"
                />
              </v-col>
            </v-row>
            
            <v-row v-if="systemSettings.databaseType !== 'SQLite'">
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="systemSettings.databaseName"
                  label="Database Name"
                  placeholder="showbuild"
                  prepend-icon="mdi-database"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="systemSettings.databaseUser"
                  label="Username"
                  placeholder="dbuser"
                  prepend-icon="mdi-account"
                />
              </v-col>
            </v-row>
            
            <v-text-field
              v-if="systemSettings.databaseType !== 'SQLite'"
              v-model="systemSettings.databasePassword"
              label="Password"
              type="password"
              placeholder="Enter database password"
              prepend-icon="mdi-lock"
              class="mb-4"
            />
            
            <v-text-field
              v-if="systemSettings.databaseType === 'SQLite'"
              v-model="systemSettings.databasePath"
              label="Database File Path"
              placeholder="/data/showbuild.db"
              prepend-icon="mdi-file-database"
              class="mb-4"
            />
            
            <div class="d-flex gap-3">
              <v-btn
                color="secondary"
                variant="outlined"
                @click="testDatabaseConnection"
                :loading="testingDatabase"
              >
                <v-icon left>mdi-database-check</v-icon>
                Test Connection
              </v-btn>
              
              <v-btn
                color="primary"
                @click="handleSave"
                :loading="savingSystem"
              >
                <v-icon left>mdi-content-save</v-icon>
                Save Database Settings
              </v-btn>
            </div>
          </v-tabs-window-item>

          <!-- Performance Settings -->
          <v-tabs-window-item value="performance">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-speedometer</v-icon>
              Performance Settings
            </h3>
            <p class="text-body-2 mb-4">Optimize system performance and resource usage.</p>
            
            <v-slider
              v-model="systemSettings.maxUploadSize"
              label="Max Upload Size"
              min="10"
              max="500"
              step="10"
              thumb-label
              class="mb-4"
            >
              <template v-slot:append>
                <v-text-field
                  v-model="systemSettings.maxUploadSize"
                  type="number"
                  style="width: 80px"
                  density="compact"
                  suffix="MB"
                  hide-details
                />
              </template>
            </v-slider>
            
            <v-slider
              v-model="systemSettings.cacheSize"
              label="Cache Size"
              min="50"
              max="1000"
              step="50"
              thumb-label
              class="mb-4"
            >
              <template v-slot:append>
                <v-text-field
                  v-model="systemSettings.cacheSize"
                  type="number"
                  style="width: 80px"
                  density="compact"
                  suffix="MB"
                  hide-details
                />
              </template>
            </v-slider>
            
            <v-divider class="my-4" />
            
            <v-switch
              v-model="systemSettings.enableCaching"
              label="Enable caching"
              hint="Cache frequently accessed data for faster response"
              persistent-hint
              color="primary"
              class="mb-3"
            />
            
            <v-switch
              v-model="systemSettings.enableCompression"
              label="Enable response compression"
              hint="Compress API responses to reduce bandwidth"
              persistent-hint
              color="primary"
              class="mb-3"
            />
            
            <v-switch
              v-model="systemSettings.lazyLoadImages"
              label="Lazy load images"
              hint="Load images only when visible on screen"
              persistent-hint
              color="primary"
              class="mb-3"
            />
            
            <v-switch
              v-model="systemSettings.debugMode"
              label="Debug mode"
              hint="Enable verbose logging (impacts performance)"
              persistent-hint
              color="warning"
              class="mb-3"
            />
            
            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingSystem"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Performance Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Backup & Recovery -->
          <v-tabs-window-item value="backup">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-backup-restore</v-icon>
              Backup & Recovery
            </h3>
            <p class="text-body-2 mb-4">Configure automatic backups and recovery options.</p>
            
            <v-switch
              v-model="systemSettings.autoBackup"
              label="Enable automatic backups"
              color="primary"
              class="mb-4"
            />
            
            <v-expand-transition>
              <div v-if="systemSettings.autoBackup">
                <v-row>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="systemSettings.backupFrequency"
                      :items="['Hourly', 'Daily', 'Weekly', 'Monthly']"
                      label="Backup Frequency"
                      prepend-icon="mdi-clock-outline"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="systemSettings.backupRetention"
                      label="Retention Period"
                      type="number"
                      suffix="days"
                      prepend-icon="mdi-calendar-range"
                    />
                  </v-col>
                </v-row>
                
                <v-text-field
                  v-model="systemSettings.backupPath"
                  label="Backup Directory"
                  placeholder="/backups"
                  persistent-hint
                  hint="Where backup files will be stored"
                  prepend-icon="mdi-folder-lock"
                  class="mb-4"
                />
                
                <v-checkbox
                  v-model="systemSettings.backupDatabase"
                  label="Include database in backups"
                  class="mb-2"
                />
                
                <v-checkbox
                  v-model="systemSettings.backupMedia"
                  label="Include media files in backups"
                  class="mb-2"
                />
                
                <v-checkbox
                  v-model="systemSettings.backupConfigs"
                  label="Include configuration files in backups"
                  class="mb-4"
                />
              </div>
            </v-expand-transition>
            
            <v-divider class="my-4" />
            
            <h4 class="text-subtitle-1 mb-3">Manual Backup</h4>
            
            <v-btn
              color="success"
              variant="outlined"
              @click="createBackup"
              :loading="creatingBackup"
              class="mb-4"
            >
              <v-icon left>mdi-database-export</v-icon>
              Create Backup Now
            </v-btn>
            
            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingSystem"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Backup Settings
            </v-btn>

            <v-divider class="my-6" />

            <h3 class="text-h6 mb-2">
              <v-icon left>mdi-history</v-icon>
              Autosave &amp; Version History
            </h3>
            <p class="text-body-2 mb-4">
              Filesystem snapshots of your content, stored in each episode's <code>.history/</code> directory.
              These provide a safety net beyond database autosave.
            </p>

            <v-switch
              v-model="autosaveHistory.enabled"
              label="Enable filesystem autosave snapshots"
              color="primary"
              class="mb-4"
            />

            <v-expand-transition>
              <div v-if="autosaveHistory.enabled">
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="autosaveHistory.segment_interval_seconds"
                      label="Segment Snapshot Interval"
                      type="number"
                      suffix="seconds"
                      prepend-icon="mdi-file-document-outline"
                      hint="How often to snapshot individual segments"
                      persistent-hint
                      :min="10"
                      :max="300"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="autosaveHistory.episode_interval_seconds"
                      label="Episode Snapshot Interval"
                      type="number"
                      suffix="seconds"
                      prepend-icon="mdi-book-open-variant"
                      hint="How often to snapshot entire episodes"
                      persistent-hint
                      :min="60"
                      :max="1800"
                    />
                  </v-col>
                </v-row>

                <v-row class="mt-2">
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="autosaveHistory.segment_retention_count"
                      label="Segment Snapshots to Keep"
                      type="number"
                      prepend-icon="mdi-counter"
                      hint="Per segment (oldest pruned automatically)"
                      persistent-hint
                      :min="5"
                      :max="100"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model.number="autosaveHistory.episode_retention_count"
                      label="Episode Snapshots to Keep"
                      type="number"
                      prepend-icon="mdi-counter"
                      hint="Per episode (oldest pruned automatically)"
                      persistent-hint
                      :min="3"
                      :max="50"
                    />
                  </v-col>
                </v-row>

                <p class="text-caption text-grey mt-3 mb-4">
                  Storage: ~{{ Math.round(autosaveHistory.segment_retention_count * 3.5) }} KB per segment,
                  ~{{ Math.round(autosaveHistory.episode_retention_count * 40) }} KB per episode
                </p>
              </div>
            </v-expand-transition>

            <v-btn
              color="primary"
              @click="saveAutosaveSettings"
              :loading="savingAutosave"
              class="mt-2"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Autosave Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Maintenance -->
          <v-tabs-window-item value="maintenance">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-wrench</v-icon>
              System Maintenance
            </h3>
            <p class="text-body-2 mb-4">Perform maintenance tasks to keep the system running smoothly.</p>
            
            <v-list class="mb-4">
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="warning">mdi-cached</v-icon>
                </template>
                <v-list-item-title>Clear Cache</v-list-item-title>
                <v-list-item-subtitle>Remove cached data to free up memory</v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn
                    color="warning"
                    variant="outlined"
                    @click="clearCache"
                    :loading="clearingCache"
                  >
                    Clear
                  </v-btn>
                </template>
              </v-list-item>
              
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="info">mdi-database-sync</v-icon>
                </template>
                <v-list-item-title>Optimize Database</v-list-item-title>
                <v-list-item-subtitle>Rebuild indexes and clean up database</v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn
                    color="info"
                    variant="outlined"
                    @click="optimizeDatabase"
                    :loading="optimizingDatabase"
                  >
                    Optimize
                  </v-btn>
                </template>
              </v-list-item>
              
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="secondary">mdi-folder-sync</v-icon>
                </template>
                <v-list-item-title>Organize Media Files</v-list-item-title>
                <v-list-item-subtitle>Reorganize media files into proper directories</v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn
                    color="secondary"
                    variant="outlined"
                    @click="organizeMedia"
                    :loading="organizingMedia"
                  >
                    Organize
                  </v-btn>
                </template>
              </v-list-item>
              
              <v-list-item>
                <template v-slot:prepend>
                  <v-icon color="error">mdi-delete-sweep</v-icon>
                </template>
                <v-list-item-title>Clean Temporary Files</v-list-item-title>
                <v-list-item-subtitle>Remove old uploads and temporary files</v-list-item-subtitle>
                <template v-slot:append>
                  <v-btn
                    color="error"
                    variant="outlined"
                    @click="cleanTempFiles"
                    :loading="cleaningTemp"
                  >
                    Clean
                  </v-btn>
                </template>
              </v-list-item>
            </v-list>
            
            <v-divider class="my-4" />
            
            <h4 class="text-subtitle-1 mb-3">System Information</h4>
            
            <v-card variant="outlined" class="pa-3">
              <v-table density="compact">
                <tbody>
                  <tr>
                    <td>Database Size:</td>
                    <td>{{ systemInfo.databaseSize || 'Loading...' }}</td>
                  </tr>
                  <tr>
                    <td>Media Storage Used:</td>
                    <td>{{ systemInfo.mediaSize || 'Loading...' }}</td>
                  </tr>
                  <tr>
                    <td>Cache Size:</td>
                    <td>{{ systemInfo.cacheSize || 'Loading...' }}</td>
                  </tr>
                  <tr>
                    <td>Last Backup:</td>
                    <td>{{ systemInfo.lastBackup || 'Never' }}</td>
                  </tr>
                </tbody>
              </v-table>
            </v-card>
          </v-tabs-window-item>

          <!-- Cold Storage -->
          <v-tabs-window-item value="cold-storage">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-snowflake</v-icon>
              Cold Storage Configuration
            </h3>
            <p class="text-body-2 mb-4">Configure long-term archival storage for older episodes and media.</p>
            
            <v-alert type="info" variant="tonal" class="mb-4">
              Cold storage allows you to archive older episodes to cheaper, slower storage while keeping recent episodes on fast storage.
            </v-alert>
            
            <v-switch
              v-model="systemSettings.coldStorageEnabled"
              label="Enable cold storage"
              color="primary"
              class="mb-4"
            />
            
            <v-expand-transition>
              <div v-if="systemSettings.coldStorageEnabled">
                <v-text-field
                  v-model="systemSettings.coldStoragePath"
                  label="Cold Storage Path"
                  placeholder="/mnt/archive/episodes"
                  persistent-hint
                  hint="Directory for archived episodes"
                  prepend-icon="mdi-archive"
                  class="mb-4"
                />
                
                <v-row>
                  <v-col cols="12" md="6">
                    <v-text-field
                      v-model="systemSettings.archiveAfterDays"
                      label="Archive After"
                      type="number"
                      suffix="days"
                      persistent-hint
                      hint="Move to cold storage after this many days"
                      prepend-icon="mdi-calendar-clock"
                    />
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-select
                      v-model="systemSettings.archiveStrategy"
                      :items="['Move', 'Copy', 'Compress & Move']"
                      label="Archive Strategy"
                      persistent-hint
                      hint="How to handle archiving"
                      prepend-icon="mdi-transfer"
                    />
                  </v-col>
                </v-row>
                
                <v-divider class="my-4" />
                
                <h4 class="text-subtitle-1 mb-3">Archive Rules</h4>
                
                <v-checkbox
                  v-model="systemSettings.keepRecentEpisodes"
                  label="Always keep last 10 episodes on fast storage"
                  class="mb-2"
                />
                
                <v-checkbox
                  v-model="systemSettings.archiveExports"
                  label="Archive exported files"
                  class="mb-2"
                />
                
                <v-checkbox
                  v-model="systemSettings.archiveRawCaptures"
                  label="Archive raw captures"
                  class="mb-2"
                />
                
                <v-checkbox
                  v-model="systemSettings.compressBeforeArchive"
                  label="Compress files before archiving"
                  class="mb-4"
                />
                
                <v-alert type="warning" variant="tonal" class="mb-4">
                  <strong>Note:</strong> This feature is under development. Settings are saved but not yet functional.
                </v-alert>
              </div>
            </v-expand-transition>
            
            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingSystem"
              :disabled="!systemSettings.coldStorageEnabled"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Cold Storage Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Archive Tab -->
          <v-tabs-window-item value="archive">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-archive</v-icon>
              Archive Service Configuration
            </h3>
            <p class="text-body-2 mb-4">
              Configure remote archive services for long-term storage. 
              Archive storage is typically separate from local drives and may use cloud services or network-attached storage.
            </p>

            <v-alert type="info" variant="tonal" class="mb-4">
              <v-alert-title>Archive vs Cold Storage</v-alert-title>
              <div class="text-body-2">
                <ul class="mt-2">
                  <li><strong>Cold Storage:</strong> Local/attached drives for rarely accessed content</li>
                  <li><strong>Archive:</strong> Remote/cloud services for permanent archival</li>
                </ul>
              </div>
            </v-alert>

            <v-switch
              v-model="systemSettings.archiveEnabled"
              label="Enable Archive Service"
              color="primary"
              class="mb-4"
            />

            <div v-if="systemSettings.archiveEnabled">
              <v-select
                v-model="systemSettings.archiveType"
                :items="['s3', 'azure', 'gcs', 'smb', 'ftp', 'webdav']"
                label="Archive Service Type"
                class="mb-4"
              >
                <template v-slot:selection="{ item }">
                  <v-chip small>
                    {{ item.value.toUpperCase() }}
                  </v-chip>
                </template>
              </v-select>

              <!-- S3-Compatible Storage -->
              <div v-if="systemSettings.archiveType === 's3'">
                <v-text-field
                  v-model="systemSettings.archiveEndpoint"
                  label="S3 Endpoint"
                  placeholder="https://s3.amazonaws.com"
                  persistent-hint
                  hint="S3-compatible endpoint URL"
                  class="mb-3"
                />
                <v-text-field
                  v-model="systemSettings.archiveBucket"
                  label="Bucket Name"
                  placeholder="show-archive"
                  class="mb-3"
                />
                <v-text-field
                  v-model="systemSettings.archiveAccessKey"
                  label="Access Key ID"
                  type="password"
                  class="mb-3"
                />
                <v-text-field
                  v-model="systemSettings.archiveSecretKey"
                  label="Secret Access Key"
                  type="password"
                  class="mb-3"
                />
              </div>

              <!-- Azure Blob Storage -->
              <div v-if="systemSettings.archiveType === 'azure'">
                <v-text-field
                  v-model="systemSettings.archiveAccountName"
                  label="Storage Account Name"
                  class="mb-3"
                />
                <v-text-field
                  v-model="systemSettings.archiveContainer"
                  label="Container Name"
                  class="mb-3"
                />
                <v-text-field
                  v-model="systemSettings.archiveConnectionString"
                  label="Connection String"
                  type="password"
                  class="mb-3"
                />
              </div>

              <!-- Google Cloud Storage -->
              <div v-if="systemSettings.archiveType === 'gcs'">
                <v-text-field
                  v-model="systemSettings.archiveProjectId"
                  label="Project ID"
                  class="mb-3"
                />
                <v-text-field
                  v-model="systemSettings.archiveBucket"
                  label="Bucket Name"
                  class="mb-3"
                />
                <v-textarea
                  v-model="systemSettings.archiveServiceAccountKey"
                  label="Service Account Key (JSON)"
                  rows="4"
                  class="mb-3"
                />
              </div>

              <!-- SMB/CIFS -->
              <div v-if="systemSettings.archiveType === 'smb'">
                <v-text-field
                  v-model="systemSettings.archiveHost"
                  label="SMB Host"
                  placeholder="//192.168.1.100/archive"
                  class="mb-3"
                />
                <v-text-field
                  v-model="systemSettings.archiveUsername"
                  label="Username"
                  class="mb-3"
                />
                <v-text-field
                  v-model="systemSettings.archivePassword"
                  label="Password"
                  type="password"
                  class="mb-3"
                />
                <v-text-field
                  v-model="systemSettings.archiveDomain"
                  label="Domain (optional)"
                  class="mb-3"
                />
              </div>

              <v-divider class="my-4" />

              <!-- Archive Policies -->
              <h4 class="text-subtitle-1 mb-3">Archive Policies</h4>
              
              <v-text-field
                v-model.number="systemSettings.archiveAfterDays"
                label="Archive Episodes After (days)"
                type="number"
                min="30"
                persistent-hint
                hint="Episodes older than this will be archived"
                class="mb-3"
              />

              <v-switch
                v-model="systemSettings.archiveAutomatic"
                label="Automatic Archival"
                persistent-hint
                hint="Automatically archive old episodes based on policy"
                color="primary"
                class="mb-3"
              />

              <v-switch
                v-model="systemSettings.archiveKeepLocal"
                label="Keep Local Copy"
                persistent-hint
                hint="Retain a local copy after archiving"
                color="primary"
                class="mb-3"
              />

              <v-switch
                v-model="systemSettings.archiveCompression"
                label="Compress Before Archive"
                persistent-hint
                hint="Compress files to save storage costs"
                color="primary"
                class="mb-3"
              />

              <!-- Test Connection -->
              <v-btn
                @click="testArchiveConnection"
                :loading="testingArchive"
                color="secondary"
                variant="outlined"
                class="mt-4 mr-2"
              >
                <v-icon left>mdi-connection</v-icon>
                Test Connection
              </v-btn>
            </div>

            <v-btn
              @click="saveArchiveSettings"
              :loading="savingArchive"
              color="primary"
              variant="elevated"
              class="mt-4"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Archive Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Voice Services Tab -->
          <v-tabs-window-item value="voice">
            <VoiceSettings
              :model-value="voiceConfigs"
              @update:model-value="voiceConfigs = $event"
              @save="handleVoiceSave"
            />
          </v-tabs-window-item>

          <!-- MP3 Encoding Tab -->
          <v-tabs-window-item value="mp3-encoding">
            <Mp3EncodingSettings />
          </v-tabs-window-item>

          <!-- Deployments Tab -->
          <v-tabs-window-item value="deployments">
            <DeploymentSettings />
          </v-tabs-window-item>

        </v-tabs-window>
      </v-col>
    </v-row>
  </v-card>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import VoiceSettings from './VoiceSettings.vue'
import Mp3EncodingSettings from './Mp3EncodingSettings.vue'
import DeploymentSettings from './DeploymentSettings.vue'

// Define props
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

// Define emits
const emit = defineEmits(['update:modelValue', 'save'])

// System sub-tab state
const systemSubTab = ref('media-storage')

// System settings with defaults
const systemSettings = ref({
  // Media Storage
  showRoot: '/mnt/sync/disaffected',
  episodesPath: '',
  mediaAssetsPath: '',
  libraryPath: '',
  uploadsPath: '',
  processPath: '',
  // Database
  databaseType: 'PostgreSQL',
  databaseHost: 'localhost',
  databasePort: 5432,
  databaseName: 'showbuild',
  databaseUser: '',
  databasePassword: '',
  databasePath: '',
  // Performance
  maxUploadSize: 100,
  cacheSize: 256,
  enableCaching: true,
  enableCompression: true,
  lazyLoadImages: true,
  debugMode: false,
  // Backup
  autoBackup: false,
  backupFrequency: 'Daily',
  backupRetention: 30,
  backupPath: '/backups',
  backupDatabase: true,
  backupMedia: false,
  backupConfigs: true,
  // Cold Storage
  coldStorageEnabled: false,
  coldStoragePath: '/mnt/archive/episodes',
  archiveAfterDays: 90,
  archiveStrategy: 'Move',
  keepRecentEpisodes: true,
  archiveExports: true,
  archiveRawCaptures: true,
  compressBeforeArchive: false,
  // Archive Service
  archiveEnabled: false,
  archiveType: 's3',
  archiveEndpoint: '',
  archiveBucket: '',
  archiveAccessKey: '',
  archiveSecretKey: '',
  archiveAccountName: '',
  archiveContainer: '',
  archiveConnectionString: '',
  archiveProjectId: '',
  archiveServiceAccountKey: '',
  archiveHost: '',
  archiveUsername: '',
  archivePassword: '',
  archiveDomain: '',
  archiveAutomatic: false,
  archiveKeepLocal: true,
  archiveCompression: false
})

// Autosave History settings
const autosaveHistory = ref({
  enabled: true,
  segment_interval_seconds: 30,
  episode_interval_seconds: 300,
  segment_retention_count: 20,
  episode_retention_count: 12
})
const savingAutosave = ref(false)

// Voice configurations
const voiceConfigs = ref({
  whisper: {
    host: '',
    endpoint: '/v1/audio/transcriptions',
    enabled: false
  },
  xtts: {
    host: 'http://192.168.51.197:5001',
    endpoint: '/v1/audio/speech',
    language: 'en',
    speed: 1.0,
    speaker: '',
    enabled: false
  },
  fishspeech: {
    host: 'http://192.168.51.197:8080',
    endpoint: '/v1/audio/speech',
    voice: 'kairo_main',
    format: 'wav',
    enabled: false
  }
})

// Derived paths computed property
const derivedPaths = ref({
  episodes: '',
  mediaAssets: '',
  library: '',
  uploads: '',
  process: ''
})

// System info
const systemInfo = ref({
  databaseSize: 'Loading...',
  mediaSize: 'Loading...',
  cacheSize: 'Loading...',
  lastBackup: 'Loading...',
  diskUsage: null,
  episodeCount: 0
})

// Loading states
const savingSystem = ref(false)
const savingArchive = ref(false)
const testingDatabase = ref(false)
const testingArchive = ref(false)
const creatingBackup = ref(false)
const clearingCache = ref(false)
const optimizingDatabase = ref(false)
const organizingMedia = ref(false)
const cleaningTemp = ref(false)

// Computed properties for media structure preview and hints
const mediaStructurePreview = computed(() => {
  const root = systemSettings.value.showRoot || '/mnt/sync/disaffected'
  const episodes = systemSettings.value.episodesPath || derivedPaths.value.episodes
  const mediaAssets = systemSettings.value.mediaAssetsPath || derivedPaths.value.mediaAssets
  const uploads = systemSettings.value.uploadsPath || derivedPaths.value.uploads
  const process = systemSettings.value.processPath || derivedPaths.value.process
  
  return `${root}/
├── ${episodes}/
│   └── {episode_number}/
│       ├── assets/
│       ├── rundown/
│       └── exports/
├── ${mediaAssets}/
│   ├── graphics/
│   ├── promos/
│   ├── ads/
│   └── music/
├── ${uploads}/
└── ${process}/`
})

const episodesPathHint = computed(() => {
  return systemSettings.value.episodesPath && systemSettings.value.episodesPath !== derivedPaths.value.episodes
    ? `Overridden (default: ${derivedPaths.value.episodes})`
    : 'Auto-configured from Show Root'
})

const mediaAssetsPathHint = computed(() => {
  return systemSettings.value.mediaAssetsPath && systemSettings.value.mediaAssetsPath !== derivedPaths.value.mediaAssets
    ? `Overridden (default: ${derivedPaths.value.mediaAssets})`
    : 'Auto-configured from Show Root'
})

const uploadsPathHint = computed(() => {
  return systemSettings.value.uploadsPath && systemSettings.value.uploadsPath !== derivedPaths.value.uploads
    ? `Overridden (default: ${derivedPaths.value.uploads})`
    : 'Auto-configured from Show Root'
})

const processPathHint = computed(() => {
  return systemSettings.value.processPath && systemSettings.value.processPath !== derivedPaths.value.process
    ? `Overridden (default: ${derivedPaths.value.process})`
    : 'Auto-configured from Show Root'
})

// Methods
const updateDerivedPaths = () => {
  const root = systemSettings.value.showRoot || '/mnt/sync/disaffected'
  derivedPaths.value = {
    episodes: `${root}/episodes`,
    mediaAssets: `${root}/mediaassets`,
    library: `${root}/library`,
    uploads: `${root}/uploads`,
    process: `${root}/process`
  }
}

const handleSave = () => {
  // Manually emit update since watcher is disabled
  emit('update:modelValue', { ...systemSettings.value })
  emit('save', { ...systemSettings.value })
}

const saveAutosaveSettings = async () => {
  savingAutosave.value = true
  try {
    const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
    const response = await fetch('/api/settings/autosave-history', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(autosaveHistory.value)
    })
    if (response.ok) {
      console.log('Autosave history settings saved')
    } else {
      console.error('Failed to save autosave settings:', await response.text())
    }
  } catch (e) {
    console.error('Error saving autosave settings:', e)
  } finally {
    savingAutosave.value = false
  }
}

const handleVoiceSave = async (configs) => {
  try {
    // Save voice configurations to API
    const response = await fetch('/api/settings/api-configs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        config: {
          preproduction: {
            ai_services: configs
          }
        }
      })
    })

    if (response.ok) {
      voiceConfigs.value = configs
      console.log('Voice settings saved successfully')
    } else {
      throw new Error('Failed to save voice settings')
    }
  } catch (error) {
    console.error('Error saving voice settings:', error)
  }
}

const testDatabaseConnection = async () => {
  testingDatabase.value = true
  try {
    const response = await fetch('/api/settings/test-database', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      // Success notification would be handled by parent
      console.log('Database connection successful')
    } else {
      throw new Error('Database connection failed')
    }
  } catch (error) {
    console.error('Database connection failed:', error)
  } finally {
    testingDatabase.value = false
  }
}

const createBackup = async () => {
  creatingBackup.value = true
  try {
    const response = await fetch('/api/settings/backup', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      console.log('Backup created successfully')
    } else {
      throw new Error('Backup failed')
    }
  } catch (error) {
    console.error('Failed to create backup:', error)
  } finally {
    creatingBackup.value = false
  }
}

const saveArchiveSettings = async () => {
  savingArchive.value = true
  try {
    const archiveConfig = {
      archive_enabled: systemSettings.value.archiveEnabled,
      archive_type: systemSettings.value.archiveType,
      archive_endpoint: systemSettings.value.archiveEndpoint,
      archive_bucket: systemSettings.value.archiveBucket,
      archive_credentials: {
        access_key: systemSettings.value.archiveAccessKey,
        secret_key: systemSettings.value.archiveSecretKey,
        account_name: systemSettings.value.archiveAccountName,
        connection_string: systemSettings.value.archiveConnectionString,
        project_id: systemSettings.value.archiveProjectId,
        service_account_key: systemSettings.value.archiveServiceAccountKey,
        host: systemSettings.value.archiveHost,
        username: systemSettings.value.archiveUsername,
        password: systemSettings.value.archivePassword,
        domain: systemSettings.value.archiveDomain
      },
      archive_policies: {
        after_days: systemSettings.value.archiveAfterDays || 90,
        automatic: systemSettings.value.archiveAutomatic,
        keep_local: systemSettings.value.archiveKeepLocal,
        compression: systemSettings.value.archiveCompression
      }
    }
    
    const response = await fetch('/api/settings/archive', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(archiveConfig)
    })
    
    if (response.ok) {
      console.log('Archive settings saved successfully')
    } else {
      throw new Error('Failed to save archive settings')
    }
  } catch (error) {
    console.error('Failed to save archive settings:', error)
  } finally {
    savingArchive.value = false
  }
}

const testArchiveConnection = async () => {
  testingArchive.value = true
  try {
    const response = await fetch('/api/settings/archive/test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        type: systemSettings.value.archiveType,
        endpoint: systemSettings.value.archiveEndpoint,
        credentials: {
          access_key: systemSettings.value.archiveAccessKey,
          secret_key: systemSettings.value.archiveSecretKey,
          // Add other credentials as needed based on type
        }
      })
    })
    
    if (response.ok) {
      console.log('Archive connection successful')
    } else {
      throw new Error('Archive connection failed')
    }
  } catch (error) {
    console.error('Failed to connect to archive service:', error)
  } finally {
    testingArchive.value = false
  }
}

const loadSystemInfo = async () => {
  try {
    const response = await fetch('/api/settings/system-info', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      const info = await response.json()
      
      // Update system info display
      systemInfo.value.databaseSize = info.database_size ? info.database_size.formatted : 'Unknown'
      systemInfo.value.mediaSize = info.media_storage_used ? info.media_storage_used.formatted : 'Unknown'
      systemInfo.value.cacheSize = info.cache_size ? info.cache_size.formatted : 'Unknown'
      
      if (info.last_backup) {
        const date = new Date(info.last_backup.timestamp)
        const ageHours = info.last_backup.age_hours
        let ageText = ''
        if (ageHours < 24) {
          ageText = `${Math.round(ageHours)} hours ago`
        } else {
          ageText = `${Math.round(ageHours / 24)} days ago`
        }
        systemInfo.value.lastBackup = `${date.toLocaleDateString()} (${ageText})`
      } else {
        systemInfo.value.lastBackup = 'Never'
      }
      
      systemInfo.value.diskUsage = info.disk_usage
      systemInfo.value.episodeCount = info.episode_count || 0
    }
  } catch (error) {
    console.error('Failed to load system info:', error)
    systemInfo.value.databaseSize = 'Error loading'
    systemInfo.value.mediaSize = 'Error loading'
    systemInfo.value.cacheSize = 'Error loading'
    systemInfo.value.lastBackup = 'Error loading'
  }
}

const clearCache = async () => {
  clearingCache.value = true
  try {
    const response = await fetch('/api/settings/cache', {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (response.ok) {
      const result = await response.json()
      console.log(`Cache cleared! Freed ${result.details.freed_space_formatted || '0 B'}`)
      // Reload system info to show updated cache size
      await loadSystemInfo()
    } else {
      throw new Error('Failed to clear cache')
    }
  } catch (error) {
    console.error('Failed to clear cache:', error)
  } finally {
    clearingCache.value = false
  }
}

const optimizeDatabase = async () => {
  optimizingDatabase.value = true
  try {
    // This would call the actual optimize endpoint
    await new Promise(resolve => setTimeout(resolve, 2000)) // Mock delay
    console.log('Database optimized successfully')
  } catch (error) {
    console.error('Failed to optimize database:', error)
  } finally {
    optimizingDatabase.value = false
  }
}

const organizeMedia = async () => {
  organizingMedia.value = true
  try {
    // This would call the actual organize endpoint
    await new Promise(resolve => setTimeout(resolve, 3000)) // Mock delay
    console.log('Media files organized successfully')
  } catch (error) {
    console.error('Failed to organize media files:', error)
  } finally {
    organizingMedia.value = false
  }
}

const cleanTempFiles = async () => {
  cleaningTemp.value = true
  try {
    // This would call the actual cleanup endpoint
    await new Promise(resolve => setTimeout(resolve, 1500)) // Mock delay
    console.log('Temporary files cleaned successfully')
  } catch (error) {
    console.error('Failed to clean temporary files:', error)
  } finally {
    cleaningTemp.value = false
  }
}

// Watch for prop changes and update local state
// Watch for props changes but prevent recursive updates during initialization
let initializing = false
watch(() => props.modelValue, async (newVal) => {
  if (newVal && !initializing) {
    initializing = true
    await nextTick()
    systemSettings.value = { ...systemSettings.value, ...newVal }
    updateDerivedPaths()
    initializing = false
  }
}, { immediate: true, deep: true })

// DISABLED: Problematic watcher causing infinite loops
// Instead, we'll handle updates manually in specific methods when needed
// watch(systemSettings, async (newVal) => {
//   emit('update:modelValue', newVal)
// }, { deep: true })

// Watch for system sub-tab changes to load system info when on maintenance tab
watch(systemSubTab, (newVal) => {
  if (newVal === 'maintenance') {
    loadSystemInfo()
  }
})

// Load voice configurations from API
const loadVoiceConfigs = async () => {
  try {
    const response = await fetch('/api/settings/api-configs', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token') || localStorage.getItem('token')}`
      }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success && data.data?.preproduction?.ai_services) {
        const aiServices = data.data.preproduction.ai_services

        // Update voice configs with loaded data
        const loadedVoice = {}
        if (aiServices.whisper) loadedVoice.whisper = aiServices.whisper
        if (aiServices.xtts) loadedVoice.xtts = aiServices.xtts
        if (aiServices.fishspeech) loadedVoice.fishspeech = aiServices.fishspeech

        voiceConfigs.value = { ...voiceConfigs.value, ...loadedVoice }
      }
    }
  } catch (error) {
    console.error('Failed to load voice configurations:', error)
  }
}

// Initialize component
const loadAutosaveSettings = async () => {
  try {
    const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
    const response = await fetch('/api/settings', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (response.ok) {
      const data = await response.json()
      if (data.autosave_history) {
        autosaveHistory.value = { ...autosaveHistory.value, ...data.autosave_history }
      }
    }
  } catch (e) {
    console.warn('Could not load autosave settings:', e)
  }
}

onMounted(() => {
  updateDerivedPaths()
  loadVoiceConfigs()
  loadAutosaveSettings()
  if (systemSubTab.value === 'maintenance') {
    loadSystemInfo()
  }
})
</script>

<style scoped>
.system-vertical-tabs {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.border-r {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.v-card {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}

.gap-3 {
  gap: 12px;
}
</style>