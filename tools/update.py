#!/usr/bin/env python3

# Rules and Policies
# ------------------
# - Documentation Updates: Only Grok updates `docs/00_rehydration_main.markdown`, `docs/03_features_and_integrations.markdown`, `docs/06_todo_and_issues.markdown`, `docs/20_changelog.markdown`.
# - Rehydration: Do not update `rehydrate.md` directly; updates to `00_rehydration_main.markdown` are concatenated via `generate_rehydrate.sh`.
# - Obsidian: No plugin implementation exists; `main.js` is for reference and must be deleted.
# - Execution: User runs `update.py` with `python3 update.py` from `/mnt/process/show-build`.
# - Changelog: Log all changes in `20_changelog.markdown` with date/time, LLM, changes, reasons, and status.
# - Validation: Use DeepSeek V3 (`python3 -m sglang.launch_server --model deepseek-ai/DeepSeek-V3 --trust-remote-code`), unit tests (`npm test`), and manual tests.
# - File Operations: Verify file existence, back up changes to `backup_md_20250709` with timestamp.

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

# Setup
BASE_DIR = Path('/mnt/process/show-build')
BACKUP_DIR = BASE_DIR / 'backup_md_20250709'
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs(BACKUP_DIR, exist_ok=True)

# Logging
log_file = BASE_DIR / 'update.log'
log = open(log_file, 'a')

def log_message(message):
    print(message)
    log.write(f"{datetime.now()}: {message}\n")
    log.flush()

def backup_file(path):
    if path.exists():
        backup_path = BACKUP_DIR / f"{path.name}.{TIMESTAMP}"
        shutil.copy(path, backup_path)
        log_message(f"Backup created: {path} -> {backup_path}")

def write_file(path, content):
    backup_file(path)
    path.write_text(content, encoding='utf-8')
    log_message(f"Created/Updated: {path}")

# Urgent Fix: Restore ContentEditor.vue
CONTENT_EDITOR_PATH = BASE_DIR / 'disaffected-ui/src/components/ContentEditor.vue'
COLOR_SELECTOR_PATH = BASE_DIR / 'disaffected-ui/src/components/ColorSelector.vue'
ROUTER_PATH = BASE_DIR / 'disaffected-ui/src/router/index.js'

