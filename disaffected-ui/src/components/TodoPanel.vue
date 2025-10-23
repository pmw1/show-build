<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      <v-icon start>mdi-clipboard-check</v-icon>
      Todo Lists
      <v-spacer></v-spacer>
      <v-btn
        icon="mdi-refresh"
        variant="text"
        size="small"
        @click="refreshTodos"
        :loading="loading"
      ></v-btn>
    </v-card-title>

    <v-tabs v-model="activeTab" density="compact">
      <v-tab value="claude">Claude</v-tab>
      <v-tab value="user">User Items</v-tab>
      <v-tab value="completed">Completed</v-tab>
    </v-tabs>

    <v-card-text class="pa-0">
      <v-window v-model="activeTab">
        <!-- Claude Todos Tab -->
        <v-window-item value="claude">
          <div class="pa-3">
            <v-list v-if="activeClaudeTodos.length > 0" density="compact">
              <v-list-item
                v-for="(todo, index) in activeClaudeTodos"
                :key="index"
                class="todo-item"
              >
                <template v-slot:prepend>
                  <v-icon :color="getStatusColor(todo.status)">
                    {{ getStatusIcon(todo.status) }}
                  </v-icon>
                </template>

                <v-list-item-title>{{ todo.content }}</v-list-item-title>
                <v-list-item-subtitle v-if="todo.status === 'in_progress'">
                  {{ todo.activeForm }}
                </v-list-item-subtitle>

                <template v-slot:append>
                  <v-chip
                    :color="getStatusColor(todo.status)"
                    size="x-small"
                    variant="flat"
                  >
                    {{ formatStatus(todo.status) }}
                  </v-chip>
                </template>
              </v-list-item>
            </v-list>

            <div v-else class="text-center text-grey py-4">
              No active Claude todos
            </div>
          </div>
        </v-window-item>

        <!-- User Todos Tab -->
        <v-window-item value="user">
          <div class="pa-3">
            <!-- Add new todo -->
            <v-form @submit.prevent="addUserTodo" class="mb-3">
              <v-textarea
                v-model="newTodoContent"
                label="Add high-level task or idea"
                rows="2"
                density="compact"
                variant="outlined"
                hide-details
                class="mb-2"
              ></v-textarea>
              <div class="d-flex gap-2">
                <v-select
                  v-model="newTodoPriority"
                  :items="priorityOptions"
                  label="Priority"
                  density="compact"
                  variant="outlined"
                  hide-details
                  style="max-width: 150px;"
                ></v-select>
                <v-spacer></v-spacer>
                <v-btn
                  type="submit"
                  color="primary"
                  size="small"
                  :disabled="!newTodoContent.trim()"
                >
                  Add
                </v-btn>
              </div>
            </v-form>

            <!-- User todos list (active only) -->
            <v-list v-if="activeUserTodos.length > 0" density="compact">
              <v-list-item
                v-for="todo in activeUserTodos"
                :key="todo.id"
                class="todo-item"
              >
                <template v-slot:prepend>
                  <v-checkbox
                    :model-value="todo.status === 'completed'"
                    @update:model-value="toggleUserTodoStatus(todo)"
                    hide-details
                    density="compact"
                  ></v-checkbox>
                </template>

                <v-list-item-title>
                  {{ todo.content }}
                </v-list-item-title>

                <template v-slot:append>
                  <v-chip
                    :color="getPriorityColor(todo.priority)"
                    size="x-small"
                    variant="flat"
                    class="me-2"
                  >
                    {{ todo.priority }}
                  </v-chip>
                  <v-btn
                    icon="mdi-delete"
                    variant="text"
                    size="x-small"
                    @click="deleteUserTodo(todo.id)"
                  ></v-btn>
                </template>
              </v-list-item>
            </v-list>

            <div v-else class="text-center text-grey py-4">
              No active todos
            </div>
          </div>
        </v-window-item>

        <!-- Completed Todos Tab -->
        <v-window-item value="completed">
          <div class="pa-3">
            <!-- Completed Claude Todos -->
            <div v-if="completedClaudeTodos.length > 0" class="mb-3">
              <div class="text-caption text-grey mb-2">Claude Tasks</div>
              <v-list density="compact">
                <v-list-item
                  v-for="(todo, index) in completedClaudeTodos"
                  :key="'claude-' + index"
                  class="todo-item"
                >
                  <template v-slot:prepend>
                    <v-icon color="success">mdi-check-circle</v-icon>
                  </template>

                  <v-list-item-title class="text-decoration-line-through text-grey">
                    {{ todo.content }}
                  </v-list-item-title>
                </v-list-item>
              </v-list>
            </div>

            <!-- Completed User Todos -->
            <div v-if="completedUserTodos.length > 0">
              <div class="text-caption text-grey mb-2">User Items</div>
              <v-list density="compact">
                <v-list-item
                  v-for="todo in completedUserTodos"
                  :key="'user-' + todo.id"
                  class="todo-item"
                >
                  <template v-slot:prepend>
                    <v-checkbox
                      :model-value="true"
                      @update:model-value="toggleUserTodoStatus(todo)"
                      hide-details
                      density="compact"
                    ></v-checkbox>
                  </template>

                  <v-list-item-title class="text-decoration-line-through text-grey">
                    {{ todo.content }}
                  </v-list-item-title>

                  <template v-slot:append>
                    <v-chip
                      :color="getPriorityColor(todo.priority)"
                      size="x-small"
                      variant="flat"
                      class="me-2"
                    >
                      {{ todo.priority }}
                    </v-chip>
                    <v-btn
                      icon="mdi-delete"
                      variant="text"
                      size="x-small"
                      @click="deleteUserTodo(todo.id)"
                    ></v-btn>
                  </template>
                </v-list-item>
              </v-list>
            </div>

            <div v-if="completedClaudeTodos.length === 0 && completedUserTodos.length === 0" class="text-center text-grey py-4">
              No completed todos
            </div>
          </div>
        </v-window-item>
      </v-window>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'TodoPanel',

  data() {
    return {
      activeTab: 'user',
      loading: false,
      claudeTodos: [],
      userTodos: [],
      newTodoContent: '',
      newTodoPriority: 'normal',
      priorityOptions: [
        { title: 'Low', value: 'low' },
        { title: 'Normal', value: 'normal' },
        { title: 'High', value: 'high' },
        { title: 'Critical', value: 'critical' }
      ]
    }
  },

  mounted() {
    this.refreshTodos()

    // Auto-refresh every 30 seconds
    this.refreshInterval = setInterval(() => {
      this.refreshTodos()
    }, 30000)
  },

  beforeUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval)
    }
  },

  computed: {
    activeClaudeTodos() {
      return this.claudeTodos.filter(todo => todo.status !== 'completed')
    },
    completedClaudeTodos() {
      return this.claudeTodos.filter(todo => todo.status === 'completed')
    },
    activeUserTodos() {
      return this.userTodos.filter(todo => todo.status !== 'completed')
    },
    completedUserTodos() {
      return this.userTodos.filter(todo => todo.status === 'completed')
    }
  },

  methods: {
    async refreshTodos() {
      this.loading = true
      await Promise.all([
        this.fetchClaudeTodos(),
        this.fetchUserTodos()
      ])
      this.loading = false
    },

    async fetchClaudeTodos() {
      try {
        const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
        const response = await fetch('/api/todos/claude', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          this.claudeTodos = await response.json()
        }
      } catch (error) {
        console.error('Error fetching Claude todos:', error)
      }
    },

    async fetchUserTodos() {
      try {
        const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
        const response = await fetch('/api/todos/user', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          this.userTodos = await response.json()
        }
      } catch (error) {
        console.error('Error fetching user todos:', error)
      }
    },

    async addUserTodo() {
      if (!this.newTodoContent.trim()) return

      try {
        const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
        const response = await fetch('/api/todos/user', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            content: this.newTodoContent,
            priority: this.newTodoPriority
          })
        })

        if (response.ok) {
          this.newTodoContent = ''
          this.newTodoPriority = 'normal'
          await this.fetchUserTodos()
        }
      } catch (error) {
        console.error('Error adding user todo:', error)
      }
    },

    async toggleUserTodoStatus(todo) {
      try {
        const newStatus = todo.status === 'completed' ? 'pending' : 'completed'
        const token = localStorage.getItem('auth-token') || localStorage.getItem('token')

        const response = await fetch(`/api/todos/user/${todo.id}`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            status: newStatus
          })
        })

        if (response.ok) {
          await this.fetchUserTodos()
        }
      } catch (error) {
        console.error('Error toggling todo status:', error)
      }
    },

    async deleteUserTodo(todoId) {
      try {
        const token = localStorage.getItem('auth-token') || localStorage.getItem('token')
        const response = await fetch(`/api/todos/user/${todoId}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })

        if (response.ok) {
          await this.fetchUserTodos()
        }
      } catch (error) {
        console.error('Error deleting user todo:', error)
      }
    },

    getStatusIcon(status) {
      switch (status) {
        case 'completed':
          return 'mdi-check-circle'
        case 'in_progress':
          return 'mdi-progress-clock'
        case 'pending':
        default:
          return 'mdi-circle-outline'
      }
    },

    getStatusColor(status) {
      switch (status) {
        case 'completed':
          return 'success'
        case 'in_progress':
          return 'primary'
        case 'pending':
        default:
          return 'grey'
      }
    },

    getPriorityColor(priority) {
      switch (priority) {
        case 'critical':
          return 'error'
        case 'high':
          return 'warning'
        case 'normal':
          return 'info'
        case 'low':
        default:
          return 'grey'
      }
    },

    formatStatus(status) {
      return status.replace('_', ' ').toUpperCase()
    }
  }
}
</script>

<style scoped>
.todo-item {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.todo-item:last-child {
  border-bottom: none;
}

.gap-2 {
  gap: 8px;
}
</style>
