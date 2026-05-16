<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Mic, Plus, Send, ChevronDown, FileText, Image } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import { useUiStore } from '@/stores/ui'

const chatStore = useChatStore()
const uiStore = useUiStore()

const inputText = ref('')
const inputBarRef = ref(null)

function handleSend() {
  const text = inputText.value.trim()
  if (!text || chatStore.loading) return
  chatStore.sendMessage(text)
  inputText.value = ''
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleClickOutside(e) {
  if (inputBarRef.value && !inputBarRef.value.contains(e.target)) {
    uiStore.closePlusMenu()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="input-bar" ref="inputBarRef">
    <div class="input-row">
      <div class="input-field-wrap">
        <input
          v-model="inputText"
          @keydown="handleKeydown"
          :disabled="chatStore.loading"
          placeholder="输入消息..."
          class="input-field"
        />
        <button class="mic-btn">
          <Mic :size="16" />
        </button>
      </div>
      <button class="plus-btn" @click.stop="uiStore.togglePlusMenu">
        <Plus :size="16" />
      </button>
      <button
        class="send-btn"
        :disabled="!inputText.trim() || chatStore.loading"
        @click="handleSend"
      >
        <Send :size="16" />
      </button>
    </div>

    <div v-if="uiStore.plusMenuOpen" class="plus-menu">
      <div class="plus-menu-item">
        <FileText :size="14" />
        <span>上传附件</span>
      </div>
      <div class="plus-menu-item">
        <Image :size="14" />
        <span>上传图片</span>
      </div>
    </div>

    <div class="input-footer">
      <div class="model-pill">
        <span>{{ uiStore.selectedModel }}</span>
        <ChevronDown :size="12" />
      </div>
      <span class="kb-hint">Enter 发送 · Shift+Enter 换行</span>
    </div>
  </div>
</template>

<style scoped>
.input-bar {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 10px 20px;
  background: var(--surface-card);
  border-top: 1px solid var(--border-subtle);
}

.input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.input-field-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: var(--radius-xl);
  background: var(--surface-secondary);
}

.input-field {
  flex: 1;
  border: none;
  outline: none;
  background: none;
  font-size: var(--font-size-md);
  color: var(--foreground-primary);
}

.input-field::placeholder {
  color: var(--foreground-muted);
}

.input-field:disabled {
  opacity: 0.5;
}

.mic-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  border: none;
  background: var(--surface-secondary);
  color: var(--foreground-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.mic-btn:hover {
  background: var(--border-subtle);
}

.plus-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  border: none;
  background: var(--surface-secondary);
  color: var(--foreground-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.plus-btn:hover {
  background: var(--border-subtle);
}

.send-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  border: none;
  background: var(--accent-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.send-btn:disabled {
  background: var(--surface-secondary);
  color: var(--foreground-muted);
  cursor: not-allowed;
}

.plus-menu {
  position: absolute;
  bottom: 80px;
  left: 20px;
  width: 160px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px;
  border-radius: var(--radius-lg);
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  z-index: 100;
}

.plus-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  background: var(--surface-secondary);
  color: var(--foreground-secondary);
  font-size: var(--font-size-base);
  cursor: pointer;
}

.plus-menu-item:hover {
  background: var(--border-subtle);
  color: var(--foreground-primary);
}

.input-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.model-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  background: var(--surface-secondary);
  font-size: var(--font-size-xs);
  color: var(--foreground-secondary);
}

.kb-hint {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}
</style>