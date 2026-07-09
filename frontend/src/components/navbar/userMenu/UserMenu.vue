<script setup>
import {useUserStore} from "@/stores/user.js";
import http from "@/js/http/api.js";
import {useRouter} from "vue-router";

const user = useUserStore()
const router = useRouter()

function closeMenu() {
  const element = document.activeElement
  if (element && element instanceof HTMLElement) element.blur()
}

async function handleLogout() {
  try {
    const res = await http.post("/api/user/logout")

    const data = res.data
    if (data.success) {
      user.logout()
      await router.push({
        name: 'user-login-index'
      })
    } else {
      alert("服务器异常，请稍后重试!")
    }
  } catch (e) {
    console.error(e)
  }
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
        <a class="text-error font-bold text-sm" @click="handleLogout">退出登录</a>
      </li>
    </ul>
  </div>
</template>

<style scoped>

</style>