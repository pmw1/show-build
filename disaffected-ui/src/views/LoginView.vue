<template>
  <div class="login-page">
    <div class="login-content">
      <h1 class="app-title">Show Builder</h1>
      <p class="copyright">© Copyrighted 2025 Polaris Broadcasting</p>
      <v-btn
        color="primary"
        variant="outlined"
        size="small"
        @click="openLoginModal"
        class="login-btn"
      >
        Login
      </v-btn>
    </div>

    <!-- Login Modal -->
    <v-dialog
      v-model="showLoginModal"
      max-width="400"
      persistent
      :z-index="10000"
    >
      <v-card>
        <v-card-title class="text-h5">Login</v-card-title>
        <v-card-text>
          <v-form @submit.prevent="handleLogin">
            <v-text-field
              v-model="loginForm.username"
              label="Username"
              variant="outlined"
              required
              @input="clearError"
            />
            <v-text-field
              v-model="loginForm.password"
              label="Password"
              type="password"
              variant="outlined"
              required
              @input="clearError"
              @keyup.enter="handleLogin"
              class="password-field"
            />
            <v-alert
              v-if="loginError"
              type="error"
              density="compact"
              class="mt-2"
            >
              {{ loginError }}
            </v-alert>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="grey" variant="text" @click="showLoginModal = false">
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            @click="handleLogin"
            :loading="loggingIn"
          >
            Login
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { setAuth } = useAuth()

const showLoginModal = ref(false)
const loggingIn = ref(false)
const loginError = ref('')

const loginForm = ref({
  username: '',
  password: ''
})

const openLoginModal = () => {
  showLoginModal.value = true
  loginError.value = ''
}

const clearError = () => {
  loginError.value = ''
}

const handleLogin = async () => {
  // Prevent multiple simultaneous login attempts
  if (loggingIn.value) {
    console.log('Login already in progress, ignoring')
    return
  }

  console.log('Form values:', loginForm.value)
  console.log('Username:', loginForm.value.username)
  console.log('Password:', loginForm.value.password)

  if (!loginForm.value.username || !loginForm.value.password) {
    loginError.value = 'Please enter both username and password'
    return
  }

  loggingIn.value = true
  loginError.value = ''

  const requestBody = {
    username: loginForm.value.username,
    password: loginForm.value.password,
  }

  console.log('Request body:', requestBody)

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    })

    console.log('Response status:', response.status)
    console.log('Response headers:', response.headers.get('content-type'))

    if (response.ok) {
      const data = await response.json()

      // Calculate expiry time (24 hours from now)
      const expiryTime = Date.now() + (24 * 60 * 60 * 1000)

      setAuth(data.access_token, data.user, expiryTime)

      // Redirect to dashboard
      router.push('/dashboard')
    } else {
      const errorText = await response.text()
      console.log('Error response text:', errorText)

      try {
        const errorData = JSON.parse(errorText)
        loginError.value = errorData.detail || 'Login failed'
      } catch (parseError) {
        loginError.value = errorText || 'Login failed'
      }
    }
  } catch (error) {
    console.error('Login error:', error)
    loginError.value = 'Network error. Please try again.'
  } finally {
    loggingIn.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 100vw;
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.login-content {
  text-align: center;
}

.app-title {
  font-size: 6rem;
  font-weight: bold;
  color: #1976d2;
  margin-bottom: 1rem;
  line-height: 1.1;
}

.copyright {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 2rem;
}

.login-btn {
  margin-top: 1rem;
}

/* Ensure modal renders above the fixed login page */
:deep(.v-overlay--active) {
  z-index: 10001 !important;
}

/* Ensure text field labels have proper positioning */
:deep(.v-text-field .v-field__input) {
  padding-top: 20px !important;
  padding-bottom: 8px !important;
}

/* Center the floating labels vertically in the input field */
:deep(.v-field__label) {
  top: 50% !important;
  transform: translateY(-50%) !important;
}

/* Add left padding to password field */
:deep(.password-field .v-field__input) {
  padding-left: 16px !important;
}

@media (max-width: 768px) {
  .app-title {
    font-size: 4rem;
  }
}

@media (max-width: 480px) {
  .app-title {
    font-size: 3rem;
  }
}
</style>