<template>
  <v-dialog v-model="isVisible" max-width="400" persistent>
    <v-card>
      <v-card-title class="text-h5 text-center pa-6">
        <v-icon size="large" class="mb-2" color="primary">mdi-account-key</v-icon>
        <div>Login to Show Builder</div>
      </v-card-title>

      <v-card-text class="px-6 pb-0">
        <v-form ref="loginForm" v-model="formValid" @submit.prevent="handleLogin">
          <v-text-field
            v-model="credentials.username"
            label="Username"
            prepend-inner-icon="mdi-account"
            variant="outlined"
            :rules="usernameRules"
            :error-messages="fieldErrors.username"
            required
            autofocus
            class="mb-3"
            @keyup.enter="handleLogin"
          />
          
          <v-text-field
            v-model="credentials.password"
            label="Password"
            prepend-inner-icon="mdi-lock"
            :type="showPassword ? 'text' : 'password'"
            :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
            @click:append-inner="showPassword = !showPassword"
            variant="outlined"
            :rules="passwordRules"
            :error-messages="fieldErrors.password"
            required
            class="mb-4"
            @keyup.enter="handleLogin"
          />

          <v-alert
            v-if="errorMessage"
            type="error"
            variant="tonal"
            class="mb-4"
            closable
            @click:close="errorMessage = ''"
          >
            {{ errorMessage }}
          </v-alert>
        </v-form>
      </v-card-text>

      <v-card-actions class="px-6 pb-6">
        <v-spacer />
        <v-btn
          color="primary"
          size="large"
          :loading="isLoading"
          :disabled="!formValid"
          @click="handleLogin"
          block
        >
          <v-icon start>mdi-login</v-icon>
          Login
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script>
import axios from 'axios'

export default {
  name: 'LoginModal',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue', 'login-success'],
  data() {
    return {
      formValid: false,
      showPassword: false,
      isLoading: false,
      errorMessage: '',
      credentials: {
        username: '',
        password: ''
      },
      fieldErrors: {
        username: [],
        password: []
      },
      usernameRules: [
        v => !!v || 'Username is required',
        v => (v && v.length >= 3) || 'Username must be at least 3 characters'
      ],
      passwordRules: [
        v => !!v || 'Password is required',
        v => (v && v.length >= 4) || 'Password must be at least 4 characters'
      ]
    }
  },
  computed: {
    isVisible: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      }
    }
  },
  methods: {
    async handleLogin() {
      if (!this.formValid) return

      this.isLoading = true
      this.errorMessage = ''
      this.fieldErrors = { username: [], password: [] }

      try {
        // Create form data for OAuth2PasswordRequestForm
        const formData = new FormData()
        formData.append('username', this.credentials.username)
        formData.append('password', this.credentials.password)

        const response = await axios.post(
          'http://192.168.51.210:8888/auth/login',
          formData,
          {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          }
        )

        if (response.data.access_token) {
          // Store token with 48-hour expiration
          const expirationTime = Date.now() + (48 * 60 * 60 * 1000) // 48 hours
          localStorage.setItem('auth-token', response.data.access_token)
          localStorage.setItem('auth-token-expiry', expirationTime.toString())
          localStorage.setItem('user-data', JSON.stringify(response.data.user))

          // Set default auth header for future requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`

          // Emit success event with user data
          this.$emit('login-success', {
            token: response.data.access_token,
            user: response.data.user
          })

          // Close modal and reset form
          this.isVisible = false
          this.resetForm()
        }
      } catch (error) {
        
        if (error.response?.status === 401) {
          this.errorMessage = 'Invalid username or password'
        } else if (error.response?.status === 422) {
          this.errorMessage = 'Please check your input'
        } else {
          this.errorMessage = 'Login failed. Please try again.'
        }
      } finally {
        this.isLoading = false
      }
    },
    resetForm() {
      this.credentials = { username: '', password: '' }
      this.errorMessage = ''
      this.fieldErrors = { username: [], password: [] }
      this.showPassword = false
      if (this.$refs.loginForm) {
        this.$refs.loginForm.reset()
      }
    }
  },
  watch: {
    isVisible(newValue) {
      if (newValue) {
        // Reset form when modal opens
        this.resetForm()
      }
    }
  }
}
</script>

<style scoped>
.v-card {
  border-radius: 12px !important;
}

.v-card-title {
  background: linear-gradient(135deg, #f5f5f5 0%, #e8e8e8 100%);
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.v-text-field {
  margin-bottom: 8px;
}

.v-btn {
  border-radius: 8px !important;
  font-weight: 600;
  text-transform: none;
  letter-spacing: 0.5px;
}
</style>
