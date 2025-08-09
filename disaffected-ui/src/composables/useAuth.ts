import { ref, type Ref } from 'vue'
import axios from 'axios'
import type { User } from '@/types'

export interface UseAuthReturn {
  isAuthenticated: Ref<boolean>
  currentUser: Ref<User | Record<string, never>>
  checkAuthStatus: () => boolean
  handleLogout: () => void
  clearAuthData: () => void
  setAuth: (token: string, user: User, expiry: number) => void
}

export function useAuth(): UseAuthReturn {
  const isAuthenticated = ref(false)
  const currentUser = ref<User | Record<string, never>>({})

  const checkAuthStatus = (): boolean => {
    const token = localStorage.getItem('auth-token')
    const expiry = localStorage.getItem('auth-token-expiry')
    const userData = localStorage.getItem('user-data')
    
    if (token && expiry && userData) {
      const currentTime = Date.now()
      const expiryTime = parseInt(expiry, 10)
      
      if (currentTime < expiryTime) {
        isAuthenticated.value = true
        try {
          currentUser.value = JSON.parse(userData) as User
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

  const handleLogout = (): void => {
    isAuthenticated.value = false
    currentUser.value = {}
    localStorage.removeItem('auth-token')
    localStorage.removeItem('auth-token-expiry')
    localStorage.removeItem('user-data')
    delete axios.defaults.headers.common['Authorization']
  }

  const clearAuthData = (): void => {
    isAuthenticated.value = false
    currentUser.value = {}
    localStorage.removeItem('auth-token')
    localStorage.removeItem('auth-token-expiry')
    localStorage.removeItem('user-data')
    delete axios.defaults.headers.common['Authorization']
  }

  const setAuth = (token: string, user: User, expiry: number): void => {
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