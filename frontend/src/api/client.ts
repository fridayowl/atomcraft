const BASE_URL = '/api'

function getToken(): string | null {
  return localStorage.getItem('aion_token')
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = { ...options?.headers as Record<string, string> }
  if (!(options?.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || 'Request failed')
  }
  return res.json()
}

function authFetch(path: string, options?: RequestInit): Promise<Response> {
  const token = getToken()
  const headers: Record<string, string> = { ...options?.headers as Record<string, string> }
  if (token) headers['Authorization'] = `Bearer ${token}`
  return fetch(`${BASE_URL}${path}`, { ...options, headers })
}

export const api = {
  materials: {
    list: (params?: string) => request<any>(`/materials/${params || ''}`),
    get: (id: number) => request<any>(`/materials/${id}`),
    create: (data: any) => request<any>('/materials/', { method: 'POST', body: JSON.stringify(data) }),
    delete: (id: number) => request<any>(`/materials/${id}`, { method: 'DELETE' }),
    search: (query: string) => request<any>(`/materials/?search=${encodeURIComponent(query)}`),
    importCif: (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      return authFetch('/materials/import-cif', { method: 'POST', body: formData })
        .then(async (r) => { if (!r.ok) throw new Error((await r.json()).detail || 'Import failed'); return r.json() })
    },
    exportCif: (id: number) =>
      authFetch(`/materials/${id}/cif`).then(async (r) => { if (!r.ok) throw new Error('Export failed'); return r.text() }),
  },
  generate: {
    crystals: (data: any) => request<any>('/generate/crystals', { method: 'POST', body: JSON.stringify(data) }),
    compositions: (data: any) => request<any>('/generate/compositions', { method: 'POST', body: JSON.stringify(data) }),
  },
  predict: {
    properties: (formula: string, properties: string[]) =>
      request<any>('/predict/', { method: 'POST', body: JSON.stringify({ formula, properties }) }),
    batch: (formulas: string[], properties: string[]) =>
      request<any>('/predict/batch', { method: 'POST', body: JSON.stringify({ formulas, properties }) }),
  },
  synthesis: {
    feasibility: (formula: string) =>
      request<any>('/synthesis/feasibility', { method: 'POST', body: JSON.stringify({ formula }) }),
    designExperiment: (formula: string, method: string) =>
      request<any>('/synthesis/design-experiment', { method: 'POST', body: JSON.stringify({ formula, method }) }),
    methods: () => request<any>('/synthesis/methods'),
  },
  experiments: {
    list: (params?: string) => request<any>(`/experiments/${params || ''}`),
    get: (id: number) => request<any>(`/experiments/${id}`),
    create: (data: any) => request<any>('/experiments/', { method: 'POST', body: JSON.stringify(data) }),
    addStep: (id: number, data: any) =>
      request<any>(`/experiments/${id}/steps`, { method: 'POST', body: JSON.stringify(data) }),
    addResult: (id: number, data: any) =>
      request<any>(`/experiments/${id}/results`, { method: 'POST', body: JSON.stringify(data) }),
    updateStatus: (id: number, status: string, successful?: boolean) => {
      const params = new URLSearchParams({ status })
      if (successful !== undefined) params.set('successful', String(successful))
      return request<any>(`/experiments/${id}/status?${params}`, { method: 'PATCH' })
    },
  },
  chat: {
    query: (message: string, context?: any) =>
      request<any>('/chat/query', { method: 'POST', body: JSON.stringify({ message, context }) }),
    suggest: (requirements: any) =>
      request<any>('/chat/suggest', { method: 'POST', body: JSON.stringify({ requirements }) }),
  },
  auth: {
    signup: (data: any) => request<any>('/auth/signup', { method: 'POST', body: JSON.stringify(data) }),
    login: (username: string, password: string) => {
      const formData = new URLSearchParams()
      formData.set('username', username)
      formData.set('password', password)
      return fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData,
      }).then(async (r) => {
        if (!r.ok) throw new Error((await r.json()).detail || 'Login failed')
        return r.json()
      })
    },
    me: () => request<any>('/auth/me'),
  },
}
