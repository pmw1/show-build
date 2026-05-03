import { defineStore } from 'pinia'
import { useUserPrefs } from '@/composables/useUserPrefs'
import { useOverridableSettings } from '@/composables/useOverridableSettings'
import { useCursorMemory } from '@/composables/useCursorMemory'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('auth-token') || null,
    user: JSON.parse(localStorage.getItem('user-data') || 'null'),
    isAuthenticated: false
  }),

  getters: {
    isLoggedIn: (state) => !!state.token && !!state.user
  },

  actions: {
    setAuth(token, user) {
      this.token = token
      this.user = user
      this.isAuthenticated = true
      localStorage.setItem('auth-token', token)
      localStorage.setItem('user-data', JSON.stringify(user))
      // Pull this user's preference cache so any component reading
      // useUserPrefs().get(key) sees the right values immediately.
      useUserPrefs().hydrate()
      useOverridableSettings().hydrate()
    },

    clearAuth() {
      // Flush any pending cursor-memory writes BEFORE we wipe the user
      // pref cache — otherwise the persist call would target an empty
      // (or wrong-user) cache.
      try { useCursorMemory().flush() } catch { /* noop */ }
      this.token = null
      this.user = null
      this.isAuthenticated = false
      localStorage.removeItem('auth-token')
      localStorage.removeItem('user-data')
      localStorage.removeItem('auth-token-expiry')
      useUserPrefs().clearCache()
      useOverridableSettings().clearCache()
    },

    checkAuthStatus() {
      const token = localStorage.getItem('auth-token')
      const expiry = localStorage.getItem('auth-token-expiry')
      const userData = localStorage.getItem('user-data')

      if (token && expiry && userData) {
        const currentTime = Date.now()
        const expiryTime = parseInt(expiry)

        if (currentTime < expiryTime) {
          this.token = token
          this.user = JSON.parse(userData)
          this.isAuthenticated = true
          // Refresh prefs cache on app reload while still authed.
          useUserPrefs().hydrate()
      useOverridableSettings().hydrate()
          return true
        } else {
          this.clearAuth()
        }
      }
      return false
    }
  }
})