CONTENT_EDITOR_CONTENT = """<template>
  <div class="content-editor-wrapper">
    <v-toolbar dense flat class="main-toolbar" style="height: 128px; min-height: 128px; max-height: 128px; align-items: flex-start;">
      <v-spacer></v-spacer>
      <v-toolbar-items>
        <v-btn text @click="saveAllContent">Save</v-btn>
        <v-btn text>Publish</v-btn>
      </v-toolbar-items>
    </v-toolbar>
    <ShowInfoHeader
      :title="currentShowTitle"
      :episode-info="currentEpisodeInfo"
      :episode-number="currentEpisodeNumber"
      :air-date="currentAirDate"
      :production-status="currentProductionStatus"
      :total-runtime="totalRuntime"
      :episodes="episodes"
      :production-statuses="productionStatuses"
      @update:episodeNumber="handleEpisodeChange"
      @update:airDate="val => currentAirDate = val"
      @update:productionStatus="val => currentProductionStatus = val"
    />
    <ColorSelector />
    <div class="main-content-area">
      <v-card class="rundown-panel" flat :style="{ border: '2px solid ' + statusBarColor, borderRadius: '0' }">
        <div class="script-status-horizontal-bar" :style="{ backgroundColor: statusBarColor, color: statusBarTextColor }">
          <span class="status-text">{{ currentProductionStatus }}</span>
        </div>
        <div class="rundown-header-row">
          <span class="rundown-header-title">Rundown</span>
          <div style="flex:1"></div>
          <v-btn icon x-small class="rundown-header-btn" @click="showNewItemModal = true"><v-icon size="18">mdi-plus</v-icon></v-btn>
          <v-btn icon x-small class="rundown-header-btn"><v-icon size="18">mdi-dots-vertical</v-icon></v-btn>
        </div>
        <div>
          <div class="rundown-table-header">
            <div class="index-container">Index</div>
            <div class="item-type-cell">Type</div>
            <div class="item-details">Slug</div>
            <div class="item-duration">Duration</div>
          </div>
          <div class="rundown-list">
            <v-virtual-scroll
              :items="rundownItems"
              :item-height="26"
              bench="10"
            >
              <template v-slot:default="{ item, index }">
                <div
                  class="rundown-item"
                  :class="{
                    'selected-item': selectedItemIndex === index,
                    'ghost-class': isDragging && draggedIndex === index,
                    'drag-over-above': dragOverIndex === index && dropZonePosition === 'above',
                    'drag-over-below': dragOverIndex === index && dropZonePosition === 'below'
                  }"
                  :style="resolveItemStyle(item, index)"
                  draggable="true"
                  @click="selectRundownItem(index)"
                  @dragstart="dragStart($event, item, index)"
                  @dragend="dragEnd($event, item, index)"
                  @dragover.prevent="dragOver($event, index)"
                  @drop.prevent="dragDrop($event, index)"
                >
                  <div class="item-content">
                    <div class="index-container">
                      <span class="item-index">{{ index + 1 }}</span>
                    </div>
                    <div class="item-type-cell">
                      <span class="item-type">{{ item.type.toUpperCase() }}</span>
                    </div>
                    <div class="item-details">
                      <span class="item-slug">{{ item.slug.toLowerCase() }}</span>
                    </div>
                    <span class="item-duration">{{ item.duration }}</span>
                  </div>
                </div>
              </template>
            </v-virtual-scroll>
          </div>
        </div>
      </v-card>
      <div class="editor-panel">
        <EditorPanel
          :item="currentRundownItem"
          v-model:script-content="scriptContent"
          v-model:scratch-content="scratchContent"
          v-model:editor-mode="editorMode"
          @update:editor-mode="editorMode = $event"
          :has-unsaved-changes="hasUnsavedChanges"
          :show-rundown-panel="showRundownPanel"
          @save="saveAllContent"
          @toggle-rundown-panel="showRundownPanel = !showRundownPanel"
          @show-asset-modal="showAssetModal = true"
          @show-template-modal="showTemplateModal = true"
          @show-gfx-modal="showGfxModal = true"
          @show-fsq-modal="showFsqModal = true"
          @show-sot-modal="showSotModal = true"
          @show-vo-modal="showVoModal = true"
          @show-nat-modal="showNatModal = true"
          @show-pkg-modal="showPkgModal = true"
          @show-vox-modal="showVoxModal = true"
          @show-mus-modal="showMusModal = true"
          @show-live-modal="showLiveModal = true"
          @content-change="onContentChange"
          @metadata-change="onMetadataChange"
        />
      </div>
    </div>
    <AssetBrowserModal :visible="showAssetModal" @update:visible="showAssetModal = $event" @asset-selected="insertAssetReference" />
    <TemplateManagerModal :visible="showTemplateManagerModal" @update:visible="showTemplateManagerModal = $event" @template-selected="insertTemplateReference" />
    <GfxModal v-model:show="showGfxModal" @submit="submitGfx" />
    <FsqModal v-model:show="showFsqModal" @submit="submitFsq" />
    <SotModal v-model:show="showSotModal" @submit="submitSot" />
    <VoModal v-model:show="showVoModal" @submit="submitVo" />
    <NatModal v-model:show="showNatModal" @submit="submitNat" />
    <PkgModal v-model:show="showPkgModal" @submit="submitPkg" />
    <VoxModal v-model:show="showVoxModal" @submit="submitVox" />
    <MusModal v-model:show="showMusModal" @submit="submitMus" />
    <LiveModal v-model:show="showLiveModal" @submit="submitLive" />
    <NewItemModal
      v-model:show="showNewItemModal"
      v-model:valid="newItemFormValid"
      v-model:type="newItemType"
      v-model:slug="newItemSlug"
      v-model:duration="newItemDuration"
      v-model:description="newItemDescription"
      :loading="creatingNewItem"
      :item-types="rundownItemTypes"
      :duration-rules="durationRules"
      @create="createNewItem"
      @cancel="cancelNewItem"
    />
  </div>
</template>
<script>
import axios from 'axios';
import EditorPanel from './EditorPanel.vue';
import AssetBrowserModal from './modals/AssetBrowserModal.vue';
import TemplateManagerModal from './modals/TemplateManagerModal.vue';
import GfxModal from './modals/GfxModal.vue';
import FsqModal from './modals/FsqModal.vue';
import SotModal from './modals/SotModal.vue';
import VoModal from './modals/VoModal.vue';
import NatModal from './modals/NatModal.vue';
import PkgModal from './modals/PkgModal.vue';
import VoxModal from './modals/VoxModal.vue';
import MusModal from './modals/MusModal.vue';
import LiveModal from './modals/LiveModal.vue';
import NewItemModal from './modals/NewItemModal.vue';
import ColorSelector from './ColorSelector.vue';
import ShowInfoHeader from './content-editor/ShowInfoHeader.vue';
import { getColorValue, resolveVuetifyColor } from '../utils/themeColorMap';
import { debounce } from 'lodash-es';

export default {
  name: 'ContentEditor',
  components: {
    EditorPanel,
    AssetBrowserModal,
    TemplateManagerModal,
    GfxModal,
    FsqModal,
    SotModal,
    VoModal,
    NatModal,
    PkgModal,
    VoxModal,
    MusModal,
    LiveModal,
    NewItemModal,
    ColorSelector,
    ShowInfoHeader,
  },
  data() {
    return {
      showRundownPanel: true,
      rundownPanelWidth: 'wide',
      editorMode: 'script',
      selectedItemIndex: -1,
      editingItemIndex: -1,
      hasUnsavedChanges: false,
      loadingRundown: true,
      rundownError: null,
      showInfo: {},
      currentEpisodeNumber: '',
      currentAirDate: '',
      currentProductionStatus: 'draft',
      productionStatuses: [
        { title: 'Draft', value: 'draft' },
        { title: 'Approved', value: 'approved' },
        { title: 'Production', value: 'production' },
        { title: 'Completed', value: 'completed' }
      ],
      selectedEpisode: null,
      episodes: [],
      loading: false,
      saving: false,
      isDragging: false,
      draggedIndex: -1,
      draggedItem: null,
      dragOverIndex: -1,
      dropZonePosition: null,
      itemContentBackup: {},
      autoSaveOnSwitch: true,
      autoSaveTimeout: null,
      hoveredItemIndex: -1,
      scriptContent: '',
      scratchContent: '',
      showAssetModal: false,
      showTemplateManagerModal: false,
      selectedFiles: [],
      availableAssets: [],
      rundownItems: [],
      currentItemMetadata: {
        title: '', type: 'segment', slug: '', duration: '00:05:30', description: '', guests: '', tags: '', sponsor: '', campaign: '', segment_number: 1, live_status: 'live'
      },
      customMetadataYaml: '',
      itemTypes: [
        { title: 'Segment', value: 'segment' },
        { title: 'Advertisement', value: 'ad' },
        { title: 'Promo', value: 'promo' },
        { title: 'Call to Action', value: 'cta' },
        { title: 'Unknown', value: 'unknown' }
      ],
      showGfxModal: false, showFsqModal: false, showSotModal: false, showVoModal: false, showNatModal: false, showPkgModal: false,
      showVoxModal: false, showMusModal: false, showLiveModal: false,
      showNewItemModal: false, showRundownOptions: false,
      newItemFormValid: false, newItemType: '', newItemTitle: '', newItemSlug: '', newItemDuration: '', newItemDescription: '',
      newItemGuests: '', newItemCustomer: '', newItemLink: '', creatingNewItem: false,
      rundownItemTypes: [
        { title: 'Segment', value: 'segment' },
        { title: 'Advertisement', value: 'ad' },
        { title: 'Promo', value: 'promo' },
        { title: 'Call to Action', value: 'cta' },
        { title: 'Transition', value: 'trans' }
      ],
      graphicDetails: { url: '', file: null },
      gfxSlug: '', gfxDescription: '', graphicPreview: null, graphicFile: null,
      totalRuntime: '00:00:00',
      showTitle: 'Disaffected',
    };
  },
  computed: {
    styleCache() { const theme = this.$vuetify.theme; if (!theme) return {}; const cache = {}; const currentTheme = theme.dark ? 'dark' : 'light'; const themeColors = theme.themes[currentTheme]; const itemTypes = this.rundownItemTypes.map(t => t.value.toLowerCase()); const states = ['selection', 'hover', 'draglight', 'highlight', 'dropline']; const allColorSources = [...new Set([...states, ...itemTypes, 'unknown'])]; for (const source of allColorSources) { const colorName = getColorValue(source); const colorValue = themeColors[colorName]; if (colorValue) cache[source] = { backgroundColor: colorValue }; } return cache; },
    currentShowTitle() { return this.showTitle || (this.showInfo && this.showInfo.title) || 'Disaffected'; },
    currentEpisodeInfo() { try { const episode = this.episodes.find(e => e.id === this.selectedEpisodeId); if (!episode) return { title: 'No episode selected', status: 'unknown' }; return { title: episode.title, status: episode.status || 'unknown' }; } catch (error) { return { title: 'Error', status: 'error' }; } },
    rundownPanelWidthValue() { return this.rundownPanelWidth === 'narrow' ? '25%' : '40%'; },
    rundownHeaderWidth() { return this.rundownPanelWidth === 'narrow' ? '25%' : '40%'; },
    cueToolbarWidth() { return !this.showRundownPanel ? '100%' : (this.rundownPanelWidth === 'narrow' ? '75%' : '60%'); },
    statusBarColor() { try { const status = this.currentEpisodeInfo.status; const color = this.themeColorMap.status[status]; return color || 'grey'; } catch (error) { return 'grey'; } },
    statusBarTextColor() { try { const color = this.statusBarColor; return this.isDarkColor(color) ? 'white' : 'black'; } catch (error) { return 'black'; } },
    scriptPlaceholder() { return `# ${this.currentRundownItem?.slug || 'Script Content'}\\n\\nWrite your script content here using Markdown...\\n\\nUse the toolbar buttons above to insert:\\n- **GFX** cues for graphics\\n- **FSQ** cues for full-screen quotes  \\n- **SOT** cues for video content\\n\\nExample:\\n[GFX: opening_title.png]\\nWelcome to today's show...\\n\\n[SOT: interview_clip.mp4 | 0:30-2:15]\\nHere's what our guest had to say...`; },
    scratchPlaceholder() { return `# Brainstorming & Notes\\n\\nUse this space for:\\n• Research notes and ideas\\n• Asset planning and references  \\n• Interview questions\\n• Production notes\\n\\n💡 **Smart Features:**\\n- Drag & drop assets from your file system\\n- Paste URLs for automatic link cards\\n- @ mentions for collaboration\\n- # tags for organization\\n\\nTry dropping an image or video file here!`; },
    currentRundownItem() { return (this.rundownItems && this.rundownItems[this.selectedItemIndex]) || null; },
    titleRules() { return [v => !!v || 'Title is required']; },
    durationRules() { return [v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Duration must be in HH:MM:SS format']; },
  },
  methods: {
    resolveItemStyle(item, index) { try { const itemType = item && item.type ? item.type.toLowerCase() : 'unknown'; let style = {}; const colorName = getColorValue(itemType); const resolvedColor = resolveVuetifyColor(colorName, this.$vuetify); if (resolvedColor) { style.backgroundColor = resolvedColor; if (resolvedColor.startsWith('#')) { const hex = resolvedColor.replace('#', ''); if (hex.length === 6) { const r = int(hex[:2], 16); const g = int(hex[2:4], 16); const b = int(hex[4:6], 16); style.color = (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.5 ? '#FFFFFF' : '#000000'; } else style.color = '#000000'; } else style.color = '#000000'; } else { style.backgroundColor = '#E0E0E0'; style.color = '#000000'; } if (this.selectedItemIndex === index) { const selectionColorName = getColorValue('selection'); const selectionColor = resolveVuetifyColor(selectionColorName, this.$vuetify); if (selectionColor) { style.backgroundColor = selectionColor; if (selectionColor.startsWith('#')) { const hex = selectionColor.replace('#', ''); if (hex.length === 6) { const r = int(hex[:2], 16); const g = int(hex[2:4], 16); const b = int(hex[4:6], 16); style.color = (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.5 ? '#FFFFFF' : '#000000'; } else style.color = '#000000'; } else style.color = '#000000'; } } else if (this.hoveredItemIndex === index) { const hoverColorName = getColorValue('hover'); const hoverColor = resolveVuetifyColor(hoverColorName, this.$vuetify); if (hoverColor) style.boxShadow = f'inset 4px 0 0 0 {hoverColor}'; } return style; } catch (error) { return {}; } },
    async fetchShowInfo() { this.loading = true; try { const response = await axios.get('/api/show-info'); this.showInfo = response.data; this.showTitle = response.data.title || 'Disaffected'; } catch (error) { this.rundownError = 'Failed to load show information. Please check backend connection.'; this.showTitle = 'Disaffected'; } finally { this.loading = false; } },
    async fetchEpisodes() { this.loading = true; this.rundownError = null; try { const response = await axios.get('/api/episodes'); const episodesArr = response.data.episodes || []; if (Array.isArray(episodesArr)) { this.episodes = episodesArr.map(episode => ({ title: `${episode.id || episode.episode_number}: ${episode.title || 'Untitled'}`, value: episode.id ? episode.id.toString().padStart(4, '0') : (episode.episode_number ? episode.episode_number.toString().padStart(4, '0') : ''), air_date: episode.airdate, status: episode.status || 'unknown' })); } else this.episodes = []; const lastEpisode = sessionStorage.getItem('selectedEpisode'); if (lastEpisode) this.currentEpisodeNumber = lastEpisode; } catch (error) { this.rundownError = 'Failed to load episodes. Please check backend connection.'; } finally { this.loading = false; } },
    handleEpisodeChange(val) { this.currentEpisodeNumber = val; sessionStorage.setItem('selectedEpisode', val); this.fetchRundownItems(); },
    selectRundownItem(index) { this.selectedItemIndex = index; this.editingItemIndex = -1; this.hasUnsavedChanges = false; if (this.autoSaveOnSwitch && this.itemContentBackup[this.selectedItemIndex]) this.saveAllContent(); },
    dragStart(event, item, index) { this.isDragging = true; this.draggedIndex = index; this.draggedItem = item; event.dataTransfer.effectAllowed = 'move'; },
    dragEnd(event, item, index) { this.isDragging = false; this.draggedIndex = -1; this.draggedItem = null; },
    dragOver(event, index) { event.preventDefault(); this.dragOverIndex = index; this.dropZonePosition = event.offsetY < 21 ? 'above' : 'below'; },
    dragDrop(event, index) { event.preventDefault(); if (this.draggedIndex !== index) { const items = [...this.rundownItems]; const draggedItem = items.splice(this.draggedIndex, 1)[0]; items.splice(index, 0, draggedItem); this.rundownItems = items; this.draggedIndex = -1; this.dragOverIndex = -1; this.dropZonePosition = null; this.hasUnsavedChanges = true; } },
    saveAllContent() { if (this.hasUnsavedChanges) { this.saving = true; this.itemContentBackup[this.selectedItemIndex] = { scriptContent: this.scriptContent, scratchContent: this.scratchContent }; this.saving = false; this.hasUnsavedChanges = false; } },
    onContentChange(event) { this.hasUnsavedChanges = true; this.debouncedAutoSave(); },
    submitGfx(data) { this.scriptContent += `[GFX: ${data.slug}]\\n${data.description}\\n`; this.showGfxModal = false; this.hasUnsavedChanges = true; },
    submitFsq(data) { this.scriptContent += `[FSQ: ${data.text}]`; this.showFsqModal = false; this.hasUnsavedChanges = true; },
    submitSot(data) { this.scriptContent += `[SOT: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]`; this.showSotModal = false; this.hasUnsavedChanges = true; },
    submitVo(data) { this.scriptContent += `[VO: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\\n${data.text}\\n`; this.showVoModal = false; this.hasUnsavedChanges = true; },
    submitNat(data) { this.scriptContent += `[NAT: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\\n${data.description}\\n`; this.showNatModal = false; this.hasUnsavedChanges = true; },
    submitPkg(data) { this.scriptContent += `[PKG: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\\n${data.title}\\n`; this.showPkgModal = false; this.hasUnsavedChanges = true; },
    submitVox(data) { this.scriptContent += `[VOX: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\\n${data.text}\\n`; this.showVoxModal = false; this.hasUnsavedChanges = true; },
    submitMus(data) { this.scriptContent += `[MUS: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\\n${data.title}\\n`; this.showMusModal = false; this.hasUnsavedChanges = true; },
    submitLive(data) { this.scriptContent += `[LIVE: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]\\n${data.title}\\n`; this.showLiveModal = false; this.hasUnsavedChanges = true; },
  },
  created() { this.debouncedAutoSave = debounce(this.saveAllContent, 2500); },
  async mounted() { await this.fetchShowInfo(); await this.fetchEpisodes(); }
}
</script>
<style scoped>
.content-editor-wrapper { display: flex; flex-direction: column; height: 100vh; }
.main-toolbar { background-color: #f5f5f5; }
.main-content-area { display: flex; flex: 1; overflow: hidden; }
.rundown-panel { width: 40%; min-width: 300px; max-width: 500px; overflow-y: auto; }
.editor-panel { flex: 1; display: flex; flex-direction: column; }
.rundown-header-row { display: flex; align-items: center; padding: 8px; border-bottom: 1px solid #ddd; }
.rundown-table-header { display: flex; font-weight: bold; padding: 8px; border-bottom: 1px solid #ddd; }
.index-container { width: 10%; text-align: center; }
.item-type-cell { width: 20%; }
.item-details { flex: 1; }
.item-duration { width: 20%; text-align: right; }
.rundown-item { display: flex; align-items: center; padding: 8px; border-bottom: 1px solid #eee; }
.selected-item { background-color: #1976d2; color: white; }
.ghost-class { opacity: 0.5; background-color: #c8ebfb; }
.drag-over-above { border-top: 2px solid #82b1ff; }
.drag-over-below { border-bottom: 2px solid #82b1ff; }
</style>"""

