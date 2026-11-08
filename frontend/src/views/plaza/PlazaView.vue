<script setup>
import { ref, onMounted, watch } from 'vue'
import { Globe, Loader2, BookOpen, X, Clock, ChevronLeft, ChevronRight, Search, Heart, User } from '@lucide/vue'
import http from '@/js/http/api.js'
import { marked } from 'marked'

const items = ref([])
const total = ref(0)
const loading = ref(true)
const showModal = ref(false)
const currentReport = ref(null)
const detailLoading = ref(false)
const searchText = ref('')
const sort = ref('likes')
const likingId = ref(null)

// 分页
const page = ref(1)
const perPage = 10
const maxPageButtons = 5
const totalPages = ref(1)
const pageRange = ref([])

function computePageRange() {
  const t = totalPages.value
  const half = Math.floor(maxPageButtons / 2)
  let s = Math.max(1, page.value - half)
  let e = Math.min(t, s + maxPageButtons - 1)
  if (e - s + 1 < maxPageButtons) s = Math.max(1, e - maxPageButtons + 1)
  const pages = []
  for (let i = s; i <= e; i++) pages.push(i)
  pageRange.value = pages
}

onMounted(fetchReports)

let searchTimer = null
watch(searchText, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => { page.value = 1; fetchReports() }, 300)
})

function changeSort(value) {
  if (sort.value === value) return
  sort.value = value
  page.value = 1
  fetchReports()
}

function goPage(p) {
  page.value = p
  fetchReports()
}

async function fetchReports() {
  loading.value = true
  try {
    const res = await http.get('/api/plaza/reports', {
      params: { keyword: searchText.value.trim(), sort: sort.value, page: page.value, page_size: perPage },
    })
    if (res.data?.success) {
      items.value = res.data.data.items
      total.value = res.data.data.total
      totalPages.value = Math.max(1, Math.ceil(total.value / perPage))
      if (page.value > totalPages.value) {
        page.value = totalPages.value
        return fetchReports()
      }
      computePageRange()
    }
  } catch (e) { console.error('获取广场列表失败', e) }
  finally { loading.value = false }
}

async function viewReport(item) {
  detailLoading.value = true
  try {
    const res = await http.get(`/api/plaza/reports/${item.id}`)
    if (res.data?.success) {
      currentReport.value = res.data.data
      showModal.value = true
    }
  } catch (e) { console.error('获取报告详情失败', e) }
  finally { detailLoading.value = false }
}

function closeModal() {
  showModal.value = false
  currentReport.value = null
}

async function toggleLike(target, event) {
  event?.stopPropagation()
  if (likingId.value) return
  likingId.value = target.id
  try {
    const res = await http.post(`/api/plaza/reports/${target.id}/like`)
    if (res.data?.success) {
      const { liked, like_count } = res.data.data
      const inList = items.value.find(i => i.id === target.id)
      if (inList) { inList.liked = liked; inList.like_count = like_count }
      if (currentReport.value?.id === target.id) {
        currentReport.value.liked = liked
        currentReport.value.like_count = like_count
      }
    }
  } catch (e) { console.error('点赞失败', e) }
  finally { likingId.value = null }
}

