<template>
  <v-dialog
    :model-value="show"
    @update:model-value="$emit('update:show', $event)"
    max-width="1100"
    scrollable
  >
    <v-card>
      <v-card-title class="d-flex align-center pa-3 bg-blue-grey-darken-4">
        <v-icon class="me-2">mdi-compare-horizontal</v-icon>
        Script Compare
        <v-spacer />
        <v-btn icon size="small" variant="text" @click="$emit('update:show', false)">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <!-- Phase 1: File Upload -->
      <v-card-text v-if="phase === 'upload'" class="pa-6">
        <div class="text-center">
          <v-icon size="64" color="blue-grey" class="mb-4">mdi-file-document-outline</v-icon>
          <div class="text-h6 mb-2">Upload Comparator Script</div>
          <div class="text-body-2 text-grey mb-6">
            Upload a text file exported from Google Docs to compare against the current rundown.
          </div>

          <div
            class="upload-zone pa-8 rounded-lg mb-4"
            :class="{ 'upload-zone-active': isDragging }"
            @dragover.prevent="isDragging = true"
            @dragleave="isDragging = false"
            @drop.prevent="handleFileDrop"
            @click="$refs.fileInput.click()"
          >
            <v-icon size="48" color="blue-grey-lighten-2" class="mb-3">mdi-cloud-upload</v-icon>
            <div class="text-body-1 mb-1">Drop text file here or click to browse</div>
            <div class="text-caption text-grey">.txt files</div>
          </div>
          <input
            ref="fileInput"
            type="file"
            accept=".txt"
            style="display: none"
            @change="handleFileSelect"
          />
        </div>
      </v-card-text>

      <!-- Phase 2: Diff View -->
      <template v-if="phase === 'diff'">
        <v-card-text class="pa-0" style="max-height: 70vh; overflow-y: auto;">
          <!-- Summary bar -->
          <div class="pa-3 bg-grey-lighten-4 d-flex align-center ga-3 border-b">
            <v-chip size="small" color="success" variant="tonal">{{ matchedCount }} matched</v-chip>
            <v-chip size="small" color="warning" variant="tonal">{{ diffCount }} with differences</v-chip>
            <v-chip size="small" color="grey" variant="tonal">{{ unmatchedCount }} unmatched</v-chip>
            <v-spacer />
            <v-btn size="small" variant="text" @click="phase = 'upload'; resetState()">
              <v-icon start size="small">mdi-arrow-left</v-icon>
              Change File
            </v-btn>
          </div>

          <!-- Item navigator -->
          <div class="pa-3 d-flex align-center ga-2 border-b">
            <v-btn
              size="small"
              icon="mdi-chevron-left"
              variant="text"
              :disabled="currentMatchIndex <= 0"
              @click="currentMatchIndex--"
            />
            <v-chip size="small" variant="outlined">
              {{ currentMatchIndex + 1 }} / {{ matchResults.length }}
            </v-chip>
            <v-btn
              size="small"
              icon="mdi-chevron-right"
              variant="text"
              :disabled="currentMatchIndex >= matchResults.length - 1"
              @click="currentMatchIndex++"
            />
            <span class="text-subtitle-2 ms-2">
              {{ currentMatch?.rundownTitle || 'No match' }}
            </span>
            <v-spacer />
            <v-chip
              v-if="currentMatch?.decision"
              size="small"
              :color="currentMatch.decision === 'adopt' ? 'success' : 'grey'"
              variant="tonal"
            >
              {{ currentMatch.decision === 'adopt' ? 'Adopting' : currentMatch.decision === 'keep' ? 'Keeping' : 'Pending' }}
            </v-chip>
          </div>

          <!-- Diff content for current item -->
          <div v-if="currentMatch" class="pa-4">
            <div class="text-overline text-grey mb-2">
              Rundown: {{ currentMatch.rundownTitle }}
              <span v-if="currentMatch.confidence < 1" class="text-caption ms-2 text-warning">
                ({{ Math.round(currentMatch.confidence * 100) }}% match confidence)
              </span>
            </div>

            <!-- No differences -->
            <div v-if="!currentMatch.hasDifferences" class="text-center pa-6">
              <v-icon size="48" color="success" class="mb-2">mdi-check-circle</v-icon>
              <div class="text-body-1">Content is identical</div>
            </div>

            <!-- Diff display -->
            <div v-else class="diff-container pa-4 rounded border">
              <div class="diff-content" v-html="currentMatch.diffHtml"></div>
            </div>

            <!-- Cue block matches -->
            <div v-if="currentMatch.cueMatches && currentMatch.cueMatches.length > 0" class="mt-3">
              <div class="text-overline text-grey mb-1">Cue Block Matches</div>
              <div v-for="(cm, idx) in currentMatch.cueMatches" :key="idx" class="d-flex align-center ga-2 mb-1">
                <v-chip size="x-small" :color="cm.matched ? 'success' : 'warning'" variant="tonal">
                  {{ cm.type }}
                </v-chip>
                <span class="text-caption">
                  Comparator: "{{ cm.comparatorSlug }}"
                  <v-icon size="x-small" class="mx-1">mdi-arrow-right</v-icon>
                  Rundown: "{{ cm.rundownSlug }}"
                </span>
                <v-icon v-if="cm.matched" size="small" color="success">mdi-check</v-icon>
                <v-icon v-else size="small" color="warning">mdi-alert</v-icon>
              </div>
            </div>
          </div>

          <div v-else class="pa-6 text-center text-grey">
            No match data available
          </div>
        </v-card-text>

        <!-- Actions for current item -->
        <v-card-actions class="pa-3 border-t">
          <v-btn
            variant="outlined"
            size="small"
            color="grey"
            @click="setDecision('keep')"
            :disabled="!currentMatch?.hasDifferences"
          >
            <v-icon start size="small">mdi-shield-check</v-icon>
            Keep Rundown
          </v-btn>
          <v-btn
            variant="outlined"
            size="small"
            color="success"
            @click="setDecision('adopt')"
            :disabled="!currentMatch?.hasDifferences"
          >
            <v-icon start size="small">mdi-swap-horizontal</v-icon>
            Adopt Comparator
          </v-btn>
          <v-spacer />
          <v-btn
            variant="tonal"
            size="small"
            color="primary"
            :disabled="!hasDecisions"
            @click="applyChanges"
          >
            <v-icon start size="small">mdi-check-all</v-icon>
            Apply {{ adoptCount }} Change{{ adoptCount !== 1 ? 's' : '' }}
          </v-btn>
        </v-card-actions>
      </template>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { registerModalEsc } from '@/composables/useModalStack';