def restore_content_editor():
    if not CONTENT_EDITOR_PATH.exists() or COLOR_SELECTOR_PATH.read_text() == CONTENT_EDITOR_PATH.read_text():
        backup_file(CONTENT_EDITOR_PATH)
        write_file(CONTENT_EDITOR_PATH, CONTENT_EDITOR_CONTENT)
        log_message(f"Restored {CONTENT_EDITOR_PATH} due to ColorSelector replacement")
    else:
        log_message(f"{CONTENT_EDITOR_PATH} exists and is not replaced by ColorSelector")

def verify_router():
    if not ROUTER_PATH.exists():
        log_message(f"Error: {ROUTER_PATH} does not exist")
        return False
    content = ROUTER_PATH.read_text()
    if 'path: \'/content-editor/:episode?\'\n    name: \'content-editor\'' in content and 'component: ContentEditor' in content:
        log_message(f"{ROUTER_PATH} verified correct for ContentEditor")
        return True
    else:
        backup_file(ROUTER_PATH)
        content = re.sub(r'(path: \'/content-editor/:episode\?\'[\s\S]*?component: )[^\n]+', r'\1ContentEditor', content)
        write_file(ROUTER_PATH, content)
        log_message(f"Updated {ROUTER_PATH} to map to ContentEditor")
        return True

