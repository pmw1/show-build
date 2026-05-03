<template>
  <div class="color-selector" :class="{ 'compact': compact }">
    <!-- Container for side-by-side layout -->
    <div class="color-tables-container">
      <!-- Core Rundown Items Table -->
      <div class="color-table-section">
        <h2 v-if="!compact" class="section-title">Core Rundown Items</h2>
        <h3 v-else class="text-subtitle-2 mb-2">Core Rundown Items</h3>
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
                    backgroundColor: resolveVuetifyColor(getFullColor(type), $vuetify),
                    color: getTextColor(resolveVuetifyColor(getFullColor(type), $vuetify))
                  }"
                >
                  {{ type }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Custom Rundown Items Table -->
      <div v-if="customRundownTypes.length > 0" class="color-table-section">
        <h2 v-if="!compact" class="section-title">Custom Rundown Items</h2>
        <h3 v-else class="text-subtitle-2 mb-2">Custom Rundown Items</h3>
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
            <tr v-for="type in customRundownTypes" :key="type">
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
                    backgroundColor: resolveVuetifyColor(getFullColor(type), $vuetify),
                    color: getTextColor(resolveVuetifyColor(getFullColor(type), $vuetify))
                  }"
                >
                  {{ type }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="customRundownTypes.length === 0" class="text-caption text-grey">
          No custom rundown types defined. Add custom types in Settings → Content → Content Library.
        </p>
      </div>

      <!-- Rundown Regions Table -->
      <div class="color-table-section">
        <h2 v-if="!compact" class="section-title">Rundown Regions</h2>
        <h3 v-else class="text-subtitle-2 mb-2">Rundown Regions</h3>
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
            <tr v-for="type in rundownRegionsTypes" :key="type">
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
                    backgroundColor: resolveVuetifyColor(getFullColor(type), $vuetify),
                    color: getTextColor(resolveVuetifyColor(getFullColor(type), $vuetify))
                  }"
                >
                  {{ type }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Elements and Cues Table -->
      <div class="color-table-section">
        <h2 v-if="!compact" class="section-title">Elements and Cues</h2>
        <h3 v-else class="text-subtitle-2 mb-2">Elements and Cues</h3>
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
            <tr v-for="type in elementsCuesTypes" :key="type">
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
                    <div class="color-swatch-container" :style="{ backgroundColor: resolveVuetifyColor(getFullColor(type), $vuetify), width: '100%', height: '28px', display: 'inline-block', borderRadius: '2px', position: 'relative' }">
                      <span class="color-label-overlay" :style="{ color: getTextColor(resolveVuetifyColor(getFullColor(type), $vuetify)) }">{{ item.title }}</span>
                    </div>
                  </template>
                </v-select>
              </td>
              <td class="preview-cell">
                <div
                  class="preview-box-fill"
                  :style="{
                    backgroundColor: resolveVuetifyColor(getFullColor(type), $vuetify),
                    color: getTextColor(resolveVuetifyColor(getFullColor(type), $vuetify))
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
                    backgroundColor: resolveVuetifyColor(getFullColor(type + '-interface'), $vuetify),
                    color: getTextColor(resolveVuetifyColor(getFullColor(type + '-interface'), $vuetify))
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
                    backgroundColor: resolveVuetifyColor(getFullColor(type + '-script'), $vuetify),
                    color: getTextColor(resolveVuetifyColor(getFullColor(type + '-script'), $vuetify))
                  }"
                >
                  {{ type }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Global Action Colors Table -->
      <div class="color-table-section">
        <h2 v-if="!compact" class="section-title">Global Action Colors</h2>
        <h3 v-else class="text-subtitle-2 mb-2">Global Action Colors</h3>
        <table class="color-config-table">
          <thead>
            <tr>
              <th class="type-header">Action</th>
              <th class="color-header">Base Color</th>
              <th class="color-header">Variant</th>
              <th class="preview-header">Preview</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="type in globalActionTypes" :key="type">
              <td class="type-cell">{{ formatGlobalActionName(type) }}</td>
              <td class="color-cell">
                <v-select
                  v-model="baseColor[type + '-global']"
                  :items="baseColorOptions"
                  dense
                  outlined
                  hide-details
                  class="cell-fill-select"
                  @change="onBaseChange(type + '-global')"
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
                  v-model="variant[type + '-global']"
                  :items="variantOptions(baseColor[type + '-global'])"
                  dense
                  outlined
                  hide-details
                  class="cell-fill-select"
                  :disabled="!baseColor[type + '-global']"
                >
                  <template #item="{ item, props }">
                    <v-list-item v-if="item" v-bind="props">
                      <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor((baseColor[type + '-global'] || '') + (item.value ? '-' + item.value : ''), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                      <span>{{ item.title }}</span>
                    </v-list-item>
                  </template>
                  <template #selection="{ item }">
                    <div class="color-swatch-container" :style="{ backgroundColor: resolveVuetifyColor((baseColor[type + '-global'] || '') + (item.value ? '-' + item.value : ''), $vuetify), width: '100%', height: '28px', display: 'inline-block', borderRadius: '2px', position: 'relative' }">
                      <span class="color-label-overlay" :style="{ color: getTextColor(resolveVuetifyColor((baseColor[type + '-global'] || '') + (item.value ? '-' + item.value : ''), $vuetify)) }">{{ item.title }}</span>
                    </div>
                  </template>
                </v-select>
              </td>
              <td class="preview-cell">
                <div
                  class="preview-box-fill"
                  :style="{
                    backgroundColor: resolveVuetifyColor(getFullColor(type + '-global'), $vuetify),
                    color: getTextColor(resolveVuetifyColor(getFullColor(type + '-global'), $vuetify))
                  }"
                >
                  {{ formatGlobalActionName(type) }}
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- General UI Colors Table -->
      <div class="color-table-section">
        <h2 v-if="!compact" class="section-title">General UI</h2>
        <h3 v-else class="text-subtitle-2 mb-2">General UI</h3>
        <table class="color-config-table">
          <thead>
            <tr>
              <th class="type-header">Element</th>
              <th class="color-header">Base Color</th>
              <th class="color-header">Variant</th>
              <th class="preview-header">Preview</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="type in generalUiTypes" :key="type">
              <td class="type-cell">{{ formatGeneralUiName(type) }}</td>
              <td class="color-cell">
                <v-select
                  v-model="baseColor[type + '-ui']"
                  :items="baseColorOptions"
                  dense
                  outlined
                  hide-details
                  class="cell-fill-select"
                  @change="onBaseChange(type + '-ui')"
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
                  v-model="variant[type + '-ui']"
                  :items="variantOptions(baseColor[type + '-ui'])"
                  dense
                  outlined
                  hide-details
                  class="cell-fill-select"
                  :disabled="!baseColor[type + '-ui']"
                >
                  <template #item="{ item, props }">
                    <v-list-item v-if="item" v-bind="props">
                      <span class="color-swatch" :style="{ backgroundColor: resolveVuetifyColor((baseColor[type + '-ui'] || '') + (item.value ? '-' + item.value : ''), $vuetify), width: '24px', height: '24px', display: 'inline-block', borderRadius: '2px', marginRight: '8px' }"></span>
                      <span>{{ item.title }}</span>
                    </v-list-item>
                  </template>
                  <template #selection="{ item }">
                    <div class="color-swatch-container" :style="{ backgroundColor: resolveVuetifyColor((baseColor[type + '-ui'] || '') + (item.value ? '-' + item.value : ''), $vuetify), width: '100%', height: '28px', display: 'inline-block', borderRadius: '2px', position: 'relative' }">
                      <span class="color-label-overlay" :style="{ color: getTextColor(resolveVuetifyColor((baseColor[type + '-ui'] || '') + (item.value ? '-' + item.value : ''), $vuetify)) }">{{ item.title }}</span>
                    </div>
                  </template>
                </v-select>
              </td>
              <td class="preview-cell">
                <div
                  class="preview-box-fill"
                  :style="{
                    backgroundColor: resolveVuetifyColor(getFullColor(type + '-ui'), $vuetify),
                    color: getTextColor(resolveVuetifyColor(getFullColor(type + '-ui'), $vuetify))
                  }"
                >
                  {{ formatGeneralUiName(type) }}
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

    <!-- Snackbar for error messages -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
      location="bottom"
    >
      {{ snackbar.message }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar.show = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted } from 'vue'; // eslint-disable-line no-unused-vars
