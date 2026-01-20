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
import { getAllItemTypes, mergeWithCustomTypes } from '@/config/itemTypes.js';

export default {
  name: 'NewItemModal',
  emits: ['update:show', 'submit', 'open-library-picker'],
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
      dynamicColors: {},
      typeSettings: {},  // Content type settings (is_reusable flag)
      customTypesLoaded: false
    }
  },
  computed: {
    allTypes() {
      // Get all item types (core + custom) from the merged type system
      const types = getAllItemTypes();
      // Map to display format with dynamic colors
      return types.map(type => ({
        title: type.title,
        value: type.value,
        color: this.getTypeColor(type.value) || type.color,
        icon: type.icon,
        isCore: type.isCore,
        isReusable: type.isReusable || false
      }));
    }
  },
  async mounted() {
    // Add ESC key listener to document
    document.addEventListener('keydown', this.handleKeydown);

    // Load dynamic colors and type settings in parallel
    await Promise.all([
      this.loadDynamicColors(),
      this.loadTypeSettings()
    ]);
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

    async loadTypeSettings() {
      try {
        console.log('Loading content type settings for NewItemModal');
        const response = await fetch('/api/content-library/type-settings/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.settings) {
            // Convert array to object keyed by type_name
            this.typeSettings = {};
            data.settings.forEach(setting => {
              this.typeSettings[setting.type_name] = setting;
            });
            console.log('Type settings loaded:', this.typeSettings);

            // Load custom types (is_core=false) and merge them into the type system
            await this.loadCustomTypes();
          }
        }
      } catch (error) {
        console.log('Could not load type settings (content library may not be set up):', error);
        // This is fine - content library is optional
      }
    },

    async loadCustomTypes() {
      try {
        console.log('Loading custom types for NewItemModal');
        const response = await fetch('/api/content-library/custom-types/', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          if (data.custom_types && data.custom_types.length > 0) {
            // Merge custom types into the global type system
            mergeWithCustomTypes(data.custom_types);
            this.customTypesLoaded = true;
            console.log('Custom types merged:', data.custom_types.length, 'types');
            // Force computed property to re-evaluate
            this.$forceUpdate();
          }
        }
      } catch (error) {
        console.log('Could not load custom types:', error);
      }
    },

    isTypeReusable(typeValue) {
      // Map UI type values to backend type names
      const typeMapping = {
        'ad': 'advertisement',
        'coldopen': 'coldopen',
        'tease': 'tease',
        'segment': 'segment',
        'promo': 'promo',
        'reader': 'reader',
        'cta': 'cta',
        'interview': 'interview'
      };
      const backendType = typeMapping[typeValue] || typeValue;
      const setting = this.typeSettings[backendType];
      return setting?.is_reusable || false;
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

      // Check if this type is configured as reusable
      if (this.isTypeReusable(type.value)) {
        console.log(`Type ${type.value} is reusable - opening library picker`);
        // Emit event to open library picker instead of creating directly
        this.$emit('open-library-picker', {
          itemType: type.value,
          displayName: type.title
        });
        this.cancel();
        return;
      }

      // Create item with basic defaults (for non-reusable types)
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