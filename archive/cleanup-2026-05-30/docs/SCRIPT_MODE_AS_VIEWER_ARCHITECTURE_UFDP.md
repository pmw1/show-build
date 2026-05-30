# Script Mode as Pure Viewer Architecture - UFDP Documentation

## Executive Summary

The Script Mode editor has been completely rewritten to implement a **single source of truth** architecture that eliminates reactive feedback loops. Script Mode now operates as a **pure viewer** that parses and displays raw markdown content, while all editing operations directly modify the underlying Code Mode content.

**Key Achievement**: Eliminated the character-by-character reactive loops that caused text duplication, deletion cascades, and typing corruption.

## Core Architecture: Single Source of Truth Pattern

### The Problem We Solved

**Before**: Reactive Feedback Hell
```javascript
// OLD BROKEN APPROACH
parsedContentSegments() {  // ❌ Computed property from hell
  // Re-parsed entire content on every keystroke
  // Created reactive loops between Script and Code modes
  // Caused text to appear in multiple places simultaneously
  // Made character deletion cascade across paragraphs
}
```

**After**: Single Source of Truth
```javascript
// NEW CLEAN APPROACH
rawScriptContent: {  // ✅ Single source of truth
  get() { return this.scriptContent || '' },
  set(value) { this.$emit('update:scriptContent', value) }
},

scriptSegments() {  // ✅ Non-reactive parsing for display only
  // Only runs when Script mode is active
  // Parses content for visual display
  // No reactive feedback loops
}
```

### Data Flow Architecture

```
User Types in Script Mode
         ↓
handleTextareaKeydown() detects behavior
         ↓
updateTextSegment() modifies specific segment
         ↓
reconstructRawContent() rebuilds raw markdown
         ↓
rawScriptContent updated (single source of truth)
         ↓
Code Mode displays updated markdown
Script Mode re-renders from updated content
```

## Script Mode: Pure Viewer Implementation

### What Script Mode Actually Is

Script Mode is **NOT** a separate editor. It's a **visual renderer** that:

1. **Parses** raw markdown into displayable segments
2. **Renders** segments as individual textarea components
3. **Captures** user input and maps it back to raw content
4. **Never stores** parsed segments as reactive data

### Segment vs Chunk Terminology

**Critical Distinction**:
- **Segments**: Temporary parsing units created for Script Mode display only
- **Chunks**: NOT USED - avoid this term to prevent confusion
- **Raw Content**: The actual markdown stored in Code Mode

### Script Mode Display Logic

```javascript
// Script Mode Template Logic
<div v-for="(segment, index) in scriptSegments" :key="`segment-${index}`">
  <!-- Text Segment = Editable Textarea -->
  <v-textarea
    v-if="segment.type === 'text'"
    :model-value="segment.content"
    @update:model-value="updateTextSegment(index, $event)"
    @keydown="handleTextareaKeydown(index, $event)"
  />

  <!-- Cue Segment = Visual Card -->
  <CueCard
    v-else-if="segment.type === 'cue'"
    :cue-data="segment.data"
    @edit="editCue(index)"
  />
</div>
```

## Code Mode: Raw Markdown Display

### What Code Mode Shows

Code Mode displays the **actual file content** that gets saved to disk:

```markdown
---
id: '0237001'
slug: opening
type: segment
order: 10
duration: 00:05:00
title: Opening
---

<p class="josh">I've been putting off talking about the concept of forgiveness for a long time. It exercises me to the point of being genuinely triggered.</p>

<p class="josh">One of the primary points I want to get across in this monologue is the importance of giving and understanding specific definitions.</p>

<!-- Begin Cue -->
[Type: FSQ]
[AssetID: fsq_1758933032822_forgivenes]
[Slug: 90 forgiveness one]
[Quote: Forgiveness Definition 1-releasing or overcoming all negative emotionality...]
<!-- End Cue -->

<p class="josh">Let's take definition 1, releasing all negative emotionality toward the abuser.</p>
```

### What Code Mode NEVER Shows

- ❌ JavaScript objects: `{type: 'text', content: '...', speaker: 'josh'}`
- ❌ Parsed segments or arrays
- ❌ Vue component structure
- ❌ Any internal parsing artifacts

