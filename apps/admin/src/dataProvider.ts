import { DataProvider, fetchUtils } from 'react-admin'
import { mockGetList, mockGetOne, mockGetMany, hasMock } from './devData'

const apiUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const DEV = import.meta.env.DEV

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyParams = any

function buildPaginationQuery(resource: string, params: AnyParams): string {
  const { page, perPage } = params.pagination
  const { field, order } = params.sort
  const _start = (page - 1) * perPage
  const _end = _start + perPage
  const query = new URLSearchParams({
    _sort: field,
    _order: order,
    _start: String(_start),
    _end: String(_end),
  })
  if (params.filter) {
    Object.entries(params.filter).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') {
        query.append(k, String(v))
      }
    })
  }
  return `${apiUrl}/admin/${resource}?${query.toString()}`
}

const httpClient = (url: string, options: AnyParams = {}) => {
  if (!options.headers) {
    options.headers = new Headers({ Accept: 'application/json' })
  }
  const token = localStorage.getItem('admin_token')
  if (token) {
    options.headers.set('Authorization', `Bearer ${token}`)
  }
  return fetchUtils.fetchJson(url, options)
}

/** True when the backend is unreachable (network error), not an HTTP status error. */
function isNetworkError(err: unknown): boolean {
  if (!DEV) return false
  const e = err as { message?: string; status?: number }
  // react-admin's fetchJson throws HttpError with a numeric status for HTTP errors.
  // A genuine connection failure has no status and a "Failed to fetch"-style message.
  return e.status === undefined
}


// In DEV, when the backend is unreachable we fall back to local mock data so the
// UI stays explorable offline. Make that VERY visible so mock data is never
// mistaken for a real backend connection, and so failed writes aren't assumed saved.
function mockWarn(resource: string, op: string): void {
  console.warn(
    `[dataProvider] Backend unreachable — serving DEV MOCK for "${resource}.${op}". ` +
      'This is NOT real data; any changes are NOT persisted. ' +
      'Start the backend (default http://localhost:8000) for live data.',
  )
}

const dataProvider: DataProvider = {
  getList: async (resource, params) => {
    try {
      const url = buildPaginationQuery(resource, params)
      const { json } = await httpClient(url)
      return { data: json.data || [], total: json.total || 0 }
    } catch (err) {
      if (isNetworkError(err) && hasMock(resource)) {
        mockWarn(resource, 'getList')
        return mockGetList(resource, params as never)
      }
      throw err
    }
  },
  getOne: async (resource, params) => {
    try {
      const url = `${apiUrl}/admin/${resource}/${params.id}`
      const { json } = await httpClient(url)
      return { data: json }
    } catch (err) {
      if (isNetworkError(err) && hasMock(resource)) {
        mockWarn(resource, 'getOne')
        return { data: mockGetOne(resource, params.id) as never }
      }
      throw err
    }
  },
  getMany: async (resource, params) => {
    const ids = params.ids as (string | number)[]
    try {
      const results = await Promise.all(
        ids.map((id) => httpClient(`${apiUrl}/admin/${resource}/${id}`).then((r) => r.json))
      )
      return { data: results }
    } catch (err) {
      if (isNetworkError(err) && hasMock(resource)) {
        mockWarn(resource, 'getMany')
        return { data: mockGetMany(resource, ids) as never }
      }
      throw err
    }
  },
  getManyReference: async (resource, params) => {
    try {
      const url = buildPaginationQuery(resource, params)
      const { json } = await httpClient(url)
      return { data: json.data || [], total: json.total || 0 }
    } catch (err) {
      if (isNetworkError(err) && hasMock(resource)) {
        mockWarn(resource, 'getManyReference')
        return mockGetList(resource, params as never)
      }
      throw err
    }
  },
  create: async (resource, params) => {
    try {
      const url = `${apiUrl}/admin/${resource}`
      const { json } = await httpClient(url, {
        method: 'POST',
        body: JSON.stringify(params.data),
      })
      return { data: json }
    } catch (err) {
      if (isNetworkError(err)) {
        mockWarn(resource, 'create')
        return { data: { ...params.data, id: Date.now() } as never }
      }
      throw err
    }
  },
  update: async (resource, params) => {
    try {
      const url = `${apiUrl}/admin/${resource}/${params.id}`
      const { json } = await httpClient(url, {
        method: 'PUT',
        body: JSON.stringify(params.data),
      })
      return { data: json }
    } catch (err) {
      if (isNetworkError(err)) {
        mockWarn(resource, 'update')
        return { data: { ...params.data, id: params.id } as never }
      }
      throw err
    }
  },
  updateMany: async (resource, params) => {
    const ids = params.ids as (string | number)[]
    try {
      await Promise.all(
        ids.map((id) =>
          httpClient(`${apiUrl}/admin/${resource}/${id}`, {
            method: 'PUT',
            body: JSON.stringify(params.data),
          })
        )
      )
      return { data: ids }
    } catch (err) {
      if (isNetworkError(err)) {
        mockWarn(resource, 'updateMany')
        return { data: ids }
      }
      throw err
    }
  },
  delete: async (resource, params) => {
    try {
      const url = `${apiUrl}/admin/${resource}/${params.id}`
      const { json } = await httpClient(url, { method: 'DELETE' })
      return { data: json }
    } catch (err) {
      if (isNetworkError(err)) {
        mockWarn(resource, 'delete')
        return { data: { id: params.id } as never }
      }
      throw err
    }
  },
  deleteMany: async (resource, params) => {
    const ids = params.ids as (string | number)[]
    try {
      await Promise.all(
        ids.map((id) => httpClient(`${apiUrl}/admin/${resource}/${id}`, { method: 'DELETE' }))
      )
      return { data: ids }
    } catch (err) {
      if (isNetworkError(err)) {
        mockWarn(resource, 'deleteMany')
        return { data: ids }
      }
      throw err
    }
  },
}

export default dataProvider
