<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { storeToRefs } from 'pinia'
import { Mic, ArrowUp, Image, Paperclip, Globe, HardDrive, Database, Square } from 'lucide-vue-next'
import { useChatStore } from '@/stores/chat'
import AttachmentBar from './AttachmentBar.vue'

const chatStore = useChatStore()
const { attachments } = storeToRefs(chatStore)

const inputText = ref('')
const inputRef = ref(null)
const webSearchEnabled = ref(false)
const fileInputRef = ref(null)
const imageInputRef = ref(null)
const popoverMenu = ref(null)

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

function toggleWebSearch() {
  webSearchEnabled.value = !webSearchEnabled.value
}

function openPopover(type) {
  popoverMenu.value = popoverMenu.value === type ? null : type
}

function triggerFileInput() {
  popoverMenu.value = null
  fileInputRef.value?.click()
}

function triggerImageInput() {
  popoverMenu.value = null
  imageInputRef.value?.click()
}

function onFilesSelected(e) {
  const files = e.target.files
  if (!files || files.length === 0) return
  for (const file of files) {
    chatStore.uploadFile(file)
  }
  e.target.value = ''
}

function onImagesSelected(e) {
  const files = e.target.files
  if (!files || files.length === 0) return
  for (const file of files) {
    chatStore.uploadFile(file)
  }
  e.target.value = ''
}

function onPaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items) return
  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.type.startsWith('image/')) {
      e.preventDefault()
      const blob = item.getAsFile()
      if (blob) {
        const timestamp = Date.now()
        const ext = item.type.split('/')[1] || 'png'
        const file = new File([blob], `paste-${timestamp}.${ext}`, { type: item.type })
        chatStore.uploadFile(file)
      }
    }
  }
}

function handleClickOutside(e) {
  if (!popoverMenu.value) return
  const popover = document.querySelector('.upload-popover')
  if (popover && !popover.contains(e.target)) {
    popoverMenu.value = null
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
  <div class="input-bar">
    <div class="input-area">
      <AttachmentBar />
      <textarea
        ref="inputRef"
        v-model="inputText"
        @keydown="handleKeydown"
        @input="autoResize"
        @paste="onPaste"
        :disabled="chatStore.loading"
        placeholder="输入消息..."
        class="input-field"
        rows="2"
      />

      <div class="input-toolbar">
        <button
          class="web-search-btn"
          :class="{ active: webSearchEnabled }"
          @click="toggleWebSearch"
        >
          <Globe :size="14" />
          <span>联网搜索</span>
        </button>

        <div class="toolbar-actions">
          <div class="tool-btn-wrap">
            <button
              class="tool-btn"
              title="快速理解总结文件，支持PDF、Word、Excel、PPT、TXT、Python、Java等，最多10个，最大100MB"
              @click.stop="openPopover('attachment')"
            >
              <Paperclip :size="16" />
            </button>
            <div v-if="popoverMenu === 'attachment'" class="upload-popover">
              <div class="popover-item" @click.stop="triggerFileInput">
                <HardDrive :size="14" />
                <span>上传本地文件</span>
              </div>
              <div class="popover-item" @click.stop="triggerFileInput">
                <Database :size="14" />
                <span>上传知识库文件</span>
              </div>
            </div>
            <input
              ref="fileInputRef"
              type="file"
              data-attachment-input
              accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.py,.java,.csv,.md,.json,.xml,.yaml,.yml,.png,.jpg,.jpeg,.gif,.webp,.bmp"
              multiple
              hidden
              @change="onFilesSelected"
            />
          </div>

          <div class="tool-btn-wrap">
            <button
              class="tool-btn"
              title="一键解读图片内容，支持jpg、png、jpeg等，最多10个，最大10MB"
              @click.stop="openPopover('image')"
            >
              <Image :size="16" />
            </button>
            <div v-if="popoverMenu === 'image'" class="upload-popover">
              <div class="popover-item" @click.stop="triggerImageInput">
                <HardDrive :size="14" />
                <span>上传本地图片</span>
              </div>
              <div class="popover-item" @click.stop="triggerImageInput">
                <Database :size="14" />
                <span>上传知识库图片</span>
              </div>
            </div>
            <input
              ref="imageInputRef"
              type="file"
              accept=".jpg,.jpeg,.png,.gif,.webp,.bmp"
              multiple
              hidden
              @change="onImagesSelected"
            />
          </div>

          <button class="tool-btn" title="点击开启语音输入">
            <Mic :size="16" />
          </button>
          <button
            v-if="!chatStore.loading"
            class="send-btn"
            :disabled="!inputText.trim()"
            @click="handleSend"
          >
            <ArrowUp :size="18" />
          </button>
          <button
            v-else
            class="stop-btn"
            @click="chatStore.stopGeneration()"
            title="停止生成"
          >
            <Square :size="14" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.input-bar {
  padding: 12px 24px 16px;
  background: var(--surface-card);
  border-top: 1px solid var(--border-subtle);
}

.input-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: #0d1429;
  border: 1px solid rgba(59, 130, 246, 0.08);
  border-radius: var(--radius-xl);
  padding: 12px 0 8px;
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
  line-height: 1.6;
  min-height: 48px;
  max-height: 120px;
  padding: 0 16px;
}

.attachment-bar {
  padding-left: 16px;
  padding-right: 16px;
}

.input-toolbar {
  padding: 0 16px;
}

.input-field::placeholder {
  color: var(--foreground-muted);
}

.input-field:disabled {
  opacity: 0.5;
}

.input-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.web-search-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
  background: rgba(59, 130, 246, 0.08);
  color: var(--foreground-secondary);
  font-size: var(--font-size-sm);
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
}

.web-search-btn:hover {
  background: rgba(59, 130, 246, 0.14);
  color: var(--foreground-primary);
}

.web-search-btn.active {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: #fff;
}

.tool-btn-wrap {
  position: relative;
}

.tool-btn {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-full);
  border: none;
  background: transparent;
  color: var(--foreground-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
}

.tool-btn:hover {
  background: rgba(59, 130, 246, 0.1);
  color: var(--foreground-primary);
}

.upload-popover {
  position: absolute;
  bottom: calc(100% + 8px);
  right: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px;
  border-radius: var(--radius-lg);
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  z-index: 100;
  min-width: 160px;
}

.popover-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  color: var(--foreground-secondary);
  font-size: var(--font-size-base);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s;
}

.popover-item:hover {
  background: var(--surface-secondary);
  color: var(--foreground-primary);
}

.send-btn {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-full);
  border: none;
  background: var(--accent-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
  margin-left: 2px;
}

.send-btn:hover:not(:disabled) {
  opacity: 0.85;
}

.send-btn:disabled {
  background: rgba(59, 130, 246, 0.2);
  color: var(--foreground-muted);
  cursor: not-allowed;
}

.stop-btn {
  width: 34px;
  height: 34px;
  border-radius: var(--radius-full);
  border: none;
  background: var(--accent-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
  margin-left: 2px;
}

.stop-btn:hover {
  background: #dc2626;
}
</style>
