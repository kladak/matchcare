import type {
  AuditLog,
  MatchRequest,
  MatchResponse,
  Persona,
  Provider,
  TenantSummary,
  UserMe,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? '/api'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const headers = new Headers(options.headers)
  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body.detail ?? JSON.stringify(body)
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, typeof detail === 'string' ? detail : 'Request failed')
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  personas: () => request<Persona[]>('/auth/personas'),
  login: (email: string, password: string) =>
    request<{ access_token: string }>('/auth/token', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  me: (token: string) => request<UserMe>('/auth/me', {}, token),
  providers: (token: string, params?: { specialty?: string; city?: string }) => {
    const q = new URLSearchParams()
    if (params?.specialty) q.set('specialty', params.specialty)
    if (params?.city) q.set('city', params.city)
    const qs = q.toString()
    return request<Provider[]>(`/providers${qs ? `?${qs}` : ''}`, {}, token)
  },
  match: (
    token: string,
    body: {
      preferred_specialties?: string[]
      city?: string
      region?: string
      require_tier?: boolean
      limit?: number
    },
  ) =>
    request<MatchResponse>('/match', { method: 'POST', body: JSON.stringify(body) }, token),
  listRequests: (token: string) => request<MatchRequest[]>('/match-requests', {}, token),
  createRequest: (token: string, provider_user_id: number, notes = '') =>
    request<MatchRequest>(
      '/match-requests',
      { method: 'POST', body: JSON.stringify({ provider_user_id, notes }) },
      token,
    ),
  patchRequest: (token: string, id: number, status: string, scheduled_for?: string) =>
    request<MatchRequest>(
      `/match-requests/${id}`,
      {
        method: 'PATCH',
        body: JSON.stringify({ status, scheduled_for: scheduled_for ?? null }),
      },
      token,
    ),
  tenant: (token: string) => request<TenantSummary>('/admin/tenant', {}, token),
  auditLogs: (token: string) => request<AuditLog[]>('/audit/logs?limit=40', {}, token),
}
