<template>
  <div class="script-editor">
    <!-- Editor Toolbar -->
    <v-toolbar density="compact" flat class="editor-toolbar">
      <!-- Text Formatting -->
      <v-btn-toggle v-model="formatting" multiple density="compact">
        <v-btn icon="mdi-format-bold" @click="toggleBold" size="small" />
        <v-btn icon="mdi-format-italic" @click="toggleItalic" size="small" />
        <v-btn icon="mdi-format-underline" @click="toggleUnderline" size="small" />
      </v-btn-toggle>

      <v-divider vertical class="mx-2" />

      <!-- Cue Insertion Buttons -->
      <v-btn
        v-for="cue in cueTypes"
        :key="cue.type"
        :color="cue.color"
        variant="tonal"
        size="small"
        class="mx-1"
        @click="insertCue(cue.type)"
      >
        {{ cue.type }}
      </v-btn>

      <v-spacer />

      <!-- View Options -->
      <v-btn-toggle v-model="viewMode" mandatory density="compact">
        <v-btn value="edit" icon="mdi-pencil" size="small" />
        <v-btn value="preview" icon="mdi-eye" size="small" />
        <v-btn value="teleprompter" icon="mdi-script-text" size="small" />
      </v-btn-toggle>
    </v-toolbar>

    <!-- Main Editor Area -->
    <div class="editor-container" :class="`view-${viewMode}`">
      <!-- Edit Mode -->
      <div v-if="viewMode === 'edit'" class="editor-wrapper">
        <div 
          ref="editor"
          class="script-content"
          contenteditable="true"
          @input="handleInput"
          @keydown="handleKeydown"
          @paste="handlePaste"
          v-html="formattedContent"
        />
        
        <!-- Character/Word Count -->
        <div class="editor-status">
          <span>Words: {{ wordCount }}</span>
          <span class="mx-3">|</span>
          <span>Duration: ~{{ estimatedDuration }}</span>
          <span class="mx-3">|</span>
          <span>Cues: {{ cueCount }}</span>
        </div>
      </div>

      <!-- Preview Mode -->
      <div v-else-if="viewMode === 'preview'" class="preview-wrapper">
        <div class="preview-content" v-html="previewContent" />
      </div>

      <!-- Teleprompter Mode -->
      <div v-else-if="viewMode === 'teleprompter'" class="teleprompter-wrapper">
        <div class="teleprompter-controls">
          <v-btn icon="mdi-play" @click="startTeleprompter" :disabled="isScrolling" />
          <v-btn icon="mdi-pause" @click="pauseTeleprompter" :disabled="!isScrolling" />
          <v-btn icon="mdi-stop" @click="stopTeleprompter" />
          <v-slider
            v-model="scrollSpeed"
            min="1"
            max="10"
            step="1"
            label="Speed"
            class="mx-4"
            style="max-width: 200px"
          />
        </div>
        <div 
          ref="teleprompter"
          class="teleprompter-content"
          :style="{ fontSize: `${teleprompterFontSize}px` }"
          v-html="teleprompterContent"
        />
      </div>
    </div>

    <!-- Cue Insertion Dialog -->
    <v-dialog v-model="cueDialog" max-width="600">
      <v-card>
        <v-card-title>
          Insert {{ currentCueType }} Cue
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="cueData.assetId"
            label="Asset ID"
            hint="Enter the asset identifier or select from library"
            variant="outlined"
            density="comfortable"
          />
          <v-text-field
            v-model="cueData.duration"
            label="Duration"
            hint="Format: MM:SS or :SS"
            placeholder="1:30"
            variant="outlined"
            density="comfortable"
          />
          <v-text-field
            v-if="currentCueType === 'GFX'"
            v-model="cueData.text"
            label="Display Text"
            hint="Text to show (e.g., lower third text)"
            variant="outlined"
            density="comfortable"
          />
          <v-textarea
            v-model="cueData.notes"
            label="Production Notes"
            rows="2"
            variant="outlined"
            density="comfortable"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="cueDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="confirmCueInsert">Insert</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue';

