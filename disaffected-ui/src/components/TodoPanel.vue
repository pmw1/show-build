<template>
  <v-card>
    <v-card-title class="d-flex align-center dash-title dash-drag-handle">
      <v-icon size="small" class="me-2">mdi-clipboard-check</v-icon>
      <span>Task List</span>
      <v-spacer></v-spacer>
      <v-btn
        icon="mdi-plus"
        variant="text"
        size="x-small"
        color="white"
        @click="openAddModal"
      ></v-btn>
      <v-btn
        icon="mdi-refresh"
        variant="text"
        size="x-small"
        color="white"
        @click="refreshTodos"
        :loading="loading"
      ></v-btn>
    </v-card-title>

    <v-card-text class="pa-2">
      <!-- Show completed toggle -->
      <div class="d-flex align-center mb-2">
        <v-switch
          v-model="showCompleted"
          density="compact"
          hide-details
          color="primary"
          label="Show completed"
          class="todo-toggle"
        ></v-switch>
      </div>

      <!-- Unified task list (drag to reorder priority) -->
      <draggable
        v-if="visibleTodos.length > 0"
        :list="visibleTodos"
        item-key="id"
        handle=".todo-drag-handle"
        ghost-class="todo-ghost"
        @end="onDragEnd"
        class="todo-draggable pa-0"
      >
        <template #item="{ element: todo, index }">
        <div
          class="todo-item d-flex align-center"
          :class="index % 2 === 0 ? 'todo-row-blue' : 'todo-row-white'"
        >
          <v-icon size="x-small" class="todo-drag-handle me-1" style="cursor: grab;">mdi-drag-vertical</v-icon>
          <span class="todo-rank me-1">{{ index + 1 }}.</span>
          <v-checkbox
            :model-value="todo.status === 'completed'"
            @update:model-value="toggleTodoStatus(todo)"
            hide-details
            density="compact"
            class="todo-checkbox"
          ></v-checkbox>

          <div
            class="todo-text-truncate flex-grow-1"
            :class="todo.status === 'completed' ? 'text-decoration-line-through text-grey' : ''"
            @click="showFullText(todo)"
          >
            {{ todo.content }}
          </div>

          <div class="d-flex align-center">
            <v-chip
              :color="getPriorityColor(todo.priority)"
              size="x-small"
              variant="flat"
              class="me-1 todo-priority-chip justify-center"
            >
              {{ todo.priority }}
            </v-chip>
            <v-chip
              :color="todo.created_by === 'claude' ? 'deep-purple' : 'secondary'"
              size="x-small"
              variant="tonal"
              class="me-1 todo-user-chip"
              :prepend-icon="todo.created_by === 'claude' ? 'mdi-robot' : 'mdi-account'"
            >
              <span class="todo-user-label">{{ todo.created_by || 'unknown' }}</span>
            </v-chip>
            <v-btn
              icon="mdi-delete"
              variant="text"
              size="x-small"
              @click="deleteTodo(todo.id)"
            ></v-btn>
          </div>
        </div>
        </template>
      </draggable>

      <div v-else class="text-center text-grey py-4 text-caption">
        No tasks
      </div>
    </v-card-text>
  </v-card>

  <!-- Full Text Modal -->
  <v-dialog v-model="textModalOpen" max-width="600" @keydown.esc="textModalOpen = false">
    <v-card>
      <v-card-title class="d-flex align-center">
        <span>Full Text</span>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" size="small" @click="textModalOpen = false"></v-btn>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text style="white-space: pre-wrap; word-break: break-word;">
        <div class="text-body-1 font-weight-medium mb-2">{{ textModalTitle }}</div>
        <div v-if="textModalDescription" class="text-body-2 text-grey-darken-1">{{ textModalDescription }}</div>
        <div v-else class="text-caption text-grey">No description</div>
      </v-card-text>
    </v-card>
  </v-dialog>

  <!-- Add Todo Modal -->
  <v-dialog v-model="showAddModal" max-width="480" @keydown.esc="showAddModal = false">
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon start>mdi-plus-circle</v-icon>
        Add Task
        <v-spacer></v-spacer>
        <v-chip
          :color="isKnownUser ? 'secondary' : 'grey'"
          size="small"
          variant="tonal"
          prepend-icon="mdi-account"
          class="me-2"
        >
          {{ currentUsername }}
        </v-chip>
        <v-btn icon="mdi-close" variant="text" size="small" @click="closeAddModal"></v-btn>
      </v-card-title>
      <v-divider></v-divider>
      <v-card-text class="pa-4">
        <div v-if="!isKnownUser" class="text-caption text-warning mb-2">
          <v-icon size="x-small" class="me-1">mdi-alert</v-icon>
          Not logged in — task will be filed as "unknown"
        </div>
        <v-form ref="addFormRef" @submit.prevent="submitNewTodo">
          <v-text-field
            v-model="newTodo.content"
            label="Task Name"
            variant="outlined"
            density="compact"
            :rules="[v => !!v || 'Task name is required']"
            class="mb-3"
            autofocus
          ></v-text-field>

          <v-textarea
            v-model="newTodo.description"
            label="Description (optional)"
            variant="outlined"
            density="compact"
            rows="3"
            auto-grow
            class="mb-3"
          ></v-textarea>

          <v-select
            v-model="newTodo.priority"
            :items="priorityOptions"
            label="Priority"
            variant="outlined"
            density="compact"
            hide-details
          ></v-select>
        </v-form>
      </v-card-text>
      <v-divider></v-divider>
      <v-card-actions class="pa-3">
        <v-spacer></v-spacer>
        <v-btn variant="text" @click="closeAddModal">Cancel</v-btn>
        <v-btn color="primary" variant="flat" :loading="submitting" @click="submitNewTodo">
          Add Task
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import draggable from 'vuedraggable'

