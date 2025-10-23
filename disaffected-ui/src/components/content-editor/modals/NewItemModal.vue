<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="500">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-plus</v-icon>
        Select Rundown Item Type
        <v-spacer></v-spacer>
        <v-btn icon size="small" variant="text" @click="cancel">
          <v-icon>mdi-close</v-icon>
        </v-btn>
      </v-card-title>
      
      <v-card-text>
        <p class="text-body-2 mb-4">Choose the type of rundown item to create:</p>
        
        <!-- Core Content Types -->
        <div class="mb-4">
          <h6 class="text-h6 mb-2">Core Content</h6>
          <v-row>
            <v-col cols="6" sm="4" v-for="type in coreTypes" :key="type.value">
              <v-btn
                @click="selectType(type)"
                :color="type.color"
                variant="elevated"
                block
                size="large"
                class="text-wrap"
                style="height: 80px;"
              >
                <div class="text-center">
                  <v-icon class="mb-1">{{ type.icon }}</v-icon>
                  <br>
                  <span class="text-caption">{{ type.title }}</span>
                </div>
              </v-btn>
            </v-col>
          </v-row>
        </div>
        
        <!-- Production Types -->
        <div class="mb-4">
          <h6 class="text-h6 mb-2">Production Elements</h6>
          <v-row>
            <v-col cols="6" sm="4" v-for="type in productionTypes" :key="type.value">
              <v-btn
                @click="selectType(type)"
                :color="type.color"
                variant="elevated"
                block
                size="large"
                class="text-wrap"
                style="height: 80px;"
              >
                <div class="text-center">
                  <v-icon class="mb-1">{{ type.icon }}</v-icon>
                  <br>
                  <span class="text-caption">{{ type.title }}</span>
                </div>
              </v-btn>
            </v-col>
          </v-row>
        </div>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="secondary" @click="cancel">Cancel</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'NewItemModal',
  emits: ['update:show', 'submit'],
  props: {
    show: {
      type: Boolean,
      default: false
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    coreTypes() {
      // Essential broadcast rundown types only
      return [
        { title: 'Cold Open', value: 'coldopen', color: 'blue', icon: 'mdi-play-circle-outline' },
        { title: 'Tease', value: 'tease', color: 'pink', icon: 'mdi-eye-outline' },
        { title: 'Segment', value: 'segment', color: 'info', icon: 'mdi-television-classic' },
        { title: 'Promo', value: 'promo', color: 'success', icon: 'mdi-bullhorn' },
        { title: 'Advertisement', value: 'ad', color: 'primary', icon: 'mdi-currency-usd' },
        { title: 'Reader', value: 'reader', color: 'amber-lighten-2', icon: 'mdi-script-text' },
        { title: 'Call to Action', value: 'cta', color: 'accent', icon: 'mdi-hand-pointing-right' },
        { title: 'Break', value: 'break', color: 'brown', icon: 'mdi-pause' }
      ]
    },
    productionTypes() {
      // Production elements
      return [
        { title: 'Interview', value: 'interview', color: 'teal', icon: 'mdi-account-voice' }
      ]
    }
  },
  mounted() {
    // Add ESC key listener to document
    document.addEventListener('keydown', this.handleKeydown)
  },
  beforeUnmount() {
    // Clean up ESC key listener
    document.removeEventListener('keydown', this.handleKeydown)
  },
  methods: {
    handleKeydown(event) {
      // Handle ESC key when modal is open
      if (event.key === 'Escape' && this.show) {
        this.cancel()
      }
    },
    selectType(type) {
      console.log('Selected type:', type);
      
      // Create item with basic defaults - frame-based timecode format (hh:mm:ss:ff)
      // Index will be calculated by ContentEditor based on selection and type
      const item = {
        type: type.value,
        title: type.value === 'tease' ? '' : type.title,  // Tease title should be empty initially
        subtitle: '',
        slug: type.value === 'coldopen' ? 'show-cold-open' : '',
        duration: type.value === 'coldopen' ? '00:00:45:00' : '00:00:00:00',  // Frame-based timecode (hh:mm:ss:ff)
        description: '',
        airdate: '',  // Will be populated from info.md frontmatter
        priority: '',  // Empty as specified
        guests: '',
        tags: '',
        server_message: '',
        customer: '',
        link: '',
        status: 'draft'  // Default status
      };
      
      // Emit the item creation
      this.$emit('submit', item);
      
      // Close modal
      this.cancel();
    },
    cancel() {
      this.$emit('update:show', false);
    }
  }
}
</script>