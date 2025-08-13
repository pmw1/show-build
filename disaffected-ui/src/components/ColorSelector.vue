<template>
  <div class="color-selector" :class="{ 'compact': compact }">
    <!-- Container for side-by-side layout -->
    <div class="color-tables-container">
      <!-- Rundown Items Table -->
      <div class="color-table-section">
        <h2 v-if="!compact" class="section-title">Rundown Item Colors</h2>
        <h3 v-else class="text-subtitle-2 mb-2">Rundown Item Colors</h3>
        <table class="color-config-table">
          <thead>
            <tr>
              <th class="type-header">Type</th>
              <th class="color-header">Base Color</th>
              <th class="color-header">Variant</th>
              <th class="preview-header">Preview</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="type in rundownTypes" :key="type">
              <td class="type-cell">{{ type }}</td>
              <td class="color-cell">
                <v-select
                  v-model="baseColor[type]"
                  :items="baseColorOptions"
                  dense
                  outlined
                  hide-details
                  class="cell-fill-select"
              @change="onBaseChange(type)"
              item-title="title"
              item-value="value"
            >
              <template #item="{ item, props }">
                <v-list-item v-if="item && item.value" v-bind="props">
                  <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(item.value), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                  <span>{{ item.title }}</span>
                </v-list-item>
              </template>
              <template #selection="{ item }">
                <div class="color-swatch-container" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(item.value), $vuetify), width: '100%', height: '28px', display: 'inline-block', borderRadius: '2px', position: 'relative' }">
                  <span class="color-label-overlay" :style="{ color: getTextColor(resolveVuetifyColor(vuetifyColorNameToThemeKey(item.value), $vuetify)) }">{{ item.title }}</span>
                </div>
              </template>
            </v-select>
              </td>
              <td class="color-cell">
                <v-select
                  v-model="variant[type]"
                  :items="variantOptions(baseColor[type])"
                  dense
                  outlined
                  hide-details
                  class="cell-fill-select"
              :disabled="!baseColor[type]"
            >
              <template #item="{ item, props }">
                <v-list-item v-if="item" v-bind="props">
                  <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor((baseColor[type] || '') + (item.value ? '-' + item.value : ''), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                  <span>{{ item.title }}</span>
                </v-list-item>
              </template>
              <template #selection="{ item }">
                <div class="color-swatch-container" :style="{ backgroundColor: resolveVuetifyColor((baseColor[type] || '') + (item.value ? '-' + item.value : ''), $vuetify), width: '100%', height: '28px', display: 'inline-block', borderRadius: '2px', position: 'relative' }">
                  <span class="color-label-overlay" :style="{ color: getTextColor(resolveVuetifyColor((baseColor[type] || '') + (item.value ? '-' + item.value : ''), $vuetify)) }">{{ item.title }}</span>
                </div>
              </template>
            </v-select>
              </td>
              <td class="preview-cell">
                <div 
                  class="preview-box-fill" 
                  :style="{
                    backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(getFullColor(type)), $vuetify),
                    color: getTextColor(resolveVuetifyColor(vuetifyColorNameToThemeKey(getFullColor(type)), $vuetify))
                  }"
                >
                  {{ type }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Interface Elements Table -->
      <div class="color-table-section">
        <h2 v-if="!compact" class="section-title">Rundown Action Colors</h2>
        <h3 v-else class="text-subtitle-2 mb-2">Rundown Action Colors</h3>
        <table class="color-config-table">
          <thead>
            <tr>
              <th class="type-header">Type</th>
              <th class="color-header">Base Color</th>
              <th class="color-header">Variant</th>
              <th class="preview-header">Preview</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="type in interfaceTypes" :key="type">
              <td class="type-cell">{{ type }}</td>
              <td class="color-cell">
                <v-select
                  v-model="baseColor[type + '-interface']"
                  :items="baseColorOptions"
                  dense
                  outlined
                  hide-details
                  class="cell-fill-select"
                  @change="onBaseChange(type + '-interface')"
                  item-title="title"
                  item-value="value"
                >
                  <template #item="{ item, props }">
                    <v-list-item v-if="item && item.value" v-bind="props">
                      <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(item.value), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                      <span>{{ item.title }}</span>
                    </v-list-item>
                  </template>
                  <template #selection="{ item }">
                    <div class="color-swatch-container" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(item.value), $vuetify), width: '100%', height: '28px', display: 'inline-block', borderRadius: '2px', position: 'relative' }">
                  <span class="color-label-overlay" :style="{ color: getTextColor(resolveVuetifyColor(vuetifyColorNameToThemeKey(item.value), $vuetify)) }">{{ item.title }}</span>
                </div>
                  </template>
                </v-select>
              </td>
              <td class="color-cell">
                <v-select
                  v-model="variant[type + '-interface']"
                  :items="variantOptions(baseColor[type + '-interface'])"
                  dense
                  outlined
                  hide-details
                  class="cell-fill-select"
                  :disabled="!baseColor[type + '-interface']"
                >
                  <template #item="{ item, props }">
                    <v-list-item v-if="item && item.value" v-bind="props">
                      <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor((baseColor[type + '-interface'] || '') + (item.value ? '-' + item.value : ''), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                      <span>{{ item.title }}</span>
                    </v-list-item>
                  </template>
                  <template #selection="{ item }">
                    <div class="color-swatch-container" :style="{ backgroundColor: resolveVuetifyColor((baseColor[type + '-interface'] || '') + (item.value ? '-' + item.value : ''), $vuetify), width: '100%', height: '28px', display: 'inline-block', borderRadius: '2px', position: 'relative' }">
                  <span class="color-label-overlay" :style="{ color: getTextColor(resolveVuetifyColor((baseColor[type + '-interface'] || '') + (item.value ? '-' + item.value : ''), $vuetify)) }">{{ item.title }}</span>
                </div>
                  </template>
                </v-select>
              </td>
              <td class="preview-cell">
                <div 
                  class="preview-box-fill" 
                  :style="{
                    backgroundColor: resolveVuetifyColor((baseColor[type + '-interface'] || '') + (variant[type + '-interface'] ? '-' + variant[type + '-interface'] : ''), $vuetify),
                    color: getTextColor(resolveVuetifyColor((baseColor[type + '-interface'] || '') + (variant[type + '-interface'] ? '-' + variant[type + '-interface'] : ''), $vuetify))
                  }"
                >
                  {{ type }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Status Colors Table (third column) -->
      <div class="color-table-section">
        <h2 v-if="!compact" class="section-title">Status Colors</h2>
        <h3 v-else class="text-subtitle-2 mb-2">Status Colors</h3>
        <table class="color-config-table">
          <thead>
            <tr>
              <th class="type-header">Status</th>
              <th class="color-header">Base Color</th>
              <th class="color-header">Variant</th>
              <th class="preview-header">Preview</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="type in scriptStatusTypes" :key="type">
              <td class="type-cell">{{ type }}</td>
              <td class="color-cell">
                <v-select
                  v-model="baseColor[type + '-script']"
                  :items="baseColorOptions"
                  dense
                  outlined
                  hide-details
                  class="cell-fill-select"
                  @change="onBaseChange(type + '-script')"
                  item-title="title"
                  item-value="value"
                >
                  <template #item="{ item, props }">
                    <v-list-item v-if="item && item.value" v-bind="props">
                      <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(item.value), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                      <span>{{ item.title }}</span>
                    </v-list-item>
                  </template>
                  <template #selection="{ item }">
                    <div class="color-swatch-container" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(item.value), $vuetify), width: '100%', height: '28px', display: 'inline-block', borderRadius: '2px', position: 'relative' }">
                  <span class="color-label-overlay" :style="{ color: getTextColor(resolveVuetifyColor(vuetifyColorNameToThemeKey(item.value), $vuetify)) }">{{ item.title }}</span>
                </div>
                  </template>
                </v-select>
              </td>
              <td class="color-cell">
                <v-select
                  v-model="variant[type + '-script']"
                  :items="variantOptions(baseColor[type + '-script'])"
                  dense
                  outlined
                  hide-details
                  class="cell-fill-select"
                  :disabled="!baseColor[type + '-script']"
                >
                  <template #item="{ item, props }">
                    <v-list-item v-if="item && item.value" v-bind="props">
                      <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor((baseColor[type + '-script'] || '') + (item.value ? '-' + item.value : ''), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                      <span>{{ item.title }}</span>
                    </v-list-item>
                  </template>
                  <template #selection="{ item }">
                    <div class="color-swatch-container" :style="{ backgroundColor: resolveVuetifyColor((baseColor[type + '-script'] || '') + (item.value ? '-' + item.value : ''), $vuetify), width: '100%', height: '28px', display: 'inline-block', borderRadius: '2px', position: 'relative' }">
                  <span class="color-label-overlay" :style="{ color: getTextColor(resolveVuetifyColor((baseColor[type + '-script'] || '') + (item.value ? '-' + item.value : ''), $vuetify)) }">{{ item.title }}</span>
                </div>
                  </template>
                </v-select>
              </td>
              <td class="preview-cell">
                <div 
                  class="preview-box-fill" 
                  :style="{
                    backgroundColor: resolveVuetifyColor((baseColor[type + '-script'] || '') + (variant[type + '-script'] ? '-' + variant[type + '-script'] : ''), $vuetify),
                    color: getTextColor(resolveVuetifyColor((baseColor[type + '-script'] || '') + (variant[type + '-script'] ? '-' + variant[type + '-script'] : ''), $vuetify))
                  }"
                >
                  {{ type }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Save Button -->
    <v-btn
      v-if="!hideSaveButton"
      color="primary"
      class="mt-4"
      @click="saveColors"
      :loading="isSaving"
    >
      Save Color Configuration
    </v-btn>

    <!-- Add Confirmation Dialog -->
    <v-dialog
      v-model="showConfirmation"
      width="300"
    >
      <v-card>
        <v-card-title class="text-h6">
          Colors Saved
        </v-card-title>
        <v-card-text>
          Color configuration has been updated successfully.
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            variant="text"
            @click="showConfirmation = false"
          >
            Close
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { resolveVuetifyColor, updateColor, getColorValue } from '../utils/themeColorMap';
import { debounce } from 'lodash-es';

export default {
  emits: ['colors-changed', 'colors-saved'],
  props: {
    compact: {
      type: Boolean,
      default: false
    },
    hideSaveButton: {
      type: Boolean,
      default: false
    }
  },
  data() {
    // Initialize with all possible types for reactivity
    const allTypes = [
      'segment', 'ad', 'promo', 'cta', 'trans',
      'Selection-interface', 'Hover-interface', 'Highlight-interface', 
      'Dropline-interface', 'DragLight-interface',
      'Draft-script', 'Approved-script', 'Production-script', 'Completed-script'
    ];
    
    const baseColor = {};
    const variant = {};
    
    // Initialize all types to ensure reactivity
    allTypes.forEach(type => {
      baseColor[type] = null;
      variant[type] = null;
    });
    
    return {
      rundownTypes: ['segment', 'ad', 'promo', 'cta', 'trans', 'pkg', 'vo', 'sot', 'interview', 'live', 'break', 'tease', 'tag', 'bump', 'music', 'reader'],
      interfaceTypes: ['Selection', 'Hover', 'Highlight', 'Dropline', 'DragLight'],
      scriptStatusTypes: ['Draft', 'Approved', 'Production', 'Completed'],
      typeColors: {},
      showConfirmation: false,
      isSaving: false,
      baseColor,
      variant,
      isInitializing: true, // Flag to prevent watcher events during initialization
    }
  },
  computed: {
    themeColors() {
      const theme = this.$vuetify?.theme?.themes?.light;
      return theme ? Object.keys(theme.colors || {}) : [];
    },
    baseColorOptions() {
      // Official Vuetify Material Design color palette
      const materialColors = [
        'red', 'pink', 'purple', 'deep-purple', 'indigo', 'blue', 
        'light-blue', 'cyan', 'teal', 'green', 'light-green', 'lime',
        'yellow', 'amber', 'orange', 'deep-orange', 'brown', 
        'blue-grey', 'grey', 'black', 'white'
      ];
      
      return materialColors.map(color => ({
        title: color.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        value: color,
      }));
    },
    variantOptions() {
      // Returns a function to get variant options for a base color
      return (baseColor) => {
        if (!baseColor) return [{ title: 'Base', value: '' }];
        
        const variants = [
          { title: 'Base', value: '' }
        ];
        
        // Add lighten variants (lighten-5 to lighten-1)
        for (let i = 5; i >= 1; i--) {
          variants.push({ title: `Lighten ${i}`, value: `lighten-${i}` });
        }
        
        // Add darken variants (darken-1 to darken-4)  
        for (let i = 1; i <= 4; i++) {
          variants.push({ title: `Darken ${i}`, value: `darken-${i}` });
        }
        
        // Add accent variants (accent-1 to accent-4) - not available for all colors
        const accentColors = ['red', 'pink', 'purple', 'deep-purple', 'indigo', 'blue', 
                             'light-blue', 'cyan', 'teal', 'green', 'light-green', 'lime',
                             'yellow', 'amber', 'orange', 'deep-orange'];
        
        if (accentColors.includes(baseColor)) {
          for (let i = 1; i <= 4; i++) {
            variants.push({ title: `Accent ${i}`, value: `accent-${i}` });
          }
        }
        
        return variants;
      };
    },
  },
  methods: {
    getRundownTypeValues() {
      // Hardcoded rundown types to avoid circular import issues
      return ['segment', 'ad', 'promo', 'cta', 'trans', 'pkg', 'vo', 'sot', 'interview', 'live', 'break', 'tease', 'tag', 'bump', 'music', 'reader'];
    },
    resolveVuetifyColor,
    parseColorValue(colorValue) {
      if (!colorValue) return { base: null, variant: null };
      
      // Known variant patterns to look for at the end (order matters - check longer patterns first)
      const variantPatterns = [
        'lighten-5', 'lighten-4', 'lighten-3', 'lighten-2', 'lighten-1',
        'darken-4', 'darken-3', 'darken-2', 'darken-1',
        'accent-4', 'accent-3', 'accent-2', 'accent-1', 'accent',
        'base', 'dark', 'light'
      ];
      
      // Try to find a variant pattern at the end
      for (const pattern of variantPatterns) {
        if (colorValue.endsWith('-' + pattern)) {
          const base = colorValue.slice(0, -(pattern.length + 1));
          return { base, variant: pattern };
        }
      }
      
      // No variant found, entire string is the base color
      return { base: colorValue, variant: '' };
    },
    vuetifyColorNameToThemeKey(name) {
      if (!name) return '';
      const parts = name.toLowerCase().split(' ');
      const base = parts[0];
      const variant = parts.length > 1 ? parts.slice(1).join('-') : '';
      return variant ? `${base}-${variant}` : base;
    },
    onBaseChange(type) {
      // When base color changes, reset the variant to empty string (Base)
      this.variant[type] = '';
    },
    getFullColor(type) {
      const base = this.baseColor[type];
      const variant = this.variant[type];
      if (!base) return null;
      return variant ? `${base}-${variant}` : base;
    },
    getTextColor(bgColor) {
      // Basic logic to determine if text should be black or white
      if (!bgColor) return '#000000';
      const color = (bgColor.charAt(0) === '#') ? bgColor.substring(1, 7) : bgColor;
      const r = parseInt(color.substring(0, 2), 16);
      const g = parseInt(color.substring(2, 4), 16);
      const b = parseInt(color.substring(4, 6), 16);
      return (((r * 0.299) + (g * 0.587) + (b * 0.114)) > 186) ? '#000000' : '#FFFFFF';
    },
    async initializeColors() {
      const allTypes = [
        ...this.rundownTypes,
        ...this.interfaceTypes.map(t => t + '-interface'),
        ...this.scriptStatusTypes.map(t => t + '-script'),
      ];

      // Load from database (new endpoint)
      try {
        const response = await fetch('/api/settings/colors?profile=default', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
          }
        });
        
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.colors) {
            const dbColors = data.colors;
            
            // Apply database colors
            allTypes.forEach(type => {
              let lookupKey = type;
              
              // Map interface and script types to their base color keys
              if (type.endsWith('-interface')) {
                const baseType = type.replace('-interface', '').toLowerCase();
                // Map interface types to their base colors
                const interfaceMapping = {
                  'selection': 'selection',
                  'hover': 'hover', 
                  'highlight': 'highlight',
                  'dropline': 'dropline',
                  'draglight': 'draglight'
                };
                lookupKey = interfaceMapping[baseType] || baseType;
              } else if (type.endsWith('-script')) {
                const baseType = type.replace('-script', '').toLowerCase();
                // Map script status types to their base colors  
                const scriptMapping = {
                  'draft': 'draft',
                  'approved': 'approved',
                  'production': 'production', 
                  'completed': 'completed'
                };
                lookupKey = scriptMapping[baseType] || baseType;
              }
              
              const colorValue = dbColors[lookupKey];
              if (colorValue) {
                const parsed = this.parseColorValue(colorValue);
                // Set the reactive properties (Vue 3 compatible)
                this.baseColor[type] = parsed.base || null;
                this.variant[type] = parsed.variant || '';
                // Update local storage as backup
                updateColor(type, colorValue);
              }
            });
            
            // Set initialization complete
            this.$nextTick(() => {
              this.isInitializing = false;
            });
            return; // Exit early if database load succeeds
          }
        }
      } catch (error) {
        // Fallback to localStorage if database fails
      }

      // Fallback to local storage if database fails
      allTypes.forEach(type => {
        if (!this.baseColor[type]) {
          let lookupKey = type;
          
          // Map interface and script types to their base color keys
          if (type.endsWith('-interface')) {
            const baseType = type.replace('-interface', '').toLowerCase();
            const interfaceMapping = {
              'selection': 'selection',
              'hover': 'hover', 
              'highlight': 'highlight',
              'dropline': 'dropline',
              'draglight': 'draglight'
            };
            lookupKey = interfaceMapping[baseType] || baseType;
          } else if (type.endsWith('-script')) {
            const baseType = type.replace('-script', '').toLowerCase();
            const scriptMapping = {
              'draft': 'draft',
              'approved': 'approved',
              'production': 'production', 
              'completed': 'completed'
            };
            lookupKey = scriptMapping[baseType] || baseType;
          }
          
          const colorValue = getColorValue(lookupKey); // Get color from local storage using mapped key
          if (colorValue) {
            // localStorage might use space or dash format, try both
            const spaceParts = colorValue.split(' ');
            if (spaceParts.length > 1) {
              // Space format: "blue lighten-4"
              this.baseColor[type] = spaceParts[0] || null;
              this.variant[type] = spaceParts[1] || null;
            } else {
              // Dash format: "blue-lighten-4"
              const parsed = this.parseColorValue(colorValue);
              this.baseColor[type] = parsed.base;
              this.variant[type] = parsed.variant;
            }
          } else {
            this.baseColor[type] = null;
            this.variant[type] = null;
          }
        }
      });
      
      // Set initialization complete for fallback case too
      this.$nextTick(() => {
        this.isInitializing = false;
      });
    },
    saveColors: debounce(async function () {
      this.isSaving = true;
      const allTypes = [
        ...this.rundownTypes,
        ...this.interfaceTypes.map(t => t + '-interface'),
        ...this.scriptStatusTypes.map(t => t + '-script'),
      ];

      // Build colors object
      const colors = {};
      allTypes.forEach(type => {
        const fullColor = this.getFullColor(type);
        if (fullColor) {
          colors[type] = fullColor;
          updateColor(type, fullColor); // Update local storage as backup
          
          // For script status types, also save base keys for content editor
          if (type.endsWith('-script')) {
            const baseKey = type.replace('-script', '').toLowerCase();
            colors[baseKey] = fullColor;
            updateColor(baseKey, fullColor);
          }
        }
      });

      // Save to database (new endpoint with profile support)
      try {
        const token = localStorage.getItem('auth-token');
        
        const response = await fetch('/api/settings/colors', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ 
            colors, 
            category: 'colors', 
            profile: 'default' 
          })
        });

        if (response.ok) {
          await response.json();
          this.isSaving = false;
          this.showConfirmation = true;
          this.$emit('colors-saved');
        } else {
          const errorText = await response.text();
          console.error('Failed to save colors to database. Response:', response.status, errorText);
          alert(`Failed to save colors: ${response.status} - ${errorText}`);
          this.isSaving = false;
        }
      } catch (error) {
        console.error('Error saving colors:', error);
        alert(`Error saving colors: ${error.message}`);
        this.isSaving = false;
      }
    }, 1000),
  },
  created() {
    this.initializeColors();
  },
  mounted() {
    // this.initializeColors();
  },
  watch: {
    baseColor: {
      handler(_newVal, _oldVal) {
        if (this.isInitializing) {
          return;
        }
        this.$emit('colors-changed');
      },
      deep: true
    },
    variant: {
      handler(_newVal, _oldVal) {
        if (this.isInitializing) {
          return;
        }
        this.$emit('colors-changed');
      },
      deep: true
    }
  },
};
</script>