const loading = ref(false)
const todos = ref([])
const showCompleted = ref(false)
const textModalOpen = ref(false)
const textModalTitle = ref('')
const textModalDescription = ref('')
const showAddModal = ref(false)
const submitting = ref(false)
const newTodo = ref({ content: '', description: '', priority: 'normal' })
const priorityOptions = ['low', 'normal', 'high', 'critical']
const addFormRef = ref(null)

// Writable list bound to draggable (mirrors the filtered view of todos).
const visibleTodos = ref([])

function rebuildVisible() {
  visibleTodos.value = showCompleted.value
    ? [...todos.value]
    : todos.value.filter(t => t.status !== 'completed')
}

watch([todos, showCompleted], rebuildVisible, { immediate: true })

function getToken() {
  return localStorage.getItem('auth-token') || localStorage.getItem('token')
}

function getCurrentUsername() {
  // Try to decode the JWT; fall back to stored user object or 'unknown'
  const token = getToken()
  if (token) {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      if (payload.sub) return payload.sub
      if (payload.username) return payload.username
    } catch (e) {
      // ignore, fall through
    }
  }
  try {
    const user = JSON.parse(localStorage.getItem('user') || 'null')
    if (user?.username) return user.username
  } catch (e) { /* ignore */ }
  return 'unknown'
}

// Reactive current username for template bindings (re-read whenever the
// add-task modal opens so a login during the session is reflected).
const currentUsername = ref(getCurrentUsername())
const isKnownUser = computed(() => currentUsername.value && currentUsername.value !== 'unknown')

