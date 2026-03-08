# How Save & Reload Is Supposed to Work

**Plain English. Every operation. No code.**

This document describes the *intended* behavior of the ContentEditor save/reload system from the user's perspective and from the system's perspective. It serves as the authoritative spec for the refactored implementation.

---

## The Big Picture

The editor is two views of the same string. **Code Mode** shows raw markdown. **Script Mode** parses that markdown into visual paragraphs and cue cards. Every edit in Script Mode reconstructs the markdown string. Every edit in Code Mode is direct. Either way, there's one string, one source of truth.

The system's job: **never lose the user's work, never interrupt their typing, and keep the database current.**

---

## Editor States

At any moment, the editor is in exactly ONE of these states:

| State | Meaning |
|-------|---------|
| **IDLE** | User is not typing. No pending saves. Editor is ready. |
| **EDITING** | User is actively typing in a paragraph. Edits are buffered. |
| **SAVING** | A save operation is in flight to the API. |
| **LOADING** | New content is being loaded from the API (item switch, episode load). |
| **FLUSHING** | Buffered edits are being applied before a transition (item switch, mode switch, manual save). |

Rules:
- Only one state at a time. No combinations.
- State transitions are explicit. No implicit state from multiple boolean flags.
- Every operation checks the current state before proceeding.

---

## Operation: User Types in a Paragraph (Script Mode)

### What the user does
Types characters into a paragraph in Script Mode.

### What should happen visually
- Characters appear instantly with no lag or flicker.
- Cursor stays exactly where the user put it.
- No re-renders, no focus loss, no content replacement.

### What happens to the data
1. The typed content goes into an **edit buffer** for that paragraph's index. This is NOT reactive — Vue doesn't know about it, so it can't trigger re-renders.
2. A per-paragraph debounce timer starts (1.5 seconds).
3. If the user keeps typing, the timer resets. Content accumulates in the buffer.
4. When the user pauses for 1.5 seconds:
   a. The buffer content is applied to the paragraph's segment.
   b. All segments are reconstructed into the raw markdown string.
   c. The raw string is sent to the parent (ContentEditor) via emit.
   d. A save request fires to the API.
   e. On success: a brief visual flash (CSS animation, no re-render) confirms the save.
   f. Cursor position is preserved throughout.

### What should NOT happen
- ContentEditor should NOT run its own separate autosave timer on this change. The save already happened.
- No reactive state mutation (`hasUnsavedChanges`, `saving`, etc.) should trigger Vue to re-render the editor area during typing.
- No watcher should fire that could overwrite the edit buffer.

---

## Operation: User Types in Code Mode

### What the user does
Types directly into the raw markdown textarea.

### What should happen
1. The textarea updates via v-model (standard Vue two-way binding).
2. The raw markdown string updates in ContentEditor.
3. A single debounce timer (1.5 seconds) starts.
4. When the user pauses: save to API.

### Key difference from Script Mode
Code Mode doesn't need an edit buffer — the textarea IS the buffer. Vue's v-model handles it natively. But the save debounce should be the SAME timer, not a separate one.

---

## Operation: User Clicks Away from a Paragraph (Blur)

### What the user does
Clicks on a different paragraph, clicks on the rundown panel, or otherwise moves focus away from the current paragraph.

