# EditorPanel Architecture: Script Mode & Code Mode

> ⚠️ **PARTIALLY SUPERSEDED — rewrite pending.** The core thesis below
> ("two views of one string," the `update:scriptContent` → `rawMarkdownContent`
> persistence chain, the preserved markdown/cue-block format) **survives** the
> planned migration. But the *inner mechanism* — `segmentEditBuffer`, the 1.5s
> per-segment debounce, the `isActivelyEditing`/`activelyEditingSegment`/
> `isRestoringCursor` edit-buffer guard flags, and the `scriptSegments` parse
> cache — is being replaced by a TipTap/ProseMirror document model. Treat the
> "Edit Buffer" and reactivity-guard sections as **legacy** once the migration
> ships; the string-contract and Code-Mode sections stay valid. See
> [`SCRIPT_EDITOR_MIGRATION_PLAN.md`](SCRIPT_EDITOR_MIGRATION_PLAN.md).
> **Accurate for the current code until Phase 4/5 lands.**

## The #1 Thing to Understand

**Script Mode and Code Mode are two views of the same string.**

There is exactly one source of truth: a raw markdown string called `scriptContent`. Code Mode edits it directly via a `<v-textarea>`. Script Mode parses it into visual segments (paragraphs, cue cards), lets the user edit those visually, then **reconstructs the raw markdown string** and writes it back.

Every edit in Script Mode ultimately becomes a string mutation on the same data that Code Mode displays. The user sees paragraphs, speakers, and styled cue cards — but under the hood, every keystroke serializes back to raw markdown.

```
┌─────────────────────────────────────────────────────────────────┐
│                    ContentEditor.vue                            │
│                                                                 │
│   rawMarkdownContent  ←──  single source of truth (data prop)  │
│         │                                                       │
│         ▼                                                       │
│   scriptContent (computed) ── passed as prop to EditorPanel     │
│         │                                                       │
│         │  @update:script-content="updateScriptContent"         │
│         │       ▲                                               │
│         │       │  (writes back to rawMarkdownContent)          │
└─────────┼───────┼───────────────────────────────────────────────┘
          │       │
          ▼       │
┌─────────────────┼──────────────────────────────────────────────┐
│         EditorPanel.vue                                        │
│                 │                                              │
│   rawScriptContent (computed get/set)                          │
│     get() → returns scriptContent prop                         │
│     set() → emits 'update:scriptContent' to parent             │
│                 │                                              │
│    ┌────────────┴────────────┐                                 │
│    │                         │                                 │
│    ▼                         ▼                                 │
│  CODE MODE               SCRIPT MODE                          │
│  ┌──────────┐           ┌──────────────────────┐              │
│  │v-textarea│           │ CueParser.parseContent│              │
│  │ v-model= │           │        │              │              │
│  │rawScript │           │        ▼              │              │
│  │Content   │           │  scriptSegments[]     │              │
│  └──────────┘           │  (text + cue array)   │              │
│    │                    │        │              │              │
│    │ direct             │  user edits segment   │              │
│    │ two-way            │        │              │              │
│    │ binding            │        ▼              │              │
│    │                    │  segmentEditBuffer     │              │
│    │                    │  (debounced 1.5s)      │              │
│    │                    │        │              │              │
│    │                    │        ▼              │              │
│    │                    │  reconstructRawContent │              │
│    │                    │        │              │              │
│    │                    └────────┼──────────────┘              │
│    │                             │                             │
│    └──────────┬──────────────────┘                             │
│               ▼                                                │
│     $emit('update:scriptContent', newValue)                    │
│               │                                                │
└───────────────┼────────────────────────────────────────────────┘
                │
                ▼
        ContentEditor receives event
        → sets rawMarkdownContent = newValue
        → marks hasUnsavedChanges = true
```

## The Parse/Reconstruct Cycle (Script Mode)

Script Mode does NOT store its own copy of the content. It works by:

1. **Parse**: `CueParser.parseContent(rawMarkdownContent)` splits the raw markdown into an array of typed segments:
   - `{ type: 'text', content: '...', speaker: 'josh', needsParagraphTags: true }`
   - `{ type: 'cue', data: { cueType: 'SOT', ... } }`

2. **Display**: Each segment renders as a visual element — text paragraphs become editable `<textarea>` or contenteditable divs with speaker labels; cues become styled cards.

3. **Edit**: When the user types in a paragraph, `updateTextSegment(index, newContent)` stores the change in `segmentEditBuffer[index]`.

4. **Reconstruct**: After a 1.5-second debounce (or on flush), `reconstructRawContent(segments)` calls `CueParser.reconstructContent(segments)` to rebuild the full raw markdown string from all segments.

5. **Emit**: The reconstructed string is emitted via `$emit('update:scriptContent', newRawContent)`, which flows back up to ContentEditor and overwrites `rawMarkdownContent`.

**The cycle**: Raw string → parse → visual segments → user edits → reconstruct → raw string

## Key Files

| File | Role |
|------|------|
| `ContentEditor.vue` | Parent. Owns `rawMarkdownContent`. Passes it as `:script-content` prop. Receives updates via `@update:script-content`. |
| `EditorPanel.vue` | Child. `rawScriptContent` computed wraps the prop. Houses both Script and Code mode views. |
| `src/utils/cueParser.js` | Stateless parser. `CueParser.parseContent()` splits raw markdown into segments. `CueParser.reconstructContent()` joins segments back into raw markdown. |

## Code Mode: Direct Binding

Code Mode is straightforward — a `<v-textarea>` with `v-model="rawScriptContent"`:

