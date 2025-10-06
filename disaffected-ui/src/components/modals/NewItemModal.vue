<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-plus</v-icon>
        Select Rundown Item Type
        <v-spacer></v-spacer>
        <v-btn icon size="small" variant="text" @click="cancel">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-card-text>
        <p class="text-body-2 mb-4">Choose the type of rundown item to create:</p>
        
        <!-- All Rundown Item Types -->
        <div class="mb-4">
          <v-row>
            <v-col cols="6" sm="4" v-for="type in allTypes" :key="type.value">
              <v-btn
                @click="selectType(type)"
                :color="type.color"
                variant="elevated"
                block
                size="large"
                class="text-wrap"
                style="height: 80px;"
              >
                <div class="text-center">
                  <v-icon class="mb-1">{{ type.icon }}</v-icon>
                  <br>
                  <span class="text-caption">{{ type.title }}</span>
                </div>
              </v-btn>
            </v-col>
          </v-row>
        </div>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="secondary" @click="cancel">Cancel</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { getColorValue } from '@/utils/themeColorMap.js';

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
    }
  },
  data() {
    return {
      dynamicColors: {}
    }
  },
  computed: {
    allTypes() {
      // All essential broadcast rundown types with dynamic colors
      return [
        { title: 'Cold Open', value: 'coldopen', color: this.getTypeColor('coldopen'), icon: 'mdi-play-circle-outline' },
        { title: 'Tease', value: 'tease', color: this.getTypeColor('tease'), icon: 'mdi-eye-outline' },
        { title: 'Segment', value: 'segment', color: this.getTypeColor('segment'), icon: 'mdi-television-classic' },
        { title: 'Promo', value: 'promo', color: this.getTypeColor('promo'), icon: 'mdi-bullhorn' },
        { title: 'Advertisement', value: 'ad', color: this.getTypeColor('ad'), icon: 'mdi-currency-usd' },
        { title: 'Reader', value: 'reader', color: this.getTypeColor('reader'), icon: 'mdi-script-text' },
        { title: 'Call to Action', value: 'cta', color: this.getTypeColor('cta'), icon: 'mdi-hand-pointing-right' },
        { title: 'Interview', value: 'interview', color: this.getTypeColor('interview'), icon: 'mdi-account-voice' }
      ]
    }
  },
  async mounted() {
    // Add ESC key listener to document
    document.addEventListener('keydown', this.handleKeydown);
    
    // Load dynamic colors
    await this.loadDynamicColors();
  },
  beforeUnmount() {
    // Clean up ESC key listener
    document.removeEventListener('keydown', this.handleKeydown)
  },
  methods: {
    async loadDynamicColors() {
      try {
        console.log('Loading dynamic colors for NewItemModal');
        const response = await fetch('/api/settings/colors?profile=default');
        
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.colors) {
            this.dynamicColors = data.colors;
            console.log('Dynamic colors loaded:', this.dynamicColors);
          }
        }
      } catch (error) {
        console.log('Could not load dynamic colors, using defaults:', error);
      }
    },
    
    getTypeColor(type) {
      // Return dynamic color if available, otherwise use themeColorMap fallback
      return this.dynamicColors[type] || getColorValue(type);
    },
    
    handleKeydown(event) {
      // Handle ESC key when modal is open
      if (event.key === 'Escape' && this.show) {
        this.cancel()
      }
    },
    selectType(type) {
      console.log('Selected type:', type);
      
      // Create item with basic defaults
      const item = {
        type: type.value,
        title: type.value === 'tease' ? '' : type.title,  // Tease title should be empty initially
        subtitle: '',
        slug: type.value === 'coldopen' ? 'show-cold-open' : '',
        duration: type.value === 'coldopen' ? '00:00:45:00' : '00:00:00:00',  // Use hh:mm:ss:ff format
        description: '',
        airdate: '',  // Will be populated from info.md frontmatter
        priority: '',  // Empty as specified
        guests: '',
        tags: '',
        server_message: '',
        customer: '',
        link: '',
        status: 'draft'  // Default status
      };
      
      // Emit the item creation
      this.$emit('submit', item);
      
      // Close modal
      this.cancel();
    },
    cancel() {
      this.$emit('update:show', false);
    }
  }
}
</script>