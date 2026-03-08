<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card class="rif-modal-card">
      <v-card-title class="rif-modal-header">{{ editCueData ? 'Edit' : 'Add' }} Riff (RIF) Cue</v-card-title>
      <v-card-text>
        <v-text-field
          ref="slugField"
          v-model="slug"
          label="Slug"
          required
          :rules="[v => !!v || 'Slug is required', v => !duplicateSlugs.includes(v) || 'Slug must be unique']"
        ></v-text-field>

        <div class="duration-label">Duration</div>
        <div class="time-spinner">
          <div class="time-segment">
            <v-btn icon size="x-small" variant="text" @click="incrementHours" tabindex="-1">
              <v-icon>mdi-chevron-up</v-icon>
            </v-btn>
            <input
              type="text"
              class="time-input"
              :value="hours"
              maxlength="2"
              @input="onHoursInput"
              @keydown="handleTimeKeydown($event, 'hours')"
            />
            <v-btn icon size="x-small" variant="text" @click="decrementHours" tabindex="-1">
              <v-icon>mdi-chevron-down</v-icon>
            </v-btn>
            <div class="time-label">HRS</div>
          </div>
          <span class="time-colon">:</span>
          <div class="time-segment">
            <v-btn icon size="x-small" variant="text" @click="incrementMinutes" tabindex="-1">
              <v-icon>mdi-chevron-up</v-icon>
            </v-btn>
            <input
              type="text"
              class="time-input"
              :value="minutes"
              maxlength="2"
              @input="onMinutesInput"
              @keydown="handleTimeKeydown($event, 'minutes')"
            />
            <v-btn icon size="x-small" variant="text" @click="decrementMinutes" tabindex="-1">
              <v-icon>mdi-chevron-down</v-icon>
            </v-btn>
            <div class="time-label">MIN</div>
          </div>
          <span class="time-colon">:</span>
          <div class="time-segment">
            <v-btn icon size="x-small" variant="text" @click="incrementSeconds" tabindex="-1">
              <v-icon>mdi-chevron-up</v-icon>
            </v-btn>
            <input
              type="text"
              class="time-input"
              :value="seconds"
              maxlength="2"
              @input="onSecondsInput"
              @keydown="handleTimeKeydown($event, 'seconds')"
            />
            <v-btn icon size="x-small" variant="text" @click="decrementSeconds" tabindex="-1">
              <v-icon>mdi-chevron-down</v-icon>
            </v-btn>
            <div class="time-label">SEC</div>
          </div>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="handleAbort">Cancel (ESC)</v-btn>
        <v-btn color="success" @click="handleSubmit" :disabled="!slug">Submit (Shift+Enter)</v-btn>
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
    editCueData: {
      type: Object,
      default: null
    },
    cueType: {
      type: String,
      default: 'rif'
    }
  },
  data() {
    return {
      slug: '',
      hours: '00',
      minutes: '01',
      seconds: '00'
    };
  },
  computed: {
    duration() {
      return `${this.hours}:${this.minutes}:${this.seconds}`;
    }
  },
  methods: {
    // --- Time spinner methods ---
    pad(val) {
      return String(val).padStart(2, '0');
    },
    clamp(val, min, max) {
      const n = parseInt(val, 10);
      if (isNaN(n)) return min;
      return Math.min(Math.max(n, min), max);
    },
    onHoursInput(e) {
      const raw = e.target.value.replace(/\D/g, '');
      this.hours = this.pad(this.clamp(raw, 0, 99));
    },
    onMinutesInput(e) {
      const raw = e.target.value.replace(/\D/g, '');
      this.minutes = this.pad(this.clamp(raw, 0, 59));
    },
    onSecondsInput(e) {
      const raw = e.target.value.replace(/\D/g, '');
      this.seconds = this.pad(this.clamp(raw, 0, 59));
    },
    incrementHours() { this.hours = this.pad(this.clamp(parseInt(this.hours) + 1, 0, 99)); },
    decrementHours() { this.hours = this.pad(this.clamp(parseInt(this.hours) - 1, 0, 99)); },
    incrementMinutes() { this.minutes = this.pad((parseInt(this.minutes) + 1) % 60); },
    decrementMinutes() { this.minutes = this.pad((parseInt(this.minutes) + 59) % 60); },
    incrementSeconds() { this.seconds = this.pad((parseInt(this.seconds) + 1) % 60); },
    decrementSeconds() { this.seconds = this.pad((parseInt(this.seconds) + 59) % 60); },
    handleTimeKeydown(event, field) {
      if (event.key === 'ArrowUp') {
        event.preventDefault();
        if (field === 'hours') this.incrementHours();
        else if (field === 'minutes') this.incrementMinutes();
        else this.incrementSeconds();
      } else if (event.key === 'ArrowDown') {
        event.preventDefault();
        if (field === 'hours') this.decrementHours();
        else if (field === 'minutes') this.decrementMinutes();
        else this.decrementSeconds();
      }
    },
    parseDuration(dur) {
      if (!dur) return;
      const parts = dur.split(':');
      if (parts.length === 3) {
        this.hours = this.pad(this.clamp(parts[0], 0, 99));
        this.minutes = this.pad(this.clamp(parts[1], 0, 59));
        this.seconds = this.pad(this.clamp(parts[2], 0, 59));
      }
    },

    // --- Submit / Reset ---
    async handleSubmit() {
      if (!this.slug) return;
      await this.submit();
    },
    async submit() {
      const normalizedSlug = this.slug.toLowerCase().replace(/['".,!?]/g, '').replace(/\s+/g, '-');
      try {
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
      this.hours = '00';
      this.minutes = '01';
      this.seconds = '00';
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
      if (val && this.editCueData) {
        this.slug = this.editCueData.slug || '';
        this.parseDuration(this.editCueData.duration);
      } else if (!val) {
        this.reset();
      }
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
.rif-modal-card {
  padding: 16px;
  background-color: #EDE7F6 !important;
}

.rif-modal-header {
  background-color: #5C6BC0;
  color: white;
  border-radius: 4px;
  padding: 12px 16px;
  font-weight: 600;
}

.v-card-text {
  padding-top: 24px !important;
}

.v-text-field {
  margin-bottom: 8px;
  margin-top: 8px;
}

:deep(.v-field__field) {
  padding-top: 12px;
  padding-bottom: 12px;
}

:deep(.v-field__input) {
  padding-top: 8px !important;
  min-height: auto !important;
}

/* Duration label */
.duration-label {
  font-size: 0.85rem;
  color: rgba(0, 0, 0, 0.6);
  margin-bottom: 8px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

/* Time spinner */
.time-spinner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 12px 0;
}

.time-segment {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.time-input {
  width: 52px;
  height: 48px;
  text-align: center;
  font-size: 1.6rem;
  font-weight: 700;
  font-family: 'Roboto Mono', monospace;
  border: 2px solid rgba(92, 107, 192, 0.4);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.85);
  color: #311B92;
  outline: none;
  transition: border-color 0.2s, background 0.2s;
}

.time-input:focus {
  border-color: #5C6BC0;
  background: rgba(255, 255, 255, 0.95);
}

.time-colon {
  font-size: 2rem;
  font-weight: 700;
  color: rgba(0, 0, 0, 0.4);
  padding: 0 2px;
  margin-top: -16px;
}

.time-label {
  font-size: 0.65rem;
  color: rgba(0, 0, 0, 0.45);
  letter-spacing: 1px;
  font-weight: 600;
  margin-top: 2px;
}

.time-segment :deep(.v-btn) {
  color: #5C6BC0 !important;
}

.time-segment :deep(.v-btn:hover) {
  color: #311B92 !important;
}
</style>
