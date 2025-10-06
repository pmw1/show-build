<template>
  <v-container fluid class="pa-4">
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <v-icon size="large" class="mr-3" color="primary">mdi-account-group</v-icon>
          <h2 class="text-h4 font-weight-bold">User Management</h2>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            prepend-icon="mdi-account-plus"
            @click="openCreateDialog"
            size="large"
          >
            Create User
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Users Table -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-table</v-icon>
            All Users
            <v-spacer></v-spacer>
            <v-text-field
              v-model="search"
              label="Search users"
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              clearable
              hide-details
              class="search-field"
            ></v-text-field>
          </v-card-title>

          <v-data-table
            :headers="headers"
            :items="users"
            :search="search"
            :loading="loading"
            class="elevation-0"
          >
            <!-- Username with avatar -->
            <template v-slot:[`item.username`]="{ item }">
              <div class="d-flex align-center py-2">
                <v-avatar size="32" class="mr-2">
                  <v-img v-if="item.profile_picture" :src="item.profile_picture" />
                  <v-icon v-else color="grey-lighten-1">mdi-account-circle</v-icon>
                </v-avatar>
                <span class="font-weight-medium">{{ item.username }}</span>
              </div>
            </template>

            <!-- Full name -->
            <template v-slot:[`item.name`]="{ item }">
              {{ item.first_name }} {{ item.last_name }}
            </template>

            <!-- Access level with chip -->
            <template v-slot:[`item.access_level`]="{ item }">
              <v-chip
                :color="getAccessLevelColor(item.access_level)"
                size="small"
                variant="flat"
                class="text-uppercase font-weight-bold"
              >
                {{ item.access_level }}
              </v-chip>
            </template>

            <!-- Active status -->
            <template v-slot:[`item.is_active`]="{ item }">
              <v-chip
                :color="item.is_active ? 'success' : 'error'"
                size="small"
                variant="flat"
              >
                <v-icon size="small" class="mr-1">
                  {{ item.is_active ? 'mdi-check-circle' : 'mdi-cancel' }}
                </v-icon>
                {{ item.is_active ? 'Active' : 'Inactive' }}
              </v-chip>
            </template>

            <!-- Last login -->
            <template v-slot:[`item.last_login`]="{ item }">
              <span v-if="item.last_login" class="text-caption">
                {{ formatDate(item.last_login) }}
              </span>
              <span v-else class="text-caption text-grey">Never</span>
            </template>

            <!-- Actions -->
            <template v-slot:[`item.actions`]="{ item }">
              <v-btn
                icon="mdi-pencil"
                size="small"
                variant="text"
                @click="openEditDialog(item)"
              ></v-btn>
              <v-btn
                icon="mdi-delete"
                size="small"
                variant="text"
                color="error"
                @click="openDeleteDialog(item)"
              ></v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit User Dialog -->
    <v-dialog v-model="dialog" max-width="600" persistent>
      <v-card>
        <v-card-title class="bg-primary text-white">
          <v-icon class="mr-2" color="white">{{ dialogMode === 'create' ? 'mdi-account-plus' : 'mdi-account-edit' }}</v-icon>
          {{ dialogMode === 'create' ? 'Create New User' : 'Edit User' }}
        </v-card-title>

        <v-card-text class="pt-6">
          <v-form ref="userForm" v-model="formValid">
            <v-row>
              <!-- Username -->
              <v-col cols="12">
                <v-text-field
                  v-model="formData.username"
                  label="Username"
                  :rules="[v => !!v || 'Username is required']"
                  required
                  :disabled="dialogMode === 'edit'"
                  variant="outlined"
                  prepend-inner-icon="mdi-account"
                ></v-text-field>
              </v-col>

              <!-- Password -->
              <v-col cols="12">
                <v-text-field
                  v-model="formData.password"
                  label="Password"
                  type="password"
                  :rules="dialogMode === 'create' ? [v => !!v || 'Password is required'] : []"
                  :required="dialogMode === 'create'"
                  variant="outlined"
                  prepend-inner-icon="mdi-lock"
                  :hint="dialogMode === 'edit' ? 'Leave blank to keep current password' : ''"
                ></v-text-field>
              </v-col>

              <!-- First Name -->
              <v-col cols="6">
                <v-text-field
                  v-model="formData.first_name"
                  label="First Name"
                  variant="outlined"
                  prepend-inner-icon="mdi-account-details"
                ></v-text-field>
              </v-col>

              <!-- Last Name -->
              <v-col cols="6">
                <v-text-field
                  v-model="formData.last_name"
                  label="Last Name"
                  variant="outlined"
                ></v-text-field>
              </v-col>

              <!-- Email -->
              <v-col cols="12">
                <v-text-field
                  v-model="formData.email"
                  label="Email"
                  type="email"
                  variant="outlined"
                  prepend-inner-icon="mdi-email"
                ></v-text-field>
              </v-col>

              <!-- Phone -->
              <v-col cols="12">
                <v-text-field
                  v-model="formData.phone"
                  label="Phone"
                  variant="outlined"
                  prepend-inner-icon="mdi-phone"
                ></v-text-field>
              </v-col>

              <!-- Access Level -->
              <v-col cols="6">
                <v-select
                  v-model="formData.access_level"
                  :items="accessLevels"
                  label="Access Level"
                  variant="outlined"
                  prepend-inner-icon="mdi-shield-account"
                ></v-select>
              </v-col>

              <!-- Active Status -->
              <v-col cols="6">
                <v-switch
                  v-model="formData.is_active"
                  label="Account Active"
                  color="success"
                  inset
                ></v-switch>
              </v-col>
            </v-row>
          </v-form>

          <!-- Error Display -->
          <v-alert v-if="error" type="error" variant="tonal" class="mt-4">
            {{ error }}
          </v-alert>
        </v-card-text>

        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn color="secondary" @click="closeDialog">Cancel</v-btn>
          <v-btn
            color="primary"
            @click="saveUser"
            :loading="saving"
            :disabled="!formValid"
          >
            {{ dialogMode === 'create' ? 'Create' : 'Update' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="500">
      <v-card>
        <v-card-title class="bg-error text-white">
          <v-icon class="mr-2" color="white">mdi-alert</v-icon>
          Confirm Deletion
        </v-card-title>

        <v-card-text class="pt-6">
          <p class="text-body-1">
            Are you sure you want to delete user <strong>{{ userToDelete?.username }}</strong>?
          </p>
          <p class="text-body-2 text-error mt-2">
            This action cannot be undone.
          </p>
        </v-card-text>

        <v-card-actions class="px-6 pb-4">
          <v-spacer></v-spacer>
          <v-btn color="secondary" @click="deleteDialog = false">Cancel</v-btn>
          <v-btn
            color="error"
            @click="confirmDelete"
            :loading="deleting"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script>
import axios from 'axios'

export default {
  name: 'UserManagement',
  data() {
    return {
      users: [],
      search: '',
      loading: false,
      dialog: false,
      deleteDialog: false,
      dialogMode: 'create', // 'create' or 'edit'
      formValid: false,
      saving: false,
      deleting: false,
      error: '',
      userToDelete: null,

      headers: [
        { title: 'Username', key: 'username', sortable: true },
        { title: 'Name', key: 'name', sortable: true },
        { title: 'Email', key: 'email', sortable: true },
        { title: 'Access Level', key: 'access_level', sortable: true },
        { title: 'Status', key: 'is_active', sortable: true },
        { title: 'Last Login', key: 'last_login', sortable: true },
        { title: 'Actions', key: 'actions', sortable: false, width: '120px' }
      ],

      accessLevels: [
        { title: 'Admin', value: 'admin' },
        { title: 'User', value: 'user' },
        { title: 'Guest', value: 'guest' }
      ],

      formData: {
        username: '',
        password: '',
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        access_level: 'user',
        is_active: true
      }
    }
  },
  mounted() {
    this.fetchUsers()
  },
  methods: {
    async fetchUsers() {
      this.loading = true
      try {
        const response = await axios.get('/api/auth/users')
        this.users = response.data
      } catch (error) {
        console.error('Error fetching users:', error)
        this.error = 'Failed to load users'
      } finally {
        this.loading = false
      }
    },

    openCreateDialog() {
      this.dialogMode = 'create'
      this.resetForm()
      this.dialog = true
    },

    openEditDialog(user) {
      this.dialogMode = 'edit'
      this.formData = {
        username: user.username,
        password: '',
        first_name: user.first_name || '',
        last_name: user.last_name || '',
        email: user.email || '',
        phone: user.phone || '',
        access_level: user.access_level,
        is_active: user.is_active
      }
      this.dialog = true
    },

    openDeleteDialog(user) {
      this.userToDelete = user
      this.deleteDialog = true
    },

    async saveUser() {
      if (!this.formValid) return

      this.saving = true
      this.error = ''

      try {
        if (this.dialogMode === 'create') {
          // Create new user
          await axios.post('/api/auth/users', {
            username: this.formData.username,
            password: this.formData.password
          })

          // Update additional fields if provided
          const updateData = {}
          if (this.formData.first_name) updateData.first_name = this.formData.first_name
          if (this.formData.last_name) updateData.last_name = this.formData.last_name
          if (this.formData.email) updateData.email = this.formData.email
          if (this.formData.phone) updateData.phone = this.formData.phone
          if (this.formData.access_level) updateData.access_level = this.formData.access_level
          updateData.is_active = this.formData.is_active

          if (Object.keys(updateData).length > 0) {
            await axios.put(`/api/auth/users/${this.formData.username}`, updateData)
          }
        } else {
          // Update existing user
          const updateData = {
            first_name: this.formData.first_name,
            last_name: this.formData.last_name,
            email: this.formData.email,
            phone: this.formData.phone,
            access_level: this.formData.access_level,
            is_active: this.formData.is_active
          }

          if (this.formData.password) {
            updateData.password = this.formData.password
          }

          await axios.put(`/api/auth/users/${this.formData.username}`, updateData)
        }

        // Refresh user list
        await this.fetchUsers()
        this.closeDialog()
      } catch (error) {
        console.error('Error saving user:', error)
        this.error = error.response?.data?.detail || 'Failed to save user'
      } finally {
        this.saving = false
      }
    },

    async confirmDelete() {
      if (!this.userToDelete) return

      this.deleting = true

      try {
        await axios.delete(`/api/auth/users/${this.userToDelete.username}`)
        await this.fetchUsers()
        this.deleteDialog = false
        this.userToDelete = null
      } catch (error) {
        console.error('Error deleting user:', error)
        this.error = error.response?.data?.detail || 'Failed to delete user'
      } finally {
        this.deleting = false
      }
    },

    closeDialog() {
      this.dialog = false
      this.error = ''
      this.resetForm()
    },

    resetForm() {
      this.formData = {
        username: '',
        password: '',
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        access_level: 'user',
        is_active: true
      }
      if (this.$refs.userForm) {
        this.$refs.userForm.resetValidation()
      }
    },

    getAccessLevelColor(level) {
      switch (level) {
        case 'admin':
          return 'error'
        case 'user':
          return 'success'
        case 'guest':
          return 'warning'
        default:
          return 'grey'
      }
    },

    formatDate(dateString) {
      if (!dateString) return 'Never'
      const date = new Date(dateString)
      return date.toLocaleString()
    }
  }
}
</script>

<style scoped>
.search-field {
  max-width: 300px;
}
</style>
