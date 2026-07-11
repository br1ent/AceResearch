<script setup>
import NavBar from './components/navbar/NavBar.vue'
import { useUserStore } from '@/stores/user.js'

// 立即触发 auth 初始化，不阻塞渲染
const userStore = useUserStore()
userStore.initAuth()
</script>

<template>
  <NavBar />
  <router-view />
</template>
