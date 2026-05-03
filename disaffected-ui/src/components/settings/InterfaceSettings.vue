<template>
  <v-card class="pa-0">
    <v-row no-gutters class="fill-height">
      <!-- Vertical Tabs on Left -->
      <v-col cols="3" class="border-r">
        <v-tabs
          v-model="interfaceSubTab"
          direction="vertical"
          color="primary"
          class="interface-vertical-tabs"
        >
          <v-tab value="editor" prepend-icon="mdi-file-document-edit">
            Content Editor
          </v-tab>
          <v-tab value="colors" prepend-icon="mdi-palette">
            Colors & Themes
          </v-tab>
          <v-tab value="theme" prepend-icon="mdi-theme-light-dark">
            Theme Settings
          </v-tab>
          <v-tab value="layout" prepend-icon="mdi-view-dashboard">
            Layout
          </v-tab>
          <v-tab value="accessibility" prepend-icon="mdi-wheelchair-accessibility">
            Accessibility
          </v-tab>
        </v-tabs>
      </v-col>

      <!-- Tab Content on Right -->
      <v-col cols="9">
        <v-tabs-window v-model="interfaceSubTab" class="pa-6">

          <!-- Content Editor Tab -->
          <v-tabs-window-item value="editor">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-file-document-edit</v-icon>
              Content Editor Settings
            </h3>
            <p class="text-body-2 mb-4">Configure how the content editor behaves and appears.</p>

            <!-- Font Settings -->
            <v-row>
              <v-col cols="12" md="6">
                <div class="setting-row">
                  <OverridableDot pref-key="editor.fontSize" :current-value="interfaceSettings.editorFontSize" :global-setter="makeInterfaceSettingsGlobalSetter('editorFontSize')" />
                  <v-slider
                    v-model="interfaceSettings.editorFontSize"
                    label="Font Size"
                    min="10"
                    max="24"
                    step="1"
                    thumb-label
                    class="setting-row-control"
                  >
                    <template v-slot:append>
                      <v-text-field
                        v-model="interfaceSettings.editorFontSize"
                        type="number"
                        style="width: 60px"
                        density="compact"
                        suffix="px"
                        hide-details
                      />
                    </template>
                  </v-slider>
                </div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="setting-row">
                  <OverridableDot pref-key="editor.fontFamily" :current-value="interfaceSettings.editorFontFamily" :global-setter="makeInterfaceSettingsGlobalSetter('editorFontFamily')" />
                  <v-select
                    v-model="interfaceSettings.editorFontFamily"
                    :items="[
                      { title: 'Monospace', value: 'monospace' },
                      { title: 'Arial', value: 'Arial, sans-serif' },
                      { title: 'Times New Roman', value: 'Times New Roman, serif' },
                      { title: 'Helvetica', value: 'Helvetica, sans-serif' }
                    ]"
                    label="Font Family"
                    class="setting-row-control"
                  />
                </div>
              </v-col>
            </v-row>

            <!-- Code Mode Settings -->
            <v-divider class="my-4"></v-divider>
            <h4 class="text-subtitle-1 mb-3">Code Mode Settings</h4>

            <div class="setting-row">
              <OverridableDot pref-key="editor.autoSave" :current-value="interfaceSettings.editorAutoSave" :global-setter="makeInterfaceSettingsGlobalSetter('editorAutoSave')" />
              <v-switch
                v-model="interfaceSettings.editorAutoSave"
                label="Auto-save"
                color="primary"
                class="setting-row-control"
              />
            </div>

            <!-- Script Mode Settings -->
            <v-divider class="my-4"></v-divider>
            <h4 class="text-subtitle-1 mb-3">Script Mode Settings</h4>

            <div class="setting-row">
              <OverridableDot pref-key="editor.lineNumbers" :current-value="interfaceSettings.editorLineNumbers" :global-setter="makeInterfaceSettingsGlobalSetter('editorLineNumbers')" />
              <v-switch
                v-model="interfaceSettings.editorLineNumbers"
                label="Show line numbers"
                color="primary"
                class="setting-row-control"
              />
            </div>

            <div class="setting-row">
              <OverridableDot pref-key="editor.wordWrap" :current-value="interfaceSettings.editorWordWrap" :global-setter="makeInterfaceSettingsGlobalSetter('editorWordWrap')" />
              <v-switch
                v-model="interfaceSettings.editorWordWrap"
                label="Word wrap"
                color="primary"
                class="setting-row-control"
              />
            </div>

            <div class="setting-row">
              <OverridableDot pref-key="editor.pastePlainTextOnly" :current-value="interfaceSettings.pastePlainTextOnly" :global-setter="makeInterfaceSettingsGlobalSetter('pastePlainTextOnly')" />
              <v-switch
                v-model="interfaceSettings.pastePlainTextOnly"
                label="Paste as plain text only"
                hint="Strip all formatting when pasting (removes colors, fonts, styles from copied text)"
                persistent-hint
                color="primary"
                class="setting-row-control"
              />
            </div>

            <!-- Autoformat Settings -->
            <v-divider class="my-4"></v-divider>
            <h4 class="text-subtitle-1 mb-3">
              <v-icon class="mr-1" size="small">mdi-auto-fix</v-icon>
              Autoformat Settings
            </h4>

            <v-alert
              type="info"
              variant="tonal"
              density="compact"
              class="mb-4"
            >
              <div class="text-body-2">
                <strong>What is autoformat?</strong> When enabled, the editor periodically scans your script content
                and fixes common formatting issues that occur when pasting from Google Docs or other sources.
                This runs in the background while you work.
              </div>
            </v-alert>

            <v-row align="center" class="mb-2">
              <v-col cols="12" md="6">
                <div class="setting-row">
                  <OverridableDot pref-key="editor.autoformatEnabled" :current-value="interfaceSettings.autoformatEnabled" :global-setter="makeInterfaceSettingsGlobalSetter('autoformatEnabled')" />
                  <v-switch
                    v-model="interfaceSettings.autoformatEnabled"
                    label="Enable autoformat"
                    color="primary"
                    density="compact"
                    hide-details
                    class="setting-row-control"
                  />
                </div>
              </v-col>
              <v-col cols="12" md="6">
                <div class="setting-row">
                  <OverridableDot pref-key="editor.autoformatInterval" :current-value="interfaceSettings.autoformatInterval" :global-setter="makeInterfaceSettingsGlobalSetter('autoformatInterval')" />
                  <v-slider
                    v-model="interfaceSettings.autoformatInterval"
                    :disabled="!interfaceSettings.autoformatEnabled"
                    label="Interval"
                    min="10"
                    max="120"
                    step="5"
                    thumb-label
                    hide-details
                    class="setting-row-control"
                  >
                    <template v-slot:append>
                      <v-text-field
                        v-model="interfaceSettings.autoformatInterval"
                        type="number"
                        style="width: 70px"
                        density="compact"
                        suffix="sec"
                        hide-details
                        :disabled="!interfaceSettings.autoformatEnabled"
                      />
                    </template>
                  </v-slider>
                </div>
              </v-col>
            </v-row>

            <!-- Autoformat Options with Explainers -->
            <v-expand-transition>
              <div v-if="interfaceSettings.autoformatEnabled">
                <p class="text-caption text-grey mb-3">Select which cleanup operations to perform:</p>

                <v-row>
                  <v-col cols="12" md="6">
                    <v-card variant="outlined" class="pa-3">
                      <div class="setting-row">
                        <OverridableDot pref-key="editor.autoformatStripSpans" :current-value="interfaceSettings.autoformatStripSpans" :global-setter="makeInterfaceSettingsGlobalSetter('autoformatStripSpans')" />
                        <v-switch
                          v-model="interfaceSettings.autoformatStripSpans"
                          label="Strip span tags"
                          color="primary"
                          density="compact"
                          hide-details
                          class="setting-row-control"
                        />
                      </div>
                      <p class="text-caption text-grey-darken-1 ml-10">
                        Google Docs wraps text in &lt;span&gt; tags with inline styles.
                        These often paste with unclosed tags that corrupt content.
                        Stripping them preserves bold/italic while removing junk.
                      </p>
                    </v-card>
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-card variant="outlined" class="pa-3">
                      <div class="setting-row">
                        <OverridableDot pref-key="editor.autoformatRemoveEmptyParagraphs" :current-value="interfaceSettings.autoformatRemoveEmptyParagraphs" :global-setter="makeInterfaceSettingsGlobalSetter('autoformatRemoveEmptyParagraphs')" />
                        <v-switch
                          v-model="interfaceSettings.autoformatRemoveEmptyParagraphs"
                          label="Remove empty paragraphs"
                          color="primary"
                          density="compact"
                          hide-details
                          class="setting-row-control"
                        />
                      </div>
                      <p class="text-caption text-grey-darken-1 ml-10">
                        Collapses multiple blank lines into one and removes
                        empty &lt;p&gt; tags that accumulate after cue insertions
                        or editing.
                      </p>
                    </v-card>
                  </v-col>
                </v-row>

                <v-row class="mt-2">
                  <v-col cols="12" md="6">
                    <v-card variant="outlined" class="pa-3">
                      <div class="setting-row">
                        <OverridableDot pref-key="editor.autoformatRemoveLeadingDashes" :current-value="interfaceSettings.autoformatRemoveLeadingDashes" :global-setter="makeInterfaceSettingsGlobalSetter('autoformatRemoveLeadingDashes')" />
                        <v-switch
                          v-model="interfaceSettings.autoformatRemoveLeadingDashes"
                          label="Remove leading dashes"
                          color="primary"
                          density="compact"
                          hide-details
                          class="setting-row-control"
                        />
                      </div>
                      <p class="text-caption text-grey-darken-1 ml-10">
                        Strips dashes from the start of paragraphs (e.g., "- Some text"
                        becomes "Some text"). Preserves actual bulleted lists where
                        multiple consecutive lines have dashes.
                      </p>
                    </v-card>
                  </v-col>
                  <v-col cols="12" md="6">
                    <v-card variant="outlined" class="pa-3">
                      <div class="setting-row">
                        <OverridableDot pref-key="editor.autoformatCleanWhitespace" :current-value="interfaceSettings.autoformatCleanWhitespace" :global-setter="makeInterfaceSettingsGlobalSetter('autoformatCleanWhitespace')" />
                        <v-switch
                          v-model="interfaceSettings.autoformatCleanWhitespace"
                          label="Clean whitespace"
                          color="primary"
                          density="compact"
                          hide-details
                          class="setting-row-control"
                        />
                      </div>
                      <p class="text-caption text-grey-darken-1 ml-10">
                        Converts &amp;nbsp; (non-breaking spaces) to regular spaces
                        and collapses multiple consecutive spaces into one.
                        Common issue from web copy-paste.
                      </p>
                    </v-card>
                  </v-col>
                </v-row>
              </div>
            </v-expand-transition>

            <v-divider class="my-4"></v-divider>
            <h4 class="text-subtitle-1 mb-3">Save Integrity</h4>
            <p class="text-body-2 mb-3" style="color: rgba(0,0,0,0.6);">
              Refuses to persist a save when the reconstructed script would be more than 30% shorter
              than the previous version (and the previous was non-trivial). Backstop for the
              data-loss bug we just hit on episode 272. Press
              <kbd>Ctrl</kbd>+<kbd>Alt</kbd>+<kbd>S</kbd> in the editor to allow one save through
              when you're intentionally deleting a large chunk.
            </p>
            <div class="setting-row">
              <v-switch
                v-model="interfaceSettings.scriptShrinkGuardEnabled"
                label="Enable shrink guard (recommended)"
                color="primary"
                class="setting-row-control"
                hide-details
              />
            </div>

            <v-divider class="my-4"></v-divider>
            <h4 class="text-subtitle-1 mb-3">Legacy Cue Convert</h4>
            <p class="text-body-2 mb-3" style="color: rgba(0,0,0,0.6);">
              Adds a <strong>Convert to Cue</strong> button on Auto-Scrub-flagged paragraphs that
              contain legacy <code>{SOT/foo}</code> or <code>(SOT/foo)</code> tokens. One click
              parses the token, generates a properly-typed AssetID, links a matching media file
              from the episode's <code>preshow/</code> folder when one exists, and replaces the
              token with a real cue block — preserving any prose around it. The toggle controls
              the button only; Auto Scrub keeps detecting and flagging legacy tokens whether the
              module is on or off. Model used for the media-match LLM tiebreaker is configured
              under Settings &rarr; LLM Routing.
            </p>
            <div class="setting-row">
              <v-switch
                v-model="interfaceSettings.legacyCueConvertEnabled"
                label="Enable Legacy Cue Convert"
                color="primary"
                class="setting-row-control"
                hide-details
              />
            </div>

            <div class="mt-4">
              <div class="d-flex align-center mb-1">
                <label class="text-body-2 font-weight-medium">Media-match LLM prompt:</label>
                <v-btn
                  size="x-small"
                  variant="text"
                  color="primary"
                  class="ml-2"
                  :loading="legacyCuePromptLoading"
                  @click="resetLegacyCuePrompt"
                >
                  Reset to default
                </v-btn>
              </div>
              <p v-pre class="text-caption mb-2" style="color: rgba(0,0,0,0.55);">
                Template variables: <code>{{type}}</code>, <code>{{slug}}</code>,
                <code>{{file_list}}</code>. Edits take effect on the next conversion that
                triggers the LLM tiebreaker.
              </p>
              <v-textarea
                v-model="legacyCuePromptDraft"
                :loading="legacyCuePromptLoading"
                rows="8"
                auto-grow
                variant="outlined"
                density="compact"
                hide-details
                class="font-mono mb-2"
                style="font-family: monospace; font-size: 12px;"
              />
              <v-btn
                size="small"
                color="primary"
                variant="tonal"
                :loading="legacyCuePromptSaving"
                :disabled="legacyCuePromptDraft === legacyCuePromptOriginal"
                @click="saveLegacyCuePrompt"
              >
                Save prompt
              </v-btn>
            </div>

            <v-divider class="my-4"></v-divider>

            <v-select
              v-model="interfaceSettings.cueCardAlignment"
              :items="[
                { title: 'Left', value: 'left' },
                { title: 'Center', value: 'center' },
                { title: 'Right', value: 'right' }
              ]"
              label="Cue Card Alignment"
              hint="How cue cards are aligned in script mode"
              persistent-hint
              class="mb-4"
            />

            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingInterface"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Editor Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Colors & Themes Tab -->
          <v-tabs-window-item value="colors">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-palette</v-icon>
              Colors & Theme Configuration
            </h3>
            <p class="text-body-2 mb-4">Configure segment colors, interface themes, and visual styling.</p>

            <!-- Color Selector Component -->
            <ColorSelector />

            <v-divider class="my-6" />

            <!-- Editor Display Sizes (per-user) -->
            <EditorDisplaySettings />

            <v-divider class="my-6" />

            <!-- Content Origin Indicators -->
            <h4 class="text-subtitle-1 mb-3 d-flex align-center">
              <v-icon class="mr-2" size="small">mdi-tag-text-outline</v-icon>
              Content Origin Indicators
            </h4>
            <p class="text-body-2 text-grey mb-4">
              Colors that indicate where content came from and its current status.
              Applied to text, field borders, and overlays throughout the editor.
              Add new indicators for any origin or status you need to track.
            </p>

            <div
              v-for="(indicator, index) in (interfaceSettings.contentIndicators || defaultIndicators)"
              :key="indicator.key"
              class="indicator-row mb-3 pa-3 rounded"
              :style="{ border: `2px solid ${indicator.borderColor}` }"
            >
              <div class="d-flex align-center mb-2">
                <v-icon size="small" class="mr-2" :style="{ color: indicator.textColor }">{{ indicator.icon }}</v-icon>
                <span class="text-body-2 font-weight-bold">{{ indicator.label }}</span>
                <v-spacer />
                <v-btn v-if="!indicator.locked" icon size="x-small" variant="text" color="grey" @click="removeIndicator(index)">
                  <v-icon size="small">mdi-close</v-icon>
                </v-btn>
              </div>
              <v-row dense>
                <v-col cols="6">
                  <v-text-field
                    :model-value="indicator.textColor"
                    @update:model-value="updateIndicator(index, 'textColor', $event)"
                    label="Text"
                    variant="outlined"
                    density="compact"
                    hide-details
                  >
                    <template v-slot:prepend-inner>
                      <input
                        type="color"
                        :value="indicator.textColor"
                        @input="updateIndicator(index, 'textColor', $event.target.value)"
                        style="width: 20px; height: 20px; border: none; cursor: pointer; padding: 0; background: none;"
                      />
                    </template>
                  </v-text-field>
                </v-col>
                <v-col cols="6">
                  <v-text-field
                    :model-value="indicator.borderColor"
                    @update:model-value="updateIndicator(index, 'borderColor', $event)"
                    label="Border"
                    variant="outlined"
                    density="compact"
                    hide-details
                  >
                    <template v-slot:prepend-inner>
                      <input
                        type="color"
                        :value="indicator.borderColor"
                        @input="updateIndicator(index, 'borderColor', $event.target.value)"
                        style="width: 20px; height: 20px; border: none; cursor: pointer; padding: 0; background: none;"
                      />
                    </template>
                  </v-text-field>
                </v-col>
              </v-row>
              <!-- Live preview -->
              <div class="mt-2 pa-2 rounded" :style="{ border: `1.5px solid ${indicator.borderColor}`, background: 'rgba(0,0,0,0.02)' }">
                <span class="text-caption" :style="{ color: indicator.textColor, fontStyle: 'italic' }">Preview: {{ indicator.label }} content looks like this.</span>
              </div>
            </div>

            <!-- Add new indicator -->
            <v-card variant="tonal" color="grey-lighten-3" class="pa-3 mb-4">
              <div class="text-caption font-weight-medium mb-2">Add New Indicator</div>
              <v-row dense>
                <v-col cols="4">
                  <v-text-field v-model="newIndicatorKey" label="Key" placeholder="e.g. approved" variant="outlined" density="compact" hide-details />
                </v-col>
                <v-col cols="4">
                  <v-text-field v-model="newIndicatorLabel" label="Label" placeholder="e.g. Approved" variant="outlined" density="compact" hide-details />
                </v-col>
                <v-col cols="4">
                  <v-btn color="primary" variant="tonal" block @click="addIndicator" :disabled="!newIndicatorKey.trim() || !newIndicatorLabel.trim()">
                    <v-icon left size="small">mdi-plus</v-icon> Add
                  </v-btn>
                </v-col>
              </v-row>
            </v-card>

            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingInterface"
              class="mt-4"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Color Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Theme Settings Tab -->
          <v-tabs-window-item value="theme">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-theme-light-dark</v-icon>
              Theme Settings
            </h3>
            <p class="text-body-2 mb-4">Configure the overall appearance and theme of the interface.</p>

            <v-select
              v-model="interfaceSettings.theme"
              :items="[
                { title: 'Dark', value: 'dark' },
                { title: 'Light', value: 'light' },
                { title: 'Auto', value: 'auto' }
              ]"
              label="Color Theme"
              class="mb-4"
            />

            <v-switch
              v-model="interfaceSettings.highContrast"
              label="High contrast mode"
              color="primary"
              class="mb-3"
            />

            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingInterface"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Theme Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Layout Tab -->
          <v-tabs-window-item value="layout">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-view-dashboard</v-icon>
              Layout Settings
            </h3>
            <p class="text-body-2 mb-4">Configure the layout and behavior of interface elements.</p>

            <v-slider
              v-model="interfaceSettings.sidebarWidth"
              label="Sidebar Width"
              min="200"
              max="500"
              step="10"
              thumb-label
              class="mb-4"
            >
              <template v-slot:append>
                <v-text-field
                  v-model="interfaceSettings.sidebarWidth"
                  type="number"
                  style="width: 80px"
                  density="compact"
                  suffix="px"
                  hide-details
                />
              </template>
            </v-slider>

            <v-switch
              v-model="interfaceSettings.compactMode"
              label="Compact mode"
              color="primary"
              class="mb-3"
            />

            <v-switch
              v-model="interfaceSettings.showToolbarLabels"
              label="Show toolbar labels"
              color="primary"
              class="mb-3"
            />

            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingInterface"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Layout Settings
            </v-btn>
          </v-tabs-window-item>

          <!-- Accessibility Tab -->
          <v-tabs-window-item value="accessibility">
            <h3 class="text-h6 mb-4">
              <v-icon left>mdi-wheelchair-accessibility</v-icon>
              Accessibility Options
            </h3>
            <p class="text-body-2 mb-4">Configure accessibility features and preferences.</p>

            <v-switch
              v-model="interfaceSettings.reducedMotion"
              label="Reduce motion and animations"
              color="primary"
              class="mb-3"
            />

            <v-switch
              v-model="interfaceSettings.keyboardShortcuts"
              label="Enable keyboard shortcuts"
              color="primary"
              class="mb-3"
            />

            <v-btn
              color="primary"
              @click="handleSave"
              :loading="savingInterface"
            >
              <v-icon left>mdi-content-save</v-icon>
              Save Accessibility Settings
            </v-btn>
          </v-tabs-window-item>

        </v-tabs-window>
      </v-col>
    </v-row>
  </v-card>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import axios from 'axios'
