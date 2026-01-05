# Clipboard Image Detection - Usage Guide

**For Developers**: Quick start guide for using `useClipboardImageDetection` composable

---

## Quick Start

### 1. Import the Composable

```javascript
import { useClipboardImageDetection } from '@/composables/useClipboardImageDetection'
```

### 2. Initialize in Your Component

```javascript
export default {
  setup() {
    const clipboardDetection = useClipboardImageDetection({
      onImageReady: (file, filename) => {
        // Handle the processed image file
        console.log('Image ready:', filename, file)
      },
      autoProbeClipboard: true,  // Auto-detect on mount
      minStepDuration: 300        // Minimum ms per status message
    })

    return {
      clipboardDetection
    }
  }
}
```

### 3. Use in Your Template

```vue
<template>
  <v-btn
    @click="clipboardDetection.pasteImage()"
    :color="clipboardDetection.buttonColor.value"
    :loading="clipboardDetection.isProcessing.value"
  >
    {{ clipboardDetection.buttonLabel.value }}
  </v-btn>

  <v-alert v-if="clipboardDetection.error.value" type="error">
    {{ clipboardDetection.error.value }}
  </v-alert>
</template>
```

---

## Options API vs Composition API

### Composition API (Recommended)

```javascript
import { useClipboardImageDetection } from '@/composables/useClipboardImageDetection'

export default {
  setup() {
    const { buttonLabel, buttonColor, pasteImage, isProcessing } =
      useClipboardImageDetection({
        onImageReady: (file, filename) => {
          // Handle image
        }
      })

    return { buttonLabel, buttonColor, pasteImage, isProcessing }
  }
}
```

### Options API

```javascript
import { useClipboardImageDetection } from '@/composables/useClipboardImageDetection'

export default {
  setup() {
    const clipboardDetection = useClipboardImageDetection({
      onImageReady: null // Set in methods
    })
    return { clipboardDetection }
  },
  methods: {
    async handlePaste() {
      const result = await this.clipboardDetection.pasteImage()
      if (result) {
        this.processImage(result.file, result.filename)
      }
    }
  }
}
```

---

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `onImageReady` | Function | `null` | Callback when image is ready: `(file, filename) => {}` |
| `autoProbeClipboard` | Boolean | `true` | Auto-detect clipboard types on component mount |
| `minStepDuration` | Number | `300` | Minimum milliseconds to display each status message |

---

## Exposed Properties

### Reactive Refs

| Property | Type | Description |
|----------|------|-------------|
| `detectedTypes` | `Ref<Array>` | Array of detected paste types |
| `primaryType` | `Ref<String>` | Best paste type to use (highest priority) |
| `buttonLabel` | `Ref<String>` | Dynamic button text (e.g., "Paste HTML Clipboard Image") |
| `buttonColor` | `Ref<String>` | Button color state: 'primary', 'info', 'success', 'error' |
| `statusMessage` | `Ref<String>` | Current operation status message |
| `isProcessing` | `Ref<Boolean>` | True when paste operation is in progress |
| `error` | `Ref<String>` | Error message if paste failed |

### Methods

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `pasteImage()` | `event` (optional) | `Promise<{file, filename}>` | Execute paste with detected type |
| `probeClipboard()` | None | `Promise<Array>` | Manually probe clipboard for types |

### Constants

| Constant | Description |
|----------|-------------|
| `PASTE_TYPES` | Object with paste type constants |
| `TYPE_LABELS` | Object mapping types to user-friendly labels |

---

## Complete Example: Image Upload Modal

