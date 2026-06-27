<script setup lang="ts">
import { computed } from 'vue'
import { Bot, Wrench, ChevronDown, ChevronRight, Loader } from 'lucide-vue-next'
import { marked } from 'marked'
import type { ExecutionBlock } from '@/types/chat'
import ToolCallCard from './ToolCallCard.vue'
import AgentCard from './AgentCard.vue'

const props = defineProps<{
  blocks: ExecutionBlock[]
}>()

function renderMarkdown(text: string): string {
  if (!text) return ''
  return marked.parse(text, { breaks: true }) as string
}
</script>

<template>
  <div class="trace-tree">
    <template v-for="(block, idx) in blocks" :key="idx">
      <div v-if="block.type === 'text'" class="markdown-body" v-html="renderMarkdown(block.content)" />
      <ToolCallCard v-else-if="block.type === 'tool_call'" :tool="block.toolCall" />
      <AgentCard v-else-if="block.type === 'sub_agent'" :agent="block.subAgent" />
    </template>
  </div>
</template>

<style scoped>
.trace-tree {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 10px 0 4px;
  font-weight: var(--font-weight-semibold);
}

.markdown-body :deep(h1) { font-size: 17px; }
.markdown-body :deep(h2) { font-size: 15px; }
.markdown-body :deep(h3) { font-size: var(--font-size-md); }

.markdown-body :deep(p) {
  margin: 4px 0;
  line-height: 1.6;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 4px 0;
  padding-left: 18px;
}

.markdown-body :deep(li) {
  margin: 2px 0;
  line-height: 1.5;
}

.markdown-body :deep(code) {
  padding: 1px 5px;
  border-radius: var(--radius-sm);
  background: var(--surface-secondary);
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.markdown-body :deep(pre) {
  margin: 6px 0;
  padding: 10px;
  border-radius: var(--radius-md);
  background: var(--surface-secondary);
  overflow-x: auto;
}

.markdown-body :deep(pre code) {
  padding: 0;
  background: none;
}

.markdown-body :deep(blockquote) {
  margin: 4px 0;
  padding: 4px 10px;
  border-left: 3px solid var(--accent-primary);
  background: var(--surface-secondary);
  color: var(--foreground-secondary);
}

.markdown-body :deep(a) {
  color: var(--accent-primary);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(strong) {
  font-weight: var(--font-weight-semibold);
}
</style>