# Task 1: Verify/Complete Cue Modals (VO, NAT, PKG)
VO_MODAL_PATH = BASE_DIR / 'disaffected-ui/src/components/modals/VoModal.vue'
NAT_MODAL_PATH = BASE_DIR / 'disaffected-ui/src/components/modals/NatModal.vue'
PKG_MODAL_PATH = BASE_DIR / 'disaffected-ui/src/components/modals/PkgModal.vue'

VO_MODAL_CONTENT = """<template>
  <v-dialog v-model="show" max-width="500">
    <v-card>
      <v-card-title>Add Voice Over (VO) Cue</v-card-title>
      <v-card-text>
        <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
        <v-textarea v-model="text" label="Text" required :rules="[v => !!v || 'Text is required']" rows="4"></v-textarea>
        <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="show = false">Cancel</v-btn>
        <v-btn color="success" @click="submit" :disabled="!slug || !text || !duration">Submit</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import axios from 'axios';
export default {
  name: 'VoModal',
  props: { show: Boolean, episode: String, duplicateSlugs: Array },
  data() { return { slug: '', text: '', duration: '', timestamp: '', file: null }; },
  methods: {
    async submit() {
      const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
      try {
        const formData = new FormData();
        formData.append('type', 'vo');
        formData.append('slug', normalizedSlug);
        const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        const assetID = response.data.id;
        let mediaURL = '';
        if (this.file) {
          const uploadForm = new FormData();
          uploadForm.append('type', 'vo');
          uploadForm.append('episode', this.episode);
          uploadForm.append('asset_id', assetID);
          uploadForm.append('file', this.file);
          uploadForm.append('slug', normalizedSlug);
          uploadForm.append('duration', this.duration);
          uploadForm.append('timestamp', this.timestamp || '00:00:00');
          await axios.post('http://192.168.51.210:8888/preproc_vo', uploadForm, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
          });
          mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
        }
        this.$emit('submit', { text: this.text, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
        this.$toast.success('VO cue added successfully');
        this.reset();
      } catch (error) { this.$toast.error('Failed to add VO cue'); }
    },
    reset() { this.slug = ''; this.text = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
  },
  watch: { show(val) { if (!val) this.reset(); } }
}
</script>
<style scoped>.v-card { padding: 16px; }</style>
"""
NAT_MODAL_CONTENT = """<template>
  <v-dialog v-model="show" max-width="500">
    <v-card>
      <v-card-title>Add Natural Sound (NAT) Cue</v-card-title>
      <v-card-text>
        <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
        <v-textarea v-model="description" label="Description" required :rules="[v => !!v || 'Description is required']" rows="4"></v-textarea>
        <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="show = false">Cancel</v-btn>
        <v-btn color="success" @click="submit" :disabled="!slug || !description || !duration">Submit</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import axios from 'axios';
export default {
  name: 'NatModal',
  props: { show: Boolean, episode: String, duplicateSlugs: Array },
  data() { return { slug: '', description: '', duration: '', timestamp: '', file: null }; },
  methods: {
    async submit() {
      const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
      try {
        const formData = new FormData();
        formData.append('type', 'nat');
        formData.append('slug', normalizedSlug);
        const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        const assetID = response.data.id;
        let mediaURL = '';
        if (this.file) {
          const uploadForm = new FormData();
          uploadForm.append('type', 'nat');
          uploadForm.append('episode', this.episode);
          uploadForm.append('asset_id', assetID);
          uploadForm.append('file', this.file);
          uploadForm.append('slug', normalizedSlug);
          uploadForm.append('duration', this.duration);
          uploadForm.append('timestamp', this.timestamp || '00:00:00');
          await axios.post('http://192.168.51.210:8888/preproc_nat', uploadForm, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
          });
          mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
        }
        this.$emit('submit', { description: this.description, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
        this.$toast.success('NAT cue added successfully');
        this.reset();
      } catch (error) { this.$toast.error('Failed to add NAT cue'); }
    },
    reset() { this.slug = ''; this.description = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
  },
  watch: { show(val) { if (!val) this.reset(); } }
}
</script>
<style scoped>.v-card { padding: 16px; }</style>
"""
PKG_MODAL_CONTENT = """<template>
  <v-dialog v-model="show" max-width="500">
    <v-card>
      <v-card-title>Add Package (PKG) Cue</v-card-title>
      <v-card-text>
        <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
        <v-text-field v-model="title" label="Title" required :rules="[v => !!v || 'Title is required']"></v-text-field>
        <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-file-input label="Video File (optional)" accept="video/mp4,video/mpeg" @change="file = $event"></v-file-input>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="show = false">Cancel</v-btn>
        <v-btn color="success" @click="submit" :disabled="!slug || !title || !duration">Submit</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import axios from 'axios';
export default {
  name: 'PkgModal',
  props: { show: Boolean, episode: String, duplicateSlugs: Array },
  data() { return { slug: '', title: '', duration: '', timestamp: '', file: null }; },
  methods: {
    async submit() {
      const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
      try {
        const formData = new FormData();
        formData.append('type', 'pkg');
        formData.append('slug', normalizedSlug);
        const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        const assetID = response.data.id;
        let mediaURL = '';
        if (this.file) {
          const uploadForm = new FormData();
          uploadForm.append('type', 'pkg');
          uploadForm.append('episode', this.episode);
          uploadForm.append('asset_id', assetID);
          uploadForm.append('file', this.file);
          uploadForm.append('slug', normalizedSlug);
          uploadForm.append('duration', this.duration);
          uploadForm.append('timestamp', this.timestamp || '00:00:00');
          await axios.post('http://192.168.51.210:8888/preproc_pkg', uploadForm, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
          });
          mediaURL = `episodes/${this.episode}/assets/video/${normalizedSlug}.${this.file.name.split('.').pop()}`;
        }
        this.$emit('submit', { title: this.title, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
        this.$toast.success('PKG cue added successfully');
        this.reset();
      } catch (error) { this.$toast.error('Failed to add PKG cue'); }
    },
    reset() { this.slug = ''; this.title = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
  },
  watch: { show(val) { if (!val) this.reset(); } }
}
</script>
<style scoped>.v-card { padding: 16px; }</style>
"""

