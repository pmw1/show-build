<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card>
      <v-card-title>Add Full-Screen Quote</v-card-title>
      <v-card-text>
        <v-textarea 
          v-model="quote" 
          label="Quote Text" 
          variant="outlined"
          rows="3"
          required
        ></v-textarea>
        <v-text-field 
          v-model="source" 
          label="Source" 
          variant="outlined"
          required
        ></v-text-field>
        <v-text-field 
          v-model="timestamp" 
          label="Timestamp (optional)" 
          variant="outlined"
          placeholder="00:00:00"
        ></v-text-field>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="cancel">Cancel</v-btn>
        <v-btn color="success" @click="submit" :disabled="!quote || !source">Insert</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'FsqModal',
  props: {
    show: { type: Boolean, required: true },
  },
  emits: ['update:show', 'submit'],
  data() {
    return {
      quote: '',
      source: '',
      timestamp: ''
    }
  },
  methods: {
    submit() {
      const cueData = {
        type: 'FSQ',
        quote: this.quote,
        source: this.source,
        timestamp: this.timestamp
      }
      this.$emit('submit', cueData)
      this.reset()
    },
    cancel() {
      this.$emit('update:show', false)
      this.reset()
    },
    reset() {
      this.quote = ''
      this.source = ''
      this.timestamp = ''
    }
  }
}
</script>
