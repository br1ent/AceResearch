import { ref } from 'vue'
import { defineStore } from 'pinia'
import http, { setAccessToken, getAccessToken } from '@/js/http/api.js'

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
    isLogin
  }
})