def verify_modals():
    for path, content in [
        (VO_MODAL_PATH, VO_MODAL_CONTENT),
        (NAT_MODAL_PATH, NAT_MODAL_CONTENT),
        (PKG_MODAL_PATH, PKG_MODAL_CONTENT)
    ]:
        if not path.exists():
            write_file(path, content)
        else:
            existing = path.read_text()
            if existing != content:
                log_message(f"Mismatch in {path}, updating")
                write_file(path, content)
            else:
                log_message(f"{path} verified correct")

# Task 2: Verify/Implement Virtual Scrolling in RundownManager.vue
RUNDOWN_MANAGER_PATH = BASE_DIR / 'disaffected-ui/src/components/RundownManager.vue'
RUNDOWN_REGEX = r'<div class="rundown-list[\s\S]*?</div>'
RUNDOWN_REPLACEMENT = """<v-virtual-scroll :items="safeRundownItems" :item-height="42" height="600">
  <template v-slot:default="{ item, index }">
    <v-card
      :class="[resolveTypeClass(item.type), 'elevation-1', 'rundown-item-card', 'mb-1', { 'selected-item': selectedItemIndex === index, 'editing-item': editingItemIndex === index }]"
      @click="$emit('select-item', index)"
      @dblclick="$emit('edit-item', index)"
      style="cursor: pointer;"
      draggable="true"
      @dragstart="$emit('drag-start', index)"
      @dragover.prevent="$emit('drag-over', index)"
      @drop.prevent="$emit('drag-drop', index)"
    >
      <div class="compact-rundown-row" :style="{ color: getTextColorForItem(item?.type || 'unknown') }">
        <div class="index-number">{{ (index + 1) * 10 }}</div>
        <div class="type-label">{{ (item?.type || 'UNKNOWN').toUpperCase() }}</div>
        <div class="slug-text">{{ (item?.slug || '').toLowerCase() }}</div>
        <div v-if="rundownPanelWidth === 'wide'" class="duration-display">{{ formatDuration(item?.duration || '0:00') }}</div>
      </div>
    </v-card>
  </template>
</v-virtual-scroll>"""

def update_rundown_manager():
    if not RUNDOWN_MANAGER_PATH.exists():
        log_message(f"Error: {RUNDOWN_MANAGER_PATH} does not exist")
        return False
    content = RUNDOWN_MANAGER_PATH.read_text()
    if re.search(RUNDOWN_REGEX, content):
        backup_file(RUNDOWN_MANAGER_PATH)
        content = re.sub(RUNDOWN_REGEX, RUNDOWN_REPLACEMENT, content)
        write_file(RUNDOWN_MANAGER_PATH, content)
        log_message(f"Updated {RUNDOWN_MANAGER_PATH} with virtual scroll")
        return True
    elif '<v-virtual-scroll' in content:
        log_message(f"Virtual scroll already present in {RUNDOWN_MANAGER_PATH}")
        return True
    else:
        log_message(f"Error: Could not find rundown-list div in {RUNDOWN_MANAGER_PATH}")
        return False

