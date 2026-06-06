<!--
  ModifyWithAiModal — the "Modify with AI" flow for the multi-select toolbar.

  Shows the SELECTED text (line-numbered, read-only) on the left and an
  instruction field + preset buttons on the right. On run it resolves the prompt
  through the Prompt Override system (operation 'modify-blocks', category
  'modify', editable in Prompt Manager) with the line-numbered variables
  {fullSegment} {selectedText} {selectedLineNumbers} {instruction}, calls the
  LLM, and emits the rewritten passage. The host (ScriptEditor) replaces the
  selected blocks in one transaction.
-->
<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="900" persistent>
    <v-card class="modify-ai-card">
      <v-card-title class="d-flex align-center bg-purple-darken-1 text-white py-2">
        <v-icon class="mr-2">mdi-robot</v-icon>
        Modify with AI
        <span v-if="ctx" class="text-caption ml-2 text-purple-lighten-4">
          {{ ctx.count }} block{{ ctx.count > 1 ? 's' : '' }} · lines {{ ctx.selectedLineNumbers }}
        </span>
        <v-spacer />
        <v-btn icon size="small" variant="text" color="white" @click="cancel" :disabled="running">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>

      <v-card-text class="py-4">
        <v-row>
          <!-- Left: the selected text, line-numbered, read-only -->
          <v-col cols="12" md="6">
            <div class="text-caption text-medium-emphasis mb-1">Selected text</div>
            <pre class="selected-preview">{{ ctx ? ctx.selectedText : '' }}</pre>
          </v-col>

          <!-- Right: presets + instruction -->
          <v-col cols="12" md="6">
            <div class="text-caption text-medium-emphasis mb-1">Quick actions</div>
            <div class="preset-row mb-3">
              <v-btn
                v-for="p in presets"
                :key="p.key"
                size="small"
                variant="outlined"
                color="purple"
                class="ma-1"
                :disabled="running"
                @click="run(p.instruction)"
              >
                <v-icon start size="small">{{ p.icon }}</v-icon>{{ p.label }}
              </v-btn>
            </div>

            <div class="text-caption text-medium-emphasis mb-1">Your instruction</div>
            <v-textarea
              v-model="instruction"
              variant="outlined"
              rows="4"
              auto-grow
              placeholder="Describe what you want done with the selected text…"
              :disabled="running"
              @keydown.ctrl.enter.prevent="run(instruction)"
              @keydown.meta.enter.prevent="run(instruction)"
            />
            <div class="text-caption text-medium-emphasis">Ctrl+Enter to run</div>
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions class="px-4 pb-4">
        <v-spacer />
        <v-btn variant="text" @click="cancel" :disabled="running">Cancel</v-btn>
        <v-btn
          color="purple"
          variant="elevated"
          :loading="running"
          :disabled="running || !instruction.trim()"
          @click="run(instruction)"
        >
          <v-icon start>mdi-robot</v-icon>Modify
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getLLMPrompt } from '@/composables/useLLMPrompts'
import { useLLM } from '@/composables/useLLM'
import { registerModalEsc } from '@/composables/useModalStack'

const props = defineProps({
  show: { type: Boolean, default: false },
  // { count, indices, fullSegment, selectedText, selectedLineNumbers }
  ctx: { type: Object, default: null },
})

const emit = defineEmits(['update:show', 'apply', 'cancel'])

const instruction = ref('')
const running = ref(false)

const presets = [
  { key: 'spelling', label: 'Check spelling', icon: 'mdi-alphabetical', instruction: 'Correct ONLY spelling mistakes in the selected lines. Do not change wording, grammar, tone, or meaning.' },
  { key: 'grammar', label: 'Check grammar', icon: 'mdi-spellcheck', instruction: 'Fix grammar and punctuation in the selected lines without changing the meaning or voice.' },
  { key: 'shorten', label: 'Shorten', icon: 'mdi-arrow-collapse-vertical', instruction: 'Shorten and tighten the selected lines while preserving their meaning and voice.' },
  { key: 'expand', label: 'Expand', icon: 'mdi-arrow-expand-vertical', instruction: 'Expand and elaborate on the selected lines, adding detail while keeping the same voice.' },
  { key: 'tone', label: 'Change tone', icon: 'mdi-tune-vertical', instruction: 'Rewrite the selected lines in a more conversational, engaging broadcast tone.' },
  { key: 'stub', label: 'Insert stub', icon: 'mdi-text-box-outline', instruction: 'Replace the selected lines with a brief placeholder stub/outline (a short skeleton of what this section should cover) for the writer to fill in later.' },
]

// Reset instruction when the modal opens for a fresh selection.
watch(() => props.show, (open) => {
  if (open) { instruction.value = ''; running.value = false }
})

registerModalEsc(() => props.show && !running.value, () => cancel(), 'ModifyWithAiModal')

function cancel() {
  emit('update:show', false)
  emit('cancel')
}

async function run(text) {
  const instr = (text || '').trim()
  if (!instr || running.value || !props.ctx) return
  running.value = true
  try {
    const { smartCall } = useLLM()
    let prompt
    let temperature = 0.7
    let maxTokens = 2000
    try {
      const resolved = await getLLMPrompt(
        'modify-blocks',
        {
          fullSegment: props.ctx.fullSegment,
          selectedText: props.ctx.selectedText,
          selectedLineNumbers: props.ctx.selectedLineNumbers,
          instruction: instr,
        },
        { category: 'modify' }
      )
      prompt = resolved.prompt
      if (resolved.temperature != null) temperature = resolved.temperature
      if (resolved.maxTokens != null) maxTokens = resolved.maxTokens
    } catch (e) {
      console.warn('modify-blocks prompt resolve failed, using inline fallback:', e)
      prompt = `You are editing a broadcast script. Below is the FULL script with line numbers, then the specific SELECTED lines to modify, then the instruction.\n\nModify ONLY the selected lines per the instruction. Leave every other line EXACTLY as-is. Then return the ENTIRE script (all lines, in order) with only those changes applied.\n\nINSTRUCTION: ${instr}\n\nFULL SCRIPT (line-numbered, for context):\n${props.ctx.fullSegment}\n\nSELECTED LINES TO MODIFY (${props.ctx.selectedLineNumbers}):\n${props.ctx.selectedText}\n\nReturn the COMPLETE rewritten script as plain text, paragraphs separated by blank lines. Do NOT include line numbers, do NOT add commentary or preamble, do NOT wrap in code fences.`
    }

    const result = await smartCall(prompt, { taskType: 'content-expansion', temperature, max_tokens: maxTokens })
    const out = (typeof result === 'string' ? result : (result?.text || '')).trim()
    if (!out) {
      if (window.notifyUserStandard) window.notifyUserStandard('AI returned no text', '#f44336', 3000)
      running.value = false
      return
    }
    emit('apply', out)
    // host closes the modal after applying
  } catch (err) {
    console.error('Modify with AI failed:', err)
    if (window.notifyUserStandard) window.notifyUserStandard('Modify with AI failed', '#f44336', 3000)
    running.value = false
  }
}
</script>

<style scoped>
.selected-preview {
  background: #1e1e2e;
  color: #cdd6f4;
  font-family: 'Roboto Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  padding: 12px;
  border-radius: 4px;
  max-height: 320px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}
.preset-row {
  display: flex;
  flex-wrap: wrap;
}
</style>
