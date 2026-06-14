// colorRegistry.js — SINGLE SOURCE OF TRUTH for the UI color system.
//
// Every configurable UI color is one entry in `colorRegistry` below. From this
// one ordered list we derive:
//   - themeColorMap.js `defaultColors` (the fallback palette)
//   - the ColorSelector picker's categories, labels, and ordering
//   - the legacy-key fold used to normalize the historically-polluted DB profile
//
// CANONICAL KEYS ARE LOWERCASE PLAIN STRINGS (e.g. 'selection', 'draft').
// The old PascalCase + suffix scheme ('Selection-interface', 'Draft-script',
// 'AutoSave-global', 'Block-Header-ui') is DEAD. It survives only as `legacyKeys`
// on the relevant entries so old stored data still resolves during the transition.
//
// Color VALUES use the Vuetify "base[-variant]" grammar (e.g. 'blue-lighten-4').
// Only `splitColor`/`composeColor` below know that grammar.

// ---------------------------------------------------------------------------
// Categories (ordered) — drive the picker's grouping.
// ---------------------------------------------------------------------------
export const colorCategories = [
  { id: 'core-rundown', label: 'Core Rundown Items' },
  { id: 'custom-rundown', label: 'Custom Rundown Items' }, // populated at runtime
  { id: 'regions', label: 'Rundown Regions' },
  { id: 'elements-cues', label: 'Elements & Cues' },
  { id: 'action-rundown', label: 'Rundown Action Colors' },
  { id: 'status', label: 'Status Colors' },
  { id: 'action-global', label: 'Global Action Colors' },
  { id: 'general-ui', label: 'General UI' },
  { id: 'ai', label: 'AI Interaction States' },
];

