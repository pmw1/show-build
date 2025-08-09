<template>
  <div class="color-selector">
    <!-- Rundown Items Table (TWO DROPDOWNS, FIXED) -->
    <h2>Rundown Item Colors</h2>
    <table>
      <thead>
        <tr>
          <th>Type</th>
          <th>Base Color</th>
          <th>Variant</th>
          <th>Preview</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="type in rundownTypes" :key="type">
          <td>{{ type }}</td>
          <td>
            <v-select
              v-model="baseColor[type]"
              :items="baseColorOptions"
              label="Base"
              dense
              outlined
              hide-details
              style="width: 110px"
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
                <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(item.value), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                <span>{{ item.title }}</span>
              </template>
            </v-select>
          </td>
          <td>
            <v-select
              v-model="variant[type]"
              :items="variantOptions(baseColor[type])"
              label="Variant"
              dense
              outlined
              hide-details
              style="width: 110px"
              :disabled="!baseColor[type]"
            >
              <template #item="{ item, props }">
                <v-list-item v-if="item && item.value" v-bind="props">
                  <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(baseColor[type] + (item.value ? ' ' + item.value : '')), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                  <span>{{ item.title }}</span>
                </v-list-item>
              </template>
              <template #selection="{ item }">
                <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(baseColor[type] + (item.value ? ' ' + item.value : '')), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                <span>{{ item.title }}</span>
              </template>
            </v-select>
          </td>
          <td>
            <div 
              class="preview-box" 
              :style="{
                backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(getFullColor(type)), $vuetify),
                color: getTextColor(resolveVuetifyColor(vuetifyColorNameToThemeKey(getFullColor(type)), $vuetify)),
                width: '60px',
                height: '28px',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 500
              }"
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
          <th>Base Color</th>
          <th>Variant</th>
          <th>Preview</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="type in interfaceTypes" :key="type">
          <td>{{ type }}</td>
          <td>
            <v-select
              v-model="baseColor[type + '-interface']"
              :items="baseColorOptions"
              label="Base"
              dense
              outlined
              hide-details
              style="width: 110px"
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
                <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(item.value), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                <span>{{ item.title }}</span>
              </template>
            </v-select>
          </td>
          <td>
            <v-select
              v-model="variant[type + '-interface']"
              :items="variantOptions(baseColor[type + '-interface'])"
              label="Variant"
              dense
              outlined
              hide-details
              style="width: 110px"
              :disabled="!baseColor[type + '-interface']"
            >
              <template #item="{ item, props }">
                <v-list-item v-if="item && item.value" v-bind="props">
                  <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(baseColor[type + '-interface'] + (item.value ? ' ' + item.value : '')), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                  <span>{{ item.title }}</span>
                </v-list-item>
              </template>
              <template #selection="{ item }">
                <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(baseColor[type + '-interface'] + (item.value ? ' ' + item.value : '')), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                <span>{{ item.title }}</span>
              </template>
            </v-select>
          </td>
          <td>
            <div class="preview-box" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey((baseColor[type + '-interface'] || '') + (variant[type + '-interface'] ? ' ' + variant[type + '-interface'] : '')), $vuetify), color: getTextColor(resolveVuetifyColor(vuetifyColorNameToThemeKey((baseColor[type + '-interface'] || '') + (variant[type + '-interface'] ? ' ' + variant[type + '-interface'] : '')), $vuetify)) }">
              {{ type }}
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Script Status Colors Table -->
    <h2 class="mt-6">Script Status Colors</h2>
    <table>
      <thead>
        <tr>
          <th>Status</th>
          <th>Base Color</th>
          <th>Variant</th>
          <th>Preview</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="type in scriptStatusTypes" :key="type">
          <td>{{ type }}</td>
          <td>
            <v-select
              v-model="baseColor[type + '-script']"
              :items="baseColorOptions"
              label="Base"
              dense
              outlined
              hide-details
              style="width: 110px"
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
                <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(item.value), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                <span>{{ item.title }}</span>
              </template>
            </v-select>
          </td>
          <td>
            <v-select
              v-model="variant[type + '-script']"
              :items="variantOptions(baseColor[type + '-script'])"
              label="Variant"
              dense
              outlined
              hide-details
              style="width: 110px"
              :disabled="!baseColor[type + '-script']"
            >
              <template #item="{ item, props }">
                <v-list-item v-if="item && item.value" v-bind="props">
                  <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(baseColor[type + '-script'] + (item.value ? ' ' + item.value : '')), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                  <span>{{ item.title }}</span>
                </v-list-item>
              </template>
              <template #selection="{ item }">
                <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey(baseColor[type + '-script'] + (item.value ? ' ' + item.value : '')), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                <span>{{ item.title }}</span>
              </template>
            </v-select>
          </td>
          <td>
            <div class="preview-box" :style="{ backgroundColor: resolveVuetifyColor(vuetifyColorNameToThemeKey((baseColor[type + '-script'] || '') + (variant[type + '-script'] ? ' ' + variant[type + '-script'] : '')), $vuetify), color: getTextColor(resolveVuetifyColor(vuetifyColorNameToThemeKey((baseColor[type + '-script'] || '') + (variant[type + '-script'] ? ' ' + variant[type + '-script'] : '')), $vuetify)) }">
              {{ type }}
            </div>
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
import { resolveVuetifyColor, updateColor, getColorValue } from '../utils/themeColorMap';
import { debounce } from 'lodash-es';

