<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="600" persistent>
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="purple">mdi-image-outline</v-icon>
        Create GFX Item
        <v-spacer></v-spacer>
        <v-btn icon size="small" variant="text" @click="cancel">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-card-text class="pb-2">
        <v-form ref="gfxFormRef" v-model="formValid">
          <!-- Slug (required) -->
          <v-text-field
            v-model="formData.slug"
            label="Slug"
            placeholder="short-descriptive-name"
            :rules="slugRules"
            required
            variant="outlined"
            density="comfortable"
            class="mb-3"
          >
            <template #append-inner>
              <span class="text-error">*</span>
            </template>
          </v-text-field>

          <!-- Title -->
          <v-text-field
            v-model="formData.title"
            label="Title"
            placeholder="GFX Title"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />

          <!-- Duration -->
          <v-text-field
            v-model="formData.duration"
            label="Duration (HH:MM:SS:FF)"
            placeholder="00:00:00:00"
            :rules="durationRules"
            variant="outlined"
            density="comfortable"
            class="mb-3"
          />

          <!-- Image Selection -->
          <div class="mb-4">
            <v-label class="text-subtitle-2 mb-2">Select Image <span class="text-error">*</span></v-label>
            
            <div class="d-flex gap-2 mb-3">
              <v-btn
                @click="handleClipboardPaste"
                color="primary"
                variant="outlined"
                prepend-icon="mdi-clipboard-outline"
              >
                Paste from Clipboard
              </v-btn>
              
              <v-btn
                @click="$refs.gfxFileInput.click()"
                color="secondary"
                variant="outlined"
                prepend-icon="mdi-folder-open"
              >
                Browse Files
              </v-btn>
            </div>

            <!-- Hidden file input -->
            <input
              ref="gfxFileInput"
              type="file"
              accept="image/*"
              @change="handleFileSelect"
              style="display: none;"
            />

            <!-- Image Preview -->
            <div v-if="imagePreview" class="image-preview-container">
              <v-img
                :src="imagePreview"
                max-width="300"
                max-height="200"
                class="rounded"
              />
              <v-chip
                size="small"
                color="success"
                class="mt-2"
              >
                {{ imageSource }}
              </v-chip>
            </div>

            <v-alert
              v-if="imageError"
              type="error"
              variant="tonal"
              class="mt-2"
            >
              {{ imageError }}
            </v-alert>
          </div>

          <!-- Description -->
          <v-textarea
            v-model="formData.description"
            label="Description"
            placeholder="Optional description of the graphic"
            variant="outlined"
            rows="3"
            auto-grow
            class="mb-3"
          />

          <!-- Error Display -->
          <v-alert
            v-if="error"
            type="error"
            variant="tonal"
            class="mb-3"
          >
            {{ error }}
          </v-alert>
        </v-form>
      </v-card-text>
      
      <v-card-actions class="px-6 pb-4">
        <v-spacer></v-spacer>
        <v-btn color="secondary" @click="cancel" variant="outlined">
          Cancel
        </v-btn>
        <v-btn 
          color="purple" 
          @click="createGFXItem"
          :disabled="!formValid || !hasImage"
          :loading="loading"
          variant="elevated"
          class="ml-2"
        >
          <v-icon left>mdi-plus</v-icon>
          Create GFX Item
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'NewGFXModal',
  emits: ['update:show', 'submit'],
  props: {
    show: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      formValid: false,
      loading: false,
      error: '',
      imageError: '',
      imagePreview: null,
      imageSource: '',
      imageBlob: null,
      imageExtension: '',
      formData: {
        slug: '',
        title: '',
        duration: '00:00:00:00',
        description: '',
        type: 'gfx',
        status: 'draft'
      }
    }
  },
  computed: {
    hasImage() {
      return !!this.imageBlob
    },
    slugRules() {
      return [
        v => !!v || 'Slug is required',
        v => /^[a-z0-9-]+$/.test(v) || 'Slug must contain only lowercase letters, numbers, and hyphens'
      ]
    },
    durationRules() {
      return [
        v => !v || /^\d{2}:\d{2}:\d{2}:\d{2}$/.test(v) || 'Duration must be in HH:MM:SS:FF format'
      ]
    }
  },
  mounted() {
    // Add ESC key listener
    document.addEventListener('keydown', this.handleKeydown)
    
    // Add Ctrl+V listener for clipboard paste
    document.addEventListener('keydown', this.handleGlobalKeydown)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown)
    document.removeEventListener('keydown', this.handleGlobalKeydown)
  },
  methods: {
    handleKeydown(event) {
      if (event.key === 'Escape' && this.show) {
        this.cancel()
      }
    },
    
    handleGlobalKeydown(event) {
      if (event.ctrlKey && event.key === 'v' && this.show) {
        event.preventDefault()
        this.handleClipboardPaste()
      }
    },

    async handleClipboardPaste() {
      this.imageError = ''
      
      try {
        const clipboardItems = await navigator.clipboard.read()
        
        for (const clipboardItem of clipboardItems) {
          for (const type of clipboardItem.types) {
            if (type.startsWith('image/')) {
              const blob = await clipboardItem.getType(type)
              const extension = type.split('/')[1] || 'png'
              
              // Store blob and show preview
              this.imageBlob = blob
              this.imageExtension = extension
              this.imagePreview = URL.createObjectURL(blob)
              this.imageSource = 'Clipboard'
              
              this.$toast.success('Image pasted from clipboard!')
              return
            }
          }
        }
        
        this.imageError = 'No image found in clipboard'
      } catch (error) {
        console.error('Clipboard paste error:', error)
        this.imageError = 'Failed to access clipboard. Please try manually.'
      }
    },

    handleFileSelect(event) {
      const file = event.target.files[0]
      if (!file) return
      
      this.imageError = ''
      
      if (!file.type.startsWith('image/')) {
        this.imageError = 'Please select an image file'
        return
      }
      
      this.imageBlob = file
      this.imageExtension = file.name.split('.').pop() || 'png'
      this.imagePreview = URL.createObjectURL(file)
      this.imageSource = file.name
      
      this.$toast.success(`File selected: ${file.name}`)
    },

    async createGFXItem() {
      if (!this.$refs.gfxFormRef.validate()) {
        return
      }
      
      if (!this.hasImage) {
        this.error = 'Please select an image'
        return
      }
      
      this.loading = true
      this.error = ''
      
      try {
        // Create the GFX item data
        const gfxItem = {
          ...this.formData,
          // Image will be handled by the parent component
          imageBlob: this.imageBlob,
          imageExtension: this.imageExtension,
          // Additional fields for GFX items
          subtitle: '',
          airdate: '',
          priority: '',
          guests: '',
          tags: '',
          server_message: '',
          customer: '',
          link: ''
        }
        
        // Emit the item creation
        this.$emit('submit', gfxItem)
        
        // Reset form
        this.resetForm()
        
        // Close modal
        this.cancel()
        
      } catch (error) {
        console.error('Error creating GFX item:', error)
        this.error = 'Failed to create GFX item. Please try again.'
      } finally {
        this.loading = false
      }
    },
    
    resetForm() {
      this.formData = {
        slug: '',
        title: '',
        duration: '00:00:00:00',
        description: '',
        type: 'gfx',
        status: 'draft'
      }
      this.imagePreview = null
      this.imageBlob = null
      this.imageExtension = ''
      this.imageSource = ''
      this.error = ''
      this.imageError = ''
      
      // Reset file input
      if (this.$refs.gfxFileInput) {
        this.$refs.gfxFileInput.value = ''
      }
    },

    cancel() {
      this.resetForm()
      this.$emit('update:show', false)
    }
  }
}
</script>

<style scoped>
.image-preview-container {
  border: 2px dashed #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.v-img {
  border: 1px solid #e0e0e0;
}
</style>