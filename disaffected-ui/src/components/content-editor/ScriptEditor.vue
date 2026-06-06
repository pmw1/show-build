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

  This is the only script editor — the legacy contenteditable surface is retired
  and it is no longer flag-gated.
-->
<template>
  <div
    class="script-editor-root"
    :class="{
      'script-editor--collapsed': collapsed,
      'script-editor--line-numbers': showLineNumbers,
    }"
  >
    <!-- Multi-selection toolbar — a transient popup shown only while a multi-
         selection is active (BlockMultiSelect plugin). Teleported to <body> and
         position:fixed so it anchors to the VIEWPORT (top third) and can't be
         scrolled out of view or clipped by an ancestor's transform/overflow.
         Mirrors the legacy contenteditable editor's multi-select actions. -->
    <Teleport to="body">
    <div v-if="multiSel.count > 0" class="pm-multiselect-toolbar">
      <div class="pm-ms-count">
        <span class="pm-ms-count-num">{{ multiSel.count }}</span>
        <span class="pm-ms-count-label">block{{ multiSel.count > 1 ? 's' : '' }} selected</span>
      </div>
      <div class="pm-ms-actions">
        <v-btn
          v-if="multiSel.count === 2"
          color="primary" variant="flat" size="small"
          prepend-icon="mdi-swap-vertical"
          @click="swapSelectedBlocks"
        >Swap</v-btn>
        <v-btn
          v-if="multiSel.paragraphCount >= 2"
          color="info" variant="flat" size="small"
          prepend-icon="mdi-set-merge"
          @click="joinSelectedParagraphs"
        >Join</v-btn>
        <v-btn
          v-if="multiSel.paragraphCount > 0"
          :color="multiSel.anyParagraphUnbulleted ? 'default' : 'primary'"
          :variant="multiSel.anyParagraphUnbulleted ? 'outlined' : 'flat'"
          size="small"
          prepend-icon="mdi-format-list-bulleted"
          :title="multiSel.anyParagraphUnbulleted ? 'Add bullets to selected paragraphs' : 'Remove bullets from selected paragraphs'"
          @click="toggleBulletOnSelection"
        >{{ multiSel.anyParagraphUnbulleted ? 'Bullet' : 'Unbullet' }}</v-btn>
        <v-btn
          v-if="multiSel.paragraphCount > 0"
          color="primary" variant="outlined" size="small"
          prepend-icon="mdi-account-voice"
          :title="`Change speaker for ${multiSel.paragraphCount} selected paragraph${multiSel.paragraphCount > 1 ? 's' : ''}`"
          @click="changeSpeakerOnSelection"
        >Change speaker</v-btn>
        <!-- Stub: bulk AI modify of the selected blocks. Wired but not yet
             functional — see modifyWithAi (todo #38). -->
        <v-btn
          color="purple" variant="outlined" size="small"
          prepend-icon="mdi-robot"
          title="Modify the selected blocks with AI (coming soon)"
          @click="modifyWithAi"
        >Modify with AI</v-btn>
        <!-- Reserved placeholder slots for future bulk actions (todo #38). -->
        <v-btn variant="text" size="small" disabled title="Reserved for a future bulk action">—</v-btn>
        <v-btn variant="text" size="small" disabled title="Reserved for a future bulk action">—</v-btn>
        <v-btn
          color="error" variant="flat" size="small"
          prepend-icon="mdi-delete"
          @click="deleteSelectedBlocks"
        >Delete {{ multiSel.count }}</v-btn>
        <v-btn
          variant="text" size="small"
          prepend-icon="mdi-close"
          @click="clearMultiSelection"
        >Cancel</v-btn>
      </div>
    </div>
    </Teleport>

    <!-- EditorContent (not a raw element mount): this is what forwards the
         host app's plugin context (Vuetify) into the cue NodeViews, so the
         cards' <v-card>/<v-btn> render. A manual `new Editor({element})` mount
         bypasses that forwarding and the cue cards come up blank. -->
    <editor-content :editor="editor" class="script-editor-host" />

    <!-- Modify with AI (multi-select): line-numbered selection + instruction;
         AI reworks the selected lines in the context of the whole script and
         returns the full piece, which replaces the script in one undo step. -->
    <ModifyWithAiModal
      v-model:show="aiModifyOpen"
      :ctx="aiModifyContext"
      @apply="applyAiModification"
    />
  </div>
</template>

<script>
import { ref, shallowRef, onMounted, onBeforeUnmount, watch } from 'vue';
import { Editor, EditorContent } from '@tiptap/vue-3';
import { buildScriptExtensions } from './prosemirror/extensions.js';
import { lineNumbersPluginKey } from './prosemirror/LineNumbers.js';
import { readMultiSelection } from './prosemirror/BlockMultiSelect.js';
import { markdownToDoc, docToMarkdown, assertNoLoss } from '@/utils/prosemirror/markdown.js';
import ModifyWithAiModal from './modals/ModifyWithAiModal.vue';

const SAVE_DEBOUNCE_MS = 1500;

export default {
  name: 'ScriptEditor',
  components: { EditorContent, ModifyWithAiModal },
  props: {
    scriptContent: { type: String, default: '' },
    // When false, the editor renders the script with full Script-Mode styling
    // (paragraphs, speakers, cue cards) but is NOT editable — used for the
    // read-only version preview (todo #35). No saves, no cue modals fire.
    editable: { type: Boolean, default: true },
    // Collapse mode: render every paragraph/cue as a compact one-line summary
    // (read-only except drag-reorder). Toggled from EditorPanel (Ctrl+Shift+C).
    collapsed: { type: Boolean, default: false },
    // Continuous line numbering across the show: the number of paragraphs in
    // all rundown items BEFORE this one. First paragraph here = offset + 1.
    lineNumberOffset: { type: Number, default: 0 },
    // Show the per-paragraph line-number gutter. Driven by the
    // Settings → Interface → "Line numbers" toggle (editor.lineNumbers).
    showLineNumbers: { type: Boolean, default: true },
  },
  emits: ['update:scriptContent', 'save-current', 'save-all', 'insert-cue', 'delete-cue', 'edit-cue', 'bulk-change-speaker'],
  setup(props, { emit, expose }) {
    const editor = shallowRef(null);
    const isActivelyEditing = ref(false);

    // Multi-selection summary (count / paragraph-count / bullet state), kept in
    // sync with the BlockMultiSelect plugin via onTransaction so the floating
    // toolbar is reactive. See prosemirror/BlockMultiSelect.js.
    const multiSel = ref({ count: 0, paragraphCount: 0, indices: [], anyParagraphUnbulleted: false });
    function refreshMultiSel() {
      multiSel.value = readMultiSelection(editor.value);
    }

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

    // allowIntentionalDelete=true is passed when the flush FOLLOWS a deliberate
    // cue/content removal (e.g. delete-cue). Without it the loss assertion below
    // sees the cue count drop, treats it as accidental loss, and SUPPRESSES the
    // emit — so the deletion never reaches the DB and the cue reappears on the
    // next item switch. The delete path knows the removal is intentional, so it
    // tells us to skip the count-drop guard (we still block `undefined` markup
    // and dropped FIELD values inside surviving cues).
    function flushPendingChanges(allowIntentionalDelete = false) {
      if (saveTimer) {
        clearTimeout(saveTimer);
        saveTimer = null;
      }
      // CRITICAL: clear the editing guard too. flushPendingChanges() is called
      // on every item switch; if isActivelyEditing stayed true here, the
      // scriptContent reload watcher would bail on the NEXT switch and the
      // editor would freeze on the current item (the "stuck on one item" bug).
      isActivelyEditing.value = false;
      const md = serialize();
      // Loss assertion: never emit a serialization that drops a cue or value
      // (successor to safeEmitScriptContent). On failure, keep the prior content.
      const loss = assertNoLoss(props.scriptContent, md);
      // A negative cueDelta is EXPECTED during an intentional delete; only the
      // accidental-loss signals (undefined markup, dropped fields in surviving
      // cues) should still block.
      // During an intentional delete, BOTH a negative cueDelta AND dropped field
      // values are EXPECTED (the removed cue's fields are gone) — so the only
      // thing we still guard is `undefined` markup (a true serialization-corruption
      // marker). Otherwise the full loss assertion applies.
      const blocked = allowIntentionalDelete ? loss.hasUndefined : !loss.ok;
      if (blocked) {
        // eslint-disable-next-line no-console
        console.error('🚨 ScriptEditor: serialization would lose content — emit suppressed', loss);
        return;
      }
      if (md !== props.scriptContent) emit('update:scriptContent', md);
    }

    // Set while WE dispatch a programmatic, doc-unchanging transaction (line-
    // number refresh, collapse toggle). onUpdate fires for ALL transactions, so
    // without this our meta-only dispatches would call scheduleSave() — which
    // sets isActivelyEditing=true and then makes the NEXT item-switch reload
    // bail (the editor freezes on the last item). Guard those out.
    let programmaticDispatch = false;

    function scheduleSave() {
      if (applyingExternal) return;
      if (programmaticDispatch) return; // ignore our own meta-only transactions
      isActivelyEditing.value = true;
      if (saveTimer) clearTimeout(saveTimer);
      saveTimer = setTimeout(() => {
        saveTimer = null;
        isActivelyEditing.value = false;
        flushPendingChanges();
      }, SAVE_DEBOUNCE_MS);
    }

    // Dispatch a transaction without tripping scheduleSave / isActivelyEditing.
    function dispatchQuiet(trFn) {
      if (!editor.value) return;
      programmaticDispatch = true;
      try {
        const { state, view } = editor.value;
        view.dispatch(trFn(state.tr));
      } finally {
        programmaticDispatch = false;
      }
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
        // The slash (/) cue menu doesn't insert a cue node itself — it hands the
        // chosen cue type up to EditorPanel, which launches the same modal the
        // ADD CUE buttons launch (insertCueFromMenu). So "/" is a shortcut for
        // those buttons.
        extensions: buildScriptExtensions({
          onSelectCue: (cueType) => {
            // The cue is inserted by the modal, which writes back through
            // scriptContent — an EXTERNAL change this editor must reload. Flush
            // any pending edit and clear isActivelyEditing so the scriptContent
            // watcher doesn't skip the reload (it bails while actively editing).
            flushPendingChanges();
            isActivelyEditing.value = false;
            emit('insert-cue', cueType);
          },
        }),
        content: initial.doc.toJSON(),
        editable: props.editable,
        onUpdate: () => { if (props.editable) scheduleSave(); },
        // Every transaction (incl. the multi-select plugin's meta-only txns)
        // refreshes the toolbar's selection summary. Cheap: just reads plugin
        // state. Kept separate from onUpdate (which only fires on doc changes).
        onTransaction: () => refreshMultiSel(),
        // Cue cards delete through here, NOT inside the NodeView: the NodeView
        // calls editor.options.onDeleteCue with the cue's data and a removeNode()
        // that drops that exact atom node. We forward it up to EditorPanel so it
        // opens the existing delete-disposition modal ("Delete Cue Only" /
        // "Delete Cue & Media" for image cues). EditorPanel calls removeNode()
        // once the user confirms a choice.
        onDeleteCue: (payload) => {
          emit('delete-cue', payload);
        },
        // Cue cards edit through here too: the NodeView calls
        // editor.options.onEditCue with { kind: 'fsq'|'gfx', cueData }. We
        // forward to EditorPanel, which opens the matching modal (FsqModal /
        // GfxModal) in edit mode so the user can change the quote text and
        // every other field. The modal writes back through scriptContent.
        onEditCue: (payload) => {
          emit('edit-cue', payload);
        },
      });

      // Seed the line-number offset (continuous-across-show numbering) and the
      // collapse flag into editor storage so the plugin + cue NodeViews read
      // them. CueNodeView reads editor.storage.collapse.on.
      editor.value.storage.lineNumbers.offset = props.lineNumberOffset || 0;
      editor.value.storage.collapse = { on: props.collapsed };
    });

    // Force the line-number decorations to recompute (used when only the offset
    // changes, with no doc edit). Dispatches an empty transaction carrying the
    // plugin meta so its apply() rebuilds.
    function refreshLineNumbers() {
      dispatchQuiet((tr) => tr.setMeta(lineNumbersPluginKey, { offset: true }));
    }

    // Set the `collapsed` attr on every cue node in the doc (whole-editor
    // collapse). One transaction so it's a single undo step.
    //   - quiet=false (default, user pressed Ctrl+Shift+C): dispatches normally
    //     so the collapse choice persists (marker → markdown → save).
    //   - quiet=true (item-switch re-apply): dispatched through the programmatic
    //     guard so it does NOT mark the freshly-loaded item dirty / autosave it.
    function setAllCuesCollapsed(on, quiet = false) {
      if (!editor.value) return;
      const { state, view } = editor.value;
      let tr = state.tr;
      let changed = false;
      state.doc.descendants((node, pos) => {
        if (node.type.name === 'cue') {
          if (!!node.attrs.collapsed !== !!on) {
            tr = tr.setNodeAttribute(pos, 'collapsed', on);
            changed = true;
          }
          return false; // cues are atoms; don't descend
        }
        return false; // only top-level cues; skip descending into paragraphs
      });
      if (!changed) return;
      if (quiet) {
        programmaticDispatch = true;
        try { view.dispatch(tr); } finally { programmaticDispatch = false; }
      } else {
        view.dispatch(tr);
      }
    }

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
        // If collapse mode is ON, the newly-loaded item's cues come in with
        // collapsed=false (their default / their own saved marker). Re-apply the
        // whole-editor collapse so switching items keeps cues collapsed too —
        // paragraphs already follow via the CSS class, but cue collapse is a
        // per-node attr that must be set on the fresh nodes.
        if (props.collapsed) {
          setAllCuesCollapsed(true, true); // quiet — don't dirty the loaded item
        }
      }
    );

    // Continuous line-numbering: when the offset (paragraphs in prior rundown
    // items) changes — e.g. switching rundown items — update storage and
    // recompute the gutter numbers.
    watch(
      () => props.lineNumberOffset,
      (next) => {
        if (!editor.value) return;
        editor.value.storage.lineNumbers.offset = next || 0;
        refreshLineNumbers();
      }
    );

    // Whole-editor collapse toggle (Ctrl+Shift+C). Master switch that:
    //   1) sets EVERY cue node's `collapsed` attr to match (reuses the per-cue
    //      collapse mechanism, so it persists via the Begin-Cue marker), and
    //   2) flips the root .script-editor--collapsed class (the `collapsed` prop
    //      drives it in the template) to squash paragraphs to one line.
    // The paragraph squash is pure CSS (no doc change). The cue-attr sweep IS a
    // doc change, so we let it dispatch normally (it should persist) but mark it
    // programmatic so it doesn't latch isActivelyEditing / freeze item-switch.
    watch(
      () => props.collapsed,
      (on) => {
        if (!editor.value) return;
        editor.value.storage.collapse = { on };
        setAllCuesCollapsed(on);
        // Rebuild the collapsed-paragraph summaries (first5 … last3). The cue
        // sweep above may be a no-op (no cues), so dispatch the toggle meta
        // explicitly and quietly so the summary plugin always recomputes.
        dispatchQuiet((tr) => tr.setMeta('collapseToggle', on));
      }
    );

    // Insert a cue block (raw markdown, e.g. a "<!-- Begin Cue -->...<!-- End Cue -->"
    // string) at the CURRENT cursor position — not at the end of the doc. The cue
    // markdown is parsed to PM node(s) via markdownToDoc, and inserted at the
    // current selection with insertContentAt. We insert at the END of the block
    // the cursor sits in (a cue is a block atom; it can't go mid-paragraph), so it
    // lands right after the paragraph/cue the user has the caret in.
    function insertCueAtCursor(cueMarkdown) {
      if (!editor.value) return false;
      const { doc: parsed } = markdownToDoc(cueMarkdown || '');
      // Collect the parsed cue node(s) as JSON (skip empty placeholder paragraphs
      // markdownToDoc adds when a region is blank).
      const nodes = [];
      parsed.forEach((child) => {
        if (child.type.name === 'cue') nodes.push(child.toJSON());
      });
      if (nodes.length === 0) return false;
      // Insert position: end of the top-level block containing the cursor, so the
      // cue drops in right after the current line rather than splitting it.
      const { $from } = editor.value.state.selection;
      const insertPos = $from.after(1); // after the depth-1 (top-level) block
      editor.value.chain().focus().insertContentAt(insertPos, nodes).run();
      // Flush so the new content serializes back to scriptContent immediately.
      flushPendingChanges();
      return true;
    }

    // ── Multi-select toolbar actions ─────────────────────────────────────────
    // Each calls the matching BlockMultiSelect command. The commands run a single
    // transaction (so UndoRedo covers them) and clear the selection where it makes
    // sense; we then refresh the summary so the toolbar updates immediately.
    function deleteSelectedBlocks() {
      editor.value?.commands.deleteSelectedBlocks();
      refreshMultiSel();
    }
    function swapSelectedBlocks() {
      editor.value?.commands.swapSelectedBlocks();
      refreshMultiSel();
    }
    function joinSelectedParagraphs() {
      editor.value?.commands.joinSelectedParagraphs();
      refreshMultiSel();
    }
    function toggleBulletOnSelection() {
      editor.value?.commands.toggleBulletOnSelection();
      refreshMultiSel();
    }
    function clearMultiSelection() {
      editor.value?.commands.clearBlockSelection();
      refreshMultiSel();
    }
    // Speaker change is the one op that needs UI we don't own: emit the selected
    // paragraph positions up to EditorPanel, which opens the SpeakerSelectorModal
    // and calls back applyBulkSpeaker(speaker) on confirm.
    function changeSpeakerOnSelection() {
      if (!multiSel.value.paragraphCount) return;
      emit('bulk-change-speaker', { count: multiSel.value.paragraphCount });
    }
    function applyBulkSpeaker(speaker) {
      editor.value?.commands.setSpeakerOnSelection(speaker);
      editor.value?.commands.clearBlockSelection();
      refreshMultiSel();
      flushPendingChanges();
    }

    // STUB (todo #38): bulk AI modify of the selected blocks. Not yet functional —
    // it surfaces the selected block indices and notifies the user. When the AI
    // bulk-modify endpoint exists, wire it here (read the selection via
    // readMultiSelection, send block content + a prompt, apply the result in one
    // transaction so UndoRedo covers it).
    // ── Modify with AI ──────────────────────────────────────────────────────
    // Build the line-numbered context for the AI-modify prompt. Line numbers
    // match the on-screen gutter exactly: only TOP-LEVEL paragraphs are numbered
    // (cues skipped), continuous across the show via lineNumberOffset (so the
    // first paragraph of this item = offset + 1). Mirrors LineNumbers.js.
    // Returns { fullSegment, selectedText, selectedLineNumbers, indices } where
    // the two text blobs are line-number-prefixed ("12: ...") and
    // selectedLineNumbers is a compact range string ("12-14, 17").
    function buildModifySelectionContext() {
      const ed = editor.value;
      if (!ed || !ed.state) return null;
      const sel = readMultiSelection(ed);
      if (!sel.count) return null;

      const offset = ed.storage?.lineNumbers?.offset || 0;
      const selectedSet = new Set(sel.indices);
      const fullLines = [];
      const selLines = [];
      const selNums = [];
      let lineNo = offset; // running paragraph line number (pre-increment below)

      ed.state.doc.forEach((node, _pos, blockIndex) => {
        if (node.type.name !== 'paragraph') return; // cues are not line-numbered
        lineNo += 1;
        const text = (node.textContent || '');
        const numbered = `${lineNo}: ${text}`;
        fullLines.push(numbered);
        if (selectedSet.has(blockIndex)) {
          selLines.push(numbered);
          selNums.push(lineNo);
        }
      });

      return {
        indices: sel.indices,
        count: sel.count,
        fullSegment: fullLines.join('\n'),
        selectedText: selLines.join('\n'),
        selectedLineNumbers: compactRanges(selNums),
      };
    }

    // [12,13,14,17] -> "12-14, 17"
    function compactRanges(nums) {
      if (!nums.length) return '';
      const sorted = [...nums].sort((a, b) => a - b);
      const out = [];
      let start = sorted[0];
      let prev = sorted[0];
      for (let i = 1; i <= sorted.length; i++) {
        const n = sorted[i];
        if (n === prev + 1) { prev = n; continue; }
        out.push(start === prev ? `${start}` : `${start}-${prev}`);
        start = prev = n;
      }
      return out.join(', ');
    }

    // Modal state. modifyWithAi() (toolbar click) snapshots the selection
    // context and opens the modal; the modal component (host-rendered) collects
    // the instruction/preset, calls the LLM via the Prompt Override system, and
    // calls applyAiModification() with the rewritten passage.
    const aiModifyOpen = ref(false);
    const aiModifyContext = ref(null);

    function modifyWithAi() {
      const ctx = buildModifySelectionContext();
      if (!ctx) {
        if (window.notifyUserStandard) {
          window.notifyUserStandard('Select one or more paragraphs first', '#7e57c2', 2500);
        }
        return;
      }
      aiModifyContext.value = ctx;
      aiModifyOpen.value = true;
    }

    // Replace the ENTIRE script with the AI's reworked version (the AI returns
    // the whole piece as markdown, with only the selected blocks changed). Done
    // as ONE ProseMirror transaction over the whole doc so it is a single
    // UNDO step (Ctrl+Z reverts the whole rewrite) and flows into the normal
    // autosave + version-history pipeline (onUpdate -> update:scriptContent).
    // `newMarkdown` is the full reworked script returned by the LLM.
    function applyAiModification(newMarkdown) {
      const ed = editor.value;
      if (!ed || typeof newMarkdown !== 'string' || !newMarkdown.trim()) return false;
      const { state, view } = ed;

      // Parse the returned markdown into a PM doc (same path as load/reload), so
      // speaker/cue/bullet attrs round-trip.
      const parsed = markdownToDoc(newMarkdown);
      const newDoc = parsed.doc;

      // ── WIPE GUARD (data-loss protection) ────────────────────────────────
      // The AI is asked to return the WHOLE script with only the selected lines
      // changed. If it instead returns only the selected snippet (or empties
      // out), a naive whole-doc replace would WIPE the segment. Refuse to apply
      // when the result is implausibly short vs the current script. The caller
      // surfaces this so the user can retry; the script is left untouched.
      const oldLen = state.doc.textContent.trim().length;
      const newLen = (newDoc.textContent || '').trim().length;
      const newBlocks = newDoc.childCount;
      const tooShort = oldLen > 200 && newLen < oldLen * 0.5;
      const empty = newLen === 0 || newBlocks === 0;
      if (empty || tooShort) {
        console.warn('[applyAiModification] REFUSED — result too short, likely the AI returned only the selection (oldLen', oldLen, 'newLen', newLen, ')');
        if (window.notifyUserStandard) {
          window.notifyUserStandard('AI returned only part of the script — not applied (your text is unchanged). Try again.', '#f44336', 5000);
        }
        return false;
      }

      // Replace the whole doc content in a single tr — NOT setContent (which
      // clears undo history). Keeps it undoable and emits onUpdate (autosave +
      // version snapshot).
      const tr = state.tr.replaceWith(0, state.doc.content.size, newDoc.content);
      tr.setMeta('addToHistory', true); // discrete undo step
      view.dispatch(tr);
      view.focus();
      aiModifyOpen.value = false;
      aiModifyContext.value = null;
      return true;
    }

    // Parent reach-in contract (mirrors EditorPanel).
    expose({
      flushPendingChanges,
      isActivelyEditing,
      insertCueAtCursor,
      applyBulkSpeaker,
      saveCurrent: () => {
        flushPendingChanges();
        emit('save-current');
      },
      saveAll: () => {
        flushPendingChanges();
        emit('save-all');
      },
    });

    return {
      editor,
      isActivelyEditing,
      flushPendingChanges,
      // multi-select toolbar
      multiSel,
      deleteSelectedBlocks,
      swapSelectedBlocks,
      joinSelectedParagraphs,
      toggleBulletOnSelection,
      changeSpeakerOnSelection,
      modifyWithAi,
      clearMultiSelection,
      // Modify-with-AI modal state + apply hook (modal is host-rendered)
      aiModifyOpen,
      aiModifyContext,
      applyAiModification,
    };
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

