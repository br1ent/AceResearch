<script setup>

import {ref} from "vue";
import {useRouter} from "vue-router";
import http from "@/js/http/api.js";

const username = ref("")
const email = ref("")
const password = ref("")
const confirmPassword = ref("")
const errorMessage = ref("")

const EMAIL_RE = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

const router = useRouter()

async function handleReset() {
  errorMessage.value = ""

  if (!username.value) {
    errorMessage.value = "用户名不能为空!"
  } else if (username.value.length > 20) {
    errorMessage.value = "用户名不能超过20个字符!"
  } else if (!email.value) {
    errorMessage.value = "邮箱不能为空!"
  } else if (!EMAIL_RE.test(email.value)) {
    errorMessage.value = "邮箱格式不正确!"
  } else if (!password.value) {
    errorMessage.value = "密码不能为空!"
  } else if (password.value.length < 6) {
    errorMessage.value = "密码不能少于6位!"
  } else if (confirmPassword.value !== password.value) {
    errorMessage.value = "两次密码不一致!"
  } else {
    try {
      const res = await http.post("/api/user/reset-password", {
        email: email.value,
        username: username.value,
        password: password.value,
        confirm_password: confirmPassword.value
      })

      const data = res.data
      if (data.success) {
        await router.push({
          name: 'user-login-index'
        })
      } else {
        errorMessage.value = data.message
      }
    } catch (e) {
      console.error(e)
    }
  }
}
</script>

<template>
  <main class="flex-1 flex items-center justify-center px-5 py-10 mt-15">
    <div class="card w-full max-w-sm bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-xl justify-center mb-2">重置密码</h2>
        <div class="form-control mb-3">
          <label class="label"><span class="label-text">用户名</span></label>
          <input type="text" class="input input-bordered w-full" v-model="username" />
        </div>

        <div class="form-control mb-3">
          <label class="label"><span class="label-text">邮箱</span></label>
          <input type="email" class="input input-bordered w-full" v-model="email" />
        </div>

        <div class="form-control mb-4">
          <label class="label"><span class="label-text">密码</span></label>
          <input type="password"class="input input-bordered w-full" v-model="password" />
        </div>

        <div class="form-control mb-4">
          <label class="label"><span class="label-text">确认密码</span></label>
          <input type="password"class="input input-bordered w-full" v-model="confirmPassword" />
        </div>

        <div v-if="errorMessage" class="text-error text-sm mb-2">
          {{ errorMessage }}
        </div>

        <button class="btn btn-neutral w-full" @click="handleReset">重置</button>
        <p class="text-center text-sm mt-3 text-base-content/60">
          已有账号？
          <router-link :to="{name: 'user-login-index'}" class="link link-neutral link-hover">登录</router-link>
        </p>
        <p class="text-center text-sm text-base-content/60">
          还没有账号？
          <router-link :to="{name: 'user-register-index'}" class="link link-neutral link-hover">注册</router-link>
        </p>
      </div>
    </div>
  </main>
</template>

<style scoped>

</style>