# Cue Block Insertion Protocol (UFDP)

**Universal Frontend Design Pattern for Content Editor Cue Insertion**

## Overview

This document defines the standardized user interaction protocol for inserting cue blocks (VO, NAT, PKG, SOT, IMG, GFX, FSQ, etc.) into script content within the Show-Build Content Editor. All cue types follow this unified workflow to provide consistent, predictable user experience.

## Protocol Specification

### 1. Modal Trigger Animation

When a user initiates cue insertion (via keyboard shortcut or button click):

- The entire screen flashes briefly with the color assigned to that cue type in the theme configuration
- Flash duration: 250ms (fast, non-intrusive)
- Color source: Dynamic from `themeColorMap.js` - changes when user updates color settings
- **No hardcoded colors** - all colors pulled from configuration

**Technical Implementation:**
- `useScreenFlash.js` composable
- `ScreenFlash.vue` component
- `EditorPanel.vue` triggers flash before opening modal

### 2. Modal Color Theming

The modal itself uses the cue type's configured color with appropriate contrast:

- **Header Background**: Full cue type color (e.g., deep-orange for VO, light-green for NAT)
- **Modal Background**: 80% lightened version of cue color for readability
- **Text Color**: Automatically contrasted (white on dark headers, dark on light backgrounds)
- Colors update dynamically when changed in Settings

**Technical Implementation:**
- `cueModalMixin.js` provides `modalStyles` and `headerStyles` computed properties
- Automatic color lightening algorithm in mixin

### 3. ESC Key Abort Behavior

While the modal is open, pressing ESC will:

