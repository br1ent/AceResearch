<script setup>
import UserMenu from '@/components/navbar/userMenu/UserMenu.vue'
</script>

<template>
  <div class="navbar bg-base-100/80 backdrop-blur border-b border-base-200 sticky top-0 z-50">
    <!-- 左侧 Logo -->
    <div class="navbar-start">
      <router-link :to="{ name: 'home-index' }" class="flex items-center gap-2 ml-5 btn btn-sm btn-ghost">
        <span class="text-lg font-semibold tracking-tight">DeepResearch 深研</span>
      </router-link>
    </div>
    <!-- 右侧 -->
    <div class="navbar-end">
      <UserMenu />
    </div>
  </div>
</template>
