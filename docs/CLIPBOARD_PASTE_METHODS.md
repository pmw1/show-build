# Clipboard Image Paste Methods - Technical Reference

**Version**: 1.0
**Last Updated**: 2025-11-15
**Related**: `useClipboardImageDetection.js` composable

## Overview

This document provides a comprehensive technical reference for all clipboard image paste methods supported in Show-Build. Each method handles clipboard data differently based on how the image was copied and what browser/platform is being used.

---

## Method 1: Direct Binary Paste

**MIME Type**: `image/png`, `image/jpeg`, `image/gif`, `image/webp`, etc.

**When This Occurs**:
- Screenshots (Windows Snipping Tool, macOS Command+Shift+4, Linux Spectacle)
- Right-click → Copy Image from web browser on actual image files
- Copy from image editing software (Photoshop, GIMP, Paint)

**Data Storage Location**:
- **Clipboard API**: `navigator.clipboard.read()` → `ClipboardItem` → `types` array includes `image/*`
- **Paste Event**: `event.clipboardData.files` or `event.clipboardData.items`

**Example Data Structure**:
```javascript
// Via Clipboard API
const clipboardItems = await navigator.clipboard.read()
// clipboardItems = [ClipboardItem]
// clipboardItem.types = ["image/png"]

const blob = await clipboardItems[0].getType('image/png')
// blob = Blob { size: 245678, type: "image/png" }

// Via Paste Event
event.clipboardData.files
// FileList = [File { name: "", size: 245678, type: "image/png" }]
```

**Example Sources**:
1. Windows Snipping Tool → Copy to clipboard
2. Chrome browser → Right-click image → Copy image
3. Screenshot on macOS (Command+Ctrl+Shift+4)

**Code Implementation**:
```javascript
// composables/useClipboardImageDetection.js: lines 176-206
async function handleDirectBinaryPaste(event) {
  if (navigator.clipboard && navigator.clipboard.read) {
    const clipboardItems = await navigator.clipboard.read()
    for (const item of clipboardItems) {
      for (const type of item.types) {
        if (type.startsWith('image/')) {
          const blob = await item.getType(type)
          const file = new File([blob], 'pasted-image.png', { type })
          return { file, filename: 'pasted-image.png' }
        }
      }
    }
  }
}
```

---

## Method 2: HTML Clipboard Format (Google Docs)

**MIME Type**: `text/html`

**When This Occurs**:
- Copy image from Google Docs
- Copy image from Google Slides
- Copy image from rich text editors (Medium, Notion)
- Microsoft Office Online (Word Online, PowerPoint Online)

**Data Storage Location**:
- **Paste Event**: `event.clipboardData.getData('text/html')`
- **Clipboard API**: `navigator.clipboard.readText()` (for HTML as text)

**Example Data Structure**:
```javascript
// Via Paste Event
const html = event.clipboardData.getData('text/html')
// html = '<meta charset="utf-8"><img src="https://lh3.googleusercontent.com/d/1AbC...xyz" alt="Image" />'

// Parse HTML
const parser = new DOMParser()
const doc = parser.parseFromString(html, 'text/html')
const images = doc.querySelectorAll('img')
const imageUrl = images[0].src
// imageUrl = "https://lh3.googleusercontent.com/d/1AbC...xyz"
```

**Example HTML Content** (Google Docs):
```html
<meta charset='utf-8'>
<img src="https://lh3.googleusercontent.com/d/1AbCdEfGhIjKlMnOpQrStUvWxYz"
     alt="Screenshot 2025-01-15"
     width="800"
     height="600"
     style="border:none;">
```

**Example Sources**:
1. Google Docs → Insert image → Select image → Copy (Ctrl+C)
2. Google Slides → Select image → Copy
3. Notion → Copy embedded image block

**Code Implementation**:
```javascript
// composables/useClipboardImageDetection.js: lines 208-249
async function handleHTMLClipboardPaste(event) {
  let html = event.clipboardData.getData('text/html')

  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')
  const images = doc.querySelectorAll('img')

  if (images.length > 0) {
    const imageUrl = images[0].src

    // Download from URL
    const response = await fetch(imageUrl, { mode: 'cors' })
    const blob = await response.blob()
    const contentType = response.headers.get('content-type') || 'image/png'
    const file = new File([blob], `google-docs-image.png`, { type: contentType })

    return { file, filename: file.name }
  }
}
```

**Multi-Step Process**:
1. **Detect HTML**: Check if `text/html` is in clipboard types
2. **Parse HTML**: Use DOMParser to extract `<img>` tags
3. **Extract URL**: Get `src` attribute from first image
4. **Download**: Fetch image from Google's servers via CORS request
5. **Convert**: Create File object from blob
6. **Process**: Pass to image handler

**Button Status Messages** (300ms minimum each):
- "Downloading from source..."
- "Converting to file..."
- "Processing image..."
- "Image ready!"

---

## Method 3: File Reference Paste

