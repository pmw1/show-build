<template>
  <div class="color-selector">
    <!-- Rundown Items Table -->
    <h2>Rundown Item Colors</h2>
    <table>
      <thead>
        <tr>
          <th>Type</th>
          <th>Color</th>
          <th>Preview</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="type in rundownTypes" :key="type">
          <td>{{ type }}</td>
          <td>
            <v-select
              v-model="typeColors[type]"
              :items="colorOptions"
              item-title="label"
              item-value="value"
              group-by="group"
              dense
              outlined
              hide-details
              @update:model-value="updateColor(type)"
            >
              <template #item="{ props, item }">
                <v-list-item v-bind="props" :title="null">
                  <template #prepend>
                    <span class="color-dot" :class="`bg-${item.raw.value}`"></span>
                  </template>
                  <v-list-item-title>{{ item.raw.label }}</v-list-item-title>
                </v-list-item>
              </template>
              <template #selection="{ item }">
                <span class="color-dot" :class="`bg-${item.raw.value}`"></span>
                {{ item.raw.label }}
              </template>
            </v-select>
          </td>
          <td>
            <div 
              class="preview-box" 
              :class="`bg-${typeColors[type]}`"
              :style="{ color: getTextColor(typeColors[type]) }"
            >
              {{ type }}
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Interface Elements Table -->
    <h2 class="mt-6">Interface Element Colors</h2>
    <table>
      <thead>
        <tr>
          <th>Type</th>
          <th>Color</th>
          <th>Preview</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="type in interfaceTypes" :key="type">
          <td>{{ type }}</td>
          <td>
            <v-select
              v-model="typeColors[type]"
              :items="colorOptions"
              item-title="label"
              item-value="value"
              group-by="group"
              dense
              outlined
              hide-details
              @update:model-value="updateColor(type)"
            >
              <template #item="{ props, item }">
                <v-list-item v-bind="props" :title="null">
                  <template #prepend>
                    <span class="color-dot" :class="`bg-${item.raw.value}`"></span>
                  </template>
                  <v-list-item-title>{{ item.raw.label }}</v-list-item-title>
                </v-list-item>
              </template>
              <template #selection="{ item }">
                <span class="color-dot" :class="`bg-${item.raw.value}`"></span>
                {{ item.raw.label }}
              </template>
            </v-select>
          </td>
          <td>
            <div class="preview-box" :class="`bg-${typeColors[type]}`"></div>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Save Button -->
    <v-btn
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
import { useTheme } from 'vuetify'
import { getColorValue, updateColor } from '../utils/themeColorMap'