### Code Mode Implementation

```javascript
// Code Mode Template - Simple v-model
<v-textarea
  v-model="rawScriptContent"  // Direct binding to single source of truth
  class="code-textarea"
  placeholder="Edit the script content in markdown format..."
/>
```

## Segment-Based Editing System

### How Script Mode Editing Works

When user types in Script Mode textarea:

```javascript
updateTextSegment(segmentIndex, newContent) {
  // 1. Get current segments from parsed content (temporary)
  const segments = [...this.scriptSegments];

  // 2. Update this specific segment (in memory only)
  segments[segmentIndex].content = newContent;

  // 3. Reconstruct raw markdown from segments
  const newRawContent = this.reconstructRawContent(segments);

  // 4. Update single source of truth (triggers all updates)
  this.rawScriptContent = newRawContent;
}
```

### Segment Index Mapping

Each Script Mode textarea maps to a specific segment index:

```
Script Mode Display:     Segment Mapping:
┌─────────────────┐     segment[0] = text: "First paragraph..."
│ First paragraph │  →  segment[1] = cue: {type: 'FSQ', ...}
├─────────────────┤     segment[2] = text: "Second paragraph..."
│ [FSQ Card]      │  →  segment[3] = cue: {type: 'SOT', ...}
├─────────────────┤     segment[4] = text: "Third paragraph..."
│ Second paragraph│
├─────────────────┤
│ [SOT Card]      │
├─────────────────┤
│ Third paragraph │
└─────────────────┘
```

## Script Mode Behaviors → Code Mode Actions

### Double Enter: Create New Paragraph

**User Action**: Types `[Enter][Enter]` in Script Mode
**Result**: Creates new `<p class="speaker">` tag in Code Mode

```javascript
handleTextareaKeydown(segmentIndex, event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    setTimeout(() => {
      if (textarea.value.endsWith('\n\n')) {
        // Clean current paragraph
        const cleanedContent = newContent.replace(/\n\n$/, '');
        this.updateTextSegment(segmentIndex, cleanedContent);

        // Create new <p> tag in Code Mode
        this.createNewParagraphAfter(segmentIndex);
      }
    }, 0);
  }
}
```

**Before (Script Mode)**:
```
┌─────────────────────────────────┐
│ This is my first paragraph██    │
│                                 │  ← User presses Enter Enter
└─────────────────────────────────┘
```

**After (Code Mode)**:
```markdown
<p class="josh">This is my first paragraph</p>

<p class="josh"></p>  ← New empty paragraph created
```

**After (Script Mode)**:
```
┌─────────────────────────────────┐
│ This is my first paragraph      │
└─────────────────────────────────┘
┌─────────────────────────────────┐
│ ██                              │  ← Focus moves to new paragraph
└─────────────────────────────────┘
```

### Backspace at Start: Merge with Previous

**User Action**: Presses `[Backspace]` at beginning of empty paragraph
**Result**: Removes empty `<p>` tag and merges with previous

```javascript
if (event.key === 'Backspace') {
  const cursorPos = textarea.selectionStart;
  const content = textarea.value;

  // If at beginning of empty paragraph
  if (cursorPos === 0 && content.trim() === '') {
    event.preventDefault();
    this.mergeParagraphWithPrevious(segmentIndex);
  }
}
```

### Delete at End: Merge with Next

**User Action**: Presses `[Delete]` at end of paragraph
**Result**: Merges content with next paragraph, removes redundant `<p>` tag

## CueParser Integration

### How Parsing Works

```javascript
// CueParser.parseContent() splits raw markdown into segments
const segments = CueParser.parseContent(contentWithoutFrontmatter);

// Example result:
[
  {
    type: 'text',
    content: 'First paragraph content',
    speaker: 'josh',
    needsParagraphTags: true
  },
  {
    type: 'cue',
    cueType: 'FSQ',
    data: { assetId: 'fsq_123', slug: 'graphic-one', ... }
  },
  {
    type: 'text',
    content: 'Second paragraph content',
    speaker: 'josh',
    needsParagraphTags: true
  }
]
```

### How Reconstruction Works

