<script setup>
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
    <div class="navbar-end gap-2">

      <router-link
        :to="{name:'chat-index'}"
        class="btn btn-ghost"
        active-class="btn-active"
      >
        研究界面
      </router-link>

      <div>
        <router-link
          :to="{name:'user-login-index'}"
          class="btn btn-ghost"
          active-class="btn-active"
        >
          登录
        </router-link>


        <router-link
          :to="{name:'user-register-index'}"
          class="btn btn-ghost"
          active-class="btn-active"
        >
          注册
        </router-link>
      </div>


    </div>

  </div>
</template>