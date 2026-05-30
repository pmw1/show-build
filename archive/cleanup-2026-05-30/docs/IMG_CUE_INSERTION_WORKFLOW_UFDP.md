# IMG Cue Insertion Workflow - User-Facing Documentation Page

**Created**: 2025-10-03
**Status**: Implementation Complete
**Related Files**: `EditorPanel.vue`, `CuePlacementOverlay.vue`, `ImgCueModal.vue`

## Overview

Complete workflow documentation for IMG cue insertion in Script Mode and Code Mode, including API endpoint requirements, slug normalization rules, and visual feedback specifications.

---

## Script Mode Workflow (6-Step Process)

### Step 1: Trigger Insertion
- **User Action**: Press `ALT+I` or click IMG button
- **System Action**: Detect segment ID from focused paragraph (extracts from `.seg-N` class)

### Step 2: Placement Preview with Flash Animation
- **Duration**: 1000ms (5 flashes at 100ms intervals)
- **Visual**:
  - 5px solid border in **locator color** (cue-specific color)
  - Glowing box-shadow with locator color
  - Background fill with locator color
  - Full opacity during flash
- **Purpose**: Show user where insertion is planned

### Step 3: Flash Message
- **Text**: `Insert IMG CUE`
- **Duration**: 800ms total (300ms display + 500ms fade out)
- **Style**: Full-screen overlay with cue color background

### Step 4: Modal Data Entry
- **Fields**:
  - Slug (required) - becomes cue identifier
  - Image file (required) - uploaded to episode assets
  - Description (optional)
  - Credit (optional)
  - Caption (optional)
- **Validation**:
  - Slug must be unique within episode
  - Slug normalization: lowercase + remove punctuation + **keep spaces**
  - Filename normalization: lowercase + spaces to hyphens + remove punctuation

### Step 5: Asset Generation
- **AssetID Request**: `POST /newAssetID`
  ```json
  {
    "asset_type": "cue",
    "cue_type": "IMG",
    "slug": "user-provided-slug",
    "parent_asset_id": "rundown-item-assetid"
  }
  ```
  Returns: `{"asset_id": "CUEMGAKAUC1PMN9J7"}`

- **Image Upload**: `POST /api/upload/image`
  ```
  FormData:
    - file: <File object>
    - filename: "slug-normalized-name.jpg"  (NO AssetID prefix)
    - episode: "0243"
  ```
  Destination: `/home/episodes/0243/assets/images/slug-normalized-name.jpg`

- **Cue Block Generation**:
  ```
  <!-- Begin Cue -->
  [Type: IMG]
  [AssetID: CUEMGAKAUC1PMN9J7]
  [Slug: test image slug]
  [Description: Optional description]
  [Credit: Photo credit]
  [Caption: Image caption]
  [MediaURL: episodes/0243/assets/images/test-image-slug.jpg]
  <!-- End Cue -->
  ```

### Step 6: Placement Locator
- **Visual Feedback**:
  - Hover over `<p>` regions: dotted border in **Dropline** color, background in **DragLight** color
  - Between-zone regions: invisible zones that snap to mouse position
  - Opacity transitions on hover
- **User Action**: Click to select final placement location
- **Insertion**: Cue block inserted at selected position in raw script content

---

## Code Mode Workflow (Simplified)

### Step 1: Trigger Insertion
- **User Action**: Position cursor, press `ALT+I`
- **System Action**: Store cursor position from `textarea.selectionStart`

### Step 2: Modal Opens Immediately
- No placement overlay preview
- No flash animation
- Direct to modal

### Step 3-4: Same as Script Mode
- AssetID generation
- Image upload
- Cue block generation

### Step 5: Direct Insertion at Cursor
- Insert cue block at stored cursor position
- Add `\n\n` before and after cue block for spacing
- No placement locator needed

---

## Critical API Endpoints

### `/newAssetID` - Generate Cue AssetID
- **Method**: POST
- **Auth**: Required (X-API-Key header)
- **Body**:
  ```json
  {
    "asset_type": "cue",
    "cue_type": "IMG",
    "slug": "user-slug",
    "parent_asset_id": "parent-rundown-item-id"
  }
  ```
- **Returns**: `{"asset_id": "CUEMGAKAUC1PMN9J7"}`

### `/api/upload/image` - Upload IMG Cue Image
- **Method**: POST
- **Auth**: Not required
- **Form Data**:
  - `file`: File object
  - `filename`: Normalized slug filename (e.g., `test-image.jpg`)
  - `episode`: Episode number (e.g., `"0243"`)
- **Destination**: `/home/episodes/{episode}/assets/images/{filename}`
- **Returns**: `{"status": "success", "filepath": "..."}`

**⚠️ IMPORTANT**: This endpoint is `/api/upload/image`, NOT `/api/upload/episode-image`

---

## Slug Normalization Rules

### Cue Block Slug (for [Slug: ...] field)
- **Rule**: Lowercase + remove punctuation + **KEEP SPACES**
- **Example**:
  - Input: `"Test Image! #1"`
  - Output: `"test image 1"`