/* ===== Multi-selection toolbar ===== */
/* Rendered as a FIXED overlay (relative to the viewport, not the scrolling
   editor host) so it can never scroll out of view, and pinned to the top third
   of the screen with a high z-index so it floats above the editor and other
   chrome. It's a transient popup — appears only while a multi-selection is
   active — so a floating card look (rounded + shadow) reads better than an
   attached bar. The .pm-multiselect-toolbar lives at the editor root but
   position:fixed lifts it out of the flex flow. */
.pm-multiselect-toolbar {
  position: fixed;
  top: 22vh; /* top third of the viewport */
  left: 50%;
  transform: translateX(-50%);
  /* Above all editor content, but BELOW Vuetify's dialog stack (v-overlay
     starts ~2400 and increments per open dialog). This keeps the
     SpeakerSelectorModal — launched from the toolbar's "Change speaker" — on
     top of the toolbar instead of being covered by it. */
  z-index: 2000;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  max-width: min(92vw, 720px);
  padding: 12px 16px;
  background: #ffffff;
  border: 2px solid var(--dropline-color, rgb(33, 150, 243));
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25), 0 2px 8px rgba(0, 0, 0, 0.15);
}
.pm-ms-count {
  display: flex;
  align-items: baseline;
  gap: 6px;
  white-space: nowrap;
}
.pm-ms-count-num {
  font-size: 18px;
  font-weight: 700;
  color: var(--dropline-color, rgb(33, 150, 243));
}
.pm-ms-count-label {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.6);
}
.pm-ms-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  flex-wrap: wrap;
}
/* ProseMirror baseline so the editable area behaves like a document. */
.script-editor-host :deep(.ProseMirror) {
  outline: none;
  min-height: 100%;
}
.script-editor-host :deep(.ProseMirror p) {
  margin: 0 0 0.6em;
  /* Per-user knobs (Settings → Content Editor → Editor Display). These CSS vars
     are set globally by useEditorDisplayPrefs; the legacy contenteditable editor
     consumed them and the new ProseMirror editor must too, or the Script text
     size / line spacing settings do nothing. */
  font-size: var(--editor-script-font-size, 16px);
  line-height: var(--editor-script-line-height, 1.5);
}
.script-editor-host :deep(rev.pm-revision) {
  background: rgba(126, 87, 194, 0.18);
  border-bottom: 1px dashed #7e57c2;
}

