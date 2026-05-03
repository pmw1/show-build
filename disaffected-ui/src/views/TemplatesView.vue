<template>
  <v-container fluid class="pa-0">
    <v-row class="header-row ma-0">
      <v-col cols="6" class="pa-4">
        <h2 class="text-h4 font-weight-bold">Templates</h2>
      </v-col>
      <v-col cols="6" class="d-flex align-center justify-end pe-4">
        <v-btn color="primary" prepend-icon="mdi-plus" @click="showCreateDialog = true">New Template</v-btn>
      </v-col>
    </v-row>
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <v-card>
          <v-data-table
            :headers="headers"
            :items="templates"
            :loading="loading"
            density="comfortable"
          >
            <template #[`item.actions`]="{ item }">
              <v-btn icon="mdi-pencil" size="small" variant="text" @click="editTemplate(item)"></v-btn>
              <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteTemplate(item)"></v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
    <v-dialog v-model="showCreateDialog" max-width="500">
      <v-card>
        <v-card-title>Create Template</v-card-title>
        <v-card-text>
          <v-text-field v-model="newTemplate.name" label="Name" required></v-text-field>
          <v-select v-model="newTemplate.type" :items="itemTypeOptions" label="Type" required></v-select>
          <v-textarea v-model="newTemplate.content" label="Content" rows="4"></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="showCreateDialog = false">Cancel</v-btn>
          <v-btn color="success" @click="createTemplate" :disabled="!newTemplate.name || !newTemplate.type">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import axios from 'axios';
import { getItemTypesForDropdown } from '@/config/itemTypes';

const loading = ref(false);
const showCreateDialog = ref(false);
const newTemplate = ref({ name: '', type: '', content: '' });
const headers = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'Type', key: 'type', sortable: true },
  { title: 'Last Modified', key: 'modified', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
];
const templates = ref([]);

const itemTypeOptions = computed(() => { // eslint-disable-line no-unused-vars
  return getItemTypesForDropdown();
});

async function loadTemplates() {
  loading.value = true;
  try {
    const response = await axios.get('/api/templates', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
    });
    templates.value = response.data;
  } catch (error) {
    console.error('Failed to load templates', error);
  }
  loading.value = false;
}

async function createTemplate() {
  loading.value = true;
  try {
    await axios.post('/api/templates', newTemplate.value, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
    });
    loadTemplates();
    showCreateDialog.value = false;
    newTemplate.value = { name: '', type: '', content: '' };
  } catch (error) {
    console.error('Failed to create template', error);
  }
  loading.value = false;
}

async function editTemplate(item) { // eslint-disable-line no-unused-vars
  // This should open a dialog pre-filled with item data
  // For simplicity, we'll just log it.
  console.log('Editing template:', item);
}

async function deleteTemplate(item) { // eslint-disable-line no-unused-vars
  loading.value = true;
  try {
    await axios.delete(`/api/templates/${item.id}`, {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
    });
    templates.value = templates.value.filter(t => t.id !== item.id);
  } catch (error) {
    console.error('Failed to delete template', error);
  }
  loading.value = false;
}

onMounted(() => {
  loadTemplates();
});
</script>

<style scoped>
.header-row {
  background: rgba(0, 0, 0, 0.03);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
</style>