import { useTheme } from 'vuetify';
import { resolveVuetifyColor, updateColor, getColorValue, getTextColorForBackground } from '../utils/themeColorMap';
import { debounce } from 'lodash-es';

defineProps({
  compact: {
    type: Boolean,
    default: false
  },
  hideSaveButton: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['colors-changed', 'colors-saved']);

// Vuetify theme instance (for themeColors computed; template still uses $vuetify directly)
// eslint-disable-next-line no-unused-vars
const theme = useTheme();

// Initialize with all possible types for reactivity
const initAllTypes = [
  'segment', 'ad', 'promo', 'cta', 'trans',
  'break', 'block', 'block-a', 'block-b', 'block-c', 'block-d', 'block-e', 'block-f', 'block-g', 'block-h',
  'Selection-interface', 'Hover-interface', 'Highlight-interface',
  'Dropline-interface', 'DragLight-interface', 'LocatorFlash-interface',
  'Draft-script', 'Approved-script', 'Production-script', 'Completed-script'
];

const initBaseColor = {};
const initVariant = {};

// Initialize all types to ensure reactivity
initAllTypes.forEach(type => {
  initBaseColor[type] = null;
  initVariant[type] = null;
});

// Data properties
// Core Rundown Items (hardcoded)
const rundownTypes = ref(['segment', 'ad', 'promo', 'cta', 'live', 'tease', 'tag']);
// Custom Rundown Items (loaded from API)
const customRundownTypes = ref([]);
const rundownRegionsTypes = ref(['break', 'block', 'block-a', 'block-b', 'block-c', 'block-d', 'block-e', 'block-f', 'block-g', 'block-h']);
const elementsCuesTypes = ref(['trans', 'pkg', 'vo', 'sot', 'interview', 'music', 'reader', 'gfx', 'fsq', 'nat', 'img', 'dir', 'bump', 'sting']);
const interfaceTypes = ref(['Selection', 'Hover', 'Highlight', 'Dropline', 'DragLight', 'LocatorFlash']);
const scriptStatusTypes = ref(['Scheduled', 'Draft', 'Production', 'Running', 'Completed']);
const globalActionTypes = ref(['AutoSave', 'Needs-Attention']);
const generalUiTypes = ref(['Block-Header']);
const typeColors = ref({}); // eslint-disable-line no-unused-vars
const showConfirmation = ref(false);
const isSaving = ref(false);
const baseColor = reactive(initBaseColor);
const variant = reactive(initVariant);
const isInitializing = ref(true); // Flag to prevent watcher events during initialization
const snackbar = reactive({
  show: false,
  message: '',
  color: 'error',
  timeout: 5000
});

// Computed
const themeColors = computed(() => { // eslint-disable-line no-unused-vars
  const lightTheme = theme?.themes?.value?.light;
  return lightTheme ? Object.keys(lightTheme.colors || {}) : [];
});

const baseColorOptions = computed(() => {
  // Official Vuetify Material Design color palette + theme colors
  const materialColors = [
    'red', 'pink', 'purple', 'deep-purple', 'indigo', 'blue',
    'light-blue', 'cyan', 'teal', 'green', 'light-green', 'lime',
    'yellow', 'amber', 'orange', 'deep-orange', 'brown',
    'blue-grey', 'grey', 'black', 'white'
  ];

  const themeColorsList = [
    'primary', 'secondary', 'accent', 'error', 'info', 'success', 'warning'
  ];

  const allColors = [...materialColors, ...themeColorsList];

  return allColors.map(color => ({
    title: color.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    value: color,
  }));
});

const variantOptions = computed(() => {
  // Returns a function to get variant options for a base color
  return (baseColorVal) => {
    if (!baseColorVal) return [{ title: 'Base', value: '' }];

    const variants = [
      { title: 'Base', value: '' }
    ];

    // Theme colors have limited variants
    const themeColorsList = ['primary', 'secondary', 'accent', 'error', 'info', 'success', 'warning'];
    const specialColors = ['black', 'white'];

    if (themeColorsList.includes(baseColorVal)) {
      // Theme colors typically have lighten/darken variants
      for (let i = 4; i >= 1; i--) {
        variants.push({ title: `Lighten ${i}`, value: `lighten-${i}` });
      }
      for (let i = 1; i <= 4; i++) {
        variants.push({ title: `Darken ${i}`, value: `darken-${i}` });
      }
    } else if (specialColors.includes(baseColorVal)) {
      // Black and white don't have variants
      return variants;
    } else {
      // Material colors - check what variants actually exist

      // Define color-specific variant availability
      const colorVariants = {
        'red': { lighten: 4, darken: 4, accent: false },
        'pink': { lighten: 4, darken: 4, accent: false },
        'purple': { lighten: 5, darken: 4, accent: false },
        'deep-purple': { lighten: 5, darken: 4, accent: false },
        'indigo': { lighten: 5, darken: 4, accent: false },
        'blue': { lighten: 5, darken: 4, accent: false },
        'light-blue': { lighten: 5, darken: 4, accent: false },
        'cyan': { lighten: 4, darken: 4, accent: false },
        'teal': { lighten: 5, darken: 4, accent: false },
        'green': { lighten: 4, darken: 4, accent: true },
        'light-green': { lighten: 5, darken: 4, accent: false },
        'lime': { lighten: 5, darken: 4, accent: false },
        'yellow': { lighten: 4, darken: 4, accent: true },
        'amber': { lighten: 4, darken: 4, accent: false },
        'orange': { lighten: 5, darken: 4, accent: false },
        'deep-orange': { lighten: 5, darken: 4, accent: false },
        'brown': { lighten: 5, darken: 4, accent: false },
        'blue-grey': { lighten: 5, darken: 4, accent: false },
        'grey': { lighten: 4, darken: 4, accent: false }
      };

      const colorConfig = colorVariants[baseColorVal] || { lighten: 4, darken: 4, accent: false };

      // Add lighten variants
      for (let i = colorConfig.lighten; i >= 1; i--) {
        variants.push({ title: `Lighten ${i}`, value: `lighten-${i}` });
      }

      // Add darken variants
      for (let i = 1; i <= colorConfig.darken; i++) {
        variants.push({ title: `Darken ${i}`, value: `darken-${i}` });
      }

      // Add accent variant only if available
      if (colorConfig.accent) {
        variants.push({ title: `Accent`, value: `accent` });
      }
    }

    return variants;
  };
});

// Methods
function getRundownTypeValues() { // eslint-disable-line no-unused-vars
  // Hardcoded rundown types to avoid circular import issues
  return ['segment', 'ad', 'promo', 'cta', 'trans', 'pkg', 'vo', 'sot', 'interview', 'live', 'tease', 'tag', 'music', 'reader'];
}

function formatGlobalActionName(type) {
  // Format global action type names for display
  const nameMap = {
    'AutoSave': 'Auto Save Indicator'
  };
  return nameMap[type] || type.replace(/([A-Z])/g, ' $1').trim();
}

function formatGeneralUiName(type) {
  // 'Block-Header' -> 'Block Header'
  return String(type).replace(/-/g, ' ');
}

async function loadCustomTypes() {
  // Load custom rundown types from API
  try {
    const response = await fetch('/api/content-library/custom-types/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('auth-token')}`
      }
    });
    if (response.ok) {
      const data = await response.json();
      if (data.custom_types && data.custom_types.length > 0) {
        // Extract type names for color configuration
        customRundownTypes.value = data.custom_types.map(ct => ct.type_name);
        // Initialize baseColor and variant for custom types
        customRundownTypes.value.forEach(type => {
          if (baseColor[type] === undefined) {
            baseColor[type] = null;
            variant[type] = null;
          }
          // Apply default color from custom type if available
          const customType = data.custom_types.find(ct => ct.type_name === type);
          if (customType && customType.color && !baseColor[type]) {
            const parsed = parseColorValue(customType.color);
            baseColor[type] = parsed.base;
            variant[type] = parsed.variant || '';
          }
        });
      }
    }
  } catch (error) {
    console.log('Could not load custom types:', error);
  }
}

