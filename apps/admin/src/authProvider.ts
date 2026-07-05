import { AuthProvider } from 'react-admin'

interface ApiError {
  status?: number
}

const authProvider: AuthProvider = {
  login: async ({ username, password }) => {
    const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const res = await fetch(`${apiUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: username, password }),
    })
    if (!res.ok) {
      // Surface real error to user; no dev fallback that masks bugs.
      const detail = await res.text().catch(() => '')
      throw new Error(
        `Login failed (HTTP ${res.status})${detail ? `: ${detail}` : ''}`,
      )
    }
    const data = await res.json()
    if (data.token) {
      localStorage.setItem('admin_token', data.token)
    }
    return Promise.resolve()
  },
  logout: () => {
    localStorage.removeItem('admin_token')
    return Promise.resolve()
  },
  checkAuth: () => {
    return localStorage.getItem('admin_token') ? Promise.resolve() : Promise.reject()
  },
  checkError: (error: unknown) => {
    const status = (error as ApiError).status
    if (status === 401 || status === 403) {
      localStorage.removeItem('admin_token')
      return Promise.reject()
    }
    return Promise.resolve()
  },
  getPermissions: () => {
    return Promise.resolve('admin')
  },
  getIdentity: () => {
    return Promise.resolve({ id: 'admin', fullName: 'Admin' })
  },
}

export default authProvider
