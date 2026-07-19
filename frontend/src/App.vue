<script setup>
import NavBar from './components/navbar/NavBar.vue'
import { useUserStore } from '@/stores/user.js'
import { useThemeStore } from '@/stores/theme.js'

// 立即触发 auth 初始化，不阻塞渲染
const userStore = useUserStore()
userStore.initAuth()

// 初始化主题
const themeStore = useThemeStore()
themeStore.initTheme()
</script>

<template>
  <NavBar />
  <router-view />
</template>
