# Script Mode Keyboard Event Handling

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

### 2. Space Key Debounce Buffer

**Problem**: Vue reactivity causes typed spaces to be overwritten during re-render

**Solution**: Edit buffer system with debounced sync (`EditorPanel.vue:2134-2186`)

```javascript
updateTextSegment(segmentIndex, newContent) {
  // Initialize edit buffer if needed
  if (!this.segmentEditBuffer) {
    this.segmentEditBuffer = {};
  }

  // Store the new content in buffer immediately
  this.segmentEditBuffer[segmentIndex] = newContent;

  // Clear existing timer for this segment
  if (this.updateDebounceTimers[segmentIndex]) {
    clearTimeout(this.updateDebounceTimers[segmentIndex]);
  }

  // Debounce the actual update to prevent race conditions during typing
  this.updateDebounceTimers[segmentIndex] = setTimeout(() => {
    // Get current segments from parsed content
    const segments = [...this.scriptSegments];
    segments[segmentIndex].content = this.segmentEditBuffer[segmentIndex];

    // Reconstruct raw markdown content
    const newRawContent = this.reconstructRawContent(segments);

    // Update single source of truth
    this.rawScriptContent = newRawContent;

    // Clear buffer and timer
    delete this.segmentEditBuffer[segmentIndex];
    delete this.updateDebounceTimers[segmentIndex];
  }, 1000); // 1 second debounce
}
```

**How It Works**:
1. User types → `@update:model-value` fires → content stored in buffer
2. `getSegmentContent()` returns buffered content to v-model (prevents overwrite)
3. After 1 second of no typing, buffer syncs to `rawScriptContent` (Code Mode)
4. When `rawScriptContent` updates, `scriptSegments` recomputes, but buffer takes precedence

**Key Benefits**:
- No lost characters during typing
- Smooth typing experience
- Automatic sync to Code Mode after pause
- Per-segment buffer prevents cross-segment interference

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
- [ ] Code Mode updates after 1 second pause
- [ ] Changes sync between Script Mode and Code Mode

## Related Files

- `disaffected-ui/src/components/content-editor/EditorPanel.vue` - Main implementation
- `disaffected-ui/src/utils/cueParser.js` - Content parsing and reconstruction
- `docs/DEBUGGING_CHEAT_SHEET.md` - Quick troubleshooting
- `docs/VUE_TEMPLATE_REF_CONFLICTS.md` - Related reactivity issues

## Performance Considerations

- **1-second debounce**: Balances responsiveness with performance
- **Per-segment timers**: Prevents interference between paragraphs
- **Buffer cleanup**: Timers and buffers are deleted after sync
- **Retry with backoff**: Focus retry uses 50ms delays to avoid tight loops