function parseColorValue(colorValue) {
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
}

function vuetifyColorNameToThemeKey(name) {
  if (!name) return '';
  const parts = name.toLowerCase().split(' ');
  const base = parts[0];
  const variantPart = parts.length > 1 ? parts.slice(1).join('-') : '';
  return variantPart ? `${base}-${variantPart}` : base;
}

function onBaseChange(type) {
  // When base color changes, reset the variant to empty string (Base)
  variant[type] = '';
}

function getFullColor(type) {
  const base = baseColor[type];
  const v = variant[type];
  if (!base) return null;
  return v ? `${base}-${v}` : base;
}

function getTextColor(bgColor) {
  // Use the enhanced contrast logic from themeColorMap
  if (!bgColor) return '#000000';
  return getTextColorForBackground(bgColor);
}

function showSnackbar(message, color = 'error') {
  snackbar.message = message;
  snackbar.color = color;
  snackbar.show = true;
}

async function initializeColors() {
  const allTypes = [
    ...rundownTypes.value,
    ...customRundownTypes.value,
    ...rundownRegionsTypes.value,
    ...elementsCuesTypes.value,
    ...interfaceTypes.value.map(t => t + '-interface'),
    ...scriptStatusTypes.value.map(t => t + '-script'),
    ...globalActionTypes.value.map(t => t + '-global'),
    ...generalUiTypes.value.map(t => t + '-ui'),
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
              'draglight': 'draglight',
              'locatorflash': 'locatorflash'
            };
            lookupKey = interfaceMapping[baseType] || baseType;
          } else if (type.endsWith('-script')) {
            const baseType = type.replace('-script', '').toLowerCase();
            // Map script status types to their base colors
            const scriptMapping = {
              'scheduled': 'scheduled',
              'draft': 'draft',
              'production': 'production',
              'running': 'running',
              'completed': 'completed'
            };
            lookupKey = scriptMapping[baseType] || baseType;
          } else if (type.endsWith('-global')) {
            const baseType = type.replace('-global', '').toLowerCase();
            // Map global action types to their base colors
            const globalMapping = {
              'autosave': 'autosave'
            };
            lookupKey = globalMapping[baseType] || baseType;
          } else if (type.endsWith('-ui')) {
            // General UI section: 'block-header-ui' -> DB key 'block-header'
            lookupKey = type.replace('-ui', '').toLowerCase();
          }

          const colorValue = dbColors[lookupKey];
          if (colorValue) {
            const parsed = parseColorValue(colorValue);
            // Set the reactive properties (Vue 3 compatible)
            baseColor[type] = parsed.base || null;
            variant[type] = parsed.variant || '';
            // Update local storage as backup
            updateColor(type, colorValue);
          }
        });

        // Set initialization complete
        nextTick(() => {
          isInitializing.value = false;
        });
        return; // Exit early if database load succeeds
      }
    }
  } catch (error) {
    // Fallback to localStorage if database fails
  }

  // Fallback to local storage if database fails
  allTypes.forEach(type => {
    if (!baseColor[type]) {
      let lookupKey = type;

      // Map interface and script types to their base color keys
      if (type.endsWith('-interface')) {
        const baseType = type.replace('-interface', '').toLowerCase();
        const interfaceMapping = {
          'selection': 'selection',
          'hover': 'hover',
          'highlight': 'highlight',
          'dropline': 'dropline',
          'draglight': 'draglight',
          'locatorflash': 'locatorflash'
        };
        lookupKey = interfaceMapping[baseType] || baseType;
      } else if (type.endsWith('-script')) {
        const baseType = type.replace('-script', '').toLowerCase();
        const scriptMapping = {
          'scheduled': 'scheduled',
          'draft': 'draft',
          'production': 'production',
          'running': 'running',
          'completed': 'completed'
        };
        lookupKey = scriptMapping[baseType] || baseType;
      } else if (type.endsWith('-global')) {
        const baseType = type.replace('-global', '').toLowerCase();
        const globalMapping = {
          'autosave': 'autosave'
        };
        lookupKey = globalMapping[baseType] || baseType;
      }

      const colorValue = getColorValue(lookupKey); // Get color from local storage using mapped key
      if (colorValue) {
        // localStorage might use space or dash format, try both
        const spaceParts = colorValue.split(' ');
        if (spaceParts.length > 1) {
          // Space format: "blue lighten-4"
          baseColor[type] = spaceParts[0] || null;
          variant[type] = spaceParts[1] || null;
        } else {
          // Dash format: "blue-lighten-4"
          const parsed = parseColorValue(colorValue);
          baseColor[type] = parsed.base;
          variant[type] = parsed.variant;
        }
      } else {
        baseColor[type] = null;
        variant[type] = null;
      }
    }
  });

  // Set initialization complete for fallback case too
  nextTick(() => {
    isInitializing.value = false;
  });
}