<style scoped>
.color-selector {
  padding: 1rem;
  background-color: #f5f5f5;
  color: #333;
}

/* Container for three-column layout */
.color-tables-container {
  display: flex;
  gap: 15px;
  flex-wrap: nowrap; /* Prevent wrapping to ensure inline layout */
}

/* Each table section takes up ~32% width for three columns */
.color-table-section {
  flex: 1;
  min-width: 30%;
  max-width: 32%;
}

/* Remove script status section styling since it's now inline */

/* Section titles - smaller than main expansion panel title */
.section-title {
  font-size: 1.0rem;
  font-weight: 500;
  margin-bottom: 12px;
  color: #333;
  border-bottom: 2px solid #ddd;
  padding-bottom: 8px;
}

/* Table styling */
.color-config-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Table headers - increased 20% from 0.6rem and left aligned */
.color-config-table th {
  padding: 0 0 0 8px;
  border: 1px solid #ddd;
  background-color: #f0f0f0;
  font-size: 0.72rem; /* 20% increase from 0.6rem */
  font-weight: 600;
  text-align: left;
  height: 36px;
  text-transform: uppercase;
}

/* Type column - right-aligned with reduced font size */
.type-cell {
  text-align: right;
  font-size: 0.76rem; /* 20% smaller than 0.95rem */
  font-weight: 500;
  padding: 0 8px 0 0; /* Right padding only for text alignment */
  border: 1px solid #ddd;
  height: 36px;
  vertical-align: middle;
}