export default {
  name: 'ScriptEditor',
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    segmentId: {
      type: String,
      required: true
    }
  },
  emits: ['update:modelValue', 'save', 'cue-inserted'],
  setup(props, { emit }) {
    // Editor state
    const editor = ref(null);
    const content = ref(props.modelValue);
    const viewMode = ref('edit');
    const formatting = ref([]);
    
    // Cue management
    const cueDialog = ref(false);
    const currentCueType = ref('');
    const cueData = ref({
      assetId: '',
      duration: '',
      text: '',
      notes: ''
    });
    
    const cueTypes = [
      { type: 'VO', color: 'blue', name: 'Voice Over' },
      { type: 'NAT', color: 'green', name: 'Natural Sound' },
      { type: 'SOT', color: 'orange', name: 'Sound on Tape' },
      { type: 'PKG', color: 'purple', name: 'Package' },
      { type: 'GFX', color: 'pink', name: 'Graphics' },
      { type: 'FSQ', color: 'red', name: 'Full Screen' }
    ];
    
    // Teleprompter state
    const teleprompter = ref(null);
    const isScrolling = ref(false);
    const scrollSpeed = ref(5);
    const teleprompterFontSize = ref(32);
    let scrollInterval = null;
    
    // Computed properties
    const wordCount = computed(() => {
      const text = content.value.replace(/<[^>]*>/g, '').replace(/\[.*?\]/g, '');
      return text.split(/\s+/).filter(word => word.length > 0).length;
    });
    
    const estimatedDuration = computed(() => {
      // Average reading speed: 150 words per minute
      const minutes = Math.ceil(wordCount.value / 150);
      return `${minutes} min`;
    });
    
    const cueCount = computed(() => {
      const matches = content.value.match(/\[[A-Z]+:.*?\]/g);
      return matches ? matches.length : 0;
    });
    
    const formattedContent = computed(() => {
      let formatted = content.value;
      
      // Format cues as styled spans
      formatted = formatted.replace(
        /\[([A-Z]+):([^\]]+)\]/g,
        '<span class="cue-marker cue-$1" contenteditable="false">[$1: $2]</span>'
      );
      
      return formatted;
    });
    
    const previewContent = computed(() => {
      let preview = content.value;
      
      // Convert cues to preview boxes
      preview = preview.replace(
        /\[([A-Z]+):([^\]]+)\]/g,
        `<div class="cue-box cue-$1">
          <span class="cue-type">$1</span>
          <span class="cue-details">$2</span>
        </div>`
      );
      
      // Convert line breaks
      preview = preview.replace(/\n/g, '<br>');
      
      return preview;
    });
    
    const teleprompterContent = computed(() => {
      let prompter = content.value;
      
      // Convert cues to teleprompter format
      prompter = prompter.replace(
        /\[([A-Z]+):([^\]]+)\]/g,
        '<div class="teleprompter-cue">[[ $1 - $2 ]]</div>'
      );
      
      // Add line breaks and styling
      prompter = prompter.replace(/\n/g, '<br>');
      
      return `<div class="teleprompter-text">${prompter}</div>`;
    });
    
    // Methods
    const handleInput = (event) => {
      content.value = event.target.innerHTML
        .replace(/<div>/g, '\n')
        .replace(/<\/div>/g, '')
        .replace(/<br>/g, '\n')
        .replace(/&nbsp;/g, ' ')
        .replace(/<span[^>]*class="cue-marker[^>]*>(\[[^\]]+\])<\/span>/g, '$1');
      
      emit('update:modelValue', content.value);
    };
    
    const handleKeydown = (event) => {
      // Auto-save on Ctrl+S
      if (event.ctrlKey && event.key === 's') {
        event.preventDefault();
        emit('save');
      }
    };
    
    const handlePaste = (event) => {
      event.preventDefault();
      const text = event.clipboardData.getData('text/plain');
      document.execCommand('insertText', false, text);
    };
    
    const toggleBold = () => {
      document.execCommand('bold');
    };
    
    const toggleItalic = () => {
      document.execCommand('italic');
    };
    
    const toggleUnderline = () => {
      document.execCommand('underline');
    };
    
    const insertCue = (type) => {
      currentCueType.value = type;
      cueData.value = {
        assetId: '',
        duration: '',
        text: '',
        notes: ''
      };
      cueDialog.value = true;
    };
    
    const confirmCueInsert = () => {
      let cueString = `[${currentCueType.value}: ${cueData.value.assetId}`;
      
      if (cueData.value.duration) {
        cueString += ` ${cueData.value.duration}`;
      }
      
      if (cueData.value.text && currentCueType.value === 'GFX') {
        cueString += ` "${cueData.value.text}"`;
      }
      
      cueString += ']';
      
      // Insert at cursor position
      const selection = window.getSelection();
      const range = selection.getRangeAt(0);
      const cueNode = document.createTextNode(cueString);
      range.insertNode(cueNode);
      range.collapse(false);
      
      // Update content
      content.value = editor.value.innerText;
      emit('update:modelValue', content.value);
      emit('cue-inserted', {
        type: currentCueType.value,
        data: cueData.value
      });
      
      cueDialog.value = false;
    };
    
    const startTeleprompter = () => {
      isScrolling.value = true;
      scrollInterval = setInterval(() => {
        if (teleprompter.value) {
          teleprompter.value.scrollTop += scrollSpeed.value;
        }
      }, 50);
    };
    
    const pauseTeleprompter = () => {
      isScrolling.value = false;
      if (scrollInterval) {
        clearInterval(scrollInterval);
        scrollInterval = null;
      }
    };
    
    const stopTeleprompter = () => {
      pauseTeleprompter();
      if (teleprompter.value) {
        teleprompter.value.scrollTop = 0;
      }
    };
    
    // Lifecycle
    onMounted(() => {
      if (editor.value) {
        editor.value.innerHTML = formattedContent.value;
      }
    });
    
    watch(() => props.modelValue, (newValue) => {
      if (newValue !== content.value) {
        content.value = newValue;
        if (editor.value) {
          editor.value.innerHTML = formattedContent.value;
        }
      }
    });
    
    return {
      editor,
      content,
      viewMode,
      formatting,
      cueDialog,
      currentCueType,
      cueData,
      cueTypes,
      teleprompter,
      isScrolling,
      scrollSpeed,
      teleprompterFontSize,
      wordCount,
      estimatedDuration,
      cueCount,
      formattedContent,
      previewContent,
      teleprompterContent,
      handleInput,
      handleKeydown,
      handlePaste,
      toggleBold,
      toggleItalic,
      toggleUnderline,
      insertCue,
      confirmCueInsert,
      startTeleprompter,
      pauseTeleprompter,
      stopTeleprompter
    };
  }
};
</script>

