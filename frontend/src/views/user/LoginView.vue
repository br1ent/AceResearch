<script setup>
</script>

<template>
  <main class="flex-1 flex items-center justify-center px-5 py-10 mt-15">
    <div class="card w-full max-w-sm bg-base-100 shadow-xl">
      <div class="card-body">
        <h2 class="card-title text-xl justify-center mb-2">登录</h2>
        <div class="form-control mb-3">
          <label class="label"><span class="label-text">邮箱</span></label>
          <input type="email" class="input input-bordered w-full" />
        </div>
        <div class="form-control mb-4">
          <label class="label"><span class="label-text">密码</span></label>
          <input type="password" class="input input-bordered w-full" />
        </div>
        <button class="btn btn-neutral w-full">登录</button>
        <p class="text-center text-sm mt-3 text-base-content/60">
          没有账号？<router-link :to="{name: 'user-register-index'}" class="link link-neutral link-hover">注册</router-link>
        </p>
      </div>
    </div>
  </main>
</template>
