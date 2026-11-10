<script setup>
import {Sun, Moon} from '@lucide/vue'
import { useThemeStore } from '@/js/theme.js'
import UserMenu from '@/components/navbar/userMenu/UserMenu.vue'
import {useUserStore} from "@/stores/user.js";
import {useChatStore} from "@/stores/chat.js";
import {useRoute, useRouter} from "vue-router";

const themeStore = useThemeStore()
const user = useUserStore()
const chat = useChatStore()
const route = useRoute()
const router = useRouter()

function isModeActive(mode) {
  return route.name === 'chat-index' && chat.mode === mode
}

function goMode(mode) {
  if (!user.isLogin()) {
    router.push({ name: 'user-login-index' })
    return
  }
  if (route.name === 'chat-index' && chat.mode === mode) return
  chat.switchMode(mode, true)
  if (route.name !== 'chat-index') {
    router.push({ name: 'chat-index' })
  }
}

function goPlaza() {
  if (user.isLogin()) {
    router.push({ name: 'plaza-index' })
  } else {
    router.push({ name: 'user-login-index' })
  }
}
</script>

<template>
  <div class="navbar bg-base-100/80 backdrop-blur border-b border-base-200 sticky top-0 z-50">
    <!-- 左侧 -->
    <div class="navbar-start">
      <router-link :to="{ name: 'home-index' }" class="flex items-center gap-2 ml-5 btn btn-sm btn-ghost">
        <span class="text-lg font-semibold tracking-tight">AceResearch 研思</span>
      </router-link>
    </div>
    <!-- 中间导航 -->
    <div class="navbar-center flex items-center gap-1">
      <button class="btn btn-sm px-4" :class="isModeActive('chat') ? 'btn-neutral' : 'btn-ghost'" @click="goMode('chat')">闲聊模式</button>
      <button class="btn btn-sm px-4" :class="isModeActive('research') ? 'btn-neutral' : 'btn-ghost'" @click="goMode('research')">研究模式</button>
      <button class="btn btn-sm px-4" :class="isModeActive('knowledge') ? 'btn-neutral' : 'btn-ghost'" @click="goMode('knowledge')">个人文档检索</button>
      <button class="btn btn-sm px-4" :class="route.name === 'plaza-index' ? 'btn-neutral' : 'btn-ghost'" @click="goPlaza">报告广场</button>
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
