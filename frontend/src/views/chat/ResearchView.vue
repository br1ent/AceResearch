<script setup>
import { ref, watch } from 'vue'
import { PanelLeft, PanelLeftClose, MessageSquarePlus, Search, FileText } from '@lucide/vue'
import SidebarTool from './components/SidebarTool.vue'
import RecentChats from './components/RecentChats.vue'
import ChatMain from './components/ChatMain.vue'
import SearchView from './components/SearchView.vue'
import PlanPanel from './components/PlanPanel.vue'
import { useChatStore } from '@/stores/chat.js'

const sidebarOpen = ref(true)
const showSearch = ref(false)
const chatStore = useChatStore()

function onNewChat() {
  showSearch.value = false
  chatStore.switchMode(chatStore.mode)
}

function onShowSearch() {
  showSearch.value = true
}

function onCloseSearch() {
  showSearch.value = false
}

function onSelectChat(chat) {
  showSearch.value = false
}

function onConfirmPlan() {
  chatStore.confirmResearch()
}

function onRevisePlan(reportId, feedback) {
  chatStore.revisePlan(reportId, feedback)
}

function onClosePlan() {
  chatStore.closePlanPanel()
}

// 方案就绪时自动打开面板
watch(() => chatStore.currentPlan, (val) => {
  if (val) chatStore.openPlanPanel()
})
</script>

<template>
  <div class="flex h-[calc(100vh-4rem)]">
    <!-- 展开的侧边栏 -->
    <transition name="sidebar">
      <aside
        v-if="sidebarOpen"
        class="w-72 shrink-0 bg-base-200/50 border-r border-base-200 flex flex-col overflow-hidden"
      >
        <!-- 顶部标题栏 -->
        <div class="flex items-center justify-between px-3 py-3 border-b border-base-200">
          <div class="flex items-center gap-3">
            <PanelLeft class="w-5 h-5 shrink-0 text-base-content/60" />
            <span class="font-semibold">多智能体研究</span>
          </div>
          <button class="btn btn-ghost btn-xs btn-circle" @click="sidebarOpen = false" title="收起侧边栏">
            <PanelLeftClose class="w-5 h-5" />
          </button>
        </div>
        <div class="p-3 border-b border-base-200">
          <SidebarTool @newChat="onNewChat" @showSearch="onShowSearch" />
        </div>
        <div class="flex-1 overflow-y-auto p-3">
          <RecentChats @selectChat="onSelectChat" />
        </div>
      </aside>
    </transition>

    <!-- 收起时的迷你侧边栏 -->
    <transition name="sidebar-mini">
      <aside
        v-if="!sidebarOpen"
        class="w-14 shrink-0 bg-base-200/50 border-r border-base-200 flex flex-col items-center py-3 gap-3 overflow-hidden"
      >
        <button class="btn btn-ghost btn-sm btn-circle" @click="sidebarOpen = true" title="展开侧边栏">
          <PanelLeft class="w-5 h-5" />
        </button>
        <button class="btn btn-ghost btn-sm btn-circle" @click="onNewChat" title="新对话">
          <MessageSquarePlus class="w-5 h-5" />
        </button>
        <button class="btn btn-ghost btn-sm btn-circle" @click="onShowSearch" title="搜索">
          <Search class="w-5 h-5" />
        </button>
      </aside>
    </transition>

    <!-- 右侧主区域 -->
    <main class="flex-1 flex flex-col min-w-0">

      <SearchView
        v-if="showSearch"
        @close="onCloseSearch"
        @selectChat="onSelectChat"
      />

      <ChatMain v-else />
    </main>

    <PlanPanel
      v-if="chatStore.currentPlan && chatStore.planPanelOpen"
      :plan="chatStore.currentPlan"
      @confirm="onConfirmPlan"
      @revise="onRevisePlan"
      @close="onClosePlan"
    />
    <!-- 方案面板收起时的重新打开按钮 -->
    <button
      v-if="chatStore.currentPlan && !chatStore.planPanelOpen"
      class="btn btn-neutral btn-sm fixed right-4 bottom-24 z-40 shadow-lg gap-1.5"
      @click="chatStore.openPlanPanel()"
    >
      <FileText class="w-4 h-4" /> 查看方案
    </button>
  </div>
</template>

<style scoped>
.sidebar-enter-active,
.sidebar-leave-active {
  transition: width 0.25s ease, opacity 0.2s ease;
}
.sidebar-enter-from,
.sidebar-leave-to {
  width: 0 !important;
  opacity: 0;
  padding: 0;
  border: none;
}

.sidebar-mini-enter-active,
.sidebar-mini-leave-active {
  transition: width 0.25s ease, opacity 0.2s ease;
}
.sidebar-mini-enter-from,
.sidebar-mini-leave-to {
  width: 0 !important;
  opacity: 0;
  padding: 0;
  border: none;
}
</style>
