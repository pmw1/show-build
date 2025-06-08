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
        />
        <v-btn color="primary" class="ml-2" @click="saveChanges">
          Save & Commit
        </v-btn>
      </v-col>
    </v-row>

    <!-- Rundown list -->
    <v-card-text>
      <draggable v-model="segments" :item-key="getItemKey">
        <template #item="{ element, index }">
          <v-card class="mb-2" outlined>
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
                    border-right: 1px solid rgba(0, 0, 0, 0.05);
                  "
                >
                  <div class="text-caption font-weight-bold" style="font-size: 0.6rem;">
                    {{ element.type?.toUpperCase() }}
                  </div>
                </div>

                <!-- Index cell -->
                <div
                  class="d-flex align-center justify-center"
                  style="
                    background: rgba(0, 0, 0, 0.02);
                    height: 75%;
                    border-right: 1px solid rgba(0, 0, 0, 0.05);
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
                    <strong style="font-size: 1.8em;">{{ element.slug }}</strong>
                    <div class="text-caption grey--text mt-1">
                      {{ element.id }}
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
                  padding: '0 1em',
                  minWidth: '80px',
                }"
              >
                <div
                  class="text-center"
                  style="width: 100%; font-size: 1.3em; font-weight: bold;"
                >
                  {{ element.duration }}
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

export default {
  name: "RundownManager",
  components: { draggable },
  data() {
    return {
      segments: [],
      selectedEpisode: "0225",
      episodes: ["0225", "0226", "0227"], // Can be made dynamic
    };
  },
  methods: {
    getItemKey(item) {
      return item.slug || item.id || item.order || Math.random().toString();
    },
    loadEpisode() {
      axios
        .get(`http://192.168.51.210:8888/rundown/${this.selectedEpisode}`)
        .then((response) => {
          console.log("[DEBUG] segments loaded:", response.data);
          this.segments = response.data.map(entry => entry.metadata);
        })
        .catch((err) => {
          console.error("Failed to load rundown:", err);
        });
    },
    saveChanges() {
      // Placeholder for backend commit logic
      console.log("Saving rundown:", this.segments);
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