/* ===== Bulleted paragraph =====
   A paragraph with the `bullet` attr round-trips as <p class="speaker bullet">.
   Render a • glyph and indent the TEXT — ports the legacy .paragraph-bullet
   visual. The marker is drawn via ::before so it doesn't enter the editable text.

   IMPORTANT layout rules:
   - Use padding-left (NOT margin-left) so the paragraph BOX doesn't move. The
     line-number widget anchors to the paragraph box edge (left: -3.2em), so
     moving the box would drag the number right — the number must stay in the
     gutter, un-indented.
   - The bullet itself sits at the paragraph's natural left edge (left: 0,
     inside the padding), so the BULLET is NOT indented — only the text shifts.
   - The speaker header is a separate widget ABOVE the paragraph and is
     unaffected; the bullet centers on the paragraph's own first text line. */
.script-editor-host :deep(.ProseMirror p.bullet) {
  position: relative;
  /* Indent only the TEXT (every line) further to the right; the box stays put,
     so the line number and the bullet itself do NOT move — only the text. */
  padding-left: 4em;
}
/* IMPORTANT: the bullet uses ::AFTER, not ::before. Every script paragraph also
   carries the `pm-drag-gutter` class, whose ::before is the drag grip (a grey
   mdi-drag-vertical glyph with a hover background). An element has only ONE
   ::before, so a bullet ::before COLLIDED with the grip — that's why the • was
   grey at rest, turned blue/black + grew a background box on hover. ::after is
   unused on these paragraphs, so the bullet owns it cleanly. */
