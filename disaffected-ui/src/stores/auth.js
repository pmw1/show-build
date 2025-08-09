import { defineStore } from 'pinia'

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
    },
    
    clearAuth() {
      this.token = null
      this.user = null
      this.isAuthenticated = false
      localStorage.removeItem('auth-token')
      localStorage.removeItem('user-data')
      localStorage.removeItem('auth-token-expiry')
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
          return true
        } else {
          this.clearAuth()
        }
      }
      return false
    }
  }
})
