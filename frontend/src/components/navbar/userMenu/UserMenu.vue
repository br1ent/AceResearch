<script setup>
import {useUserStore} from "@/stores/user.js";

const user = useUserStore()

function closeMenu() {
  const element = document.activeElement
  if (element && element instanceof HTMLElement) element.blur()
}
</script>

<template>
  <div v-if="!user.isLogin()">
    <router-link
      :to="{name:'user-login-index'}"
      class="btn btn-ghost"
    >
      登录
    </router-link>

    <router-link
      :to="{name:'user-register-index'}"
      class="btn btn-ghost"
    >
      注册
    </router-link>
  </div>

  <div v-else class="dropdown dropdown-end">
    <div tabindex="0" role="button" class="btn btn-ghost btn-circle avatar">
      <div class="w-10 rounded-full">
        <img :src="user.photo" alt="用户头像">
      </div>
    </div>
    <ul
      tabindex="0"
      class="menu menu-sm dropdown-content bg-base-100 rounded-box z-1 w-52 p-2 shadow"
    >
      <li>
        <router-link :to="{name: 'report-index'}" class="text-sm font-bold" @click="closeMenu">我的报告</router-link>
      </li>
      <li></li>
      <li>
        <a class="text-error font-bold text-sm">退出登录</a>
      </li>
    </ul>
  </div>
</template>

<style scoped>

</style>