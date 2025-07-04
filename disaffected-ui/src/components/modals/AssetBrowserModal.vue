<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="800px">
    <v-card>
      <v-card-title>
        <span class="text-h5">Asset Browser</span>
        <v-spacer></v-spacer>
        <v-btn icon @click="$emit('update:show', false)">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-card-text>
        <v-file-input
          :model-value="selectedFiles"
          @update:model-value="$emit('update:selectedFiles', $event)"
          label="Upload new assets"
          multiple
          accept="image/*,video/*,audio/*"
          @change="$emit('upload')"
          class="mb-4"
        ></v-file-input>
        
        <v-divider class="my-4"></v-divider>
        
        <v-row>
          <v-col
            v-for="asset in availableAssets"
            :key="asset.id"
            cols="12"
            sm="6"
            md="4"
          >
            <v-card @click="$emit('insert-asset', asset)" class="asset-card" hover>
              <v-img
                v-if="asset.type === 'image'"
                :src="asset.thumbnail || asset.url"
                height="120"
                cover
              ></v-img>
              <v-card-title v-else class="d-flex align-center justify-center" style="height: 120px;">
                <v-icon size="48" :color="getAssetTypeColor(asset.type)">
                  {{ getAssetTypeIcon(asset.type) }}
                </v-icon>
              </v-card-title>
              
              <v-card-subtitle class="text-center">
                {{ asset.filename }}
              </v-card-subtitle>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'AssetBrowserModal',
  props: {
    show: { type: Boolean, required: true },
    availableAssets: { type: Array, default: () => [] },
    selectedFiles: { type: Array, default: () => [] },
  },
  emits: ['update:show', 'update:selectedFiles', 'upload', 'insert-asset'],
  methods: {
    getAssetTypeColor(type) {
      const colors = {
        video: 'blue',
        audio: 'green',
        other: 'grey',
      };
      return colors[type] || colors.other;
    },
    getAssetTypeIcon(type) {
      const icons = {
        video: 'mdi-movie',
        audio: 'mdi-music-note',
        other: 'mdi-file-document',
      };
      return icons[type] || icons.other;
    },
  },
};
</script>

<style scoped>
.asset-card {
  cursor: pointer;
}
</style>
