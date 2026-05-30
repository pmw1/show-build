# Script Mode Paragraph Auto-Resize & Line Numbers - UFDP

**Status**: ✅ Implemented and Working
**Component**: `disaffected-ui/src/components/content-editor/EditorPanel.vue`
**Issue**: Vuetify v-textarea `auto-grow` broken - paragraphs stuck at uniform height instead of sizing to content
**Solution**: Pure JavaScript height control + visual line number calculation

---

## Problem Overview

### Initial Issue
- All paragraphs in script mode displayed at uniform height (6-7 lines)
- Vuetify's `auto-grow` prop completely non-functional
- CSS height constraints (`height: auto`, `min-height`, `max-height`) conflicted with JavaScript
- Short paragraphs wasted space, long paragraphs got truncated
- No line numbers to help navigate script content

### Root Causes
1. **CSS/JS Conflict**: CSS `height: auto !important` overrode JavaScript's dynamic height setting
2. **Vuetify Wrapper Constraints**: `.v-field`, `.v-field__field`, `.v-field__input` had competing height rules
3. **Broken auto-grow**: Vuetify 3's auto-grow implementation doesn't work reliably
4. **scrollHeight Measurement**: Setting `height: auto` before measuring scrollHeight gives inaccurate results

---

## Solution 1: Paragraph Auto-Resize (Pure JavaScript Control)

### Strategy
Remove **ALL** CSS height constraints and let JavaScript have complete control via inline styles.

### Implementation

#### Step 1: Strip CSS Height Rules
**File**: `EditorPanel.vue` (CSS section, lines ~6315-6355)

**Removed ALL height constraints from:**
```css
/* BEFORE - Conflicting CSS */
.speaker-textarea :deep(.v-field) {
  min-height: 1.5em !important;
  max-height: none !important;
  height: auto !important;  /* ❌ Overrides JavaScript */
}

.speaker-textarea :deep(.v-field__field) {
  min-height: 1.5em !important;
  max-height: none !important;
  height: auto !important;  /* ❌ Overrides JavaScript */
}

.speaker-textarea :deep(.v-field__input) {
  min-height: auto !important;
  max-height: none !important;
  height: auto !important;  /* ❌ Overrides JavaScript */
}

.speaker-textarea :deep(textarea) {
  overflow: visible !important;
  min-height: 1.5em !important;
  /* height: auto removed but still constrained */
}
```

**After - No height constraints:**
```css
/* AFTER - JavaScript controls everything */
.speaker-textarea :deep(.v-field) {
  background-color: #fafafa !important;
  /* All height constraints removed */
}

.speaker-textarea :deep(.v-field__field) {
  /* All height constraints removed */
}

.speaker-textarea :deep(.v-field__input) {
  padding: 5px !important;
  /* All height constraints removed */
}

.speaker-textarea :deep(textarea) {
  resize: none !important;
  overflow: hidden !important; /* Hidden for accurate scrollHeight */
  /* NO height, min-height, or max-height */
}
```

#### Step 2: Removed Vuetify auto-grow
**File**: `EditorPanel.vue` (template section, line ~447)

```vue
<!-- BEFORE -->
<v-textarea
  auto-grow  <!-- ❌ Broken in Vuetify 3 -->
  rows="1"   <!-- ❌ Constrains height -->
/>

<!-- AFTER -->
<v-textarea
  <!-- No auto-grow, no rows - JavaScript handles everything -->
/>
```

#### Step 3: JavaScript Auto-Resize Function
**File**: `EditorPanel.vue` (lines 1772-1818)

**Key technique: Reset to 1px before measuring scrollHeight**

