<template>
  <v-dialog v-model="dialog" fullscreen hide-overlay transition="dialog-bottom-transition">
    <v-card>
      <v-toolbar dark color="primary">
        <v-btn icon dark @click="closeModal">
          <v-icon>mdi-close</v-icon>
        </v-btn>
        <v-toolbar-title>Template Manager</v-toolbar-title>
        <v-spacer></v-spacer>
      </v-toolbar>
      <TemplatesView @template-selected="onTemplateSelected" />
    </v-card>
  </v-dialog>
</template>

<script>
import TemplatesView from '@/views/TemplatesView.vue';

export default {
  name: 'TemplateManagerModal',
  components: {
    TemplatesView,
  },
  props: {
    visible: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      dialog: this.visible,
    };
  },
  watch: {
    visible(newVal) {
      this.dialog = newVal;
    },
    dialog(newVal) {
      if (!newVal) {
        this.$emit('update:visible', false);
      }
    },
  },
  methods: {
    closeModal() {
      this.$emit('update:visible', false);
    },
    onTemplateSelected(template) {
      this.$emit('template-selected', template);
      this.closeModal();
    },
  },
};
</script>

<style scoped>
</style>