import ColorSelector from '@/components/ColorSelector.vue'
import OverridableDot from '@/components/OverridableDot.vue'
import EditorDisplaySettings from '@/components/settings/EditorDisplaySettings.vue'
import { useUserPrefs } from '@/composables/useUserPrefs'

const _userPrefs = useUserPrefs()

/**
 * Build a globalSetter for a field nested inside the interface.settings
 * blob. The dot's "Save as global default" button uses this so flipping
 * a switch globally writes the merged blob, not a stranded per-key row.
 */
function makeInterfaceSettingsGlobalSetter(fieldName) {
  return async (value) => {
    const current = _userPrefs.get('interface.settings', null)
    const next = { ...(current || {}), [fieldName]: value }
    await _userPrefs.set('interface.settings', next, { scope: 'global' })
  }
}

// Component props
const props = defineProps({
  modelValue: {
    type: Object,
    required: true
  }
})

// Component emits
const emit = defineEmits(['update:modelValue', 'save'])

// Interface sub-tab state
const interfaceSubTab = ref('editor')

// Loading state
const savingInterface = ref(false)

// Local reactive copy of interface settings
const interfaceSettings = ref({ ...props.modelValue })

// Save-integrity: shrink guard toggle is mirrored to localStorage so the
// editor's useScriptCore composable sees the same value without a backend
// round-trip. Seed the local form from localStorage if the parent didn't
// supply a value yet (default true).
const SHRINK_GUARD_LS_KEY = 'show-build:scriptShrinkGuardEnabled'
if (typeof interfaceSettings.value.scriptShrinkGuardEnabled === 'undefined') {
  try {
    const ls = localStorage.getItem(SHRINK_GUARD_LS_KEY)
    interfaceSettings.value.scriptShrinkGuardEnabled = ls === null ? true : ls === 'true'
  } catch (_e) {
    interfaceSettings.value.scriptShrinkGuardEnabled = true
  }
}
watch(
  () => interfaceSettings.value.scriptShrinkGuardEnabled,
  (v) => {
    try {
      localStorage.setItem(SHRINK_GUARD_LS_KEY, v ? 'true' : 'false')
    } catch (_e) { /* ignore */ }
  }
)