function formatTime(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`
}
</script>

<template>
  <main class="flex-1 px-5 py-8 max-w-4xl mx-auto w-full">
    <h1 class="text-2xl font-semibold mb-4 flex items-center gap-2">
      <Globe class="w-6 h-6" /> 报告广场
      <span v-if="total" class="text-sm font-normal text-base-content/40">共 {{ total }} 篇</span>
    </h1>

    <div class="flex items-center gap-3 mb-4 flex-wrap">
      <div class="relative flex-1 min-w-[220px]">
        <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-base-content/40" />
        <input v-model="searchText" type="text" class="input input-bordered w-full pl-10" placeholder="搜索报告标题或作者名称..." />
      </div>
      <div class="join">
        <button class="btn btn-sm join-item" :class="sort === 'likes' ? 'btn-neutral' : 'btn-ghost'" @click="changeSort('likes')">按点赞量</button>
        <button class="btn btn-sm join-item" :class="sort === 'date' ? 'btn-neutral' : 'btn-ghost'" @click="changeSort('date')">按最新发布</button>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-16"><Loader2 class="w-6 h-6 animate-spin text-base-content/40" /></div>

    <div v-else-if="items.length === 0" class="text-center py-16 text-base-content/40">
      <Globe class="w-12 h-12 mx-auto mb-3 opacity-30" />
      <p v-if="searchText.trim()">没有匹配 "{{ searchText }}" 的报告</p>
      <p v-else>广场暂无报告，快去"我的报告"发布第一篇吧</p>
    </div>

    <template v-else>
      <div class="flex flex-col gap-3">
        <div v-for="item in items" :key="item.id"
          class="card bg-base-100 shadow-sm border border-base-200 hover:shadow-md transition-shadow cursor-pointer"
          @click="viewReport(item)">
          <div class="card-body py-5 px-6">
            <div class="flex items-center justify-between gap-4">
              <div class="flex items-center gap-4 min-w-0 flex-1">
                <div class="avatar shrink-0">
                  <div class="w-12 h-12 rounded-full ring ring-base-200 ring-offset-1 overflow-hidden bg-base-200 flex items-center justify-center">
                    <img v-if="item.author_photo" :src="item.author_photo" :alt="item.author" class="object-cover" />
                    <span v-else class="text-base font-semibold text-base-content/50">{{ item.author?.charAt(0)?.toUpperCase() }}</span>
                  </div>
                </div>
                <div class="min-w-0 flex-1">
                  <p class="font-semibold text-lg truncate">{{ item.title }}</p>
                  <p class="text-xs text-base-content/40 flex items-center gap-3 mt-1">
                    <span class="flex items-center gap-1"><User class="w-3 h-3" /> {{ item.author }}</span>
                    <span class="flex items-center gap-1"><Clock class="w-3 h-3" /> {{ formatTime(item.published_at) }}</span>
                  </p>
                </div>
              </div>
              <button class="btn btn-ghost btn-sm gap-1 shrink-0" :class="item.liked ? 'text-error' : 'text-base-content/50'"
                @click="toggleLike(item, $event)" :disabled="likingId === item.id" :title="item.liked ? '取消点赞' : '点赞'">
                <Loader2 v-if="likingId === item.id" class="w-4 h-4 animate-spin" />
                <Heart v-else class="w-4 h-4" :fill="item.liked ? 'currentColor' : 'none'" />
                <span class="text-sm">{{ item.like_count }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-center gap-1 mt-6" v-if="totalPages > 1">
        <button class="btn btn-ghost btn-sm" :disabled="page <= 1" @click="goPage(Math.max(1, page - 1))"><ChevronLeft class="w-4 h-4" /></button>
        <button v-for="p in pageRange" :key="p" class="btn btn-sm min-w-[36px]" :class="p === page ? 'btn-neutral' : 'btn-ghost'" @click="goPage(p)">{{ p }}</button>
        <button class="btn btn-ghost btn-sm" :disabled="page >= totalPages" @click="goPage(Math.min(totalPages, page + 1))"><ChevronRight class="w-4 h-4" /></button>
        <span class="text-xs text-base-content/40 ml-3">第 {{ page }} / {{ totalPages }} 页</span>
      </div>
    </template>

    <!-- 报告详情模态框 -->
    <div v-if="showModal && currentReport" class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" @click.self="closeModal">
      <div class="bg-base-100 rounded-lg shadow-2xl w-full max-w-6xl flex flex-col" style="height: 90vh; max-height: 90vh;">
        <div class="flex items-center justify-between px-6 py-3 border-b border-base-200 shrink-0 gap-3">
          <div class="flex items-center gap-3 min-w-0">
            <div class="avatar shrink-0">
              <div class="w-10 h-10 rounded-full ring ring-base-200 ring-offset-1 overflow-hidden bg-base-200 flex items-center justify-center">
                <img v-if="currentReport.author_photo" :src="currentReport.author_photo" :alt="currentReport.author" class="object-cover" />
                <span v-else class="text-sm font-semibold text-base-content/50">{{ currentReport.author?.charAt(0)?.toUpperCase() }}</span>
              </div>
            </div>
            <div class="min-w-0">
              <h2 class="text-lg font-semibold truncate">{{ currentReport.title }}</h2>
              <p class="text-xs text-base-content/40 mt-0.5">作者：{{ currentReport.author }} · 发布于 {{ formatTime(currentReport.published_at) }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2 shrink-0">
            <button class="btn btn-ghost btn-sm gap-1" :class="currentReport.liked ? 'text-error' : 'text-base-content/50'"
              @click="toggleLike(currentReport)" :disabled="likingId === currentReport.id">
              <Heart class="w-4 h-4" :fill="currentReport.liked ? 'currentColor' : 'none'" />
              <span class="text-sm">{{ currentReport.like_count }}</span>
            </button>
            <button class="btn btn-ghost btn-sm btn-circle" @click="closeModal"><X class="w-5 h-5" /></button>
          </div>
        </div>
        <div class="overflow-y-auto px-6 py-5" style="flex: 1; min-height: 0;">
          <div class="report-content leading-relaxed break-words" v-html="marked(currentReport.content)"></div>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
.report-content :deep(p) { margin: 0.6rem 0; line-height: 1.8; }
.report-content :deep(h1) { font-size: 1.4rem; font-weight: 700; margin: 1.2rem 0 0.8rem; }
.report-content :deep(h2) { font-size: 1.15rem; font-weight: 600; margin: 1.2rem 0 0.6rem; border-bottom: 1px solid hsl(var(--bc) / 0.15); padding-bottom: 0.3rem; }
.report-content :deep(h3) { font-size: 1rem; font-weight: 600; margin: 1rem 0 0.4rem; }
.report-content :deep(h4) { font-size: 0.95rem; font-weight: 600; margin: 0.8rem 0 0.3rem; }
.report-content :deep(table) { width: 100%; border-collapse: collapse; margin: 0.8rem 0; font-size: 0.9rem; }
.report-content :deep(th) { background: hsl(var(--b2)); padding: 0.5rem 0.75rem; border: 1px solid hsl(var(--bc) / 0.2); font-weight: 600; text-align: left; }
.report-content :deep(td) { padding: 0.4rem 0.75rem; border: 1px solid hsl(var(--bc) / 0.15); }
.report-content :deep(tr):nth-child(even) td { background: hsl(var(--b2) / 0.5); }
.report-content :deep(hr) { margin: 1.2rem 0; border-color: hsl(var(--bc) / 0.1); }
.report-content :deep(ul), .report-content :deep(ol) { margin: 0.4rem 0 0.4rem 1.5rem; }
.report-content :deep(li) { margin: 0.2rem 0; line-height: 1.7; }
.report-content :deep(blockquote) { border-left: 3px solid hsl(var(--bc) / 0.3); padding-left: 0.8rem; margin: 0.6rem 0; color: hsl(var(--bc) / 0.7); }
</style>
