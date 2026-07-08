import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', () => {
  const id = ref(0)
  const username = ref("")
  const email = ref("")
  const photo = ref("")
  const accessToken = ref("")
  const hasPullUserInfo = ref(false)


  function isLogin() {
    return !!accessToken.value
  }

  function setAccessToken(token) {
    accessToken.value = token
  }

  function setUserInfo(data) {
    id.value = data.id
    username.value = data.username
    photo.value = data.photo
    email.value = data.email
  }

  function setHasPullUserInfo(newStatus) {
    hasPullUserInfo.value = newStatus
  }

  function logout() {
    id.value = 0
    username.value = ""
    photo.value = ""
    email.value = ""
    accessToken.value = ""
  }

  return {
    id,
    username,
    photo,
    email,
    accessToken,
    isLogin,
    setAccessToken,
    setUserInfo,
    logout,
    setHasPullUserInfo
  }
})
