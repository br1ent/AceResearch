<script setup>
import { ref, onMounted } from 'vue'
import { MessageCircle, Trash2, Loader2, BookOpen, MessageCircle as ChatIcon } from '@lucide/vue'
import { useChatStore } from '@/stores/chat.js'

const chatStore = useChatStore()

const loading = ref(true)

const emit = defineEmits(['selectChat'])

onMounted(async () => {
  loading.value = true
  await chatStore.fetchConversations()
  loading.value = false
})

function selectChat(conv) {
  chatStore.selectConversation(conv)
  emit('selectChat', conv)
}

function formatTime(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) {
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}
</script>

<template>
  <div class="flex flex-col gap-1">
    <div v-if="loading" class="flex items-center justify-center py-8">
      <Loader2 class="w-5 h-5 animate-spin text-base-content/40" />
    </div>

    <div v-else-if="chatStore.conversations.length === 0" class="text-sm text-base-content/40 text-center py-8">
      暂无对话，开始一个新的研究吧
    </div>

    <template v-else>
      <div
        v-for="conv in chatStore.conversations"
        :key="conv.id"
        class="group flex items-center gap-3 px-3 py-3 rounded-lg hover:bg-base-200 cursor-pointer transition-colors"
        :class="{ 'bg-base-200': chatStore.currentConvId === conv.id }"
        @click="selectChat(conv)"
      >
        <div class="w-5 h-5 shrink-0 flex items-center justify-center">
          <BookOpen v-if="conv.mode === 'research'" class="w-4 h-4 text-info" />
          <ChatIcon v-else class="w-4 h-4 text-success" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <p class="text-sm font-medium truncate">{{ conv.title }}</p>
            <span
              class="text-[10px] px-1.5 py-0.5 rounded-full shrink-0"
              :class="conv.mode === 'research' ? 'bg-info/10 text-info' : 'bg-success/10 text-success'"
            >
              {{ conv.mode === 'research' ? '研究' : '闲聊' }}
            </span>
          </div>
          <p class="text-xs text-base-content/30">{{ formatTime(conv.updated_at) }}</p>
        </div>
        <!-- hover 时显示删除按钮（暂不实现删除功能） -->
        <button class="opacity-0 group-hover:opacity-100 btn btn-ghost btn-xs btn-circle transition-opacity" title="删除">
          <Trash2 class="w-4 h-4 text-base-content/40" />
        </button>
      </div>
    </template>
  </div>
</template>
