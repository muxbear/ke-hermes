<script setup lang="ts">
import { computed, ref } from 'vue'
import { Sparkles, UserCircle, Brain, ChevronDown, ChevronRight, FileText } from 'lucide-vue-next'
import { marked } from 'marked'
import { useChatStore } from '@/stores/chat'
import TraceTree from './TraceTree.vue'
import type { ChatMessage } from '@/types/chat'

const props = defineProps<{
  message: ChatMessage
}>()

const chatStore = useChatStore()
const showReasoning = ref(false)

const hasBlocks = computed(() => {
  return chatStore.traceEnabled && props.message.blocks && props.message.blocks.length > 0
})

const renderedContent = computed(() => {
  if (props.message.role === 'user') return props.message.content
  if (!props.message.content) return ''
  return marked.parse(props.message.content, { breaks: true })
})

function isImage(mimeType: string): boolean {
  return mimeType.startsWith('image/')
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}
</script>

<template>
  <div class="message-item" :class="[message.role, { streaming: message.streaming }]">
    <div class="message-avatar">
      <UserCircle v-if="message.role === 'user'" :size="32" />
      <Sparkles v-else :size="32" />
    </div>
    <div class="message-body">
      <div class="message-bubble">
        <!-- Trace mode: hierarchical card view -->
        <TraceTree
          v-if="hasBlocks"
          :blocks="message.blocks!"
        />
        <!-- Normal mode: reasoning section -->
        <div v-else-if="message.role === 'assistant' && message.reasoning" class="reasoning-section">
          <div class="reasoning-toggle" @click="showReasoning = !showReasoning">
            <Brain :size="12" />
            <span>思考过程</span>
            <ChevronDown v-if="!showReasoning" :size="12" />
            <ChevronRight v-else :size="12" />
          </div>
          <div v-if="showReasoning" class="reasoning-content">
            {{ message.reasoning }}
          </div>
        </div>
        <!-- Normal mode: markdown content -->
        <div
          v-if="!hasBlocks && message.role === 'assistant'"
          class="markdown-body"
          v-html="renderedContent"
        ></div>
        <div v-if="message.role === 'user'">
          <!-- Attachment thumbnails -->
          <div v-if="message.attachments && message.attachments.length > 0" class="user-attachments">
            <div v-for="(att, i) in message.attachments" :key="i" class="user-attachment-item">
              <img v-if="isImage(att.mimeType)" :src="att.thumbnailUrl" class="user-att-thumb" alt="" />
              <FileText v-else :size="24" />
              <span class="user-att-name">{{ att.filename }}</span>
              <span class="user-att-size">{{ formatFileSize(att.size) }}</span>
            </div>
          </div>
          {{ message.content }}
        </div>
        <span v-if="message.streaming && !message.content && !hasBlocks" class="typing-indicator">
          <span class="dot" />
          <span class="dot" />
          <span class="dot" />
        </span>
      </div>
      <div v-if="message.role === 'assistant' && !message.streaming" class="message-meta">
        DeepSeek V4
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-item {
  display: flex;
  gap: 10px;
  width: 100%;
}

.message-item.user {
  justify-content: flex-end;
}

.message-item.user .message-avatar {
  order: 1;
}

.message-item.user .message-body {
  order: 0;
}

.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-item.assistant .message-avatar {
  background: var(--accent-primary);
  color: white;
}

.message-item.user .message-avatar {
  background: var(--surface-secondary);
  color: var(--foreground-secondary);
}

.message-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 70%;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: var(--radius-xl);
  font-size: var(--font-size-md);
  line-height: 1.5;
  word-break: break-word;
}

.message-item.user .message-bubble {
  background: var(--accent-primary);
  color: white;
}

.message-item.assistant .message-bubble {
  background: var(--surface-card);
  border: 1px solid var(--border-medium);
  color: var(--foreground-primary);
}

.message-meta {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.typing-indicator {
  display: inline-flex;
  gap: 4px;
  padding: 4px 0;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-primary);
  animation: typing 1.4s infinite;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%,
  60%,
  100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  30% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Markdown rendered styles inside assistant bubble */
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 12px 0 6px;
  font-weight: var(--font-weight-semibold);
}

.markdown-body :deep(h1) {
  font-size: 18px;
}
.markdown-body :deep(h2) {
  font-size: 16px;
}
.markdown-body :deep(h3) {
  font-size: 15px;
}
.markdown-body :deep(h4) {
  font-size: var(--font-size-md);
}

.markdown-body :deep(p) {
  margin: 6px 0;
  line-height: 1.6;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 6px 0;
  padding-left: 20px;
}

.markdown-body :deep(li) {
  margin: 2px 0;
  line-height: 1.5;
}

.markdown-body :deep(code) {
  padding: 2px 6px;
  border-radius: var(--radius-sm);
  background: var(--surface-secondary);
  font-size: 13px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.markdown-body :deep(pre) {
  margin: 8px 0;
  padding: 12px;
  border-radius: var(--radius-lg);
  background: var(--surface-secondary);
  overflow-x: auto;
}

.markdown-body :deep(pre code) {
  padding: 0;
  background: none;
}

.markdown-body :deep(blockquote) {
  margin: 6px 0;
  padding: 6px 12px;
  border-left: 3px solid var(--accent-primary);
  background: var(--surface-secondary);
  color: var(--foreground-secondary);
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  margin: 8px 0;
  width: 100%;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--border-medium);
  padding: 6px 10px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: var(--surface-secondary);
  font-weight: var(--font-weight-semibold);
}

.markdown-body :deep(a) {
  color: var(--accent-primary);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-subtle);
  margin: 10px 0;
}

.reasoning-section {
  margin-bottom: 8px;
  border-left: 3px solid #a78bfa;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  background: rgba(167, 139, 250, 0.06);
  font-size: var(--font-size-xs);
  overflow: hidden;
}

.reasoning-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  cursor: pointer;
  color: #7c3aed;
  user-select: none;
}

.reasoning-toggle:hover {
  background: rgba(167, 139, 250, 0.1);
}

.reasoning-content {
  padding: 6px 10px 8px 24px;
  color: var(--foreground-muted);
  white-space: pre-wrap;
  word-break: break-word;
  font-style: italic;
  line-height: 1.5;
}

.markdown-body :deep(strong) {
  font-weight: var(--font-weight-semibold);
}

.markdown-body :deep(em) {
  font-style: italic;
}

.user-attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 8px;
}

.user-attachment-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  width: 64px;
  padding: 4px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.12);
}

.user-att-thumb {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 4px;
}

.user-att-name {
  font-size: 9px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
  text-align: center;
  opacity: 0.85;
}

.user-att-size {
  font-size: 8px;
  opacity: 0.6;
}
</style>