<style scoped>
.script-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
}

.editor-toolbar {
  border-bottom: 1px solid #333;
}

.editor-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.editor-wrapper,
.preview-wrapper,
.teleprompter-wrapper {
  flex: 1;
  overflow: auto;
  padding: 20px;
}

.script-content {
  min-height: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  background: #2a2a2a;
  border-radius: 8px;
  font-family: 'Courier New', monospace;
  font-size: 16px;
  line-height: 1.8;
  color: #fff;
  outline: none;
  text-align: left;
  direction: ltr;
  writing-mode: horizontal-tb;
}

.script-content:focus {
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.3);
}

.script-content * {
  text-align: inherit;
  direction: inherit;
}

.script-content p,
.script-content div {
  text-align: left;
  direction: ltr;
}

:deep(.cue-marker) {
  display: inline-block;
  padding: 2px 8px;
  margin: 0 4px;
  border-radius: 4px;
  font-weight: bold;
  font-size: 14px;
  user-select: none;
}

:deep(.cue-VO) { background: #2196F3; color: white; }
:deep(.cue-NAT) { background: #4CAF50; color: white; }
:deep(.cue-SOT) { background: #FF9800; color: white; }
:deep(.cue-PKG) { background: #9C27B0; color: white; }
:deep(.cue-GFX) { background: #E91E63; color: white; }
:deep(.cue-FSQ) { background: #F44336; color: white; }

.editor-status {
  display: flex;
  justify-content: center;
  padding: 10px;
  font-size: 12px;
  color: #888;
  border-top: 1px solid #333;
}

.preview-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  background: white;
  color: black;
  border-radius: 8px;
  font-family: 'Georgia', serif;
  font-size: 18px;
  line-height: 1.8;
}

.cue-box {
  display: inline-block;
  margin: 10px 0;
  padding: 10px;
  border-left: 4px solid;
  background: #f5f5f5;
  width: 100%;
}

.cue-box.cue-VO { border-color: #2196F3; }
.cue-box.cue-NAT { border-color: #4CAF50; }
.cue-box.cue-SOT { border-color: #FF9800; }
.cue-box.cue-PKG { border-color: #9C27B0; }
.cue-box.cue-GFX { border-color: #E91E63; }
.cue-box.cue-FSQ { border-color: #F44336; }

.cue-type {
  font-weight: bold;
  margin-right: 10px;
}

.teleprompter-controls {
  position: sticky;
  top: 0;
  background: #1e1e1e;
  padding: 10px;
  border-bottom: 1px solid #333;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.teleprompter-content {
  max-width: 600px;
  margin: 0 auto;
  padding: 40px 20px 200px;
  font-family: sans-serif;
  line-height: 2;
  color: white;
  text-align: center;
}

.teleprompter-text {
  font-size: inherit;
}

.teleprompter-cue {
  display: block;
  margin: 20px 0;
  padding: 10px;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid #FFD700;
  border-radius: 8px;
  font-weight: bold;
  text-transform: uppercase;
}
</style>