/* Color cells - completely fill cell with no padding/margin */
.color-cell {
  padding: 0;
  margin: 0;
  border: 1px solid #ddd;
  height: 36px;
  position: relative;
  overflow: hidden;
  vertical-align: top;
  line-height: 0;
}

/* Ensure the cell content takes full width and height */
.color-cell > * {
  width: 100%;
  height: 100%;
  display: block;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  line-height: 0;
}

/* Preview cell - completely fill cell with no padding/margin */
.preview-cell {
  padding: 0;
  margin: 0;
  border: 1px solid #ddd;
  height: 36px;
  overflow: hidden;
  vertical-align: top;
  line-height: 0;
  position: relative;
}

/* Ensure preview cell content takes full space */
.preview-cell > * {
  width: 100%;
  height: 100%;
  display: block;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  line-height: 0;
}

/* Select dropdowns that completely fill the cell */
.cell-fill-select {
  width: 100%;
  height: 36px;
  margin: 0;
  padding: 0;
  font-size: 0.66rem; /* 10% larger than 0.6rem */
}

.cell-fill-select :deep(.v-input) {
  width: 100%;
  height: 36px;
  margin: 0;
  padding: 0;
  min-height: 36px;
}

.cell-fill-select :deep(.v-field) {
  width: 100%;
  height: 36px;
  border-radius: 0;
  border: none;
  margin: 0;
  padding: 0;
  min-height: 36px;
  font-size: 0.66rem; /* 10% larger than 0.6rem */
  background: white;
}

