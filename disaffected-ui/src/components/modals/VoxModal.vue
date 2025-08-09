<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card>
      <v-card-title>Add Voiceover (VOX) Cue</v-card-title>
      <v-card-text>
        <v-text-field v-model="slug" label="Slug" required></v-text-field>
        <v-textarea v-model="description" label="Description" required rows="4"></v-textarea>
        <v-text-field v-model="duration" label="Duration (HH:MM:SS)" required></v-text-field>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="error" @click="$emit('update:show', false)">Cancel</v-btn>
        <v-btn color="success" @click="submit">Submit</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
<script>
export default {
  name: 'VoxModal',
  props: { show: Boolean },
  emits: ['update:show', 'submit'],
  data() { return { slug: '', description: '', duration: '' }; },
  methods: {
    submit() {
      this.$emit('submit', { 
        type: 'VOX',
        slug: this.slug, 
        description: this.description, 
        duration: this.duration 
      });
      this.reset();
    },
    reset() { 
      this.slug = ''; 
      this.description = ''; 
      this.duration = ''; 
      this.$emit('update:show', false);
    }
  },
  watch: { 
    show(val) { 
      if (!val) {
        // Optional: Reset fields when dialog is closed externally
        this.slug = ''; 
        this.description = ''; 
        this.duration = ''; 
      }
    } 
  }
}
</script>
<style scoped>.v-card { padding: 16px; }</style>