.script-editor-host :deep(.ProseMirror p.bullet)::after {
  content: "\2022"; /* • */
  position: absolute;
  /* Sit roughly halfway into the text indent: the text is padding-left 4em, so
     ~2em is the indent midpoint. Pulling the bullet back to ~1em puts it about
     50% of the indent to the left of where it was — clear of the gutter grip
     and comfortably left of the words. */
  left: 1em;
  width: 1.4em;
  top: 0;
  /* The marker box is exactly ONE text line tall (font-size × line-height of the
     paragraph) so the glyph centers on the FIRST line of text, both vertically
     (align-items:center) and horizontally within its own width (justify:center). */
  height: calc(var(--editor-script-font-size, 16px) * var(--editor-script-line-height, 1.5));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6em; /* bigger glyph */
  line-height: 1;
  font-weight: bold;
  color: #000 !important; /* always black, never inherit the speaker text color */
  background: transparent !important; /* no box behind the glyph */
  pointer-events: none;
}
/* When the paragraph ALSO begins a speaker run, the header widget occupies the
   top of the box and the text starts below it — push the bullet down by the
   header's full height (--pm-speaker-header-h) so the • sits on the first line
   of TEXT, not on the speaker header. :has() reacts to the header child. */
.script-editor-host :deep(.ProseMirror p.bullet:has(.pm-speaker-header))::after {
  top: var(--pm-speaker-header-h, 32px);
}