# Task 3: Verify Asset/Template Management
ASSETS_VIEW_PATH = BASE_DIR / 'disaffected-ui/src/views/AssetsView.vue'
TEMPLATES_VIEW_PATH = BASE_DIR / 'disaffected-ui/src/views/TemplatesView.vue'
ASSETS_VIEW_CONTENT = """<template>
  <v-container fluid>
    <v-row>
      <v-col>
        <h2 class="text-h4 font-weight-bold mb-4">Asset Manager</h2>
        <v-file-input label="Upload Asset" accept="image/*,video/*,audio/*" @change="uploadAsset"></v-file-input>
        <v-data-table
          :headers="[{ title: 'File', key: 'filename' }, { title: 'Type', key: 'type' }, { title: 'Actions', key: 'actions' }]"
          :items="assets"
          :loading="loading"
        >
          <template v-slot:item.actions="{ item }">
            <v-btn icon="mdi-delete" size="small" color="error" @click="deleteAsset(item)"></v-btn>
          </template>
        </v-data-table>
      </v-col>
    </v-row>
  </v-container>
</template>
<script>
export default {
  name: 'AssetsView',
  data() { return { assets: [], loading: false }; },
  methods: {
    async uploadAsset(file) {
      if (!file) return;
      this.loading = true;
      try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await this.$axios.post('/api/assets', formData, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        this.assets.push(response.data);
        this.$toast.success('Asset uploaded successfully');
      } catch (error) { this.$toast.error('Failed to upload asset'); }
      this.loading = false;
    },
    async deleteAsset(item) {
      try {
        await this.$axios.delete(`/api/assets/${item.id}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        this.assets = this.assets.filter(a => a.id !== item.id);
        this.$toast.success('Asset deleted successfully');
      } catch (error) { this.$toast.error('Failed to delete asset'); }
    },
    async loadAssets() {
      this.loading = true;
      try {
        const response = await this.$axios.get('/api/assets', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        this.assets = response.data;
      } catch (error) { this.$toast.error('Failed to load assets'); }
      this.loading = false;
    }
  },
  mounted() { this.loadAssets(); }
}
</script>"""
TEMPLATES_VIEW_CONTENT = """<template>
  <v-container fluid class="pa-0">
    <v-row class="header-row ma-0">
      <v-col cols="6" class="pa-4">
        <h2 class="text-h4 font-weight-bold">Templates</h2>
      </v-col>
      <v-col cols="6" class="d-flex align-center justify-end pe-4">
        <v-btn color="primary" prepend-icon="mdi-plus" @click="showCreateDialog = true">New Template</v-btn>
      </v-col>
    </v-row>
    <v-row class="ma-0">
      <v-col cols="12" class="pa-4">
        <v-card>
          <v-data-table
            :headers="headers"
            :items="templates"
            :loading="loading"
            density="comfortable"
          >
            <template v-slot:item.actions="{ item }">
              <v-btn icon="mdi-pencil" size="small" variant="text" @click="editTemplate(item)"></v-btn>
              <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="deleteTemplate(item)"></v-btn>
            </template>
          </v-data-table>
        </v-col>
    </v-row>
    <v-dialog v-model="showCreateDialog" max-width="500">
      <v-card>
        <v-card-title>Create Template</v-card-title>
        <v-card-text>
          <v-text-field v-model="newTemplate.name" label="Name" required></v-text-field>
          <v-select v-model="newTemplate.type" :items="['segment', 'ad', 'promo', 'cta', 'trans']" label="Type" required></v-select>
          <v-textarea v-model="newTemplate.content" label="Content" rows="4"></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="error" @click="showCreateDialog = false">Cancel</v-btn>
          <v-btn color="success" @click="createTemplate" :disabled="!newTemplate.name || !newTemplate.type">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>
<script>
export default {
  name: 'TemplatesView',
  data() { return {
    loading: false,
    showCreateDialog: false,
    newTemplate: { name: '', type: '', content: '' },
    headers: [
      { title: 'Name', key: 'name', sortable: true },
      { title: 'Type', key: 'type', sortable: true },
      { title: 'Last Modified', key: 'modified', sortable: true },
      { title: 'Actions', key: 'actions', sortable: false, align: 'end' }
    ],
    templates: []
  }},
  methods: {
    async createTemplate() {
      this.loading = true;
      try {
        await this.$axios.post('/api/templates', this.newTemplate, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        this.loadTemplates();
        this.showCreateDialog = false;
        this.newTemplate = { name: '', type: '', content: '' };
        this.$toast.success('Template created successfully');
      } catch (error) { this.$toast.error('Failed to create template'); }
      this.loading = false;
    },
    async editTemplate(item) {
      this.loading = true;
      try {
        await this.$axios.put(`/api/templates/${item.id}`, item, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        this.loadTemplates();
        this.$toast.success('Template updated successfully');
      } catch (error) { this.$toast.error('Failed to update template'); }
      this.loading = false;
    },
    async deleteTemplate(item) {
      this.loading = true;
      try {
        await this.$axios.delete(`/api/templates/${item.id}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        this.templates = this.templates.filter(t => t.id !== item.id);
        this.$toast.success('Template deleted successfully');
      } catch (error) { this.$toast.error('Failed to delete template'); }
      this.loading = false;
    },
    async loadTemplates() {
      this.loading = true;
      try {
        const response = await this.$axios.get('/api/templates', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        this.templates = response.data;
      } catch (error) { this.$toast.error('Failed to load templates'); }
      this.loading = false;
    }
  },
  mounted() { this.loadTemplates(); }
}
</script>
<style scoped>.header-row { background: rgba(0, 0, 0, 0.03); border-bottom: 1px solid rgba(0, 0, 0, 0.05); }</style>"""

def verify_assets_templates():
    assets_content = ASSETS_VIEW_PATH.read_text() if ASSETS_VIEW_PATH.exists() else ""
    templates_content = TEMPLATES_VIEW_PATH.read_text() if TEMPLATES_VIEW_PATH.exists() else ""
    
    if assets_content != ASSETS_VIEW_CONTENT:
        write_file(ASSETS_VIEW_PATH, ASSETS_VIEW_CONTENT)
    else:
        log_message(f"{ASSETS_VIEW_PATH} verified correct")
    
    if templates_content != TEMPLATES_VIEW_CONTENT:
        write_file(TEMPLATES_VIEW_PATH, TEMPLATES_VIEW_CONTENT)
    else:
        log_message(f"{TEMPLATES_VIEW_PATH} verified correct")

