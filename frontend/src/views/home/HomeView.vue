<script setup>
import { useRouter } from 'vue-router'
import { MessageCircle, BookOpen, Search, ArrowRight, Sparkles } from '@lucide/vue'
import { useUserStore } from '@/stores/user.js'

const router = useRouter()
const user = useUserStore()

function goChat() {
  if (user.isLogin()) {
    router.push({ name: 'chat-index' })
  } else {
    router.push({ name: 'user-login-index' })
  }
}

const features = [
  {
    icon: MessageCircle,
    title: '闲聊模式',
    desc: '基于 DeepSeek 大模型的智能对话，支持联网搜索、天气查询、实时时间等工具调用',
    color: 'text-primary',
  },
  {
    icon: BookOpen,
    title: '研究模式',
    desc: '多 Agent 协作完成深度研究：规划、搜索、分析、撰写、审查，自动生成高质量报告',
    color: 'text-secondary',
  },
  {
    icon: Search,
    title: '个人文档检索',
    desc: '上传你的文档，基于向量检索和重排序技术，精准回答文档内容相关问题',
    color: 'text-accent',
  },
]
</script>

<template>
  <main class="flex-1">
    <!-- Hero -->
    <section class="max-w-4xl mx-auto px-6 pt-20 pb-16 text-center">
      <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
        <Sparkles class="w-3.5 h-3.5" />
        多 Agent 协作
      </div>
      <h1 class="text-5xl font-bold tracking-tight mb-4">
        AceResearch 研思
      </h1>
      <p class="text-xl text-base-content/60 max-w-xl mx-auto mb-8 leading-relaxed">
        基于多 Agent 协作的深度研究平台，支持智能对话、自动生成研究报告和个人知识库问答
      </p>
      <button class="btn btn-neutral btn-lg gap-2 px-8 rounded-full" @click="goChat">
        开始使用
        <ArrowRight class="w-5 h-5" />
      </button>
    </section>

    <!-- Features -->
    <section class="max-w-5xl mx-auto px-6 pb-20">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          v-for="f in features"
          :key="f.title"
          class="card bg-base-200/50 border border-base-300 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
        >
          <div class="card-body gap-3">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center bg-base-300/50">
              <component :is="f.icon" class="w-5 h-5" :class="f.color" />
            </div>
            <h3 class="card-title text-base">{{ f.title }}</h3>
            <p class="text-sm text-base-content/60 leading-relaxed">{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>