- Immediately close the modal
- Trigger a full-screen flash with red "ABORT" message in capital letters
- Message style: Same urgent flash style as used for modal launch
- Duration: 500ms
- Color: Red (#F44336)
- This cancels the entire cue insertion process

**Technical Implementation:**
- `cueModalMixin.js` provides `handleAbort()` method
- `useScreenFlash.flashUrgent()` displays abort message

### 4. Auto-Focus Slug Field

When the modal opens:

- Cursor is automatically placed in the slug field (for cue types that have a slug field)
- User can immediately begin typing without clicking
- Reduces friction and speeds up workflow
- Exception: Cue types without slug fields will focus the first available input

**Technical Implementation:**
- `cueModalMixin.js` provides `focusSlugField()` method
- Triggered in `$nextTick()` after modal renders
- Uses `ref="slugField"` on slug input elements

### 5. Shift+Enter Submit Shortcut

While in the modal:

- Pressing Shift+Enter submits the form (equivalent to clicking the Insert/Submit button)
- Only works when required fields are filled
- Provides keyboard-only workflow option
- Button labels display the shortcut: "Submit (Shift+Enter)"

**Technical Implementation:**
- `cueModalMixin.js` keyboard event handler
- Calls `handleSubmit()` method when Shift+Enter detected

### 6. Drop Locator Activation

Once the insertion logic is triggered (via Submit button or Shift+Enter):

- Modal disappears immediately
- Drop locator overlay activates using the same animation logic as the rundown panel drag-and-drop
- The selector highlights two types of insertion zones:
  - **Between-paragraph zones**: Spaces between paragraphs
  - **Paragraph zones**: Within existing paragraph content
- **Snap behavior**: Selector always highlights one zone - never shows "nothing highlighted"
- Highlighting follows mouse movement OR keyboard arrow keys
- User scrolling automatically recalculates zone positions

**Technical Implementation:**
- `CuePlacementOverlay.vue` component
- Two-phase system: Phase 1 (zone selection), Phase 2 (character-level cursor)
- `selectedZoneIndex` state ensures always-highlighted behavior

### 7. Drop Locator Visual Styling

The drop locator uses theme-configured colors for consistency:

- **Shadow**: Cast using the `draglight` color from theme configuration
- **Border**: Dotted line using the `dragline` color from theme configuration
- **Margins**: Forces 1em top and 1em bottom margin to visually push surrounding elements away
- This creates clarity and focus on the insertion target

**Visual Details:**
- Non-highlighted zones: 2px dotted border, transparent background
- Highlighted zones: 3px dotted border, draglight background color, shadow effect
- Zone labels appear only when highlighted
- Smooth transitions between zones

**Technical Implementation:**
- CSS in `CuePlacementOverlay.vue`
- Uses `#B2EBF2` (draglight) for shadow and background
- Uses `#4CAF50` (dragline) for dotted border
- `margin: 1em 0;` applied to all zones

### 8. ESC Abort During Placement

While the drop locator is active:

- Pressing ESC will abort the entire process
- Triggers urgent flash with "ABORT" message in red capitals
- Clears all pending cue data and closes the placement overlay
- Returns user to normal editing mode

**Technical Implementation:**
- `handleKeydown()` method in `CuePlacementOverlay.vue`
- `flashUrgent('ABORT', '#F44336', 500)` called on ESC

### 9. Keyboard Navigation in Placement Mode

While the drop locator is active, keyboard controls provide mouse-free operation:

- **↑ (Up Arrow)**: Navigate to previous zone
- **↓ (Down Arrow)**: Navigate to next zone
- **Enter or Shift+Enter**: Confirm current zone selection and insert cue
- **ESC**: Abort entire process (see #8 above)

**Behavior:**
- Arrow keys update `selectedZoneIndex` and auto-scroll zone into view
- Navigation wraps at boundaries (can't go beyond first/last zone)
- Current zone is always highlighted

**Technical Implementation:**
- `navigateUp()`, `navigateDown()`, `confirmCurrentZone()` methods
- `scrollZoneIntoView()` ensures selected zone is visible

### 10. Between-Paragraph Insertion (Simple Path)

If the user selects a space between paragraphs:

- This is the simple insertion path
- Cue block is inserted exactly at the selected location (between the two paragraphs)
- Process completes immediately
- Content auto-saves

**Technical Implementation:**
- `handleBetweenZoneClick()` method
- Emits `place-cue` event with `type: 'between'` and zone index
- `EditorPanel.insertCueBetweenParagraphs()` performs insertion

### 11. Within-Paragraph Insertion (Character-Level Path)

If the user selects a paragraph itself:

- System enters Phase 2: Character-level cursor placement
- A small drop locator (cursor-sized, approximately 3px wide × 20px tall) appears
- User can position cursor with precision inside the paragraph using:
  - **Mouse movement**: Cursor follows horizontal mouse position
  - **Click**: Confirms insertion at cursor position
- Character at cursor position is "pushed" (highlighted) to show where cue will insert
- Overlay shows live preview of text split

**Technical Implementation:**
- Phase 2 mode in `CuePlacementOverlay.vue`
- Orange cursor (`#ff6600`) with blinking animation
- `handleCharacterMouseMove()` calculates position
- `handleCharacterClick()` confirms insertion
- Character offset passed to insertion logic

## Workflow Summary

```
User Action → Screen Flash (Cue Color)
           → Modal Opens (Themed with Cue Color)
           → Auto-Focus Slug Field
           → User Fills Form
           → [Shift+Enter OR Click Submit]
           → Modal Closes
           → Drop Locator Activates (First Zone Auto-Selected)
           → User Navigates (Mouse/Arrow Keys)
           → User Confirms (Click/Enter)
           → [IF Between-Paragraph] → Insert Cue → Complete
           → [IF Within-Paragraph] → Character Cursor → Click Position → Insert Cue → Complete

           → [ESC at any point] → Red "ABORT" Flash → Cancel Process
```

## Design Principles

1. **Consistency**: All cue types use identical workflow
2. **Visual Feedback**: Color-coded flashes and themed modals provide clear state indication
3. **Keyboard First**: Complete workflow possible without mouse
4. **Always Highlighted**: User always knows where action will occur
5. **Dynamic Theming**: Colors adapt to user preferences in real-time
6. **Undo-Friendly**: Clear abort mechanism at every stage
7. **Minimal Friction**: Auto-focus and keyboard shortcuts reduce clicks/actions

## Color Configuration

All colors are stored in `themeColorMap.js` and can be modified via Settings → Color Management:

- **Cue Type Colors**: `vo`, `nat`, `pkg`, `sot`, `img`, `gfx`, `fsq`, etc.
- **System Colors**: `draglight`, `dragline`, `dropline`
- Colors sync to database and update all instances immediately

## Implementation Files

### Components
- `ScreenFlash.vue` - Global flash overlay
- `CuePlacementOverlay.vue` - Drop locator with two-phase insertion
- `VoModal.vue`, `NatModal.vue`, `PkgModal.vue` - Themed cue modals
- `SotModal.vue` - Complex cue modal with custom workflow

### Composables
- `useScreenFlash.js` - Screen flash utilities

### Mixins
- `cueModalMixin.js` - Shared modal behavior (ESC, Shift+Enter, auto-focus, theming)

### Parent Components
- `ContentEditor.vue` - Orchestrates modal opening and cue submission
- `EditorPanel.vue` - Handles cue insertion logic and placement

## Accessibility Notes

- All keyboard shortcuts documented in UI (button labels, tooltips)
- Visual feedback provided at every step (flashes, highlights, cursor)
- Color contrast maintained (lightened backgrounds, contrasting text)
- No reliance on color alone (borders, labels, icons also used)
- Keyboard navigation matches visual layout (top-to-bottom with arrows)

## Future Enhancements

Potential improvements to consider:

- Configurable flash duration in Settings
- Custom flash messages per cue type
- Multi-cue batch insertion workflow
- Preset cue templates
- Recent cue memory/quick-insert
- Drag-and-drop from external sources

---

**Document Version**: 1.0
**Last Updated**: 2025-01-07
**Status**: Implemented and Active
