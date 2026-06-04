<template>
  <div class="color-selector" :class="{ compact }">
    <!-- Sticky toolbar: search + global actions + save state -->
    <div class="cs-toolbar">
      <v-text-field
        v-model="search"
        density="compact"
        variant="outlined"
        hide-details
        clearable
        prepend-inner-icon="mdi-magnify"
        placeholder="Search colors…"
        class="cs-search"
      />
      <div class="cs-toolbar-actions">
        <v-btn size="small" variant="text" @click="toggleAll">
          {{ allExpanded ? 'Collapse all' : 'Expand all' }}
        </v-btn>
        <v-btn size="small" variant="text" color="error" @click="confirmResetAll = true">
          Reset all
        </v-btn>
        <span class="cs-save-state" :class="`cs-save-${saveState}`">
          <v-icon size="14" class="mr-1">{{ saveStateIcon }}</v-icon>{{ saveStateLabel }}
        </span>
        <v-btn
          v-if="!hideSaveButton"
          size="small"
          color="primary"
          :loading="saveState === 'saving'"
          @click="saveNow"
        >
          Save
        </v-btn>
      </div>
    </div>

    <!-- Category sections -->
    <div class="cs-categories">
      <div
        v-for="cat in visibleCategories"
        :key="cat.id"
        class="cs-category"
      >
        <button type="button" class="cs-category-header" @click="toggleCategory(cat.id)">
          <v-icon size="18">{{ isExpanded(cat.id) ? 'mdi-chevron-down' : 'mdi-chevron-right' }}</v-icon>
          <span class="cs-category-label">{{ cat.label }}</span>
          <span class="cs-category-count">{{ entriesFor(cat.id).length }}</span>
        </button>

        <div v-show="isExpanded(cat.id)" class="cs-rows">
          <div v-for="entry in entriesFor(cat.id)" :key="entry.key" class="cs-row">
            <!-- Label + description -->
            <div class="cs-row-label">
              <span class="cs-row-name">{{ entry.label }}</span>
              <span v-if="entry.description" class="cs-row-desc">{{ entry.description }}</span>
            </div>

            <!-- Swatch button → popover picker -->
            <v-menu
              :close-on-content-click="false"
              location="bottom start"
            >
              <template #activator="{ props }">
                <button
                  type="button"
                  class="cs-swatch-btn"
                  v-bind="props"
                  :style="swatchStyle(entry.key)"
                >
                  <span class="cs-swatch-text">{{ values[entry.key] || 'unset' }}</span>
                  <v-icon size="16">mdi-menu-down</v-icon>
                </button>
              </template>

              <v-card class="cs-popover" min-width="320">
                <div class="cs-popover-section-title">Base</div>
                <div class="cs-base-grid">
                  <button
                    v-for="base in BASE_COLORS"
                    :key="base"
                    type="button"
                    class="cs-base-swatch"
                    :class="{ active: split(entry.key).base === base }"
                    :title="base"
                    :style="{ backgroundColor: resolveVuetifyColor(base, $vuetify) }"
                    @click="setBase(entry.key, base)"
                  />
                </div>

                <div class="cs-popover-section-title">Variant</div>
                <div class="cs-variant-strip">
                  <button
                    v-for="v in variantsFor(entry.key)"
                    :key="v.value || 'base'"
                    type="button"
                    class="cs-variant-chip"
                    :class="{ active: split(entry.key).variant === v.value }"
                    :style="variantChipStyle(entry.key, v.value)"
                    @click="setVariant(entry.key, v.value)"
                  >
                    {{ v.title }}
                  </button>
                </div>

                <v-divider class="my-2" />

                <!-- Live preview of the actual widget this color drives -->
                <div class="cs-popover-section-title">Live</div>
                <div class="cs-preview-wrap">
                  <div :class="previewClass(entry)" :style="previewStyle(entry.key)">
                    {{ entry.label }}
                  </div>
                </div>

                <div class="cs-popover-actions">
                  <v-btn
                    size="small"
                    variant="text"
                    :disabled="!isModified(entry.key)"
                    @click="resetOne(entry.key)"
                  >
                    Reset to default
                  </v-btn>
                </div>
              </v-card>
            </v-menu>

            <!-- Inline live preview chip in the row -->
            <div class="cs-row-preview">
              <div :class="previewClass(entry)" :style="previewStyle(entry.key)">
                {{ entry.label }}
              </div>
            </div>

            <!-- Per-row reset (only when modified) -->
            <v-btn
              v-if="isModified(entry.key)"
              icon="mdi-restore"
              size="x-small"
              variant="text"
              :title="`Reset ${entry.label} to default`"
              @click="resetOne(entry.key)"
            />
            <span v-else class="cs-reset-spacer" />
          </div>
        </div>
      </div>

      <div v-if="visibleCategories.length === 0" class="cs-empty">
        No colors match “{{ search }}”.
      </div>
    </div>

    <!-- Reset-all confirmation -->
    <v-dialog v-model="confirmResetAll" max-width="420">
      <v-card>
        <v-card-title>Reset all colors?</v-card-title>
        <v-card-text>
          This restores every color to its default value. Your current custom colors
          will be overwritten.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="confirmResetAll = false">Cancel</v-btn>
          <v-btn color="error" @click="resetAll">Reset all</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="4000">
      {{ snackbar.message }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useTheme } from 'vuetify';
