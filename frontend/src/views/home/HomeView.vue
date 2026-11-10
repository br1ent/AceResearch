<script setup>
import { Sparkles } from '@lucide/vue'
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
        基于 LangGraph 多 Agent 协作的科研辅助平台设计与实现，支持用户闲聊、自动生成研究报告和基于个人上传文档进行问答，生成的研究报告也可以
        按需发布到报告广场里面，以供其他用户参考。
      </p>
    </section>
  </main>
</template>
