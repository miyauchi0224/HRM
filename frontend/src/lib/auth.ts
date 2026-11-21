import api, { fetchCsrfToken } from './api'

export interface LoginUser {
  id:         string
  email:      string
  role:       string
  full_name:  string
}

export interface LoginResponse {
  user: LoginUser
}

/** ログイン。トークンはサーバーが HttpOnly Cookie に保存する（本文には含まれない） */
export async function login(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>('/api/v1/auth/login/', { email, password })
  // ログインで CSRF トークンが入れ替わるため取り直す
  await fetchCsrfToken(true)
  return data
}

export async function logout() {
  try {
    await api.post('/api/v1/auth/logout/')
  } finally {
    window.location.href = '/login'
  }
}

/** ログイン済みならユーザー情報、未ログインなら null（ログイン画面へは移動しない） */
export async function fetchCurrentUser() {
  try {
    const { data } = await api.get('/api/v1/auth/me/', { skipAuthRedirect: true })
    return data
  } catch {
    return null
  }
}