**MIME Type**: `Files` (from DataTransfer)

**When This Occurs**:
- Copy file from file explorer (Windows Explorer, macOS Finder, Linux file manager)
- Drag and drop from desktop
- Copy from email attachments

**Data Storage Location**:
- **Paste Event**: `event.clipboardData.files` (FileList)
- **Drag Event**: `event.dataTransfer.files` (FileList)

**Example Data Structure**:
```javascript
// Via Paste Event
event.clipboardData.files
// FileList = [
//   File {
//     name: "vacation-photo.jpg",
//     size: 2456789,
//     type: "image/jpeg",
//     lastModified: 1705354800000
//   }
// ]
```

**Example Sources**:
1. Windows Explorer → Right-click image file → Copy → Paste in browser
2. macOS Finder → Select .png file → Command+C → Paste
3. Email attachment → Copy → Paste

**Code Implementation**:
```javascript
// Direct file paste detection
if (event.clipboardData.files && event.clipboardData.files.length > 0) {
  for (const file of event.clipboardData.files) {
    if (file.type.startsWith('image/')) {
      return { file, filename: file.name || 'pasted-image.png' }
    }
  }
}
```

---

## Method 4: URL-Embedded Paste

**MIME Type**: `text/plain`

**When This Occurs**:
- Copy image URL from browser address bar
- Copy direct link to image (https://example.com/image.png)
- Copy CDN/cloud storage URLs

**Data Storage Location**:
- **Paste Event**: `event.clipboardData.getData('text/plain')`
- **Clipboard API**: `navigator.clipboard.readText()`

**Example Data Structure**:
```javascript
// Via Paste Event
const url = event.clipboardData.getData('text/plain')
// url = "https://cdn.example.com/images/product-photo.jpg"

// Validate URL pattern
const isImageUrl = url.match(/^https?:\/\/.+\.(jpg|jpeg|png|gif|webp|svg)/i)
// isImageUrl = ["https://cdn.example.com/images/product-photo.jpg", "jpg"]
```

**Example URLs**:
```
https://cdn.example.com/uploads/2025/01/banner.png
https://i.imgur.com/AbC123.jpg
https://example.com/assets/logo.svg
```

**Code Implementation**:
```javascript
// composables/useClipboardImageDetection.js: lines 251-282
async function handleURLEmbeddedPaste(event) {
  let url = event.clipboardData.getData('text/plain')

  if (!url.match(/^https?:\/\/.+\.(jpg|jpeg|png|gif|webp|svg)/i)) {
    throw new Error('No valid image URL found')
  }

  const response = await fetch(url, { mode: 'cors' })
  const blob = await response.blob()
  const filename = url.split('/').pop() || 'url-image.png'
  const file = new File([blob], filename, { type: response.headers.get('content-type') })

  return { file, filename }
}
```

**Multi-Step Process**:
1. **Validate URL**: Check URL format matches image extension pattern
2. **Download**: Fetch from URL
3. **Process**: Convert to File object

**Button Status Messages**:
- "Validating URL..."
- "Downloading..."
- "Processing..."
- "Image ready!"

---

## Method 5: Clipboard Pickling Format (W3C Structured Data)

**MIME Type**: Custom structured data (experimental)

**When This Occurs**:
- Future browser implementations
- Web applications using structured clipboard API
- Custom data formats with image embedding

**Data Storage Location**:
- **Clipboard API**: `navigator.clipboard.read()` → Custom MIME types
- **DataTransfer**: `event.dataTransfer.getData(customType)`

**Example Data Structure** (Theoretical):
```javascript
const clipboardItems = await navigator.clipboard.read()
const customItem = clipboardItems.find(item =>
  item.types.includes('application/vnd.image-plus-metadata')
)

const data = await customItem.getType('application/vnd.image-plus-metadata')
// Structured format containing image + metadata
```

**Status**: Currently planned but not implemented in composable

---

## Detection Priority Order

The composable detects clipboard types in this priority order:

1. **Direct Binary** (fastest, most reliable)
2. **File Reference** (second fastest)
3. **HTML Clipboard** (requires download step)
4. **URL-Embedded** (requires validation + download)
5. **Clipboard Pickling** (future)

**Code Reference**:
```javascript
// composables/useClipboardImageDetection.js: lines 113-127
if (types.includes(PASTE_TYPES.DIRECT_BINARY)) {
  primaryType.value = PASTE_TYPES.DIRECT_BINARY
} else if (types.includes(PASTE_TYPES.FILE_REFERENCE)) {
  primaryType.value = PASTE_TYPES.FILE_REFERENCE
} else if (types.includes(PASTE_TYPES.HTML_CLIPBOARD)) {
  primaryType.value = PASTE_TYPES.HTML_CLIPBOARD
} else if (types.includes(PASTE_TYPES.URL_EMBEDDED)) {
  primaryType.value = PASTE_TYPES.URL_EMBEDDED
}
```

---

## Browser Compatibility

| Method | Chrome | Firefox | Safari | Edge |
|--------|--------|---------|--------|------|
| Direct Binary | ✅ | ✅ | ✅ | ✅ |
| HTML Clipboard | ✅ | ✅ | ⚠️ | ✅ |
| File Reference | ✅ | ✅ | ✅ | ✅ |
| URL-Embedded | ✅ | ✅ | ✅ | ✅ |
| Clipboard Pickling | ❌ | ❌ | ❌ | ❌ |

**Notes**:
- ⚠️ Safari: HTML clipboard may require additional CORS handling
- All browsers require HTTPS for Clipboard API access
- Clipboard permissions may prompt user on first use

---

## Testing Each Method

### Test Direct Binary:
1. Take screenshot (Windows+Shift+S, Command+Shift+4, PrintScreen)
2. Open Show-Build IMG modal
3. Click "Paste from Clipboard"
4. Expected: "Paste Direct Image" button label

### Test HTML Clipboard (Google Docs):
1. Open Google Doc with embedded image
2. Select image → Copy (Ctrl+C)
3. Open Show-Build IMG modal
4. Click button (should show "Paste HTML Clipboard Image")
5. Watch status: "Downloading from source..." → "Processing..."

### Test File Reference:
1. Copy image file from file explorer (Right-click → Copy)
2. Open Show-Build IMG modal
3. Paste (Ctrl+V)
4. Expected: "Paste File Image" button label

### Test URL-Embedded:
1. Copy image URL: `https://i.imgur.com/example.jpg`
2. Open Show-Build IMG modal
3. Paste (Ctrl+V)
4. Watch status: "Validating URL..." → "Downloading..." → "Processing..."

---

## Debugging

### Enable Console Logging:
All paste methods include comprehensive console logging:

```javascript
console.log('🔍 Probing clipboard for image types...')
console.log('✓ Found direct binary image:', type)
console.log('📄 Handling HTML clipboard paste')
console.log('🔗 Handling URL-embedded paste')
```

### Common Issues:

**"No image found on clipboard"**:
- Clipboard is empty
- Image not properly copied
- Browser clipboard permissions denied

**"Failed to download image: CORS error"**:
- Google Docs image URL blocked by CORS
- Solution: Right-click image → Save As → Use "Select File" button

**"Clipboard access denied by browser"**:
- Browser needs HTTPS for Clipboard API
- User must grant clipboard permissions
- Fallback: Use Ctrl+V paste event instead

---

## File Locations

**Composable**: `/mnt/process/show-build/disaffected-ui/src/composables/useClipboardImageDetection.js`
**Implementation**: `/mnt/process/show-build/disaffected-ui/src/components/content-editor/modals/ImgCueModal.vue`
**Documentation**:
- Technical Reference: `/mnt/process/show-build/docs/CLIPBOARD_PASTE_METHODS.md`
- Usage Guide: `/mnt/process/show-build/docs/CLIPBOARD_IMAGE_DETECTION_USAGE_GUIDE.md`

## Potential Integration Points (Experimental - Untested)

This clipboard detection system could be integrated into the following Show-Build components, but these integrations are **experimental and have not been tested**:

### High Priority (Similar Use Cases to IMG Cues)
- **GFX Cue Modals** - Graphics insertion modals
- **Profile Picture Upload** (`ProfileView.vue`) - User avatars
- **Asset Browser** (`AssetBrowserModal.vue`) - Media asset ingestion

### Medium Priority (Requires Workflow Analysis)
- **SOT Thumbnails** (`SotModal.vue`) - Video clip thumbnails
- **Show/Episode Thumbnails** (`ShowEdit.vue`) - Master artwork
- **Media Repository** - Bump/Sting graphics upload

### Low Priority (Exploratory)
- **Speaker Profiles** - Speaker image uploads
- **Organization Branding** - Logo/branding images
- **Scratchpad** (`ScratchpadView.vue`) - Whiteboard image embedding

### Universal LLM Framework Integration (Experimental)
The clipboard system could potentially integrate with:
- **LLM Vision Analysis** - Paste images for AI analysis
- **Multimodal Prompts** - Image + text prompts to LLMs
- **Asset Annotation** - Quick image paste for AI-assisted tagging

**⚠️ Warning**: These integrations are speculative and untested. Production use would require:
- Thorough testing in target context
- CORS validation for Google Docs images
- Browser compatibility verification
- Performance testing with large images
- Error handling customization
- User workflow validation

---

## References

- **W3C Clipboard API**: https://w3c.github.io/clipboard-apis/
- **MDN Clipboard API**: https://developer.mozilla.org/en-US/docs/Web/API/Clipboard_API
- **Clipboard Pickling**: https://github.com/w3c/editing/blob/gh-pages/docs/clipboard-pickling/explainer.md
- **Google Docs Clipboard Behavior**: https://superuser.com/questions/413115/

---

**End of Document**
