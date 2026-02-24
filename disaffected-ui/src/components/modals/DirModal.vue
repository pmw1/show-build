<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card :style="modalStyles">
      <v-card-title :style="headerStyles">Add Note Cue</v-card-title>
      <v-card-text>
        <v-select
          v-model="noteFor"
          :items="productionRoles"
          item-title="name"
          item-value="name"
          label="Note For"
          clearable
          hint="Who is this note intended for?"
          persistent-hint
          class="mb-3"
        ></v-select>
        <v-textarea
          ref="noteField"
          v-model="noteText"
          label="Note"
          required
          :rules="[v => !!v || 'Note text is required']"
          rows="4"
          hint="Special note or instruction for the director/crew"
          persistent-hint
        ></v-textarea>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="handleAbort">Cancel (ESC)</v-btn>
        <v-btn color="success" @click="handleSubmit" :disabled="!noteText">Submit (Shift+Enter)</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
import { cueModalMixin } from '@/mixins/cueModalMixin';
import axios from 'axios';

export default {
  name: 'DirModal',
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
      default: 'NOTE'
    },
    editingCueData: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      noteText: '',
      noteFor: null,
      productionRoles: []
    };
  },
  methods: {
    async loadProductionRoles() {
      try {
        const token = localStorage.getItem('auth-token');
        const response = await axios.get('/api/production-roles/', {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        if (response.data && response.data.data) {
          this.productionRoles = response.data.data;
        }
      } catch (err) {
        console.warn('Failed to load production roles:', err);
      }
    },
    async handleSubmit() {
      if (!this.noteText) {
        return;
      }
      await this.submit();
    },
    async submit() {
      const cueBlockContent = this.buildCueBlock();
      this.$emit('submit', cueBlockContent);
      this.reset();
    },
    buildCueBlock() {
      let block = '<!-- Begin Cue -->\n';
      block += '[Type: NOTE]\n';
      if (this.noteFor) {
        block += `[Note For: ${this.noteFor}]\n`;
      }
      block += `[Note Text: ${this.noteText}]\n`;
      block += '<!-- End Cue -->';
      return block;
    },
    handleAbort() {
      this.$emit('update:show', false);
      this.reset();
    },
    reset() {
      this.noteText = '';
      this.noteFor = null;
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
    show(newVal) {
      // Populate fields when opening in edit mode
      if (newVal && this.editingCueData) {
        this.noteText = this.editingCueData.noteText || '';
        this.noteFor = this.editingCueData.noteFor || null;
      }
      // Only reset when closing, mixin handles opening/focus
      if (!newVal) {
        this.reset();
      }
    }
  },
  async mounted() {
    document.addEventListener('keydown', this.handleKeydown);
    await this.loadProductionRoles();
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown);
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
.v-textarea {
  margin-bottom: 16px;
  margin-top: 8px;
}

/* Prevent label from being cut off */
:deep(.v-field__field) {
  padding-top: 12px;
  padding-bottom: 12px;
}

/* Fix textarea input fading/cutoff issue (Vuetify clip-path bug) */
:deep(.v-field),
:deep(.v-field__field),
:deep(.v-field__input),
:deep(textarea) {
  clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;
  overflow: visible !important;
}

:deep(.v-field__input) {
  padding-top: 8px !important;
  min-height: auto !important;
}

:deep(textarea.v-field__input) {
  padding-top: 8px !important;
  line-height: 1.5 !important;
}
</style>
