<template>
  <v-dialog v-model="show" max-width="600">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-plus</v-icon>
        Add New Rundown Item
      </v-card-title>
      
      <v-card-text>
        <v-form ref="newItemForm" v-model="formValid">
          <v-row>
            <v-col cols="12">
              <v-select
                v-model="itemType"
                :items="rundownItemTypes"
                label="Item Type"
                variant="outlined"
                density="comfortable"
                :rules="[v => !!v || 'Item type is required']"
                required
              >
                <template v-slot:item="{ props, item }">
                  <v-list-item v-bind="props" :title="item.title">
                    <template v-slot:prepend>
                      <v-chip 
                        :color="getItemTypeColor(item.value)" 
                        size="x-small" 
                        class="mr-2"
                      >
                        {{ item.value.toUpperCase() }}
                      </v-chip>
                    </template>
                  </v-list-item>
                </template>
              </v-select>
            </v-col>
            
            <v-col cols="12">
              <v-text-field
                v-model="itemTitle"
                label="Title"
                variant="outlined"
                density="comfortable"
                :rules="titleRules"
                required
              ></v-text-field>
            </v-col>
            
            <v-col cols="12" md="6">
              <v-text-field
                v-model="itemSlug"
                label="Slug"
                variant="outlined"
                density="comfortable"
                hint="Short identifier (auto-generated from title if empty)"
                persistent-hint
              ></v-text-field>
            </v-col>
            
            <v-col cols="12" md="6">
              <v-text-field
                v-model="itemDuration"
                label="Duration"
                variant="outlined"
                density="comfortable"
                placeholder="MM:SS or HH:MM:SS"
                hint="Expected duration"
                persistent-hint
                :rules="durationRules"
              ></v-text-field>
            </v-col>
            
            <v-col cols="12">
              <v-textarea
                v-model="itemDescription"
                label="Description"
                variant="outlined"
                density="comfortable"
                rows="3"
                auto-grow
              ></v-textarea>
            </v-col>
            
            <!-- Type-specific fields -->
            <v-col cols="12" v-if="itemType === 'segment'">
              <v-text-field
                v-model="itemGuests"
                label="Guests"
                variant="outlined"
                density="comfortable"
                hint="Comma-separated list of guests"
                persistent-hint
              ></v-text-field>
            </v-col>
            
            <v-col cols="12" v-if="itemType === 'ad'">
              <v-text-field
                v-model="itemCustomer"
                label="Customer Name"
                variant="outlined"
                density="comfortable"
              ></v-text-field>
            </v-col>
            
            <v-col cols="12" v-if="itemType === 'cta'">
              <v-text-field
                v-model="itemLink"
                label="Link URL"
                variant="outlined"
                density="comfortable"
                placeholder="https://..."
                :rules="linkRules"
              ></v-text-field>
            </v-col>
          </v-row>
        </v-form>
        
        <!-- Item Preview -->
        <v-divider class="my-4"></v-divider>
        <v-row v-if="itemType">
          <v-col cols="12">
            <h4 class="text-subtitle-1 mb-2">Preview</h4>
            <v-card outlined class="pa-2">
              <div class="d-flex align-center">
                <v-chip 
                  :color="getItemTypeColor(itemType)" 
                  size="small" 
                  class="mr-2"
                >
                  {{ itemType.toUpperCase() }}
                </v-chip>
                <strong>{{ itemTitle || 'Untitled Item' }}</strong>
                <v-spacer></v-spacer>
                <small class="text-medium-emphasis">{{ itemDuration || '00:00' }}</small>
              </div>
              <p v-if="itemDescription" class="text-caption mt-1 mb-0">{{ itemDescription }}</p>
              
              <!-- Type-specific preview info -->
              <div v-if="itemType === 'segment' && itemGuests" class="text-caption text-medium-emphasis mt-1">
                Guests: {{ itemGuests }}
              </div>
              <div v-if="itemType === 'ad' && itemCustomer" class="text-caption text-medium-emphasis mt-1">
                Customer: {{ itemCustomer }}
              </div>
              <div v-if="itemType === 'cta' && itemLink" class="text-caption text-medium-emphasis mt-1">
                Link: {{ itemLink }}
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn 
          color="primary" 
          @click="submit"
          :disabled="!formValid"
          :loading="loading"
        >
          Create Item
        </v-btn>
        <v-btn color="secondary" @click="cancel">Cancel</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'NewItemModal',
  emits: ['update:show', 'submit'],
  props: {
    show: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    },
    rundownItemTypes: {
      type: Array,
      default: () => [
        { title: 'Opening', value: 'opening' },
        { title: 'Segment', value: 'segment' },
        { title: 'Commercial Break', value: 'ad' },
        { title: 'Interview', value: 'interview' },
        { title: 'Music', value: 'music' },
        { title: 'Call to Action', value: 'cta' },
        { title: 'Closing', value: 'closing' },
        { title: 'Outro', value: 'outro' }
      ]
    }
  },
  data() {
    return {
      formValid: false,
      itemType: '',
      itemTitle: '',
      itemSlug: '',
      itemDuration: '',
      itemDescription: '',
      itemGuests: '',
      itemCustomer: '',
      itemLink: '',
      titleRules: [
        v => !!v || 'Title is required',
        v => (v && v.length >= 3) || 'Title must be at least 3 characters'
      ],
      durationRules: [
        v => !v || /^\d{1,2}:\d{2}(:\d{2})?$/.test(v) || 'Duration must be in MM:SS or HH:MM:SS format'
      ],
      linkRules: [
        v => !v || /^https?:\/\/.+/.test(v) || 'Link must be a valid URL starting with http:// or https://'
      ]
    }
  },
  methods: {
    getItemTypeColor(type) {
      const colorMap = {
        opening: 'green',
        segment: 'blue',
        ad: 'orange',
        interview: 'purple',
        music: 'teal',
        cta: 'red',
        closing: 'indigo',
        outro: 'brown'
      }
      return colorMap[type] || 'grey'
    },
    submit() {
      const item = {
        type: this.itemType,
        title: this.itemTitle,
        slug: this.itemSlug || this.generateSlug(this.itemTitle),
        duration: this.itemDuration,
        description: this.itemDescription,
        guests: this.itemGuests,
        customer: this.itemCustomer,
        link: this.itemLink
      }
      this.$emit('submit', item)
      this.reset()
    },
    cancel() {
      this.$emit('update:show', false)
      this.reset()
    },
    reset() {
      this.itemType = ''
      this.itemTitle = ''
      this.itemSlug = ''
      this.itemDuration = ''
      this.itemDescription = ''
      this.itemGuests = ''
      this.itemCustomer = ''
      this.itemLink = ''
      this.formValid = false
    },
    generateSlug(title) {
      return title
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .trim()
    }
  },
  watch: {
    show(newVal) {
      if (!newVal) {
        this.reset()
      }
    }
  }
}
</script>
