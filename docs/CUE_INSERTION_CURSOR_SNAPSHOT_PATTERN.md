# Cue Insertion Cursor Position Snapshot Pattern

**Version**: 1.0
**Status**: ✅ Production Pattern
**Implemented**: FSQ (Full-Screen Quote)
**Pending**: SOT, GFX, VO, NAT, PKG, VOX, MUS, LIVE, IMG

---

## The Problem

When a user presses a hotkey (e.g., Ctrl+Q for FSQ) to open a cue insertion modal:

1. **User is focused in the editor** - `focusedParagraphIndex` has a valid value
2. **Modal opens** - Focus moves from editor to modal form fields
3. **User fills out form** - Still focused in modal, not editor
4. **User clicks Insert** - `focusedParagraphIndex` is now `null` (no editor focus)
5. **Cue inserts at bottom** - Falls back to end of document instead of cursor position

**Root Cause**: Checking cursor position at insertion time is too late - focus has already moved to the modal.

---

## The Solution

**Snapshot cursor position when the hotkey is pressed, BEFORE the modal opens.**

### Three-Step Implementation

#### Step 1: Add Snapshot Variable

In `ContentEditor.vue` data section:

```javascript
data() {
  return {
    // ... existing data ...

    // Cue insertion position snapshots
    fsqInsertionIndex: null,   // FSQ (Full-Screen Quote)
    sotInsertionIndex: null,   // SOT (Sound on Tape)
    gfxInsertionIndex: null,   // GFX (Graphics)
    voInsertionIndex: null,    // VO (Voice Over)
    natInsertionIndex: null,   // NAT (Natural Sound)
    pkgInsertionIndex: null,   // PKG (Package)
    voxInsertionIndex: null,   // VOX (Vox Pop)
    musInsertionIndex: null,   // MUS (Music)
    liveInsertionIndex: null,  // LIVE (Live Shot)
    imgInsertionIndex: null,   // IMG (Image)
  }
}
```

**Why separate variables?**
Prevents conflicts if user has multiple cue modals open simultaneously.

---

#### Step 2: Capture Position on Hotkey Press

In the modal handler method (e.g., `handleShowFsqModal()`):

```javascript
handleShowFsqModal() {
  if (!this.showFsqModal) {
    // 📸 SNAPSHOT: Capture cursor position RIGHT NOW
    this.fsqInsertionIndex = this.$refs.editorPanel?.focusedParagraphIndex;
    console.log('📍 FSQ hotkey pressed - captured cursor position:', this.fsqInsertionIndex);

    // Fallback: If no paragraph focused, use last segment
    if (this.fsqInsertionIndex === null || this.fsqInsertionIndex === undefined) {
      const segments = this.$refs.editorPanel?.scriptSegments || [];
      this.fsqInsertionIndex = segments.length > 0 ? segments.length - 1 : null;
      console.log('📍 No focus detected, using last segment:', this.fsqInsertionIndex);
    }

    // NOW open the modal (focus will move here)
    this.showFsqModal = true;
  }
}
```

**Key Points:**
- Capture happens BEFORE `this.showFsqModal = true`
- Always include fallback logic (last segment)
- Console logging helps debug cursor position issues

---

#### Step 3: Use Snapshot for Insertion

In the submit handler (e.g., `submitFsq()`):

```javascript
submitFsq(cueData) {
  // ... format cue block ...

  if (isLastPart) {
    // Close modal
    this.showFsqModal = false;

    // ✅ USE SNAPSHOT: Not current focus!
    const insertionIndex = this.fsqInsertionIndex;
    console.log(`📍 Using snapshotted cursor position: ${insertionIndex}`);

    // Insert cue at snapshotted position
    this.appendToScriptContent(`\n${cueBlock}\n`, insertionIndex);

    // 🧹 CLEAR SNAPSHOT: Prevent stale position on next use
    this.fsqInsertionIndex = null;
    console.log('🧹 Cleared fsqInsertionIndex snapshot');

    this.hasUnsavedChanges = true;
  }
}
```

**Key Points:**
- Use the stored snapshot, NOT `this.$refs.editorPanel?.focusedParagraphIndex`
- Always clear snapshot after use (`null`)
- Clearing prevents accidental reuse of stale position

---

## Copy-Paste Template

Use this template for implementing other cue types (replace `TYPE` with cue type):

### Data Section
```javascript
typeInsertionIndex: null,  // TYPE insertion position snapshot
```

### Hotkey Handler
```javascript
handleShowTypeModal() {
  if (!this.showTypeModal) {
    // Snapshot cursor position
    this.typeInsertionIndex = this.$refs.editorPanel?.focusedParagraphIndex;
    console.log('📍 TYPE hotkey pressed - captured cursor position:', this.typeInsertionIndex);

    // Fallback to last segment if no focus
    if (this.typeInsertionIndex === null || this.typeInsertionIndex === undefined) {
      const segments = this.$refs.editorPanel?.scriptSegments || [];
      this.typeInsertionIndex = segments.length > 0 ? segments.length - 1 : null;
      console.log('📍 No focus detected, using last segment:', this.typeInsertionIndex);
    }

    this.showTypeModal = true;
  }
}
```