- **Code**:
  ```javascript
  slug.toLowerCase().replace(/[^a-z0-9\s]/g, '').trim()
  ```

### Filename Slug (for file storage)
- **Rule**: Lowercase + spaces to hyphens + remove punctuation
- **Example**:
  - Input: `"Test Image! #1"`
  - Output: `"test-image-1.jpg"`
- **Code**:
  ```javascript
  slug.toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
  ```

### Duplicate Prevention
- Slugs are extracted from existing cue blocks using regex: `/\[Slug:\s*([^\]]+)\]/gi`
- New slug is compared (case-insensitive) against all existing slugs
- Error thrown if duplicate detected

---

## Color System

### Flash Animation Colors
- **Source**: `getColorValue(cueType.toLowerCase())` from theme system
- **IMG**: Uses IMG locator color
- **FSQ**: Uses FSQ locator color
- **SOT**: Uses SOT locator color
- Each cue type has its own distinctive flash color

### Placement Overlay Colors
- **DragLight**: Background color on hover (light blue by default)
- **Dropline**: Border color (darker blue by default)
- **User Customizable**: These colors are defined in user settings

---

## Key Discoveries

### 1. API Endpoint Mismatch (FIXED)
- **Issue**: Frontend was calling `/api/upload/episode-image`
- **Reality**: Backend endpoint is `/api/upload/image`
- **Impact**: All IMG cue uploads were failing silently
- **Fix**: Updated endpoint URL and form parameter names

### 2. Form Parameter Names
- **Wrong**: `episodeNumber`, `newFilename`, `assetId`
- **Correct**: `episode`, `filename` (assetId not needed)
- **Backend Expects**: Exact parameter names from `Form(...)` decorators

### 3. Filename Convention
- **Old Assumption**: Filename includes AssetID prefix
- **Actual Requirement**: Filename is slug-only, no AssetID
- **Reason**: AssetID is stored in cue block, not in filename
- **Example**: `test-image.jpg` (not `CUEMGA-test-image.jpg`)

### 4. Segment ID Detection
- **Method**: Extract from `.seg-N` class on `.paragraph-content` div
- **Not Cursor Position**: Script mode uses segment IDs, not text cursor positions
- **Code Mode Different**: Code mode uses actual cursor position from textarea

### 5. Placement Overlay Timing
- **Sequence**: Flash animation FIRST (preview) → Flash message → Modal
- **Purpose**: Show user the planned insertion point before opening modal
- **Duration**: 1000ms flash + 800ms message = 1.8s total preview time

---

## Testing Checklist

### Script Mode
- [ ] Press ALT+I with cursor in paragraph
- [ ] Verify 5x flash animation in locator color
- [ ] Verify "Insert IMG CUE" flash message
- [ ] Fill modal with slug and image
- [ ] Verify AssetID generated successfully
- [ ] Verify image uploads to correct directory
- [ ] Verify placement overlay appears with hover effects
- [ ] Click to place cue
- [ ] Verify cue block appears in correct location
- [ ] Verify no duplicate slugs allowed

### Code Mode
- [ ] Switch to code mode
- [ ] Position cursor in textarea
- [ ] Press ALT+I
- [ ] Verify modal opens immediately (no flash/overlay)
- [ ] Fill modal and submit
- [ ] Verify cue inserts at cursor position
- [ ] Verify proper spacing around cue block

### Edge Cases
- [ ] Test with special characters in slug
- [ ] Test with spaces in slug
- [ ] Test duplicate slug rejection
- [ ] Test with missing image file
- [ ] Test with invalid image type
- [ ] Test ESC to cancel at each step

---

## Related Documentation

- [`docs/ASSETID_SYSTEM_GUIDE.md`](docs/ASSETID_SYSTEM_GUIDE.md) - AssetID generation and management
- [`docs/API_ENDPOINTS.md`](docs/API_ENDPOINTS.md) - Complete API reference
- [`SCRIPT_MODE_AS_VIEWER_ARCHITECTURE_UFDP.md`](SCRIPT_MODE_AS_VIEWER_ARCHITECTURE_UFDP.md) - Script mode architecture

---

## Implementation Files

### Frontend
- `disaffected-ui/src/components/content-editor/EditorPanel.vue:2086-2185` - `insertCue()` method
- `disaffected-ui/src/components/content-editor/EditorPanel.vue:2251-2385` - `handleImgCueSubmit()` method
- `disaffected-ui/src/components/content-editor/EditorPanel.vue:3134-3168` - `insertCueAtCursor()` method
- `disaffected-ui/src/components/content-editor/CuePlacementOverlay.vue:304-318` - Flash animation
- `disaffected-ui/src/components/content-editor/CuePlacementOverlay.vue:393-398` - Flash styling

### Backend
- `app/main.py:561-630` - `/api/upload/image` endpoint
- `app/assetid_router.py` - `/newAssetID` endpoint

---

**Last Updated**: 2025-10-03
**Tested**: Pending user verification
**Status**: Ready for production testing
