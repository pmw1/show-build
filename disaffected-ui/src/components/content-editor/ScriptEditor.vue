<!--
  ScriptEditor.vue — the TipTap/ProseMirror replacement for the legacy
  contenteditable Script Mode surface (migration Phase 4).

  Contract preserved so it can drop in behind EditorPanel's script view:
    prop  scriptContent          : raw markdown string (the DB script_content)
    event update:scriptContent   : serialized markdown string (debounced)
    event save-current / save-all
    exposed flushPendingChanges(): force-apply the pending debounce before
                                   transitions (item switch, mode switch, Ctrl+S)
    exposed isActivelyEditing    : ref the parent reads to gate its own watchers

  The editor owns the ProseMirror document; on every change it SERIALIZES back to
  the legacy markdown form and emits it, so ContentEditor's save/reload/undo/
  remote-sync machinery (the ~9,900-line parent) stays untouched.

  Flag-gated OFF by default via useFeatureFlags (useProseMirrorEditor).
-->
<template>
  <div class="script-editor-root">
    <!-- EditorContent (not a raw element mount): this is what forwards the
         host app's plugin context (Vuetify) into the cue NodeViews, so the
         cards' <v-card>/<v-btn> render. A manual `new Editor({element})` mount
         bypasses that forwarding and the cue cards come up blank. -->
    <editor-content :editor="editor" class="script-editor-host" />
  </div>
</template>

<script>
import { ref, shallowRef, onMounted, onBeforeUnmount, watch } from 'vue';
import { Editor, EditorContent } from '@tiptap/vue-3';
import { buildScriptExtensions } from './prosemirror/extensions.js';
import { markdownToDoc, docToMarkdown, assertNoLoss } from '@/utils/prosemirror/markdown.js';

const SAVE_DEBOUNCE_MS = 1500;

export default {
  name: 'ScriptEditor',
  components: { EditorContent },
  props: {
    scriptContent: { type: String, default: '' },
  },
  emits: ['update:scriptContent', 'save-current', 'save-all'],
  setup(props, { emit, expose }) {
    const editor = shallowRef(null);
    const isActivelyEditing = ref(false);

    // Frontmatter is out-of-band: stripped on load, re-prepended on serialize.
    let frontmatter = '';
    let saveTimer = null;
    // Guard so programmatic setContent (load / item switch) doesn't echo back
    // out through update:scriptContent and fight the parent.
    let applyingExternal = false;

    function serialize() {
      if (!editor.value) return props.scriptContent;
      return docToMarkdown(editor.value.state.doc, frontmatter);
    }

    function flushPendingChanges() {
      if (saveTimer) {
        clearTimeout(saveTimer);
        saveTimer = null;
      }
      const md = serialize();
      // Loss assertion: never emit a serialization that drops a cue or value
      // (successor to safeEmitScriptContent). On failure, keep the prior content.
      const loss = assertNoLoss(props.scriptContent, md);
      if (!loss.ok) {
        // eslint-disable-next-line no-console
        console.error('🚨 ScriptEditor: serialization would lose content — emit suppressed', loss);
        return;
      }
      if (md !== props.scriptContent) emit('update:scriptContent', md);
    }

    function scheduleSave() {
      if (applyingExternal) return;
      isActivelyEditing.value = true;
      if (saveTimer) clearTimeout(saveTimer);
      saveTimer = setTimeout(() => {
        saveTimer = null;
        isActivelyEditing.value = false;
        flushPendingChanges();
      }, SAVE_DEBOUNCE_MS);
    }

    function loadContent(raw) {
      const parsed = markdownToDoc(raw || '');
      frontmatter = parsed.frontmatter;
      applyingExternal = true;
      // setContent with the doc's JSON so attrs (speaker/cue fields) survive.
      editor.value.commands.setContent(parsed.doc.toJSON(), false);
      applyingExternal = false;
    }

    onMounted(() => {
      // No `element` — <EditorContent> mounts the editor's DOM and forwards the
      // host app context (Vuetify) into the cue NodeViews.
      const initial = markdownToDoc(props.scriptContent || '');
      frontmatter = initial.frontmatter;
      editor.value = new Editor({
        extensions: buildScriptExtensions(),
        content: initial.doc.toJSON(),
        onUpdate: () => scheduleSave(),
      });
    });

    onBeforeUnmount(() => {
      if (saveTimer) clearTimeout(saveTimer);
      if (editor.value) editor.value.destroy();
    });

    // External content changes (item switch / Code Mode edits) reload the doc,
    // but only when we're not the source of the change.
    watch(
      () => props.scriptContent,
      (next) => {
        if (applyingExternal || isActivelyEditing.value) return;
        if (!editor.value) return;
        if (next === serialize()) return; // already in sync
        loadContent(next);
      }
    );

    // Parent reach-in contract (mirrors EditorPanel).
    expose({
      flushPendingChanges,
      isActivelyEditing,
      saveCurrent: () => {
        flushPendingChanges();
        emit('save-current');
      },
      saveAll: () => {
        flushPendingChanges();
        emit('save-all');
      },
    });

    return { editor, isActivelyEditing, flushPendingChanges };
  },
};
</script>

<style scoped>
.script-editor-root {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.script-editor-host {
  flex: 1 1 auto;
  overflow-y: auto;
  padding: 12px 16px;
}
/* ProseMirror baseline so the editable area behaves like a document. */
.script-editor-host :deep(.ProseMirror) {
  outline: none;
  min-height: 100%;
}
.script-editor-host :deep(.ProseMirror p) {
  margin: 0 0 0.6em;
  line-height: 1.5;
}
.script-editor-host :deep(rev.pm-revision) {
  background: rgba(126, 87, 194, 0.18);
  border-bottom: 1px dashed #7e57c2;
}
</style>
