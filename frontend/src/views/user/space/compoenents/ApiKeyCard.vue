<script setup>
import { ref, onMounted } from 'vue'
import { KeyRound, ExternalLink, Loader2, Trash2, CheckCircle2 } from '@lucide/vue'
import http from '@/js/http/api.js'

const loading = ref(true)
const saving = ref(false)
const message = ref('')
const messageType = ref('success')

const models = ref({ deepseek_model: '', embedding_model: '', rerank_model: '' })
const status = ref({
  deepseek_api_key: { configured: false, masked: '' },
  dashscope_api_key: { configured: false, masked: '' },
  dashscope_workspace_id: { configured: false, masked: '' },
})
const form = ref({
  deepseek_api_key: '',
  dashscope_api_key: '',
  dashscope_workspace_id: '',
})

const sections = [
  {
    field: 'deepseek_api_key',
    label: 'DeepSeek API Key',
    desc: '用于大模型对话与研究报告生成',
    modelLabel: '大模型',
    modelKey: 'deepseek_model',
    link: 'https://platform.deepseek.com/api_keys',
    linkText: '前往 DeepSeek 开放平台申请',
  },
  {
    field: 'dashscope_api_key',
    label: '阿里云百炼 API Key',
    desc: '用于文档嵌入（向量化）与检索重排序',
    modelLabel: '嵌入模型',
    modelKey: 'embedding_model',
    link: 'https://bailian.console.aliyun.com/cn-beijing/model/settings/api-key',
    linkText: '前往阿里云百炼申请',
  },
  {
    field: 'dashscope_workspace_id',
    label: '百炼 Workspace ID',
    desc: '百炼工作空间 ID，重排序服务需要',
    modelLabel: '重排序模型',
    modelKey: 'rerank_model',
    link: 'https://bailian.console.aliyun.com/cn-beijing/model/settings/api-key',
    linkText: '前往百炼控制台获取',
  },
]

onMounted(fetchKeys)

function showMessage(text, ok = true) {
  message.value = text
  messageType.value = ok ? 'success' : 'error'
  setTimeout(() => { message.value = '' }, 3000)
}

async function fetchKeys() {
  loading.value = true
  try {
    const res = await http.get('/api/user/apikeys')
    if (res.data?.success) {
      const d = res.data.data
      status.value.deepseek_api_key = d.deepseek_api_key
      status.value.dashscope_api_key = d.dashscope_api_key
      status.value.dashscope_workspace_id = d.dashscope_workspace_id
      models.value = d.models
    }
  } catch (e) { console.error('获取 API Key 配置失败', e) }
  finally { loading.value = false }
}

async function save() {
  const payload = {}
  for (const f of Object.keys(form.value)) {
    if (form.value[f].trim()) payload[f] = form.value[f].trim()
  }
  if (!Object.keys(payload).length) {
    showMessage('请先填写要保存的内容', false)
    return
  }
  saving.value = true
  try {
    const res = await http.post('/api/user/apikeys', payload)
    if (res.data?.success) {
      showMessage('API Key 已保存')
      form.value = { deepseek_api_key: '', dashscope_api_key: '', dashscope_workspace_id: '' }
      await fetchKeys()
    } else {
      showMessage(res.data?.message || '保存失败', false)
    }
  } catch (e) {
    console.error('保存 API Key 失败', e)
    showMessage('保存失败，请稍后重试', false)
  } finally { saving.value = false }
}

async function clearField(field) {
  try {
    const res = await http.post('/api/user/apikeys/delete', { fields: [field] })
    if (res.data?.success) {
      showMessage('已清除，对应功能将不可用直至重新配置')
      await fetchKeys()
    } else {
      showMessage(res.data?.message || '清除失败', false)
    }
  } catch (e) {
    console.error('清除 API Key 失败', e)
    showMessage('清除失败，请稍后重试', false)
  }
}
</script>

<template>
  <div>
    <h2 class="text-lg font-semibold mb-1 flex items-center gap-2">
      <KeyRound class="w-5 h-5" /> 模型 API 配置
    </h2>
    <p class="text-base text-warning mb-4">
      平台使用你自己的 API Key 调用模型，未配置的功能将无法使用。Key 仅加密展示，不会明文回显。
    </p>

    <div v-if="loading" class="flex justify-center py-8">
      <Loader2 class="w-5 h-5 animate-spin text-base-content/40" />
    </div>

    <div v-else class="flex flex-col gap-5">
      <div v-for="s in sections" :key="s.field" class="border border-base-200 rounded-lg p-4">
        <div class="flex items-center justify-between mb-1">
          <span class="font-medium text-sm">{{ s.label }}</span>
          <div class="flex items-center gap-2">
            <span v-if="status[s.field].configured" class="badge badge-success badge-sm gap-1">
              <CheckCircle2 class="w-3 h-3" /> 已配置
            </span>
            <button v-if="status[s.field].configured" class="btn btn-ghost btn-xs btn-square text-error"
              title="清除" @click="clearField(s.field)">
              <Trash2 class="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
        <p class="text-xs text-base-content/50 mb-2">{{ s.desc }}</p>

        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs text-base-content/50 shrink-0">{{ s.modelLabel }}：</span>
          <input type="text" class="input input-bordered input-xs flex-1 bg-base-200/50 text-base-content/60"
            :value="models[s.modelKey]" readonly disabled title="模型由系统预置，暂不支持修改" />
        </div>

        <input v-model="form[s.field]" type="password" autocomplete="new-password"
          class="input input-bordered input-sm w-full"
          :placeholder="status[s.field].configured ? `当前：${status[s.field].masked}（输入新值以替换）` : '请输入'" />

        <a :href="s.link" target="_blank" rel="noopener"
          class="link link-info text-xs inline-flex items-center gap-1 mt-2">
          <ExternalLink class="w-3 h-3" /> {{ s.linkText }}
        </a>
      </div>

      <div class="flex items-center gap-3">
        <button class="btn btn-neutral btn-sm px-6" :disabled="saving" @click="save">
          <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
          保存配置
        </button>
        <span v-if="message" class="text-sm" :class="messageType === 'success' ? 'text-success' : 'text-error'">{{ message }}</span>
      </div>
    </div>
  </div>
</template>
