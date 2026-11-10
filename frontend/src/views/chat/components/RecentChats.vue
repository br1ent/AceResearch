<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Trash2, Loader2, BookOpen, MessageCircle as ChatIcon, Pencil } from '@lucide/vue'
import { useChatStore } from '@/stores/chat.js'

const chatStore = useChatStore()
const route = useRoute()

const loading = ref(true)
const showDeleteModal = ref(false)
const deletingConv = ref(null)
const isDeleting = ref(false)
const showRenameModal = ref(false)
const renamingConv = ref(null)
const renameText = ref('')
const isRenaming = ref(false)

const emit = defineEmits(['selectChat'])

async function loadConversations() {
  loading.value = true
  await chatStore.fetchConversations()
  loading.value = false
  // 自动选中最近一条与当前模式相同的对话，避免切换模式后被其他模式的对话抢占
  if (chatStore.conversations.length > 0 && !chatStore.currentConvId) {
    const match = chatStore.conversations.find(c => c.mode === chatStore.mode)
    if (match) selectChat(match)
  }
}

onMounted(loadConversations)
watch(() => route.path, (to, from) => {
  if (to === '/chat' && from !== '/chat') loadConversations()
})

function selectChat(conv) {
  chatStore.selectConversation(conv)
  emit('selectChat', conv)
}

function openDeleteModal(conv, event) {
  event.stopPropagation()
  deletingConv.value = conv
  showDeleteModal.value = true
}

function openRenameModal(conv, event) {
  event.stopPropagation()
  renamingConv.value = conv
  renameText.value = conv.title
  showRenameModal.value = true
}

function closeRenameModal() {
  showRenameModal.value = false
  renamingConv.value = null
}

async function confirmRename() {
  const title = renameText.value.trim()
  if (!title) return
  isRenaming.value = true
  await chatStore.renameConversation(renamingConv.value.id, title)
  isRenaming.value = false
  closeRenameModal()
}

function closeDeleteModal() {
  showDeleteModal.value = false
  deletingConv.value = null
}

async function confirmDelete() {
  if (!deletingConv.value) return
  isDeleting.value = true
  await chatStore.deleteConversation(deletingConv.value.id)
  isDeleting.value = false
  closeDeleteModal()
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
            <p class="text-sm font-medium truncate" :title="conv.title">{{ conv.title }}</p>
            <span
              class="text-[10px] px-1.5 py-0.5 rounded-full shrink-0"
              :class="conv.mode === 'research' ? 'bg-info/10 text-info' : conv.mode === 'knowledge' ? 'bg-accent/10 text-accent' : 'bg-success/10 text-success'"
            >
              {{ conv.mode === 'research' ? '研究' : conv.mode === 'knowledge' ? '文档检索' : '闲聊' }}
            </span>
          </div>
          <p class="text-xs text-base-content/30">{{ formatTime(conv.updated_at) }}</p>
        </div>
        <!-- hover 时显示重命名 / 删除按钮 -->
        <button class="opacity-0 group-hover:opacity-100 btn btn-ghost btn-xs btn-circle transition-opacity" title="重命名" @click.stop="openRenameModal(conv, $event)">
          <Pencil class="w-4 h-4 text-base-content/40" />
        </button>
        <button class="opacity-0 group-hover:opacity-100 btn btn-ghost btn-xs btn-circle transition-opacity" title="删除" @click.stop="openDeleteModal(conv, $event)">
          <Trash2 class="w-4 h-4 text-base-content/40" />
        </button>
      </div>
    </template>
  </div>

  <!-- 重命名模态框 -->
  <div v-if="showRenameModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="closeRenameModal">
    <div class="card bg-base-100 shadow-xl max-w-sm w-full mx-4">
      <div class="card-body">
        <h3 class="card-title text-lg">重命名对话</h3>
        <input v-model="renameText" type="text" maxlength="100" class="input input-bordered w-full mt-2"
          placeholder="输入新的对话标题" @keydown.enter="confirmRename" />
        <div class="card-actions justify-end gap-2 mt-4">
          <button class="btn bg-base-300 text-base-content border-none hover:bg-base-300/80" @click="closeRenameModal">
            取消
          </button>
          <button class="btn btn-neutral" :disabled="isRenaming || !renameText.trim()" @click="confirmRename">
            <Loader2 v-if="isRenaming" class="w-4 h-4 animate-spin" />
            保存
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- 删除确认模态框 -->
  <div v-if="showDeleteModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" @click.self="closeDeleteModal">
    <div class="card bg-base-100 shadow-xl max-w-sm w-full mx-4">
      <div class="card-body">
        <h3 class="card-title text-lg">确认删除</h3>
        <p class="text-sm text-base-content/70 py-2">
          确定删除对话 <strong>"{{ deletingConv?.title }}"</strong> 吗？此操作不可撤销。
        </p>
        <div class="card-actions justify-end gap-2 mt-2">
          <button class="btn bg-base-300 text-base-content border-none hover:bg-base-300/80" @click="closeDeleteModal">
            取消
          </button>
          <button class="btn btn-error" :disabled="isDeleting" @click="confirmDelete">
            <Loader2 v-if="isDeleting" class="w-4 h-4 animate-spin" />
            <Trash2 v-else class="w-4 h-4" />
            确认删除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
