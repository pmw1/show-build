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
      activeTab: 'colors' // Start with the color configuration tab
    }
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