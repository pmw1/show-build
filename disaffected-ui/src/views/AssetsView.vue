<template>
  <v-container fluid>
    <v-row>
      <v-col>
        <h2 class="text-h4 font-weight-bold mb-4">Asset Manager</h2>
        <v-file-input
          label="Upload Asset"
          accept="image/*,video/*,audio/*"
          @change="uploadAsset"
          prepend-icon="mdi-upload"
        ></v-file-input>
        <v-data-table
          :headers="headers"
          :items="assets"
          :loading="loading"
          class="elevation-1"
        >
          <template v-slot:[`item.actions`]="{ item }">
            <v-btn
              icon="mdi-delete"
              size="small"
              color="error"
              @click="deleteAsset(item)"
            ></v-btn>
          </template>
        </v-data-table>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AssetsView',
  data() {
    return {
      assets: [],
      loading: false,
      headers: [
        { title: 'Filename', key: 'filename', sortable: true },
        { title: 'Type', key: 'type', sortable: true },
        { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
      ]
    };
  },
  methods: {
    async uploadAsset(event) {
      const file = event.target.files[0];
      if (!file) return;
      this.loading = true;
      try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await axios.post('/api/assets', formData, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth-token')}`,
            'Content-Type': 'multipart/form-data'
          }
        });
        this.assets.push(response.data);
      } catch (error) {
        console.error('Failed to upload asset:', error);
      }
      this.loading = false;
    },
    async deleteAsset(item) {
      try {
        await axios.delete(`/api/assets/${item.id}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        this.assets = this.assets.filter(a => a.id !== item.id);
      } catch (error) {
        console.error('Failed to delete asset:', error);
      }
    },
    async loadAssets() {
      this.loading = true;
      try {
        const response = await axios.get('/api/assets', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        this.assets = response.data;
      } catch (error) {
        console.error('Failed to load assets:', error);
      }
      this.loading = false;
    }
  },
  mounted() {
    this.loadAssets();
  }
}
</script>

<style scoped>
.header-row {
  background: rgba(0, 0, 0, 0.03);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.cursor-pointer {
  cursor: pointer;
}
</style>