// Legacy Cue Convert: same localStorage-mirror pattern as the shrink guard.
// The editor's useLegacyCueConvertEnabled composable reads this key and
// listens for cross-tab 'storage' events.
const LEGACY_CUE_CONVERT_LS_KEY = 'show-build:legacyCueConvertEnabled'
if (typeof interfaceSettings.value.legacyCueConvertEnabled === 'undefined') {
  try {
    const ls = localStorage.getItem(LEGACY_CUE_CONVERT_LS_KEY)
    interfaceSettings.value.legacyCueConvertEnabled = ls === null ? true : ls === 'true'
  } catch (_e) {
    interfaceSettings.value.legacyCueConvertEnabled = true
  }
}
watch(
  () => interfaceSettings.value.legacyCueConvertEnabled,
  (v) => {
    try {
      localStorage.setItem(LEGACY_CUE_CONVERT_LS_KEY, v ? 'true' : 'false')
    } catch (_e) { /* ignore */ }
  }
)

// Legacy Cue Convert: editable LLM media-match prompt, persisted server-side
// via api_configs (workflow=generation, category=llm, service=legacy_cue_convert,
// config_key=media_match_prompt). Three endpoints:
//   GET    /api/legacy-cue-convert/media-match-prompt
//   PUT    /api/legacy-cue-convert/media-match-prompt
//   POST   /api/legacy-cue-convert/media-match-prompt/reset
const legacyCuePromptDraft = ref('')
const legacyCuePromptOriginal = ref('')
const legacyCuePromptLoading = ref(false)
const legacyCuePromptSaving = ref(false)

