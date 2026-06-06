<template>
  <v-dialog v-model="isVisible" max-width="400" persistent>
    <v-card>
      <v-card-title class="text-h5 text-center pa-6">
        <v-icon size="large" class="mb-2" color="primary">mdi-account-key</v-icon>
        <div>Login to Show Build</div>
        <v-btn
          icon="mdi-close"
          variant="text"
          size="small"
          class="position-absolute"
          style="top: 8px; right: 8px;"
          @click="isVisible = false"
        />
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

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { registerModalEsc } from '@/composables/useModalStack'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})
const emit = defineEmits(['update:modelValue', 'login-success'])

const formValid = ref(false)
const showPassword = ref(false)
const isLoading = ref(false)
const errorMessage = ref('')
const credentials = ref({ username: '', password: '' })
const fieldErrors = ref({ username: [], password: [] })
const loginForm = ref(null)

const usernameRules = [
  v => !!v || 'Username is required',
  v => (v && v.length >= 3) || 'Username must be at least 3 characters'
]
const passwordRules = [
  v => !!v || 'Password is required',
  v => (v && v.length >= 4) || 'Password must be at least 4 characters'
]

const isVisible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

function resetForm() {
  credentials.value = { username: '', password: '' }
  errorMessage.value = ''
  fieldErrors.value = { username: [], password: [] }
  showPassword.value = false
  loginForm.value?.reset()
}

// ESC handled by global modal stack
registerModalEsc(() => isVisible.value, () => { isVisible.value = false }, 'LoginModal')

async function handleLogin() {
  if (!formValid.value) return

  isLoading.value = true
  errorMessage.value = ''
  fieldErrors.value = { username: [], password: [] }

  try {
    const response = await axios.post('/api/auth/login', {
      username: credentials.value.username,
      password: credentials.value.password
    })

    if (response.data.access_token) {
      const expirationTime = Date.now() + (48 * 60 * 60 * 1000)
      localStorage.setItem('auth-token', response.data.access_token)
      localStorage.setItem('auth-token-expiry', expirationTime.toString())
      localStorage.setItem('user-data', JSON.stringify(response.data.user))
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`

      emit('login-success', {
        token: response.data.access_token,
        user: response.data.user,
        expiry: expirationTime
      })

      isVisible.value = false
      resetForm()
    }
  } catch (error) {
    if (error.response?.status === 401) {
      errorMessage.value = 'Invalid username or password'
    } else if (error.response?.status === 422) {
      errorMessage.value = 'Please check your input'
    } else {
      errorMessage.value = 'Login failed. Please try again.'
    }
  } finally {
    isLoading.value = false
  }
}

watch(isVisible, (newValue) => {
  if (newValue) resetForm()
})
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