/* ===== Speaker header =====
   A non-editable widget injected (by the SpeakerHeaders plugin) above each
   paragraph that begins a new speaker run — top of doc / after a cue / when the
   speaker changes. Ports the legacy .speaker-header / .speaker-name visual:
   small uppercase name with a speaker-colored bottom border.

   The header's TOTAL vertical footprint is pinned to --pm-speaker-header-h so a
   bulleted paragraph that also starts a speaker run can offset its • by exactly
   that amount (see the p.bullet:has(.pm-speaker-header) rule above). Keep the
   box geometry below summing to this value:
     margin-top(8) + height(28, incl. padding + border) + margin-bottom(4) = 40. */
.script-editor-host :deep(.ProseMirror) {
  --pm-speaker-header-h: 40px;
}
.script-editor-host :deep(.pm-speaker-header) {
  display: flex;
  align-items: center;
  box-sizing: border-box;
  height: 28px;
  padding: 2px 2px;
  margin-top: 8px;
  margin-bottom: 4px;
  border-bottom: 2px solid;
  user-select: none;
}
.script-editor-host :deep(.pm-speaker-name) {
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Helvetica Light', 'Helvetica', sans-serif;
  font-weight: 600;
  font-size: 0.95rem;
  line-height: 1.2;
}
/* The speaker header widget is rendered INSIDE the <p>, so a bulleted
   paragraph's padding-left would otherwise indent the header too. Pull it back
   to the paragraph's true left edge so the header is unaffected by the bullet
   indent (and the • only marks the first line of TEXT, not the header). */