import {
  extractPlainText,
  parseComparatorFile,
  normalizeComparatorBody,
  matchSections,
  computeDiff,
  cuePatternMatch
} from '@/utils/scriptCompare';

const props = defineProps({
  show: Boolean,
  rundownItems: { type: Array, default: () => [] }
});

const emit = defineEmits(['update:show', 'apply-changes']);

// Template refs
const fileInput = ref(null);

// Data
const phase = ref('upload');
const isDragging = ref(false);
const fileContent = ref('');
const fileName = ref('');
const comparatorSections = ref([]);
const matchResults = ref([]);
const currentMatchIndex = ref(0);

// Computed
const currentMatch = computed(() => {
  return matchResults.value[currentMatchIndex.value] || null;
});

const matchedCount = computed(() => {
  return matchResults.value.length;
});

const diffCount = computed(() => {
  return matchResults.value.filter(m => m.hasDifferences).length;
});

const unmatchedCount = computed(() => {
  return props.rundownItems.filter(
    (_, i) => !matchResults.value.some(m => m.rundownIndex === i)
  ).length;
});

const adoptCount = computed(() => {
  return matchResults.value.filter(m => m.decision === 'adopt').length;
});

const hasDecisions = computed(() => {
  return matchResults.value.some(m => m.decision === 'adopt');
});

// Methods — ESC handled by registerModalEsc via global modal stack
registerModalEsc(() => props.show, () => emit('update:show', false), 'ScriptCompareModal');

function resetState() {
  fileContent.value = '';
  fileName.value = '';
  comparatorSections.value = [];
  matchResults.value = [];
  currentMatchIndex.value = 0;
}

function handleFileSelect(event) {
  const file = event.target.files?.[0];
  if (file) loadFile(file);
}

function handleFileDrop(event) {
  isDragging.value = false;
  const file = event.dataTransfer?.files?.[0];
  if (file) loadFile(file);
}