export default {
  setup() {
    const theme = useTheme()
    return { theme }
  },
  data() {
    return {
      rundownTypes: ['Advert', 'CTA', 'Promo', 'Segment', 'Trans'],
      interfaceTypes: ['Highlight', 'Dropline', 'DragLight'],  // Added DragLight
      typeColors: {},
      showConfirmation: false,
      isSaving: false,
      colorOptions: [
        // Red family
        { label: 'Red', value: 'red-base', group: 'Red Colors' },
        { label: 'Red Accent', value: 'red-accent', group: 'Red Colors' },
        { label: 'Red Dark', value: 'red-dark', group: 'Red Colors' },
        { label: 'Red Light', value: 'red-light', group: 'Red Colors' },
        
        // Deep Purple family
        { label: 'Deep Purple', value: 'deep-purple-base', group: 'Deep Purple Colors' },
        { label: 'Deep Purple Accent', value: 'deep-purple-accent', group: 'Deep Purple Colors' },
        { label: 'Deep Purple Dark', value: 'deep-purple-dark', group: 'Deep Purple Colors' },
        { label: 'Deep Purple Light', value: 'deep-purple-light', group: 'Deep Purple Colors' },

        // Blue family
        { label: 'Blue', value: 'blue-base', group: 'Blue Colors' },
        { label: 'Blue Accent', value: 'blue-accent', group: 'Blue Colors' },
        { label: 'Blue Dark', value: 'blue-dark', group: 'Blue Colors' },
        { label: 'Blue Light', value: 'blue-light', group: 'Blue Colors' },

        // Indigo family
        { label: 'Indigo', value: 'indigo-base', group: 'Indigo Colors' },
        { label: 'Indigo Accent', value: 'indigo-accent', group: 'Indigo Colors' },
        { label: 'Indigo Dark', value: 'indigo-dark', group: 'Indigo Colors' },
        { label: 'Indigo Light', value: 'indigo-light', group: 'Indigo Colors' },

        // Teal family
        { label: 'Teal', value: 'teal-base', group: 'Teal Colors' },
        { label: 'Teal Accent', value: 'teal-accent', group: 'Teal Colors' },
        { label: 'Teal Dark', value: 'teal-dark', group: 'Teal Colors' },
        { label: 'Teal Light', value: 'teal-light', group: 'Teal Colors' },

        // Green family
        { label: 'Green', value: 'green-base', group: 'Green Colors' },
        { label: 'Green Accent', value: 'green-accent', group: 'Green Colors' },
        { label: 'Green Dark', value: 'green-dark', group: 'Green Colors' },
        { label: 'Green Light', value: 'green-light', group: 'Green Colors' },

        // Lime family
        { label: 'Lime', value: 'lime-base', group: 'Lime Colors' },
        { label: 'Lime Accent', value: 'lime-accent', group: 'Lime Colors' },
        { label: 'Lime Dark', value: 'lime-dark', group: 'Lime Colors' },
        { label: 'Lime Light', value: 'lime-light', group: 'Lime Colors' },

        // Yellow family
        { label: 'Yellow', value: 'yellow-base', group: 'Yellow Colors' },
        { label: 'Yellow Accent', value: 'yellow-accent', group: 'Yellow Colors' },
        { label: 'Yellow Dark', value: 'yellow-dark', group: 'Yellow Colors' },
        { label: 'Yellow Light', value: 'yellow-light', group: 'Yellow Colors' },

        // Grey family
        { label: 'Grey', value: 'grey-base', group: 'Grey Colors' },
        { label: 'Grey Accent', value: 'grey-accent', group: 'Grey Colors' },
        { label: 'Grey Dark', value: 'grey-dark', group: 'Grey Colors' },
        { label: 'Grey Light', value: 'grey-light', group: 'Grey Colors' }
      ]
    }
  },
  methods: {
    updateColor(type, newColor) {
      console.log("[DEBUG] ColorSelector updating:", { type, newColor });
      
      // Handle both direct calls and v-select updates
      const colorToApply = newColor || this.typeColors[type];
      
      if (colorToApply) {
        // Update color map and return result
        const result = updateColor(type.toLowerCase(), colorToApply);
        console.log("[DEBUG] Color update result:", { 
          type, 
          color: colorToApply, 
          success: result 
        });
        return result;
      }
    },
    
    async saveColors() {
      this.isSaving = true
      try {
        // Maybe add validation or API sync here
        console.log('Colors already saved in map')
        this.showConfirmation = true
      } finally {
        this.isSaving = false
      }
    },
    
    // Add this new method
    getTextColor(backgroundColor) {
      // Extract color values from background class
      const colorMap = {
        'light': '#ffffff',
        'dark': '#000000',
        'base': '#424242',
        'accent': '#212121'
      };
      
      const bgColor = colorMap[backgroundColor.split('-').pop()] || '#424242';
      
      // Calculate relative luminance
      const hex = bgColor.replace('#', '');
      const r = parseInt(hex.substr(0, 2), 16) / 255;
      const g = parseInt(hex.substr(2, 2), 16) / 255;
      const b = parseInt(hex.substr(4, 2), 16) / 255;
      const luminance = (0.299 * r + 0.587 * g + 0.114 * b);
      
      // Return white for dark backgrounds, black for light backgrounds
      return luminance > 0.5 ? 'rgba(0, 0, 0, 0.87)' : '#ffffff';
    }
  },
  created() {
    // Initialize all types with their stored or default colors
    [...this.rundownTypes, ...this.interfaceTypes].forEach(type => {
      // Get color from theme color map
      const colorValue = getColorValue(type)
      
      // Set initial color in component state
      this.typeColors[type] = colorValue
      
      // Store in localStorage if not present
      if (!localStorage.getItem(`color_${type}`)) {
        updateColor(type, colorValue)
      }
    })
  }
}
</script>

<style>
/* Base table styles */
.color-selector table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  border: 1px solid #e0e0e0;
  margin: 0.5em;  /* Increased from 0.25em */
}