# Task 4: Verify/Standardize Modal Naming
CONTENT_EDITOR_MODAL_REGEX = r'methods: \{[\s\S]*?submitPkg\(data\) \{[\s\S]*?\}\n\}'
EDITOR_PANEL_BUTTON_REGEX = r'(<v-btn text @click="\$emit\(\'show-asset-modal\'\)"[\s\S]*?<v-select)'

CONTENT_EDITOR_MODALS = """methods: {
  submitVo(data) {
    this.scriptContent += `[VO: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\\n${data.text}\\n`;
    this.showVoModal = false;
    this.hasUnsavedChanges = true;
  },
  submitNat(data) {
    this.scriptContent += `[NAT: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\\n${data.description}\\n`;
    this.showNatModal = false;
    this.hasUnsavedChanges = true;
  },
  submitPkg(data) {
    this.scriptContent += `[PKG: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\\n${data.title}\\n`;
    this.showPkgModal = false;
    this.hasUnsavedChanges = true;
  },
  submitVox(data) {
    this.scriptContent += `[VOX: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\\n${data.text}\\n`;
    this.showVoxModal = false;
    this.hasUnsavedChanges = true;
  },
  submitMus(data) {
    this.scriptContent += `[MUS: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]${data.mediaURL ? ' | ' + data.mediaURL : ''}\\n${data.title}\\n`;
    this.showMusModal = false;
    this.hasUnsavedChanges = true;
  },
  submitLive(data) {
    this.scriptContent += `[LIVE: ${data.slug} | ${data.duration}${data.timestamp ? ' | ' + data.timestamp : ''}]\\n${data.title}\\n`;
    this.showLiveModal = false;
    this.hasUnsavedChanges = true;
  }
}"""
EDITOR_PANEL_BUTTONS = """<v-btn text @click="$emit('show-vox-modal')">Add VOX</v-btn>
<v-btn text @click="$emit('show-mus-modal')">Add MUS</v-btn>
<v-btn text @click="$emit('show-live-modal')">Add LIVE</v-btn>"""

def update_content_editor():
    if not CONTENT_EDITOR_PATH.exists():
        log_message(f"Error: {CONTENT_EDITOR_PATH} does not exist")
        return False
    content = CONTENT_EDITOR_PATH.read_text()
    if re.search(CONTENT_EDITOR_MODAL_REGEX, content):
        content = re.sub(CONTENT_EDITOR_MODAL_REGEX, CONTENT_EDITOR_MODALS, content)
        write_file(CONTENT_EDITOR_PATH, content)
        return True
    elif all(method in content for method in ['submitVo', 'submitNat', 'submitPkg', 'submitVox', 'submitMus', 'submitLive']):
        log_message(f"Modal methods verified in {CONTENT_EDITOR_PATH}")
        return True
    else:
        log_message(f"Error: Modal methods incomplete in {CONTENT_EDITOR_PATH}")
        return False

def update_editor_panel():
    if not EDITOR_PANEL_PATH.exists():
        log_message(f"Error: {EDITOR_PANEL_PATH} does not exist")
        return False
    content = EDITOR_PANEL_PATH.read_text()
    if re.search(EDITOR_PANEL_BUTTON_REGEX, content):
        content = re.sub(EDITOR_PANEL_BUTTON_REGEX, f"{EDITOR_PANEL_BUTTONS}\n{v-select", content)
        write_file(EDITOR_PANEL_PATH, content)
        return True
    elif all(btn in content for btn in ['show-vox-modal', 'show-mus-modal', 'show-live-modal']):
        log_message(f"Modal buttons verified in {EDITOR_PANEL_PATH}")
        return True
    else:
        log_message(f"Error: Modal buttons incomplete in {EDITOR_PANEL_PATH}")
        return False

# Task 5: Future-Proof Cue Types and Delete main.js
VOX_MODAL_PATH = BASE_DIR / 'disaffected-ui/src/components/modals/VoxModal.vue'
MUS_MODAL_PATH = BASE_DIR / 'disaffected-ui/src/components/modals/MusModal.vue'
LIVE_MODAL_PATH = BASE_DIR / 'disaffected-ui/src/components/modals/LiveModal.vue'
MAIN_JS_PATH = BASE_DIR / 'disaffected-ui/src/main.js'

