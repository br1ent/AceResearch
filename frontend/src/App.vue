<script setup>
import { onMounted } from 'vue'
import NavBar from './components/navbar/NavBar.vue'
import { useUserStore } from '@/stores/user.js'

const userStore = useUserStore()

onMounted(async () => {
  // 首次访问，尝试用 refresh_token 恢复登录态
  await userStore.initAuth()
})
</script>

<template>
  <NavBar />
  <router-view />
</template>
