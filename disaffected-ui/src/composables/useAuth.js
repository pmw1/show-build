import { ref } from 'vue'
import axios from 'axios'

export function useAuth() {
  const isAuthenticated = ref(false)
  const currentUser = ref({})

  const checkAuthStatus = () => {
    const token = localStorage.getItem('auth-token')
    const expiry = localStorage.getItem('auth-token-expiry')
    const userData = localStorage.getItem('user-data')
    
    if (token && expiry && userData) {
      const currentTime = Date.now()
      const expiryTime = parseInt(expiry)
      
      if (currentTime < expiryTime) {
        isAuthenticated.value = true
        currentUser.value = JSON.parse(userData)
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
        return true
      } else {
        clearAuthData()
      }
    }
    return false
  }

  const handleLogout = () => {
    isAuthenticated.value = false
    currentUser.value = {}
    localStorage.removeItem('auth-token')
    localStorage.removeItem('auth-token-expiry')
    localStorage.removeItem('user-data')
    delete axios.defaults.headers.common['Authorization']
  }

  const clearAuthData = () => {
    isAuthenticated.value = false
    currentUser.value = {}
    localStorage.removeItem('auth-token')
    localStorage.removeItem('auth-token-expiry')
    localStorage.removeItem('user-data')
    delete axios.defaults.headers.common['Authorization']
  }

  const setAuth = (token, user, expiry) => {
    isAuthenticated.value = true
    currentUser.value = user
    localStorage.setItem('auth-token', token)
    localStorage.setItem('user-data', JSON.stringify(user))
    localStorage.setItem('auth-token-expiry', expiry.toString())
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
  }

  return { 
    isAuthenticated, 
    currentUser, 
    checkAuthStatus, 
    handleLogout, 
    clearAuthData, 
    setAuth 
  }
}
