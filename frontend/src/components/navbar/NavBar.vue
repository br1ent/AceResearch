<script setup>
import { Sun, Moon } from '@lucide/vue'
import { useThemeStore } from '@/stores/theme.js'
import UserMenu from '@/components/navbar/userMenu/UserMenu.vue'

const themeStore = useThemeStore()
</script>

<template>
  <div class="navbar bg-base-100/80 backdrop-blur border-b border-base-200 sticky top-0 z-50">
    <!-- 左侧 -->
    <div class="navbar-start">
      <router-link :to="{ name: 'home-index' }" class="flex items-center gap-2 ml-5 btn btn-sm btn-ghost">
        <span class="text-lg font-semibold tracking-tight">AceResearch 研思</span>
      </router-link>
    </div>
    <!-- 右侧 -->
    <div class="navbar-end">
      <button class="btn btn-ghost btn-sm btn-circle mr-3" @click="themeStore.toggleTheme()" :title="themeStore.isDark ? '切换亮色模式' : '切换黑夜模式'">
        <Sun v-if="themeStore.isDark" class="w-5 h-5" />
        <Moon v-else class="w-5 h-5" />
      </button>

      <UserMenu />
    </div>
  </div>
</template>
