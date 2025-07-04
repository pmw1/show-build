<template>
  <v-dialog v-model="show" max-width="600">
    <v-card>
      <v-card-title>Add {{ cueType.toUpperCase() }} ({{ cueTypeLabel }})</v-card-title>
      <v-card-text>
        <v-form ref="cueForm" v-model="formValid">
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="slug"
                label="Slug"
                variant="outlined"
                density="comfortable"
                :rules="slugRules"
                required
              ></v-text-field>
            </v-col>
            
            <v-col cols="12" md="6">
              <v-text-field
                v-model="duration"
                label="Duration"
                variant="outlined"
                density="comfortable"
                placeholder="MM:SS"
                :rules="durationRules"
              ></v-text-field>
            </v-col>
            
            <v-col cols="12">
              <v-textarea
                v-model="description"
                label="Description"
                variant="outlined"
                density="comfortable"
                rows="3"
                auto-grow
                required
                :rules="descriptionRules"
              ></v-textarea>
            </v-col>
            
            <!-- Type-specific fields -->
            <template v-if="cueType === 'sot'">
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="sourceFile"
                  label="Source File"
                  variant="outlined"
                  density="comfortable"
                  hint="Path to video/audio file"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="timecode"
                  label="Timecode"
                  variant="outlined"
                  density="comfortable"
                  placeholder="HH:MM:SS:FF"
                  hint="Start timecode"
                  persistent-hint
                ></v-text-field>
              </v-col>
            </template>
            
            <template v-if="cueType === 'vo'">
              <v-col cols="12">
                <v-textarea
                  v-model="voScript"
                  label="Voice Over Script"
                  variant="outlined"
                  density="comfortable"
                  rows="4"
                  auto-grow
                  hint="Script to be read by talent"
                  persistent-hint
                ></v-textarea>
              </v-col>
            </template>
            
            <template v-if="cueType === 'fsq'">
              <v-col cols="12">
                <v-textarea
                  v-model="quoteText"
                  label="Quote Text"
                  variant="outlined"
                  density="comfortable"
                  rows="3"
                  auto-grow
                  hint="Text to display full screen"
                  persistent-hint
                  required
                  :rules="quoteRules"
                ></v-textarea>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="attribution"
                  label="Attribution"
                  variant="outlined"
                  density="comfortable"
                  hint="Source or author"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="fontStyle"
                  :items="fontStyles"
                  label="Font Style"
                  variant="outlined"
                  density="comfortable"
                ></v-select>
              </v-col>
            </template>
            
            <template v-if="cueType === 'nat'">
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="location"
                  label="Location"
                  variant="outlined"
                  density="comfortable"
                  hint="Where the sound was recorded"
                  persistent-hint
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-select
                  v-model="ambientType"
                  :items="ambientTypes"
                  label="Ambient Type"
                  variant="outlined"
                  density="comfortable"
                ></v-select>
              </v-col>
            </template>
            
            <template v-if="cueType === 'pkg'">
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="reporter"
                  label="Reporter"
                  variant="outlined"
                  density="comfortable"
                ></v-text-field>
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="pkgDuration"
                  label="Package Duration"
                  variant="outlined"
                  density="comfortable"
                  placeholder="MM:SS"
                ></v-text-field>
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="packageNotes"
                  label="Package Notes"
                  variant="outlined"
                  density="comfortable"
                  rows="2"
                  auto-grow
                  hint="Additional production notes"
                  persistent-hint
                ></v-textarea>
              </v-col>
            </template>
          </v-row>
        </v-form>
        
        <!-- Preview -->
        <v-divider class="my-4"></v-divider>
        <v-row>
          <v-col cols="12">
            <h4 class="text-subtitle-1 mb-2">Preview</h4>
            <v-card outlined class="pa-3">
              <div class="cue-preview">
                <v-chip 
                  :color="cueColor" 
                  size="small" 
                  class="mb-2"
                >
                  {{ cueType.toUpperCase() }}
                </v-chip>
                <h5 class="text-subtitle-1">{{ slug || 'Unnamed Cue' }}</h5>
                <p class="text-body-2 mb-2">{{ description || 'No description' }}</p>
                <small class="text-caption text-medium-emphasis">Duration: {{ duration || 'Not specified' }}</small>
              </div>
            </v-card>
          </v-col>
        </v-row>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn 
          color="primary" 
          @click="submit"
          :disabled="!formValid"
        >
          Insert
        </v-btn>
        <v-btn color="secondary" @click="cancel">Cancel</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'CueModal',
  emits: ['update:show', 'submit'],
  props: {
    show: {
      type: Boolean,
      default: false
    },
    cueType: {
      type: String,
      required: true,
      validator: (value) => ['fsq', 'sot', 'vo', 'nat', 'pkg'].includes(value)
    }
  },
  data() {
    return {
      formValid: false,
      slug: '',
      duration: '',
      description: '',
      // SOT specific
      sourceFile: '',
      timecode: '',
      // VO specific
      voScript: '',
      // FSQ specific
      quoteText: '',
      attribution: '',
      fontStyle: 'normal',
      // NAT specific
      location: '',
      ambientType: 'outdoor',
      // PKG specific
      reporter: '',
      pkgDuration: '',
      packageNotes: '',
      
      // Validation rules
      slugRules: [
        v => !!v || 'Slug is required',
        v => (v && v.length >= 2) || 'Slug must be at least 2 characters'
      ],
      descriptionRules: [
        v => !!v || 'Description is required',
        v => (v && v.length >= 5) || 'Description must be at least 5 characters'
      ],
      durationRules: [
        v => !v || /^\d{1,2}:\d{2}$/.test(v) || 'Duration must be in MM:SS format'
      ],
      quoteRules: [
        v => !!v || 'Quote text is required'
      ],
      
      // Select options
      fontStyles: [
        'normal',
        'bold',
        'italic',
        'large',
        'small'
      ],
      ambientTypes: [
        'outdoor',
        'indoor',
        'crowd',
        'traffic',
        'nature',
        'office',
        'restaurant',
        'street',
        'other'
      ]
    }
  },
  computed: {
    cueTypeLabel() {
      const labels = {
        fsq: 'Full Screen Quote',
        sot: 'Sound on Tape',
        vo: 'Voice Over',
        nat: 'Natural Sound',
        pkg: 'Package'
      }
      return labels[this.cueType] || this.cueType
    },
    cueColor() {
      const colors = {
        fsq: 'green-darken-3',
        sot: 'purple-darken-3',
        vo: 'deep-orange-darken-3',
        nat: 'teal-darken-3',
        pkg: 'red-darken-3'
      }
      return colors[this.cueType] || 'grey'
    }
  },
  methods: {
    submit() {
      const baseData = {
        type: this.cueType,
        slug: this.slug,
        duration: this.duration,
        description: this.description
      }
      
      // Add type-specific data
      const typeSpecificData = {}
      
      if (this.cueType === 'sot') {
        typeSpecificData.sourceFile = this.sourceFile
        typeSpecificData.timecode = this.timecode
      } else if (this.cueType === 'vo') {
        typeSpecificData.script = this.voScript
      } else if (this.cueType === 'fsq') {
        typeSpecificData.quoteText = this.quoteText
        typeSpecificData.attribution = this.attribution
        typeSpecificData.fontStyle = this.fontStyle
      } else if (this.cueType === 'nat') {
        typeSpecificData.location = this.location
        typeSpecificData.ambientType = this.ambientType
      } else if (this.cueType === 'pkg') {
        typeSpecificData.reporter = this.reporter
        typeSpecificData.pkgDuration = this.pkgDuration
        typeSpecificData.notes = this.packageNotes
      }
      
      this.$emit('submit', { ...baseData, ...typeSpecificData })
      this.reset()
    },
    cancel() {
      this.$emit('update:show', false)
      this.reset()
    },
    reset() {
      this.slug = ''
      this.duration = ''
      this.description = ''
      this.sourceFile = ''
      this.timecode = ''
      this.voScript = ''
      this.quoteText = ''
      this.attribution = ''
      this.fontStyle = 'normal'
      this.location = ''
      this.ambientType = 'outdoor'
      this.reporter = ''
      this.pkgDuration = ''
      this.packageNotes = ''
      this.formValid = false
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

<style scoped>
.cue-preview {
  min-height: 80px;
}
</style>
