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
<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({ show: Boolean })
const emit = defineEmits(['update:show', 'submit'])

const slug = ref('')
const description = ref('')
const duration = ref('')

function submit() {
  emit('submit', { type: 'VOX', slug: slug.value, description: description.value, duration: duration.value })
  reset()
}
function reset() {
  slug.value = ''; description.value = ''; duration.value = ''
  emit('update:show', false)
}
function handleKeydown(event) {
  if (event.key === 'Escape' && props.show) { event.preventDefault(); event.stopPropagation(); emit('update:show', false) }
}
watch(() => props.show, (val) => { if (!val) { slug.value = ''; description.value = ''; duration.value = '' } })
onMounted(() => document.addEventListener('keydown', handleKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', handleKeydown))
</script>
<style scoped>.v-card { padding: 16px; }</style>
