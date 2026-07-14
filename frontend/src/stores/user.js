import { ref } from 'vue'
import { defineStore } from 'pinia'
import http, { setAccessToken as setApiToken, getAccessToken } from '@/js/http/api.js'

export const useUserStore = defineStore('user', () => {
  const id = ref(0)
  const username = ref("")
  const email = ref("")
  const photo = ref("")
  const createAt = ref("")
  const updateAt = ref("")
  const hasPullUserInfo = ref(false)
  const accessToken = ref("")

  const _authInitialized = ref(false)
  let _initPromise = null

  function isLogin() {
    return !!accessToken.value
  }

  /** 等待 auth 初始化完成 */
  function waitForAuth() {
    if (_authInitialized.value) return Promise.resolve()
    if (_initPromise) return _initPromise
    return Promise.resolve()
  }

  function setAccessToken(token) {
    accessToken.value = token
  }

  function setUserInfo(data) {
    id.value = data.id
    username.value = data.username
    email.value = data.email
    photo.value = data.photo
    if (data.create_at) createAt.value = data.create_at
    if (data.update_at) updateAt.value = data.update_at
  }

  function setHasPullUserInfo(newStatus) {
    hasPullUserInfo.value = newStatus
  }

  async function initAuth() {
    if (_initPromise) return await _initPromise

    _initPromise = (async () => {
      // 1. 用 refresh_token cookie 换取新的 access_token
      const refreshRes = await http.post('/api/user/refresh').catch(() => null)
      if (!refreshRes || !refreshRes.data?.success) {
        return false
      }

      const newToken = refreshRes.data.data.access_token
      setAccessToken(newToken)
      setApiToken(newToken)

      // 2. 用 access_token 获取用户信息
      const meRes = await http.get('/api/user/me').catch(() => null)
      if (meRes?.data?.success) {
        setUserInfo(meRes.data.data)
        setHasPullUserInfo(true)
      }

      return true
    })()

    const result = await _initPromise
    _authInitialized.value = true
    return result
  }

  function logout() {
    id.value = 0
    username.value = ""
    email.value = ""
    photo.value = ""
    createAt.value = ""
    updateAt.value = ""
    accessToken.value = ""
    _authInitialized.value = false
    _initPromise = null
  }

  return {
    id,
    email,
    username,
    photo,
    createAt,
    updateAt,
    accessToken,
    hasPullUserInfo,
    setUserInfo,
    setAccessToken,
    setHasPullUserInfo,
    logout,
    isLogin,
    initAuth,
    waitForAuth,
  }
})
