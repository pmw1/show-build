# Script Editor Migration Plan — contenteditable → TipTap/ProseMirror

**Status:** Proposed (not started)
**Author:** Claude (show-build session, 2026-05-30)
**Related:** [`EDITOR_PANEL_ARCHITECTURE.md`](EDITOR_PANEL_ARCHITECTURE.md), [`SAVE_RELOAD_SPEC.md`](SAVE_RELOAD_SPEC.md), [`ARCHITECTURE_DECISIONS.md`](ARCHITECTURE_DECISIONS.md)

---

## 1. Why this exists

Script Mode is implemented as a **hand-rolled `contenteditable` editor**: one `contenteditable` div per text segment, edits buffered in a non-reactive object, debounced, reconstructed into a raw markdown string, and saved. Hand-managing a `contenteditable` caret + document model is one of the most bug-prone things in web development, and this codebase has paid for it repeatedly:

- The **cursor-snapback bug** (caret jumps back after repositioning) — a stale cursor offset re-applied by the autosave path. *(Mitigated 2026-05-30 with a live-caret guard in `restoreCursorPosition()`; the root cause is architectural.)*
- The **character-reversal bug** (the `v-safe-html` editing guard exists solely to prevent it).
- **Silent cue-wipe / content-shrink** data-loss incidents (episodes 0272, 0273) — the `safeEmitScriptContent` tripwires exist because the string round-trip silently dropped content.
- **Focus-stealing** on every reactive update (the `isActivelyEditing` / `isRestoringCursor` / `activelyEditingSegment` flag system).

The industry solved structured rich-text editing a decade ago. A real editor framework owns the document model, the selection, and DOM reconciliation — so an **entire class of bugs becomes impossible**, not merely patched. This plan migrates the editable-text surface to **TipTap** (the Vue-friendly wrapper over **ProseMirror**), the standard choice for structured rich text (Notion-class editors).

### Goal posture
This is a **product-quality investment**, not a bug fix. It trades a large one-time effort for the deletion of ~1,500–2,000 lines of fragile band-aid code and a maintainable, salable editor.

---

## 2. What we learned from the codebase (grounding facts)

A full file:line inventory backs every claim here; key facts that shape the plan:

### 2a. The document model is already flat and ordinal — the ideal case
The raw string is a **flat, top-level sequence** of two block kinds: `paragraph` and `cue`. They interleave but **never nest** (a cue is never inside a paragraph; text is never inside a cue). Cue cards are **already separate Vue components** rendered as draggable siblings — *not* embedded inside a single contenteditable. This maps directly to a ProseMirror schema:

```
doc -> (paragraph | cue)+
```

There is **no heading/segment-header node** in the string — rundown structure lives in the database, not in `script_content`. (`cueParser.js`, segment types are only `'text'` and `'cue'`.)

### 2b. The markdown is HTML-in-markdown, not plain markdown
- Paragraphs are `<p class="speaker [bullet]" data-needs-attention data-flag-note>…</p>`. Speaker is the first class token (default `josh`); `bullet` is a co-class; attention flags are `data-*` attrs. Speaker list: `josh, scott, asian-scott, guest, caller, announcer, narrator, host`.
- Cues are HTML-comment-delimited key/value bags:
  ```
  <!-- Begin Cue -->
  [Type: FSQ]
  [AssetID: a1b2c3d4]
  [Slug: quote-…]
  [Quote: "…"]
  [Attribution: …]
  [Duration: 00:00:08]
  <!-- End Cue -->
  ```
- Optional YAML frontmatter is stripped on load and re-prepended on save (`useContentSanitizer.js`). Treat as **out-of-band doc metadata**, not part of the ProseMirror doc.

### 2c. The string contract is the integration boundary to preserve
Every save path funnels through one event: **`emit('update:scriptContent', rawMarkdownString)`** → parent `ContentEditor.updateScriptContent` → `rawMarkdownContent`. The parent is ~9,900 lines of save/reload/undo/remote-sync/Code-Mode machinery that deeply assumes a raw markdown string. **The migration must keep emitting the same serialized markdown string on the same channel** so the parent stays untouched.

### 2d. The band-aid deletion list (~1,500–2,000 lines)
These exist *only* to compensate for contenteditable and become unnecessary with ProseMirror:
`segmentEditBuffer`, `v-safe-html` editing/paste-cooldown guard, `isActivelyEditing`/`activelyEditingSegment`/`isRestoringCursor`/`blockReactiveUpdates` flags, `savedCursorState`+`restoreCursorPosition()`, `handleParagraphBlur` focus-fighting, live-innerHTML `getSegmentContent`, browser-quirk HTML cleanup, double-Enter Range-API split, `execCommand` formatting, paste sanitizers, `_pasteCooldown`, ResizeObserver line-counting, contenteditable auto-resize, mode-switch needle-search caret mapping.

