<script setup>
import { ref, onUnmounted, onMounted, watch, computed, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { Send, Loader2, BookOpen, MessageCircle, FileText } from '@lucide/vue'
import { useUserStore } from '@/stores/user.js'
import { useChatStore } from '@/stores/chat.js'
import AvatarBox from './AvatarBox.vue'

const userStore = useUserStore()
const chatStore = useChatStore()
const route = useRoute()

const inputText = ref('')
const inputRef = ref(null)

function focusInput() {
  nextTick(() => inputRef.value?.focus())
}

function scrollToBottom() {
  nextTick(() => {
    const el = document.querySelector('.msg-scroll-container')
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
  })
}

onMounted(() => {
  focusInput()
  if (chatStore.currentConvId && chatStore.isResearching) {
    chatStore.connectWebSocket(chatStore.currentConvId)
  }
})
watch(() => route.path, (to) => {
  if (to === '/chat') focusInput()
})

const visibleMessages = computed(() => {
  let msgs = chatStore.messages
  if (chatStore.mode === 'chat') {
    msgs = msgs.filter(m => m.msg_type === 'text' || m.msg_type === 'report')
  }
  // 按创建时间排序，保证消息顺序一致
  return [...msgs].sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
})

watch(visibleMessages, () => scrollToBottom(), { deep: true })

onUnmounted(() => {
  chatStore.disconnectWebSocket()
})

function submitRevise(msg) {
  const feedback = msg._reviseText?.trim()
  if (!feedback || !msg.plan?.report_id) return
  chatStore.revisePlan(msg.plan.report_id, feedback)
  msg._revised = true
  msg._showRevise = false
  msg._reviseText = ''
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || chatStore.isResearching) return
  inputText.value = ''
  await chatStore.sendMessage(text)
}

function formatTime(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return d.toLocaleTimeString()
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- 模式切换条 -->
    <div class="flex items-center justify-center gap-2 px-4 py-2 border-b border-base-200 bg-base-100/80">
      <button class="btn btn-sm gap-1.5" :class="chatStore.mode === 'chat' ? 'btn-neutral' : 'btn-ghost'"
        @click="chatStore.switchMode('chat')" :disabled="chatStore.isResearching || chatStore.isChatting">
        <MessageCircle class="w-4 h-4" /> 闲聊模式
      </button>
      <button class="btn btn-sm gap-1.5" :class="chatStore.mode === 'research' ? 'btn-neutral' : 'btn-ghost'"
        @click="chatStore.switchMode('research')" :disabled="chatStore.isResearching || chatStore.isChatting">
        <BookOpen class="w-4 h-4" /> 研究模式
      </button>
    </div>

    <div v-if="visibleMessages.length === 0" class="flex-1 flex flex-col items-center justify-center px-6">
      <template v-if="chatStore.mode === 'research'">
        <h2 class="text-2xl font-bold mb-2">{{ userStore.username }}，今天想研究些什么领域？</h2>
        <p class="text-base-content/50 text-center max-w-md">请输入一个研究主题，我将为你规划研究任务、搜索资料并生成报告</p>
      </template>
      <template v-else>
        <h2 class="text-2xl font-bold mb-2">👋 {{ userStore.username }}，有什么想聊的？</h2>
        <p class="text-base-content/50 text-center max-w-md">直接和我对话吧！需要深度研究时可以随时切换到研究模式</p>
      </template>
    </div>

    <!-- 消息列表 -->
    <div v-if="visibleMessages.length > 0" class="msg-scroll-container flex-1 overflow-y-auto px-6 py-4 space-y-4">
      <div v-if="chatStore.hasMore" class="flex justify-center">
        <button class="btn btn-ghost btn-sm text-base-content/50" @click="chatStore.loadMore()" :disabled="chatStore.isLoadingMore">
          <Loader2 v-if="chatStore.isLoadingMore" class="w-4 h-4 animate-spin" /><span v-else>加载更早的消息</span>
        </button>
      </div>

      <div v-for="(msg, i) in visibleMessages" :key="i" class="flex gap-3 items-start"
        :class="msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'">
        <AvatarBox :role="msg.role" />
        <div class="max-w-[70%] rounded-2xl px-4 py-2.5" :class="{
          'bg-success/20 rounded-tr-md': msg.role === 'user',
          'bg-base-200 rounded-tl-md': msg.role !== 'user',
          'border border-info/30 bg-info/5': msg.msg_type === 'agent_status',
          'border border-warning/30 bg-warning/5': msg.msg_type === 'error',
        }">
          <p class="text-sm whitespace-pre-wrap" v-if="msg.msg_type === 'report'">
            <span class="text-base-content/70">{{ msg.content }}</span>
          </p>
          <template v-else-if="msg.msg_type === 'plan_ready' && msg.plan">
            <p class="text-sm font-semibold mb-1"><FileText class="w-4 h-4 inline-block mr-1" />研究方案已生成</p>
            <p class="text-xs text-base-content/50">包含 {{ msg.plan.outline?.length || 0 }} 个章节，{{ msg.plan.subtasks?.length || 0 }} 个子任务</p>
            <p class="text-xs text-base-content/40 mt-1">右侧面板可查看完整方案</p>
            <div class="mt-2" v-if="!msg._revised">
              <button class="btn btn-sm btn-neutral" @click="chatStore.openPlanPanel()">查看方案</button>
            </div>
            <div v-if="msg._revised" class="mt-1 text-xs text-base-content/40">已提交修改，正在生成新方案...</div>
          </template>
          <p v-else class="text-sm whitespace-pre-wrap">{{ msg.content }}<span v-if="chatStore.isChatting && msg.role === 'assistant' && i === visibleMessages.length - 1" class="animate-pulse">▌</span></p>
          <p class="text-xs mt-1 text-base-content/40 text-right">{{ formatTime(msg.created_at) }}</p>
        </div>
      </div>

      <!-- 研究进度气泡 -->
      <div v-if="chatStore.mode === 'research' && chatStore.isResearching" class="flex gap-3 items-start">
        <AvatarBox role="assistant" />
        <div class="bg-base-200 rounded-2xl rounded-tl-md px-4 py-3 max-w-[70%] min-w-[260px]">
          <div class="flex items-center gap-2 mb-2">
            <Loader2 class="w-4 h-4 animate-spin text-info shrink-0" />
            <span class="text-sm text-base-content/70">{{ chatStore.researchMessage || '处理中...' }}</span>
          </div>
          <div class="flex items-center gap-2">
            <div class="flex-1 bg-base-300 rounded-full h-2">
              <div class="bg-info h-2 rounded-full transition-all duration-500 ease-out" :style="{ width: chatStore.researchProgress + '%' }"></div>
            </div>
            <span class="text-xs text-base-content/40 shrink-0">{{ Math.round(chatStore.researchProgress) }}%</span>
          </div>
          <p class="text-[10px] text-base-content/30 mt-2">研究进行中，请不要离开此页面</p>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="border-t border-base-200 p-4">
      <div class="max-w-4xl mx-auto flex gap-2">
        <input v-model="inputText" ref="inputRef" type="text" class="input input-bordered w-full rounded-full pl-4"
          :placeholder="chatStore.mode === 'research' ? (chatStore.isResearching ? '研究进行中...' : '输入研究主题...') : (chatStore.isChatting ? '输入新消息打断当前回复...' : '输入消息...')"
          :disabled="chatStore.isResearching" @keydown.enter="sendMessage" />
        <button class="btn btn-neutral btn-circle shrink-0" :disabled="!inputText.trim() || chatStore.isResearching" @click="sendMessage">
          <Send class="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
</template>