```javascript
autoResizeTextarea(index) {
  this.$nextTick(() => {
    const textareaRefArray = this.$refs[`textareaRef-${index}`];
    const textareaRef = Array.isArray(textareaRefArray) ? textareaRefArray[0] : textareaRefArray;

    if (textareaRef && textareaRef.$el) {
      const textarea = textareaRef.$el.querySelector('textarea');

      if (textarea) {
        // Force overflow hidden and remove any height constraints
        textarea.style.overflow = 'hidden';
        textarea.style.minHeight = '0';
        textarea.style.maxHeight = 'none';

        // 🔑 KEY: Reset to 1px to force accurate recalculation
        // (height: auto doesn't always trigger proper scrollHeight update)
        textarea.style.height = '1px';

        // Calculate the new height based on scrollHeight
        const scrollHeight = textarea.scrollHeight;
        const newHeight = scrollHeight + 'px';

        // Apply the new height directly via inline style
        textarea.style.height = newHeight;

        // Update line count for line number display
        this.$nextTick(() => {
          this.updateLineCount(index);
        });
      }
    }
  });
}
```

**Why `height = '1px'` instead of `height = 'auto'`?**
- Setting to `'auto'` often doesn't force browsers to recalculate scrollHeight
- Setting to `'1px'` forces content to reflow, giving accurate scrollHeight measurement
- This is a known technique for reliable textarea auto-resizing

#### Step 4: Multi-Attempt Initialization
**File**: `EditorPanel.vue` (mounted hook, lines 1250-1273)

**Problem**: Content may not be fully rendered when mounted() runs
**Solution**: Retry auto-resize at 0ms, 100ms, and 300ms delays

```javascript
mounted() {
  // Auto-resize all textareas with multiple attempts
  this.$nextTick(() => {
    if (this.scriptSegments && this.scriptSegments.length > 0) {
      // First attempt immediately
      this.scriptSegments.forEach((segment, index) => {
        if (segment.type === 'text' && segment.needsParagraphTags) {
          this.autoResizeTextarea(index);
        }
      });

      // Second attempt after 100ms to catch late renders
      setTimeout(() => {
        this.scriptSegments.forEach((segment, index) => {
          if (segment.type === 'text' && segment.needsParagraphTags) {
            this.autoResizeTextarea(index);
          }
        });
      }, 100);

      // Third attempt after 300ms to ensure everything is settled
      setTimeout(() => {
        this.scriptSegments.forEach((segment, index) => {
          if (segment.type === 'text' && segment.needsParagraphTags) {
            this.autoResizeTextarea(index);
          }
        });
      }, 300);
    }
  });
}
```

#### Step 5: Trigger on Content Changes
**File**: `EditorPanel.vue` (line ~1759)

Auto-resize is called whenever content changes:
```javascript
handleTextareaInput(index, newValue) {
  // Update content...

  // Auto-resize after content change
  this.autoResizeTextarea(index);
}
```

### Result
✅ Each paragraph now sizes **exactly** to its content
✅ Short paragraphs: ~24px (1 line)
✅ Long paragraphs: Dynamic height based on actual text
✅ No scrollbars, no truncation, no wasted space

---

## Solution 2: True Line Numbers (Visual Line Counting)

### Strategy
Calculate **visual** line count based on rendered textarea height, not just newline characters. Display cumulative line numbers across all paragraphs (like a code editor).

### Implementation

#### Step 1: Line Number Column in Template
**File**: `EditorPanel.vue` (template, lines 438-447)

```vue
<div class="paragraph-content">
  <!-- Line Numbers Column -->
  <div class="line-numbers-column" :ref="`lineNumbers-${index}`">
    <div
      v-for="lineNum in getLineCount(index)"
      :key="lineNum"
      class="line-number"
    >
      {{ getAbsoluteLineNumber(index, lineNum) }}
    </div>
  </div>

  <v-textarea ... />
</div>
```

**Key points:**
- `v-for` generates one line number per visual line
- `getLineCount(index)` returns number of lines in this paragraph
- `getAbsoluteLineNumber(index, lineNum)` calculates cumulative line number

#### Step 2: Visual Line Count Calculation
**File**: `EditorPanel.vue` (lines 1821-1833)

```javascript
// Calculate number of VISUAL lines in a textarea (based on rendered height)
getLineCount(index) {
  // Return cached value if available
  if (this.segmentLineCounts[index]) {
    return this.segmentLineCounts[index];
  }

  const content = this.getSegmentContent(index);
  if (!content || content.trim() === '') return 1;

  // Fallback: count newlines (used before textarea is measured)
  const newlineCount = (content.match(/\n/g) || []).length;
  return newlineCount + 1;
}
```