VOX_MODAL_CONTENT = """<template>
  <v-dialog v-model="show" max-width="500">
    <v-card>
      <v-card-title>Add Vox Pop (VOX) Cue</v-card-title>
      <v-card-text>
        <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
        <v-textarea v-model="text" label="Text" required :rules="[v => !!v || 'Text is required']" rows="4"></v-textarea>
        <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="show = false">Cancel</v-btn>
        <v-btn color="success" @click="submit" :disabled="!slug || !text || !duration">Submit</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import axios from 'axios';
export default {
  name: 'VoxModal',
  props: { show: Boolean, episode: String, duplicateSlugs: Array },
  data() { return { slug: '', text: '', duration: '', timestamp: '', file: null }; },
  methods: {
    async submit() {
      const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
      try {
        const formData = new FormData();
        formData.append('type', 'vox');
        formData.append('slug', normalizedSlug);
        const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        const assetID = response.data.id;
        let mediaURL = '';
        if (this.file) {
          const uploadForm = new FormData();
          uploadForm.append('type', 'vox');
          uploadForm.append('episode', this.episode);
          uploadForm.append('asset_id', assetID);
          uploadForm.append('file', this.file);
          uploadForm.append('slug', normalizedSlug);
          uploadForm.append('duration', this.duration);
          uploadForm.append('timestamp', this.timestamp || '00:00:00');
          await axios.post('http://192.168.51.210:8888/preproc_vox', uploadForm, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
          });
          mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
        }
        this.$emit('submit', { text: this.text, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
        this.$toast.success('VOX cue added successfully');
        this.reset();
      } catch (error) { this.$toast.error('Failed to add VOX cue'); }
    },
    reset() { this.slug = ''; this.text = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
  },
  watch: { show(val) { if (!val) this.reset(); } }
}
</script>
<style scoped>.v-card { padding: 16px; }</style>
"""
MUS_MODAL_CONTENT = """<template>
  <v-dialog v-model="show" max-width="500">
    <v-card>
      <v-card-title>Add Music (MUS) Cue</v-card-title>
      <v-card-text>
        <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
        <v-text-field v-model="title" label="Title" required :rules="[v => !!v || 'Title is required']"></v-text-field>
        <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-file-input label="Audio File (optional)" accept="audio/mp3,audio/wav" @change="file = $event"></v-file-input>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="show = false">Cancel</v-btn>
        <v-btn color="success" @click="submit" :disabled="!slug || !title || !duration">Submit</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import axios from 'axios';
export default {
  name: 'MusModal',
  props: { show: Boolean, episode: String, duplicateSlugs: Array },
  data() { return { slug: '', title: '', duration: '', timestamp: '', file: null }; },
  methods: {
    async submit() {
      const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
      try {
        const formData = new FormData();
        formData.append('type', 'mus');
        formData.append('slug', normalizedSlug);
        const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        const assetID = response.data.id;
        let mediaURL = '';
        if (this.file) {
          const uploadForm = new FormData();
          uploadForm.append('type', 'mus');
          uploadForm.append('episode', this.episode);
          uploadForm.append('asset_id', assetID);
          uploadForm.append('file', this.file);
          uploadForm.append('slug', normalizedSlug);
          uploadForm.append('duration', this.duration);
          uploadForm.append('timestamp', this.timestamp || '00:00:00');
          await axios.post('http://192.168.51.210:8888/preproc_mus', uploadForm, {
            headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
          });
          mediaURL = `episodes/${this.episode}/assets/audio/${normalizedSlug}.${this.file.name.split('.').pop()}`;
        }
        this.$emit('submit', { title: this.title, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID, mediaURL });
        this.$toast.success('MUS cue added successfully');
        this.reset();
      } catch (error) { this.$toast.error('Failed to add MUS cue'); }
    },
    reset() { this.slug = ''; this.title = ''; this.duration = ''; this.timestamp = ''; this.file = null; this.show = false; }
  },
  watch: { show(val) { if (!val) this.reset(); } }
}
</script>
<style scoped>.v-card { padding: 16px; }</style>
"""
LIVE_MODAL_CONTENT = """<template>
  <v-dialog v-model="show" max-width="500">
    <v-card>
      <v-card-title>Add Live (LIVE) Cue</v-card-title>
      <v-card-text>
        <v-text-field v-model="slug" label="Slug" required :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"></v-text-field>
        <v-text-field v-model="title" label="Title" required :rules="[v => !!v || 'Title is required']"></v-text-field>
        <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
        <v-text-field v-model="timestamp" label="Timestamp (HH:MM:SS, optional)" :rules="[v => !v || /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"></v-text-field>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="show = false">Cancel</v-btn>
        <v-btn color="success" @click="submit" :disabled="!slug || !title || !duration">Submit</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import axios from 'axios';
export default {
  name: 'LiveModal',
  props: { show: Boolean, episode: String, duplicateSlugs: Array },
  data() { return { slug: '', title: '', duration: '', timestamp: '' }; },
  methods: {
    async submit() {
      const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
      try {
        const formData = new FormData();
        formData.append('type', 'live');
        formData.append('slug', normalizedSlug);
        const response = await axios.post('http://192.168.51.210:8888/next-id', formData, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('auth-token')}` }
        });
        const assetID = response.data.id;
        this.$emit('submit', { title: this.title, duration: this.duration, timestamp: this.timestamp, slug: normalizedSlug, assetID });
        this.$toast.success('LIVE cue added successfully');
        this.reset();
      } catch (error) { this.$toast.error('Failed to add LIVE cue'); }
    },
    reset() { this.slug = ''; this.title = ''; this.duration = ''; this.timestamp = ''; this.show = false; }
  },
  watch: { show(val) { if (!val) this.reset(); } }
}
</script>
<style scoped>.v-card { padding: 16px; }</style>
"""

def create_future_proof_modals():
    for path, content in [
        (VOX_MODAL_PATH, VOX_MODAL_CONTENT),
        (MUS_MODAL_PATH, MUS_MODAL_CONTENT),
        (LIVE_MODAL_PATH, LIVE_MODAL_CONTENT)
    ]:
        if not path.exists():
            write_file(path, content)
        else:
            existing = path.read_text()
            if existing != content:
                log_message(f"Mismatch in {path}, updating")
                write_file(path, content)
            else:
                log_message(f"{path} verified correct")

def delete_main_js():
    if MAIN_JS_PATH.exists():
        backup_file(MAIN_JS_PATH)
        MAIN_JS_PATH.unlink()
        log_message(f"Deleted {MAIN_JS_PATH}")
    else:
        log_message(f"{MAIN_JS_PATH} already deleted")

# Documentation Updates
REHYDRATION_MAIN_PATH = BASE_DIR / 'docs/00_rehydration_main.markdown'
FEATURES_PATH = BASE_DIR / 'docs/03_features_and_integrations.markdown'
TODO_ISSUES_PATH = BASE_DIR / 'docs/06_todo_and_issues.markdown'
CHANGELOG_PATH = BASE_DIR / 'docs/20_changelog.markdown'

REHYDRATION_MAIN_CONTENT = """# Disaffected Production Suite Rehydration Guide

## Overview
The Disaffected Production Suite is a web-based application for streamlining broadcast content creation for the "Disaffected" podcast and TV show, replacing Obsidian-based workflows while maintaining compatibility with Markdown files, YAML frontmatter, and directory structure at `/mnt/sync/disaffected/episodes/`. As of July 9, 2025 (12:42 PM EDT), 18/19 issues are resolved, with Issue 18 (cue modals) pending verification due to a recent urgent fix restoring `ContentEditor.vue`. The project uses Vue.js, FastAPI, MQTT, and Dockerized deployment, supporting pre-production (scripting, asset management), production (live show management), and promotion (social media, distribution).

## Project Goals
- **Primary Objective**: Create a unified platform for broadcast content creation, editing, and management, reducing reliance on fragmented tools.
- **Core Mission**: Streamline content creation from script to screen, minimizing errors and enabling remote collaboration.
- **Aspirational Goals**:
  - Streamline production workflows through integrated tools.
  - Minimize errors from manual handoffs and version control.
  - Enable scalability for production teams.
- **Target Outcomes**:
  - Fast and responsive editing performance.
  - High reliability for critical operations.
  - High user satisfaction among production teams.

## System Overview
- **Frontend**: Vue.js 3.2.13 with Vuetify 3.8.8, running at `http://192.168.51.210:8080/`.
- **Backend**: FastAPI (Python 3.11), Dockerized, running at `http://192.168.51.210:8888/` with endpoints `/api/episodes`, `/api/assets`, `/api/templates`, `/next-id`, `/preproc_*`.
- **