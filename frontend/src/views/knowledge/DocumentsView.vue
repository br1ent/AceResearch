<script setup>
import { onMounted, ref } from 'vue'
import { Upload, FileText, Trash2, Loader2, AlertTriangle } from '@lucide/vue'
import { useKnowledgeStore } from '@/stores/knowledge.js'

const store = useKnowledgeStore()
const dragOver = ref(false)
const error = ref('')

onMounted(() => store.fetchDocuments())

function onDragOver(e) {
  e.preventDefault()
  dragOver.value = true
}
function onDragLeave() { dragOver.value = false }

async function onDrop(e) {
  e.preventDefault()
  dragOver.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) await handleFile(file)
}

async function onFileChange(e) {
  const file = e.target?.files?.[0]
  if (file) await handleFile(file)
  e.target.value = ''
}

async function handleFile(file) {
  error.value = ''
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!['pdf', 'txt', 'md', 'docx'].includes(ext)) {
    error.value = '仅支持 PDF、TXT、MD、DOCX 格式'
    return
  }
  if (store.documents.length >= 3) {
    error.value = '已达到上传上限（3 份）'
    return
  }
  try {
    await store.uploadDocument(file)
  } catch (e) {
    error.value = e.response?.data?.detail || '上传失败'
  }
}

function fileIcon(type) {
  if (type === 'pdf') return 'text-red-500'
  if (type === 'docx') return 'text-blue-500'
  return 'text-base-content/60'
}
</script>

<template>
  <div class="max-w-2xl mx-auto py-8 px-4">
    <h1 class="text-2xl font-bold mb-6">我的文档</h1>

    <!-- 上传区域 -->
    <div
      class="border-2 border-dashed rounded-2xl p-12 text-center mb-6 transition-colors cursor-pointer"
      :class="{
        'border-base-300 bg-base-200/50 hover:border-info/50': !dragOver && store.documents.length < 3,
        'border-info bg-info/5': dragOver,
        'border-base-200 bg-base-100 opacity-50 cursor-not-allowed': store.documents.length >= 3,
      }"
      @dragover="onDragOver"
      @dragleave="onDragLeave"
      @drop="onDrop"
      @click="store.documents.length < 3 && $refs.fileInput?.click()"
    >
      <input
        type="file"
        accept=".pdf,.txt,.md,.docx"
        class="hidden"
        ref="fileInput"
        @change="onFileChange"
        :disabled="store.documents.length >= 3"
      />
      <div v-if="store.uploading" class="flex flex-col items-center gap-2">
        <Loader2 class="w-8 h-8 animate-spin text-info" />
        <span class="text-base-content/70">正在处理文档...</span>
      </div>
      <div v-else class="flex flex-col items-center gap-3">
        <Upload class="w-10 h-10 text-base-content/30" />
        <div>
          <p class="text-base-content/70">
            {{ store.documents.length >= 3 ? '已达到上传上限（3 份）' : '拖拽或点击上传文档' }}
          </p>
          <p class="text-xs text-base-content/40 mt-1">支持 PDF / TXT / MD / DOCX</p>
        </div>
      </div>
    </div>

    <!-- 字数提示 -->
    <div v-if="store.documents.length < 3" class="flex items-center gap-2 mb-6 text-xs text-warning/80">
      <AlertTriangle class="w-3.5 h-3.5" />
      <span>文档内容超过 5000 字部分将被自动截断，请注意字数</span>
    </div>

    <!-- 错误 -->
    <div v-if="error" class="alert alert-warning mb-4 text-sm">
      <AlertTriangle class="w-4 h-4" /> {{ error }}
    </div>

    <!-- 文档列表 -->
    <div v-if="store.documents.length > 0" class="space-y-2">
      <div
        v-for="doc in store.documents"
        :key="doc.id"
        class="flex items-center justify-between p-4 rounded-xl bg-base-200/50"
      >
        <div class="flex items-center gap-3 min-w-0">
          <FileText class="w-5 h-5 shrink-0" :class="fileIcon(doc.file_type)" />
          <div class="min-w-0">
            <p class="text-sm font-medium truncate">{{ doc.title }}</p>
            <p class="text-xs text-base-content/40">
              {{ doc.status === 'processing' ? '处理中...' : doc.status === 'failed' ? '处理失败' : '' }}
            </p>
          </div>
        </div>
        <button class="btn btn-ghost btn-sm btn-square text-base-content/30 hover:text-error" @click="store.deleteDocument(doc.id)">
          <Trash2 class="w-4 h-4" />
        </button>
      </div>
    </div>

    <div v-else-if="!store.loading" class="text-center py-8 text-base-content/40 text-sm">
      还没有上传文档
    </div>
  </div>
</template>
