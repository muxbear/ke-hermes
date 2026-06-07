<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { Mic, Plus, Send, FileText, Image } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import { useUiStore } from '@/stores/ui'

const chatStore = useChatStore()
const uiStore = useUiStore()

const inputText = ref('')
const inputRef = ref(null)
const inputBarRef = ref(null)

function handleSend() {
  const text = inputText.value.trim()
  if (!text || chatStore.loading) return
  chatStore.sendMessage(text)
  inputText.value = ''
  nextTick(() => {
    if (inputRef.value) inputRef.value.style.height = 'auto'
  })
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function autoResize() {
  const el = inputRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
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

watch(() => chatStore.loading, (loading) => {
  if (!loading) {
    nextTick(() => inputRef.value?.focus())
  }
})
</script>

<template>
  <div class="input-bar" ref="inputBarRef">
    <div class="input-row">
      <div class="input-field-wrap">
        <textarea
          ref="inputRef"
          v-model="inputText"
          @keydown="handleKeydown"
          @input="autoResize"
          :disabled="chatStore.loading"
          placeholder="输入消息..."
          class="input-field"
          rows="1"
        />
        <button class="mic-btn">
          <Mic :size="16" />
        </button>
      </div>
      <div class="plus-wrap">
        <button class="plus-btn" @click.stop="uiStore.togglePlusMenu">
          <Plus :size="16" />
        </button>
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
      </div>
      <button
        class="send-btn"
        :disabled="!inputText.trim() || chatStore.loading"
        @click="handleSend"
      >
        <Send :size="16" />
      </button>
    </div>

    <div class="trace-toggle-row">
      <el-switch
        v-model="chatStore.traceEnabled"
        size="small"
        :disabled="chatStore.loading"
      />
      <span class="trace-toggle-label">跟踪调用</span>
    </div>

    <span class="kb-hint">Enter 发送 · Shift+Enter 换行</span>
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
  align-items: flex-end;
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
  font-family: inherit;
  color: var(--foreground-primary);
  resize: none;
  line-height: 1.5;
  min-height: 24px;
  max-height: 120px;
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

.plus-wrap {
  position: relative;
}

.plus-menu {
  position: absolute;
  bottom: calc(100% + 8px);
  right: 0;
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

.trace-toggle-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 4px;
}

.trace-toggle-label {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.kb-hint {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  text-align: center;
}
</style>