import { debounce } from 'lodash-es';
import {
  resolveVuetifyColor,
  getTextColorForBackground,
  updateColor,
} from '../utils/themeColorMap';
import {
  colorRegistry,
  colorCategories,
  registryByKey,
  BASE_COLORS,
  getVariantsForBase,
  splitColor,
  composeColor,
} from '../utils/colorRegistry';

defineProps({
  compact: { type: Boolean, default: false },
  hideSaveButton: { type: Boolean, default: false },
});

const emit = defineEmits(['colors-changed', 'colors-saved']);

// eslint-disable-next-line no-unused-vars
const theme = useTheme(); // template references $vuetify directly for resolveVuetifyColor

// --- State -------------------------------------------------------------------
// values: { canonicalKey -> 'base[-variant]' }. The ONLY shape we persist.
const values = reactive({});
// Runtime-discovered custom rundown types (appended as registry-like entries).
const customEntries = ref([]);
const search = ref('');
const expanded = reactive({});
const confirmResetAll = ref(false);
const saveState = ref('saved'); // 'saved' | 'unsaved' | 'saving' | 'error'
const snackbar = reactive({ show: false, message: '', color: 'error' });

// --- Derived -----------------------------------------------------------------
// All entries = static registry + runtime custom types.
const allEntries = computed(() => [...colorRegistry, ...customEntries.value]);

const defaultsByKey = computed(() => {
  const m = {};
  for (const e of allEntries.value) m[e.key] = e.default;
  return m;
});

function entriesFor(catId) {
  const term = (search.value || '').trim().toLowerCase();
  return allEntries.value.filter((e) => {
    if (e.category !== catId) return false;
    if (!term) return true;
    return (
      e.key.toLowerCase().includes(term) ||
      e.label.toLowerCase().includes(term) ||
      (e.description || '').toLowerCase().includes(term)
    );
  });
}

const visibleCategories = computed(() =>
  colorCategories.filter((c) => entriesFor(c.id).length > 0)
);

const allExpanded = computed(() =>
  visibleCategories.value.every((c) => expanded[c.id])
);

const saveStateLabel = computed(() => ({
  saved: 'Saved',
  unsaved: 'Unsaved changes',
  saving: 'Saving…',
  error: 'Save failed',
}[saveState.value]));

const saveStateIcon = computed(() => ({
  saved: 'mdi-check-circle',
  unsaved: 'mdi-circle-edit-outline',
  saving: 'mdi-progress-clock',
  error: 'mdi-alert-circle',
}[saveState.value]));

// --- Color composition helpers ----------------------------------------------
function split(key) {
  return splitColor(values[key]);
}

function variantsFor(key) {
  return getVariantsForBase(split(key).base);
}

function setBase(key, base) {
  // Changing base resets variant to plain base.
  values[key] = composeColor(base, '');
  onChanged(key);
}

function setVariant(key, variant) {
  const { base } = split(key);
  if (!base) return;
  values[key] = composeColor(base, variant);
  onChanged(key);
}

