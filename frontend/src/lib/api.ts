import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

/**
 * API クライアント（v1.3: HttpOnly Cookie 方式）
 *
 * - ログイン用トークンはサーバーが HttpOnly Cookie に保存する。JavaScript では一切扱わない
 * - POST / PUT / PATCH / DELETE には CSRF トークンを X-CSRFToken ヘッダーで付ける
 * - 401 になったら /auth/refresh/ を1回だけ呼んで再送する。失敗したらログイン画面へ
 */
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

type RetryConfig = InternalAxiosRequestConfig & {
  _retriedAuth?: boolean
  _retriedCsrf?: boolean
  /** true のとき 401 でもログイン画面へ移動しない（ログイン状態の確認用） */
  skipAuthRedirect?: boolean
}

declare module 'axios' {
  interface AxiosRequestConfig {
    skipAuthRedirect?: boolean
  }
}

const api = axios.create({
  baseURL: BASE_URL,
  withCredentials: true,
})

const UNSAFE_METHODS = ['post', 'put', 'patch', 'delete']
const AUTH_PATHS = ['/api/v1/auth/login/', '/api/v1/auth/refresh/', '/api/v1/auth/logout/', '/api/v1/auth/csrf/']

let csrfToken: string | null = null
let csrfPromise: Promise<string> | null = null

export async function fetchCsrfToken(force = false): Promise<string> {
  if (csrfToken && !force) return csrfToken
  if (!csrfPromise || force) {
    csrfPromise = axios
      .get<{ csrfToken: string }>(`${BASE_URL}/api/v1/auth/csrf/`, { withCredentials: true })
      .then(({ data }) => {
        csrfToken = data.csrfToken
        return data.csrfToken
      })
      .finally(() => { csrfPromise = null })
  }
  return csrfPromise
}

api.interceptors.request.use(async (config) => {
  if (UNSAFE_METHODS.includes((config.method ?? 'get').toLowerCase())) {
    config.headers['X-CSRFToken'] = await fetchCsrfToken()
  }
  return config
})

let refreshPromise: Promise<void> | null = null

function refreshSession(): Promise<void> {
  if (!refreshPromise) {
    refreshPromise = fetchCsrfToken()
      .then((token) =>
        axios.post(`${BASE_URL}/api/v1/auth/refresh/`, {}, {
          withCredentials: true,
          headers: { 'X-CSRFToken': token },
        }),
      )
      .then(() => undefined)
      .finally(() => { refreshPromise = null })
  }
  return refreshPromise
}

function goToLogin() {
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
    window.location.href = '/login'
  }
}

api.interceptors.response.use(
  (res) => res,
  async (err: AxiosError<{ detail?: string }>) => {
    const config = err.config as RetryConfig | undefined
    const status = err.response?.status
    const url = config?.url ?? ''
    if (!config || AUTH_PATHS.some((p) => url.includes(p))) return Promise.reject(err)

    // CSRF トークンが古い（ログイン・ログアウトで入れ替わった）場合は取り直して1回だけ再送
    if (status === 403 && !config._retriedCsrf && String(err.response?.data?.detail ?? '').includes('CSRF')) {
      config._retriedCsrf = true
      config.headers['X-CSRFToken'] = await fetchCsrfToken(true)
      return api(config)
    }

    if (status === 401 && !config._retriedAuth) {
      config._retriedAuth = true
      try {
        await refreshSession()
        return api(config)
      } catch {
        if (!config.skipAuthRedirect) goToLogin()
      }
    } else if (status === 401 && !config.skipAuthRedirect) {
      goToLogin()
    }
    return Promise.reject(err)
  },
)

export default api
