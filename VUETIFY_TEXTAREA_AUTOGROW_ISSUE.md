# Vuetify 3 v-textarea Auto-Grow Issue - Comprehensive Analysis

## Environment

### Stack
- **Frontend Framework**: Vue 3 with Composition API
- **UI Framework**: Vuetify 3 (exact version unknown, likely 3.3.23+)
- **Component**: `v-textarea` with `auto-grow` prop
- **File**: `/mnt/process/show-build/disaffected-ui/src/components/content-editor/EditorPanel.vue`

### Component Configuration
```vue
<v-textarea
  :ref="`textarea-${index}`"
  :model-value="getSegmentContent(index)"
  @update:model-value="updateTextSegment(index, $event)"
  @keydown="handleTextareaKeydown(index, $event)"
  @focus="handleParagraphFocus(index)"
  @blur="handleParagraphBlur(index)"
  variant="plain"
  hide-details
  auto-grow
  rows="1"
  class="speaker-textarea"
  :class="`speaker-${segment.speaker}`"
  :placeholder="`Enter ${getSpeakerDisplayName(segment.speaker)}'s dialogue here...`"
  no-resize
></v-textarea>
```

### Key Props
- `auto-grow`: Enabled (should make textarea expand to fit content)
- `rows="1"`: Initial height set to 1 row
- `variant="plain"`: Plain style variant
- `hide-details`: No validation/error messages shown
- `no-resize`: User cannot manually resize

## Problem Description

### Current Behavior
- Textareas remain at exactly 1 row height regardless of content length
- When content exceeds 1 row, scrollbars appear instead of the textarea growing
- The `auto-grow` prop appears to have no effect whatsoever
- This affects all speaker paragraphs in Script Mode

### Expected Behavior
- Textarea should start at 1 row height
- As user types and content wraps to multiple lines, textarea should automatically expand vertically
- No scrollbars should ever appear
- Each textarea should display all its content without scrolling

### Specific Test Case
- **Episode**: 0243
- **Index**: 30
- **Paragraph**: 2
- **Result**: Still only taking up one row despite multi-line content

## Known Vuetify 3 Issues

### Issue #18566: min-height Breaks Auto-Grow
- **Affected Version**: Vuetify 3.3.23
- **Status**: Closed as "not planned"
- **Description**: Setting `min-height` via CSS breaks auto-grow functionality
- **Working Version**: Last worked in Vuetify 2.7.0
- **Maintainer Response**: Component uses sophisticated CSS calculation; controlling min-height is complex
- **Resolution**: Vuetify team does not plan to fix this

### Issue #5526: Hidden Elements
- **Description**: Auto-grow fails when textarea is initially hidden with `display: none`
- **Workaround**: Call `calculateInputHeight()` when element becomes visible

### Issue #6995: Window Resize
- **Description**: Auto-grow doesn't recalculate when window is resized
- **Workaround**: Use `v-resize` directive and call `calculateInputHeight()`

### Issue #12444: Model Change
- **Description**: Auto-grow doesn't respond to model value changes
- **Workaround**: Force re-render or manual height calculation

## CSS Overrides Applied (Current State)

### Parent Container
```css
.speaker-textarea {
  font-family: 'Helvetica', sans-serif;
  font-size: 16px;
  line-height: 1.5;
  padding: 0;
  background-color: #fafafa !important;
}
```

### Vuetify Internal Elements (All with !important)
```css
.speaker-textarea :deep(.v-input__control) {
  min-height: auto !important;
  max-height: none !important;
  height: auto !important;
}

.speaker-textarea :deep(.v-field) {
  background-color: #fafafa !important;
  clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;
  min-height: auto !important;
  max-height: none !important;
  height: auto !important;
}

.speaker-textarea :deep(.v-field__field) {
  min-height: auto !important;
  max-height: none !important;
  height: auto !important;
}

.speaker-textarea :deep(.v-field__input) {
  padding: 5px !important;
  background-color: #fafafa !important;
  clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;
  min-height: auto !important;
  max-height: none !important;
  height: auto !important;
}

.speaker-textarea :deep(textarea) {
  resize: none !important;
  box-sizing: border-box !important;
  background-color: #fafafa !important;
  color: #000000 !important;
  font-family: 'Helvetica', sans-serif !important;
  font-size: 16px !important;
  padding: 0 !important;
  line-height: 1.5 !important;
  margin: 0 !important;
  clip-path: none !important;
  mask: none !important;
  -webkit-mask: none !important;
  min-height: auto !important;
  max-height: none !important;
  height: auto !important;
  overflow: hidden !important;
  scrollbar-width: none !important;
  -ms-overflow-style: none !important;
}

