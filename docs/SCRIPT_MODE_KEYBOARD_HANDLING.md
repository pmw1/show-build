# Script Mode Keyboard Event Handling

> ⚠️ **SUPERSEDED — slated for deletion.** This document describes the legacy
> hand-rolled `contenteditable` Script Mode (custom Enter/Backspace Range-API
> handling, `segmentEditBuffer`, the `isActivelyEditing` guard, focus-retry,
> "spaces disappear while typing" workarounds). The Script editor is migrating
> to TipTap/ProseMirror, where the framework owns block-split/join and the
> caret, so this entire mechanism ceases to exist. See
> [`SCRIPT_EDITOR_MIGRATION_PLAN.md`](SCRIPT_EDITOR_MIGRATION_PLAN.md).
> **Accurate for the current code until the migration's Phase 5 lands; it will
> be deleted then.**

## Overview

Script Mode in EditorPanel.vue uses custom keyboard event handling to provide a natural writing experience while maintaining synchronization between Script Mode (visual editing) and Code Mode (markdown).

## Key Features

### 1. Triple Enter Creates New Paragraph

**User Experience**: Press Enter three times to create a new `<p>` paragraph

**Implementation**: `EditorPanel.vue:2188-2245`

```javascript
handleTextareaKeydown(segmentIndex, event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    const textarea = event.target;
    const currentContent = textarea.value;
    const cursorPos = textarea.selectionStart;

    // Check if we're at the end and if content already ends with newline
    const atEnd = cursorPos === currentContent.length;
    const contentEndsWithNewline = currentContent.endsWith('\n');

    if (atEnd && contentEndsWithNewline) {
      // Double Enter detected - create new paragraph
      event.preventDefault();

      // Remove trailing newline from current segment
      const cleanedContent = currentContent.replace(/\n$/, '');
      this.updateTextSegment(segmentIndex, cleanedContent);

      // Create new paragraph in Code mode (new <p> tag)
      this.createNewParagraphAfter(segmentIndex);
    }
  }
}
```

**Behavior**:
1. First Enter: Adds newline to current paragraph
2. Second Enter: Content now ends with `\n`, ready for paragraph creation
3. Third Enter: Detects double-newline pattern, creates new `<p>` tag, focuses new paragraph

**Key Details**:
- Only triggers at end of paragraph (`cursorPos === currentContent.length`)
- Uses `preventDefault()` to avoid adding extra newline
- New paragraph inherits speaker from current paragraph
- Automatically focuses new paragraph with retry logic (up to 5 attempts)

### 2. Autosave System with Cursor Preservation

**Problem**: Vue reactivity causes typed content to be overwritten during re-render, and autosave operations can steal focus/cursor position.

**Solution**: Multi-layer protection system (`EditorPanel.vue:3670-3735`)

#### 2.1 Edit Buffer with 5-Second Debounce

```javascript
updateTextSegment(segmentIndex, newContent) {
  // Store the new content in buffer immediately
  this.segmentEditBuffer[segmentIndex] = newContent;

  // Clear existing timer for this segment
  if (this.updateDebounceTimers[segmentIndex]) {
    clearTimeout(this.updateDebounceTimers[segmentIndex]);
  }

  // Debounce the actual update to prevent race conditions during typing
  this.updateDebounceTimers[segmentIndex] = setTimeout(async () => {
    const segments = [...this.scriptSegments];
    segments[segmentIndex].content = this.segmentEditBuffer[segmentIndex];
    const newRawContent = this.reconstructRawContent(segments);
    this.$emit('update:scriptContent', newRawContent);

    // Clear buffer and timer
    delete this.segmentEditBuffer[segmentIndex];
    delete this.updateDebounceTimers[segmentIndex];

    // Clear editing flags BEFORE persist
    if (this.activelyEditingSegment === segmentIndex) {
      this.activelyEditingSegment = null;
      this.isActivelyEditing = false;
    }

    // Persist to database and show visual feedback
    await this.persistCurrentItemToDatabase(segmentIndex);
  }, 5000); // 5 second debounce - longer to avoid cursor disruption
}
```

#### 2.2 Active Editing Guard (`isActivelyEditing` Flag)