#### Step 3: Update Line Count After Resize
**File**: `EditorPanel.vue` (lines 1836-1852)

```javascript
// Update line count for a segment (called after resize)
updateLineCount(index) {
  const textareaRefArray = this.$refs[`textareaRef-${index}`];
  const textareaRef = Array.isArray(textareaRefArray) ? textareaRefArray[0] : textareaRefArray;

  if (textareaRef && textareaRef.$el) {
    const textarea = textareaRef.$el.querySelector('textarea');
    if (textarea) {
      // Calculate line count based on actual rendered height
      const lineHeight = 24; // 16px font * 1.5 line-height
      const totalHeight = textarea.scrollHeight;
      const lineCount = Math.max(1, Math.round(totalHeight / lineHeight));

      // Update reactive cache (Vue 3 way - direct assignment)
      this.segmentLineCounts[index] = lineCount;
    }
  }
}
```

**Formula**: `lineCount = scrollHeight / lineHeight`
- `lineHeight = 24px` (16px font-size × 1.5 line-height)
- `scrollHeight` comes from actual rendered textarea
- Counts **visual** wrapped lines, not just `\n` characters

#### Step 4: Cumulative Line Numbers
**File**: `EditorPanel.vue` (lines 1855-1867)

```javascript
// Calculate absolute line number across all paragraphs
getAbsoluteLineNumber(segmentIndex, relativeLineNum) {
  let absoluteLine = 0;

  // Sum up all lines from previous segments
  for (let i = 0; i < segmentIndex; i++) {
    if (this.scriptSegments[i] && this.scriptSegments[i].type === 'text' && this.scriptSegments[i].needsParagraphTags) {
      absoluteLine += this.getLineCount(i);
    }
  }

  // Add the current relative line number
  return absoluteLine + relativeLineNum;
}
```

**Example**:
- Paragraph 0: 3 lines → Lines 1, 2, 3
- Paragraph 1: 5 lines → Lines 4, 5, 6, 7, 8
- Paragraph 2: 2 lines → Lines 9, 10

#### Step 5: Reactive Cache for Performance
**File**: `EditorPanel.vue` (data section, line 1247)

```javascript
data() {
  return {
    segmentLineCounts: {} // Cache of line counts per segment for reactivity
  }
}
```

**Why cache?**
- `getLineCount()` is called in template for `v-for` rendering
- Re-measuring scrollHeight on every render is expensive
- Cache updates only when `updateLineCount()` is called (after resize)

#### Step 6: Flexbox Layout for Alignment
**File**: `EditorPanel.vue` (CSS, lines 6182-6216)

```css
/* Paragraph content - flex container */
.paragraph-content {
  padding: 5px 0;
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

/* Line numbers column */
.line-numbers-column {
  flex-shrink: 0;
  width: 45px;
  display: flex;
  flex-direction: column;
  padding-top: 5px;
  user-select: none;
}

.line-number {
  text-align: right;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.4);
  line-height: 1.5;
  height: 24px; /* Match textarea line height (16px font * 1.5) */
  padding-right: 8px;
  white-space: nowrap;
}

.speaker-textarea {
  flex: 1;
}
```

**Key alignments:**
- `height: 24px` on `.line-number` matches textarea line height exactly
- `line-height: 1.5` matches textarea's line-height
- `flex-direction: column` stacks line numbers vertically
- `align-items: flex-start` aligns numbers with top of each text line

### Result
✅ True line numbers counting visual wrapped lines
✅ Cumulative numbering across all paragraphs (1, 2, 3... like a code editor)
✅ Numbers update automatically when content changes
✅ Perfect vertical alignment with text lines
✅ Monospace font for consistent width

---

## Key Techniques Summary

### Paragraph Auto-Resize
1. **Remove ALL CSS height constraints** - let JavaScript have full control
2. **Set `height = '1px'` before measuring** - forces accurate scrollHeight calculation
3. **Use inline styles for height** - `textarea.style.height = scrollHeight + 'px'`
4. **Multi-attempt initialization** - retry at 0ms, 100ms, 300ms for DOM readiness
5. **No `auto-grow` prop** - Vuetify's implementation is broken

