<script setup>
import { useRouter } from 'vue-router'
import { Home } from '@lucide/vue'

const router = useRouter()
</script>

<template>
  <main class="flex-1 flex flex-col items-center justify-center text-center px-6">
    <h1 class="text-8xl font-black tracking-tight text-base-content/10">404</h1>
    <h2 class="text-2xl font-semibold mt-2 mb-3">页面不存在</h2>
    <p class="text-base-content/50 max-w-md mb-8">你访问的页面可能已被删除、移动或从未存在过</p>
    <router-link :to="{ name: 'home-index' }" class="btn btn-neutral gap-2">
      <Home class="w-4 h-4" /> 返回首页
    </router-link>
  </main>
</template>