// ---------------------------------------------------------------------------
// The registry. `default` values match the historical themeColorMap defaults.
// `legacyKeys` lists old DB keys that fold into this entry's canonical key.
// `preview` selects which live-preview widget the picker renders for this slot.
// ---------------------------------------------------------------------------
export const colorRegistry = [
  // --- Core Rundown Items ---
  { key: 'segment', label: 'Segment', category: 'core-rundown', default: 'info', description: 'Top-level rundown segment', preview: 'rundown-row' },
  { key: 'ad', label: 'Ad', category: 'core-rundown', default: 'primary', description: 'Advertising break', preview: 'rundown-row' },
  { key: 'promo', label: 'Promo', category: 'core-rundown', default: 'success', description: 'Promotional spot', preview: 'rundown-row' },
  { key: 'cta', label: 'CTA', category: 'core-rundown', default: 'accent', description: 'Call to action', preview: 'rundown-row' },
  { key: 'live', label: 'Live', category: 'core-rundown', default: 'red', description: 'Live shot', preview: 'rundown-row' },
  { key: 'tease', label: 'Tease', category: 'core-rundown', default: 'pink', description: 'Tease', preview: 'rundown-row' },
  { key: 'tag', label: 'Tag', category: 'core-rundown', default: 'indigo', description: 'Tag', preview: 'rundown-row' },

  // --- Rundown Regions ---
  { key: 'break', label: 'Break', category: 'regions', default: 'grey', description: 'Commercial break region', preview: 'rundown-row' },
  { key: 'block', label: 'Block', category: 'regions', default: 'grey-darken-1', description: 'Generic block region', preview: 'rundown-row' },
  { key: 'block-a', label: 'Block A', category: 'regions', default: 'blue', description: 'Block A', preview: 'rundown-row' },
  { key: 'block-b', label: 'Block B', category: 'regions', default: 'green', description: 'Block B', preview: 'rundown-row' },
  { key: 'block-c', label: 'Block C', category: 'regions', default: 'purple', description: 'Block C', preview: 'rundown-row' },
  { key: 'block-d', label: 'Block D', category: 'regions', default: 'red', description: 'Block D', preview: 'rundown-row' },
  { key: 'block-e', label: 'Block E', category: 'regions', default: 'orange', description: 'Block E', preview: 'rundown-row' },
  { key: 'block-f', label: 'Block F', category: 'regions', default: 'cyan', description: 'Block F', preview: 'rundown-row' },
  { key: 'block-g', label: 'Block G', category: 'regions', default: 'pink', description: 'Block G', preview: 'rundown-row' },
  { key: 'block-h', label: 'Block H', category: 'regions', default: 'yellow', description: 'Block H', preview: 'rundown-row' },
  { key: 'rejoin', label: 'Rejoin', category: 'regions', default: 'deep-orange', description: 'Rejoin marker', preview: 'rundown-row' },
  { key: 'close', label: 'Close', category: 'regions', default: 'amber', description: 'Close marker', preview: 'rundown-row' },

  // --- Elements & Cues ---
  { key: 'trans', label: 'Transition', category: 'elements-cues', default: 'secondary', description: 'Transition', preview: 'cue-card' },
  { key: 'pkg', label: 'Package', category: 'elements-cues', default: 'purple', description: 'Package', preview: 'cue-card' },
  { key: 'vo', label: 'Voice Over', category: 'elements-cues', default: 'deep-orange', description: 'Voice over', preview: 'cue-card' },
  { key: 'sot', label: 'SOT', category: 'elements-cues', default: 'amber', description: 'Sound on tape', preview: 'cue-card' },
  { key: 'interview', label: 'Interview', category: 'elements-cues', default: 'teal', description: 'Interview', preview: 'cue-card' },
  { key: 'music', label: 'Music', category: 'elements-cues', default: 'orange', description: 'Music', preview: 'cue-card' },
  { key: 'reader', label: 'Reader', category: 'elements-cues', default: 'amber-lighten-2', description: 'Reader', preview: 'cue-card' },
  { key: 'gfx', label: 'Graphics', category: 'elements-cues', default: 'cyan', description: 'Graphics', preview: 'cue-card' },
  { key: 'fsq', label: 'Full Screen Quote', category: 'elements-cues', default: 'lime', description: 'Full screen quote', preview: 'cue-card' },
  { key: 'nat', label: 'Nat Sound', category: 'elements-cues', default: 'light-green', description: 'Natural sound', preview: 'cue-card' },
  { key: 'img', label: 'Image', category: 'elements-cues', default: 'purple-lighten-2', description: 'Image', preview: 'cue-card' },
  { key: 'dir', label: 'Director Note', category: 'elements-cues', default: 'amber-darken-3', description: 'Director note', preview: 'cue-card' },
  { key: 'bump', label: 'Bump', category: 'elements-cues', default: 'purple-darken-2', description: 'Bumper', preview: 'cue-card' },
  { key: 'sting', label: 'Sting', category: 'elements-cues', default: 'pink-darken-2', description: 'Stinger', preview: 'cue-card' },
  { key: 'stinger', label: 'Stinger', category: 'elements-cues', default: 'pink-darken-2', description: 'Stinger (alias)', preview: 'cue-card' },
  { key: 'vox', label: 'Vox Pop', category: 'elements-cues', default: 'yellow', description: 'Vox pop', preview: 'cue-card' },
  { key: 'note', label: 'Note', category: 'elements-cues', default: 'amber-darken-3', description: 'Note', preview: 'cue-card' },
  { key: 'credits', label: 'Credits', category: 'elements-cues', default: 'blue-grey', description: 'Credits', preview: 'cue-card' },
  { key: 'weather', label: 'Weather', category: 'elements-cues', default: 'light-blue', description: 'Weather', preview: 'cue-card' },
  { key: 'sports', label: 'Sports', category: 'elements-cues', default: 'green-darken-2', description: 'Sports', preview: 'cue-card' },
  { key: 'brief', label: 'Brief', category: 'elements-cues', default: 'grey-lighten-2', description: 'News brief', preview: 'cue-card' },
  { key: 'openclose', label: 'Open/Close', category: 'elements-cues', default: 'purple-darken-2', description: 'Open/close', preview: 'cue-card' },
  { key: 'coldopen', label: 'Cold Open', category: 'elements-cues', default: 'teal-darken-3', description: 'Cold open', preview: 'cue-card' },
  { key: 'cut', label: 'Cut', category: 'elements-cues', default: 'red-darken-1', description: 'Hard cut', preview: 'cue-card' },
  { key: 'fade', label: 'Fade', category: 'elements-cues', default: 'blue-grey-darken-1', description: 'Fade', preview: 'cue-card' },
  { key: 'rif', label: 'Riff', category: 'elements-cues', default: 'deep-purple-lighten-1', description: 'Riff', preview: 'cue-card' },

  // --- Rundown Action Colors (was '-interface' suffix) ---
  { key: 'selection', label: 'Selection', category: 'action-rundown', default: 'warning', description: 'Highlight for the selected rundown row', preview: 'swatch', legacyKeys: ['Selection-interface'] },
  { key: 'hover', label: 'Hover', category: 'action-rundown', default: 'blue-lighten-4', description: 'Row hover highlight', preview: 'swatch', legacyKeys: ['Hover-interface'] },
  { key: 'highlight', label: 'Highlight', category: 'action-rundown', default: 'yellow-lighten-3', description: 'General highlight', preview: 'swatch', legacyKeys: ['Highlight-interface'] },
  { key: 'dropline', label: 'Drop Line', category: 'action-rundown', default: 'green-lighten-4', description: 'Drag-drop insertion line', preview: 'swatch', legacyKeys: ['Dropline-interface'] },
  { key: 'draglight', label: 'Drag Light', category: 'action-rundown', default: 'cyan-lighten-4', description: 'Drag target highlight', preview: 'swatch', legacyKeys: ['DragLight-interface'] },
  { key: 'locatorflash', label: 'Locator Flash', category: 'action-rundown', default: 'deep-orange-lighten-1', description: 'Flash when locating an item', preview: 'swatch', legacyKeys: ['LocatorFlash-interface'] },

  // --- Status Colors (was '-script' suffix) ---
  { key: 'draft', label: 'Draft', category: 'status', default: 'grey-darken-2', description: 'Not yet approved', preview: 'status-badge', legacyKeys: ['Draft-script'] },
  { key: 'approved', label: 'Approved', category: 'status', default: 'green-accent', description: 'Approved', preview: 'status-badge', legacyKeys: ['Approved-script'] },
  { key: 'production', label: 'Production', category: 'status', default: 'blue-accent', description: 'In production', preview: 'status-badge', legacyKeys: ['Production-script'] },
  { key: 'promotion', label: 'Promotion', category: 'status', default: 'deep-orange', description: 'In promotion', preview: 'status-badge', legacyKeys: ['Promotion-script'] },
  { key: 'scheduled', label: 'Scheduled', category: 'status', default: 'deep-orange', description: 'Scheduled', preview: 'status-badge', legacyKeys: ['Scheduled-script'] },
  { key: 'running', label: 'Running', category: 'status', default: 'green-accent', description: 'In flight', preview: 'status-badge', legacyKeys: ['Running-script'] },
  { key: 'completed', label: 'Completed', category: 'status', default: 'yellow-accent', description: 'Completed', preview: 'status-badge', legacyKeys: ['Completed-script'] },

  // --- Global Action Colors (was '-global' suffix) ---
  { key: 'autosave', label: 'Auto Save Indicator', category: 'action-global', default: 'info', description: 'Auto-save activity indicator', preview: 'swatch', legacyKeys: ['AutoSave-global'] },
  { key: 'needs-attention', label: 'Needs Attention', category: 'action-global', default: 'orange-lighten-3', description: 'Flagged item / paragraph', preview: 'swatch', legacyKeys: ['Needs-Attention-global'] },
  { key: 'complete', label: 'Complete', category: 'action-global', default: 'green', description: 'Completed / done indicator (e.g. cue cards)', preview: 'swatch' },
  { key: 'urgent-attention', label: 'Urgent Attention', category: 'action-global', default: 'red-darken-2', description: 'Urgent flag requiring immediate action', preview: 'swatch' },

  // --- General UI (was '-ui' suffix) ---
  { key: 'block-header', label: 'Block Header', category: 'general-ui', default: 'blue', description: 'Sidebar block header background', preview: 'swatch', legacyKeys: ['Block-Header-ui'] },

  // --- AI Interaction States ---
  { key: 'ai-analyzing', label: 'AI Analyzing', category: 'ai', default: 'amber', description: 'AI considering something', preview: 'swatch' },
  { key: 'ai-rejected', label: 'AI Needs Review', category: 'ai', default: 'red', description: 'AI change pending / needs human attention', preview: 'swatch' },
  { key: 'ai-approved', label: 'AI Approved', category: 'ai', default: 'green', description: 'AI generation approved by user', preview: 'swatch' },
  { key: 'ai-auto', label: 'AI Auto', category: 'ai', default: 'blue', description: 'AI auto-generation, no approval needed', preview: 'swatch' },
  { key: 'ai-generated', label: 'AI Generated', category: 'ai', default: 'deep-purple-lighten-1', description: 'LLM-generated field / content indicator (purple)', preview: 'swatch' },

  // --- Fallback ---
  { key: 'unknown', label: 'Unknown', category: 'general-ui', default: 'grey', description: 'Fallback for unrecognized types', preview: 'swatch' },
];

