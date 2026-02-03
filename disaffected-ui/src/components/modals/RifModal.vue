<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card :style="modalStyles">
      <v-card-title :style="headerStyles">Add Riff (RIF) Cue</v-card-title>
      <v-card-text>
        <v-text-field
          ref="slugField"
          v-model="slug"
          label="Slug"
          required
          :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
        ></v-text-field>
        <v-text-field
          v-model="duration"
          label="Duration (HH:MM:SS)"
          required
          :rules="[v => /^\d{2}:\d{2}:\d{2}$/.test(v) || 'Format must be HH:MM:SS']"
        ></v-text-field>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="handleAbort">Cancel (ESC)</v-btn>
        <v-btn color="success" @click="handleSubmit" :disabled="!slug || !duration">Submit (Shift+Enter)</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios';
import { cueModalMixin } from '@/mixins/cueModalMixin';

export default {
  name: 'RifModal',
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
      default: 'rif'
    }
  },
  data() {
    return {
      slug: '',
      duration: ''
    };
  },
  methods: {
    async handleSubmit() {
      // Validate before submitting
      if (!this.slug || !this.duration) {
        return;
      }
      await this.submit();
    },
    async submit() {
      const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
      try {
        // Generate AssetID for the RIF cue
        const formData = new FormData();
        formData.append('type', 'rif');
        formData.append('slug', normalizedSlug);
        const response = await axios.post('/assetid/generate-legacy', formData, {
          headers: {
            'Accept': 'application/json',
            'X-API-Key': 'FDT5WyO7S2DbBifbDUEsd1H8cmZTT3_qpJXtb3c7qaY'
          }
        });
        const assetID = response.data.id;

        // Emit the RIF cue data
        this.$emit('submit', {
          slug: normalizedSlug,
          duration: this.duration,
          assetID
        });
        this.$toast.success('RIF cue added');
        this.reset();
      } catch (error) {
        console.error('Failed to add RIF cue:', error);
        this.$toast.error('Failed to add RIF cue');
      }
    },
    reset() {
      this.slug = '';
      this.duration = '';
      this.$emit('update:show', false);
    },
    handleKeydown(event) {
      if (event.key === 'Escape' && this.show) {
        event.preventDefault();
        event.stopPropagation();
        this.handleAbort();
      }
    }
  },
  watch: {
    show(val) {
      if (!val) this.reset();
    }
  },
  mounted() {
    document.addEventListener('keydown', this.handleKeydown);
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown);
  }
}
</script>

<style scoped>
.v-card {
  padding: 16px;
}

/* Fix text visibility - add proper padding */
.v-card-text {
  padding-top: 32px !important;
}

/* Ensure text fields have proper spacing and prevent label cutoff */
.v-text-field,
.v-textarea {
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