async function loadLegacyCuePrompt() {
  legacyCuePromptLoading.value = true
  try {
    const res = await axios.get('/api/legacy-cue-convert/media-match-prompt')
    legacyCuePromptDraft.value = res.data?.prompt || ''
    legacyCuePromptOriginal.value = legacyCuePromptDraft.value
  } catch (err) {
    console.warn('[LegacyCueConvert] failed to load prompt:', err)
  } finally {
    legacyCuePromptLoading.value = false
  }
}

async function saveLegacyCuePrompt() {
  legacyCuePromptSaving.value = true
  try {
    const res = await axios.put('/api/legacy-cue-convert/media-match-prompt', {
      prompt: legacyCuePromptDraft.value,
    })
    legacyCuePromptOriginal.value = res.data?.prompt || legacyCuePromptDraft.value
  } catch (err) {
    console.error('[LegacyCueConvert] failed to save prompt:', err)
  } finally {
    legacyCuePromptSaving.value = false
  }
}

async function resetLegacyCuePrompt() {
  legacyCuePromptLoading.value = true
  try {
    const res = await axios.post('/api/legacy-cue-convert/media-match-prompt/reset')
    legacyCuePromptDraft.value = res.data?.prompt || ''
    legacyCuePromptOriginal.value = legacyCuePromptDraft.value
  } catch (err) {
    console.error('[LegacyCueConvert] failed to reset prompt:', err)
  } finally {
    legacyCuePromptLoading.value = false
  }
}

