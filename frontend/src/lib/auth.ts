import api from './api'

export interface LoginResponse {
  access:  string
  refresh: string
  user: {
    id:         string
    email:      string
    role:       string
    full_name:  string
  }
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/api/v1/auth/login/', { email, password })
  console.log('[Login] Response keys:', Object.keys(data))
  console.log('[Login] access token exists:', !!data.access)
  console.log('[Login] refresh token exists:', !!data.refresh)
  localStorage.setItem('access_token',  data.access)
  localStorage.setItem('refresh_token', data.refresh)
  console.log('[Login] Stored access_token:', localStorage.getItem('access_token')?.slice(0, 20) + '...')
  return data
}

export async function logout() {
  const refresh = localStorage.getItem('refresh_token')
  try {
    await api.post('/api/v1/auth/logout/', { refresh_token: refresh })
  } finally {
    localStorage.clear()
    window.location.href = '/login'
  }
}

export function getStoredUser() {
  if (typeof window === 'undefined') return null
  const token = localStorage.getItem('access_token')
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload
  } catch { return null }
}
