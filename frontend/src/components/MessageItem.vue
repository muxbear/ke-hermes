<script setup>
import { computed } from 'vue'
import { Sparkles, UserCircle } from 'lucide-vue-next'
import { marked } from 'marked'
import TracePanel from './TracePanel.vue'

const props = defineProps({
  message: {
    type: Object,
    required: true,
  },
})

const renderedContent = computed(() => {
  if (props.message.role === 'user') return props.message.content
  if (!props.message.content) return ''
  return marked.parse(props.message.content, { breaks: true })
})
</script>

<template>
  <div class="message-item" :class="[message.role, { streaming: message.streaming }]">
    <div class="message-avatar">
      <UserCircle v-if="message.role === 'user'" :size="32" />
      <Sparkles v-else :size="32" />
    </div>
    <div class="message-body">
      <div class="message-bubble">
        <TracePanel
          v-if="message.role === 'assistant' && message.traces && message.traces.length > 0"
          :traces="message.traces"
          :streaming="message.streaming"
        />
        <div v-if="message.role === 'assistant'" class="markdown-body" v-html="renderedContent"></div>
        <div v-else>{{ message.content }}</div>
        <span v-if="message.streaming && !message.content" class="typing-indicator">
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
  0%, 60%, 100% { opacity: 0.3; transform: scale(0.8); }
  30% { opacity: 1; transform: scale(1); }
}

/* Markdown rendered styles inside assistant bubble */
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 12px 0 6px;
  font-weight: var(--font-weight-semibold);
}

.markdown-body :deep(h1) { font-size: 18px; }
.markdown-body :deep(h2) { font-size: 16px; }
.markdown-body :deep(h3) { font-size: 15px; }
.markdown-body :deep(h4) { font-size: var(--font-size-md); }

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

.markdown-body :deep(strong) {
  font-weight: var(--font-weight-semibold);
}

.markdown-body :deep(em) {
  font-style: italic;
}
</style>