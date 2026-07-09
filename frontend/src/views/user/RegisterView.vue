<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import http from "@/js/http/api.js";

const username = ref("");
const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const errorMessage = ref("");

const router = useRouter();
</script>

<template>
  <main class="flex-1 flex items-center justify-center px-5 py-10 mt-15">
    <div class="card w-full max-w-sm bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-xl justify-center mb-2">注册</h2>
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
          <input type="password" class="input input-bordered w-full" v-model="password" />
        </div>
        <div class="form-control mb-4">
          <label class="label"><span class="label-text">确认密码</span></label>
          <input type="password" class="input input-bordered w-full" v-model="confirmPassword" />
        </div>

        <div v-if="errorMessage" class="text-error text-sm mb-2">
          {{ errorMessage }}
        </div>

        <button class="btn btn-neutral w-full" @click="handleRegister">注册</button>
        <p class="text-center text-sm mt-3 text-base-content/60">
          已有账号？<router-link :to="{ name: 'user-login-index' }" class="link link-neutral link-hover">登录</router-link>
        </p>
      </div>
    </div>
  </main>
</template>