```vue
<!-- EditorPanel.vue line ~1403 -->
<v-textarea
  v-model="rawScriptContent"
  placeholder="Edit the script content in markdown format..."
  variant="plain"
  class="code-textarea flex-grow-1"
  style="font-family: 'Roboto Mono', monospace;"
/>
```

Every keystroke directly triggers the `rawScriptContent` setter, which emits to the parent. No parsing, no reconstruction — just raw string editing.

## Script Mode: The Visual Layer

Script Mode parses `rawScriptContent` into `scriptSegments` (a computed property) and renders each segment as a visual element. The computed property uses caching and a `segmentReparseKey` to control re-parsing:

```javascript
// EditorPanel.vue computed
scriptSegments: {
  get() {
    const _reparseKey = this.segmentReparseKey; // Vue dependency trigger
    if (!this.rawScriptContent || this.editorMode !== 'script') return [];

    // Cache check — only re-parse if content actually changed
    const currentContent = this.rawScriptContent;
    if (this.lastParsedContent === currentContent && this.cachedScriptSegments !== null) {
      return this.cachedScriptSegments;
    }

    // Parse via CueParser
    const contentWithoutFrontmatter = this.stripYamlFrontmatter(currentContent);
    const segments = CueParser.parseContent(contentWithoutFrontmatter);
    this.cachedScriptSegments = segments;
    this.lastParsedContent = currentContent;
    return segments;
  }
}
```

## The Edit Buffer (Preventing Reactivity Races)

When the user types in Script Mode, the edit goes into a **buffer** rather than immediately triggering a full parse/reconstruct cycle. This prevents Vue's reactivity from overwriting the user's cursor position and content mid-keystroke.

```
User types in paragraph #3
        │
        ▼
segmentEditBuffer[3] = "new text"     ← immediate
        │
        ▼ (after 1.5 second debounce)
segments = [...scriptSegments]
segments[3].content = segmentEditBuffer[3]
newRawContent = reconstructRawContent(segments)
$emit('update:scriptContent', newRawContent)  ← writes back to raw string
```

**Guard flags** during active editing:
- `isActivelyEditing` — blocks Vue watchers from triggering disruptive re-renders
- `activelyEditingSegment` — tracks which segment the user is typing in
- `isRestoringCursor` — blocks watchers during the emit/re-render cycle

These flags are set on input and cleared on blur or after the debounce fires.

## Cue Insertion Flow (Both Modes)

All cue insertion methods (SOT, VO, IMG, FSQ, GFX, NAT, RIF, PKG, NOTE, BUMP, STING) follow the same pattern but branch on `editorMode`:

**In Code Mode**: Insert the cue markdown text at the textarea cursor position.

**In Script Mode**:
1. Snapshot the focused paragraph index at button-press time
2. Parse current segments
3. Splice the new cue segment into the array at the correct position
4. Call `reconstructRawContent(segments)` to rebuild the raw string
5. Emit the updated string to the parent

In both cases, the end result is the same: the raw markdown string gets a new cue block inserted.

## Mode Switching

Switching between Script and Code mode is seamless because both read from the same `rawScriptContent`:

- **Script → Code**: The raw string is already up to date (flush any pending edits first via `flushPendingChanges()`), so Code Mode's textarea just displays it.
- **Code → Script**: `scriptSegments` re-parses the raw string into visual segments.

The parent ContentEditor manages the `editorMode` state and passes it as a prop.

## Persistence Chain

```
EditorPanel edit
    → $emit('update:scriptContent', newValue)
        → ContentEditor.updateScriptContent(newValue)
            → this.rawMarkdownContent = newValue
            → this.hasUnsavedChanges = true
                → User clicks Save (or autosave triggers)
                    → API call: PUT /rundown/{episode}/item/{id}
                        → { script_content: rawMarkdownContent }
                            → PostgreSQL rundown_items.script_content
```

The database column `script_content` stores the raw markdown. Script Mode's visual representation is never persisted — it's always generated on-the-fly by parsing the raw string.

## Common Misconceptions

| Misconception | Reality |
|---|---|
| Script Mode has its own data store | No. It's a computed view of `rawScriptContent`. |
| Edits in Script Mode go to a different place than Code Mode | No. Both write to the same `rawScriptContent` → parent's `rawMarkdownContent`. |
| Cue cards are separate objects in the database | No. Cues are `<!-- Begin Cue -->...<!-- End Cue -->` blocks within the raw markdown string. `CueParser` extracts them for display and re-embeds them on save. |
| Switching modes requires a save | No. Both modes read the same live string. A `flushPendingChanges()` call ensures any buffered Script Mode edits are written before the switch. |

## Related Documentation

- [`SCRIPT_MODE_KEYBOARD_HANDLING.md`](SCRIPT_MODE_KEYBOARD_HANDLING.md) — Keyboard event handling, autosave, cursor preservation
- [`CUE_BLOCK_INSERTION_PROTOCOL.md`](CUE_BLOCK_INSERTION_PROTOCOL.md) — Cue insertion workflow details
- [`CUE_INSERTION_CURSOR_SNAPSHOT_PATTERN.md`](CUE_INSERTION_CURSOR_SNAPSHOT_PATTERN.md) — Snapshotting cursor position for precise insertion
- [`DEBUGGING_STANDARDS.md`](DEBUGGING_STANDARDS.md) — Debugging Script Mode issues
- [`LLM_GENERATOR_TROUBLESHOOTING.md`](LLM_GENERATOR_TROUBLESHOOTING.md) — LLM-generated content and Script Mode display
