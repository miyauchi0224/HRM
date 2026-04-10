import api from './api'

export interface LoginResponse {
  access_token:  string
  refresh_token: string
  user: {
    id:         string
    email:      string
    role:       string
    full_name:  string
  }
}

export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/api/v1/auth/login/', { email, password })
  localStorage.setItem('access_token',  data.access_token)
  localStorage.setItem('refresh_token', data.refresh_token)
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
    // JWT のペイロードをデコード（署名検証なし・表示用のみ）
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload
  } catch { return null }
}