### Submit Handler
```javascript
submitType(cueData) {
  // ... format cue block ...

  if (isLastPart) {
    this.showTypeModal = false;

    // Use snapshot
    const insertionIndex = this.typeInsertionIndex;
    console.log(`📍 Using snapshotted position: ${insertionIndex}`);

    this.appendToScriptContent(`\n${cueBlock}\n`, insertionIndex);

    // Clear snapshot
    this.typeInsertionIndex = null;
    console.log('🧹 Cleared typeInsertionIndex snapshot');

    this.hasUnsavedChanges = true;
  }
}
```

---

## Implementation Checklist

For each cue type modal:

- [ ] Add `{type}InsertionIndex: null` to data section
- [ ] Modify `handleShow{Type}Modal()` to capture position before opening
- [ ] Add fallback logic (last segment if no focus)
- [ ] Modify `submit{Type}()` to use snapshot instead of current focus
- [ ] Clear snapshot after insertion (`this.{type}InsertionIndex = null`)
- [ ] Add console logging for debugging
- [ ] Test with cursor at beginning, middle, end of document
- [ ] Test with no cursor focus (should use last segment)

---

## Cue Types Implementation Status

| Cue Type | Modal Method | Submit Method | Status |
|----------|-------------|---------------|--------|
| **FSQ** | `handleShowFsqModal()` | `submitFsq()` | ✅ Implemented |
| **SOT** | `handleShowSotModal()` | `submitSot()` | 🔲 Pending |
| **GFX** | `handleShowGfxModal()` | `submitGfx()` | 🔲 Pending |
| **VO** | `handleShowVoModal()` | `submitVo()` | 🔲 Pending |
| **NAT** | `handleShowNatModal()` | `submitNat()` | 🔲 Pending |
| **PKG** | `handleShowPkgModal()` | `submitPkg()` | 🔲 Pending |
| **VOX** | `handleShowVoxModal()` | `submitVox()` | 🔲 Pending |
| **MUS** | `handleShowMusModal()` | `submitMus()` | 🔲 Pending |
| **LIVE** | `handleShowLiveModal()` | `submitLive()` | 🔲 Pending |
| **IMG** | `handleShowImgModal()` | `handleImgCueSubmit()` | 🔲 Pending |

---

## Common Mistakes to Avoid

### ❌ Don't Check Current Focus at Insertion Time
```javascript
// WRONG: Focus has moved to modal by now
submitFsq(cueData) {
  const insertionIndex = this.$refs.editorPanel?.focusedParagraphIndex; // Always null!
  this.appendToScriptContent(cueBlock, insertionIndex);
}
```

### ✅ Use the Snapshot
```javascript
// CORRECT: Use position captured when hotkey pressed
submitFsq(cueData) {
  const insertionIndex = this.fsqInsertionIndex; // Valid snapshot!
  this.appendToScriptContent(cueBlock, insertionIndex);
  this.fsqInsertionIndex = null; // Clear for next time
}
```

---

### ❌ Don't Forget to Clear Snapshot
```javascript
// WRONG: Stale position will be reused next time
submitFsq(cueData) {
  const insertionIndex = this.fsqInsertionIndex;
  this.appendToScriptContent(cueBlock, insertionIndex);
  // Missing: this.fsqInsertionIndex = null
}
```

### ✅ Always Clear After Use
```javascript
// CORRECT: Prevent stale position reuse
submitFsq(cueData) {
  const insertionIndex = this.fsqInsertionIndex;
  this.appendToScriptContent(cueBlock, insertionIndex);
  this.fsqInsertionIndex = null; // Essential!
}
```

---

### ❌ Don't Share One Variable Across Cue Types
```javascript
// WRONG: Multiple modals will conflict
data() {
  return {
    cueInsertionIndex: null // Shared by all cue types - BAD!
  }
}
```

### ✅ One Variable Per Cue Type
```javascript
// CORRECT: Each cue type has its own snapshot
data() {
  return {
    fsqInsertionIndex: null,
    sotInsertionIndex: null,
    gfxInsertionIndex: null,
    // ... one per cue type
  }
}
```

---

## Testing Strategy

For each cue type implementation:

1. **Cursor at Beginning**: Press hotkey with cursor in first paragraph
   - **Expected**: Cue inserts after first paragraph

2. **Cursor in Middle**: Press hotkey with cursor in middle paragraph
   - **Expected**: Cue inserts after that paragraph

3. **Cursor at End**: Press hotkey with cursor in last paragraph
   - **Expected**: Cue inserts after last paragraph

4. **No Cursor Focus**: Press hotkey when not focused in editor
   - **Expected**: Cue inserts at end (last segment fallback)

5. **Modal Interaction**: Fill out modal, click Insert
   - **Expected**: Cue inserts at originally snapshotted position, NOT at end

6. **Multiple Uses**: Insert cue, then insert another one
   - **Expected**: Each insertion uses fresh snapshot, not stale position

---

## Files Modified

**Primary File**: `/mnt/process/show-build/disaffected-ui/src/components/ContentEditor.vue`

**FSQ Implementation Lines** (reference for other cue types):
- Line 763: `fsqInsertionIndex: null` data variable
- Lines 1122-1137: `handleShowFsqModal()` snapshot capture
- Lines 3074-3100: `submitFsq()` snapshot usage

---

## Related Documentation

- **UNIVERSAL_LLM_FRAMEWORK_UFDP.md** - Universal LLM Framework documentation
- **DEBUGGING_STANDARDS.md** - Frontend debugging standards
- **DEBUG_FIRST.md** - Quick debugging checklist

---

**Implementation Date**: 2025-10-09
**Author**: Claude Code
**Status**: Production Pattern - Ready for Rollout to All Cue Types
