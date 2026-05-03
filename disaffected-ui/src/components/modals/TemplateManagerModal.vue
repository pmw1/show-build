<template>
  <v-dialog v-model="dialog" fullscreen hide-overlay transition="dialog-bottom-transition">
    <v-card>
      <v-toolbar dark color="primary">
        <v-btn icon dark @click="closeModal">
          <v-icon>mdi-close</v-icon>
        </v-btn>
        <v-toolbar-title>Template Manager</v-toolbar-title>
        <v-spacer></v-spacer>
      </v-toolbar>
      <TemplatesView @template-selected="onTemplateSelected" />
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import TemplatesView from '@/views/TemplatesView.vue'

const props = defineProps({ visible: { type: Boolean, default: false } })
const emit = defineEmits(['update:visible', 'template-selected'])

const dialog = ref(props.visible)

watch(() => props.visible, (val) => { dialog.value = val })
watch(dialog, (val) => { if (!val) emit('update:visible', false) })

function closeModal() { emit('update:visible', false) }
function onTemplateSelected(template) { emit('template-selected', template); closeModal() }
function handleKeydown(event) {
  if (event.key === 'Escape' && dialog.value) { event.preventDefault(); event.stopPropagation(); closeModal() }
}
onMounted(() => document.addEventListener('keydown', handleKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', handleKeydown))

void TemplatesView
</script>

<style scoped>
</style>
