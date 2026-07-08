import axios from 'axios'
import { resolveMock } from './devMocks'
import { useAppStore } from '../lib/store'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  // DEV fallback: outside Telegram, use a locally-forged initData so the app can
  // talk to the real backend. Stripped from production builds.
  const devInit = import.meta.env.DEV
    ? (import.meta.env as Record<string, string | undefined>).VITE_DEV_INIT_DATA
    : undefined
  const initData = window.Telegram?.WebApp?.initData || devInit
  if (initData) {
    config.headers['x-telegram-init-data'] = initData
  }
  const lang = useAppStore.getState().language
  if (lang) {
    config.headers['x-lang'] = lang
  }
  return config
})

// DEV fallback: when no real backend is configured, the request either fails
// (network error) or hits the Vite dev server and returns the SPA index.html.
// In both cases serve mock data so the UI can be reviewed with content.
function looksLikeHtml(data: unknown): boolean {
  return typeof data === 'string' && data.trimStart().startsWith('<')
}

api.interceptors.response.use(
  (response) => {
    if (import.meta.env.DEV && response.config?.method === 'get' && looksLikeHtml(response.data)) {
      const mock = resolveMock(response.config.url ?? '')
      if (mock !== undefined) return { ...response, data: mock, statusText: 'OK (mock)' }
    }
    return response
  },
  (error) => {
    if (import.meta.env.DEV && !error.response && error.config?.method === 'get') {
      const mock = resolveMock(error.config.url ?? '')
      if (mock !== undefined) {
        return Promise.resolve({ data: mock, status: 200, statusText: 'OK (mock)', headers: {}, config: error.config })
      }
    }
    return Promise.reject(error)
  },
)

export default api
