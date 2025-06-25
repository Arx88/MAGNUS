const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000'

class AuthService {
  constructor() {
    this.baseURL = `${API_BASE_URL}/api/auth`
  }

  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`
    const token = localStorage.getItem('auth_token')
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    }

    try {
      const response = await fetch(url, config)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || `HTTP error! status: ${response.status}`)
      }

      return data
    } catch (error) {
      console.error('API request failed:', error)
      throw error
    }
  }

  async login(credentials) {
    const response = await this.makeRequest('/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })

    return response
  }

  async register(userData) {
    const response = await this.makeRequest('/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    })

    return response
  }

  async logout() {
    try {
      await this.makeRequest('/logout', {
        method: 'POST',
      })
    } catch (error) {
      // Ignorar errores de logout, limpiar token de todas formas
      console.warn('Logout request failed:', error)
    }
  }

  async getCurrentUser() {
    const response = await this.makeRequest('/me')
    return response.user
  }

  async refreshToken() {
    const response = await this.makeRequest('/refresh', {
      method: 'POST',
    })

    if (response.token) {
      localStorage.setItem('auth_token', response.token)
    }

    return response
  }

  async updateProfile(userData) {
    const response = await this.makeRequest('/profile', {
      method: 'PUT',
      body: JSON.stringify(userData),
    })

    return response.user
  }

  async changePassword(passwordData) {
    const response = await this.makeRequest('/change-password', {
      method: 'POST',
      body: JSON.stringify(passwordData),
    })

    return response
  }

  async requestPasswordReset(email) {
    const response = await this.makeRequest('/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })

    return response
  }

  async resetPassword(token, newPassword) {
    const response = await this.makeRequest('/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, password: newPassword }),
    })

    return response
  }

  isTokenExpired() {
    const token = localStorage.getItem('auth_token')
    if (!token) return true

    try {
      const payload = JSON.parse(atob(token.split('.')[1]))
      const currentTime = Date.now() / 1000
      return payload.exp < currentTime
    } catch (error) {
      return true
    }
  }

  getToken() {
    return localStorage.getItem('auth_token')
  }

  removeToken() {
    localStorage.removeItem('auth_token')
  }
}

export const authService = new AuthService()