function isModified(key) {
  return values[key] !== defaultsByKey.value[key];
}

function resetOne(key) {
  values[key] = defaultsByKey.value[key];
  onChanged(key);
}

function resetAll() {
  for (const e of allEntries.value) values[e.key] = e.default;
  confirmResetAll.value = false;
  // Reflect every change to localStorage mirror, then save.
  for (const e of allEntries.value) updateColor(e.key, values[e.key]);
  emit('colors-changed');
  saveState.value = 'unsaved';
  saveDebounced();
}

// --- Styling -----------------------------------------------------------------
function hex(key) {
  return resolveVuetifyColor(values[key], theme);
}

function swatchStyle(key) {
  const bg = hex(key);
  return { backgroundColor: bg, color: getTextColorForBackground(values[key]) };
}

function variantChipStyle(key, variant) {
  const { base } = split(key);
  const composed = composeColor(base, variant);
  const bg = resolveVuetifyColor(composed, theme);
  return { backgroundColor: bg, color: getTextColorForBackground(composed) };
}

function previewClass(entry) {
  return ['cs-preview', `cs-preview--${entry.preview || 'swatch'}`];
}

function previewStyle(key) {
  const bg = hex(key);
  const fg = getTextColorForBackground(values[key]);
  const p = (registryByKey[key] || customEntries.value.find((e) => e.key === key) || {}).preview;
  if (p === 'rundown-row' || p === 'cue-card') {
    // colored left accent border + tinted background
    return { borderLeft: `6px solid ${bg}`, color: '#222', background: '#fafafa' };
  }
  // swatch / status-badge: filled
  return { backgroundColor: bg, color: fg };
}

// --- Expand/collapse ---------------------------------------------------------
function isExpanded(id) {
  return !!expanded[id];
}
function toggleCategory(id) {
  expanded[id] = !expanded[id];
}
function toggleAll() {
  const target = !allExpanded.value;
  for (const c of colorCategories) expanded[c.id] = target;
}

// --- Change / save -----------------------------------------------------------
function onChanged(key) {
  updateColor(key, values[key]); // keep localStorage mirror in sync
  emit('colors-changed');
  saveState.value = 'unsaved';
  saveDebounced();
}

const saveDebounced = debounce(() => { saveNow(); }, 1000);

async function saveNow() {
  saveState.value = 'saving';
  // Build a clean canonical-key payload. NO legacy keys, NO double-writes.
  const colors = {};
  for (const e of allEntries.value) {
    if (values[e.key]) colors[e.key] = values[e.key];
  }
  try {
    const token = localStorage.getItem('auth-token');
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const response = await fetch('/api/settings/colors', {
      method: 'POST',
      headers,
      body: JSON.stringify({ colors, category: 'colors', profile: 'default' }),
    });
    if (response.ok) {
      saveState.value = 'saved';
      emit('colors-saved');
    } else {
      const text = await response.text();
      saveState.value = 'error';
      showSnackbar(`Failed to save colors: ${response.status} ${text}`);
    }
  } catch (err) {
    saveState.value = 'error';
    showSnackbar(`Error saving colors: ${err.message}`);
  }
}

function showSnackbar(message, color = 'error') {
  snackbar.message = message;
  snackbar.color = color;
  snackbar.show = true;
}

// --- Load --------------------------------------------------------------------
async function loadCustomTypes() {
  try {
    const token = localStorage.getItem('auth-token');
    const response = await fetch('/api/content-library/custom-types/', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) return;
    const data = await response.json();
    if (!data.custom_types) return;
    customEntries.value = data.custom_types.map((ct) => ({
      key: String(ct.type_name).toLowerCase(),
      label: ct.type_name,
      category: 'custom-rundown',
      default: ct.color || 'grey',
      description: 'Custom rundown type',
      preview: 'rundown-row',
    }));
  } catch (e) {
    // custom types are optional; ignore failures
  }
}

