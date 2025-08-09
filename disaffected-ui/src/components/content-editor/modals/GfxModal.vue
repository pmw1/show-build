<template>
  <v-dialog v-model="show" max-width="600">
    <v-card>
      <v-card-title>Add GFX</v-card-title>
      <v-card-text>
        <v-text-field
          label="Slug"
          v-model="gfxSlug"
          required
        ></v-text-field>
        <v-textarea
          label="Description"
          v-model="gfxDescription"
          rows="3"
          required
        ></v-textarea>
        <div class="d-flex justify-space-between mt-4">
          <v-btn color="primary" @click="pasteFromClipboard">Paste from Clipboard</v-btn>
          <v-btn color="primary" @click="selectFile">Select File</v-btn>
          <v-btn color="primary" @click="pasteUrl">Paste URL</v-btn>
        </div>
        <v-img
          v-if="graphicPreview"
          :src="graphicPreview"
          max-height="200"
          class="mt-4"
        ></v-img>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="submit">Attach</v-btn>
        <v-btn color="secondary" @click="cancel">Cancel</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'GfxModal',
  emits: ['update:show', 'submit'],
  props: {
    show: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      gfxSlug: '',
      gfxDescription: '',
      graphicPreview: null
    }
  },
  methods: {
    pasteFromClipboard() {
      // Clipboard API implementation
      navigator.clipboard.readText().then(text => {
        if (text.startsWith('http')) {
          this.graphicPreview = text
        }
      }).catch(() => {
        // console.warn('Could not read clipboard:', err)
      })
    },
    selectFile() {
      // File input implementation
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = 'image/*'
      input.onchange = (e) => {
        const file = e.target.files[0]
        if (file) {
          const reader = new FileReader()
          reader.onload = (e) => {
            this.graphicPreview = e.target.result
          }
          reader.readAsDataURL(file)
        }
      }
      input.click()
    },
    pasteUrl() {
      const url = prompt('Enter image URL:')
      if (url) {
        this.graphicPreview = url
      }
    },
    submit() {
      this.$emit('submit', {
        type: 'gfx',
        slug: this.gfxSlug,
        description: this.gfxDescription,
        preview: this.graphicPreview
      })
      this.reset()
    },
    cancel() {
      this.$emit('update:show', false)
      this.reset()
    },
    reset() {
      this.gfxSlug = ''
      this.gfxDescription = ''
      this.graphicPreview = null
    }
  },
  watch: {
    show(newVal) {
      if (!newVal) {
        this.reset()
      }
    }
  }
}
</script>
