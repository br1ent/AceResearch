<script setup>
import { nextTick, ref } from 'vue'
import { Upload, User } from '@lucide/vue'
import Croppie from 'croppie'
import 'croppie/croppie.css'
import http from '@/js/http/api.js'
import { useUserStore } from '@/stores/user.js'

const userStore = useUserStore()
const emit = defineEmits(['updated'])

const uploading = ref(false)
const fileInput = ref(null)
const cropModal = ref(null)
const croppieContainer = ref(null)
let croppie = null

function onFileChange(e) {
  const file = e.target.files[0]
  e.target.value = ''
  if (!file) return

  const reader = new FileReader()
  reader.onload = () => openCropModal(reader.result)
  reader.readAsDataURL(file)
}

async function openCropModal(dataUrl) {
  cropModal.value.showModal()
  await nextTick()

  if (!croppie) {
    croppie = new Croppie(croppieContainer.value, {
      viewport: { width: 200, height: 200, type: 'square' },
      boundary: { width: 300, height: 300 },
      enableOrientation: true,
      enforceBoundary: true,
    })
  }

  croppie.bind({ url: dataUrl })
}

async function doCrop() {
  if (!croppie) return

  uploading.value = true
  try {
    const base64 = await croppie.result({ type: 'base64', size: 'viewport' })
    const blob = await fetch(base64).then(r => r.blob())

    const form = new FormData()
    form.append('file', blob, 'avatar.png')

    const res = await http.post('/api/user/avatar', form)
    if (res.data.success) {
      userStore.photo = res.data.data.photo
      emit('updated')
    }
  } catch (e) {
    console.error(e)
  } finally {
    uploading.value = false
    cropModal.value.close()
  }
}

function cancelCrop() {
  cropModal.value.close()
}
</script>

<template>
  <div class="flex flex-col items-center gap-4">
    <div
      class="avatar cursor-pointer group relative"
      @click="fileInput?.click()"
    >
      <div class="w-32 rounded-full ring ring-base-300">
        <img v-if="userStore.photo" :src="userStore.photo" alt="头像" />
        <div v-else class="w-32 h-32 rounded-full bg-neutral text-neutral-content flex items-center justify-center">
          <User class="w-12 h-12" />
        </div>
      </div>
      <div class="absolute inset-0 flex items-center justify-center bg-black/40 rounded-full opacity-0 group-hover:opacity-100 transition-opacity">
        <Upload class="w-6 h-6 text-white" />
      </div>
    </div>

    <p class="text-sm text-base-content/50">点击头像更换</p>

    <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileChange" />

    <dialog ref="cropModal" class="modal">
      <div class="modal-box transition-none max-w-[calc(100vw-1rem)]">
        <button class="btn btn-circle btn-sm btn-ghost float-end" @click="cancelCrop">✕</button>

        <div ref="croppieContainer" class="flex flex-col justify-center my-4"></div>

        <div class="modal-action">
          <button class="btn btn-neutral" :disabled="uploading" @click="doCrop">
            {{ uploading ? '保存中...' : '确认裁剪' }}
          </button>
          <button class="btn btn-outline" @click="cancelCrop">取消</button>
        </div>
      </div>
    </dialog>
  </div>
</template>