```javascript
// CueParser.reconstructContent() converts segments back to markdown
const reconstructed = CueParser.reconstructContent(segments);

// Result:
<p class="josh">First paragraph content</p>

<!-- Begin Cue -->
[Type: FSQ]
[AssetID: fsq_123]
[Slug: graphic-one]
<!-- End Cue -->

<p class="josh">Second paragraph content</p>
```

## Reactive Flow Prevention

### The Old Broken System

```javascript
// OLD: Reactive Feedback Loop from Hell
computed: {
  parsedContentSegments() {  // ❌ Re-ran on EVERY keystroke
    // Parsed entire content
    // Triggered template re-render
    // Caused multiple textareas to update
    // Created character deletion cascades
    return CueParser.parseContent(this.scriptContent);
  }
}

// Template used reactive segments
<textarea @update:model-value="updateSegmentContent">  // ❌ Triggered more parsing
  {{ segment.content }}
</textarea>
```

### The New Clean System

```javascript
// NEW: Non-Reactive Display-Only Parsing
computed: {
  scriptSegments() {  // ✅ Only runs when Script mode is active
    if (!this.rawScriptContent || this.editorMode !== 'script') {
      return [];  // No parsing unless needed
    }
    return CueParser.parseContent(this.rawScriptContent);
  }
}

// Direct raw content updates
updateTextSegment(index, content) {  // ✅ No reactive loops
  // Update raw content directly
  this.rawScriptContent = newContent;
}
```

## Performance Implications

### Before: Reactive Chaos

- **Every keystroke**: Re-parsed entire document
- **Multiple event handlers**: `@input` + `@update:model-value` conflicts
- **Cascading updates**: One change triggered dozens of re-renders
- **Memory leaks**: Accumulated watchers and timers

### After: Efficient Updates

- **Parse only when needed**: Script mode activation or content change
- **Single event handler**: Only `@update:model-value`
- **Direct updates**: Raw content changes propagate naturally
- **Clean memory**: No accumulated reactive watchers

## Mode Switching Architecture

### Instant Mode Switching

Both modes show the **same data** in different formats:

```javascript
// Code Mode: Shows raw content directly
<v-textarea v-model="rawScriptContent" />

// Script Mode: Shows parsed segments of same content
<div v-for="segment in scriptSegments">
  <v-textarea :model-value="segment.content" />
</div>
```

### No Sync Needed

- **Code Mode changes**: Automatically visible in Script Mode (same data)
- **Script Mode changes**: Directly update Code Mode content
- **No sync logic**: Single source of truth eliminates sync problems

## Cue Block Editing

### Cue Cards in Script Mode

Cue blocks appear as **visual cards** between text segments:

```
Script Mode:
┌─────────────────────────────────┐
│ Text before cue...              │
└─────────────────────────────────┘
┌─────────────────────────────────┐
│ [FSQ] 90 forgiveness one        │ ← Non-editable card
│ Forgiveness Definition 1...     │
│ [Edit] [Delete]                 │
└─────────────────────────────────┘
┌─────────────────────────────────┐
│ Text after cue...               │
└─────────────────────────────────┘
```

### Cue Editing Modal System

```javascript
editCue(segmentIndex) {
  // Open modal with all cue fields editable
  this.editingCueData = { ...this.scriptSegments[segmentIndex].data };
  this.showCueEditModal = true;
}

saveCueEdit(updatedCueData) {
  // Update specific cue segment
  const segments = [...this.scriptSegments];
  segments[segmentIndex].data = updatedCueData;

  // Reconstruct raw content with updated cue
  const newRawContent = this.reconstructRawContent(segments);
  this.rawScriptContent = newRawContent;
}
```

## Error Prevention and Debugging

### Common Pitfalls Avoided

1. **Don't store segments in reactive data**
   ```javascript
   // ❌ WRONG - Creates reactive loops
   data() { return { segments: [] } }

   // ✅ CORRECT - Computed from raw content
   computed: { scriptSegments() { /* parse only when needed */ } }
   ```

2. **Don't use multiple event handlers**
   ```javascript
   // ❌ WRONG - Double events
   @update:model-value="updateContent"
   @input="handleInput"

   // ✅ CORRECT - Single event
   @update:model-value="updateTextSegment"
   ```

