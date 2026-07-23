<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="600">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="purple-lighten-2">mdi-image</v-icon>
        {{ editData ? 'Edit Image Cue' : 'Insert Image Cue' }}
        <v-spacer></v-spacer>
        <v-btn icon size="small" variant="text" @click="cancel">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-card-text>
        
        <!-- Slug Input -->
        <v-text-field
          v-model="formData.slug"
          label="Slug *"
          placeholder="e.g., un-women-journalists"
          variant="outlined"
          density="comfortable"
          class="mb-4"
          :rules="[rules.required]"
          hint="Unique identifier for this image (no spaces, use hyphens)"
          persistent-hint
          color="error"
          ref="slugInput"
          autofocus
        ></v-text-field>

        <!-- Description Input -->
        <v-text-field
          v-model="formData.description"
          label="Description"
          placeholder="Brief description of the image"
          variant="outlined"
          density="comfortable"
          class="mb-4"
        ></v-text-field>

        <!-- Credit Input -->
        <v-text-field
          v-model="formData.credit"
          label="Photo Credit"
          placeholder="e.g., AP Photo, Reuters, Getty Images"
          variant="outlined"
          density="comfortable"
          class="mb-4"
        ></v-text-field>

        <!-- Caption Input -->
        <v-textarea
          v-model="formData.caption"
          label="Caption"
          placeholder="Image caption for display"
          variant="outlined"
          density="comfortable"
          rows="2"
          class="mb-4"
        ></v-textarea>

        <!-- Image Upload Section -->
        <div class="mb-4">
          <h6 class="text-h6 mb-2">Add Image</h6>
          
          <!-- Image Preview -->
          <div v-if="previewUrl" class="mb-3">
            <v-card variant="outlined" class="pa-2">
              <img
                :src="previewUrl"
                alt="Image preview"
                style="max-width: 100%; max-height: 200px; object-fit: contain;"
                class="mx-auto d-block"
              />
              <div class="d-flex justify-space-between align-center mt-2 px-2">
                <v-chip size="small" color="success">{{ fileName }}</v-chip>
                <v-btn
                  color="error"
                  variant="flat"
                  size="small"
                  @click="clearImage"
                  :prepend-icon="'mdi-delete'"
                  style="color: white;"
                >
                  Clear
                </v-btn>
              </div>
            </v-card>
          </div>

          <!-- Upload Buttons -->
          <div class="d-flex gap-3 justify-center">
            <v-btn
              @click="pasteFromClipboard"
              :color="clipboardDetection.buttonColor.value"
              variant="outlined"
              :prepend-icon="'mdi-clipboard-outline'"
              :loading="clipboardDetection.isProcessing.value"
              :disabled="!!previewUrl"
              ref="pasteTarget"
              tabindex="0"
            >
              {{ clipboardDetection.buttonLabel.value }}
              <v-tooltip activator="parent" location="bottom">
                {{ pasteShortcut }} - {{ clipboardDetection.statusMessage.value || 'Paste image from clipboard' }}
              </v-tooltip>
            </v-btn>

            <v-btn
              @click="selectFile"
              color="primary"
              variant="outlined"
              :prepend-icon="'mdi-file-image'"
              :disabled="!!previewUrl"
            >
              Select File
              <v-tooltip activator="parent" location="bottom">
                {{ fileSelectShortcut }}
              </v-tooltip>
            </v-btn>
          </div>

          <!-- Hidden file input -->
          <input
            ref="imgFileInput"
            type="file"
            accept="image/*"
            style="display: none"
            @change="handleFileSelect"
          />
        </div>

        <!-- Error Messages -->
        <v-alert
          v-if="errorMessage"
          type="error"
          variant="text"
          class="mb-4"
        >
          {{ errorMessage }}
        </v-alert>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="secondary" @click="cancel">Cancel</v-btn>
        <v-btn
          color="primary"
          @click="submit"
          :disabled="!canSubmit"
          :loading="submitLoading"
        >
          {{ editData ? 'Update IMG Cue' : 'Insert IMG Cue' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios'
import { useRequireEpisode } from '@/composables/useRequireEpisode'
import { useClipboardImageDetection } from '@/composables/useClipboardImageDetection'

export default {
  name: 'ImgCueModal',
  setup() {
    const { requireEpisode } = useRequireEpisode()

    // Initialize clipboard detection composable
    // We'll pass the callback in methods via a ref
    const clipboardDetection = useClipboardImageDetection({
      autoProbeClipboard: false, // We'll manually probe when modal opens
      onImageReady: null // Will be set in methods
    })

    return {
      requireEpisode,
      clipboardDetection
    }
  },
  emits: ['update:show', 'submit'],
  props: {
    show: {
      type: Boolean,
      default: false
    },
    currentEpisode: {
      type: String,
      default: ''
    },
    editData: {
      type: Object,
      default: null
    }
  },
  data() {
    return {
      formData: {
        slug: '',
        description: '',
        credit: '',
        caption: ''
      },
      imageFile: null,
      previewUrl: '',
      fileName: '',
      pasteLoading: false,
      submitLoading: false,
      errorMessage: '',
      temporaryEpisode: null, // For episode requirement callback
      rules: {
        required: value => !!value || 'This field is required'
      }
    }
  },
  computed: {
    canSubmit() {
      // In edit mode, allow submit if slug exists and either we have a new image or an existing preview
      if (this.editData) {
        const result = this.formData.slug.trim() && (this.imageFile || this.previewUrl);
        console.error('🔍 canSubmit (EDIT mode):', {
          result,
          slug: this.formData.slug,
          imageFile: !!this.imageFile,
          previewUrl: !!this.previewUrl
        });
        return result;
      }
      // In create mode, require both slug and new image file
      const result = this.formData.slug.trim() && this.imageFile;
      console.error('🔍 canSubmit (CREATE mode):', {
        result,
        slug: this.formData.slug,
        imageFile: !!this.imageFile,
        imageFileName: this.fileName
      });
      return result;
    },
    isMac() {
      return typeof navigator !== 'undefined' && navigator.platform && navigator.platform.toUpperCase().indexOf('MAC') >= 0
    },
    pasteShortcut() {
      return this.isMac ? 'Cmd+V' : 'Ctrl+V'
    },
    fileSelectShortcut() {
      return this.isMac ? 'Cmd+O' : 'Ctrl+O'
    }
  },
  watch: {
    show(newVal) {
      if (newVal) {
        // Probe clipboard when modal opens to detect available paste types
        this.clipboardDetection.probeClipboard()

        if (this.editData) {
          // Populate form with existing data for editing
          this.formData = {
            slug: this.editData.rawData?.slug || this.editData.slug || '',
            description: this.editData.rawData?.description || '',
            credit: this.editData.rawData?.credit || '',
            caption: this.editData.rawData?.caption || ''
          };

          // Load existing image preview if available
          const mediaUrl = this.editData.rawData?.mediaurl;
          if (mediaUrl) {
            this.previewUrl = mediaUrl;
            this.fileName = mediaUrl.split('/').pop() || 'existing-image';
            // Note: imageFile remains null for existing images (no upload needed)
          }
        } else {
          this.resetForm()
        }

        // Focus the slug input after the modal opens
        this.$nextTick(() => {
          if (this.$refs.slugInput) {
            this.$refs.slugInput.focus()
          }
        })
      }
    }
  },
  mounted() {
    document.addEventListener('keydown', this.handleKeydown)
    document.addEventListener('paste', this.handleGlobalPaste)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown)
    document.removeEventListener('paste', this.handleGlobalPaste)
    if (this.previewUrl && this.previewUrl.startsWith('blob:')) {
      URL.revokeObjectURL(this.previewUrl)
    }
  },
  methods: {
    handleKeydown(event) {
      // Only handle hotkeys when modal is open
      if (!this.show) return

      if (event.key === 'Escape') {
        this.cancel()
        return
      }

      // Paste shortcut (Ctrl+V on Windows/Linux, Cmd+V on Mac)
      const isValidPaste = this.isMac
        ? (event.metaKey && event.key === 'v' && !event.ctrlKey && !event.altKey)
        : (event.ctrlKey && event.key === 'v' && !event.altKey && !event.metaKey)

      if (isValidPaste) {
        // Only trigger if not in a text input/textarea (let normal paste work there)
        if (!['INPUT', 'TEXTAREA'].includes(event.target.tagName)) {
          event.preventDefault()
          if (!this.previewUrl && !this.pasteLoading) {
            this.pasteFromClipboard()
          }
        }
        return
      }

      // File select shortcut (Ctrl+O on Windows/Linux, Cmd+O on Mac)
      const isValidFileSelect = this.isMac
        ? (event.metaKey && event.key === 'o' && !event.ctrlKey && !event.altKey)
        : (event.ctrlKey && event.key === 'o' && !event.altKey && !event.metaKey)

      if (isValidFileSelect) {
        // Only trigger if not in a text input/textarea
        if (!['INPUT', 'TEXTAREA'].includes(event.target.tagName)) {
          event.preventDefault()
          if (!this.previewUrl) {
            this.selectFile()
          }
        }
        return
      }
    },
    
    async pasteFromClipboard() {
      try {
        // Use the composable's intelligent paste detection
        const result = await this.clipboardDetection.pasteImage()

        if (result && result.file) {
          // Process the image file
          await this.processImageFile(result.file, result.filename)
        }
      } catch (error) {
        console.error('Paste failed:', error)
        this.errorMessage = error.message || 'Failed to paste image from clipboard'
      }
    },

    getPasteInstructions() {
      return `Press ${this.pasteShortcut} to paste your image`
    },


    async handleGlobalPaste(event) {
      console.log('Global paste event fired:', {
        modalOpen: this.show,
        target: event.target?.tagName || 'unknown'
      })

      // Only handle paste when modal is open
      if (!this.show) {
        console.log('Ignoring paste - modal not open')
        return
      }

      // Prevent default to handle paste ourselves
      event.preventDefault()

      try {
        // Use the composable's intelligent paste detection
        const result = await this.clipboardDetection.pasteImage(event)

        if (result && result.file) {
          // Process the image file
          await this.processImageFile(result.file, result.filename)
        }
      } catch (error) {
        console.error('Paste failed:', error)
        this.errorMessage = error.message || 'Failed to paste image from clipboard'
      }
    },
    
    selectFile() {
      this.$refs.imgFileInput.click()
    },
    
    async handleFileSelect(event) {
      const file = event.target.files[0]
      if (file) {
        await this.processImageFile(file, file.name)
      }
      // Clear the input so the same file can be selected again
      event.target.value = ''
    },
    
    async processImageFile(file, name) {
      console.error('🖼️ processImageFile called:', { name, type: file.type, size: file.size });

      // Validate file type
      if (!file.type.startsWith('image/')) {
        this.errorMessage = 'Please select a valid image file.'
        console.error('❌ Invalid file type:', file.type);
        return
      }

      // Validate file size (20MB max)
      if (file.size > 20 * 1024 * 1024) {
        this.errorMessage = 'Image file must be smaller than 20MB.'
        console.error('❌ File too large:', file.size);
        return
      }

      // Clear previous image
      if (this.previewUrl && this.previewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(this.previewUrl)
      }

      // Set new image
      this.imageFile = file
      this.fileName = name
      this.previewUrl = URL.createObjectURL(file)
      this.errorMessage = ''

      console.error('✅ Image processed successfully:', {
        fileName: this.fileName,
        imageFile: !!this.imageFile,
        previewUrl: !!this.previewUrl
      });
    },
    
    clearImage() {
      if (this.previewUrl && this.previewUrl.startsWith('blob:')) {
        URL.revokeObjectURL(this.previewUrl)
      }
      this.imageFile = null
      this.previewUrl = ''
      this.fileName = ''
      this.errorMessage = ''
    },
    
    async submit() {
      console.error('🎨 ImgCueModal submit() called');
      console.error('🎨 canSubmit:', this.canSubmit);

      if (!this.canSubmit) {
        console.error('🎨 Submit blocked - canSubmit is false');
        return;
      }

      this.submitLoading = true;
      this.errorMessage = '';

      try {
        console.error('🎨 Generating filename...');
        // Generate sanitized filename from slug
        const fileExtension = this.getFileExtension();
        const sanitizedSlug = this.sanitizeSlug(this.formData.slug);
        const filename = `${sanitizedSlug}.${fileExtension}`;
        console.error('🎨 Filename:', filename);

        // Upload image to episode assets/images directory
        console.error('🎨 Uploading image...');
        const uploadResult = await this.uploadImage(filename);
        console.error('🎨 Upload result:', uploadResult);

        if (!uploadResult.success) {
          // Check if we're waiting for episode selection (not a real error)
          if (uploadResult.message === 'Waiting for episode selection') {
            console.log('⏸️ Upload paused - episode modal will handle retry');
            return; // Don't show error, modal will trigger callback
          }
          console.error('🎨 Upload failed:', uploadResult.error);
          this.errorMessage = uploadResult.error || 'Failed to upload image';
          return;
        }

        // Create IMG cue data (AssetID will be generated by EditorPanel)
        const imgCueData = {
          type: 'IMG',
          slug: this.formData.slug,
          description: this.formData.description,
          credit: this.formData.credit,
          caption: this.formData.caption,
          filename: filename,
          filepath: uploadResult.filepath,
          imageFile: this.imageFile
        };
        console.error('🎨 Created imgCueData:', imgCueData);

        // Emit to parent
        console.error('🎨 Emitting submit event to parent...');
        this.$emit('submit', imgCueData);
        console.error('🎨 Submit event emitted!');

        // Close modal
        this.cancel();
      } catch (error) {
        console.error('🎨 Submit error:', error);
        this.errorMessage = 'Failed to create IMG cue. Please try again.';
      } finally {
        this.submitLoading = false;
      }
    },
    
    async uploadImage(filename) {
      try {
        // Get episode (may trigger modal if not available)
        const episode = this.getCurrentEpisode();
        if (!episode) {
          console.log('⏸️ Upload paused - waiting for episode selection');
          return { success: false, message: 'Waiting for episode selection' };
        }

        // Create FormData for image upload
        const formData = new FormData()
        formData.append('file', this.imageFile)
        formData.append('filename', filename)
        formData.append('episode', episode)

        // Upload to backend
        const response = await axios.post('/api/upload/image', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })

        if (response.data && response.data.status === 'success') {
          return {
            success: true,
            filepath: response.data.filepath,
            filename: response.data.filename
          }
        } else {
          return {
            success: false,
            error: response.data?.message || 'Upload failed'
          }
        }
      } catch (error) {
        console.error('Image upload error:', error)
        return {
          success: false,
          error: error.response?.data?.detail || 'Network error during upload'
        }
      }
    },

    getFileExtension() {
      if (this.imageFile && this.imageFile.type) {
        const mimeType = this.imageFile.type
        if (mimeType === 'image/jpeg') return 'jpg'
        if (mimeType === 'image/png') return 'png'
        if (mimeType === 'image/gif') return 'gif'
        if (mimeType === 'image/webp') return 'webp'
        // Fallback to extracting from MIME type
        return mimeType.split('/')[1] || 'png'
      }
      return 'png' // Default fallback
    },

    sanitizeSlug(slug) {
      return slug
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '') // Remove punctuation except spaces and hyphens
        .replace(/\s+/g, '-') // Convert spaces to hyphens
        .replace(/-+/g, '-') // Collapse multiple hyphens
        .replace(/^-+|-+$/g, '') // Remove leading/trailing hyphens
    },

    getCurrentEpisode() {
      // Use the episode requirement system
      const episode = this.requireEpisode(
        this.currentEpisode,
        'Upload Image',
        (selectedEpisode) => {
          // Callback: retry upload after episode selection
          console.log('📺 Episode selected from modal, retrying upload with:', selectedEpisode);
          // Store the selected episode temporarily
          this.temporaryEpisode = selectedEpisode;
          // Retry the submit
          this.submit();
        }
      );

      // If episode is available, return it
      if (episode) {
        console.log('✅ Episode available for upload:', episode);
        return episode;
      }

      // If we have a temporary episode from the callback, use it
      if (this.temporaryEpisode) {
        const temp = this.temporaryEpisode;
        this.temporaryEpisode = null; // Clear it
        return temp;
      }

      // Episode modal will be shown, return null to abort current operation
      console.log('⏸️ No episode - modal will prompt user');
      return null;
    },

    
    resetForm() {
      this.formData = {
        slug: '',
        description: '',
        credit: '',
        caption: ''
      }
      this.clearImage()
      this.errorMessage = ''
      this.submitLoading = false
      this.pasteLoading = false
    },
    
    cancel() {
      console.error('🚪 ImgCueModal cancel() called - closing modal');
      this.$emit('update:show', false)
    }
  }
}
</script>

<style scoped>
.gap-3 {
  gap: 12px;
}
</style>