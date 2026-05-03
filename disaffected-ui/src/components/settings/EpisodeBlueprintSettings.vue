<template>
  <v-card flat class="episode-blueprint-settings">
    <v-card-title class="d-flex align-center pa-4">
      <v-icon class="me-2">mdi-folder-tree</v-icon>
      Episode Blueprint
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        prepend-icon="mdi-plus"
        size="small"
        @click="openCreateDialog(null)"
      >
        Add Root Directory
      </v-btn>
    </v-card-title>

    <v-card-text>
      <v-alert v-if="error" type="error" class="mb-4" closable @click:close="error = null">
        {{ error }}
      </v-alert>

      <v-alert v-if="!loading && nodes.length === 0" type="info" class="mb-4">
        No blueprint nodes found. Add directories to define the episode folder structure.
      </v-alert>

      <!-- Tree View -->
      <div v-if="loading" class="d-flex justify-center pa-8">
        <v-progress-circular indeterminate color="primary" />
      </div>

      <div v-else class="blueprint-tree">
        <blueprint-tree-node
          v-for="node in rootNodes"
          :key="node.id"
          :node="node"
          :all-nodes="nodes"
          :depth="0"
          @edit="openEditDialog"
          @add-child="openCreateDialog"
          @delete="confirmDelete"
        />
      </div>
    </v-card-text>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="showDialog" max-width="550" persistent>
      <v-card>
        <v-card-title>
          {{ editingNode ? 'Edit Node' : 'Add Directory' }}
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="formData.name"
            label="Name"
            hint="Directory or file name (lowercase, no spaces)"
            persistent-hint
            class="mb-3"
          />
          <v-textarea
            v-model="formData.description"
            label="Description"
            hint="Purpose of this directory — useful for humans and LLMs"
            persistent-hint
            rows="3"
            auto-grow
            class="mb-3"
          />
          <v-select
            v-model="formData.node_type"
            :items="nodeTypes"
            label="Type"
            class="mb-3"
          />
          <v-text-field
            v-model.number="formData.sort_order"
            label="Sort Order"
            type="number"
            class="mb-3"
          />
          <v-switch
            v-model="formData.is_required"
            label="Required"
            color="primary"
            hide-details
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeDialog">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="saving"
            @click="saveNode"
          >
            {{ editingNode ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title>Delete Node</v-card-title>
        <v-card-text>
          Delete <strong>{{ deletingNode?.name }}</strong>?
          <span v-if="getChildren(deletingNode?.id).length > 0">
            This will also delete {{ getChildren(deletingNode?.id).length }} child node(s).
          </span>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">Cancel</v-btn>
          <v-btn color="error" :loading="saving" @click="deleteNode">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup>
import { ref, computed, onMounted, defineComponent, h } from 'vue'
import axios from 'axios'

// Recursive tree node component
const BlueprintTreeNode = defineComponent({
  name: 'BlueprintTreeNode',
  props: {
    node: { type: Object, required: true },
    allNodes: { type: Array, required: true },
    depth: { type: Number, default: 0 }
  },
  emits: ['edit', 'add-child', 'delete'],
  setup(props, { emit }) {
    const expanded = ref(true)

    const children = computed(() =>
      props.allNodes
        .filter(n => n.parent_id === props.node.id)
        .sort((a, b) => a.sort_order - b.sort_order)
    )

    const hasChildren = computed(() => children.value.length > 0)

    const icon = computed(() => {
      if (props.node.node_type === 'file') return 'mdi-file-outline'
      return expanded.value ? 'mdi-folder-open' : 'mdi-folder'
    })

    return () => {
      const nodeRow = h('div', {
        class: 'blueprint-node d-flex align-center py-1 px-2 rounded',
        style: { paddingLeft: `${props.depth * 24 + 4}px` }
      }, [
        // Expand/collapse toggle
        h('v-btn', {
          icon: true,
          variant: 'text',
          size: 'x-small',
          class: 'me-1',
          style: { visibility: hasChildren.value ? 'visible' : 'hidden' },
          onClick: () => { expanded.value = !expanded.value }
        }, () => [h('v-icon', { size: 'small' }, () => expanded.value ? 'mdi-chevron-down' : 'mdi-chevron-right')]),
        // Folder/file icon
        h('v-icon', { size: 'small', class: 'me-2', color: props.node.node_type === 'directory' ? 'amber' : 'grey' }, () => icon.value),
        // Name
        h('span', { class: 'font-weight-medium me-2' }, props.node.name),
        // Description preview
        props.node.description
          ? h('span', { class: 'text-grey text-caption text-truncate', style: { maxWidth: '400px' } }, props.node.description)
          : h('span', { class: 'text-grey-darken-1 text-caption font-italic' }, 'No description'),
        h('v-spacer'),
        // Required badge
        props.node.is_required
          ? h('v-chip', { size: 'x-small', color: 'success', variant: 'tonal', class: 'me-1' }, () => 'required')
          : null,
        // Actions
        h('v-btn', {
          icon: 'mdi-pencil-outline',
          variant: 'text',
          size: 'x-small',
          onClick: (e) => { e.stopPropagation(); emit('edit', props.node) }
        }),
        props.node.node_type === 'directory'
          ? h('v-btn', {
            icon: 'mdi-plus',
            variant: 'text',
            size: 'x-small',
            onClick: (e) => { e.stopPropagation(); emit('add-child', props.node) }
          })
          : null,
        h('v-btn', {
          icon: 'mdi-delete-outline',
          variant: 'text',
          size: 'x-small',
          color: 'error',
          onClick: (e) => { e.stopPropagation(); emit('delete', props.node) }
        })
      ])

      const childNodes = expanded.value && hasChildren.value
        ? children.value.map(child =>
          h(BlueprintTreeNode, {
            key: child.id,
            node: child,
            allNodes: props.allNodes,
            depth: props.depth + 1,
            onEdit: (n) => emit('edit', n),
            onAddChild: (n) => emit('add-child', n),
            onDelete: (n) => emit('delete', n)
          })
        )
        : []

      return h('div', {}, [nodeRow, ...childNodes])
    }
  }
})

// Auto-register BlueprintTreeNode in script setup
void BlueprintTreeNode

const nodes = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const error = ref(null)
    const showDialog = ref(false)
    const showDeleteDialog = ref(false)
    const editingNode = ref(null)
    const deletingNode = ref(null)
    const parentForCreate = ref(null)
    const nodeTypes = ['directory', 'file']

    const formData = ref({
      name: '',
      description: '',
      node_type: 'directory',
      sort_order: 0,
      is_required: true
    })

    const rootNodes = computed(() =>
      nodes.value
        .filter(n => n.parent_id === null)
        .sort((a, b) => a.sort_order - b.sort_order)
    )

    function getChildren(parentId) {
      if (!parentId) return []
      return nodes.value.filter(n => n.parent_id === parentId)
    }

    function getAuthHeaders() {
      const token = localStorage.getItem('auth-token')
      return token ? { Authorization: `Bearer ${token}` } : {}
    }

    async function loadNodes() {
      loading.value = true
      error.value = null
      try {
        const { data } = await axios.get('/api/settings/blueprint-nodes/', {
          headers: getAuthHeaders()
        })
        nodes.value = data
      } catch (e) {
        error.value = e.response?.data?.detail || 'Failed to load blueprint nodes'
      } finally {
        loading.value = false
      }
    }

    function openCreateDialog(parentNode) {
      editingNode.value = null
      parentForCreate.value = parentNode
      formData.value = {
        name: '',
        description: '',
        node_type: 'directory',
        sort_order: parentNode
          ? getChildren(parentNode.id).length * 10
          : rootNodes.value.length * 10,
        is_required: true
      }
      showDialog.value = true
    }

    function openEditDialog(node) {
      editingNode.value = node
      parentForCreate.value = null
      formData.value = {
        name: node.name,
        description: node.description || '',
        node_type: node.node_type,
        sort_order: node.sort_order,
        is_required: node.is_required
      }
      showDialog.value = true
    }

    function closeDialog() {
      showDialog.value = false
      editingNode.value = null
      parentForCreate.value = null
    }

    async function saveNode() {
      saving.value = true
      error.value = null
      try {
        if (editingNode.value) {
          await axios.put(
            `/api/settings/blueprint-nodes/${editingNode.value.id}`,
            formData.value,
            { headers: getAuthHeaders() }
          )
        } else {
          const payload = {
            ...formData.value,
            parent_id: parentForCreate.value?.id || null
          }
          await axios.post('/api/settings/blueprint-nodes/', payload, {
            headers: getAuthHeaders()
          })
        }
        closeDialog()
        await loadNodes()
      } catch (e) {
        error.value = e.response?.data?.detail || 'Failed to save node'
      } finally {
        saving.value = false
      }
    }

    function confirmDelete(node) {
      deletingNode.value = node
      showDeleteDialog.value = true
    }

    async function deleteNode() {
      if (!deletingNode.value) return
      saving.value = true
      error.value = null
      try {
        await axios.delete(
          `/api/settings/blueprint-nodes/${deletingNode.value.id}`,
          { headers: getAuthHeaders() }
        )
        showDeleteDialog.value = false
        deletingNode.value = null
        await loadNodes()
      } catch (e) {
        error.value = e.response?.data?.detail || 'Failed to delete node'
      } finally {
        saving.value = false
      }
    }

    onMounted(loadNodes)
</script>

<style scoped>
.blueprint-tree {
  font-family: monospace;
}

.blueprint-node:hover {
  background: rgba(255, 255, 255, 0.05);
}
</style>
