<!--
  Vue NodeView for the ProseMirror `cue` atom node.

  Bridges the ProseMirror node attrs ({ cueType, fields, imgTag }) to the data
  shape the EXISTING cue cards expect (CueParser.formatForCard output), then
  dispatches to the right card component by cueType — exactly as EditorPanel does
  today. The cards are reused unchanged (Phase 2 wraps, it does not rewrite).

  Attribute edits made inside a card are written back to the node via
  updateAttributes so they persist in the document (and thus the saved markdown).
-->
<template>
  <node-view-wrapper
    class="pm-cue-nodeview"
    :class="{ 'pm-cue-selected': selected }"
    data-cue
    :data-cue-type="node.attrs.cueType"
  >
    <!-- contenteditable=false: the cue is an atom; its internals are not PM-editable -->
    <div contenteditable="false">
      <image-cue-card
        v-if="isImageType"
        :cue-data="cueData"
        @update:cue-data="onCardUpdate"
      />
      <placeholder-cue-card
        v-else
        :cue-data="cueData"
        @update:cue-data="onCardUpdate"
      />
    </div>
  </node-view-wrapper>
</template>

<script>
import { NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3';
import { CueParser } from '@/utils/cueParser.js';
import ImageCueCard from '@/components/content-editor/cards/ImageCueCard.vue';
import PlaceholderCueCard from '@/components/content-editor/cards/PlaceholderCueCard.vue';

// Re-derive the parsed-cue object (camelCased keys, as parseCueBlock produces)
// from the node's ordered field-label map, so formatForCard can build card data.
function fieldsToParsedCue(fields, imgTag, cueType) {
  const parsed = {};
  for (const [label, value] of Object.entries(fields || {})) {
    parsed[CueParser.toCamelCase(label)] = value;
  }
  parsed.type = parsed.type || cueType;
  if (imgTag) {
    parsed.imageTag = imgTag;
    const src = (imgTag.match(/src="([^"]+)"/) || [])[1];
    if (src) parsed.imageSrc = src;
  }
  return parsed;
}

export default {
  name: 'CueNodeView',
  components: { NodeViewWrapper, ImageCueCard, PlaceholderCueCard },
  props: nodeViewProps,
  computed: {
    cueData() {
      const parsed = fieldsToParsedCue(this.node.attrs.fields, this.node.attrs.imgTag, this.node.attrs.cueType);
      return CueParser.formatForCard(parsed);
    },
    isImageType() {
      return CueParser.isImageCueType(this.node.attrs.cueType);
    },
  },
  methods: {
    // When a card edits its data, fold the change back into the node's fields
    // map (preserving label order) so it persists into the document + markdown.
    onCardUpdate(updated) {
      if (!updated) return;
      const fields = { ...this.node.attrs.fields };
      // Map known card fields back to their original labels where present;
      // unknown keys are appended with a display-cased label.
      for (const [key, val] of Object.entries(updated.rawData || updated)) {
        if (val == null || typeof val === 'object') continue;
        const existingLabel = Object.keys(fields).find(
          (l) => CueParser.toCamelCase(l) === key
        );
        const label = existingLabel || CueParser.formatFieldForDisplay(key);
        fields[label] = String(val);
      }
      this.updateAttributes({ fields });
    },
  },
};
</script>

<style scoped>
.pm-cue-nodeview {
  display: block;
  margin: 4px 0;
}
.pm-cue-selected {
  outline: 2px solid var(--v-theme-primary, #1976d2);
  outline-offset: 2px;
  border-radius: 4px;
}
</style>
