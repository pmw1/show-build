<template>
  <v-container fluid class="pa-0">
    <!-- Header Row -->
    <v-row class="header-row ma-0">
      <v-col cols="6" class="pa-4">
        <h2 class="text-h4 font-weight-bold">Templates</h2>
      </v-col>
      <v-col cols="6" class="d-flex align-center justify-end pe-4">
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="createTemplate"
        >
          New Template
        </v-btn>
      </v-col>
    </v-row>

    <!-- Content Area -->
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <v-card>
          <v-data-table
            :headers="headers"
            :items="templates"
            :loading="loading"
            density="comfortable"
          >
            <!-- Fix v-slot syntax -->
            <template #[`item.actions`]="{ item }">
              <v-btn
                icon="mdi-pencil"
                size="small"
                variant="text"
                @click="editTemplate(item)"
              ></v-btn>
              <v-btn
                icon="mdi-delete"
                size="small"
                variant="text"
                color="error"
                @click="deleteTemplate(item)"
              ></v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'TemplatesView',
  data: () => ({
    loading: false,
    headers: [
      { title: 'Name', key: 'name', sortable: true },
      { title: 'Type', key: 'type', sortable: true },
      { title: 'Last Modified', key: 'modified', sortable: true },
      { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
    ],
    templates: []
  }),
  methods: {
    createTemplate() {
      console.log('Create new template')
    },
    editTemplate(item) {
      console.log('Edit template', item)
    },
    deleteTemplate(item) {
      console.log('Delete template', item)
    }
  }
}
</script>

<style scoped>
.header-row {
  background: rgba(0, 0, 0, 0.03);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}
</style>