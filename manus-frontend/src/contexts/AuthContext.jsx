import { createContext, useContext, useState, useEffect } from 'react'
import { authService } from '@/services/authService'

export const AuthContext = createContext({}) // Added export

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const initialToken = localStorage.getItem('auth_token');
  const [token, setToken] = useState(initialToken)
  console.log('[AuthContext] Initial token from localStorage:', initialToken);

  useEffect(() => {
    console.log('[AuthContext] useEffect triggered. Current token state:', token);
    const initAuth = async () => {
      console.log('[AuthContext] initAuth started.');
      if (token) {
        console.log('[AuthContext] Token exists, attempting to get current user.');
        try {
          const userData = await authService.getCurrentUser()
          console.log('[AuthContext] getCurrentUser success:', userData);
          setUser(userData)
        } catch (error) {
          console.error('[AuthContext] Auth initialization failed (getCurrentUser error):', error)
          localStorage.removeItem('auth_token')
          setToken(null) // This will re-trigger useEffect
          console.log('[AuthContext] Token removed due to error.');
        }
      } else {
        console.log('[AuthContext] No token, skipping getCurrentUser.');
      }
      console.log('[AuthContext] Setting loading to false.');
      setLoading(false)
    }

    initAuth()
  }, [token])

  console.log('[AuthContext] Rendering AuthProvider. State: ', { user, token, loading });

  const login = async (credentials) => {
    try {
      const response = await authService.login(credentials)
      const { user: userData, token: authToken } = response
      
      setUser(userData)
      setToken(authToken)
      localStorage.setItem('auth_token', authToken)
      
      return { success: true, user: userData }
    } catch (error) {
      console.error('Login failed:', error)
      return { 
        success: false, 
        error: error.message || 'Login failed' 
      }
    }
  }

  const register = async (userData) => {
    try {
      const response = await authService.register(userData)
      const { user: newUser, token: authToken } = response
      
      setUser(newUser)
      setToken(authToken)
      localStorage.setItem('auth_token', authToken)
      
      return { success: true, user: newUser }
    } catch (error) {
      console.error('Registration failed:', error)
      return { 
        success: false, 
        error: error.message || 'Registration failed' 
      }
    }
  }

  const logout = async () => {
    try {
      await authService.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setUser(null)
      setToken(null)
      localStorage.removeItem('auth_token')
    }
  }

  const updateUser = (userData) => {
    setUser(prev => ({ ...prev, ...userData }))
  }

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    updateUser,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin'
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