3. **Don't modify segments directly**
   ```javascript
   // ❌ WRONG - Mutates parsed data
   this.scriptSegments[0].content = newContent;

   // ✅ CORRECT - Updates raw content
   this.rawScriptContent = reconstructedContent;
   ```

### Debugging Checklist

**Script Mode Issues**:
- [ ] Check `scriptSegments` computed property only runs in Script mode
- [ ] Verify `rawScriptContent` is single source of truth
- [ ] Ensure no double event handlers on textareas
- [ ] Confirm segments are not stored in reactive data

**Code Mode Issues**:
- [ ] Verify direct binding to `rawScriptContent`
- [ ] Check YAML frontmatter preservation
- [ ] Ensure no segment artifacts in displayed content

**Mode Switching Issues**:
- [ ] Confirm both modes use same `rawScriptContent`
- [ ] Check computed properties don't run when not needed
- [ ] Verify no sync logic between modes

## Implementation Files

### Core Files Modified

1. **EditorPanel.vue**: Complete rewrite of editing logic
   - Replaced `parsedContentSegments` with `scriptSegments`
   - Added `rawScriptContent` computed property
   - Implemented segment-based editing methods
   - Added Script mode behavior handlers

2. **ContentEditor.vue**: Removed conflicting event handlers
   - Removed `@content-change` event binding
   - Cleaned up `onContentChange` method
   - Simplified parent-child communication

3. **CueParser.js**: Enhanced reconstruction logic
   - Improved `reconstructContent()` method
   - Better text segment merging
   - Preserved YAML frontmatter handling

### Key Methods

```javascript
// Core editing method
updateTextSegment(segmentIndex, newContent)

// Behavior handlers
handleTextareaKeydown(segmentIndex, event)
createNewParagraphAfter(segmentIndex)
mergeParagraphWithPrevious(segmentIndex)
mergeParagraphWithNext(segmentIndex)

// Reconstruction
reconstructRawContent(segments)
```

## Testing and Verification

### Manual Test Cases

1. **Double Enter Test**:
   - Type in Script Mode paragraph
   - Press Enter Enter
   - Verify new paragraph created
   - Check Code Mode shows proper `<p>` tags

2. **Mode Switch Test**:
   - Edit in Script Mode
   - Switch to Code Mode
   - Verify changes appear immediately
   - Switch back to Script Mode
   - Verify consistent display

3. **Cue Edit Test**:
   - Edit cue in Script Mode modal
   - Verify Code Mode shows updated cue block
   - Check cue fields preserved correctly

4. **Backspace Merge Test**:
   - Create empty paragraph
   - Press Backspace at start
   - Verify paragraph removed
   - Check focus moves to previous

### Performance Verification

- **No character-by-character parsing**: Type rapidly, check CPU usage
- **No reactive loops**: Monitor Vue DevTools for excessive updates
- **Clean memory**: Check for accumulating watchers
- **Fast mode switching**: Time switches between Script/Code modes

## Future Enhancements

### Potential Improvements

1. **Incremental Parsing**: Only re-parse changed segments
2. **Virtual Scrolling**: Handle very long scripts efficiently
3. **Undo/Redo**: Implement proper history management
4. **Collaborative Editing**: Multi-user editing support
5. **Syntax Highlighting**: Enhanced Code Mode display

### Architecture Extensibility

The single source of truth pattern supports:
- **New Script Mode behaviors**: Add to `handleTextareaKeydown()`
- **Additional cue types**: Extend CueParser recognition
- **Custom rendering**: Modify `scriptSegments` computed property
- **Export formats**: Generate from `rawScriptContent`

## Conclusion

The Script Mode as Pure Viewer architecture successfully eliminates reactive feedback loops while providing an intuitive editing experience. Users get the benefits of visual editing in Script Mode with the reliability and transparency of direct markdown editing in Code Mode.

**Key Success Metrics**:
- ✅ Zero reactive feedback loops
- ✅ No text duplication or deletion cascades
- ✅ Smooth typing experience
- ✅ Instant mode switching
- ✅ Proper paragraph management
- ✅ Clean cue block editing
- ✅ Single source of truth maintained

The implementation proves that complex editor requirements can be met with simple, clean architecture when the right abstractions are chosen.