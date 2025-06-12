<template>
  <v-container>
    <!-- Header row with episode selector and save button -->
    <v-row class="align-center justify-space-between mb-4">
      <v-col cols="6">
        <h2>Rundown Editor</h2>
      </v-col>
      <v-col cols="6" class="text-right">
        <v-select
          v-model="selectedEpisode"
          :items="episodes"
          label="Select Episode"
          @change="loadEpisode"
          :disabled="loading"
        />
        <v-btn color="primary" class="ml-2" @click="saveChanges" :disabled="loading || segments.length === 0">
          Save & Commit
        </v-btn>
      </v-col>
    </v-row>
    <!-- Rundown list -->
    <v-card-text>
      <div v-if="loading" class="text-center">
        <v-progress-circular indeterminate color="primary" />
        <p>Loading rundown for episode {{ selectedEpisode }}...</p>
      </div>
      <div v-else-if="segments.length === 0" class="text-center">
        <v-alert type="warning" outlined>
          No segments found for episode {{ selectedEpisode }}. Check /mnt/sync/disaffected/episodes/{{ selectedEpisode }}/rundown/ for .md files.
        </v-alert>
      </div>
      <draggable v-else v-model="segments" :item-key="getItemKey">
        <template #item="{ element, index }">
          <v-card
            class="mb-2"
            outlined
            :class="resolveTypeClass(element.type)"
          >
            <v-row no-gutters>
              <!-- Type + Index column (uniform width) -->
              <v-col
                :style="{ width: '80px', minWidth: '80px', maxWidth: '80px' }"
                class="d-flex flex-column"
              >
                <!-- Type cell -->
                <div
                  class="d-flex align-center justify-center"
                  style="
                    background: rgba(0, 0, 0, 0.05);
                    height: 25%;
                    text-align: center;
                    border-right: 1px solid rgba(0, 0, 0, 0.1);
                  "
                >
                  <div class="text-caption font-weight-bold" style="font-size: 0.6rem;">
                    {{ (element.type || 'UNKNOWN').toUpperCase() }}
                  </div>
                </div>
                <!-- Index cell -->
                <div
                  class="d-flex align-center justify-center"
                  style="
                    background: rgba(0, 0, 0, 0.02);
                    height: 75%;
                    border-right: 1px solid rgba(0, 0, 0, 0.1);
                  "
                >
                  <div style="font-size: 1.5em;">
                    {{ (index + 1) * 10 }}
                  </div>
                </div>
              </v-col>
              <!-- Slug content -->
              <v-col>
                <v-card-text>
                  <div>
                    <strong style="font-size: 1.8em;">{{ element.title || 'No title' }}</strong>
                    <div class="text-caption grey--text mt-1">
                      {{ element.asset_id || 'No ID' }}
                    </div>
                    <div class="text-caption grey--text">
                      {{ element.description || 'No description' }}
                    </div>
                    <div class="text-caption grey--text">
                      File: {{ element.filename || 'Unknown' }}
                    </div>
                  </div>
                </v-card-text>
              </v-col>
              <!-- Duration column -->
              <v-col
                cols="auto"
                class="d-flex align-center justify-end"
                :style="{
                  background: 'rgba(0, 0, 0, 0.05)',
                  padding: '0 16px',
                  minWidth: '100px',
                }"
              >
                <div
                  class="text-center"
                  style="width: 100%; font-size: 1.3em; font-weight: bold;"
                >
                  {{ element.length || 'N/A' }}
                </div>
              </v-col>
            </v-row>
          </v-card>
        </template>
      </draggable>
    </v-card-text>
  </v-container>
</template>

<script>
import draggable from "vuedraggable";
import axios from "axios";
import colorMap from '@/assets/config/colorMap.js';

export default {
  name: "RundownManager",
  components: { draggable },
  data() {
    return {
      segments: [],
      selectedEpisode: "0225",
      episodes: ["0225", "0226", "0227"], // Can be made dynamic
      loading: false,
    };
  },
  methods: {
    getItemKey(item) {
      return item.asset_id || item.filename || item.order || Math.random().toString();
    },
    async loadEpisode() {
      this.loading = true;
      try {
        const response = await axios.get(`http://192.168.51.210:8888/rundown/${this.selectedEpisode}`);
        console.log("[DEBUG] API Response:", response.data);
        this.segments = response.data.map(entry => ({
          ...entry.metadata,
          filename: entry.filename // Ensure filename is included
        }));
        console.log("[DEBUG] Processed Segments:", this.segments);
      } catch (err) {
        console.error("[ERROR] Failed to load rundown:", err);
        this.segments = [];
        alert(`Failed to load rundown for episode ${this.selectedEpisode}: ${err.message}`);
      } finally {
        this.loading = false;
      }
    },
    async saveChanges() {
      try {
        const payload = { segments: this.segments.map(segment => ({ filename: segment.filename })) };
        const response = await axios.post(
          `http://192.168.51.210:8888/rundown/${this.selectedEpisode}/reorder`,
          payload
        );
        console.log("[DEBUG] Rundown saved:", response.data);
        alert("Rundown reordered successfully!");
      } catch (err) {
        console.error("[ERROR] Failed to save rundown:", err);
        alert("Failed to save rundown: " + err.message);
      }
    },
    resolveTypeClass(type) {
      const typeKey = (type || '').toLowerCase();
      const color = colorMap[typeKey] || 'white';
      console.log("[DEBUG] Type:", typeKey, "Class:", color);
      return color; // Returns class like 'blue lighten-4'
    },
  },
  mounted() {
    this.loadEpisode();
  },
};
</script>

<style scoped>
.v-card {
  cursor: grab;
}
</style>
