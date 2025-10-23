import { ref } from 'vue'
import axios from 'axios'

// Global shared state
const isAuthenticated = ref(false)
const currentUser = ref({})

export function useAuth() {

  const checkAuthStatus = () => {
    const token = localStorage.getItem('auth-token')
    const expiry = localStorage.getItem('auth-token-expiry')
    const userData = localStorage.getItem('user-data')
    
    if (token && expiry && userData) {
      const currentTime = Date.now()
      const expiryTime = parseInt(expiry, 10)
      
      if (currentTime < expiryTime) {
        isAuthenticated.value = true
        try {
          currentUser.value = JSON.parse(userData)
        } catch (err) {
          console.error('Failed to parse user data:', err)
          clearAuthData()
          return false
        }
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

  const checkUserGroup = async (groupSlug) => {
    try {
      if (!currentUser.value || !currentUser.value.id) {
        return false
      }

      const response = await axios.get(`/api/rbac/users/${currentUser.value.id}/groups`)
      if (response.data.success) {
        const userGroups = response.data.groups || []
        return userGroups.some(group => group.slug === groupSlug)
      }
      return false
    } catch (error) {
      console.error('Failed to check user groups:', error)
      return false
    }
  }

  const refreshUserProfile = async () => {
    try {
      const token = localStorage.getItem('auth-token')
      if (!token) return false

      const baseUrl = process.env.VUE_APP_API_BASE_URL || 'http://192.168.51.210:8888'
      const response = await axios.get(`${baseUrl}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.data) {
        currentUser.value = response.data
        localStorage.setItem('user-data', JSON.stringify(response.data))
        return true
      }
      return false
    } catch (error) {
      console.error('Failed to refresh user profile:', error)
      return false
    }
  }

  return {
    isAuthenticated,
    currentUser,
    checkAuthStatus,
    handleLogout,
    clearAuthData,
    setAuth,
    checkUserGroup,
    refreshUserProfile
  }
}