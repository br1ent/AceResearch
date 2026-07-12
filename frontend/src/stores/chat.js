import { ref } from 'vue'
import { defineStore } from 'pinia'
import http, { getAccessToken } from '@/js/http/api.js'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref([])
  const currentConvId = ref(null)
  const messages = ref([])
  const mode = ref('research')
  const ws = ref(null)
  const wsConnected = ref(false)
  const isResearching = ref(false)
  const researchProgress = ref(0)
  const researchMessage = ref('')
  const isChatting = ref(false)

  // ---- 模式切换 ----
  function switchMode(newMode) {
    if (isResearching.value || isChatting.value) return
    mode.value = newMode
    currentConvId.value = null
    messages.value = []
  }

  // ---- 对话列表 ----
  async function fetchConversations() {
    try {
      const res = await http.get('/api/chat/conversations')
      if (res.data?.success) conversations.value = res.data.data
    } catch (e) { console.error('获取对话列表失败', e) }
  }

  async function createConversation(title = '新对话', convMode = 'research') {
    try {
      const res = await http.post('/api/chat/conversations', { title, mode: convMode })
      if (res.data?.success) {
        conversations.value.unshift(res.data.data)
        return res.data.data
      }
    } catch (e) { console.error('创建对话失败', e) }
    return null
  }

  // ---- 消息 ----
  async function fetchMessages(convId) {
    if (convId == null || convId === undefined) return
    try {
      const res = await http.get(`/api/chat/conversations/${convId}/messages`)
      if (res.data?.success) {
        messages.value = res.data.data
        currentConvId.value = convId
      }
    } catch (e) { console.error('获取消息失败', e) }
  }

  function addMessage(msg) { messages.value.push(msg) }

  // ---- WebSocket ----
  function connectWebSocket(convId) {
    disconnectWebSocket()
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const wsUrl = `${protocol}//${host}/ws/${convId}?token=${encodeURIComponent(getAccessToken())}`

    ws.value = new WebSocket(wsUrl)
    ws.value.onopen = () => { wsConnected.value = true }
    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        switch (data.type) {
          case 'agent_status':
            isResearching.value = true; researchProgress.value = data.progress; researchMessage.value = data.message; break
          case 'report_completed':
            isResearching.value = false; researchProgress.value = 100; researchMessage.value = '报告已生成完成'; break
          case 'error':
            isResearching.value = false
            addMessage({ id: Date.now(), role: 'assistant', content: `❌ ${data.message || '研究过程发生错误'}`, msg_type: 'error', created_at: new Date().toISOString() })
            break
          case 'pong': break
        }
      } catch (e) { /* ignore */ }
    }
    ws.value.onerror = () => { wsConnected.value = false }
    ws.value.onclose = () => { wsConnected.value = false }
  }

  function disconnectWebSocket() {
    if (ws.value) { ws.value.close(); ws.value = null }
    wsConnected.value = false
  }

  // ---- 发送消息 ----
  async function sendMessage(text) {
    if (isResearching.value || isChatting.value) return null
    return mode.value === 'research' ? _startResearch(text) : _sendChat(text)
  }

  async function _startResearch(topic) {
    isResearching.value = true; researchProgress.value = 0; researchMessage.value = '正在启动研究...'
    try {
      const res = await http.post('/api/chat/send', { conversation_id: currentConvId.value, message: topic, mode: 'research' })
      if (res.data?.success) {
        const { conversation_id } = res.data.data
        currentConvId.value = conversation_id; messages.value = []
        connectWebSocket(conversation_id)
        addMessage({ id: Date.now(), role: 'user', content: topic, msg_type: 'text', created_at: new Date().toISOString() })
        addMessage({ id: Date.now() + 1, role: 'assistant', content: '🔍 正在分析研究主题...', msg_type: 'agent_status', created_at: new Date().toISOString() })
        await fetchConversations()
        return res.data.data
      }
    } catch (e) {
      console.error('发起研究失败', e)
      isResearching.value = false; researchMessage.value = '发起研究失败，请重试'
      addMessage({ id: Date.now(), role: 'assistant', content: '❌ 系统错误，请稍后重试', msg_type: 'error', created_at: new Date().toISOString() })
    }
    return null
  }

  function updateLastMessage(content) {
    // 更新最后一条消息的内容（流式追加 token）
    if (messages.value.length > 0) {
      const last = messages.value[messages.value.length - 1]
      last.content = content
    }
  }

  async function _sendChat(text) {
    isChatting.value = true
    // 用户消息
    const userMsgId = Date.now()
    addMessage({ id: userMsgId, role: 'user', content: text, msg_type: 'text', created_at: new Date().toISOString() })
    // 占位：空的助手消息，后续流式填充
    const assistantMsgId = Date.now() + 1
    addMessage({ id: assistantMsgId, role: 'assistant', content: '', msg_type: 'text', created_at: new Date().toISOString() })

    try {
      // 使用原生 fetch 处理 SSE 流
      const baseUrl = ''  // 同源，走 Vite proxy
      const res = await fetch(`${baseUrl}/api/chat/send/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({
          conversation_id: currentConvId.value,
          message: text,
          mode: 'chat',
        }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let fullText = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        // 处理 SSE 行：每行格式为 "data: {...}\n"
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''  // 最后一段不完整，保留

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6)
            try {
              const data = JSON.parse(jsonStr)
              if (data.type === 'token') {
                fullText += data.content
                updateLastMessage(fullText)
              } else if (data.type === 'meta') {
                currentConvId.value = data.conversation_id
              }
            } catch (e) { /* skip malformed */ }
          }
        }
      }

      // 流结束，刷新对话列表
      await fetchConversations()
    } catch (e) {
      console.error('聊天失败', e)
      updateLastMessage('❌ 请求失败，请稍后重试')
    } finally {
      isChatting.value = false
    }
  }

  // ---- 选择对话 ----
  async function selectConversation(conv) {
    if (!conv || !conv.id) return
    currentConvId.value = conv.id
    mode.value = conv.mode || 'research'
    await fetchMessages(conv.id)
    if (conv.mode === 'research') connectWebSocket(conv.id)
  }

  return {
    conversations, currentConvId, messages, mode, switchMode,
    isResearching, researchProgress, researchMessage, isChatting, wsConnected,
    fetchConversations, createConversation, fetchMessages, addMessage,
    sendMessage, selectConversation, connectWebSocket, disconnectWebSocket,
  }
})
