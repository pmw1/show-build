<template>
  <v-btn
    size="small"
    color="primary"
    variant="tonal"
    :loading="busy"
    :disabled="busy"
    class="legacy-cue-convert-btn"
    @click.stop="onClick"
  >
    Convert to Cue
  </v-btn>
</template>

<script setup>
/**
 * "Convert to Cue" button rendered on Auto-Scrub-flagged paragraphs
 * whose flag-note is "Invalid cue code" (i.e. the paragraph contains
 * one or more legacy {SOT/foo} or (SOT/foo) tokens).
 *
 * Click flow:
 *   1. Call convertLegacyToken() with the paragraph's content +
 *      episode + segment id.
 *   2. Emit 'converted' with { replacementSegments, segmentIndex,
 *      audit }. The parent (EditorPanel) splices the segments into
 *      scriptSegments — that write goes through useScriptCore's
 *      safeEmitScriptContent guards automatically.
 *   3. Toast each conversion in the audit list (one per token
 *      converted, including pending-AssetID notices).
 *
 * The button hides itself in the parent template via
 *    v-if="legacyCueConvertEnabled && segment.flagNote === LEGACY_CUE_FLAG_LABEL"
 * so it only appears on legacy-cue-flagged paragraphs and only when
 * the module is enabled in Settings.
 */
import { ref } from 'vue'
import { useToast } from 'vue-toastification'

import { convertLegacyToken } from './conversion'

const props = defineProps({
  paragraphSegment: { type: Object, required: true },
  segmentIndex:     { type: Number, required: true },
  episode:          { type: String, required: true },
  segmentId:        { type: [String, Number], default: null },
})

const emit = defineEmits(['converted'])

const toast = useToast()
const busy = ref(false)

async function onClick() {
  if (busy.value) return
  busy.value = true
  try {
    const result = await convertLegacyToken({
      paragraphSegment: props.paragraphSegment,
      episode: props.episode,
      segmentId: props.segmentId,
    })

    emit('converted', {
      replacementSegments: result.replacementSegments,
      segmentIndex: props.segmentIndex,
      audit: result.audit,
    })

    // One toast per token converted. Includes pending-AssetID and
    // unconvertible-token entries so the user knows what landed.
    for (const entry of result.audit) {
      if (entry.to === null) {
        if (entry.reason === 'unconvertible-type') {
          toast.warning(`Skipped ${entry.from} — type not auto-convertible`)
        } else if (entry.reason === 'empty-slug') {
          toast.warning(`Skipped ${entry.from} — empty slug`)
        }
        continue
      }
      const idDisplay = entry.pending ? '[AssetID pending — retry later]' : entry.assetId
      const mediaNote = entry.mediaMatched ? ' + media linked' : ''
      toast.success(`Converted ${entry.from} → ${idDisplay}${mediaNote}`)
    }
  } catch (err) {
    console.error('[legacyCueConvert] ConvertButton onClick failed:', err)
    toast.error(`Conversion failed: ${err?.message || 'unknown error'}`)
  } finally {
    busy.value = false
  }
}
</script>