**Purpose**: Prevents Vue watchers from triggering re-renders that would steal cursor/focus during active typing.

**Data Property**:
```javascript
data() {
  return {
    activelyEditingSegment: null, // Which segment is being typed in
    isActivelyEditing: false,     // Master flag to block watchers
  }
}
```

**Set on input**:
```javascript
handleContentEditableInput(index, event) {
  this.activelyEditingSegment = index;
  this.isActivelyEditing = true; // Block watchers during active editing
  // ...
}
```

**Cleared on blur or after debounce save**:
```javascript
handleParagraphBlur(index) {
  this.activelyEditingSegment = null;
  this.isActivelyEditing = false; // Re-enable watchers
}
```

**Watcher guard**:
```javascript
scriptContent: {
  handler(newVal, oldVal) {
    // CRITICAL GUARD: Skip disruptive operations while user is actively editing
    if (this.isActivelyEditing) {
      console.log('Skipping scriptContent watcher - user is actively editing');
      return;
    }
    // ... rest of handler
  }
}
```

#### 2.3 CSS Animation-Based Flash (Non-Reactive)

**Problem**: The old `flashParagraph()` method used reactive state mutations that triggered Vue re-renders, stealing focus.

**Old Approach** (PROBLEMATIC):
```javascript
// BAD: Reactive state mutations cause re-renders
async flashParagraph(index, type, count) {
  for (let i = 0; i < count; i++) {
    this.savedParagraphIndex = index;  // Triggers re-render!
    await sleep(150);
    this.savedParagraphIndex = null;   // Triggers another re-render!
  }
}
```

**New Approach** (CSS Animation):
```javascript
// GOOD: Pure DOM manipulation, no Vue re-renders
async flashParagraph(index, type, count) {
  const element = this.$refs[`textareaRef-${index}`];
  if (element) {
    const paragraphDiv = element.closest('.paragraph-content');
    if (paragraphDiv) {
      const animationClass = type === 'success' ? 'flash-save-animation' : 'flash-error-animation';
      paragraphDiv.classList.add(animationClass);
      setTimeout(() => paragraphDiv.classList.remove(animationClass), 900);
    }
  }
}
```

**CSS Keyframes**:
```css
@keyframes flash-save {
  0%, 100% { background-color: inherit; }
  16.67%, 50%, 83.33% { background-color: rgba(33, 150, 243, 0.4); }
  33.33%, 66.67% { background-color: inherit; }
}

.paragraph-content.flash-save-animation {
  animation: flash-save 0.9s ease-in-out;
}
```

**Key Benefits**:
- No Vue re-renders during flash animation
- Cursor position preserved
- User can continue typing immediately after autosave
- Visual feedback (blue blink) still works

**How The Complete System Works**:
1. User types → `isActivelyEditing = true`, content stored in buffer
2. `getSegmentContent()` returns buffered content (prevents Vue overwrite)
3. Watchers see `isActivelyEditing=true` and skip disruptive operations
4. After 5 seconds of no typing, debounce fires:
   - Reconstructs markdown and emits to parent
   - Clears editing flags
   - Persists to database
   - Triggers CSS animation (blue blink) - no re-render!
5. User can continue typing immediately with cursor intact

**Key Benefits**:
- No lost characters during typing
- Smooth typing experience with preserved cursor
- 5-second debounce gives user time to think without interruption
- Automatic sync to Code Mode after pause
- Per-segment buffer prevents cross-segment interference
- Blue blink visual feedback without focus disruption

### 3. Backspace at Beginning Merges Paragraphs

**Implementation**: `EditorPanel.vue:2219-2229`

```javascript
if (event.key === 'Backspace') {
  const textarea = event.target;
  const content = textarea.value;
  const cursorPos = textarea.selectionStart;

  // If at beginning of empty paragraph, merge with previous paragraph
  if (cursorPos === 0 && content.trim() === '') {
    event.preventDefault();
    this.mergeParagraphWithPrevious(segmentIndex);
  }
}
```

**Behavior**: When at the start of an empty paragraph, Backspace merges it with the previous paragraph

### 4. Delete at End Merges with Next

**Implementation**: `EditorPanel.vue:2232-2241`