async function initValues() {
  // Seed every known slot with its default first.
  for (const e of allEntries.value) {
    if (values[e.key] === undefined) values[e.key] = e.default;
  }
  // Overlay stored values. Backend already normalizes to canonical keys.
  try {
    const token = localStorage.getItem('auth-token');
    const response = await fetch('/api/settings/colors?profile=default', {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (response.ok) {
      const data = await response.json();
      if (data.success && data.colors) {
        for (const [key, value] of Object.entries(data.colors)) {
          values[key] = value;
          // Surface any stored key that isn't in the registry as a misc entry
          // so the user can still see/edit it rather than it silently vanishing.
          if (!registryByKey[key] && !customEntries.value.some((e) => e.key === key)) {
            customEntries.value.push({
              key,
              label: key,
              category: 'general-ui',
              default: value,
              description: 'Stored color (not in registry)',
              preview: 'swatch',
            });
          }
        }
      }
    }
  } catch (e) {
    // fall back to defaults already seeded
  }
  saveState.value = 'saved';
}

onMounted(async () => {
  await loadCustomTypes();
  await initValues();
  // Expand the first couple of categories by default for orientation.
  expanded['core-rundown'] = true;
  expanded['status'] = true;
});
</script>

<style scoped>
.color-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Toolbar */
.cs-toolbar {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 4px;
  background: var(--v-theme-surface, #fff);
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.cs-search {
  max-width: 320px;
  flex: 1 1 auto;
}
.cs-toolbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
}
.cs-save-state {
  display: inline-flex;
  align-items: center;
  font-size: 0.8rem;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 12px;
}
.cs-save-saved { color: #2e7d32; }
.cs-save-unsaved { color: #ef6c00; }
.cs-save-saving { color: #1565c0; }
.cs-save-error { color: #c62828; }

/* Categories */
.cs-category {
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 6px;
  margin-bottom: 8px;
  overflow: hidden;
}
.cs-category-header {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.03);
  border: none;
  cursor: pointer;
  font-weight: 600;
  text-align: left;
}
.cs-category-label { flex: 1 1 auto; }
.cs-category-count {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.5);
  background: rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  padding: 1px 8px;
}

/* Rows */
.cs-rows { padding: 4px 0; }
.cs-row {
  display: grid;
  grid-template-columns: 1fr 180px 160px 36px;
  align-items: center;
  gap: 12px;
  padding: 6px 12px;
}
.cs-row:hover { background: rgba(0, 0, 0, 0.02); }
.cs-row-label { display: flex; flex-direction: column; min-width: 0; }
.cs-row-name { font-weight: 500; }
.cs-row-desc {
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.55);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Swatch button */
.cs-swatch-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 32px;
  padding: 0 8px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.78rem;
}
.cs-swatch-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Row inline preview */
.cs-row-preview { min-width: 0; }
.cs-preview {
  display: inline-flex;
  align-items: center;
  height: 28px;
  padding: 0 10px;
  border-radius: 4px;
  font-size: 0.78rem;
  font-weight: 500;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.cs-preview--status-badge { border-radius: 12px; text-transform: uppercase; font-size: 0.7rem; }
.cs-preview--rundown-row,
.cs-preview--cue-card { border-radius: 3px; }

.cs-reset-spacer { display: inline-block; width: 28px; }

/* Popover */
.cs-popover { padding: 12px; }
.cs-popover-section-title {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  color: rgba(0, 0, 0, 0.55);
  margin: 6px 0 4px;
}
.cs-base-grid {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 4px;
}
.cs-base-swatch {
  width: 100%;
  aspect-ratio: 1;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 3px;
  cursor: pointer;
  padding: 0;
}
.cs-base-swatch.active {
  outline: 2px solid #1565c0;
  outline-offset: 1px;
}
.cs-variant-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.cs-variant-chip {
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 3px;
  padding: 3px 8px;
  font-size: 0.72rem;
  cursor: pointer;
}
.cs-variant-chip.active { outline: 2px solid #1565c0; outline-offset: 1px; }
.cs-preview-wrap { padding: 4px 0; }
.cs-popover-actions { display: flex; justify-content: flex-end; margin-top: 4px; }

.cs-empty {
  padding: 24px;
  text-align: center;
  color: rgba(0, 0, 0, 0.5);
}

/* Compact tweaks */
.compact .cs-row {
  grid-template-columns: 1fr 150px 130px 32px;
  padding: 4px 8px;
}
</style>