.speaker-textarea :deep(textarea::-webkit-scrollbar) {
  display: none !important;
}
```

## Attempted Solutions (All Failed)

### 1. Removed `rows="1"` Attribute
- **Result**: All textareas became 7-8 rows tall regardless of content
- **Conclusion**: Worse than original problem

### 2. Changed `overflow: hidden` to `overflow: visible`
- **Result**: Scrollbars reappeared
- **Conclusion**: Did not enable auto-grow

### 3. Removed All Height Constraints
- **Result**: No change in behavior
- **Conclusion**: Vuetify's auto-grow still not functioning

### 4. Added Explicit Height CSS Overrides
- **Result**: No change in behavior
- **Conclusion**: Setting `min-height: auto`, `max-height: none`, `height: auto` on all elements had no effect

### 5. Attempted to Call `calculateInputHeight()` Method
- **Result**: Method does not exist in Vuetify 3
- **Conclusion**: This was a Vuetify 2 API that no longer exists

### 6. Searched for Hidden Parent Elements
- **Result**: Textareas are always visible in Script Mode
- **Conclusion**: Not a visibility/hidden element issue

## Research Findings

### Vuetify 3 Auto-Grow Mechanism
- Uses sophisticated CSS calculations internally
- Requires specific CSS properties to not be overridden
- Known to be fragile and break easily with custom CSS
- No public API to manually trigger recalculation in Vuetify 3

### Common Working Solutions (For Other Contexts)
These solutions work in other scenarios but **have not worked in our case**:

1. **Force Re-render with Key**: Change component `:key` to recreate component
2. **Call calculateInputHeight()**: Only exists in Vuetify 2, not Vuetify 3
3. **Use v-resize Directive**: For window resize issues
4. **Delayed Height Calculation**: Use `$nextTick` and timers
5. **Remove min-height**: Vuetify maintainers recommend this

## Alternative Approaches to Consider

### Option 1: Custom Auto-Resize Implementation
Replace Vuetify's `auto-grow` with custom Vue 3 logic:

```javascript
// Method approach
const autoResize = (event) => {
  const textarea = event.target;
  textarea.style.height = 'auto';
  textarea.style.height = textarea.scrollHeight + 'px';
};

// Usage
<textarea @input="autoResize"></textarea>
```

### Option 2: VueUse Composable
Use `useTextareaAutosize` from VueUse library:

```javascript
import { useTextareaAutosize } from '@vueuse/core';

const { textarea, input } = useTextareaAutosize();

// Template
<textarea ref="textarea" v-model="input" />
```

### Option 3: Replace v-textarea with Native Textarea
Stop using Vuetify's `v-textarea` entirely and implement custom textarea with auto-resize:

```vue
<textarea
  :value="getSegmentContent(index)"
  @input="handleInput(index, $event)"
  @focus="handleFocus(index)"
  @blur="handleBlur(index)"
  @keydown="handleKeydown(index, $event)"
  class="custom-textarea"
  :placeholder="placeholder"
  rows="1"
></textarea>
```

With custom resize method:
```javascript
const resizeTextarea = (element) => {
  element.style.height = 'auto';
  element.style.height = element.scrollHeight + 'px';
};

const handleInput = (index, event) => {
  resizeTextarea(event.target);
  updateTextSegment(index, event.target.value);
};
```

### Option 4: Third-Party Component
Install a Vue 3 textarea component specifically designed for auto-resize:
- `vue-textarea-autosize` (npm package)
- Custom component from community examples

## Questions for Other LLMs

1. **Is there a working way to make Vuetify 3's `v-textarea` with `auto-grow` work when `rows="1"` is set?**

2. **What CSS properties are preventing Vuetify 3's auto-grow from functioning?** We've tried setting `min-height: auto`, `max-height: none`, `height: auto` on all internal elements with no success.

3. **Is there a way to access or manually trigger Vuetify 3's internal height calculation?** The `calculateInputHeight()` method from Vuetify 2 no longer exists.

4. **Should we abandon Vuetify's `v-textarea` entirely and implement a custom auto-resize solution?** If so, what's the most robust implementation?

5. **Are there known working examples of Vuetify 3 `v-textarea` with `auto-grow` and `rows="1"` in a production environment?**

6. **Could the issue be related to the `:deep()` CSS selectors or specificity battles with other Vuetify styles?**

7. **Is there a specific Vuetify 3 version that has working auto-grow functionality that we should downgrade/upgrade to?**

## Additional Context

### Component Architecture
- **Data Flow**: `scriptContent` prop → `rawScriptContent` computed → `scriptSegments` computed → individual segment rendering
- **Edit Buffer**: Debounced updates (1.5 seconds) with immediate save on blur
- **Paragraph State**: Tracks focused/saved states for visual feedback
- **Dynamic Rendering**: Multiple textareas rendered in `v-for` loop with segment-based styling

### Other CSS in File
The EditorPanel.vue file has 5600+ lines of CSS with many height-related rules for different modes (Code Mode, Script Mode, Typing Area). There may be conflicting rules or parent container constraints affecting textarea behavior.

### Critical User Requirement
- **Scrollbars must NEVER appear** on textareas in Script Mode
- Textareas must expand to show all content at all times
- Initial state should be compact (1 row) for empty/short content
- This is a core usability requirement for the Script Mode editing experience

## Next Steps to Consider

1. **Test with minimal Vuetify textarea** in isolated component to see if auto-grow works without CSS overrides
2. **Check parent container constraints** that might be limiting textarea expansion
3. **Implement custom auto-resize** as primary solution if Vuetify's auto-grow is fundamentally broken
4. **Consider filing new Vuetify GitHub issue** with this specific reproduction case
5. **Test with different Vuetify 3 versions** to find one where auto-grow works properly
6. **Replace v-textarea with native textarea + custom resize logic** as most reliable solution

## Summary

Vuetify 3's `v-textarea` with `auto-grow` prop is not functioning despite:
- Following official documentation
- Removing CSS height constraints that are known to break auto-grow
- Attempting multiple workarounds from GitHub issues and Stack Overflow
- Testing various CSS override combinations

The issue appears to be a fundamental limitation or bug in Vuetify 3's auto-grow implementation that may require either:
- A custom non-Vuetify solution
- Replacing the component entirely
- Finding an undocumented CSS combination that enables auto-grow
- Waiting for a Vuetify update (unlikely given issue #18566 was closed as "not planned")

**This document should be shared with other LLMs to gather alternative perspectives and solutions.**