```javascript
if (event.key === 'Delete') {
  const textarea = event.target;
  const content = textarea.value;
  const cursorPos = textarea.selectionStart;

  // If at end of paragraph, merge with next paragraph
  if (cursorPos === content.length) {
    setTimeout(() => {
      this.mergeParagraphWithNext(segmentIndex);
    }, 0);
  }
}
```

**Behavior**: When at the end of a paragraph, Delete key merges with the next paragraph

## Data Architecture

### Single Source of Truth

**Prop**: `scriptContent` (from parent ContentEditor.vue)
**Internal**: `rawScriptContent` (computed from `scriptContent`)

```javascript
computed: {
  rawScriptContent: {
    get() {
      return this.scriptContent;
    },
    set(value) {
      this.$emit('update:script-content', value);
    }
  }
}
```

### Segment Parsing

**Computed**: `scriptSegments` (parsed from `rawScriptContent`)

```javascript
scriptSegments() {
  const contentWithoutFrontmatter = this.stripYamlFrontmatter(this.rawScriptContent);
  const segments = CueParser.parseContent(contentWithoutFrontmatter);
  return segments;
}
```

### Edit Buffer Layer

**Data Properties**:
- `segmentEditBuffer: {}` - Stores actively edited content
- `updateDebounceTimers: {}` - Debounce timers for each segment

**Helper Method**:
```javascript
getSegmentContent(segmentIndex) {
  // Return buffered content if it exists (user is actively editing)
  if (this.segmentEditBuffer && this.segmentEditBuffer[segmentIndex] !== undefined) {
    return this.segmentEditBuffer[segmentIndex];
  }

  // Otherwise return parsed content from single source of truth
  const segment = this.scriptSegments[segmentIndex];
  return segment ? segment.content : '';
}
```

## Common Issues

### Issue: Spaces disappearing during typing

**Cause**: Vue reactivity loop overwrites textarea content before user's keystroke completes

**Solution**: Edit buffer system prevents overwrite by serving buffered content to v-model

**Location**: `EditorPanel.vue:2119-2186`

### Issue: Double Enter not creating paragraph

**Cause**: Checking `textarea.value` before the second Enter's newline is added

**Solution**: Check if content already ends with `\n` to detect the second Enter

**Location**: `EditorPanel.vue:2188-2245`

### Issue: New paragraph not focused after creation

**Cause**: Vue hasn't rendered the new paragraph yet when focus is attempted

**Solution**: Retry logic with `$nextTick` and timeout (up to 5 attempts, 50ms apart)

**Location**: `EditorPanel.vue:2267-2293`

## Testing Checklist

- [ ] Space key works without double-press
- [ ] Rapid typing preserves all characters
- [ ] Triple Enter creates new paragraph
- [ ] New paragraph receives focus automatically
- [ ] New paragraph inherits speaker from previous
- [ ] Backspace at beginning merges with previous paragraph
- [ ] Delete at end merges with next paragraph
- [ ] Code Mode updates after 5 second pause
- [ ] Changes sync between Script Mode and Code Mode
- [ ] Cursor stays in place during autosave (blue blink)
- [ ] Blue blink animation appears after 5 seconds of no typing
- [ ] User can continue typing immediately after autosave triggers

## Related Files

- `disaffected-ui/src/components/content-editor/EditorPanel.vue` - Main implementation
- `disaffected-ui/src/utils/cueParser.js` - Content parsing and reconstruction
- `docs/DEBUGGING_CHEAT_SHEET.md` - Quick troubleshooting
- `docs/VUE_TEMPLATE_REF_CONFLICTS.md` - Related reactivity issues

## Performance Considerations

- **5-second debounce**: Longer delay prevents cursor disruption while maintaining reasonable sync time
- **Per-segment timers**: Prevents interference between paragraphs
- **Buffer cleanup**: Timers and buffers are deleted after sync
- **Retry with backoff**: Focus retry uses 50ms delays to avoid tight loops
- **CSS animations**: Flash effects use CSS keyframes instead of reactive state to avoid re-renders
- **Watcher guards**: `isActivelyEditing` flag prevents unnecessary watcher execution during typing