export default {
  data() {
    return {
      rundownTypes: ['segment', 'ad', 'promo', 'cta', 'trans'],
      interfaceTypes: ['Selection', 'Hover', 'Highlight', 'Dropline', 'DragLight'],
      scriptStatusTypes: ['Draft', 'Approved', 'Production', 'Completed'],
      typeColors: {},
      showConfirmation: false,
      isSaving: false,
      baseColor: {},
      variant: {},
    }
  },
  computed: {
    themeColors() {
      const theme = this.$vuetify?.theme?.themes?.light;
      return theme ? Object.keys(theme.colors || {}) : [];
    },
    baseColorOptions() {
      const theme = this.$vuetify?.theme?.themes?.light?.colors || {};
      return Object.entries(theme).map(([key]) => ({
        title: key.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
        value: key,
      }));
    },
    variantOptions() {
      // Returns a function to get variant options for a base
      return () => {
        const variants = ['base', 'lighten-1', 'lighten-2', 'lighten-3', 'lighten-4', 'darken-1', 'darken-2', 'darken-3', 'darken-4'];
        return variants.map(v => ({ title: v, value: v }));
      };
    },
  },
  methods: {
    resolveVuetifyColor,
    vuetifyColorNameToThemeKey(name) {
      if (!name) return '';
      const parts = name.toLowerCase().split(' ');
      const base = parts[0];
      const variant = parts.length > 1 ? parts.slice(1).join('-') : '';
      return variant ? `${base}-${variant}` : base;
    },
    onBaseChange(type) {
      // When base color changes, reset the variant
      this.variant[type] = null;
    },
    getFullColor(type) {
      const base = this.baseColor[type];
      const variant = this.variant[type];
      if (!base) return null;
      return variant ? `${base} ${variant}` : base;
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
    initializeColors() {
      const allTypes = [
        ...this.rundownTypes,
        ...this.interfaceTypes.map(t => t + '-interface'),
        ...this.scriptStatusTypes.map(t => t + '-script'),
      ];

      allTypes.forEach(type => {
        const colorValue = getColorValue(type); // Get color from central config
        if (colorValue) {
          const parts = colorValue.split(' ');
          this.baseColor[type] = parts[0] || null;
          this.variant[type] = parts[1] || null;
        } else {
          this.baseColor[type] = null;
          this.variant[type] = null;
        }
      });
    },
    saveColors: debounce(function () {
      this.isSaving = true;
      const allTypes = [
        ...this.rundownTypes,
        ...this.interfaceTypes.map(t => t + '-interface'),
        ...this.scriptStatusTypes.map(t => t + '-script'),
      ];

      allTypes.forEach(type => {
        const fullColor = this.getFullColor(type);
        if (fullColor) {
          updateColor(type, fullColor); // Update central config
        }
      });

      setTimeout(() => {
        this.isSaving = false;
        this.showConfirmation = true;
      }, 1000);
    }, 1000),
  },
  created() {
    this.initializeColors();
  },
  mounted() {
    // this.initializeColors();
  },
};
</script>

<style scoped>
.color-selector {
  padding: 1rem;
  background-color: #1E1E1E;
  color: #FFFFFF;
}
h2 {
  border-bottom: 1px solid #444;
  padding-bottom: 8px;
  margin-bottom: 16px;
  font-weight: 500;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  border: 1px solid #333;
  padding: 8px;
  text-align: left;
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
.color-swatch {
  width: 20px;
  height: 20px;
  display: inline-block;
  margin-right: 8px;
  border-radius: 3px;
  border: 1px solid #555;
}
</style>