const saveColors = debounce(async function () {
  isSaving.value = true;
  const allTypes = [
    ...rundownTypes.value,
    ...customRundownTypes.value,
    ...rundownRegionsTypes.value,
    ...elementsCuesTypes.value,
    ...interfaceTypes.value.map(t => t + '-interface'),
    ...scriptStatusTypes.value.map(t => t + '-script'),
    ...globalActionTypes.value.map(t => t + '-global'),
    ...generalUiTypes.value.map(t => t + '-ui'),
  ];

  // Build colors object
  const colors = {};
  allTypes.forEach(type => {
    const fullColor = getFullColor(type);
    if (fullColor) {
      colors[type] = fullColor;
      updateColor(type, fullColor); // Update local storage as backup

      // For script status types, also save base keys for content editor
      if (type.endsWith('-script')) {
        const baseKey = type.replace('-script', '').toLowerCase();
        colors[baseKey] = fullColor;
        updateColor(baseKey, fullColor);
      }

      // For interface types, also save base keys for content editor
      if (type.endsWith('-interface')) {
        const baseType = type.replace('-interface', '').toLowerCase();
        // Map interface types to their base colors
        const interfaceMapping = {
          'selection': 'selection',
          'hover': 'hover',
          'highlight': 'highlight',
          'dropline': 'dropline',
          'draglight': 'draglight',
          'locatorflash': 'locatorflash'
        };
        const baseKey = interfaceMapping[baseType] || baseType;
        colors[baseKey] = fullColor;
        updateColor(baseKey, fullColor);
      }

      // For global action types, also save base keys for content editor
      if (type.endsWith('-global')) {
        const baseType = type.replace('-global', '').toLowerCase();
        // Map global action types to their base colors
        const globalMapping = {
          'autosave': 'autosave'
        };
        const baseKey = globalMapping[baseType] || baseType;
        colors[baseKey] = fullColor;
        updateColor(baseKey, fullColor);
      }

      // For general UI types, also save the base key
      if (type.endsWith('-ui')) {
        const baseKey = type.replace('-ui', '').toLowerCase();
        colors[baseKey] = fullColor;
        updateColor(baseKey, fullColor);
      }
    }
  });

  // Save to database (new endpoint with profile support)
  try {
    const token = localStorage.getItem('auth-token');

    // Build headers - only add Authorization if token exists
    const headers = {
      'Content-Type': 'application/json'
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    console.log('Saving colors to database:', colors);
    console.log('Using headers:', headers);

    const response = await fetch('/api/settings/colors', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        colors,
        category: 'colors',
        profile: 'default'
      })
    });

    if (response.ok) {
      const result = await response.json();
      console.log('Colors saved successfully:', result);
      isSaving.value = false;
      showConfirmation.value = true;
      emit('colors-saved');
    } else {
      const errorText = await response.text();
      console.error('Failed to save colors to database. Response:', response.status, response.statusText, errorText);
      console.error('Request body was:', JSON.stringify({
        colors,
        category: 'colors',
        profile: 'default'
      }));
      showSnackbar(`Failed to save colors: ${response.status} ${response.statusText} - ${errorText}`);
      isSaving.value = false;
    }
  } catch (error) {
    console.error('Error saving colors:', error);
    showSnackbar(`Error saving colors: ${error.message}`);
    isSaving.value = false;
  }
}, 1000);

// Watchers
watch(baseColor, () => {
  if (isInitializing.value) {
    return;
  }
  emit('colors-changed');
}, { deep: true });

watch(variant, () => {
  if (isInitializing.value) {
    return;
  }
  emit('colors-changed');
}, { deep: true });

// Created lifecycle (runs immediately in script setup)
(async () => {
  await loadCustomTypes();
  initializeColors();
})();

// Expose resolveVuetifyColor for template usage
// (imported function needs to be accessible in template with script setup)
</script>

<style scoped>
.color-selector {
  padding: 1rem;
  background-color: #f5f5f5;
  color: #333;
}

/* Container for masonry layout */
.color-tables-container {
  column-count: 3;
  column-gap: 15px;
}

/* Each table section - masonry item */
.color-table-section {
  break-inside: avoid;
  page-break-inside: avoid;
  margin-bottom: 15px;
  display: inline-block;
  width: 100%;
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
  margin-bottom: 20px; /* Add space after each table */
}

/* Add padding to the bottom row of each table */
.color-config-table tbody tr:last-child td {
  padding-bottom: 8px;
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
