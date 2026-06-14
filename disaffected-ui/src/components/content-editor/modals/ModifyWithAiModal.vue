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
                @click="runPreset(p)"
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

// Each preset maps to an overridable Prompt Manager operation (category
// 'modify') whose template returns the instruction string. The `instruction`
// here is only an inline fallback if that op can't be resolved.
const presets = [
  { key: 'spelling', op: 'modify-spelling', label: 'Check spelling', icon: 'mdi-alphabetical', instruction: 'Correct ONLY spelling mistakes in the selected lines. Do not change wording, grammar, tone, or meaning. If a line has no misspellings, return it exactly as-is.' },
  { key: 'grammar', op: 'modify-grammar', label: 'Check grammar', icon: 'mdi-spellcheck', instruction: 'Fix grammar and punctuation in the selected lines without changing the meaning or voice. If a line is already correct, leave it as-is.' },
  { key: 'shorten', op: 'modify-shorten', label: 'Shorten', icon: 'mdi-arrow-collapse-vertical', instruction: 'Shorten and tighten the selected lines while preserving their meaning and voice. If already concise, leave unchanged.' },
  { key: 'expand', op: 'modify-expand', label: 'Expand', icon: 'mdi-arrow-expand-vertical', instruction: 'Expand and elaborate on the selected lines, keeping the same voice. If already detailed, leave unchanged.' },
  { key: 'tone', op: 'modify-tone', label: 'Change tone', icon: 'mdi-tune-vertical', instruction: 'Rewrite the selected lines in a more conversational, engaging broadcast tone. If already in that tone, leave unchanged.' },
  { key: 'stub', op: 'modify-stub', label: 'Insert stub', icon: 'mdi-text-box-outline', instruction: 'Replace the selected lines with a brief placeholder stub/outline for the writer to fill in later.' },
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

// A quick-action button: resolve its instruction from the (overridable) Prompt
// Manager op (category 'modify'), falling back to the inline preset string, then
// run with that instruction.
async function runPreset(p) {
  if (running.value || !props.ctx) return
  let instruction = p.instruction
  try {
    const resolved = await getLLMPrompt(p.op, {}, { category: 'modify' })
    if (resolved && resolved.prompt) instruction = resolved.prompt
  } catch (e) {
    console.warn(`quick-action ${p.op} resolve failed, using inline instruction:`, e)
  }
  run(instruction)
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
      prompt = `You are editing a broadcast script. Below is the FULL script with line numbers (context only), then the SELECTED lines to rewrite, then the instruction.\n\nRewrite ONLY the selected lines per the instruction. Use the full script for context but DO NOT output any non-selected line.\n\nINSTRUCTION: ${instr}\n\nFULL SCRIPT (line-numbered, context only):\n${props.ctx.fullSegment}\n\nSELECTED LINES TO REWRITE (${props.ctx.selectedLineNumbers}):\n${props.ctx.selectedText}\n\nReturn ONE line per selected line, each prefixed with its line number in square brackets, e.g.:\n[12] rewritten text for line 12\n[13] rewritten text for line 13\nKeep the same line numbers. Output ONLY those lines. No commentary, no blank lines, no code fences.`
    }

    const result = await smartCall(prompt, { taskType: 'content-expansion', temperature, max_tokens: maxTokens })
    const out = (typeof result === 'string' ? result : (result?.text || '')).trim()
    if (!out) {
      if (window.notifyUserStandard) window.notifyUserStandard('AI returned no text', '#f44336', 3000)
      running.value = false
      return
    }
    // Host applies + closes on success; on a refused apply (wipe guard) it stays
    // open and notifies. Either way clear running so the modal is usable again.
    emit('apply', out)
    running.value = false
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
