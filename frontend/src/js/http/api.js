import axios from 'axios'

const http = axios.create({
  timeout: 30000,
  withCredentials: true,
})

// ---- 纯内存 token，不落盘 ----
let _accessToken = ''
let _onTokenRefreshed = null

export function setAccessToken(token) {
  _accessToken = token
}

export function getAccessToken() {
  return _accessToken
}

/** api.js 静默刷新成功后，通知 store 更新 accessToken ref */
export function onTokenRefreshed(fn) {
  _onTokenRefreshed = fn
}

// ---- 请求拦截器 ----
http.interceptors.request.use((config) => {
  if (_accessToken) {
    config.headers.Authorization = `Bearer ${_accessToken}`
  }
  return config
})

// ---- 刷新防重入 ----
let refreshPromise = null

function refreshAccessToken() {
  if (refreshPromise) return refreshPromise

  refreshPromise = http
    .post('/api/user/refresh')
    .then((res) => {
      const newToken = res.data?.data?.access_token
      if (newToken) {
        setAccessToken(newToken)
        _onTokenRefreshed?.(newToken)
      }
      return newToken
    })
    .catch(() => {
      setAccessToken('')
      _onTokenRefreshed?.('')
      return null
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

// ---- 响应拦截器：401 自动刷新 ----
http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status !== 401 || originalRequest.url === '/api/user/refresh') {
      return Promise.reject(error)
    }

    if (originalRequest._retry) {
      setAccessToken('')
      _onTokenRefreshed?.('')
      return Promise.reject(error)
    }
    originalRequest._retry = true

    const newToken = await refreshAccessToken()
    if (newToken) {
      originalRequest.headers.Authorization = `Bearer ${newToken}`
      return http(originalRequest)
    }

    return Promise.reject(error)
  }
)

export default http
