import axios from 'axios'

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
  withCredentials: true,
})

// リクエスト時にアクセストークンを付与
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// 401 が返ったらリフレッシュトークンで再試行
api.interceptors.response.use(
  (res) => res,
  async (err) => {
    console.error('[API Error]', err.config?.url, err.response?.status, err.response?.data)

    if (err.response?.status === 401) {
      const refresh = localStorage.getItem('refresh_token')
      console.log('[Auth] 401 detected, refresh token exists:', !!refresh)

      if (refresh) {
        try {
          const { data } = await axios.post(
            `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/api/v1/auth/refresh/`,
            { refresh }
          )
          console.log('[Auth] Token refresh success')
          localStorage.setItem('access_token',  data.access)
          if (data.refresh) localStorage.setItem('refresh_token', data.refresh)
          err.config.headers.Authorization = `Bearer ${data.access}`
          return api(err.config)
        } catch (refreshErr: any) {
          const msg = `[Auth] Token refresh failed: ${refreshErr.response?.status} ${JSON.stringify(refreshErr.response?.data)}`
          console.error(msg)
          localStorage.setItem('debug_last_error', msg)
          localStorage.clear()
          localStorage.setItem('debug_last_error', msg)  // clear後に再セット
          window.location.href = '/login'
        }
      } else {
        const msg = `[Auth] No refresh token. Original error: ${err.config?.url} ${err.response?.status} ${JSON.stringify(err.response?.data)}`
        localStorage.setItem('debug_last_error', msg)
        localStorage.clear()
        localStorage.setItem('debug_last_error', msg)
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

export default api
