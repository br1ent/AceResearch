<script setup>
import { ref, onMounted } from 'vue'
import { Sparkles, FileText, Microscope } from '@lucide/vue'
import http from '@/js/http/api.js'

const publishedReports = ref(0)
const researches = ref(0)

onMounted(async () => {
  try {
    const res = await http.get('/api/plaza/stats/today')
    if (res.data?.success) {
      publishedReports.value = res.data.data.published_reports_today
      researches.value = res.data.data.researches_today
    }
  } catch (e) { console.error('获取今日统计失败', e) }
})
</script>

<template>
  <main class="flex-1">
    <!-- Hero -->
    <section class="max-w-4xl mx-auto px-6 pt-24 pb-10 text-center">
      <div class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
        <Sparkles class="w-3.5 h-3.5" />
        多 Agent 协作
      </div>
      <h1 class="text-5xl font-bold tracking-tight mb-5">
        AceResearch 研思
      </h1>
      <p class="text-lg text-base-content/60 max-w-xl mx-auto leading-relaxed">
        基于多 Agent 协作的深度研究平台
      </p>
      <p class="text-sm text-base-content/40 max-w-md mx-auto mt-3 leading-relaxed">
        闲聊问答 · 自动生成研究报告 · 个人文档检索，通过顶部导航栏进入对应功能
      </p>
    </section>

    <!-- 今日统计 -->
    <section class="max-w-2xl mx-auto px-6 pb-24">
      <div class="grid grid-cols-2 gap-6">
        <div class="card bg-base-200/50 border border-base-300">
          <div class="card-body items-center py-8 gap-2">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center bg-primary/10">
              <FileText class="w-5 h-5 text-primary" />
            </div>
            <p class="text-4xl font-bold leading-none mt-1">{{ publishedReports }}</p>
            <p class="text-sm text-base-content/50">今日发布报告</p>
          </div>
        </div>
        <div class="card bg-base-200/50 border border-base-300">
          <div class="card-body items-center py-8 gap-2">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center bg-secondary/10">
              <Microscope class="w-5 h-5 text-secondary" />
            </div>
            <p class="text-4xl font-bold leading-none mt-1">{{ researches }}</p>
            <p class="text-sm text-base-content/50">今日研究次数</p>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>