async function fetchTodos() {
  try {
    const response = await fetch('/api/todos', {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (response.ok) {
      todos.value = await response.json()
    }
  } catch (error) {
    console.error('Error fetching todos:', error)
  }
}

async function refreshTodos() {
  loading.value = true
  await fetchTodos()
  loading.value = false
}

async function submitNewTodo() {
  const { valid } = await addFormRef.value.validate()
  if (!valid) return
  submitting.value = true
  try {
    const response = await fetch('/api/todos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
      body: JSON.stringify({
        content: newTodo.value.content,
        description: newTodo.value.description || null,
        priority: newTodo.value.priority,
        created_by: getCurrentUsername()
      })
    })
    if (response.ok) {
      closeAddModal()
      await fetchTodos()
    }
  } catch (error) {
    console.error('Error adding todo:', error)
  } finally {
    submitting.value = false
  }
}

function openAddModal() {
  // Re-read the username each time the modal opens so a login during
  // the session is reflected immediately.
  currentUsername.value = getCurrentUsername()
  showAddModal.value = true
}

function closeAddModal() {
  showAddModal.value = false
  newTodo.value = { content: '', description: '', priority: 'normal' }
}

async function toggleTodoStatus(todo) {
  try {
    const newStatus = todo.status === 'completed' ? 'pending' : 'completed'
    const response = await fetch(`/api/todos/${todo.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
      body: JSON.stringify({ status: newStatus })
    })
    if (response.ok) await fetchTodos()
  } catch (error) {
    console.error('Error toggling todo status:', error)
  }
}

async function onDragEnd() {
  // visibleTodos reflects the new order; persist to backend.
  // Merge visible order back into the full todos list so hidden
  // (completed) items keep their relative positions at the tail.
  const visibleIds = visibleTodos.value.map(t => t.id)
  const hiddenTodos = todos.value.filter(t => !visibleIds.includes(t.id))
  const newOrder = [...visibleTodos.value, ...hiddenTodos]
  // Optimistically reflect new sort_order locally
  newOrder.forEach((t, i) => { t.sort_order = i + 1 })
  todos.value = newOrder
  try {
    await fetch('/api/todos/reorder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
      body: JSON.stringify({ ids: newOrder.map(t => t.id) })
    })
  } catch (error) {
    console.error('Error reordering todos:', error)
    await fetchTodos()
  }
}

async function deleteTodo(todoId) {
  try {
    const response = await fetch(`/api/todos/${todoId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${getToken()}` }
    })
    if (response.ok) await fetchTodos()
  } catch (error) {
    console.error('Error deleting todo:', error)
  }
}

function getPriorityColor(priority) {
  const map = { critical: 'error', high: 'warning', normal: 'info' }
  return map[priority] || 'grey'
}

function showFullText(todo) {
  textModalTitle.value = todo.content
  textModalDescription.value = todo.description || ''
  textModalOpen.value = true
}

let refreshInterval
onMounted(() => {
  refreshTodos()
  refreshInterval = setInterval(refreshTodos, 30000)
})
onBeforeUnmount(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.todo-item {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  min-height: 32px !important;
  padding-inline: 6px !important;
}

.todo-item:last-child {
  border-bottom: none;
}

.todo-row-blue {
  background-color: #e3f2fd;
}

.todo-row-white {
  background-color: #ffffff;
}

.todo-text-truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  font-size: 0.8rem !important;
}

.todo-text-truncate:hover {
  text-decoration: underline;
}

.todo-checkbox {
  flex: 0 0 auto;
}

.todo-checkbox :deep(.v-selection-control) {
  min-height: 28px;
}

.todo-priority-chip {
  width: 64px;
  min-width: 64px;
  max-width: 64px;
}

.todo-priority-chip :deep(.v-chip__content) {
  width: 100%;
  justify-content: center;
  text-transform: capitalize;
}

.todo-user-chip {
  width: 96px;
  min-width: 96px;
  max-width: 96px;
}

.todo-user-chip :deep(.v-chip__content) {
  width: 100%;
  overflow: hidden;
}

.todo-user-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
  max-width: 100%;
}

.todo-rank {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.6);
  min-width: 18px;
  text-align: right;
}

.todo-ghost {
  opacity: 0.5;
  background: #ffe082 !important;
}

.todo-toggle :deep(.v-label) {
  font-size: 0.75rem !important;
}
</style>