function loadFile(file) {
  fileName.value = file.name;
  const reader = new FileReader();
  reader.onload = (e) => {
    fileContent.value = e.target.result;
    processFile();
  };
  reader.readAsText(file);
}

function processFile() {
  comparatorSections.value = parseComparatorFile(fileContent.value, props.rundownItems);

  if (comparatorSections.value.length === 0) {
    return;
  }

  const matches = matchSections(comparatorSections.value, props.rundownItems);

  matchResults.value = matches.map(match => {
    const rundownItem = props.rundownItems[match.rundownIndex];
    const comparatorSection = comparatorSections.value[match.comparatorIndex];

    const rundownText = extractPlainText(rundownItem.script || '');
    const comparatorText = normalizeComparatorBody(comparatorSection.body);

    const diffChunks = computeDiff(rundownText, comparatorText);
    const hasDifferences = diffChunks.some(c => c.added || c.removed);

    const diffHtml = buildDiffHtml(diffChunks);
    const cueMatches = findCueMatches(rundownText, comparatorText);

    return {
      rundownIndex: match.rundownIndex,
      comparatorIndex: match.comparatorIndex,
      rundownTitle: rundownItem.title || rundownItem.slug || `Item ${match.rundownIndex}`,
      confidence: match.confidence,
      rundownText,
      comparatorText,
      diffChunks,
      hasDifferences,
      diffHtml,
      cueMatches,
      decision: hasDifferences ? null : 'keep'
    };
  });

  currentMatchIndex.value = 0;
  phase.value = 'diff';
}

function buildDiffHtml(chunks) {
  return chunks.map(chunk => {
    const escaped = escapeHtml(chunk.value);
    const formatted = escaped.replace(/\n/g, '<br>');

    if (chunk.removed) {
      return `<span class="diff-removed">${formatted}</span>`;
    }
    if (chunk.added) {
      return `<span class="diff-added">${formatted}</span>`;
    }
    return `<span class="diff-unchanged">${formatted}</span>`;
  }).join('');
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function findCueMatches(rundownText, comparatorText) {
  const rdCues = [...rundownText.matchAll(/\{([^/}]+)\/([^}]+)\}/g)];
  const compCues = [...comparatorText.matchAll(/\{([^/}]+)\/([^}]+)\}/g)];
  const matches = [];

  for (const compCue of compCues) {
    const compToken = compCue[0];
    const compType = compCue[1].trim().toUpperCase();
    const compSlug = compCue[2].trim();

    let matched = false;
    let rdSlug = '';
    for (const rdCue of rdCues) {
      if (cuePatternMatch(compToken, rdCue[0])) {
        matched = true;
        rdSlug = rdCue[2].trim();
        break;
      }
    }

    matches.push({
      type: compType,
      comparatorSlug: compSlug,
      rundownSlug: rdSlug || '(not found)',
      matched
    });
  }

  return matches;
}

function setDecision(decision) {
  if (currentMatch.value) {
    currentMatch.value.decision = decision;
  }
}

function applyChanges() {
  const changes = matchResults.value
    .filter(m => m.decision === 'adopt')
    .map(m => ({
      rundownIndex: m.rundownIndex,
      comparatorText: m.comparatorText
    }));

  emit('apply-changes', changes);
  emit('update:show', false);
}

// Watchers
watch(() => props.show, (val) => {
  if (val) {
    phase.value = 'upload';
    resetState();
  }
});

// Lifecycle (ESC handler is auto-registered above)
</script>

<style scoped>
.upload-zone {
  border: 2px dashed #bdbdbd;
  cursor: pointer;
  transition: all 0.2s;
}
.upload-zone:hover,
.upload-zone-active {
  border-color: #1976d2;
  background: rgba(25, 118, 210, 0.04);
}

.diff-container {
  background: #fafafa;
  font-family: 'Georgia', serif;
  font-size: 0.95rem;
  line-height: 1.7;
  max-height: 400px;
  overflow-y: auto;
}

.diff-content :deep(.diff-removed) {
  background: #ffcdd2;
  text-decoration: line-through;
  color: #b71c1c;
  padding: 1px 2px;
  border-radius: 2px;
}

.diff-content :deep(.diff-added) {
  background: #c8e6c9;
  color: #1b5e20;
  padding: 1px 2px;
  border-radius: 2px;
}

.diff-content :deep(.diff-unchanged) {
  color: #424242;
}
</style>