.cell-fill-select :deep(.v-field__field) {
  width: 100%;
  height: 36px;
  padding: 0;
  margin: 0;
  min-height: 36px;
}

.cell-fill-select :deep(.v-field__input) {
  width: 100%;
  height: 36px;
  padding: 0;
  min-height: 36px;
  font-size: 0.66rem; /* 10% larger than 0.6rem */
  display: flex;
  align-items: center;
  margin: 0;
}

.cell-fill-select :deep(.v-field__append-inner) {
  height: 36px;
  padding: 0 !important;
  margin: 0 !important;
  display: flex;
  align-items: center;
  min-width: 20px;
  max-width: 20px;
  width: 20px;
  flex-shrink: 0;
}

.cell-fill-select :deep(.v-field__outline) {
  display: none;
}

.cell-fill-select :deep(.v-input__control) {
  width: 100%;
  height: 36px;
  margin: 0;
  padding: 0;
  min-height: 36px;
}

.cell-fill-select :deep(.v-input__details) {
  display: none;
}

.cell-fill-select :deep(.v-field__prepend-inner),
.cell-fill-select :deep(.v-field__clearable) {
  padding: 0;
  margin: 0;
}

.cell-fill-select :deep(.v-select__selection) {
  padding: 0 !important;
  margin: 0 !important;
  width: 100% !important;
  max-width: 100% !important;
  min-width: 100% !important;
  flex: 1 1 100% !important;
  display: flex !important;
  align-items: center !important;
  overflow: visible !important;
}

