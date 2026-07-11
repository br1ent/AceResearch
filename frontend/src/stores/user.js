import { ref } from 'vue'
import { defineStore } from 'pinia'
import http, { setAccessToken as setApiToken, getAccessToken } from '@/js/http/api.js'

export const useUserStore = defineStore('user', () => {
  const id = ref(0)
  const username = ref("")
  const email = ref("")
  const photo = ref("")
  const hasPullUserInfo = ref(false)
  const accessToken = ref("")

  function isLogin() {
    return !!accessToken.value
  }

  function setAccessToken(token) {
    accessToken.value = token
  }

  function setUserInfo(data) {
    id.value = data.id
    username.value = data.username
    email.value = data.email
    photo.value = data.photo
  }

  function setHasPullUserInfo(newStatus) {
    hasPullUserInfo.value = newStatus
  }

  async function initAuth() {
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
  }

  function logout() {
    id.value = 0
    username.value = ""
    email.value = ""
    photo.value = ""
    accessToken.value = ""
  }

  return {
    id,
    email,
    username,
    photo,
    accessToken,
    hasPullUserInfo,
    setUserInfo,
    setAccessToken,
    setHasPullUserInfo,
    logout,
    isLogin,
    initAuth,
  }
})
