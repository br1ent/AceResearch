<script setup>
import { ref, onUnmounted, computed } from 'vue'
import { Send, Loader2, BookOpen, MessageCircle } from '@lucide/vue'
import { useUserStore } from '@/stores/user.js'
import { useChatStore } from '@/stores/chat.js'
import AvatarBox from './AvatarBox.vue'

const userStore = useUserStore()
const chatStore = useChatStore()

const inputText = ref('')

// 闲聊模式只显示文本消息；研究模式显示全部
const visibleMessages = computed(() => {
  if (chatStore.mode === 'chat') {
    return chatStore.messages.filter(m => m.msg_type === 'text' || m.msg_type === 'report')
  }
  return chatStore.messages
})

onUnmounted(() => {
  chatStore.disconnectWebSocket()
})

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || chatStore.isResearching || chatStore.isChatting) return

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
      <button
        class="btn btn-sm gap-1.5"
        :class="chatStore.mode === 'chat' ? 'btn-neutral' : 'btn-ghost'"
        @click="chatStore.switchMode('chat')"
        :disabled="chatStore.isResearching || chatStore.isChatting"
      >
        <MessageCircle class="w-4 h-4" />
        闲聊模式
      </button>
      <button
        class="btn btn-sm gap-1.5"
        :class="chatStore.mode === 'research' ? 'btn-neutral' : 'btn-ghost'"
        @click="chatStore.switchMode('research')"
        :disabled="chatStore.isResearching || chatStore.isChatting"
      >
        <BookOpen class="w-4 h-4" />
        研究模式
      </button>
    </div>

    <!-- 欢迎区域 -->
    <div v-if="visibleMessages.length === 0" class="flex-1 flex flex-col items-center justify-center px-6">
      <!-- 研究模式 -->
      <template v-if="chatStore.mode === 'research'">
        <h2 class="text-2xl font-bold mb-2">
          {{ userStore.username }}，今天想研究些什么领域？
        </h2>
        <p class="text-base-content/50 text-center max-w-md">
          请输入一个研究主题，我将为你规划研究任务、搜索资料并生成报告
        </p>
      </template>
      <!-- 闲聊模式 -->
      <template v-else>
        <h2 class="text-2xl font-bold mb-2">
          👋 {{ userStore.username }}，有什么想聊的？
        </h2>
        <p class="text-base-content/50 text-center max-w-md">
          直接和我对话吧！需要深度研究时可以随时切换到研究模式
        </p>
      </template>
    </div>

    <!-- 消息列表 -->
    <div v-else class="flex-1 overflow-y-auto px-6 py-4 space-y-4">
      <!-- 加载更早消息 -->
      <div v-if="chatStore.hasMore" class="flex justify-center">
        <button class="btn btn-ghost btn-sm text-base-content/50" @click="chatStore.loadMore()" :disabled="chatStore.isLoadingMore">
          <Loader2 v-if="chatStore.isLoadingMore" class="w-4 h-4 animate-spin" />
          <span v-else>加载更早的消息</span>
        </button>
      </div>
      <div
        v-for="(msg, i) in visibleMessages"
        :key="i"
        class="flex gap-3 items-start"
        :class="msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'"
      >
        <AvatarBox :role="msg.role" />

        <div
          class="max-w-[70%] rounded-2xl px-4 py-2.5"
          :class="{
            'bg-success/20 rounded-tr-md': msg.role === 'user',
            'bg-base-200 rounded-tl-md': msg.role !== 'user',
            'border border-info/30 bg-info/5': msg.msg_type === 'agent_status',
            'border border-warning/30 bg-warning/5': msg.msg_type === 'error',
          }"
        >
          <p class="text-sm whitespace-pre-wrap" v-if="msg.msg_type === 'report'">
            📄 <strong>研究报告已生成</strong>
            <br><br>
            <span class="text-base-content/70">{{ msg.content }}</span>
          </p>
          <!-- 研究方案（带确认按钮） -->
          <template v-else-if="msg.msg_type === 'plan_ready' && msg.plan">
            <p class="text-sm font-semibold mb-2">📋 研究方案</p>
            <div class="text-sm text-base-content/80 space-y-2">
              <div v-if="msg.plan.outline && msg.plan.outline.length">
                <p class="font-medium text-xs text-base-content/50 mb-1">大纲</p>
                <p v-for="(item, j) in msg.plan.outline" :key="j" class="whitespace-pre-wrap">- {{ item }}</p>
              </div>
              <div v-if="msg.plan.subtasks && msg.plan.subtasks.length">
                <p class="font-medium text-xs text-base-content/50 mt-2 mb-1">研究子任务</p>
                <p v-for="(t, j) in msg.plan.subtasks" :key="j" class="whitespace-pre-wrap">{{ j + 1 }}. <strong>{{ t.title }}</strong> — {{ t.description }}</p>
              </div>
            </div>
            <div class="flex gap-2 mt-3">
              <button class="btn btn-sm btn-primary" @click="chatStore.confirmResearch()" :disabled="chatStore.isResearching">
                确认并开始研究
              </button>
              <button class="btn btn-sm btn-ghost" disabled>
                修改方向（输入新消息修改）
              </button>
            </div>
          </template>
          <p v-else class="text-sm whitespace-pre-wrap">{{ msg.content }}</p>
          <p class="text-xs mt-1 text-base-content/40 text-right">{{ formatTime(msg.created_at) }}</p>
        </div>
      </div>

      <!-- 闲聊中的等待 -->
      <div v-if="chatStore.isChatting" class="flex gap-3 items-start">
        <AvatarBox role="assistant" />
        <div class="bg-base-200 rounded-2xl rounded-tl-md px-4 py-2.5">
          <div class="flex items-center gap-2">
            <Loader2 class="w-4 h-4 animate-spin text-info" />
            <span class="text-sm text-base-content/70">思考中...</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="border-t border-base-200 p-4">
      <div class="max-w-4xl mx-auto flex gap-2">
        <div class="flex-1 relative">
          <input
            v-model="inputText"
            type="text"
            class="input input-bordered w-full rounded-full pl-4 pr-12"
            :placeholder="chatStore.mode === 'research'
              ? (chatStore.isResearching ? '研究进行中...' : '输入研究主题...')
              : (chatStore.isChatting ? '等待回复...' : '输入消息...')"
            :disabled="chatStore.isResearching || chatStore.isChatting"
            @keydown.enter="sendMessage"
          />
        </div>
        <button
          class="btn btn-neutral btn-circle shrink-0"
          :disabled="!inputText.trim() || chatStore.isResearching || chatStore.isChatting"
          @click="sendMessage"
        >
          <Send class="w-4 h-4" />
        </button>
      </div>
    </div>
  </div>
</template>
