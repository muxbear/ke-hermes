import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { sendStreamRequest } from '@/services/request'
import { useUiStore } from '@/stores/ui'
import type { ChatMessage, ExecutionBlock, AttachmentDisplayInfo } from '@/types/chat'
import type { StreamCallbacks } from '@/services/request'
import type { Attachment } from '@/types/chat'
import { uploadAttachment, deleteAttachment } from '@/services/attachmentApi'

export type { ChatMessage }

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const loading = ref(false)
  const threadId = ref<string | null>(null)
  const traceEnabled = ref(false)
  const attachments = ref<Attachment[]>([])
  let nextId = 1
  let abortController: AbortController | null = null

  function generateId(): string {
    return crypto.randomUUID()
  }

  function addMessage(role: 'user' | 'assistant', content = '', streaming = false): ChatMessage {
    const msg: ChatMessage = { id: nextId++, role, content, streaming }
    messages.value.push(msg)
    return msg
  }

  /** Look up the reactive proxy of a message by ID */
  function byId(id: number): { idx: number; msg: ChatMessage } | null {
    const idx = messages.value.findIndex((m) => m.id === id)
    if (idx === -1) return null
    return { idx, msg: messages.value[idx] }
  }

  /** Build callbacks for trace-enabled mode: construct execution block tree */
  function buildTraceCallbacks(assistantId: number): StreamCallbacks {
    const blocks: ExecutionBlock[] = []

    // Initialize blocks on the reactive message
    const init = byId(assistantId)
    if (init) {
      messages.value[init.idx] = { ...init.msg, blocks }
    }

    // Track agent_name → blocks[] for token routing
    const agentBlocks = new Map<string, ExecutionBlock[]>()
    agentBlocks.set('main', blocks)

    // Track call_id → ExecutionBlock for tool_end / agent_end lookups
    const activeBlocks = new Map<string, ExecutionBlock>()

    return {
      onToken(agentName: string, content: string) {
        const target = agentBlocks.get(agentName) || blocks
        const last = target[target.length - 1]
        if (last && last.type === 'text') {
          last.content += content
        } else {
          target.push({ type: 'text', content })
        }
        // Trigger Vue reactivity by touching the reactive message
        const entry = byId(assistantId)
        if (entry) {
          messages.value[entry.idx] = { ...entry.msg, blocks: [...blocks] }
        }
      },

      onReasoning(_agentName: string, content: string) {
        const entry = byId(assistantId)
        if (entry) {
          messages.value[entry.idx] = {
            ...entry.msg,
            reasoning: (entry.msg.reasoning || '') + content,
          }
        }
      },

      onAgentStart(data) {
        if (data.agent_type === 'sub') {
          const block: ExecutionBlock = {
            type: 'sub_agent',
            subAgent: {
              callId: data.call_id,
              name: data.agent_name,
              status: 'running',
              blocks: [],
            },
          }
          agentBlocks.set(data.agent_name, block.subAgent.blocks)
          const parent = agentBlocks.get('main') || blocks
          parent.push(block)
          activeBlocks.set(data.call_id, block)
          const entry = byId(assistantId)
          if (entry) {
            messages.value[entry.idx] = { ...entry.msg, blocks: [...blocks] }
          }
        }
      },

      onAgentEnd(data) {
        const block = activeBlocks.get(data.call_id)
        if (block && block.type === 'sub_agent') {
          block.subAgent.status =
            data.status === 'completed' ? 'completed' : 'failed'
        }
        agentBlocks.delete(data.agent_name)
        const entry = byId(assistantId)
        if (entry) {
          messages.value[entry.idx] = { ...entry.msg, blocks: [...blocks] }
        }
      },

      onToolStart(data) {
        const block: ExecutionBlock = {
          type: 'tool_call',
          toolCall: {
            callId: data.call_id,
            name: data.tool_name,
            input: data.input,
            output: '',
            status: 'running',
          },
        }
        blocks.push(block)
        activeBlocks.set(data.call_id, block)
        const entry = byId(assistantId)
        if (entry) {
          messages.value[entry.idx] = { ...entry.msg, blocks: [...blocks] }
        }
      },

      onToolOutput(callId: string, content: string) {
        const block = activeBlocks.get(callId)
        if (block && block.type === 'tool_call') {
          block.toolCall.output += content
          const entry = byId(assistantId)
          if (entry) {
            messages.value[entry.idx] = { ...entry.msg, blocks: [...blocks] }
          }
        }
      },

      onToolEnd(data) {
        const block = activeBlocks.get(data.call_id)
        if (block && block.type === 'tool_call') {
          block.toolCall.output = data.output || block.toolCall.output
          block.toolCall.status = 'completed'
          const entry = byId(assistantId)
          if (entry) {
            messages.value[entry.idx] = { ...entry.msg, blocks: [...blocks] }
          }
        }
      },

      onThreadId(id: string) {
        threadId.value = id
      },

      onDone() {
        const entry = byId(assistantId)
        if (entry) {
          messages.value[entry.idx] = { ...entry.msg, streaming: false }
        }
        loading.value = false
        const uiStore = useUiStore()
        uiStore.activeThreadId = threadId.value
        uiStore.fetchHistories()
      },

      onError(errorMsg: string) {
        const entry = byId(assistantId)
        if (entry) {
          const sep = entry.msg.content ? '\n\n' : ''
          messages.value[entry.idx] = {
            ...entry.msg,
            content: entry.msg.content + `${sep}${errorMsg}`,
            streaming: false,
          }
        }
        loading.value = false
      },
    }
  }

  /** Build callbacks for normal mode: merge all agent tokens into content */
  function buildNormalCallbacks(assistantId: number): StreamCallbacks {
    return {
      onToken(agentName: string, content: string) {
        // 普通模式只显示主智能体 token，子智能体作为内部处理不展示
        if (agentName !== 'main') return
        const entry = byId(assistantId)
        if (entry) {
          messages.value[entry.idx] = {
            ...entry.msg,
            content: entry.msg.content + content,
          }
        }
      },

      onReasoning(_agentName: string, content: string) {
        const entry = byId(assistantId)
        if (entry) {
          messages.value[entry.idx] = {
            ...entry.msg,
            reasoning: (entry.msg.reasoning || '') + content,
          }
        }
      },

      onAgentStart() {},
      onAgentEnd() {},
      onToolStart() {},
      onToolOutput() {},
      onToolEnd() {},

      onThreadId(id: string) {
        threadId.value = id
      },

      onDone() {
        const entry = byId(assistantId)
        if (entry) {
          messages.value[entry.idx] = { ...entry.msg, streaming: false }
        }
        loading.value = false
        const uiStore = useUiStore()
        uiStore.activeThreadId = threadId.value
        uiStore.fetchHistories()
      },

      onError(errorMsg: string) {
        const entry = byId(assistantId)
        if (entry) {
          const sep = entry.msg.content ? '\n\n' : ''
          messages.value[entry.idx] = {
            ...entry.msg,
            content: entry.msg.content + `${sep}${errorMsg}`,
            streaming: false,
          }
        }
        loading.value = false
      },
    }
  }

  function buildAttachmentDisplayInfo(): AttachmentDisplayInfo[] {
    return attachments.value
      .filter((a) => a.status === 'success')
      .map((a) => ({
        filename: a.filename,
        mimeType: a.mimeType,
        size: a.size,
        thumbnailUrl: URL.createObjectURL(a.file),
      }))
  }

  function clearAttachments() {
    attachments.value = []
  }

  async function sendMessage(text: string) {
    if (loading.value || !text.trim()) return

    loading.value = true

    // Capture attachment display info before clearing
    const displayInfo = buildAttachmentDisplayInfo()
    const attIds = [...activeAttachmentIds.value]

    // Clear input-area attachments
    clearAttachments()

    // Add user message with attachment display info
    const userMsg = addMessage('user', text.trim())
    if (displayInfo.length > 0) {
      const idx = messages.value.findIndex((m) => m.id === userMsg.id)
      if (idx !== -1) {
        messages.value[idx] = { ...messages.value[idx], attachments: displayInfo }
      }
    }

    const assistantMsg = addMessage('assistant', '', true)

    const callbacks = traceEnabled.value
      ? buildTraceCallbacks(assistantMsg.id)
      : buildNormalCallbacks(assistantMsg.id)

    abortController = new AbortController()

    try {
      await sendStreamRequest(text.trim(), {
        threadId: threadId.value,
        callbacks,
        attachmentIds: attIds.length > 0 ? attIds : undefined,
        signal: abortController.signal,
      })
    } catch {
      const entry = byId(assistantMsg.id)
      if (entry) {
        const sep = entry.msg.content ? '\n\n' : ''
        messages.value[entry.idx] = {
          ...entry.msg,
          content: entry.msg.content + `${sep}抱歉，网络连接失败，请检查网络后重试。`,
          streaming: false,
        }
      }
      loading.value = false
    } finally {
      abortController = null
    }
  }

  function stopGeneration() {
    if (abortController) {
      abortController.abort()
      abortController = null
      loading.value = false
    }
  }

  function clearMessages() {
    messages.value = []
    loading.value = false
    threadId.value = null
  }

  async function uploadFile(file: File): Promise<void> {
    const id = generateId()
    const att: Attachment = {
      id,
      file,
      filename: file.name,
      size: file.size,
      mimeType: file.type || 'application/octet-stream',
      status: 'uploading',
      progress: 0,
    }
    attachments.value.push(att)

    try {
      const result = await uploadAttachment(file, (percent) => {
        const idx = attachments.value.findIndex((a) => a.id === id)
        if (idx !== -1) {
          attachments.value[idx] = { ...attachments.value[idx], progress: percent }
        }
      })
      const idx = attachments.value.findIndex((a) => a.id === id)
      if (idx !== -1) {
        attachments.value[idx] = {
          ...attachments.value[idx],
          serverId: result.id,
          status: 'success',
          progress: 100,
        }
      }
    } catch {
      const idx = attachments.value.findIndex((a) => a.id === id)
      if (idx !== -1) {
        attachments.value[idx] = { ...attachments.value[idx], status: 'failed' }
      }
    }
  }

  function removeAttachment(id: string): void {
    const att = attachments.value.find((a) => a.id === id)
    if (att?.serverId) {
      deleteAttachment(att.serverId).catch(() => {})
    }
    attachments.value = attachments.value.filter((a) => a.id !== id)
  }

  async function retryUpload(id: string): Promise<void> {
    const idx = attachments.value.findIndex((a) => a.id === id)
    if (idx === -1) return
    const file = attachments.value[idx].file
    attachments.value = attachments.value.filter((a) => a.id !== id)
    await uploadFile(file)
  }

  const activeAttachmentIds = computed<string[]>(() => {
    return attachments.value
      .filter((a) => a.status === 'success' && a.serverId)
      .map((a) => a.serverId!)
  })

  async function loadConversation(tid: string) {
    const { fetchConversationMessages } = await import('@/services/conversationApi')
    threadId.value = tid
    loading.value = true
    try {
      const detail = await fetchConversationMessages(tid)

      messages.value = detail.messages
        .filter((m) => m.role === 'user' || m.role === 'assistant')
        .map((m, idx) => ({
          id: idx + 1,
          role: m.role as 'user' | 'assistant',
          content: m.content,
          streaming: false,
        }))
      nextId = messages.value.length + 1
    } catch {
      // ignore
    }

    loading.value = false
  }

  return {
    messages,
    loading,
    threadId,
    traceEnabled,
    attachments,
    activeAttachmentIds,
    sendMessage,
    clearMessages,
    stopGeneration,
    loadConversation,
    uploadFile,
    removeAttachment,
    retryUpload,
  }
})
