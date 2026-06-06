<template>
  <div class="login-page">
    <!-- Center icon -->
    <div class="login-content">
      <img src="/show-build-logo-medium.png" alt="Show Build" class="login-icon" :class="{ 'login-icon-raised': showForm }" />

      <!-- Login form overlaid on lower half -->
      <div class="login-form-area">
        <v-btn
          v-if="!showForm"
          color="white"
          variant="outlined"
          size="large"
          @click="showForm = true"
          class="login-trigger-btn"
        >
          <v-icon start>mdi-login</v-icon>
          Login
        </v-btn>

        <v-card v-else class="login-card" elevation="0">
          <v-card-text class="pa-4">
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                v-model="loginForm.username"
                placeholder="Username"
                variant="outlined"
                density="compact"
                hide-details="auto"
                bg-color="rgba(255,255,255,0.1)"
                class="mb-3 login-field"
                autofocus
                @input="clearError"
              />
              <v-text-field
                v-model="loginForm.password"
                placeholder="Password"
                type="password"
                variant="outlined"
                density="compact"
                hide-details="auto"
                bg-color="rgba(255,255,255,0.1)"
                class="mb-3 login-field"
                @input="clearError"
                @keyup.enter="handleLogin"
              />
              <v-alert
                v-if="loginError"
                type="error"
                density="compact"
                class="mb-3"
                style="font-size: 0.8rem;"
              >
                {{ loginError }}
              </v-alert>
              <v-btn
                type="submit"
                color="primary"
                variant="flat"
                block
                :loading="loggingIn"
              >
                Login
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </div>
    </div>
    <div class="version-label">dev-v2.01.00</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { setAuth } = useAuth()

const showForm = ref(false)
const loggingIn = ref(false)
const loginError = ref('')

const loginForm = ref({
  username: '',
  password: ''
})

const clearError = () => {
  loginError.value = ''
}

const handleLogin = async () => {
  if (loggingIn.value) return

  if (!loginForm.value.username || !loginForm.value.password) {
    loginError.value = 'Please enter both username and password'
    return
  }

  loggingIn.value = true
  loginError.value = ''

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: loginForm.value.username,
        password: loginForm.value.password
      })
    })

    if (response.ok) {
      const data = await response.json()
      const expiryTime = Date.now() + (24 * 60 * 60 * 1000)
      setAuth(data.access_token, data.user, expiryTime)
      router.push('/dashboard')
    } else {
      const errorText = await response.text()
      try {
        const errorData = JSON.parse(errorText)
        loginError.value = errorData.detail || 'Login failed'
      } catch {
        loginError.value = errorText || 'Login failed'
      }
    }
  } catch {
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
  background-color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.login-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
}

.login-icon {
  width: min(420px, 80vw);
  height: min(420px, 80vw);
  object-fit: contain;
  user-select: none;
  -webkit-user-drag: none;
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-icon-raised {
  transform: translateY(-200px);
}

.login-form-area {
  position: absolute;
  bottom: calc(40px - 2em);
  left: 50%;
  transform: translateX(-50%);
  width: min(300px, 70vw);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.login-trigger-btn {
  border-color: rgba(0, 0, 0, 0.25) !important;
  color: rgba(0, 0, 0, 0.7) !important;
  text-transform: none !important;
  font-weight: 500 !important;
  letter-spacing: 1px !important;
}

.login-trigger-btn:hover {
  border-color: rgba(0, 0, 0, 0.5) !important;
  color: rgba(0, 0, 0, 0.9) !important;
  background: rgba(0, 0, 0, 0.05) !important;
}

.login-card {
  background: rgba(245, 245, 245, 0.9) !important;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px !important;
  width: 100%;
}

.version-label {
  position: fixed;
  bottom: 16px;
  right: 20px;
  font-size: 0.75rem;
  color: rgba(0, 0, 0, 0.3);
  letter-spacing: 0.5px;
  user-select: none;
}

@media (max-width: 480px) {
  .login-icon {
    width: 280px;
    height: 280px;
  }

  .login-form-area {
    width: 260px;
    bottom: -10px;
  }
}
</style>