```vue
<template>
  <v-dialog v-model="show" max-width="600">
    <v-card>
      <v-card-title>Upload Image</v-card-title>

      <v-card-text>
        <!-- Image Preview -->
        <div v-if="imageFile" class="mb-4">
          <img :src="previewUrl" style="max-width: 100%;" />
          <v-chip>{{ fileName }}</v-chip>
        </div>

        <!-- Paste Button with Dynamic Label/Color -->
        <v-btn
          @click="handlePaste"
          :color="clipboardDetection.buttonColor.value"
          :loading="clipboardDetection.isProcessing.value"
          :disabled="!!imageFile"
          block
        >
          {{ clipboardDetection.buttonLabel.value }}

          <!-- Show status in tooltip -->
          <v-tooltip activator="parent">
            {{ clipboardDetection.statusMessage.value || 'Paste image from clipboard' }}
          </v-tooltip>
        </v-btn>

        <!-- Error Display -->
        <v-alert
          v-if="clipboardDetection.error.value"
          type="error"
          class="mt-4"
        >
          {{ clipboardDetection.error.value }}
        </v-alert>
      </v-card-text>

      <v-card-actions>
        <v-btn @click="show = false">Cancel</v-btn>
        <v-btn color="primary" @click="submit" :disabled="!imageFile">
          Upload
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import { useClipboardImageDetection } from '@/composables/useClipboardImageDetection'

export default {
  setup() {
    const clipboardDetection = useClipboardImageDetection({
      autoProbeClipboard: false, // We'll probe when modal opens
      onImageReady: null // Set in methods
    })

    return { clipboardDetection }
  },
  data() {
    return {
      show: false,
      imageFile: null,
      fileName: '',
      previewUrl: ''
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        // Probe clipboard when modal opens
        this.clipboardDetection.probeClipboard()
      } else {
        // Cleanup
        this.reset()
      }
    }
  },
  methods: {
    async handlePaste() {
      try {
        const result = await this.clipboardDetection.pasteImage()

        if (result && result.file) {
          this.imageFile = result.file
          this.fileName = result.filename
          this.previewUrl = URL.createObjectURL(result.file)
        }
      } catch (error) {
        console.error('Paste failed:', error)
      }
    },

    async submit() {
      const formData = new FormData()
      formData.append('image', this.imageFile)

      // Upload to server
      await fetch('/api/upload', {
        method: 'POST',
        body: formData
      })

      this.show = false
    },

    reset() {
      if (this.previewUrl) {
        URL.revokeObjectURL(this.previewUrl)
      }
      this.imageFile = null
      this.fileName = ''
      this.previewUrl = ''
    }
  }
}
</script>
```

---

## Status Message Flow Examples

### HTML Clipboard (Google Docs):
```
"Paste HTML Clipboard Image"  (idle, primary)
     ↓ [User clicks]
"Downloading from source..."   (processing, info) [300ms+]
     ↓
"Converting to file..."        (processing, info) [300ms+]
     ↓
"Processing image..."          (processing, info) [300ms+]
     ↓
"Image ready!"                 (success, success) [300ms]
```

### Direct Binary (Screenshot):
```
"Paste Direct Image"           (idle, primary)
     ↓ [User clicks]
"Processing image..."          (processing, info) [300ms+]
     ↓
"Image ready!"                 (success, success) [300ms]
```

### URL-Embedded:
```
"Paste Image from URL"         (idle, primary)
     ↓ [User clicks]
"Validating URL..."            (processing, info) [300ms+]
     ↓
"Downloading..."               (processing, info) [300ms+]
     ↓
"Processing..."                (processing, info) [300ms+]
     ↓
"Image ready!"                 (success, success) [300ms]
```

---

## Manual vs Automatic Probing

### Automatic (Default)
```javascript
const clipboardDetection = useClipboardImageDetection({
  autoProbeClipboard: true  // Probes on mount
})
// Button label updates automatically when component mounts
```

### Manual (For Modals/Dialogs)
```javascript
const clipboardDetection = useClipboardImageDetection({
  autoProbeClipboard: false  // Don't probe on mount
})

// In modal watch:
watch: {
  show(newVal) {
    if (newVal) {
      this.clipboardDetection.probeClipboard()  // Probe when modal opens
    }
  }
}
```

---

## Error Handling

```javascript
async handlePaste() {
  try {
    const result = await this.clipboardDetection.pasteImage()

    if (result && result.file) {
      // Success - process the image
      this.processImage(result.file, result.filename)
    }
  } catch (error) {
    // Error is automatically set in clipboardDetection.error
    // You can also handle it manually:
    console.error('Paste failed:', error)
    this.$toast.error('Failed to paste image: ' + error.message)
  }
}
```

The composable automatically sets `error.value` when paste fails, so you can display it in your template:

```vue
<v-alert v-if="clipboardDetection.error.value" type="error">
  {{ clipboardDetection.error.value }}
</v-alert>
```

---

## Global Paste Event Handling

The composable automatically listens for global paste events (`Ctrl+V` / `Cmd+V`) when mounted.

To prevent conflicts, you can disable this behavior:

```javascript
// In composable setup (would need to modify composable to add this option)
// Currently it always listens - modify onMounted to conditionally add listener
```

**Current Behavior**: Listens globally for paste events
**Recommended**: Keep global listener active, it will only fire `pasteImage()` when called

---

## Migration from Old Code

### Before (Manual Clipboard Handling):
```javascript
async pasteFromClipboard() {
  try {
    const clipboardItems = await navigator.clipboard.read()
    for (const item of clipboardItems) {
      for (const type of item.types) {
        if (type.startsWith('image/')) {
          const blob = await item.getType(type)
          const file = new File([blob], 'pasted-image.png', { type })
          this.processImage(file)
          return
        }
      }
    }
  } catch (error) {
    // Handle error
  }
}
```

### After (Using Composable):
```javascript
import { useClipboardImageDetection } from '@/composables/useClipboardImageDetection'

setup() {
  const clipboardDetection = useClipboardImageDetection({
    onImageReady: (file, filename) => {
      this.processImage(file, filename)
    }
  })
  return { clipboardDetection }
}

// In template
<v-btn @click="clipboardDetection.pasteImage()">
  {{ clipboardDetection.buttonLabel.value }}
</v-btn>
```

