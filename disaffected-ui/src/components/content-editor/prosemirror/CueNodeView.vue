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
    <!-- #49: ONE shell for every cue type. PlaceholderCueCard makes the
         per-type display decision internally (FSQ/SOT/GFX/IMG/... content
         children). The image card is no longer a separate top-level component
         (routing IMG/GFX here also restores GfxCueContent for GFX, which the
         old image-cue-card branch had been shadowing). -->
    <div contenteditable="false">
      <placeholder-cue-card
        :cue-data="cueData"
        :collapsed="node.attrs.collapsed"
        :readonly="!editor.isEditable"
        @toggle-collapsed="onToggleCollapsed"
        @update:cue-data="onCardUpdate"
        @update-meta="onUpdateMeta"
        @modify="onModify"
        @edit-fsq="onEditCue('fsq', $event)"
        @edit-gfx="onEditCue('gfx', $event)"
        @delete="onDelete"
      />
    </div>
  </node-view-wrapper>
</template>

<script>
import { NodeViewWrapper, nodeViewProps } from '@tiptap/vue-3';
import { CueParser } from '@/utils/cueParser.js';
import PlaceholderCueCard from '@/components/content-editor/cards/PlaceholderCueCard.vue';

// Re-derive the parsed-cue object (camelCased keys, as parseCueBlock produces)
// from the node's ordered field-label map, so formatForCard can build card data.
function fieldsToParsedCue(fields, imgTag, cueType) {
  const parsed = {};
  for (const [label, value] of Object.entries(fields || {})) {
    const key = CueParser.toCamelCase(label);
    // Strip the storage-wrapping quotes from the Quote field — exactly as
    // parseCueBlock does. Without this, the TipTap path kept the [Quote: "..."]
    // marks, so the FSQ rendered (and re-saved) with accumulating quotes.
    parsed[key] = key === 'quote' ? CueParser.stripWrappingQuotes(value) : value;
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
  components: { NodeViewWrapper, PlaceholderCueCard },
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
    // Single-field updates emitted by the cards (e.g. the FSQ generate-PNG
    // completion writes `{ field: 'mediaUrl', value }`, the per-cue style
    // sliders write `{ field: 'fontSize', value }`). Fold the one field into
    // the node's label-ordered `fields` map so it persists into the document
    // and the saved markdown — and so the card re-renders with the new value
    // (this is what makes View/Download PNG appear after a render).
    // Toggle the cue's collapsed state. This is a UI-state attr kept SEPARATE
    // from `fields` (it must never leak into card content), written straight to
    // the node so it survives drag-drop and persists into the saved markdown
    // (via the Begin-Cue marker suffix in markdown.js).
    onToggleCollapsed() {
      this.updateAttributes({ collapsed: !this.node.attrs.collapsed });
    },
    onUpdateMeta(payload) {
      if (!payload) return;
      // Two shapes flow through here:
      //  (a) single-field { field, value } — FSQ/GFX/SOT children + style sliders.
      //  (b) multi-field { metadata: {...} } — the IMG meta-edit panel
      //      (ImageCueContent) saves description/credit/caption/duration/tags
      //      together. Normalize both into per-field writes.
      const entries = payload.metadata
        ? Object.entries(payload.metadata)
        : (payload.field ? [[payload.field, payload.value]] : []);
      if (!entries.length) return;

      const fields = { ...this.node.attrs.fields };
      // Canonical labels for fields the rest of the codebase writes a specific
      // way (formatFieldForDisplay would emit "Media Url"; the codebase uses
      // "MediaURL"). Both round-trip to the same camelCase key, but keep the
      // markdown consistent.
      const canonicalLabels = { mediaUrl: 'MediaURL' };
      for (const [field, value] of entries) {
        const existingLabel = Object.keys(fields).find(
          (l) => CueParser.toCamelCase(l) === field
        );
        const label = existingLabel || canonicalLabels[field] || CueParser.formatFieldForDisplay(field);
        fields[label] = value == null ? '' : String(value);
      }
      this.updateAttributes({ fields });
    },
    // IMG modify tools (crop / enhance / resize / comfyui) bubble up from
    // ImageCueContent. Bridge to EditorPanel the same way edit/delete do, so it
    // can open the relevant tool/modal. No-op (logged) if no bridge is wired.
    onModify(payload) {
      const fn = this.editor?.options?.onModifyCue;
      if (typeof fn === 'function') {
        fn(payload);
      } else {
        console.warn('[CueNodeView] onModifyCue bridge not wired; modify ignored', payload);
      }
    },
    // Edit (FSQ / GFX) is handled by EditorPanel, which owns the modals.
    // Same bridge pattern as onDelete: hand the cue's data up via an editor
    // option callback. EditorPanel opens the existing FsqModal / GfxModal in
    // edit mode (initial-data = this cue), where the user edits the quote text
    // and every other detail; the modal writes back through scriptContent.
    onEditCue(kind, cueData) {
      const fn = this.editor?.options?.onEditCue;
      if (typeof fn === 'function') {
        fn({ kind, cueData: cueData || this.cueData });
      } else {
        console.warn('[CueNodeView] onEditCue bridge not wired; edit ignored');
      }
    },
    // NOTE: "Apply All" (apply-all-fsq/gfx) is intentionally NOT bridged here
    // yet — the legacy handler iterates the old scriptSegments array, which is
    // not the source of truth in this editor, so it would be a silent no-op.
    // Wiring it correctly means walking the PM doc and updateAttributes per
    // cue node; tracked separately.
    // Delete is NOT decided here. We hand the cue up to EditorPanel (via the
    // editor's onDeleteCue callback, mirroring the slash-menu's onSelectCue
    // bridge) so it can open the SAME delete-disposition modals the legacy
    // editor used — "Delete Cue Only" vs "Delete Cue & Media" for image cues,
    // a plain confirm for the rest. EditorPanel calls the `removeNode` we pass
    // here once the user confirms a choice; that's what actually removes this
    // exact atom node from the document.
    onDelete() {
      const onDeleteCue = this.editor?.options?.onDeleteCue;
      const removeNode = () => {
        if (typeof this.deleteNode === 'function') {
          this.deleteNode();
        } else if (typeof this.getPos === 'function' && this.getPos() != null) {
          const pos = this.getPos();
          this.editor.chain().focus().deleteRange({ from: pos, to: pos + this.node.nodeSize }).run();
        }
      };
      if (typeof onDeleteCue === 'function') {
        onDeleteCue({ cueData: this.cueData, isImageType: this.isImageType, removeNode });
      } else {
        // No bridge wired (shouldn't happen) — fail safe by removing the node.
        removeNode();
      }
    },
  },
};
</script>

<style scoped>
.pm-cue-nodeview {
  display: block;
  /* #42: more breathing room above/below each cue, and a small left indent so
     the cue block's left edge lines up with the body paragraph TEXT instead of
     sitting flush at the editor edge. The line-number gutter (when on) is a
     shared padding-left on .ProseMirror, so it shifts cues and paragraphs
     together — this margin is the extra nudge to match the paragraph text. */
  margin: 14px 0;
  margin-left: 0.25em;
}
.pm-cue-selected {
  outline: 2px solid var(--v-theme-primary, #1976d2);
  outline-offset: 2px;
  border-radius: 4px;
}
</style>
