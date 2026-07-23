<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="700">
    <v-card :style="modalStyles">
      <v-card-title :style="headerStyles">Add Stinger from Media Repository</v-card-title>

      <!-- Mode Selection Tabs -->
      <v-tabs v-model="selectedTab" class="mb-3">
        <v-tab value="existing">Select from Repository</v-tab>
        <v-tab value="new">Create New</v-tab>
      </v-tabs>

      <v-card-text>
        <v-window v-model="selectedTab">
          <!-- Select from Library Tab -->
          <v-window-item value="existing">
            <v-text-field
              ref="slugField"
              v-model="slug"
              label="Slug"
              required
              :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
              hint="Unique identifier for this instance"
              persistent-hint
              class="mb-2"
            ></v-text-field>

            <v-select
              v-model="selectedLibraryItem"
              :items="libraryItems"
              item-title="name"
              item-value="id"
              label="Select Stinger from Repository"
              return-object
              @update:model-value="onLibraryItemSelected"
            >
              <template v-slot:item="{ props, item }">
                <v-list-item v-bind="props">
                  <template v-slot:title>
                    <strong>{{ item.raw.name }}</strong>
                  </template>
                  <template v-slot:subtitle>
                    AssetID: {{ item.raw.assetId }} | Duration: {{ item.raw.duration }}
                  </template>
                </v-list-item>
              </template>
            </v-select>

            <!-- Preview of selected library item -->
            <v-card v-if="selectedLibraryItem" variant="outlined" class="mt-3 pa-3">
              <div class="text-subtitle-2 mb-2">Preview</div>
              <div><strong>Name:</strong> {{ selectedLibraryItem.name }}</div>
              <div><strong>AssetID:</strong> {{ selectedLibraryItem.assetId }}</div>
              <div><strong>Duration:</strong> {{ selectedLibraryItem.duration }}</div>
              <div><strong>Media URL:</strong> {{ selectedLibraryItem.mediaUrl || 'N/A' }}</div>
              <div><strong>Alpha:</strong> {{ selectedLibraryItem.alpha ? 'Yes' : 'No' }}</div>
              <div><strong>Audio:</strong> {{ selectedLibraryItem.audio ? 'Yes' : 'No' }}</div>
            </v-card>
          </v-window-item>

          <!-- Create New Tab -->
          <v-window-item value="new">
            <v-text-field
              v-model="slug"
              label="Slug"
              required
              :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
            ></v-text-field>
            <v-text-field
              v-model="assetId"
              label="AssetID"
              required
              :rules="[v => !!v || 'AssetID is required']"
              hint="Associated asset identifier"
              persistent-hint
            ></v-text-field>
            <v-text-field
              v-model="name"
              label="Name"
              required
              :rules="[v => !!v || 'Name is required']"
              hint="Stinger name or description"
              persistent-hint
            ></v-text-field>
            <v-text-field
              v-model="duration"
              label="Duration (HH:MM:SS)"
              required
              :rules="[v => !!v || 'Duration is required', v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
              hint="Duration never changes"
              persistent-hint
            ></v-text-field>
            <v-text-field
              v-model="mediaUrl"
              label="Media URL"
              hint="Link to media file or sequence"
              persistent-hint
            ></v-text-field>
            <v-checkbox
              v-model="alpha"
              label="Alpha Channel"
              hint="Has alpha/transparency"
              persistent-hint
            ></v-checkbox>
            <v-checkbox
              v-model="audio"
              label="Audio"
              hint="Has audio track"
              persistent-hint
            ></v-checkbox>
            <v-checkbox
              v-model="saveToLibrary"
              label="Save to Repository"
              hint="Save this stinger to Media Repository for reuse"
              persistent-hint
            ></v-checkbox>
          </v-window-item>
        </v-window>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="handleAbort">Cancel (ESC)</v-btn>
        <v-btn
          color="success"
          @click="handleSubmit"
          :disabled="!isValid"
        >
          Submit (Shift+Enter)
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { cueModalMixin } from '@/mixins/cueModalMixin';

