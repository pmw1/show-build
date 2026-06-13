/**
 * Per-user content-editor display sizes, applied as CSS custom properties
 * on the document root so any component can opt in by reading the variable.
 *
 *   .script-paragraph { font-size: var(--editor-script-font-size, 16px); }
 *
 * Keys live under the `editor.display.*` namespace in useUserPrefs and
 * therefore travel with the user across devices. Changes apply instantly
 * (the watcher rewrites the CSS variable; no reload required).
 *
 * Usage:
 *   import { useEditorDisplayPrefs } from '@/composables/useEditorDisplayPrefs'
 *   useEditorDisplayPrefs().install()  // call once from App.vue (or main.js)
 */
import { computed, watch } from 'vue'
import { useUserPrefs } from './useUserPrefs'

// One row per knob — matches the keys defined in the user-sessions plan.
// Adding a new knob is two lines: append here + reference the CSS var
// from the appropriate component stylesheet.
const KNOBS = [
  { key: 'editor.display.scriptFontFamily',   cssVar: '--editor-script-font-family',   fallback: 'monospace', unit: '', min: null, max: null, step: null,
    options: [
      { title: 'Monospace', value: 'monospace' },
      { title: 'Sans Serif', value: 'sans-serif' },
      { title: 'Serif', value: 'serif' },
    ] },
  { key: 'editor.display.scriptFontSize',     cssVar: '--editor-script-font-size',     fallback: 16, unit: 'px',  min: 12, max: 24, step: 1 },
  { key: 'editor.display.scriptLineHeight',   cssVar: '--editor-script-line-height',   fallback: 1.5, unit: '',   min: 1.2, max: 2.0, step: 0.05 },
  { key: 'editor.display.cueBlockFontSize',   cssVar: '--editor-cue-font-size',        fallback: 13, unit: 'px',  min: 10, max: 18, step: 1 },
  { key: 'editor.display.cueBlockDensity',    cssVar: '--editor-cue-density',          fallback: 'comfortable', unit: '', min: null, max: null, step: null,
    densityToPad: { compact: '4px 6px', comfortable: '8px 10px', roomy: '12px 14px' } },
  { key: 'editor.display.imageMaxHeight',     cssVar: '--editor-image-max-height',     fallback: 160, unit: 'px', min: 60, max: 320, step: 10 },
  { key: 'editor.display.rundownItemFontSize', cssVar: '--editor-rundown-font-size',   fallback: 13, unit: 'px',  min: 11, max: 16, step: 1 },
]

// ── Special characters ───────────────────────────────────────────────────────
// Preset glyphs are a fixed code constant (common typographic/broadcast marks).
// The user's own pinned favorites live under a single user-pref key as an array
// of single-character strings, so they travel with the account like the knobs.
const CHAR_PRESETS = [
  { char: '—', name: 'Em dash' },
  { char: '–', name: 'En dash' },
  { char: '“', name: 'Left double quote' },
  { char: '”', name: 'Right double quote' },
  { char: '‘', name: 'Left single quote' },
  { char: '’', name: 'Right single quote / apostrophe' },
  { char: '…', name: 'Ellipsis' },
  { char: '•', name: 'Bullet' },
  { char: '©', name: 'Copyright' },
  { char: '®', name: 'Registered' },
  { char: '™', name: 'Trademark' },
  { char: '°', name: 'Degree' },
  { char: '×', name: 'Multiplication' },
  { char: '½', name: 'One half' },
  { char: '¼', name: 'One quarter' },
  { char: '¾', name: 'Three quarters' },
  { char: '€', name: 'Euro' },
  { char: '£', name: 'Pound' },
  { char: '¢', name: 'Cent' },
  { char: '§', name: 'Section' },
  { char: '¶', name: 'Pilcrow' },
  { char: '†', name: 'Dagger' },
  { char: '‡', name: 'Double dagger' },
  { char: '→', name: 'Right arrow' },
]
const CHAR_FAVORITES_KEY = 'editor.display.charFavorites'

function listCharPresets() {
  return CHAR_PRESETS.map(c => ({ ...c }))
}

const charFavorites = computed(() => {
  const v = useUserPrefs().get(CHAR_FAVORITES_KEY, [])
  return Array.isArray(v) ? v : []
})

async function addCharFavorite(char) {
  if (!char) return
  const cur = charFavorites.value
  if (cur.includes(char)) return
  return useUserPrefs().set(CHAR_FAVORITES_KEY, [...cur, char])
}

async function removeCharFavorite(char) {
  const cur = charFavorites.value
  if (!cur.includes(char)) return
  return useUserPrefs().set(CHAR_FAVORITES_KEY, cur.filter(c => c !== char))
}

function _format(knob, value) {
  if (knob.densityToPad) {
    return knob.densityToPad[value] || knob.densityToPad[knob.fallback]
  }
  // Select-type knob (e.g. font family): emit the chosen value verbatim, no unit.
  if (knob.options) {
    return String(value || knob.fallback)
  }
  if (value == null) return `${knob.fallback}${knob.unit}`
  return `${value}${knob.unit}`
}

function _applyAll() {
  const prefs = useUserPrefs()
  const root = document.documentElement
  for (const k of KNOBS) {
    const v = prefs.get(k.key, k.fallback)
    root.style.setProperty(k.cssVar, _format(k, v))
  }
}

let installed = false

function install() {
  if (installed) return
  installed = true
  // Initial apply (uses defaults; overrides land when prefs hydrate).
  _applyAll()
  // Reapply whenever any of the editor.display.* keys change.
  const prefs = useUserPrefs()
  watch(() => {
    const out = {}
    for (const k of KNOBS) out[k.key] = prefs.cache.value[k.key]
    return out
  }, _applyAll, { deep: true })
}

function getKnob(key) {
  return KNOBS.find(k => k.key === key)
}

function listKnobs() {
  return KNOBS.map(k => ({ ...k }))
}

const valueFor = computed(() => {
  const prefs = useUserPrefs()
  const out = {}
  for (const k of KNOBS) out[k.key] = prefs.get(k.key, k.fallback)
  return out
})

async function setKnob(key, value) {
  return useUserPrefs().set(key, value)
}

async function resetKnob(key) {
  return useUserPrefs().remove(key)
}

export function useEditorDisplayPrefs() {
  return {
    install,
    listKnobs,
    getKnob,
    valueFor,
    setKnob,
    resetKnob,
    // Special characters
    listCharPresets,
    charFavorites,
    addCharFavorite,
    removeCharFavorite,
  }
}