.script-editor-host :deep(.ProseMirror p.bullet .pm-speaker-header) {
  margin-left: -2.4em;
}

/* ===== Per-paragraph line numbers ===== */
/* The number is a widget decoration injected at each paragraph start. By
   default it's hidden; the gutter only appears when the Settings toggle is on
   (root gets .script-editor--line-numbers). When shown, paragraphs are indented
   to make room and the number is pulled into the gutter. */
.script-editor-host :deep(.pm-line-number) {
  display: none;
}
.script-editor--line-numbers .script-editor-host :deep(.ProseMirror) {
  /* room for the gutter to the left of every block */
  padding-left: 3.2em;
}
.script-editor--line-numbers .script-editor-host :deep(.pm-line-number) {
  display: inline-block;
  position: absolute;
  left: -3.2em;
  width: 2.6em;
  text-align: right;
  user-select: none;
  pointer-events: none;
  font-variant-numeric: tabular-nums;
  font-size: 0.72em;
  line-height: var(--editor-script-line-height, 1.5);
  color: rgba(0, 0, 0, 0.32);
  font-family: 'Courier New', monospace;
}
/* Paragraphs must be position:relative so the absolutely-positioned number
   anchors to the paragraph's own top edge. */
.script-editor--line-numbers .script-editor-host :deep(.ProseMirror p) {
  position: relative;
}

