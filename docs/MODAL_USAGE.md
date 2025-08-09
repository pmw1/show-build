# Modal Usage and Naming Conventions

This document outlines the conventions for creating, naming, and using modals within the Disaffected Production Suite.

## Naming Conventions

To maintain consistency and improve code readability, all modal-related assets should follow these naming patterns:

1.  **Modal Component Files**: PascalCase, ending with `Modal.vue`.
    *   Example: `AssetBrowserModal.vue`, `VoModal.vue`.

2.  **Visibility State Properties**: camelCase, starting with `show` and ending with `Modal`.
    *   Example: `showAssetBrowserModal`, `showVoModal`.

3.  **Event Emitters (to show a modal)**: kebab-case, starting with `show-` and ending with `-modal`.
    *   Example: `@show-asset-browser-modal`, `@show-vo-modal`.

## Implementation Pattern

Modals should be implemented as separate components and imported into the parent view or component where they are used (e.g., `ContentEditor.vue`).

### Parent Component (`ContentEditor.vue`)

1.  **Import**: Import the modal components.
    ```javascript
    import AssetBrowserModal from './modals/AssetBrowserModal.vue';
    import TemplateManagerModal from './modals/TemplateManagerModal.vue';
    ```

2.  **Component Registration**: Register the modals in the `components` object.
    ```javascript
    components: {
      AssetBrowserModal,
      TemplateManagerModal,
      // ... other components
    },
    ```

3.  **Data Properties**: Define data properties to control modal visibility.
    ```javascript
    data() {
      return {
        showAssetBrowserModal: false,
        showTemplateManagerModal: false,
        // ... other data properties
      };
    },
    ```

4.  **Template Usage**: Include the modal component in the template, using props and events to control visibility.
    ```html
    <AssetBrowserModal
      :visible="showAssetBrowserModal"
      @update:visible="showAssetBrowserModal = $event"
      @asset-selected="insertAssetReference"
    />

    <TemplateManagerModal
      :visible="showTemplateManagerModal"
      @update:visible="showTemplateManagerModal = $event"
      @template-selected="insertTemplateReference"
    />
    ```

5.  **Event Handling**: Listen for events from child components (like `EditorPanel.vue`) to toggle modal visibility.
    ```html
    <EditorPanel
      @show-asset-browser-modal="showAssetBrowserModal = true"
      @show-template-manager-modal="showTemplateManagerModal = true"
      ...
    />
    ```

### Modal Component (`ExampleModal.vue`)

Modals should use a `visible` prop and emit an `update:visible` event to allow for two-way binding with the parent.

```vue
<template>
  <v-dialog v-model="dialog" ...>
    <!-- Modal content -->
  </v-dialog>
</template>

<script>
export default {
  name: 'ExampleModal',
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
    // ... other methods
  },
};
</script>
```
