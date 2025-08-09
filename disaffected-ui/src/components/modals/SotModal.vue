<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card>
      <v-card-title>Add Sound on Tape (SOT)</v-card-title>
      <v-card-text>
        <v-text-field 
          v-model="filename" 
          label="Audio File Name" 
          variant="outlined"
          required
        ></v-text-field>
        <v-text-field 
          v-model="duration" 
          label="Duration" 
          variant="outlined"
          placeholder="00:00:30"
          required
        ></v-text-field>
        <v-textarea 
          v-model="description" 
          label="Description (optional)" 
          variant="outlined"
          rows="2"
        ></v-textarea>
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
        <v-btn color="success" @click="submit" :disabled="!filename || !duration">Insert</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'SotModal',
  props: {
    show: { type: Boolean, required: true },
  },
  emits: ['update:show', 'submit'],
  data() {
    return {
      filename: '',
      duration: '',
      description: '',
      timestamp: ''
    }
  },
  methods: {
    submit() {
      const cueData = {
        type: 'SOT',
        filename: this.filename,
        duration: this.duration,
        description: this.description,
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
      this.filename = ''
      this.duration = ''
      this.description = ''
      this.timestamp = ''
    }
  }
}
</script>