/* ===== Collapse mode ===== */
/* Each paragraph becomes one summary line:
     "first five words …"            (left-aligned)
                          "… last 3" (right-aligned)
   The real inline text is hidden; the summary is drawn from data attributes
   set by the CollapseSummary plugin. Line numbers stay visible (the gutter is
   NOT hidden in collapse mode) and the rows get +1em extra spacing. */
.script-editor--collapsed .script-editor-host :deep(.ProseMirror p.pm-collapsed-para) {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 16px;
  white-space: nowrap;
  overflow: hidden;
  /* +1em spacing between collapsed lines (on top of normal paragraph rhythm) */
  margin-bottom: 1em;
  padding-top: 1px;
  padding-bottom: 1px;
  cursor: default;
  caret-color: transparent;
}
/* Collapsed row: the real paragraph text is collapsed to font-size:0 (so it
   takes no space and can't overflow); the two summary widget spans carry the
   visible text at their own font-size. Gray pill behind it all. The class
   reliably reaches the <p> (node decoration), so these rules are the source of
   truth; the plugin also sets matching inline styles as a belt-and-suspenders. */
/* Collapsed paragraph: a relative block row. The real text is hidden
   (font-size:0); the two summary spans + line number are ABSOLUTELY positioned
   inside it (see CollapseSummary.js inline styles), so layout is immune to
   inherited speaker text-align and the drag gutter — every row's left summary
   starts at the same x. These rules just back up the inline styles. */
