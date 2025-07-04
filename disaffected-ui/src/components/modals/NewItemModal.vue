<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="600">
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-plus</v-icon>
          Add New Rundown Item
        </v-card-title>
        
        <v-card-text>
          <v-form ref="newItemForm" :model-value="valid"
          @update:model-value="$emit('update:valid', $event)">
            <v-row>
              <v-col cols="12">
                <v-select
                  :model-value="type"
                  @update:model-value="$emit('update:type', $event)"
                  :items="itemTypes"
                  label="Item Type"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || 'Item type is required']"
                  required
                >
                </v-select>
              </v-col>
              
              <v-col cols="12">
                <v-text-field
                  :model-value="slug"
                  @update:model-value="$emit('update:slug', $event)"
                  label="Slug"
                  placeholder="e.g., Cold Open, Interview with Mayor"
                  variant="outlined"
                  density="comfortable"
                  :rules="[v => !!v || 'Slug is required']"
                  required
                ></v-text-field>
              </v-col>
              
              <v-col cols="12" md="6">
                <v-text-field
                  :model-value="duration"
                  @update:model-value="$emit('update:duration', $event)"
                  label="Estimated Duration"
                  placeholder="00:01:30"
                  variant="outlined"
                  density="comfortable"
                  persistent-hint
                  hint="HH:MM:SS or MM:SS format"
                  :rules="durationRules"
                ></v-text-field>
              </v-col>
              
              <v-col cols="12" md="6">
                <v-text-field
                  :model-value="owner"
                  @update:model-value="$emit('update:owner', $event)"
                  label="Owner / Producer"
                  placeholder="e.g., Sarah J."
                  variant="outlined"
                  density="comfortable"
                  :rules="durationRules"
                ></v-text-field>
              </v-col>
              
              <v-col cols="12">
                <v-textarea
                  :model-value="description"
                  @update:model-value="$emit('update:description', $event)"
                  label="Description / Notes"
                  placeholder="Optional summary or notes for this item."
                  variant="outlined"
                  density="comfortable"
                  rows="2"
                  auto-grow
                ></v-textarea>
              </v-col>
              
              <!-- Type-specific fields -->
              <v-col cols="12" v-if="type === 'segment'">
                <!-- Segment specific fields can be added here -->
              </v-col>
              
              <v-col cols="12" v-if="type === 'ad'">
                 <!-- Ad specific fields can be added here -->
              </v-col>
              
              <v-col cols="12" v-if="type === 'cta'">
                 <!-- CTA specific fields can be added here -->
              </v-col>
            </v-row>
          </v-form>
          
          <!-- Item Preview -->
          <v-divider class="my-4"></v-divider>
          <v-row v-if="type">
            <v-col cols="12">
              <h4 class="text-subtitle-1 mb-2">Preview</h4>
              <v-card outlined class="pa-2">
                <!-- A simple preview of the item can be shown here -->
                <p><strong>Type:</strong> {{ type }}</p>
                <p><strong>Slug:</strong> {{ slug }}</p>
                <p><strong>Duration:</strong> {{ duration }}</p>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
        
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn 
            color="primary" 
            @click="$emit('create')"
            :disabled="!valid"
            :loading="loading"
          >
            Create Item
          </v-btn>
          <v-btn color="secondary" @click="$emit('cancel')">Cancel</v-btn>
        </v-card-actions>
      </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'NewItemModal',
  props: {
    show: { type: Boolean, required: true },
    valid: { type: Boolean, required: true },
    loading: { type: Boolean, default: false },
    type: { type: String, default: null },
    slug: { type: String, default: '' },
    duration: { type: String, default: '' },
    owner: { type: String, default: '' },
    description: { type: String, default: '' },
    itemTypes: { type: Array, default: () => [] },
    durationRules: { type: Array, default: () => [] },
  },
  emits: [
    'update:show',
    'update:valid',
    'update:type',
    'update:slug',
    'update:duration',
    'update:owner',
    'update:description',
    'create',
    'cancel',
  ],
};
</script>