### What should happen
1. If there's a pending debounce timer for that paragraph: cancel it.
2. Apply the buffered content immediately (don't wait for the timer).
3. Reconstruct the raw markdown string.
4. Save to API immediately.
5. Transition state from EDITING to SAVING, then to IDLE.

### What should NOT happen
- If the blur was caused by an autosave re-render (programmatic blur), the paragraph should re-focus. The user didn't intend to leave.
- If the blur target is within the same editor (clicking another paragraph), the save should complete but not block the new paragraph from receiving focus.

---

## Operation: User Presses Ctrl+S (Manual Save All)

### What the user does
Presses Ctrl+S or clicks the "Save All" button.

### What should happen
1. **Flush**: Apply all pending edit buffers immediately.
2. **Save everything**: Episode metadata + all rundown items in a single API call.
3. Visual confirmation (success notification).
4. Mark all content as saved.

### Why this is different from autosave
Autosave saves ONE item (the currently selected rundown item). Manual save saves EVERYTHING — all items, all metadata, episode info. It's a full checkpoint.

---

## Operation: User Switches Rundown Items

### What the user does
Clicks a different item in the rundown panel.

### What should happen
1. **Flush**: Apply all pending edit buffers for the current item.
2. **Save**: Save the current item to the API (if there are unsaved changes).
3. **Wait**: Don't load the new item until the save completes.
4. **Load**: Fetch the new item's content from the API (or use cached rundown data).
5. **Parse**: Set the raw markdown string, which causes Script Mode to re-parse into segments.
6. **Display**: Show the new item's content in the editor.
7. **Reset state**: Clear all edit buffers, clear editing flags, set state to IDLE.

### What should NOT happen
- The autosave watcher should NOT fire when the new content is loaded (it's not a user edit, it's a load).
- No "save the content we just loaded" loop.

---

## Operation: User Switches Between Script and Code Mode

### What the user does
Clicks the Script or Code mode button.

### What should happen
1. **Flush**: Apply all pending edit buffers.
2. **Switch view**: Change the rendering mode. Both modes read the same raw string, so no data transformation is needed.

### What should NOT happen
- No save required (the content hasn't changed, just the view).
- No re-parse required for Code Mode (it just shows the raw string).
- Script Mode will re-parse on display (that's fine, it's a computed property).

---

## Operation: User Loads an Episode

### What the user does
Selects a different episode from the episode picker.

### What should happen
1. **Save current**: If there are unsaved changes, save the current item.
2. **Clear state**: Reset all editor state (edit buffers, editing flags, selected item).
3. **Fetch**: Load episode info + rundown items from API.
4. **Display**: Populate the rundown panel with items.
5. **Auto-select**: Select the first item (or restore the previously selected item from session storage).
6. **Load content**: Load the selected item's content into the editor.

---

## Operation: Remote Sync (Multi-User)

### What should happen (background, no user action required)
1. After 15 seconds of user inactivity (no typing), fetch the current item from the server.
2. Compare remote content with local content.
3. If they match: do nothing.
4. If they differ AND the user is NOT editing: silently update the local content.
5. If they differ AND the user IS editing: stash the remote content. Apply it when the user finishes editing (on blur).

### Why this exists
Another user might be editing the same item. The 15-second sync picks up their changes without interrupting the current user's work.

---

## Operation: Create New Paragraph (Double Enter)

### What the user does
Presses Enter twice at the end of a paragraph.

### What should happen
1. Detect the double-enter pattern (content ends with newline, cursor at end).
2. Remove the trailing newline from the current paragraph.
3. Create a new empty paragraph after the current one.
4. The new paragraph inherits the current paragraph's speaker.
5. Focus moves to the new paragraph automatically.
6. The raw markdown is reconstructed with the new `<p>` tag.
7. Autosave fires normally (after 1.5s debounce).

---

## Operation: Merge Paragraphs (Backspace/Delete)

### What the user does
- Presses Backspace at the beginning of an empty paragraph, OR
- Presses Delete at the end of a paragraph.

### What should happen
1. Combine the content of the two adjacent paragraphs.
2. Remove the now-empty paragraph from the segment array.
3. Reconstruct the raw markdown.
4. Place cursor at the merge point.
5. Autosave fires normally.

---

## Operation: Insert a Cue Block

### What the user does
Presses a cue button (or keyboard shortcut like Alt+V for VO), fills out the modal, confirms placement.

### What should happen
1. Record the current cursor/paragraph position (snapshot).
2. Open the cue modal with themed colors.
3. User fills in fields, presses Shift+Enter or Submit.
4. Modal closes.
5. Placement overlay appears — user selects where the cue goes.
6. Cue markdown block is inserted at the selected position.
7. Raw markdown is reconstructed.
8. Save fires (this is a structural change, should save promptly).

---

## Operation: Edit/Delete a Cue Block

### What the user does
Clicks edit or delete on a cue card.

### What should happen
- **Edit**: Opens modal pre-populated with current cue data. On submit, updates the cue block in the markdown and saves.
- **Delete**: Removes the cue block from the segment array, reconstructs markdown, saves.

---

## Operation: Drag-Reorder Paragraphs or Cues

### What the user does
Drags a paragraph or cue card to a new position in Script Mode.

### What should happen
1. The segment array is reordered.
2. Raw markdown is reconstructed with new order.
3. Save fires.

---

## Operation: Change Paragraph Speaker

### What the user does
Clicks the speaker label on a paragraph, selects a new speaker.

### What should happen
1. The segment's `speaker` field is updated.
2. The paragraph's visual styling changes to the new speaker's color.
3. Raw markdown is reconstructed (speaker is part of the markdown format).
4. Save fires.

---

## Operation: Format Text (Bold/Italic/Underline/Highlight)

### What the user does
Selects text and presses Ctrl+B, Ctrl+I, Ctrl+U, or Ctrl+Alt+H.

### What should happen
1. The selected text is wrapped in the appropriate HTML tags.
2. The edit buffer is updated with the formatted content.
3. Normal autosave debounce applies.

---

## Operation: Before Unmount (Page Navigation/Close)

### What should happen automatically
1. Flush all pending edit buffers.
2. Save the current item if there are unsaved changes.
3. Release any segment locks.
4. Clear all timers.

---

## The Persistence Chain (How Data Gets Saved)

There is ONE path from user edit to database:

```
User types
  -> Edit buffer (non-reactive, per-paragraph)
  -> 1.5s debounce (or immediate on blur/flush)
  -> reconstructRawContent() builds markdown string
  -> emit to ContentEditor (sets rawMarkdownContent)
  -> API call: PUT /api/episodes/{id}/save-rundown
  -> Database: rundown_items.script_content
  -> Revision history snapshot
```

There is NOT:
- A second watcher-based save path
- A "silent" save path
- A separate Code Mode save path (same debounce, same API call)

---

## The Loading Chain (How Data Gets Loaded)

```
User selects item (or episode loads)
  -> State = LOADING
  -> API call: GET /api/episodes/{id}/rundown (or cached)
  -> Set rawMarkdownContent = item.script_content
  -> Script Mode re-parses into segments (computed)
  -> Clear edit buffers
  -> State = IDLE
```

During LOADING state:
- No autosave fires
- No watchers trigger saves
- No edit buffers are populated

---

## Dirty Tracking

`hasUnsavedChanges` should be tracked WITHOUT triggering Vue re-renders of the editor. Options:
- Use a plain JavaScript variable (not `ref()` or reactive `data()`)
- Use `markRaw()` on the tracking object
- Check buffer state directly instead of maintaining a separate flag

The flag is read by:
- The "unsaved changes" indicator in the UI
- The "save before switching" confirmation dialog
- The beforeUnmount handler

It does NOT need to trigger re-renders of the editor content area.

---

## Revision History

Every save (auto or manual) creates a revision entry:
- Content hash (SHA256) for dedup — don't create duplicate versions
- Timestamp
- Save type (autosave vs manual)
- Pre-restore snapshots before any rollback

This is handled entirely by the backend. The frontend just sends `save_type: 'autosave'` or `save_type: 'manual'` with the save request.

---

## What We're Removing

| Thing | Why It Existed | Why We're Removing It |
|-------|---------------|----------------------|
| ContentEditor's 500ms rawMarkdownContent watcher autosave | Caught non-typing content changes | EditorPanel's save-current emit already covers this. Non-typing changes (cue insertion, metadata) can trigger save directly. |
| `saveCurrentItemSilent()` | Prevented focus theft during autosave | Root cause was reactive state mutation. Fix: make `hasUnsavedChanges` non-reactive. |
| Multiple boolean guard flags | Prevented race conditions between dual save paths | With single save path, most guards unnecessary. One state enum replaces all. |
| ContentEditor reaching into EditorPanel's `isActivelyEditing` flag | Needed to decide which save path to use | With single save path, parent doesn't need to know child's editing state. |

---

## What We're Keeping

| Thing | Why |
|-------|-----|
| Edit buffer (`segmentEditBuffer`) | Essential for preventing cursor/keystroke loss during typing |
| Per-segment debounce timers | Prevents cross-paragraph interference |
| `flushPendingChanges()` | Still needed before item switch, mode switch, manual save |
| Remote sync (15s timer) | Multi-user support, correct design |
| Corruption guards (min content check) | Prevents destructive saves |
| Revision history | Aggressive history capture is intentional |
| Blur-triggered immediate save | Critical UX — save when user leaves paragraph |
| Before-unmount save | Last-ditch data preservation |

---

*This document is the spec. If the code doesn't match this document, the code is wrong.*