export default {
  name: 'StingModal',
  mixins: [cueModalMixin],
  props: {
    show: Boolean,
    episode: String,
    duplicateSlugs: {
      type: Array,
      default: () => []
    },
    cueType: {
      type: String,
      default: 'sting'
    }
  },
  data() {
    return {
      selectedTab: 'existing', // Start with library selection
      slug: '',
      assetId: '',
      name: '',
      duration: '',
      mediaUrl: '',
      alpha: false,
      audio: true,
      saveToLibrary: false,
      libraryItems: [],
      selectedLibraryItem: null,
      loadingLibrary: false
    };
  },
  computed: {
    isValid() {
      if (this.selectedTab === 'existing') {
        // For library selection, just need slug and selected item
        return !!this.slug && !!this.selectedLibraryItem;
      } else {
        // For new creation, need all required fields
        return !!this.slug && !!this.assetId && !!this.name && !!this.duration;
      }
    }
  },
  methods: {
    async handleSubmit() {
      if (!this.isValid) {
        return;
      }

      // If using library item, populate fields from selection
      if (this.selectedTab === 'existing' && this.selectedLibraryItem) {
        this.assetId = this.selectedLibraryItem.assetId;
        this.name = this.selectedLibraryItem.name;
        this.duration = this.selectedLibraryItem.duration;
        this.mediaUrl = this.selectedLibraryItem.mediaUrl || '';
        this.alpha = this.selectedLibraryItem.alpha;
        this.audio = this.selectedLibraryItem.audio;
      }

      await this.submit();
    },
    async submit() {
      const cueBlockContent = this.buildCueBlock();

      // If creating new and save to library is checked, save to library
      if (this.selectedTab === 'new' && this.saveToLibrary) {
        await this.saveToLibraryDatabase();
      }

      this.$emit('submit', cueBlockContent);
      this.reset();
    },
    async saveToLibraryDatabase() {
      try {
        const response = await fetch('/api/repo', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            type: 'sting',
            assetId: this.assetId,
            name: this.name,
            duration: this.duration,
            mediaUrl: this.mediaUrl,
            alpha: this.alpha,
            audio: this.audio
          })
        });

        if (response.ok) {
          console.log('✅ Stinger saved to repository');
          // Refresh library items
          await this.fetchLibraryItems();
        }
      } catch (error) {
        console.error('❌ Failed to save to repository:', error);
      }
    },
    async fetchLibraryItems() {
      this.loadingLibrary = true;
      try {
        const response = await fetch('/api/repo?type=sting');
        if (response.ok) {
          const data = await response.json();
          this.libraryItems = data.items || [];
        }
      } catch (error) {
        console.error('❌ Failed to fetch repository items:', error);
        this.libraryItems = [];
      } finally {
        this.loadingLibrary = false;
      }
    },
    onLibraryItemSelected(item) {
      if (item) {
        console.log('📚 Library item selected:', item);
        // No need to populate fields yet - they'll be populated on submit
      }
    },
    buildCueBlock() {
      let block = '<!-- Begin Cue -->\n';
      block += `[Type: ${this.cueType}]\n`;
      block += `[Slug: ${this.slug}]\n`;
      block += `[AssetID: ${this.assetId}]\n`;
      block += `[Name: ${this.name}]\n`;
      block += `[Duration: ${this.duration}]\n`;
      block += `[Alpha: ${this.alpha}]\n`;
      block += `[Audio: ${this.audio}]\n`;
      if (this.mediaUrl) {
        block += `[Media URL: ${this.mediaUrl}]\n`;
      }
      block += '<!-- End Cue -->';
      return block;
    },
    handleAbort() {
      this.$emit('update:show', false);
      this.reset();
    },
    reset() {
      this.slug = '';
      this.assetId = '';
      this.name = '';
      this.duration = '';
      this.mediaUrl = '';
      this.alpha = false;
      this.audio = true;
      this.saveToLibrary = false;
      this.selectedLibraryItem = null;
      this.selectedTab = 'existing';
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        // Fetch library items when modal opens
        this.fetchLibraryItems();
      } else {
        this.reset();
      }
    }
  }
};
</script>

<style scoped>
/* Fix text visibility - add proper padding */
.v-card-text {
  padding-top: 32px !important;
}

/* Ensure text fields have proper spacing and prevent label cutoff */
.v-text-field,
.v-textarea,
.v-select,
.v-checkbox {
  margin-bottom: 16px;
  margin-top: 8px;
}

/* Prevent label from being cut off */
:deep(.v-field__field) {
  padding-top: 12px;
  padding-bottom: 12px;
}

/* Fix textarea input fading/cutoff issue */
:deep(.v-field__input) {
  padding-top: 8px !important;
  min-height: auto !important;
}

:deep(textarea.v-field__input) {
  padding-top: 8px !important;
  line-height: 1.5 !important;
}
</style>
