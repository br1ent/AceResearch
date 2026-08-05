<script setup>
import { ref, reactive, computed } from 'vue'
import {
  Mail,
  User,
  Lock,
  Pencil,
  Check,
  X,
} from '@lucide/vue'
import http from '@/js/http/api.js'
import { useUserStore } from '@/stores/user.js'

const userStore = useUserStore()
const emit = defineEmits(['updated'])

const editing = ref(false)
const saving = ref(false)
const form = reactive({ username: '', email: '' })
const errorMessage = ref('')

function startEdit() {
  form.username = userStore.username
  form.email = userStore.email
  errorMessage.value = ''
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  errorMessage.value = ''
}

async function saveProfile() {
  errorMessage.value = ''
  if (!form.username) { errorMessage.value = '用户名不能为空'; return }
  if (!form.email) { errorMessage.value = '邮箱不能为空'; return }

  saving.value = true
  try {
    const fd = new FormData()
    fd.append('username', form.username)
    fd.append('email', form.email)
    const res = await http.put('/api/user/profile', fd)
    if (res.data.success) {
      userStore.setUserInfo(res.data.data)
      editing.value = false
      emit('updated')
    } else {
      errorMessage.value = res.data.message
    }
  } catch (e) {
    errorMessage.value = e.response?.data?.detail || '更新失败'
  }
  saving.value = false
}

const fields = computed(() => [
  { icon: User, label: '用户名', value: userStore.username, key: 'username', editable: true },
  { icon: Mail, label: '邮箱', value: userStore.email, key: 'email', editable: true },
])
</script>

<template>
  <div class="flex flex-col gap-6">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold">个人资料</h2>
      <button
        v-if="!editing"
        class="btn btn-sm btn-outline"
        @click="startEdit"
      >
        <Pencil class="w-4 h-4" /> 更新资料
      </button>
    </div>

    <div class="space-y-4">
      <div
        v-for="f in fields"
        :key="f.key"
        class="flex items-center gap-4 py-3 border-b border-base-200 last:border-0"
      >
        <div class="w-9 h-9 rounded-lg bg-base-200 flex items-center justify-center shrink-0">
          <component :is="f.icon" class="w-4 h-4 text-base-content/60" />
        </div>

        <div class="flex-1 min-w-0">
          <p class="text-xs text-base-content/50">{{ f.label }}</p>

          <!-- 编辑模式 + 可编辑字段 -->
          <div v-if="editing && f.editable" class="mt-1">
            <input
              v-model="form[f.key]"
              class="input input-bordered input-sm w-full"
            />
          </div>

          <!-- 不可编辑 或 查看模式 -->
          <p v-else class="font-medium truncate">
            {{ f.value }}
            <Lock v-if="!f.editable" class="w-3 h-3 inline ml-1 text-base-content/30" />
          </p>
        </div>
      </div>
    </div>

    <div v-if="errorMessage" class="text-error text-sm">{{ errorMessage }}</div>

    <div v-if="editing" class="flex gap-3 justify-between">
      <button class="btn btn-sm btn-neutral" :disabled="saving" @click="saveProfile">
        <Check class="w-4 h-4" /> {{ saving ? '保存中...' : '保存' }}
      </button>
      <button class="btn btn-sm btn-outline justify-end" @click="cancelEdit">
        <X class="w-4 h-4" /> 取消
      </button>
    </div>
  </div>
</template>
