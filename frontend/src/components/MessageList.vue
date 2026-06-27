<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import MessageItem from './MessageItem.vue'

const chatStore = useChatStore()
const scrollContainer = ref(null)

const lastContent = computed(() => {
  const msgs = chatStore.messages
  if (msgs.length === 0) return ''
  return msgs[msgs.length - 1].content
})

const streamingBlocksLen = computed(() => {
  const last = chatStore.messages[chatStore.messages.length - 1]
  if (last?.blocks) return last.blocks.length
  return 0
})

function scrollToBottom() {
  nextTick(() => {
    const el = scrollContainer.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  })
}

watch(() => chatStore.messages.length, scrollToBottom)
watch(lastContent, scrollToBottom)
watch(streamingBlocksLen, scrollToBottom)
</script>

<template>
  <div class="message-list" ref="scrollContainer">
    <MessageItem v-for="msg in chatStore.messages" :key="msg.id" :message="msg" />
  </div>
</template>

<style scoped>
.message-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: var(--surface-primary);
}
</style>