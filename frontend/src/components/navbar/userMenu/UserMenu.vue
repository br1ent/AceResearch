<script setup>
import { useUserStore } from "@/stores/user.js";
import { useChatStore } from "@/stores/chat.js";
import http from "@/js/http/api.js";
import { useRouter } from "vue-router";
import { User, FileText, LogOut, BookOpen } from '@lucide/vue';

const user = useUserStore();
const chat = useChatStore();
const router = useRouter();

function closeMenu() {
  const el = document.activeElement;
  if (el && el instanceof HTMLElement) el.blur();
}

async function handleLogout() {
  try {
    const res = await http.post("/api/user/logout");
    if (res.data.success) {
      user.logout();
      chat.resetStore();
      await router.push({ name: "user-login-index" });
    } else {
      alert("服务器异常，请稍后重试!");
    }
  } catch (e) {
    console.error(e);
  }
}
</script>

<template>
  <div v-if="!user.isLogin()">
    <router-link :to="{ name: 'user-login-index' }" class="btn btn-ghost">
      登录
    </router-link>
    <router-link :to="{ name: 'user-register-index' }" class="btn btn-ghost">
      注册
    </router-link>
  </div>

  <div v-else class="dropdown dropdown-end">
    <div tabindex="0" role="button" class="btn btn-ghost btn-circle avatar">
      <div class="w-10 rounded-full">
        <img :src="user.photo" alt="用户头像" />
      </div>
    </div>
    <ul
      tabindex="0"
      class="menu dropdown-content bg-base-100 rounded-box z-10 w-48 shadow"
    >
      <!-- 用户名 -->
      <li class="menu-title px-4 pt-3 pb-1 text-xs text-base-content/50">
        账号
      </li>
      <li>
        <router-link :to="{name: 'user-space-index'}" class="flex items-center gap-3 px-4 py-2 font-semibold min-w-0" @click="closeMenu">
          <User class="w-4 h-4 shrink-0" />
          <span class="truncate block max-w-[120px]">{{ user.username }}</span>
        </router-link>
      </li>

      <li></li>

      <!-- 我的报告 -->
      <li>
        <router-link :to="{ name: 'report-index' }" class="flex items-center gap-3 px-4 py-2" @click="closeMenu">
          <FileText class="w-4 h-4 shrink-0" />
          <span>我的报告</span>
        </router-link>
      </li>

      <!-- 我的文档 -->
      <li>
        <router-link :to="{ name: 'documents-index' }" class="flex items-center gap-3 px-4 py-2" @click="closeMenu">
          <BookOpen class="w-4 h-4 shrink-0" />
          <span>我的文档</span>
        </router-link>
      </li>

      <!-- 退出登录 -->
      <li>
        <a class="flex items-center gap-3 px-4 py-2 text-error" @click="handleLogout">
          <LogOut class="w-4 h-4 shrink-0" />
          <span>退出登录</span>
        </a>
      </li>
    </ul>
  </div>
</template>