The **integrity tripwires** (`safeEmitScriptContent` cue-loss/corruption/shrink guards) become largely unnecessary too — but we keep an equivalent **assertion on the serializer** (see Risks).

### 2e. Cue types are open-ended, with rich per-type attributes
Insert palette: `IMG, GFX, FSQ, SOT, VO, NAT, PKG, NOTE, BUMP, STING, RIF` plus legacy `DIR` and many renderable extras (`VOX, MUS, LIVE, CG, LOWER, TITLE, …`). Unknown types still render via a generic placeholder — **the schema must allow an open-ended cue type, not a closed enum.** Per-type attribute sets are documented in the cue-type components (e.g. GFX `xpost` is effectively a polymorphic social-post sub-node with ~12 engagement attrs; FSQ strips/re-adds quote marks; SOT/VO carry async-only job state that must stay out of the persisted schema).

---

## 3. Target architecture

```
ContentEditor.vue  (UNCHANGED — still owns rawMarkdownContent, save/reload, Code Mode, undo)
        │  prop: scriptContent (raw markdown string)
        │  event: update:scriptContent (raw markdown string)
        ▼
ScriptEditor.vue   (NEW — thin wrapper, replaces the Script-Mode portion of EditorPanel)
        │  - markdown string  → ProseMirror doc   (parser)
        │  - ProseMirror doc  → markdown string   (serializer)  ← emitted on update:scriptContent
        ▼
   TipTap Editor
        ├─ paragraph node   (attrs: speaker, bullet, needsAttention, flagNote)
        ├─ cue node         (atom block, attrs: type + per-type field bag)  → Vue NodeView
        │       └─ renders existing PlaceholderCueCard / cue-type components unchanged
        └─ (optional) revision mark (inline <rev>)
```

**Key design decisions:**

1. **Keep the markdown string as the persistence contract.** ProseMirror's doc is the in-editor source of truth, but on every change we serialize to the exact legacy markdown (`<p class="…">` + `<!-- Begin/End Cue -->`) and emit it. ContentEditor, the backend, and `host_script_generator` never know the editor changed. This is what makes the migration *incremental and safe* rather than a big-bang rewrite.

2. **Cue cards become ProseMirror atom NodeViews wrapping the existing Vue cue components.** We do **not** rewrite the cue cards — `PlaceholderCueCard.vue` and the `cue-types/*` components are reused as-is inside a `VueNodeViewRenderer`. The cue node is a leaf/atom (non-editable text inside), drag-reorderable via ProseMirror's own selection/drag, which replaces vuedraggable for the script body.

3. **One `cue` node with a free-form `attrs.fields` map + `attrs.type`,** rather than one node type per cue type. Rationale: the cue type list is open-ended and fields vary loosely; a single node with a typed `type` + a `fields` object preserves every attribute losslessly and renders via the existing per-type dispatch. (Per-type nodes are cleaner in theory but require enumerating every field and still need an unknown-type fallback — not worth it.)

4. **Paragraph attrs carry speaker/bullet/flags.** The serializer reproduces the exact `<p class="speaker[ bullet]" data-needs-attention data-flag-note>` form. The serializer must **never** emit `class="undefined"` or `>undefined<` (the existing loss guards literally regex for these).