.script-editor--collapsed .script-editor-host :deep(.ProseMirror p.pm-collapsed-para) {
  position: relative !important;
  display: block !important;
  white-space: nowrap;
  overflow: visible;                /* don't clip the absolute summary spans */
  font-size: 0 !important;          /* hide the paragraph's own bare text */
  background: transparent;
  height: 24px !important;          /* absolute — em would be 0 at font-size:0 */
  min-height: 24px !important;
  padding: 0 !important;
  margin-bottom: 24px !important;   /* ~one blank line between collapsed rows (px, not em) */
  text-align: left !important;
  text-indent: 0 !important;
}
.script-editor--collapsed .script-editor-host :deep(.pm-collapse-left) {
  position: absolute !important;
  left: 64px !important;            /* after line-number (0-26px) + grabber (28-62px) */
  top: 2px;
  max-width: 55%;
  color: #000 !important;
  font-size: var(--editor-script-font-size, 16px) !important;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: left !important;
}
/* In collapse mode push the drag grabber to the RIGHT of the line number:
   line number occupies 0-26px, grabber sits at 28px. */
.script-editor--collapsed .script-editor-host :deep(.ProseMirror p.pm-collapsed-para.pm-drag-gutter)::before {
  left: 28px !important;
  width: 34px !important;
}
.script-editor--collapsed .script-editor-host :deep(.pm-collapse-right) {
  position: absolute !important;
  right: 0 !important;
  top: 2px;
  color: #000 !important;
  font-size: var(--editor-script-font-size, 16px) !important;
  white-space: nowrap;
  text-align: right;
}
/* Collapse mode ALWAYS shows line numbers (regardless of the Settings toggle).
   The line number sits in the 34px gutter reserved by the collapsed paragraph's
   padding-left. It is a child of the (font-size:0, position:relative) <p>, so we
   absolutely-position it into the gutter and force an explicit font-size/color
   (it would otherwise inherit font-size:0 and vanish). High specificity beats
   the base `.pm-line-number { display:none }` and the drag-gutter rules. */
.script-editor--collapsed .script-editor-host :deep(.ProseMirror p.pm-collapsed-para .pm-line-number) {
  display: inline-block !important;
  position: absolute !important;
  left: 0 !important;
  top: 2px;
  width: 28px;
  text-align: right;
  user-select: none;
  pointer-events: none;
  font-variant-numeric: tabular-nums;
  font-family: 'Courier New', monospace;
  color: #000 !important;
  font-size: 11px !important;       /* absolute — the parent <p> is font-size:0 */
  order: 0;
}
.script-editor--collapsed .script-editor-host :deep(.ProseMirror) {
  caret-color: transparent;
  /* In collapse mode the line number / grabber / summary are absolutely placed
     relative to each <p>, so we don't want the big line-numbers gutter padding
     pushing everything right — start hard against the editor's left edge. */
  padding-left: 0 !important;
}
</style>
