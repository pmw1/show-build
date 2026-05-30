<template>
  <v-container fluid class="unmanaged-data pa-4">
    <v-row>
      <v-col>
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2" color="amber-darken-2">mdi-database-alert</v-icon>
            <span>Unmanaged Data</span>
            <v-chip size="small" color="amber-darken-2" variant="tonal" class="ml-3">
              Admin
            </v-chip>
          </v-card-title>
          <v-card-subtitle>
            Data that arrived from external systems but isn't yet shaped into
            show-build's primary workflow. Use these views to inspect what's
            coming in and decide what to formalize.
          </v-card-subtitle>
        </v-card>

        <v-tabs v-model="activeTab" color="amber-darken-2" class="mt-4 mb-4">
          <v-tab value="showtime">
            <v-icon class="mr-2">mdi-record-rec</v-icon>
            Showtime Data
          </v-tab>
        </v-tabs>

        <v-tabs-window v-model="activeTab">
          <v-tabs-window-item value="showtime">
            <ShowtimeDataPanel />
          </v-tabs-window-item>
        </v-tabs-window>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import ShowtimeDataPanel from '@/components/unmanaged-data/ShowtimeDataPanel.vue'

const activeTab = ref('showtime')
</script>

<style scoped>
.unmanaged-data {
  max-width: 1600px;
  margin: 0 auto;
}
</style>
