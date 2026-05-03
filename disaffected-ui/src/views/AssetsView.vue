<template>
  <v-container fluid>
    <v-row>
      <v-col>
        <h2 class="text-h4 font-weight-bold mb-4">Asset Pool</h2>
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

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const assets = ref([])
const loading = ref(false)
const headers = [
  { title: 'Filename', key: 'filename', sortable: true },
  { title: 'Type', key: 'type', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
]

async function uploadAsset(event) {
  const file = event.target.files[0]
  if (!file) return
  loading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    const response = await axios.post('/api/assets', formData, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`,
        'Content-Type': 'multipart/form-data'
      }
    })
    assets.value.push(response.data)
  } catch (error) {
    console.error('Failed to upload asset:', error)
  }
  loading.value = false
}

async function deleteAsset(item) {
  try {
    await axios.delete(`/api/assets/${item.id}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
    })
    assets.value = assets.value.filter(a => a.id !== item.id)
  } catch (error) {
    console.error('Failed to delete asset:', error)
  }
}

async function loadAssets() {
  loading.value = true
  try {
    const response = await axios.get('/api/assets', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
    })
    assets.value = response.data
  } catch (error) {
    console.error('Failed to load assets:', error)
  }
  loading.value = false
}

onMounted(() => {
  loadAssets()
})
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