### Line Numbers
1. **Calculate visual lines** - `scrollHeight / lineHeight`, not just `\n` count
2. **Reactive cache** - store line counts in `segmentLineCounts` object
3. **Cumulative numbering** - sum previous paragraph line counts for absolute position
4. **Update after resize** - call `updateLineCount()` in `autoResizeTextarea()`
5. **Flexbox alignment** - fixed-width column with `height: 24px` per line

---

## Files Modified

### Primary File
- **`disaffected-ui/src/components/content-editor/EditorPanel.vue`**
  - Lines 438-462: Line number column template
  - Lines 1247: Added `segmentLineCounts` reactive cache
  - Lines 1250-1273: Multi-attempt auto-resize in mounted()
  - Lines 1772-1818: `autoResizeTextarea()` function
  - Lines 1821-1867: `getLineCount()`, `updateLineCount()`, `getAbsoluteLineNumber()` functions
  - Lines 6182-6256: CSS for line numbers and paragraph layout
  - Lines 6315-6375: Stripped all CSS height constraints from textareas

---

## Testing Checklist

### Paragraph Sizing
- ✅ Short paragraphs (1-2 lines) display compact
- ✅ Long paragraphs (10+ lines) expand to show all content
- ✅ No scrollbars appear on textareas
- ✅ Heights adjust when typing/deleting content
- ✅ Heights correct after episode load

### Line Numbers
- ✅ Line 1 starts at first paragraph
- ✅ Numbers continue sequentially across paragraphs
- ✅ Visual wrapped lines counted (not just `\n` characters)
- ✅ Numbers vertically aligned with text
- ✅ Numbers update when content changes

---

## Performance Considerations

### Auto-Resize Optimization
- ✅ Uses `$nextTick()` to batch DOM updates
- ✅ Only resizes on content change, not on every render
- ✅ No expensive operations in render loop

### Line Number Optimization
- ✅ Cached line counts prevent repeated scrollHeight measurements
- ✅ Only recalculates when `updateLineCount()` called
- ✅ `v-for` renders efficiently from cached numbers

---

## Debugging Tips

### If paragraphs aren't resizing:
1. Check browser console for `autoResizeTextarea` logs
2. Verify no CSS `height` rules are overriding inline styles
3. Check if `textareaRef` is resolving correctly
4. Ensure `$nextTick()` is being called

### If line numbers are wrong:
1. Check `lineHeight` calculation (should be 24px for 16px font × 1.5)
2. Verify `updateLineCount()` is called after resize
3. Check `segmentLineCounts` cache in Vue DevTools
4. Ensure `getAbsoluteLineNumber()` is summing previous paragraphs

---

## Related Issues Resolved

### Issue: Template ref naming conflicts
- **Problem**: Using `ref="episodeForm"` conflicted with reactive variable `episodeForm`
- **Solution**: Use `Ref` suffix for template refs (`episodeFormRef`)
- **Reference**: `docs/VUE_TEMPLATE_REF_CONFLICTS.md`

### Issue: Vue 2 `$set` API in Vue 3 code
- **Problem**: `this.$set(this.segmentLineCounts, index, lineCount)` - `$set` doesn't exist in Vue 3
- **Solution**: Direct assignment `this.segmentLineCounts[index] = lineCount`
- **Reference**: Vue 3 Migration Guide - Reactivity API changes

---

## Future Enhancements

### Potential Improvements
1. **Line number click-to-select**: Click line number to select/focus that line
2. **Breakpoint indicators**: Allow marking specific lines for production notes
3. **Line highlighting**: Highlight current line when focused
4. **Minimap**: VSCode-style minimap for long scripts
5. **Syntax highlighting**: Color-code speakers, stage directions, etc.

### Known Limitations
- Line count calculation assumes monospace-equivalent wrapping
- Very long single words may cause slight misalignment
- Line numbers don't account for hidden YAML frontmatter lines

---

**Implementation Date**: 2025-10-03
**Component Version**: EditorPanel.vue (latest)
**Status**: ✅ Production Ready
