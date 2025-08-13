<!-- eslint-disable vue/valid-v-slot -->
<template>
  <v-container fluid class="pa-6">
    <div class="d-flex align-center mb-6">
      <v-icon size="32" class="mr-3">mdi-format-list-bulleted-type</v-icon>
      <h1 class="text-h4 font-weight-light">Rundown Item Types</h1>
      <v-spacer></v-spacer>
      <v-btn 
        color="primary" 
        variant="elevated"
        prepend-icon="mdi-plus"
        @click="showAddDialog = true"
      >
        Add Custom Type
      </v-btn>
    </div>

    <!-- Statistics Cards -->
    <v-row class="mb-6">
      <v-col cols="12" sm="6" md="3">
        <v-card class="text-center pa-4">
          <v-icon size="40" color="primary" class="mb-2">mdi-television-classic</v-icon>
          <div class="text-h6">{{ coreTypes.length }}</div>
          <div class="text-body-2 text-medium-emphasis">Core Types</div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="text-center pa-4">
          <v-icon size="40" color="success" class="mb-2">mdi-broadcast</v-icon>
          <div class="text-h6">{{ productionTypes.length }}</div>
          <div class="text-body-2 text-medium-emphasis">Production Types</div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="text-center pa-4">
          <v-icon size="40" color="info" class="mb-2">mdi-cog</v-icon>
          <div class="text-h6">{{ technicalTypes.length }}</div>
          <div class="text-body-2 text-medium-emphasis">Technical Types</div>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card class="text-center pa-4">
          <v-icon size="40" color="warning" class="mb-2">mdi-newspaper-variant</v-icon>
          <div class="text-h6">{{ contentTypes.length }}</div>
          <div class="text-body-2 text-medium-emphasis">Content Types</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Main Types Table -->
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-3">mdi-table</v-icon>
        Item Types Reference
        <v-spacer></v-spacer>
        <v-text-field
          v-model="search"
          append-inner-icon="mdi-magnify"
          label="Search types..."
          single-line
          hide-details
          variant="outlined"
          density="compact"
          style="max-width: 300px"
        ></v-text-field>
      </v-card-title>
      
      <v-data-table
        :headers="headers"
        :items="filteredItemTypes"
        :search="search"
        :items-per-page="25"
        class="item-types-table"
        item-value="value"
      >
        <!-- Color Preview Column -->
        <template v-slot:[`item.color`]="{ item }">
          <div class="d-flex align-center">
            <div 
              class="color-preview mr-3"
              :style="{ backgroundColor: resolveVuetifyColor(getColorValue(item.value)) }"
            ></div>
            <code class="text-caption">{{ getColorValue(item.value) }}</code>
          </div>
        </template>

        <!-- Type Column with Icon -->
        <template v-slot:[`item.title`]="{ item }">
          <div class="d-flex align-center">
            <v-icon :color="getColorValue(item.value)" class="mr-2">
              {{ getTypeIcon(item.value) }}
            </v-icon>
            <span class="font-weight-medium">{{ item.title }}</span>
          </div>
        </template>

        <!-- Value Column -->
        <template v-slot:[`item.value`]="{ item }">
          <v-chip 
            size="small" 
            :color="getColorValue(item.value)"
            text-color="white"
          >
            {{ item.value.toUpperCase() }}
          </v-chip>
        </template>

        <!-- Category Column -->
        <template v-slot:[`item.category`]="{ item }">
          <v-chip 
            size="small" 
            variant="outlined"
            :color="getCategoryColor(item.category)"
          >
            {{ item.category }}
          </v-chip>
        </template>

        <!-- Actions Column -->
        <template v-slot:[`item.actions`]="{ item }">
          <v-btn 
            icon="mdi-pencil" 
            size="small" 
            variant="text"
            @click="editType(item)"
          ></v-btn>
          <v-btn 
            icon="mdi-palette" 
            size="small" 
            variant="text"
            @click="editColor(item)"
          ></v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Color Legend -->
    <v-card class="mt-6">
      <v-card-title>
        <v-icon class="mr-3">mdi-palette</v-icon>
        Color Legend
      </v-card-title>
      <v-card-text>
        <v-row>
          <v-col 
            v-for="category in categories" 
            :key="category.name"
            cols="12" 
            md="6" 
            lg="3"
          >
            <h4 class="text-subtitle-1 mb-3">{{ category.name }}</h4>
            <div class="d-flex flex-wrap ga-2">
              <v-chip
                v-for="type in category.types"
                :key="type.value"
                size="small"
                :color="getColorValue(type.value)"
                text-color="white"
                class="ma-1"
              >
                {{ type.value.toUpperCase() }}
              </v-chip>
            </div>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Add/Edit Dialog -->
    <v-dialog v-model="showAddDialog" max-width="600">
      <v-card>
        <v-card-title>
          {{ editingType ? 'Edit' : 'Add' }} Item Type
        </v-card-title>
        <v-card-text>
          <v-form v-model="formValid">
            <v-text-field
              v-model="typeForm.title"
              label="Display Title"
              :rules="[v => !!v || 'Title is required']"
              variant="outlined"
            ></v-text-field>
            <v-text-field
              v-model="typeForm.value"
              label="Value/Code"
              :rules="[v => !!v || 'Value is required', v => /^[a-z]+$/.test(v) || 'Use lowercase letters only']"
              variant="outlined"
              hint="Lowercase letters only, no spaces (e.g., 'newsbrief')"
            ></v-text-field>
            <v-select
              v-model="typeForm.category"
              :items="categoryOptions"
              label="Category"
              variant="outlined"
            ></v-select>
            <v-text-field
              v-model="typeForm.description"
              label="Description"
              variant="outlined"
            ></v-text-field>
            <v-select
              v-model="typeForm.color"
              :items="colorOptions"
              label="Color"
              variant="outlined"
            >
              <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props">
                  <template v-slot:prepend>
                    <div 
                      class="color-preview-small mr-3"
                      :style="{ backgroundColor: resolveVuetifyColor(item.value) }"
                    ></div>
                  </template>
                </v-list-item>
              </template>
            </v-select>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showAddDialog = false">Cancel</v-btn>
          <v-btn 
            color="primary" 
            :disabled="!formValid"
            @click="saveType"
          >
            {{ editingType ? 'Update' : 'Add' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import { getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap'
import { getAllItemTypes, getItemTypeIcon } from '@/config/itemTypes'

export default {
  name: 'ItemTypesView',
  data() {
    return {
      search: '',
      showAddDialog: false,
      editingType: null,
      formValid: false,
      typeForm: {
        title: '',
        value: '',
        category: '',
        description: '',
        color: ''
      },
      headers: [
        { title: 'Color', key: 'color', sortable: false, width: '120px' },
        { title: 'Type', key: 'title', sortable: true },
        { title: 'Code', key: 'value', sortable: true, width: '100px' },
        { title: 'Category', key: 'category', sortable: true, width: '120px' },
        { title: 'Description', key: 'description', sortable: false },
        { title: 'Actions', key: 'actions', sortable: false, width: '100px' }
      ],
      itemTypes: getAllItemTypes(), // Load from single source of truth
      categoryOptions: ['Core', 'Production', 'Technical', 'Content'],
      colorOptions: [
        { title: 'Primary', value: 'primary' },
        { title: 'Secondary', value: 'secondary' },
        { title: 'Success', value: 'success' },
        { title: 'Info', value: 'info' },
        { title: 'Warning', value: 'warning' },
        { title: 'Error', value: 'error' },
        { title: 'Red', value: 'red' },
        { title: 'Pink', value: 'pink' },
        { title: 'Purple', value: 'purple' },
        { title: 'Deep Purple', value: 'deep-purple' },
        { title: 'Indigo', value: 'indigo' },
        { title: 'Blue', value: 'blue' },
        { title: 'Light Blue', value: 'light-blue' },
        { title: 'Cyan', value: 'cyan' },
        { title: 'Teal', value: 'teal' },
        { title: 'Green', value: 'green' },
        { title: 'Light Green', value: 'light-green' },
        { title: 'Lime', value: 'lime' },
        { title: 'Yellow', value: 'yellow' },
        { title: 'Amber', value: 'amber' },
        { title: 'Orange', value: 'orange' },
        { title: 'Deep Orange', value: 'deep-orange' },
        { title: 'Brown', value: 'brown' },
        { title: 'Grey', value: 'grey' },
        { title: 'Blue Grey', value: 'blue-grey' }
      ]
    }
  },
  computed: {
    filteredItemTypes() {
      if (!this.search) return this.itemTypes
      return this.itemTypes.filter(type => 
        type.title.toLowerCase().includes(this.search.toLowerCase()) ||
        type.value.toLowerCase().includes(this.search.toLowerCase()) ||
        type.category.toLowerCase().includes(this.search.toLowerCase()) ||
        (type.description && type.description.toLowerCase().includes(this.search.toLowerCase()))
      )
    },
    coreTypes() {
      return this.itemTypes.filter(type => type.category === 'Core')
    },
    productionTypes() {
      return this.itemTypes.filter(type => type.category === 'Production')
    },
    technicalTypes() {
      return this.itemTypes.filter(type => type.category === 'Technical')
    },
    contentTypes() {
      return this.itemTypes.filter(type => type.category === 'Content')
    },
    categories() {
      return [
        { name: 'Core Types', types: this.coreTypes },
        { name: 'Production Types', types: this.productionTypes },
        { name: 'Technical Types', types: this.technicalTypes },
        { name: 'Content Types', types: this.contentTypes }
      ]
    }
  },
  methods: {
    getColorValue,
    resolveVuetifyColor,
    getTypeIcon: getItemTypeIcon, // Use centralized icon function
    getCategoryColor(category) {
      const colors = {
        'Core': 'primary',
        'Production': 'success', 
        'Technical': 'info',
        'Content': 'warning'
      }
      return colors[category] || 'grey'
    },
    editType(type) {
      this.editingType = type
      this.typeForm = { ...type }
      this.showAddDialog = true
    },
    editColor(type) {
      // Open color selector for this type
      this.$router.push(`/settings?tab=colors&type=${type.value}`)
    },
    saveType() {
      if (this.editingType) {
        // Update existing type
        const index = this.itemTypes.findIndex(t => t.value === this.editingType.value)
        if (index >= 0) {
          this.itemTypes.splice(index, 1, { ...this.typeForm })
        }
      } else {
        // Add new type
        this.itemTypes.push({ ...this.typeForm })
      }
      this.showAddDialog = false
      this.editingType = null
      this.typeForm = { title: '', value: '', category: '', description: '', color: '' }
    }
  }
}
</script>

<style scoped>
.color-preview {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid rgba(0,0,0,0.12);
}

.color-preview-small {
  width: 16px;
  height: 16px;
  border-radius: 2px;
  border: 1px solid rgba(0,0,0,0.12);
}

.item-types-table :deep(.v-data-table__td) {
  padding: 8px 16px;
}

.item-types-table :deep(.v-data-table__th) {
  font-weight: 600;
}
</style>