/* Container margins */
.color-selector {
  margin: 0.5em;  /* Increased from 0.25em */
  width: calc(100% - 1em);  /* Adjust width to account for larger margins */
}

/* Header styling */
th {
  background-color: #2c3e50;  /* Darker background */
  color: white;              /* White text */
  font-weight: 600;         /* Bolder text */
  height: 2.5em;           /* Increased from 2em to 2.5em */
  border: 1px solid #1a2634; /* Darker border */
  text-align: left;
  padding: 0 8px;
  font-size: 0.875rem;      /* Slightly larger text */
  text-transform: uppercase; /* Optional: makes headers more distinct */
  letter-spacing: 0.05em;   /* Optional: better readability */
}

/* Optional: Add subtle transition on hover */
th:hover {
  background-color: #34495e;
}

/* Cell borders and alignment */
td {
  border: 1px solid #e0e0e0;
  height: 20px;  /* Reduced from 25px */
  padding: 0;
  vertical-align: middle;
  font-size: 0.75rem;
}

/* Type label cell */
td:first-child {
  width: 15%;
  text-align: center;
  font-weight: 500;
  padding: 0 4px;
  font-size: 1.1em;  /* Increased from 0.75rem */
  color: rgba(0, 0, 0, 0.87);  /* Better contrast */
  letter-spacing: 0.01em;  /* Slightly better readability */
}

/* Dropdown cell with tighter v-select positioning */
td:nth-child(2) {
  width: 65%;
  padding: 0;
  position: relative;
}

/* Preview cell */
td:last-child {
  width: 20%;
  padding: 0;
  position: relative;
}

/* Preview box - full height and width */
.preview-box {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  transition: all 0.2s ease;
}

/* Force v-select to fill cell with no spacing */
:deep(.v-select) {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  margin: 0;
  padding: 0;
  height: 100% !important;
}

/* Remove internal field spacing */
:deep(.v-field) {
  border-radius: 0;
  height: 100% !important;
  min-height: unset !important;
  --v-field-padding-top: 0 !important;
  --v-field-padding-bottom: 0 !important;
}

/* Control input container spacing */
:deep(.v-field__input) {
  padding: 0 4px !important;
  min-height: unset !important;
  height: 100% !important;
  color: rgba(0, 0, 0, 0.87) !important;
}

/* Adjust field layout */
:deep(.v-field__field) {
  padding: 0 !important;
  min-height: unset !important;
  height: 100% !important;
}

/* Control input wrapper */
:deep(.v-input__control) {
  height: 100% !important;
  min-height: unset !important;
}

/* Adjust input text size */
:deep(.v-field__input, .v-select__content) {
  font-size: 0.75rem;  /* Even smaller font */
}

/* Color dot adjustments */
.color-dot {
  width: 12px;  /* Even smaller */
  height: 12px;  /* Even smaller */
  border-radius: 50%;
  margin-right: 4px;  /* Less margin */
}

/* Add spacing between tables */
h2.mt-6 {
  margin-top: 24px;
}

.mt-4 {
  margin-top: 16px;
}

/* Remove v-select top padding */
:deep(.v-field.v-field--variant-filled) {
  padding-top: 0 !important;
  --v-field-padding-top: 0 !important;
}

:deep(.v-input.v-select) {
  padding-top: 0 !important;
}

:deep(.v-field__field) {
  padding-top: 0 !important;
}

:deep(.v-field__input) {
  padding-top: 0 !important;
  min-height: 20px !important;  /* Match new height */
  line-height: 20px !important; /* Match new height */
}

:deep(.v-select__selection) {
  padding-top: 0 !important;
  margin-top: 0 !important;
  line-height: 20px !important; /* Match new height */
  color: rgba(0, 0, 0, 0.87);
  font-weight: 500;
}

/* Ensure content is vertically centered */
:deep(.v-field__input > *) {
  margin: auto 0 !important;
}

/* Specific selector for v-text-field in color column */
td:nth-child(2) :deep(.v-text-field) {
  padding-top: 0 !important;
  margin-top: 0 !important;
}

/* Additional specificity for the input wrapper */
td:nth-child(2) :deep(.v-input.v-text-field.v-select) {
  padding-top: 0 !important;
  margin-top: 0 !important;
}
</style>