5. **Code Mode is unchanged** — it stays a `<v-textarea>` over the same raw string. Mode-switch caret mapping becomes a position-map between the ProseMirror doc and the raw-string textarea (far simpler than today's needle-search, but still needs a small mapping helper).

---

## 4. Phased execution

Each phase is independently shippable and reversible behind a feature flag (`useProseMirrorEditor`), so we never have a long-lived broken branch.

### Phase 0 — Spike & schema proof (≈2–3 days)
- Add TipTap deps (`@tiptap/core`, `@tiptap/vue-3`, `@tiptap/starter-kit` or hand-built schema, `@tiptap/pm`).
- Write the **schema** (`paragraph` + `cue` atom node) and a **standalone round-trip harness**: `markdown → doc → markdown` over a corpus of real episode `script_content` values (pull a dozen from the DB, include 0272/0273 and an `xpost` GFX). **Acceptance: byte-identical or semantically-identical round-trip** (normalize attribute order/whitespace; never lose a cue field). This de-risks the entire migration before any UI work.

### Phase 1 — Markdown ↔ ProseMirror parser/serializer (≈3–5 days)
- Port `cueParser.parseContent` → ProseMirror parser, `cueParser.reconstructContent`/`formatCueToMarkdown` → ProseMirror serializer. Preserve every quirk: quote strip/re-add (FSQ), `style`→`alignment` alias, casing normalization, `data-*` flags, frontmatter re-attach, field ordering.
- Keep a **serializer loss-assertion** (cue count + no-`undefined` + no field dropped) — the spiritual successor to `safeEmitScriptContent`, but now guarding a structured→string transform instead of a string→string one.
- Unit-test against the Phase 0 corpus in CI.

### Phase 2 — Cue NodeViews (≈4–6 days)
- Wrap `PlaceholderCueCard.vue` + `cue-types/*` in a TipTap `VueNodeViewRenderer`. Cue node is an atom; its Vue component receives `node.attrs` and emits attr updates back through the NodeView.
- Preserve the cue event surface (`insert-cue`, `relocate-cue`, `edit-*-cue`, `sot-job-complete`, `asset-drop`) by mapping them onto ProseMirror transactions.
- Async job state (SOT/VO `jobStatus`, thumbnails, transcription) stays in a **side store keyed by `assetId`**, not in node attrs — only persisted fields live in the schema.

### Phase 3 — Paragraph editing + behaviors (≈4–6 days)
- Speaker assignment, bullet toggle, attention-flag UI as paragraph-attr commands.
- Revision markup (`<rev>`, Alt+/, Alt+.) as a ProseMirror **mark** + plugin (replaces the inline-HTML-stripped approach).
- Keyboard shortcuts (bold/italic/underline → real marks, not `execCommand`; Enter/double-Enter → native block split). Update `keyboardShortcuts.js` + `KEYBOARD_SHORTCUTS.md` per the CLAUDE.md rule.

### Phase 4 — Wire into ContentEditor behind a flag (≈3–4 days)
- New `ScriptEditor.vue` mounts when `useProseMirrorEditor` flag is on; old EditorPanel script path stays as fallback.
- Re-expose the parent's reach-in contract: `flushPendingChanges()`, `isActivelyEditing` (a ProseMirror editor still has a "focused/transacting" state), and an insertion-index accessor for cue insertion. Keep emitting `update:scriptContent` (serialized markdown) and `save-current`/`save-all`.
- Preserve the **LLM-generated-field highlighting** and **generation-history** patterns where they intersect the editor (these are mostly MetadataPanel-side and unaffected, but verify).

### Phase 5 — Soak, parity QA, delete band-aids (≈1 week)
- Run both editors in parallel (flag per-user) on real episodes. Diff saved `script_content` between old and new editor for the same edits — must be identical.
- Once parity holds, flip the default, then **delete the contenteditable band-aids** (§2d) and the now-dead `vuedraggable` script-body path. This is where the ~1,500–2,000-line reduction lands.

**Rough total:** ~5–7 focused weeks of one engineer, dominated by Phases 1–3 (the cue round-trip and NodeViews). Phase 0 is the gate — if the round-trip can't be made lossless, stop and reassess before sinking UI effort.

---

## 5. Risks & mitigations

| Risk | Mitigation |
|---|---|
| **Lossy markdown round-trip** (the core data-integrity risk; episodes 0272/0273 history) | Phase 0 round-trip harness over real corpus is a hard gate; serializer loss-assertion kept in production; both-editors parity diff in Phase 5. |
| **Cue type/field drift** (open-ended types, mixed casing, legacy aliases) | Single `cue` node with free-form `fields` map preserves unknowns; casing normalized on import; aliases handled in serializer; unknown-type generic render preserved. |
| **Parent coupling** (~9,900-line ContentEditor reaches into `$refs.editorPanel`) | Keep the exact prop/event/method contract (`update:scriptContent` string, `flushPendingChanges`, `isActivelyEditing`); parent stays untouched. |
| **Big-bang regression** | Feature flag + parallel run + per-phase shippability; old path remains fallback until parity proven. |
| **GFX `xpost` polymorphism / rich sub-data** | Modeled as cue `fields` sub-object; existing `GfxCueContent.vue` xpost render path reused via NodeView. |
| **Scope creep into the 9,900-line parent** | Explicit non-goal: this migration replaces ONLY the editable-text surface. Save/reload/undo/remote-sync/Code-Mode stay as-is. |

### Non-goals
- Not changing the DB schema or `script_content` format.
- Not touching the backend, `host_script_generator`, or cue-asset processing.
- Not rewriting cue card components (reused inside NodeViews).
- Not replacing Code Mode or the scratch pad.

---

## 6. Decision needed before Phase 0
- **Framework confirm:** TipTap (recommended, Vue-native) vs. raw ProseMirror. TipTap unless we hit a wall its abstraction hides.
- **Go/no-go gate:** Phase 0 lossless round-trip over real episodes. Everything downstream depends on it.

---

## 7. Documentation impact

The migration touches a cluster of editor docs. **Timing principle:** every doc
below is accurate for *today's* code and must stay live until the migration's
flag flips (Phase 4/5). The only safe immediate action is forward-looking
deprecation banners (done — see "Banners applied now" column). The actual
deletes/rewrites happen when Phase 5 lands.

| Doc | Class | Banner applied now | Phase 5 action |
|---|---|---|---|
| `SCRIPT_MODE_KEYBOARD_HANDLING.md` | **DELETE** | ✅ | Delete — entire doc is the contenteditable keyboard band-aid system; UX captured in KEYBOARD_SHORTCUTS + SAVE_RELOAD_SPEC. |
| `CUE_INSERTION_CURSOR_SNAPSHOT_PATTERN.md` | **DELETE** | ✅ | Delete — snapshot pattern only exists because contenteditable loses focus to modals; replaced by Phase-4 insertion-index accessor. |
| `EDITOR_PANEL_ARCHITECTURE.md` | **REWRITE** | ✅ | Keep the "two views of one string" + persistence-chain thesis; rewrite the Edit-Buffer / reactivity-guard / `scriptSegments`-cache sections; add `ScriptEditor.vue` + PM schema/serializer to Key Files. |
| `CLAUDE.md` (editor sections) | **REWRITE** | — (project file; note in plan) | Rewrite "Critical Design Rule" (the `isActivelyEditing` focus rule disappears), the "Save Ownership" Script-typing row, and "Edit Buffer System" (`segmentEditBuffer` rationale gone; `flushPendingChanges()` survives as a contract method). Preserve MetadataPanel-highlighting, LLM generation-history, Data-Storage sections. |
| `SAVE_RELOAD_SPEC.md` | **MINOR** | ✅ | Behavior preserved; update only the named-mechanism notes (edit buffer, per-segment debounce, double-Enter Range-API, non-reactive `hasUnsavedChanges` rationale). |
| `CUE_BLOCK_INSERTION_PROTOCOL.md` | **MINOR** | — | UX protocol survives; note that #10/#11 (between- and within-paragraph insertion) plumbing becomes ProseMirror transactions/positions. |
| `CUE_DATA_LOSS_AND_UNDO_FOLLOW_UPS.md` | **MINOR** | ✅ | §5 tripwire item superseded by serializer loss-assertion; §4 + verification checklists re-expressed against PM editor. |
| `CODEBASE_NAVIGATION_INDEX.md` | **MINOR** | — | Update Layer 0 hot-spots ("cursor loss" largely gone), add `ScriptEditor.vue`, note `cueParser.js` logic moved into PM parser/serializer. |
| `KEYBOARD_SHORTCUTS.md` | **MINOR** | — | Mandated by Phase 3: update Script/Code Editor impl refs (marks not `execCommand`, native block ops); chords themselves unchanged. Keep `keyboardShortcuts.js` in sync. |
| `SCRIPT_AND_CUE_ARCHITECTURE.md` | **UNAFFECTED** | — | Cue data model + markdown format preserved. (Pre-existing staleness unrelated to migration.) |
| `DEBUGGING_STANDARDS.md` | **UNAFFECTED** | — | Generic Vue/API debugging; its EditorPanel ref is Code-Mode Vuetify, which stays. |
| `VUE_DRAGGABLE_IMPLEMENTATION.md` | **UNAFFECTED** | — | Covers rundown-list DnD, not the script body. Only the script-body draggable path is removed. |
| `rehydrate.md` | **UNAFFECTED** | — | Already-obsolete July-2025 snapshot; orthogonal to this migration. |
| `INDEX.md` | **UNAFFECTED** | — | Never links the DELETE-class docs; no edit needed when they're removed. |

---

## Appendix — Authoritative source files
- `src/utils/cueParser.js` — current parser/serializer; the schema authority for Phases 0–1.
- `src/composables/useScriptCore.js` — segment state + `safeEmitScriptContent` loss guards (the behavior the serializer assertion must replicate).
- `src/composables/useContentSanitizer.js` — `stripYamlFrontmatter` (frontmatter handling).
- `src/components/content-editor/EditorPanel.vue` — current contenteditable surface (`:310–737` block interleaving), `cueDefinitions` (`:1989`), `generateCueBlock` (`:6648`), the band-aid set to delete.
- `src/components/content-editor/cards/PlaceholderCueCard.vue` + `cards/cue-types/*` — cue render components to reuse in NodeViews.
- `src/components/content-editor/modals/CueModal.vue` — per-type creation field sets.
- `ContentEditor.vue` — the parent whose string contract must be preserved.