**Benefits**:
- 150+ lines of code eliminated
- Handles 5 paste methods automatically
- Dynamic UI feedback
- Better error handling
- Reusable across components

---

## Best Practices

1. **Probe on Modal Open**: Use `autoProbeClipboard: false` and manually probe when modal opens
2. **Show Status Messages**: Display `statusMessage` in tooltip or below button
3. **Handle Errors**: Always display `error.value` to user
4. **Cleanup Previews**: Use `URL.revokeObjectURL()` when clearing image previews
5. **Disable During Processing**: Bind `:disabled="isProcessing.value"` to prevent duplicate pastes
6. **Use Button Colors**: Bind `:color="buttonColor.value"` for visual feedback

---

## Where to Use This Composable

✅ **Currently Implemented**:
- **ImgCueModal** - IMG cue insertion in Content Editor

✅ **Recommended Future Integration Points** (Experimental - Untested):

### High Priority
1. **GFX Cue Modals** (`src/components/content-editor/modals/GfxCueModal.vue`)
   - Similar to IMG cues, would benefit from intelligent paste detection
   - ⚠️ **Status**: Experimental - Not yet tested

2. **Profile Picture Upload** (`src/views/ProfileView.vue`)
   - User avatar image selection
   - Currently uses file input only
   - ⚠️ **Status**: Experimental - Would require integration testing

3. **Asset Browser Modal** (`src/components/modals/AssetBrowserModal.vue`)
   - Asset upload functionality
   - Could streamline media ingestion
   - ⚠️ **Status**: Experimental - Integration approach TBD

### Medium Priority
4. **SOT Modal Thumbnails** (`src/components/modals/SotModal.vue`)
   - SOT clip thumbnail selection
   - May have specific video thumbnail requirements
   - ⚠️ **Status**: Experimental - Video thumbnail workflow needs analysis

5. **Show/Episode Thumbnail Uploads** (`src/components/ShowEdit.vue`, Episode creation forms)
   - Master artwork and promotional images
   - Could replace/supplement file picker
   - ⚠️ **Status**: Experimental - Needs workflow review

6. **Media Repository Uploads** (Bump/Sting graphics)
   - Media repository asset ingestion
   - Could improve bulk upload workflow
   - ⚠️ **Status**: Experimental - Repository integration untested

### Low Priority (Exploratory)
7. **Speaker Profile Pictures**
   - Speaker metadata image uploads
   - Low frequency use case
   - ⚠️ **Status**: Experimental - Nice-to-have feature

8. **Organization/Show Logos** (Settings/Branding)
   - Branding image uploads
   - Infrequent updates
   - ⚠️ **Status**: Experimental - Low priority

9. **Scratchpad Image Embedding** (`src/views/ScratchpadView.vue`)
   - Quick image paste into notes/planning
   - Would enhance whiteboard functionality
   - ⚠️ **Status**: Experimental - Requires WYSIWYG editor integration

### Integration Considerations

**Before integrating into new components:**
1. Test clipboard detection with component's specific use case
2. Verify CORS handling for Google Docs images
3. Test browser compatibility in target environment
4. Consider file size limits and validation requirements
5. Plan error handling specific to context
6. Test with real user workflows

**UFDP Integration Note:**
This clipboard system could be integrated into Universal LLM Framework workflows where image analysis/annotation is needed. However, this integration is purely experimental and would require:
- Testing with LLM vision models
- CORS handling for remote image URLs
- Integration with existing asset management
- Performance testing with large images

❌ **Not Recommended**:
- Text-only paste operations
- File uploads that aren't images
- Clipboard data that isn't images
- Production use without thorough testing in target context

---

## Troubleshooting

### Button says "No Image Detected"
- Clipboard is empty
- No image copied
- Try copying an image and reopening the modal

### "Clipboard access denied by browser"
- Browser requires HTTPS for Clipboard API
- Grant clipboard permissions when prompted
- Fallback: Use Ctrl+V paste event instead of button click

### Google Docs images fail with CORS error
- Google blocks some cross-origin image requests
- Workaround shown in error message:
  - Right-click image → "Save image as..."
  - Use "Select File" button instead

### Status messages flash too quickly
- Increase `minStepDuration` option (default: 300ms)
- Each step will display for at least that duration

---

## Related Documentation

- **Technical Reference**: `/docs/CLIPBOARD_PASTE_METHODS.md`
- **Composable Source**: `/disaffected-ui/src/composables/useClipboardImageDetection.js`
- **Example Implementation**: `/disaffected-ui/src/components/content-editor/modals/ImgCueModal.vue`

---

**Last Updated**: 2025-11-15