// ---------------------------------------------------------------------------
// Derived lookups.
// ---------------------------------------------------------------------------
export const registryByKey = Object.fromEntries(
  colorRegistry.map((e) => [e.key, e])
);

// legacyKeyMap: every old key (and its lowercased form, since getColorValue
// lowercases its argument) -> canonical key. The ONLY acknowledgement of the
// dead naming scheme anywhere in the codebase.
export const legacyKeyMap = (() => {
  const map = {};
  for (const entry of colorRegistry) {
    if (!entry.legacyKeys) continue;
    for (const legacy of entry.legacyKeys) {
      map[legacy] = entry.key;
      map[legacy.toLowerCase()] = entry.key;
    }
  }
  return map;
})();

/**
 * Normalize a raw colors dict (from DB or localStorage) into canonical keys.
 * - lowercases every key
 * - folds legacy keys to their canonical key
 * - on collision (both legacy and canonical present), CANONICAL WINS
 * - keeps unknown keys pass-through so nothing silently disappears
 */
export function normalizeColorKeys(rawColors) {
  if (!rawColors || typeof rawColors !== 'object') return {};
  const out = {};
  const canonicalSeen = new Set();

  // First pass: canonical/unknown keys (canonical wins over any legacy alias).
  for (const [rawKey, value] of Object.entries(rawColors)) {
    const lower = String(rawKey).toLowerCase();
    if (legacyKeyMap[rawKey] || legacyKeyMap[lower]) continue; // handled in pass 2
    out[lower] = value;
    canonicalSeen.add(lower);
  }

  // Second pass: fold legacy keys, but never clobber a canonical value.
  for (const [rawKey, value] of Object.entries(rawColors)) {
    const lower = String(rawKey).toLowerCase();
    const canonical = legacyKeyMap[rawKey] || legacyKeyMap[lower];
    if (!canonical) continue;
    if (canonicalSeen.has(canonical)) continue; // canonical already won
    out[canonical] = value;
  }

  return out;
}

