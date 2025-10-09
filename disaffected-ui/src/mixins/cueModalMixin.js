import { getColorValue, resolveVuetifyColor } from '@/utils/themeColorMap'
import { useScreenFlash } from '@/composables/useScreenFlash'

/**
 * Mixin for all cue modals to provide consistent behavior:
 * - ESC to abort with red "ABORT" flash
 * - Shift+Enter to submit
 * - Auto-focus slug field
 * - Color theming based on cue type
 */
export const cueModalMixin = {
  props: {
    show: {
      type: Boolean,
      default: false
    },
    cueType: {
      type: String,
      required: true
    }
  },

  data() {
    return {
      keydownHandler: null
    }
  },

  computed: {
    /**
     * Get the base color for this cue type
     */
    cueColor() {
      const colorName = getColorValue(this.cueType.toLowerCase())
      return resolveVuetifyColor(colorName)
    },

    /**
     * Get a lightened version of the cue color for modal background
     */
    cueColorLight() {
      // Convert hex to RGB and lighten by 80%
      const color = this.cueColor
      if (!color || !color.startsWith('#')) return '#f5f5f5'

      const hex = color.replace('#', '')
      const r = parseInt(hex.substring(0, 2), 16)
      const g = parseInt(hex.substring(2, 4), 16)
      const b = parseInt(hex.substring(4, 6), 16)

      // Lighten: move 80% toward white (255)
      const lighten = (c) => Math.round(c + (255 - c) * 0.8)

      const newR = lighten(r).toString(16).padStart(2, '0')
      const newG = lighten(g).toString(16).padStart(2, '0')
      const newB = lighten(b).toString(16).padStart(2, '0')

      return `#${newR}${newG}${newB}`
    },

    /**
     * Modal styles with cue color theming
     */
    modalStyles() {
      return {
        backgroundColor: this.cueColorLight
      }
    },

    /**
     * Header styles with cue color
     */
    headerStyles() {
      return {
        backgroundColor: this.cueColor,
        color: 'white'
      }
    }
  },

  watch: {
    show: {
      handler(newVal) {
        if (newVal) {
          this.setupKeyboardHandlers()
          this.$nextTick(() => {
            this.focusSlugField()
          })
        } else {
          this.removeKeyboardHandlers()
        }
      },
      immediate: true
    }
  },

  mounted() {
    if (this.show) {
      this.setupKeyboardHandlers()
      this.$nextTick(() => {
        this.focusSlugField()
      })
    }
  },

  beforeUnmount() {
    this.removeKeyboardHandlers()
  },

  methods: {
    /**
     * Setup keyboard event handlers for ESC and Shift+Enter
     */
    setupKeyboardHandlers() {
      this.keydownHandler = (event) => {
        // ESC to abort
        if (event.key === 'Escape') {
          event.preventDefault()
          event.stopPropagation()
          this.handleAbort()
          return
        }

        // Shift+Enter to submit
        if (event.shiftKey && event.key === 'Enter') {
          event.preventDefault()
          event.stopPropagation()
          this.handleSubmit()
          return
        }
      }

      document.addEventListener('keydown', this.keydownHandler, true)
    },

    /**
     * Remove keyboard event handlers
     */
    removeKeyboardHandlers() {
      if (this.keydownHandler) {
        document.removeEventListener('keydown', this.keydownHandler, true)
        this.keydownHandler = null
      }
    },

    /**
     * Handle ESC abort - flash "ABORT" in red
     */
    handleAbort() {
      const { flashUrgent } = useScreenFlash()
      flashUrgent('ABORT', '#F44336', 500)

      this.$emit('update:show', false)

      // Emit abort event so parent can clear any pending state
      this.$emit('abort')
    },

    /**
     * Auto-focus the slug field when modal opens
     * Override this method in child components if the field ref name is different
     */
    focusSlugField() {
      const slugField = this.$refs.slugField || this.$refs.slug
      if (slugField) {
        // Handle both v-text-field and native input
        const input = slugField.$el?.querySelector('input') || slugField
        if (input && input.focus) {
          input.focus()
        }
      }
    },

    /**
     * Handle submit - child components must override this
     */
    handleSubmit() {
      console.error('handleSubmit must be implemented by child component')
    }
  }
}