onMounted(() => {
  loadLegacyCuePrompt()
})

// Watch for changes to props and update local state
watch(() => props.modelValue, (newValue) => {
  // Only update if values actually changed to avoid loops
  if (JSON.stringify(interfaceSettings.value) !== JSON.stringify(newValue)) {
    interfaceSettings.value = { ...newValue }
  }
}, { deep: true })

// Watch for changes to local state and emit updates
watch(interfaceSettings, (newValue) => {
  emit('update:modelValue', newValue)
}, { deep: true, flush: 'post' })

// --- Content Origin Indicators ---
const defaultIndicators = [
  { key: 'llm_generated', label: 'LLM Generated', icon: 'mdi-robot-outline', textColor: '#7e57c2', borderColor: '#7e57c2', locked: true },
  { key: 'imported', label: 'Imported', icon: 'mdi-import', textColor: '#1976d2', borderColor: '#1976d2', locked: false },
  { key: 'unverified', label: 'Unverified', icon: 'mdi-alert-circle-outline', textColor: '#ff9800', borderColor: '#ff9800', locked: false },
  { key: 'approved', label: 'Approved', icon: 'mdi-check-decagram', textColor: '#4caf50', borderColor: '#4caf50', locked: false }
]

// Initialize indicators if not present
if (!interfaceSettings.value.contentIndicators) {
  interfaceSettings.value.contentIndicators = [...defaultIndicators]
}