// ---------------------------------------------------------------------------
// Base color + variant model (moved out of ColorSelector.vue, now data-driven).
// ---------------------------------------------------------------------------
export const MATERIAL_COLORS = [
  'red', 'pink', 'purple', 'deep-purple', 'indigo', 'blue',
  'light-blue', 'cyan', 'teal', 'green', 'light-green', 'lime',
  'yellow', 'amber', 'orange', 'deep-orange', 'brown',
  'blue-grey', 'grey', 'black', 'white',
];

export const THEME_COLORS = [
  'primary', 'secondary', 'accent', 'error', 'info', 'success', 'warning',
];

export const BASE_COLORS = [...MATERIAL_COLORS, ...THEME_COLORS];

// Per-material-color variant availability (matches the real Vuetify palette).
const MATERIAL_VARIANTS = {
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
  'grey': { lighten: 4, darken: 4, accent: false },
};

/**
 * Returns the list of variant options available for a given base color.
 * Each option: { title, value } where value '' means the plain base.
 */
export function getVariantsForBase(base) {
  const variants = [{ title: 'Base', value: '' }];
  if (!base) return variants;

  if (THEME_COLORS.includes(base)) {
    for (let i = 4; i >= 1; i--) variants.push({ title: `Lighten ${i}`, value: `lighten-${i}` });
    for (let i = 1; i <= 4; i++) variants.push({ title: `Darken ${i}`, value: `darken-${i}` });
    return variants;
  }

  if (base === 'black' || base === 'white') return variants;

  const cfg = MATERIAL_VARIANTS[base] || { lighten: 4, darken: 4, accent: false };
  for (let i = cfg.lighten; i >= 1; i--) variants.push({ title: `Lighten ${i}`, value: `lighten-${i}` });
  for (let i = 1; i <= cfg.darken; i++) variants.push({ title: `Darken ${i}`, value: `darken-${i}` });
  if (cfg.accent) variants.push({ title: 'Accent', value: 'accent' });
  return variants;
}

// Known variant suffixes, longest-first so 'lighten-5' beats 'lighten' etc.
const VARIANT_PATTERNS = [
  'lighten-5', 'lighten-4', 'lighten-3', 'lighten-2', 'lighten-1',
  'darken-4', 'darken-3', 'darken-2', 'darken-1',
  'accent-4', 'accent-3', 'accent-2', 'accent-1', 'accent',
  'base', 'dark', 'light',
];

/**
 * Split a composed Vuetify color string into { base, variant }.
 * 'blue-lighten-4' -> { base: 'blue', variant: 'lighten-4' }
 * 'blue'           -> { base: 'blue', variant: '' }
 */
export function splitColor(value) {
  if (!value) return { base: null, variant: '' };
  for (const pattern of VARIANT_PATTERNS) {
    if (value.endsWith('-' + pattern)) {
      return { base: value.slice(0, -(pattern.length + 1)), variant: pattern };
    }
  }
  return { base: value, variant: '' };
}

/**
 * Compose a base + variant back into a Vuetify color string.
 * ('blue', 'lighten-4') -> 'blue-lighten-4'; ('blue', '') -> 'blue'.
 */
export function composeColor(base, variant) {
  if (!base) return null;
  return variant ? `${base}-${variant}` : base;
}