.cell-fill-select :deep(.v-select__selection-text) {
  width: 100% !important;
  flex: 1 !important;
}

/* Force color swatch container to expand completely */
.cell-fill-select :deep(.v-field__field) {
  width: 100% !important;
  max-width: 100% !important;
}

.cell-fill-select :deep(.v-field__input) {
  width: 100% !important;
  max-width: 100% !important;
  flex: 1 !important;
}

/* Override any Vuetify chip constraints */
.cell-fill-select :deep(.v-chip) {
  width: 100% !important;
  max-width: 100% !important;
}

/* Target the color swatch specifically */
.cell-fill-select :deep(.color-swatch) {
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
}

/* Color swatch container with overlay label */
.cell-fill-select :deep(.color-swatch-container) {
  width: 100% !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
  position: relative !important;
}

/* Overlay label positioning and styling */
.cell-fill-select :deep(.color-label-overlay) {
  position: absolute !important;
  top: 50% !important;
  left: 50% !important;
  transform: translate(-50%, -50%) !important;
  font-size: 0.605rem !important; /* 10% larger than 0.55rem */
  font-weight: 600 !important;
  text-shadow: 1px 1px 1px rgba(0,0,0,0.5), -1px -1px 1px rgba(255,255,255,0.5) !important;
  white-space: nowrap !important;
  pointer-events: none !important;
  z-index: 10 !important;
}