const newIndicatorKey = ref('')
const newIndicatorLabel = ref('')

function updateIndicator(index, field, value) {
  const indicators = interfaceSettings.value.contentIndicators || defaultIndicators
  indicators[index][field] = value
  interfaceSettings.value.contentIndicators = [...indicators]
}

function removeIndicator(index) {
  const indicators = interfaceSettings.value.contentIndicators || []
  indicators.splice(index, 1)
  interfaceSettings.value.contentIndicators = [...indicators]
}

function addIndicator() {
  const key = newIndicatorKey.value.trim().toLowerCase().replace(/\s+/g, '_')
  const label = newIndicatorLabel.value.trim()
  if (!key || !label) return
  const indicators = interfaceSettings.value.contentIndicators || []
  if (indicators.some(i => i.key === key)) return
  indicators.push({
    key,
    label,
    icon: 'mdi-tag-outline',
    textColor: '#9e9e9e',
    borderColor: '#9e9e9e',
    locked: false
  })
  interfaceSettings.value.contentIndicators = [...indicators]
  newIndicatorKey.value = ''
  newIndicatorLabel.value = ''
}

// Methods
const handleSave = () => {
  savingInterface.value = true
  // Only emit 'save', don't double-emit 'update:modelValue' since watcher already does it
  emit('save', interfaceSettings.value)
  // Reset loading state after a brief delay
  setTimeout(() => {
    savingInterface.value = false
  }, 1000)
}
</script>

<style scoped>
/* Layout for a settings row that has an OverridableDot to its left */
.setting-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.setting-row-control {
  flex: 1;
  margin-bottom: 0 !important;
}

.interface-vertical-tabs {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.border-r {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.indicator-row {
  background: rgba(0, 0, 0, 0.02);
  transition: border-color 0.2s;
}

.v-card {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}
</style>