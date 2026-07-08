<script setup>
import UserMenu from "@/components/navbar/userMenu/UserMenu.vue";
</script>

<template>
  <div class="navbar bg-base-100 shadow-sm">

    <!-- 左侧 Logo -->
    <div class="navbar-start">
      <router-link
        :to="{name:'home-index'}"
        class="btn btn-ghost text-xl"
      >
        基于多智能体的研究助手
      </router-link>
    </div>

    <!-- 右侧导航 -->
    <div class="navbar-end gap-10">

      <router-link
        :to="{name:'chat-index'}"
        class="btn btn-ghost"
      >
        研究界面
      </router-link>

      <UserMenu/>
    </div>

  </div>
</template>