.cell-fill-select :deep(.v-chip) {
  margin: 0;
  padding: 0 2px;
}

.cell-fill-select :deep(.v-input__icon) {
  width: 16px;
  height: 16px;
  margin: 0 !important;
  padding: 0 !important;
}

.cell-fill-select :deep(.v-icon) {
  width: 16px !important;
  height: 16px !important;
  margin: 0 !important;
  padding: 0 !important;
  font-size: 16px !important;
}

/* Override any scoped CSS margins from other components */
.cell-fill-select :deep([data-v-615c7762]) {
  margin: 0 !important;
  padding: 0 !important;
}

/* Generic override for any scoped CSS data attributes */
.cell-fill-select :deep([class*="data-v-"]) {
  margin: 0 !important;
}

.cell-fill-select :deep(*[data-v-615c7762]) {
  margin: 0 !important;
  padding: 0 !important;
}

/* Preview box that completely fills the entire cell */
.preview-box-fill {
  width: 100%;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.704rem; /* 10% larger than 0.64rem */
  margin: 0;
  padding: 0;
  border: none;
  box-sizing: border-box;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  line-height: 1;
}

.compact th, 
.compact td {
  padding: 4px 6px;
  font-size: 0.875rem;
}

th {
  background-color: #2a2a2a;
}

.preview-box {
  padding: 4px 8px;
  border-radius: 4px;
  text-align: center;
  font-weight: bold;
  width: 100px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #000;
}

.compact .preview-box {
  width: 80px;
  height: 24px;
  font-size: 0.75rem;
  padding: 2px 6px;
}

.color-swatch {
  width: 20px;
  height: 20px;
  display: inline-block;
  margin-right: 8px;
  border-radius: 3px;
  border: 1px solid #555;
}

.compact .color-swatch {
  width: 16px;
  height: 16px;
  margin-right: 4px;
}

.compact :deep(.v-select) {
  font-size: 0.875rem;
}

.compact :deep(.v-field__input) {
  font-size: 0.875rem;
  min-height: 28px !important;
}
</style>
