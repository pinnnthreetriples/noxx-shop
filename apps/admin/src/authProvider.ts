import { AuthProvider } from 'react-admin'

interface ApiError {
  status?: number
  body?: { detail?: unknown }
}

/** Thrown by login() when the backend demands a TOTP/backup code. */
export interface TotpError extends Error {
  code: 'totp_required' | 'totp_invalid'
}

const authProvider: AuthProvider = {
  login: async ({ username, password, otp }: { username: string; password: string; otp?: string }) => {
    const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const res = await fetch(`${apiUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: username, password, ...(otp ? { otp } : {}) }),
    })
    if (!res.ok) {
      // Surface real error to user; no dev fallback that masks bugs.
      const body = await res.json().catch(() => null) as { detail?: unknown } | null
      const detail = body?.detail
      const code = detail && typeof detail === 'object' ? (detail as { code?: unknown }).code : undefined
      if (code === 'totp_required' || code === 'totp_invalid') {
        throw Object.assign(new Error(code), { code }) as TotpError
      }
      const detailText = typeof detail === 'string' ? detail : ''
      throw new Error(
        `Login failed (HTTP ${res.status})${detailText ? `: ${detailText}` : ''}`,
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
    const { status, body } = error as ApiError
    const detail = body?.detail
    const code = detail && typeof detail === 'object' ? (detail as { code?: unknown }).code : undefined
    if (code === 'totp_setup_required') {
      // Admin hasn't enabled 2FA but the server now requires it — send them to
      // the setup page without logging them out.
      return Promise.reject({ redirectTo: '/security', logoutUser: false })
    }
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
