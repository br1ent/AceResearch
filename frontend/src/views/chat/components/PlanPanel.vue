<script setup>
import { ref, computed } from 'vue'
import { X, GripVertical, FileText, Search as SearchIcon, CheckCircle, Edit3 } from '@lucide/vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

const props = defineProps({
  plan: { type: Object, default: null },
})

const emit = defineEmits(['confirm', 'revise', 'close'])

const md = new MarkdownIt({
  html: true,
  highlight(str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try { return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>` } catch (e) {}
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  },
})

// 可拖拽宽度
const panelWidth = ref(420)
const dragging = ref(false)

function onMouseDown(e) {
  dragging.value = true
  e.preventDefault()
  const startX = e.clientX
  const startW = panelWidth.value
  const handler = (ev) => {
    const newW = startW + (startX - ev.clientX)
    panelWidth.value = Math.max(320, Math.min(640, newW))
  }
  const cleanup = () => { dragging.value = false; document.removeEventListener('mousemove', handler); document.removeEventListener('mouseup', cleanup) }
  document.addEventListener('mousemove', handler)
  document.addEventListener('mouseup', cleanup)
}

const reviseOpen = ref(false)
const reviseText = ref('')

function submitRevise() {
  const fb = reviseText.value.trim()
  if (!fb || !props.plan?.report_id) return
  emit('revise', props.plan.report_id, fb)
  reviseOpen.value = false
  reviseText.value = ''
}

// 格式化方案为 Markdown（增加间距）
const planMd = computed(() => {
  if (!props.plan) return ''
  const { report_title, outline, subtasks } = props.plan
  let text = `# ${report_title || '研究方案'}\n\n---\n\n`
  if (outline?.length) {
    text += '## 📋 大纲\n\n'
    outline.forEach(o => { text += `- ${o}\n` })
    text += '\n---\n\n'
  }
  if (subtasks?.length) {
    text += '## 🔍 研究子任务\n\n'
    subtasks.forEach((t, i) => {
      text += `### ${i + 1}. ${t.title}\n\n${t.description}\n\n---\n\n`
    })
  }
  return md.render(text)
})
</script>

<template>
  <aside
    v-if="plan"
    class="relative border-l border-base-200 bg-base-100 flex flex-col overflow-hidden shrink-0"
    :style="{ width: panelWidth + 'px' }"
  >
    <!-- 拖拽手柄 -->
    <div
      class="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-primary/30 z-10"
      @mousedown="onMouseDown"
    ></div>

    <!-- 标题 -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-base-200 shrink-0">
      <span class="font-semibold text-sm flex items-center gap-1.5"><FileText class="w-4 h-4" /> 研究方案</span>
      <button class="btn btn-ghost btn-xs btn-circle" @click="emit('close')">
        <X class="w-4 h-4" />
      </button>
    </div>

    <!-- 内容 -->
    <div class="flex-1 overflow-y-auto px-4 py-3 plan-content" v-html="planMd"></div>

    <!-- 底部操作区 -->
    <div class="border-t border-base-200 px-4 py-3 shrink-0 space-y-2">
      <template v-if="!reviseOpen">
        <button class="btn btn-neutral btn-sm w-full" @click="emit('confirm')">确认并开始研究</button>
        <button class="btn btn-ghost btn-sm w-full" @click="reviseOpen = true">修改计划</button>
      </template>
      <template v-else>
        <textarea
          v-model="reviseText"
          class="textarea textarea-bordered text-sm w-full"
          rows="3"
          placeholder="请输入修改意见..."
        ></textarea>
        <div class="flex gap-2">
          <button class="btn btn-neutral btn-sm flex-1" @click="submitRevise" :disabled="!reviseText.trim()">提交</button>
          <button class="btn btn-ghost btn-sm" @click="reviseOpen = false; reviseText = ''">取消</button>
        </div>
      </template>
    </div>
  </aside>
</template>

<style scoped>
.plan-content :deep(h1) { font-size: 1.25rem; font-weight: 700; margin: 1rem 0 0.75rem 0; }
.plan-content :deep(h2) { font-size: 1.05rem; font-weight: 600; margin: 1.25rem 0 0.5rem 0; padding-bottom: 0.25rem; border-bottom: 1px solid hsl(var(--bc) / 0.15); }
.plan-content :deep(h3) { font-size: 0.95rem; font-weight: 600; margin: 1rem 0 0.35rem 0; }
.plan-content :deep(p) { margin: 0.5rem 0; line-height: 1.7; }
.plan-content :deep(ul), .plan-content :deep(ol) { margin: 0.4rem 0 0.4rem 1.2rem; }
.plan-content :deep(li) { margin: 0.2rem 0; line-height: 1.6; }
.plan-content :deep(hr) { margin: 1.25rem 0; border-color: hsl(var(--bc) / 0.1); }
.plan-content :deep(code) { background: hsl(var(--b3)); padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.85rem; }
.plan-content :deep(pre) { margin: 0.75rem 0; padding: 0.75rem; border-radius: 8px; overflow-x: auto; }
</style>
