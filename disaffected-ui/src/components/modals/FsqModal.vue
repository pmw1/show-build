<template>
  <v-dialog :model-value="show" @update:model-value="$emit('update:show', $event)" max-width="600">
    <v-card>
      <v-card-title>Add FSQ (Full Screen Quote)</v-card-title>
      <v-card-text>
        <!-- FSQ fields will be populated based on user's next message -->
        <p class="text-caption">FSQ modal fields coming soon...</p>
      </v-card-text>
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn color="primary" @click="$emit('submit')">Insert</v-btn>
        <v-btn color="secondary" @click="$emit('update:show', false)">Cancel</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
export default {
  name: 'FsqModal',
  props: {
    show: { type: Boolean, required: true },
  },
  emits: ['update:show', 'submit'],
};
</script>
