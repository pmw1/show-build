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

    <!-- Revision proposal popup (#51): Alt+/ revise, Alt+. add. Type the
         replacement (blank = pure cut), Enter commits, Esc cancels. -->
    <div
      v-if="revPopup.open"
      class="rev-popup"
      :style="{ left: revPopup.x + 'px', top: revPopup.y + 'px' }"
    >
      <span class="rev-popup-label">{{ revPopup.mode === 'add' ? 'Add' : 'Replace with' }}</span>
      <input
        ref="revPopupInput"
        v-model="revPopup.text"
        class="rev-popup-input"
        :placeholder="revPopup.mode === 'add' ? 'text to insert…' : 'replacement (blank = cut)…'"
        @keydown.enter.prevent="commitRevisionPopup"
        @keydown.esc.prevent="cancelRevisionPopup"
      />
      <button class="rev-popup-btn ok" title="Commit (Enter)" @mousedown.prevent="commitRevisionPopup">&#10003;</button>
      <button class="rev-popup-btn cancel" title="Cancel (Esc)" @mousedown.prevent="cancelRevisionPopup">&#10007;</button>
    </div>

    <!-- Needs-attention note panel: teleported to <body> + position:fixed so it
         floats OVER the right sidebar and is never clipped by the editor's
         overflow. Left edge ≈ the block's right edge; Resolved clears the flag. -->
    <Teleport to="body">
    <div
      v-if="flagPanel.open"
      class="flag-note-panel"
      :style="{ left: flagPanel.x + 'px', top: flagPanel.y + 'px' }"
      @mousedown.stop
      @pointerdown="flagPanelInteracting = true"
      @focusin="flagPanelInteracting = true"
      @focusout="onFlagPanelFocusOut"
    >
      <div class="flag-note-header">
        <svg viewBox="0 0 24 24" width="1em" height="1em" fill="currentColor" class="flag-note-icon"><path d="M5 21V4h11l-2 4 2 4H5z"/></svg>
        <span class="flag-note-title">Needs attention</span>
        <span v-if="flagPanel.user" class="flag-note-by">created by: {{ flagPanel.user }}</span>
        <button
          class="flag-note-close"
          title="Close (keeps the flag — does not resolve)"
          @mousedown.prevent="collapseFlagPanel"
        >
          <svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
        </button>
      </div>
      <textarea
        ref="flagNoteInput"
        :value="flagPanel.note"
        class="flag-note-textarea"
        placeholder="Why does this need attention?"
        rows="2"
        @input="updateFlagPanelNote($event.target.value)"
      ></textarea>
      <div class="flag-note-actions">
        <button class="flag-note-resolve" @mousedown.prevent="resolveFlagPanel">
          <svg viewBox="0 0 24 24" width="1em" height="1em" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5L20 7"/></svg>
          Resolved
        </button>
      </div>
    </div>
    </Teleport>

    <!-- Attempt Fix source-video picker: find-media couldn't determine the
         source, so the user chooses from the episode's candidate files. -->
    <Teleport to="body">
      <div v-if="mediaPick" class="rev-diff-overlay" @mousedown.self="cancelMediaPick">
        <div class="rev-diff-modal">
          <div class="rev-diff-header">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h5l2 3h9v11H4z"/><path d="M10 13l5 2.5L10 18z"/></svg>
            <span>Select source video for {{ mediaPick.label }}</span>
            <button class="rev-diff-close" title="Cancel" @click="cancelMediaPick">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
            </button>
          </div>
          <p class="media-pick-intro">
            No source video could be determined automatically
            (searched for “{{ mediaPick.slug }}”<template v-if="mediaPick.sourceHint">, hint “{{ mediaPick.sourceHint }}”</template>).
            Pick the file this cue should use:
          </p>
          <div class="media-pick-list">
            <button
              v-for="f in mediaPick.files"
              :key="f.source_dir + '/' + f.filename"
              class="media-pick-item"
              @click="chooseMediaFile(f)"
            >
              <span class="media-pick-name">{{ f.filename }}</span>
              <span class="media-pick-meta">{{ f.source_dir }}<template v-if="f.size_bytes"> · {{ formatFileSize(f.size_bytes) }}</template></span>
            </button>
          </div>
          <p class="convert-error-hint">
            Choosing a file imports it and starts processing with the extracted
            trim points. Cancel to leave the block flagged.
          </p>
        </div>
      </div>
    </Teleport>

    <!-- Attempt Fix error modal: video-cue conversion is all-or-nothing —
         on failure the block stays flagged and the reasons show here. -->
    <Teleport to="body">
      <div v-if="convertError" class="rev-diff-overlay" @mousedown.self="closeConvertError">
        <div class="rev-diff-modal">
          <div class="rev-diff-header convert-error-header">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16.5v.5"/></svg>
            <span>Attempt Fix failed — no cue was created</span>
            <button class="rev-diff-close" title="Close" @click="closeConvertError">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
            </button>
          </div>
          <div class="convert-error-list">
            <div v-for="(f, i) in convertError.failures" :key="i" class="convert-error-item">
              <strong v-if="f.cue">{{ f.cue }}: </strong>{{ f.reason }}
            </div>
          </div>
          <div class="rev-diff-label">Flagged block</div>
          <div class="rev-diff-text">{{ convertError.block || '(empty)' }}</div>
          <p class="convert-error-hint">
            The block stays flagged. Fix the cause (e.g. drop the media file into the
            episode's preshow/ folder) and click Attempt Fix again.
          </p>
        </div>
      </div>
    </Teleport>

    <!-- Revision diff modal: word-level original-vs-proposed diff. -->
    <Teleport to="body">
      <div v-if="revDiff.open" class="rev-diff-overlay" @mousedown.self="closeRevisionDiff">
        <div class="rev-diff-modal">
          <div class="rev-diff-header">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3M8 11h6M11 8v6"/></svg>
            <span>Proposed change</span>
            <button class="rev-diff-close" title="Close" @click="closeRevisionDiff">
              <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6L6 18"/></svg>
            </button>
          </div>
          <div class="rev-diff-cols">
            <div class="rev-diff-col">
              <div class="rev-diff-label">Original</div>
              <div class="rev-diff-text">{{ revDiff.original || '(empty)' }}</div>
            </div>
            <div class="rev-diff-col">
              <div class="rev-diff-label">Proposed</div>
              <div class="rev-diff-text">{{ revDiff.proposed || '(empty — this is a cut)' }}</div>
            </div>
          </div>
          <div class="rev-diff-label">Diff</div>
          <div class="rev-diff-merged">
            <span
              v-for="(part, i) in revDiff.parts"
              :key="i"
              :class="{ 'diff-add': part.added, 'diff-del': part.removed }"
            >{{ part.value }}</span>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script>
import { ref, shallowRef, onMounted, onBeforeUnmount, watch, nextTick } from 'vue';
import { Editor, EditorContent } from '@tiptap/vue-3';
import { buildScriptExtensions } from './prosemirror/extensions.js';
import { lineNumbersPluginKey } from './prosemirror/LineNumbers.js';
import { readMultiSelection } from './prosemirror/BlockMultiSelect.js';
import { markdownToDoc, docToMarkdown, assertNoLoss } from '@/utils/prosemirror/markdown.js';
import axios from 'axios';
import { convertLegacyToken, convertVideoBlockWithLLM } from '@/modules/legacyCueConvert/conversion.js';
import { isPasteInterpretEnabled } from '@/modules/legacyCueConvert/interpretSetting.js';
import {
  LEGACY_CUE_REGEX,
  LEGACY_CUE_FLAG_LABEL,
  VIDEO_CUE_TOKEN_TYPES,
  VIDEO_CUE_LOOSE_REGEX,
  VIDEO_INOUT_REGEX,
  VIDEO_TECH_LINE_REGEX,
  VIDEO_BLOCK_MEMBER_FLAG_LABEL,
  CUE_CONTINUATION_REGEX,
  normalizeTokenType,
} from '@/modules/legacyCueConvert/patterns.js';
import ModifyWithAiModal from './modals/ModifyWithAiModal.vue';
import { computeDiff } from '@/utils/scriptCompare';
import { WB_DRAG_MIME } from '@/composables/useCueTranslation';

const SAVE_DEBOUNCE_MS = 1500;

export default {
  name: 'ScriptEditor',
  components: { EditorContent, ModifyWithAiModal },
  props: {
    scriptContent: { type: String, default: '' },
    // Episode number (e.g. "0278") — needed by the legacy-cue Convert flow to
    // generate AssetIDs and look up media in the episode's preshow/ folder.
    episode: { type: String, default: '' },
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
  emits: ['update:scriptContent', 'save-current', 'save-all', 'insert-cue', 'delete-cue', 'edit-cue', 'bulk-change-speaker', 'whiteboard-drop'],
  setup(props, { emit, expose }) {
    const editor = shallowRef(null);
    const isActivelyEditing = ref(false);

    // Last KNOWN-GOOD caret position inside the editor. A cue insert (esp. SOT/VO)
    // happens AFTER a modal was open + a processing delay, by which point the live
    // ProseMirror selection has drifted (a blurred editor resolves selection to the
    // doc end) — so insertCueAtCursor using state.selection would drop the cue at
    // the END of the script. We instead remember the caret as the user moves it
    // (only while a real text selection exists) and insert there. Updated on every
    // transaction that carries a selection inside a top-level block.
    let lastCaretPos = null;

    // Legacy-cue sweeper state. The old contenteditable Auto Scrub
    // (EditorPanel, 30s interval) is fully disabled (AUTOSCRUB_DISABLED —
    // server port pending, todo #31), so without this nothing re-scans
    // DB-loaded or hand-typed scripts for legacy tokens / host video blocks;
    // they were only caught at paste time.
    const SWEEP_MS = 30000;
    let sweepTimer = null;
    let lastDocChangeAt = 0;
    let isConverting = false; // pause sweeping while Attempt Fix is in flight

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
        editorProps: {
          // Whiteboard item dragged in from the AssetPoolPanel: remember the
          // drop point as the caret (the same lastCaretPos the cue inserter
          // uses), then hand the item up — ContentEditor opens the matching
          // cue modal and the eventual insert lands where the user dropped.
          // Returning true stops ProseMirror from pasting the payload as text.
          handleDrop: (view, event) => {
            const raw = event.dataTransfer && event.dataTransfer.getData(WB_DRAG_MIME);
            if (!raw) return false;
            event.preventDefault();
            if (!props.editable) return true;
            let item = null;
            try { item = JSON.parse(raw); } catch (e) { return true; }
            const coords = view.posAtCoords({ left: event.clientX, top: event.clientY });
            if (coords) lastCaretPos = coords.pos;
            emit('whiteboard-drop', item);
            return true;
          },
        },
        onUpdate: () => {
          lastDocChangeAt = Date.now();
          if (props.editable) scheduleSave();
        },
        // Every transaction (incl. the multi-select plugin's meta-only txns)
        // refreshes the toolbar's selection summary. Cheap: just reads plugin
        // state. Kept separate from onUpdate (which only fires on doc changes).
        onTransaction: () => {
          refreshMultiSel();
          syncFlagPanelToSelection();
          // Remember the caret ONLY while the editor actually holds focus — a
          // blur (e.g. opening the SOT modal) fires a selection transaction that
          // resolves to the doc end, which we must NOT capture, or the cue would
          // land at the bottom. While focused, record where the user really is.
          const ed = editor.value;
          if (ed && ed.view && ed.view.hasFocus()) {
            lastCaretPos = ed.state.selection.from;
          }
        },
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
        // Revision proposals (#51): Alt+/ (revise/cut) and Alt+. (add) hand off
        // here so we can mark the selection and open the inline replacement
        // popup. See openRevisionPopup.
        onProposeRevision: (mode) => openRevisionPopup(mode),
        // Needs-attention (legacy port): the flag button toggled the attr; this
        // opens/closes the attached note panel for the paragraph at `pos`.
        onFlagParagraph: (pos) => toggleFlagNotePanel(pos),
        // Legacy-cue Convert ("Fix") button: the paragraph at `pos` contains a
        // legacy cue token ((TYPE/slug)); convert it to a real cue block.
        onConvertLegacyCue: (pos) => convertLegacyCueAt(pos),
        // Revision diff button: { original, proposed } -> open the diff modal.
        onShowRevisionDiff: (payload) => openRevisionDiff(payload),
      });

      // Seed the line-number offset (continuous-across-show numbering) and the
      // collapse flag into editor storage so the plugin + cue NodeViews read
      // them. CueNodeView reads editor.storage.collapse.on.
      editor.value.storage.lineNumbers.offset = props.lineNumberOffset || 0;
      editor.value.storage.collapse = { on: props.collapsed };

      // Legacy-cue sweeper: once shortly after load, then on an interval.
      setTimeout(sweepForLegacyCues, 1500);
      sweepTimer = setInterval(sweepForLegacyCues, SWEEP_MS);
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
      if (sweepTimer) clearInterval(sweepTimer);
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
      // Insert position: end of the top-level block containing the caret, so the
      // cue drops in right after the current line rather than splitting it.
      // Prefer the REMEMBERED caret (lastCaretPos) over the live selection: by the
      // time a SOT/VO cue is inserted, the modal + processing delay have drifted
      // the live selection to the doc end, which would append the cue at the
      // bottom. lastCaretPos is the last place the user actually was while focused.
      const doc = editor.value.state.doc;
      let basePos = editor.value.state.selection.from;
      if (lastCaretPos != null && lastCaretPos >= 0 && lastCaretPos <= doc.content.size) {
        basePos = lastCaretPos;
      }
      const $from = doc.resolve(Math.min(Math.max(basePos, 0), doc.content.size));
      // $from.after(1) is the end of the depth-1 (top-level) block; if the
      // resolved pos isn't inside a top-level block (e.g. doc edge), fall back to
      // the doc end so we still insert something rather than throw.
      let insertPos;
      try {
        insertPos = $from.after(1);
      } catch (e) {
        insertPos = doc.content.size;
      }
      editor.value.chain().focus().insertContentAt(insertPos, nodes).run();
      // The inserted cue is now the reference point for any follow-up insert.
      lastCaretPos = insertPos;
      // Flush so the new content serializes back to scriptContent immediately.
      flushPendingChanges();
      return true;
    }

    // Insert plain script text (one or more paragraphs, NOT a cue block) after
    // the block holding the remembered caret. Mirrors insertCueAtCursor but
    // keeps non-cue nodes instead — used by the whiteboard "Script Paragraph"
    // insert (text card → script body).
    function insertParagraphAtCursor(text) {
      if (!editor.value || !text || !text.trim()) return false;
      const { doc: parsed } = markdownToDoc(text);
      const nodes = [];
      parsed.forEach((child) => {
        if (child.type.name !== 'cue' && child.textContent.trim()) nodes.push(child.toJSON());
      });
      if (nodes.length === 0) return false;
      const doc = editor.value.state.doc;
      let basePos = editor.value.state.selection.from;
      if (lastCaretPos != null && lastCaretPos >= 0 && lastCaretPos <= doc.content.size) {
        basePos = lastCaretPos;
      }
      const $from = doc.resolve(Math.min(Math.max(basePos, 0), doc.content.size));
      let insertPos;
      try {
        insertPos = $from.after(1);
      } catch (e) {
        insertPos = doc.content.size;
      }
      editor.value.chain().focus().insertContentAt(insertPos, nodes).run();
      lastCaretPos = insertPos;
      flushPendingChanges();
      return true;
    }

    // Source-video picker modal. When find-media can't determine a source
    // for a video cue during Attempt Fix, this lists the episode's candidate
    // files (preshow/ first, then assets/video) and resolves the pending
    // conversion with the user's choice. Promise-based: pickMediaForCue is
    // handed to convertVideoBlockWithLLM as its pickMedia callback and
    // resolves { filename, source_dir } / null (cancel) / false (no files).
    const mediaPick = ref(null); // { label, slug, sourceHint, files: [], resolve }
    async function pickMediaForCue({ label, slug, cueType, sourceHint }) {
      let files = [];
      try {
        const res = await axios.get('/api/legacy-cue-convert/list-media', {
          params: { episode: props.episode || '', cue_type: cueType },
        });
        files = res.data?.files || [];
      } catch (e) {
        console.warn('[pickMediaForCue] list-media failed:', e);
        return false;
      }
      if (files.length === 0) return false;
      return new Promise((resolve) => {
        mediaPick.value = { label, slug, sourceHint, files, resolve };
      });
    }
    function chooseMediaFile(file) {
      const p = mediaPick.value;
      mediaPick.value = null;
      if (p?.resolve) p.resolve({ filename: file.filename, source_dir: file.source_dir });
    }
    function cancelMediaPick() {
      const p = mediaPick.value;
      mediaPick.value = null;
      if (p?.resolve) p.resolve(null);
    }
    function formatFileSize(bytes) {
      if (!bytes) return '';
      if (bytes >= 1e9) return (bytes / 1e9).toFixed(1) + ' GB';
      if (bytes >= 1e6) return (bytes / 1e6).toFixed(1) + ' MB';
      return Math.max(1, Math.round(bytes / 1e3)) + ' KB';
    }

    // Attempt Fix error modal. Video-cue conversion is all-or-nothing; when
    // it fails, the reasons render here (instead of a transient toast) and
    // the block stays flagged so the user can fix the cause and retry.
    const convertError = ref(null); // { failures: [{cue, reason}], block }
    function openConvertError(e, blockLines) {
      let failures = Array.isArray(e?.failures) && e.failures.length ? e.failures : null;
      if (!failures) {
        let reason = e?.response?.data?.detail || e?.message || 'Unknown error';
        if (/extracted no cues|no convertible cues/i.test(reason)) {
          reason = 'The AI could not extract any usable cue data from this block. ' +
            'Check that the block names a type (SOT/VO/NAT), a slug or title, and try again.';
        }
        failures = [{ cue: null, reason }];
      }
      convertError.value = { failures, block: (blockLines || []).join('\n') };
    }
    function closeConvertError() {
      convertError.value = null;
    }

    // ── Legacy-cue sweeper ──────────────────────────────────────────────────
    // Interval scan over the PM doc (see SWEEP_MS above): flags legacy cue
    // tokens AND host-pasted video-cue blocks so they get the needs-attention
    // box + Attempt Fix button even when they arrived via DB load or hand
    // typing rather than paste.
    //
    // Per paragraph (top level only), in document order:
    //   ANCHOR — strict (TYPE/slug) token, loose/broken video token
    //   ("( SOT / x"), or an IN/OUT-timecode line with no anchor above it →
    //   flagNote = LEGACY_CUE_FLAG_LABEL (renders the Attempt Fix button).
    //   MEMBER — continuation lines (IN/OUT, bare "to", bare quote, bare
    //   timecode) following a video anchor → flagNote =
    //   VIDEO_BLOCK_MEMBER_FLAG_LABEL (tint only, no button) so the whole
    //   block reads as one box. Attempt Fix on the anchor consumes them.
    //   CLEARED — paragraphs carrying one of OUR two labels that no longer
    //   match anything (user fixed the text by hand). Manual user flags
    //   (any other flagNote) are never touched.
    //
    // Attr-only transaction, addToHistory:false, no focus steal. Skipped
    // within 3s of a doc change so it never fights the typist.
    function sweepForLegacyCues() {
      const ed = editor.value;
      if (!ed || !props.editable || isConverting) return;
      if (Date.now() - lastDocChangeAt < 3000) return;

      const { state } = ed;
      const updates = []; // { pos, attrs }
      let inVideoBlock = false;

      // Collect top-level entries first — the classifier needs one-line
      // lookahead (a tech line directly ABOVE a video token belongs to that
      // token's block, tint-only; the button stays on the token line and
      // Attempt Fix gathers the tech line backward into the conversion).
      const entries = [];
      state.doc.forEach((node, offset) => entries.push({ node, offset }));
      const nextRealText = (i) => {
        for (let j = i + 1; j < entries.length; j++) {
          const e = entries[j];
          if (e.node.type.name !== 'paragraph') return null;
          const t = (e.node.textContent || '').trim();
          if (t) return t;
        }
        return null;
      };
      const isVideoAnchorText = (t) => {
        const s = t.match(LEGACY_CUE_REGEX);
        if (s) return VIDEO_CUE_TOKEN_TYPES.has(normalizeTokenType(s[1]));
        return VIDEO_CUE_LOOSE_REGEX.test(t);
      };

      // "Interpret cues & media from pasted script" setting: when OFF, only
      // strict {TYPE/slug} tokens keep their validity flag — the video-block
      // flavors (loose tokens, IN/OUT lines, tech lines) neither anchor nor
      // tint, and any flags we previously set on them fall into the clear
      // branch below and get removed.
      const interpret = isPasteInterpretEnabled();

      entries.forEach(({ node, offset }, i) => {
        if (node.type.name !== 'paragraph') {
          inVideoBlock = false; // a cue card or other block ends the run
          return;
        }
        const text = (node.textContent || '').trim();
        if (!text) return; // blank line inside a block: keep the run alive

        const strict = text.match(LEGACY_CUE_REGEX);
        const strictType = strict ? normalizeTokenType(strict[1]) : null;
        const isTech = interpret && VIDEO_TECH_LINE_REGEX.test(text);
        // Tech line directly above a video token anchor → member of THAT
        // block (tint, no second button).
        const techAboveAnchor = isTech && !strict && !inVideoBlock &&
          (() => { const nxt = nextRealText(i); return !!(nxt && isVideoAnchorText(nxt)); })();
        // Tokenless anchors: a loose/broken video token, or — when no block
        // is already open above — an IN/OUT timecode line or a technical
        // "FULL VIDEO IS TITLED '…'" line (both can START a host cue block).
        const isVideoAnchor =
          (strictType && VIDEO_CUE_TOKEN_TYPES.has(strictType)) ||
          (interpret && !strictType && !techAboveAnchor && (VIDEO_CUE_LOOSE_REGEX.test(text) ||
            (!inVideoBlock && (VIDEO_INOUT_REGEX.test(text) || isTech))));
        const isAnchor = !!strict || isVideoAnchor;
        const isMember = !isAnchor && (techAboveAnchor || (interpret && inVideoBlock &&
          (CUE_CONTINUATION_REGEX.test(text) || VIDEO_INOUT_REGEX.test(text) || isTech)));

        let wantNote = null;
        if (isAnchor) wantNote = LEGACY_CUE_FLAG_LABEL;
        else if (isMember) wantNote = VIDEO_BLOCK_MEMBER_FLAG_LABEL;
        inVideoBlock = isVideoAnchor || (isMember && inVideoBlock);

        const cur = node.attrs;
        if (wantNote) {
          if (!cur.needsAttention || cur.flagNote !== wantNote) {
            // Don't overwrite a user's own note — only claim unflagged
            // paragraphs or ones already carrying one of our labels.
            const ours = !cur.flagNote || cur.flagNote === LEGACY_CUE_FLAG_LABEL ||
              cur.flagNote === VIDEO_BLOCK_MEMBER_FLAG_LABEL;
            if (ours) {
              updates.push({ pos: offset, attrs: { ...cur, needsAttention: true, flagNote: wantNote } });
            }
          }
        } else if (
          cur.needsAttention &&
          (cur.flagNote === LEGACY_CUE_FLAG_LABEL || cur.flagNote === VIDEO_BLOCK_MEMBER_FLAG_LABEL)
        ) {
          // Our flag, but the offending pattern is gone — clear it (mirrors
          // the old Auto Scrub step 3c).
          updates.push({ pos: offset, attrs: { ...cur, needsAttention: false, flagNote: '' } });
        }
      });

      if (updates.length === 0) return;
      let tr = state.tr;
      for (const u of updates) {
        tr = tr.setNodeMarkup(u.pos, undefined, u.attrs);
      }
      tr.setMeta('addToHistory', false);
      ed.view.dispatch(tr);
    }

    // Legacy-cue Convert ("Fix"): the paragraph at `pos` was flagged by the
    // PasteHandler because it contains a legacy cue token ((TYPE/slug)).
    //
    // Two conversion paths:
    //   VIDEO types (SOT/VO/NAT) → LLM extraction. Hosts paste these as
    //   multi-line blocks (token line + IN-/OUT- timecode lines with quoted
    //   in/out cues, random whitespace), and Josh often notes the source
    //   file nearby — so we gather the anchor paragraph PLUS its
    //   continuation lines plus surrounding context and let the local LLM
    //   (extract-cue endpoint) pull out type/slug/trims/cues/source. The
    //   whole block is replaced by the resulting cue block(s), and the
    //   matched media is submitted to the SOT/VO Celery pipeline with the
    //   extracted trim points. Falls back to the regex path on LLM failure.
    //
    //   Everything else → convertLegacyToken (regex), anchor paragraph only.
    //
    // On a hard failure or when nothing converted, leave the flag in place
    // so the user can retry, and surface a non-fatal notice.
    async function convertLegacyCueAt(pos) {
      if (!editor.value) return;
      const { state } = editor.value;
      // Resolve the flagged paragraph node + its range from pos, tracking
      // top-level order so we can walk neighbors for the block + context.
      const topNodes = [];
      let para = null;
      let paraIndex = -1;
      state.doc.forEach((node, offset, index) => {
        topNodes.push({ node, offset, index });
        if (!para && node.type.name === 'paragraph' && pos >= offset && pos < offset + node.nodeSize) {
          para = { node, from: offset, to: offset + node.nodeSize };
          paraIndex = index;
        }
      });
      if (!para) return;

      const paragraphText = para.node.textContent || '';
      const speaker = para.node.attrs.speaker || 'josh';
      const notify = (msg, color, ms) => {
        if (window.notifyUserStandard) window.notifyUserStandard(msg, color, ms);
      };

      // Path decision: strict token whose type is video, or a loose/broken
      // video token anchor (e.g. "( SOT / keysha eight" missing the bracket).
      const tokenMatch = paragraphText.match(LEGACY_CUE_REGEX);
      const tokenType = tokenMatch ? normalizeTokenType(tokenMatch[1]) : null;
      // Video path: strict video token, loose/broken token, a bare
      // IN/OUT-timecode anchor, or a technical "FULL VIDEO IS TITLED '…'"
      // line (sweeper-flagged blocks with no token at all — the LLM derives
      // type/slug/source file from the block + surrounding context).
      const isVideoBlock = tokenType
        ? VIDEO_CUE_TOKEN_TYPES.has(tokenType)
        : (VIDEO_CUE_LOOSE_REGEX.test(paragraphText) ||
           VIDEO_INOUT_REGEX.test(paragraphText) ||
           VIDEO_TECH_LINE_REGEX.test(paragraphText));

      // Gather the block: anchor + following continuation paragraphs
      // (IN-/OUT-/to/quote/timecode lines). Blank paragraphs inside the
      // block are tolerated (random whitespace) but only committed when a
      // real continuation line follows them.
      let blockFrom = para.from;
      let blockTo = para.to;
      let firstBlockIndex = paraIndex;
      let lastBlockIndex = paraIndex;
      const blockLines = [paragraphText];
      if (isVideoBlock) {
        // Backward: technical lines directly ABOVE the anchor ("FROM FULL
        // SURVEILLANCE VIDEO" over a (VO/…) token) belong to this cue —
        // include them so the conversion consumes them AND the LLM sees
        // their filename data in the block itself.
        for (let i = paraIndex - 1; i >= 0; i--) {
          const { node, offset } = topNodes[i];
          if (node.type.name !== 'paragraph') break;
          const txt = (node.textContent || '').trim();
          if (!txt) continue; // blank between tech line and anchor is fine
          if (!VIDEO_TECH_LINE_REGEX.test(txt)) break;
          blockLines.unshift(txt);
          blockFrom = offset;
          firstBlockIndex = i;
        }
        // Forward: IN/OUT/to/quote/timecode continuation lines (and any
        // further tech lines) with random whitespace tolerated.
        let pendingBlankEnd = null;
        for (let i = paraIndex + 1; i < topNodes.length; i++) {
          const { node, offset } = topNodes[i];
          if (node.type.name !== 'paragraph') break;
          const txt = (node.textContent || '').trim();
          if (!txt) {
            pendingBlankEnd = offset + node.nodeSize;
            continue;
          }
          if (!CUE_CONTINUATION_REGEX.test(txt) && !VIDEO_INOUT_REGEX.test(txt) &&
              !VIDEO_TECH_LINE_REGEX.test(txt)) break;
          blockLines.push(txt);
          blockTo = offset + node.nodeSize;
          lastBlockIndex = i;
          pendingBlankEnd = null;
        }
        void pendingBlankEnd; // trailing blanks stay out of the replacement
      }

      // Context for source-file hints: a few top-level nodes on each side
      // of the block. Paragraphs contribute their text; cues contribute a
      // compact "[TYPE: slug-or-note]" line (Josh's notes are often NOTE
      // cues or nearby prose).
      const contextOf = (entry) => {
        const { node } = entry;
        if (node.type.name === 'paragraph') {
          const t = (node.textContent || '').trim();
          // Exclude OTHER cue blocks' data lines (tokens, IN/OUT lines,
          // continuations, tech lines) — context is for source-file hints
          // from prose/notes only. Leaked neighbor-block data makes the
          // LLM emit spurious cues / wrong trims (seen live on ep 0283).
          if (
            LEGACY_CUE_REGEX.test(t) || VIDEO_CUE_LOOSE_REGEX.test(t) ||
            CUE_CONTINUATION_REGEX.test(t) || VIDEO_INOUT_REGEX.test(t) ||
            VIDEO_TECH_LINE_REGEX.test(t)
          ) return '';
          return t;
        }
        if (node.type.name === 'cue') {
          const f = node.attrs.fields || {};
          const detail = f.slug || f.noteText || f.mediaUrl || '';
          return `[${node.attrs.cueType || 'CUE'}: ${detail}]`;
        }
        return '';
      };
      const contextText = [
        ...topNodes.slice(Math.max(0, firstBlockIndex - 4), firstBlockIndex),
        ...topNodes.slice(lastBlockIndex + 1, lastBlockIndex + 5),
      ].map(contextOf).filter(Boolean).join('\n');

      let result = null;
      isConverting = true; // pause the sweeper until the replacement lands
      try {
        if (isVideoBlock) {
          notify('Extracting cue data with AI…', '#7e57c2', 2500);
          try {
            result = await convertVideoBlockWithLLM({
              blockText: blockLines.join('\n'),
              contextText,
              episode: props.episode || '',
              speaker,
              segmentId: null,
              pickMedia: pickMediaForCue,
            });
          } catch (e) {
            // Video conversion is ALL-OR-NOTHING (per user direction): either
            // a complete cue block lands (AssetID + media + pipeline
            // dispatched) or the error pops in a modal and the block stays
            // flagged for retry. No regex fallback — it would produce a
            // half-filled cue. Exception: if every failure is a deliberate
            // picker cancel, a quiet toast beats stacking a second modal.
            console.warn('[convertLegacyCue] video conversion failed:', e);
            const fails = Array.isArray(e?.failures) ? e.failures : [];
            if (fails.length > 0 && fails.every((f) => f.cancelled)) {
              notify('Conversion cancelled — block left flagged.', '#ff9800', 3000);
            } else {
              openConvertError(e, blockLines);
            }
            return;
          }
        }

        if (!result) {
          try {
            result = await convertLegacyToken({
              paragraphSegment: { content: paragraphText, speaker },
              episode: props.episode || '',
              segmentId: null,
            });
          } catch (e) {
            console.warn('[convertLegacyCue] conversion failed:', e);
            notify('Could not convert this cue token — leaving it flagged.', '#f44336', 4000);
            return; // leave flag set for retry
          }
        }

      const segs = (result && result.replacementSegments) || [];
      if (segs.length === 0) {
        notify('Nothing to convert in this paragraph.', '#ff9800', 3000);
        return;
      }

      // Reassemble the replacement region as markdown: text segments become
      // plain paragraphs, cue segments use their rawContent (the cue block md).
      const md = segs
        .map((s) => (s.type === 'cue' ? (s.rawContent || '') : (s.content || '')))
        .filter((chunk) => chunk && chunk.trim())
        .join('\n\n');

      const { doc: parsed } = markdownToDoc(md || '');
      const nodes = [];
      parsed.forEach((child) => {
        // Skip the trailing empty placeholder paragraph markdownToDoc may add.
        if (child.type.name === 'paragraph' && child.content.size === 0) return;
        nodes.push(child.toJSON());
      });
      if (nodes.length === 0) {
        notify('Conversion produced no content — leaving it flagged.', '#f44336', 4000);
        return;
      }

      // Replace the flagged block (gathered tech lines above + anchor
      // paragraph + continuation lines below) with the resolved nodes
      // (one undo step).
      editor.value
        .chain()
        .focus()
        .insertContentAt({ from: blockFrom, to: blockTo }, nodes)
        .run();
      // Persist the conversion. (See #convert-undo below for the history note.)
      flushPendingChanges();

      // ALSO persist server-side, immediately. The editor save path above is
      // a browser-session concern and can silently fail (frozen autosave,
      // 2026-07-18: every conversion orphaned — pipelines completed against
      // cue blocks that only existed in memory, and a reload reverted the
      // script). The backend locates the flagged block by its text and does
      // the same replacement directly in script_content, so a reload after
      // conversion shows the cue block, and the pipeline's completion
      // write-back always finds its cue. Editor save remains as redundancy.
      try {
        const persistRes = await axios.post('/api/legacy-cue-convert/persist-conversion', {
          episode: props.episode || '',
          speaker,
          block_lines: blockLines,
          segments: segs.map((s) => ({
            type: s.type === 'cue' ? 'cue' : 'text',
            content: s.type === 'cue' ? (s.rawContent || '') : (s.content || ''),
          })),
        });
        if (!persistRes.data?.persisted) {
          console.warn('[convertLegacyCue] server-side persist declined:', persistRes.data?.reason);
          notify('Cue converted — server-side save skipped (' + (persistRes.data?.reason || 'unknown') + '); editor save will cover it.', '#ff9800', 4000);
        }
      } catch (e) {
        console.warn('[convertLegacyCue] server-side persist failed (editor save will cover):', e);
      }

      // Report whether media matched (audit carries mediaMatched per cue)
      // and whether the SOT/VO pipeline was dispatched.
      const audit = (result && result.audit) || [];
      const matched = audit.filter((a) => a.mediaMatched).length;
      const dispatched = audit.filter((a) => a.processingJobId).length;
      const viaLLM = audit.some((a) => a.llmExtracted);
      const cues = audit.filter((a) => a.to).length;
      if (cues > 0) {
        notify(
          `${viaLLM ? 'AI-extracted' : 'Converted'} ${cues} cue${cues > 1 ? 's' : ''}` +
            (matched > 0 ? ` — ${matched} with media` : ' (no media matched)') +
            (dispatched > 0 ? `, processing started` : ''),
          matched > 0 ? '#43a047' : '#ff9800',
          5000
        );
      }
      } finally {
        isConverting = false;
      }
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
      // line number -> the selected paragraph's text range { from, to } at build
      // time, so applyAiModification can target the right block per returned line.
      const lineToRange = {};
      let lineNo = offset; // running paragraph line number (pre-increment below)

      ed.state.doc.forEach((node, pos, blockIndex) => {
        if (node.type.name !== 'paragraph') return; // cues are not line-numbered
        lineNo += 1;
        const text = (node.textContent || '');
        const numbered = `${lineNo}: ${text}`;
        fullLines.push(numbered);
        if (selectedSet.has(blockIndex)) {
          selLines.push(numbered);
          selNums.push(lineNo);
          // paragraph text content spans (pos+1 .. pos+1+contentSize)
          lineToRange[lineNo] = { from: pos + 1, to: pos + node.nodeSize - 1 };
        }
      });

      return {
        indices: sel.indices,
        count: sel.count,
        fullSegment: fullLines.join('\n'),
        selectedText: selLines.join('\n'),
        selectedLineNumbers: compactRanges(selNums),
        lineToRange,
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

    // ── Revision proposals (#51): inline popup ──────────────────────────────
    // Alt+/ (revise/cut) marks the selection as a revision immediately (so it
    // strikes through), then opens a small popup at the selection to type a
    // replacement. Enter commits the replacement (setRevisionReplacement); Esc
    // cancels and removes the just-added mark (revert to a clean selection).
    // Alt+. (add) inserts a zero-width insertion proposal at the caret and opens
    // the same popup; the typed text becomes the addition.
    function _revUser() {
      try { return JSON.parse(localStorage.getItem('user-data') || '{}').username || 'unknown'; }
      catch { return 'unknown'; }
    }
    const revPopup = ref({ open: false, mode: 'revise', text: '', x: 0, y: 0, markFrom: 0, markTo: 0 });

    function openRevisionPopup(mode) {
      const ed = editor.value;
      if (!ed) return;
      const { state, view } = ed;
      const { from, to, empty } = state.selection;
      const user = _revUser();
      const ts = new Date().toISOString();

      if (mode === 'revise') {
        if (empty) {
          if (window.notifyUserStandard) window.notifyUserStandard('Select text to propose a revision', '#ff9800', 1800);
          return;
        }
        // Mark the selection as a cut proposal now (strikethrough shows instantly).
        const tr = state.tr.addMark(from, to, state.schema.marks.revision.create({ user, ts, replacement: '' }));
        tr.setMeta('addToHistory', true);
        view.dispatch(tr);
        revPopup.value.markFrom = from;
        revPopup.value.markTo = to;
      } else {
        // Addition: insert a single placeholder char marked as a proposal so the
        // range exists to attach the replacement to; the popup text replaces it.
        const at = to;
        const tr = state.tr.insertText('​', at); // zero-width
        tr.addMark(at, at + 1, state.schema.marks.revision.create({ user, ts, replacement: '' }));
        tr.setMeta('addToHistory', true);
        view.dispatch(tr);
        revPopup.value.markFrom = at;
        revPopup.value.markTo = at + 1;
      }

      // Position the popup near the selection end.
      const coords = view.coordsAtPos(revPopup.value.markTo);
      const hostRect = view.dom.getBoundingClientRect();
      revPopup.value.x = coords.left - hostRect.left;
      revPopup.value.y = coords.bottom - hostRect.top + 4;
      revPopup.value.mode = mode;
      revPopup.value.text = '';
      revPopup.value.open = true;
      nextTick(() => { revPopupInput.value?.focus?.(); });
    }

    const revPopupInput = ref(null);

    function commitRevisionPopup() {
      const ed = editor.value;
      if (!ed || !revPopup.value.open) return;
      const text = (revPopup.value.text || '').trim();
      const { markFrom } = revPopup.value;
      if (text) {
        // Set the replacement on the proposal covering the marked range.
        ed.commands.setRevisionReplacement(markFrom + 1, text);
      }
      // For an addition with no text, drop the placeholder entirely (cancel).
      if (revPopup.value.mode === 'add' && !text) {
        cancelRevisionPopup();
        return;
      }
      revPopup.value.open = false;
      ed.view.focus();
    }

    function cancelRevisionPopup() {
      const ed = editor.value;
      if (!ed || !revPopup.value.open) { revPopup.value.open = false; return; }
      const { state, view } = ed;
      const { markFrom, markTo, mode } = revPopup.value;
      const tr = state.tr;
      if (mode === 'add') {
        // Remove the inserted placeholder char entirely.
        tr.delete(markFrom, markTo);
      } else {
        // Revise: just drop the proposal mark, keep the original text.
        tr.removeMark(markFrom, markTo, state.schema.marks.revision);
      }
      tr.setMeta('addToHistory', true);
      view.dispatch(tr);
      revPopup.value.open = false;
      view.focus();
    }

    // ── Needs-attention note panel (legacy port) ────────────────────────────
    // The flag button (in the NeedsAttention plugin) toggles the paragraph's
    // needsAttention attr, then calls onFlagParagraph(pos) -> here. We open a
    // panel attached to the block's right edge with a note textarea + Resolved
    // button when the block is (now) flagged; close it when it isn't.
    const flagPanel = ref({ open: false, pos: 0, note: '', user: '', x: 0, y: 0 });

    function _paragraphFlaggedAt(pos) {
      const ed = editor.value;
      if (!ed) return null;
      const $p = ed.state.doc.resolve(Math.min(pos, ed.state.doc.content.size));
      // pos is block-start+1 region; find the enclosing paragraph.
      let found = null;
      ed.state.doc.forEach((node, offset) => {
        if (found || node.type.name !== 'paragraph') return;
        if (pos >= offset && pos < offset + node.nodeSize) found = { node, offset };
      });
      void $p;
      return found;
    }

    // Open (expand) the note panel for a given flagged paragraph. The panel's
    // LEFT edge is locked to the RIGHT edge of the paragraph block — i.e. it
    // starts where the text column ends and extends to the right (into the
    // sidebar zone), so it never overlaps the paragraph text. Vertically lined
    // up with the block top.
    // The panel is TELEPORTED to <body> and positioned with VIEWPORT (fixed)
    // coordinates, so it floats OVER the right sidebar and is never clipped by
    // the editor's overflow or covered by sibling panels. Left edge ≈ the
    // editor host's right edge; top lined up with the block.
    const PANEL_W = 360;
    function openFlagPanelForParagraph(p, focusInput) {
      const ed = editor.value;
      if (!ed) return;
      const hostRect = ed.view.dom.getBoundingClientRect();
      const coords = ed.view.coordsAtPos(p.offset + 1);
      flagPanel.value.pos = p.offset + 1;
      flagPanel.value.note = p.node.attrs.flagNote || '';
      flagPanel.value.user = p.node.attrs.flagUser || '';
      // Viewport coords. Left at the host's right edge; clamp so the panel never
      // runs off the right of the screen.
      flagPanel.value.x = Math.min(hostRect.right - 6, window.innerWidth - PANEL_W - 8);
      flagPanel.value.y = coords.top;
      flagPanel.value.open = true;
      if (focusInput) nextTick(() => { flagNoteInput.value?.focus?.(); });
    }

    // FOCUS-DRIVEN: the panel is expanded only while the caret is inside a
    // FLAGGED paragraph; otherwise it collapses to the persistent red flag.
    // Called on every selection change (onSelectionUpdate) + after a fresh flag.
    function syncFlagPanelToSelection() {
      const ed = editor.value;
      if (!ed) { flagPanel.value.open = false; return; }
      // Don't collapse while the user is interacting with the panel itself
      // (typing the note). When focus is inside the teleported panel the editor
      // blurs + may fire a selection tx — without this guard the panel would
      // close the instant you click its textarea. Belt-and-suspenders: an
      // explicit interacting flag (set on pointerdown/focusin) AND an
      // activeElement check (the flag may lag a tick on the first pointerdown).
      if (flagPanel.value.open) {
        if (flagPanelInteracting.value) return;
        const ae = document.activeElement;
        if (ae && ae.closest && ae.closest('.flag-note-panel')) return;
      }
      const pos = ed.state.selection.from;
      const p = _paragraphFlaggedAt(pos);
      if (p && p.node.attrs.needsAttention) {
        // If the user explicitly closed THIS block's panel, keep it collapsed
        // until the caret moves to a different block.
        if (flagPanelSuppressedPos.value === p.offset + 1) { flagPanel.value.open = false; return; }
        flagPanelSuppressedPos.value = null;
        openFlagPanelForParagraph(p, false);
      } else {
        flagPanelSuppressedPos.value = null;
        flagPanel.value.open = false;
      }
    }

    // Called when the flag button is clicked. A FRESH flag opens the panel +
    // focuses the note; clicking the flag on an already-flagged block just lets
    // focus drive it (selection is already in/near the block).
    function toggleFlagNotePanel(pos, freshlyFlagged = false) {
      const ed = editor.value;
      if (!ed) return;
      const p = _paragraphFlaggedAt(pos);
      if (!p || !p.node.attrs.needsAttention) { flagPanel.value.open = false; return; }
      openFlagPanelForParagraph(p, freshlyFlagged);
    }

    const flagNoteInput = ref(null);
    // True while focus is within the panel (typing the note) — keeps the
    // focus-driven sync from collapsing it out from under the user.
    const flagPanelInteracting = ref(false);

    function onFlagPanelFocusOut(e) {
      // Only stop interacting when focus actually LEAVES the panel (not when
      // moving between the textarea and a button inside it).
      const next = e.relatedTarget;
      if (next && next.closest && next.closest('.flag-note-panel')) return;
      flagPanelInteracting.value = false;
      // Focus left the panel → let the selection decide if it should collapse.
      nextTick(() => syncFlagPanelToSelection());
    }

    function updateFlagPanelNote(val) {
      flagPanel.value.note = val;
      const ed = editor.value;
      if (ed) ed.commands.setFlagNote(flagPanel.value.pos, val);
    }

    // Close the panel WITHOUT resolving — collapses back to the flag badge. The
    // block stays flagged. Suppress the focus-sync from immediately reopening it
    // while the caret is still in this same flagged paragraph; cleared once the
    // selection moves to a different block.
    const flagPanelSuppressedPos = ref(null);
    function collapseFlagPanel() {
      flagPanelSuppressedPos.value = flagPanel.value.pos;
      flagPanelInteracting.value = false;
      flagPanel.value.open = false;
      // return focus to the editor so typing continues normally
      const ed = editor.value;
      if (ed) nextTick(() => ed.view.focus());
    }

    function resolveFlagPanel() {
      const ed = editor.value;
      if (ed) ed.commands.resolveNeedsAttention(flagPanel.value.pos);
      flagPanelInteracting.value = false;
      flagPanelSuppressedPos.value = null;
      flagPanel.value.open = false;
    }

    // ── Revision diff modal ─────────────────────────────────────────────────
    // The "Diff" button on a revision proposal opens this, showing the word-level
    // diff (computeDiff -> diff lib) of the ORIGINAL vs the PROPOSED text.
    const revDiff = ref({ open: false, original: '', proposed: '', parts: [] });
    function openRevisionDiff({ original, proposed }) {
      let parts = [];
      try {
        // computeDiff(a, b) -> array of { value, added, removed }. We diff
        // original -> proposed: removed = in original only (red), added = in
        // proposed only (green), neither = unchanged.
        parts = computeDiff(original || '', proposed || '');
      } catch (e) {
        console.warn('revision diff compute failed:', e);
        parts = [{ value: proposed || '', added: true }];
      }
      revDiff.value = { open: true, original: original || '', proposed: proposed || '', parts };
    }
    function closeRevisionDiff() { revDiff.value.open = false; }

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
    // Apply the AI result as REVISION PROPOSALS, one per selected line, so the
    // user accepts/rejects each with the ✓/✗ system. `aiResult` is the model's
    // per-line output ("[12] rewritten text" lines). For each line whose rewrite
    // DIFFERS from the current text, we mark that block's text as a revision with
    // the rewrite as the replacement (the original stays visible, struck). Lines
    // that are unchanged or unparseable are skipped. One transaction (one undo
    // step). Non-sequential selections are fine — each line maps via lineToRange.
    function applyAiModification(aiResult) {
      const ed = editor.value;
      const ctx = aiModifyContext.value;
      if (!ed || !ctx || typeof aiResult !== 'string' || !aiResult.trim()) return false;
      const { state, view } = ed;

      // Parse "[N] text" lines -> { lineNo: text }. Tolerant of leading spaces.
      const rewrites = {};
      for (const raw of aiResult.split('\n')) {
        const m = raw.match(/^\s*\[(\d+)\]\s?(.*)$/);
        if (m) rewrites[parseInt(m[1], 10)] = m[2];
      }
      const lineNos = Object.keys(rewrites).map(Number);
      if (!lineNos.length) {
        if (window.notifyUserStandard) window.notifyUserStandard('AI returned no recognizable line edits — nothing applied.', '#f44336', 4000);
        return false;
      }

      const user = _revUser();
      const ts = new Date().toISOString();
      const revType = state.schema.marks.revision;

      // Build the ranges to mark, descending by position so earlier ranges stay
      // valid as we add marks (addMark doesn't shift positions, but processing
      // descending is safe regardless).
      // Diff each returned line against the original. The LLM is told to return
      // a line VERBATIM when no change is needed; a no-diff line means "this is
      // fine" — we make NO proposal for it. Lines that differ become proposals.
      const targets = [];
      let unchangedCount = 0;
      const normalize = (s) => (s || '').trim();
      for (const ln of lineNos) {
        const range = ctx.lineToRange[ln];
        if (!range) continue; // line wasn't in the selection
        const current = state.doc.textBetween(range.from, range.to, '\n', '\n');
        const next = rewrites[ln];
        // No diff (ignoring incidental leading/trailing whitespace) => fine, skip.
        if (normalize(next) === normalize(current)) { unchangedCount += 1; continue; }
        targets.push({ from: range.from, to: range.to, replacement: next });
      }
      if (!targets.length) {
        // The LLM returned everything verbatim — nothing to change. Positive ack.
        if (window.notifyUserStandard) {
          window.notifyUserStandard('✓ No changes suggested — the selected text looks good.', '#43a047', 3500);
        }
        aiModifyOpen.value = false; aiModifyContext.value = null;
        return false;
      }
      targets.sort((a, b) => b.from - a.from);
      void unchangedCount;

      const tr = state.tr;
      for (const t of targets) {
        // Empty replacement on a non-empty line = a CUT proposal (replacement '').
        tr.addMark(t.from, t.to, revType.create({ user, ts, replacement: t.replacement || '' }));
      }
      tr.setMeta('addToHistory', true);
      view.dispatch(tr);
      view.focus();
      aiModifyOpen.value = false;
      aiModifyContext.value = null;
      if (window.notifyUserStandard) {
        window.notifyUserStandard(`AI proposed ${targets.length} revision${targets.length > 1 ? 's' : ''} — review with ✓ / ✗`, '#7e57c2', 4000);
      }
      return true;
    }

    // Parent reach-in contract (mirrors EditorPanel).
    expose({
      flushPendingChanges,
      isActivelyEditing,
      insertCueAtCursor,
      insertParagraphAtCursor,
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
      // Revision proposal popup
      revPopup,
      revPopupInput,
      commitRevisionPopup,
      cancelRevisionPopup,
      // Attempt Fix error modal
      convertError,
      closeConvertError,
      // Attempt Fix source-video picker
      mediaPick,
      chooseMediaFile,
      cancelMediaPick,
      formatFileSize,
      // Needs-attention note panel
      flagPanel,
      flagNoteInput,
      flagPanelInteracting,
      onFlagPanelFocusOut,
      updateFlagPanelNote,
      resolveFlagPanel,
      collapseFlagPanel,
      // Revision diff modal
      revDiff,
      closeRevisionDiff,
    };
  },
};
</script>

<style scoped>
.script-editor-root {
  height: 100%;
  display: flex;
  flex-direction: column;
  position: relative; /* anchor for the revision popup (#51) */
}

/* Revision proposal popup (#51) */
.rev-popup {
  position: absolute;
  z-index: 50;
  display: flex;
  align-items: center;
  gap: 0.4em;
  background: #fff;
  border: 1px solid #7e57c2;
  border-radius: 6px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
  padding: 0.35em 0.5em;
  max-width: 36em;
  /* Match the user/admin script typesetting (size + font) so the popup feels
     like part of the document, not a tiny chip. */
  font-size: var(--editor-script-font-size, 16px);
  font-family: var(--editor-script-font-family, monospace);
}
.rev-popup-label {
  font-size: 0.7em;
  font-weight: 600;
  color: #7e57c2;
  white-space: nowrap;
}
.rev-popup-input {
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 0.2em 0.45em;
  font-size: 0.9em;
  font-family: inherit;
  min-width: 16em;
  outline: none;
}
.rev-popup-input:focus {
  border-color: #7e57c2;
}
.rev-popup-btn {
  cursor: pointer;
  border: none;
  border-radius: 50%;
  width: 1.5em;
  height: 1.5em;
  font-size: 0.85em;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.rev-popup-btn.ok { background: rgba(76, 175, 80, 0.3); color: #2e7d32; }
.rev-popup-btn.ok:hover { background: rgba(76, 175, 80, 0.55); }
.rev-popup-btn.cancel { background: rgba(244, 67, 54, 0.3); color: #c62828; }
.rev-popup-btn.cancel:hover { background: rgba(244, 67, 54, 0.55); }
.script-editor-host {
  /* SCROLL OWNERSHIP: the editor lives inside a PAGE-scrolled column
     (.script-mode-container is height:auto / overflow:visible so its sticky
     toolbars stay pinned; an outer ancestor owns the scroll). The host must
     therefore NOT be its own scroll container, or two scrollers fight: the
     ancestor chain's min-height (calc(100vh - …) on .script-content-container
     and .visual-script-container) pins the host to roughly one viewport, so
     with overflow-y:auto the host clamps its own scroll range to ~1 screen —
     once the page is scrolled past that, the wheel hits the host (tiny range)
     and the page underneath stops moving. That is the "lost mouse scroll while
     editing" regression. overflow:visible hands scrolling back to the page,
     exactly like the legacy contenteditable list it replaced. */
  flex: 0 0 auto;
  overflow: visible;
  /* Extra RIGHT padding creates a gutter for the per-paragraph hover controls
     (flag/delete) + the needs-attention flag. With overflow:visible the
     controls can also extend slightly past this padding without being clipped. */
  padding: 12px 3.2em 12px 16px;
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
  /* Fill at least the visible area so clicking the empty space below the last
     paragraph still lands the caret. Viewport-relative (not 100%) because the
     host is no longer a definite-height scroller — see .script-editor-host. */
  min-height: calc(100vh - 250px);
}
.script-editor-host :deep(.ProseMirror p) {
  margin: 0 0 0.6em;
  /* Per-user knobs (Settings → Content Editor → Editor Display). These CSS vars
     are set globally by useEditorDisplayPrefs; the legacy contenteditable editor
     consumed them and the new ProseMirror editor must too, or the Script text
     size / line spacing settings do nothing. */
  font-size: var(--editor-script-font-size, 16px);
  line-height: var(--editor-script-line-height, 1.5);
  font-family: var(--editor-script-font-family, monospace);
}
/* ===== Revision proposals (#51) — ports the legacy <rev-block> look =====
   The marked (kill) text is struck through red; the inline chrome after it shows
   the proposed replacement (green), a user·time meta, and ✓/✗ buttons. */
.script-editor-host :deep(rev.pm-revision) {
  text-decoration: line-through;
  /* bolder red for the kill text */
  background-color: rgba(229, 57, 53, 0.30);
  text-decoration-color: #c62828;
  border-radius: 2px;
  padding: 0 1px;
}
.script-editor-host :deep(rev-actions) {
  display: inline-flex;
  align-items: center;
  gap: 0.4em;
  margin: 0 0.4em;
  vertical-align: middle;
  user-select: none;
  /* Reflect the user/admin script typesetting so the inline revision UI matches
     the body text size + font (was a hardcoded ~10-11px). Children use em so
     they scale together. */
  font-size: var(--editor-script-font-size, 16px);
  font-family: var(--editor-script-font-family, monospace);
}
.script-editor-host :deep(rev-add) {
  /* bolder green for the proposed add */
  background-color: rgba(67, 160, 71, 0.32);
  color: #1b5e20;
  border-radius: 2px;
  padding: 0 0.25em;
  font-size: 1em;
}
.script-editor-host :deep(rev-meta) {
  font-size: 0.7em;
  color: #888;
  font-style: italic;
}
/* Labeled action pills (icon + word) — larger + spelled out per request. */
.script-editor-host :deep(rev-btn) {
  cursor: pointer;
  border: none;
  border-radius: 6px;
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
  padding: 0.25em 0.6em;
  font-size: 0.82em;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
}
.script-editor-host :deep(rev-btn svg) { flex: 0 0 auto; }
.script-editor-host :deep(rev-btn-diff) {
  background: rgba(33, 150, 243, 0.18);
  color: #1565c0;
}
.script-editor-host :deep(rev-btn-diff:hover) { background: rgba(33, 150, 243, 0.34); }
.script-editor-host :deep(rev-btn[data-rev-action="accept"]) {
  background-color: rgba(67, 160, 71, 0.45);
  color: #1b5e20;
}
.script-editor-host :deep(rev-btn[data-rev-action="accept"]:hover) {
  background-color: rgba(67, 160, 71, 0.75);
}
.script-editor-host :deep(rev-btn[data-rev-action="reject"]) {
  background-color: rgba(229, 57, 53, 0.45);
  color: #b71c1c;
}
.script-editor-host :deep(rev-btn[data-rev-action="reject"]:hover) {
  background-color: rgba(229, 57, 53, 0.78);
}

/* ===== Delete animation (per Kevin) =====
   pm-del-dying: 3 rapid RED background flashes + the text fades out over 500ms,
   then JS deletes the block. pm-del-neighbor: the two now-adjacent neighbours
   flash BLUE twice (on/off/on/off) and resolve. */
@keyframes pm-del-red-flash {
  0%, 100% { background-color: transparent; }
  50%      { background-color: rgba(229, 57, 53, 0.55); }
}
@keyframes pm-del-text-fade {
  0%   { opacity: 1; }
  100% { opacity: 0; }
}
@keyframes pm-del-blue-flash {
  0%, 50%, 100% { background-color: transparent; }
  25%, 75%      { background-color: rgba(33, 150, 243, 0.45); }
}
.script-editor-host :deep(p.pm-del-dying) {
  border-radius: 4px;
  /* Sequence: 3 red bg flashes first (0.2s x 3 = 0.6s), THEN the block fades out
     over 1s (delay 0.6s so the fade only starts once the flashing ends; 2x the
     prior fade). Holds faded until JS deletes it. */
  animation: pm-del-red-flash 0.2s ease-in-out 3, pm-del-text-fade 1s ease-in 0.6s 1 forwards !important;
}
.script-editor-host :deep(p.pm-del-neighbor) {
  border-radius: 4px;
  /* two on/off cycles across 400ms = on,off,on,off then resolve. */
  animation: pm-del-blue-flash 0.4s ease-in-out 1 !important;
}

/* ===== Needs-attention (legacy port) ===== */
/* Red-tint background on a flagged paragraph (node decoration class). */
.script-editor-host :deep(p.pm-needs-attention) {
  background-color: rgba(229, 57, 53, 0.16);
  box-shadow: inset 3px 0 0 #e53935;
  border-radius: 2px;
}
/* Right-side hover control cluster (flag + delete). Hidden until block hover or
   when flagged; anchored to the right edge of the paragraph box. */
.script-editor-host :deep(na-controls) {
  position: absolute;
  /* Sit in the host's right gutter (created by its right padding) — clear of
     the text but INSIDE the clip boundary so they're never cut off. Negative
     right pulls into that padding without crossing the host edge. */
  right: -2.6em;
  top: 50%;
  transform: translateY(-50%);
  display: inline-flex;
  flex-direction: column; /* flag atop delete */
  align-items: center;
  gap: 0.05em;
  opacity: 0;
  transition: opacity 0.12s ease;
  /* high so the controls aren't covered by neighboring blocks / sidebar edge */
  z-index: 60;
}
.script-editor-host :deep(.ProseMirror p:hover na-controls),
.script-editor-host :deep(na-controls.na-flagged) {
  opacity: 1;
}
/* Flagged + not hovered: show ONLY the persistent red flag (the note collapses
   to this flag). The delete button reappears on paragraph hover. */
.script-editor-host :deep(na-controls.na-flagged .na-delete) {
  display: none;
}
.script-editor-host :deep(.ProseMirror p:hover na-controls.na-flagged .na-delete) {
  display: inline-flex;
}
.script-editor-host :deep(na-btn) {
  cursor: pointer;
  /* hover flag/delete buttons (20% smaller than the prior 2.6em). */
  width: 2.08em;
  height: 2.08em;
  font-size: var(--editor-script-font-size, 16px);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  color: #9e9e9e;
  background: rgba(0, 0, 0, 0.04);
}
.script-editor-host :deep(na-btn svg) {
  width: 1.36em;
  height: 1.36em;
}
.script-editor-host :deep(na-btn.na-flag:hover) { color: #fb8c00; background: rgba(251, 140, 0, 0.14); }
/* The persistent "needs attention" flag left on a flagged block reads as a
   badge: a WHITE flag inside a RED rounded box, 2.5x larger, so the block is
   clearly flagged even when not focused. */
.script-editor-host :deep(na-btn.na-flag.is-active) {
  color: #fff;                 /* the flag glyph (currentColor) is white */
  background: #e53935;         /* red box */
  width: 2.5em;
  height: 2.5em;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}
.script-editor-host :deep(na-btn.na-flag.is-active:hover) {
  background: #d32f2f;
  color: #fff;
}
.script-editor-host :deep(na-btn.na-flag.is-active svg) {
  width: 1.6em;                /* glyph sized to sit nicely inside the box */
  height: 1.6em;
  fill: currentColor;
}
.script-editor-host :deep(na-btn.na-delete:hover) { color: #e53935; background: rgba(229, 57, 53, 0.14); }

/* "Attempt Fix" overlay button — for paragraphs flagged as legacy cue tokens.
   Always visible while flagged (not hover-gated), positioned over the RIGHT
   EDGE of the flagged row itself so it's a quick, obvious one-click resolve.
   Sits above the red tint; clicking converts the token to a cue block. */
.script-editor-host :deep(na-fix) {
  position: absolute;
  right: 0.4em;
  top: 50%;
  transform: translateY(-50%);
  display: inline-flex;
  align-items: center;
  gap: 0.3em;
  padding: 0.18em 0.6em;
  font-size: calc(var(--editor-script-font-size, 16px) * 0.82);
  font-weight: 600;
  line-height: 1.2;
  color: #fff;
  background: #e53935;
  border-radius: 6px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  z-index: 65;             /* above na-controls (60) and the row tint */
  transition: background 0.12s ease;
}
.script-editor-host :deep(na-fix:hover) { background: #c62828; }
.script-editor-host :deep(na-fix svg) { width: 1.15em; height: 1.15em; }
.script-editor-host :deep(na-fix .na-fix-label) { pointer-events: none; }

/* Flag note panel (attached to the right of a flagged paragraph). */
.flag-note-panel {
  /* Teleported to <body> with viewport (fixed) coords, so it floats OVER the
     right sidebar and is never clipped by the editor's overflow. Very high
     z-index to sit above everything. */
  position: fixed;
  z-index: 4000;
  /* Compact note card; left edge ≈ the block's right edge (set inline via left). */
  width: 360px;
  background: #fff;
  border: 1px solid #e53935;
  border-left: 4px solid #e53935;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
  padding: 12px;
}
.flag-note-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 700;
  color: #c62828;
  margin-bottom: 6px;
}
.flag-note-icon { color: #e53935; }
.flag-note-close {
  margin-left: 6px;
  cursor: pointer;
  border: none;
  background: transparent;
  color: #9e9e9e;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
}
.flag-note-close:hover { color: #555; background: rgba(0, 0, 0, 0.06); }
.flag-note-by {
  margin-left: auto;
  font-size: 11px;
  font-weight: 500;
  font-style: italic;
  color: #888;
}
.flag-note-textarea {
  width: 100%;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 6px;
  font-size: 13px;
  font-family: var(--editor-script-font-family, inherit);
  resize: vertical;
  outline: none;
  box-sizing: border-box;
}
.flag-note-textarea:focus { border-color: #e53935; }
.flag-note-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 6px;
}
.flag-note-resolve {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  border: none;
  border-radius: 4px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  color: #1b5e20;
  background: rgba(67, 160, 71, 0.28);
}
.flag-note-resolve:hover { background: rgba(67, 160, 71, 0.5); }

/* Revision diff modal */
.rev-diff-overlay {
  position: fixed;
  inset: 0;
  z-index: 4100;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
}
.rev-diff-modal {
  width: min(720px, 92vw);
  max-height: 80vh;
  overflow: auto;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35);
  padding: 16px;
}

/* Attempt Fix error modal (reuses the rev-diff shell) */
.convert-error-header {
  color: #c62828;
}
.convert-error-list {
  margin: 10px 0 12px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.convert-error-item {
  background: #fdecea;
  border-left: 3px solid #c62828;
  padding: 6px 10px;
  font-size: 0.85rem;
  color: #5f2120;
  border-radius: 0 4px 4px 0;
}
.convert-error-hint {
  margin: 10px 0 0 0;
  font-size: 0.78rem;
  color: rgba(0, 0, 0, 0.55);
}

/* Attempt Fix source-video picker */
.media-pick-intro {
  margin: 10px 0 8px 0;
  font-size: 0.85rem;
  color: rgba(0, 0, 0, 0.7);
}
.media-pick-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 45vh;
  overflow-y: auto;
}
.media-pick-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 12px;
  padding: 7px 10px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  background: #fafafa;
  cursor: pointer;
  text-align: left;
  font: inherit;
  font-size: 0.85rem;
}
.media-pick-item:hover {
  background: #e3f2fd;
  border-color: #1565c0;
}
.media-pick-name {
  font-weight: 500;
  word-break: break-all;
}
.media-pick-meta {
  flex-shrink: 0;
  font-size: 0.72rem;
  color: rgba(0, 0, 0, 0.5);
}
.rev-diff-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  color: #1565c0;
  margin-bottom: 12px;
}
.rev-diff-close {
  margin-left: auto;
  cursor: pointer;
  border: none;
  background: transparent;
  color: #888;
  width: 24px; height: 24px;
  border-radius: 4px;
  display: inline-flex; align-items: center; justify-content: center;
}
.rev-diff-close:hover { background: rgba(0,0,0,0.06); color: #333; }
.rev-diff-cols { display: flex; gap: 12px; margin-bottom: 12px; }
.rev-diff-col { flex: 1 1 0; min-width: 0; }
.rev-diff-label {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.04em; color: #999; margin-bottom: 4px;
}
.rev-diff-text {
  font-family: var(--editor-script-font-family, monospace);
  font-size: 13px; line-height: 1.5;
  background: #f6f6f8; border: 1px solid #eee; border-radius: 4px;
  padding: 8px; white-space: pre-wrap; word-break: break-word;
}
.rev-diff-merged {
  font-family: var(--editor-script-font-family, monospace);
  font-size: 14px; line-height: 1.6;
  background: #fafafa; border: 1px solid #eee; border-radius: 4px;
  padding: 10px; white-space: pre-wrap; word-break: break-word;
}
.rev-diff-merged .diff-add {
  background: rgba(67, 160, 71, 0.28); color: #1b5e20; border-radius: 2px;
}
.rev-diff-merged .diff-del {
  background: rgba(229, 57, 53, 0.25); color: #b71c1c; text-decoration: line-through; border-radius: 2px;
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
