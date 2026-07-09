<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user.js";
import http from "@/js/http/api.js";

const email = ref("");
const password = ref("");
const errorMessage = ref("");

const router = useRouter();
const user = useUserStore();

const EMAIL_RE = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

async function handleLogin() {
  errorMessage.value = ""

  if (!email.value) {
    errorMessage.value = "邮箱不能为空!"
  } else if (!EMAIL_RE.test(email.value)) {
    errorMessage.value = "邮箱格式不正确!"
  } else if (!password.value) {
    errorMessage.value = "密码不能为空!"
  } else if (password.value.length < 6) {
    errorMessage.value = "密码不能少于6位!"
  } else {
    try {
       const res = await http.post("/api/user/login", {
         email: email.value,
         password: password.value
       })

      const data = res.data
      if (data.success) {
        user.setAccessToken(data.data.access_token)
        user.setUserInfo(data.data.user)

        await router.push({name: 'home-index'})
      } else {
        errorMessage.value = data.message
      }
    } catch {
    }
  }
}
</script>

<template>
  <main class="flex-1 flex items-center justify-center px-5 py-10 mt-15">
    <form @submit.prevent="handleLogin" class="card w-full max-w-sm bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-xl justify-center mb-2">登录</h2>
        <div class="form-control mb-3">
          <label class="label"><span class="label-text">邮箱</span></label>
          <input type="email" class="input input-bordered w-full" v-model="email"/>
        </div>
        <div class="form-control mb-4">
          <label class="label"><span class="label-text">密码</span></label>
          <input type="password" class="input input-bordered w-full" v-model="password" />
        </div>

        <div v-if="errorMessage" class="text-error text-sm mb-2">
          {{ errorMessage }}
        </div>

        <button class="btn btn-neutral w-full">登录</button>
        <p class="text-center text-sm mt-3 text-base-content/60">
          没有账号？
          <router-link :to="{ name: 'user-register-index' }" class="link link-neutral link-hover">注册</router-link>
        </p>
        <p class="text-center text-sm text-base-content/60">
          <router-link :to="{ name: 'user-resetpwd-index' }" class="link link-neutral link-hover">忘记密码？</router-link>
        </p>
      </div>
    </form>
  </main>
</template>
