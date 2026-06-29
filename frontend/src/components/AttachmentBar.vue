<script setup lang="ts">
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores/chat'
import { X, Plus, AlertTriangle, FileText } from 'lucide-vue-next'

const chatStore = useChatStore()
const { attachments } = storeToRefs(chatStore)

const hasAttachments = computed(() => attachments.value.length > 0)

function isImage(mimeType: string): boolean {
  return mimeType.startsWith('image/')
}

function getPreviewUrl(file: File): string {
  return URL.createObjectURL(file)
}

function triggerUpload() {
  const el = document.querySelector<HTMLInputElement>('input[data-attachment-input]')
  el?.click()
}
</script>

<template>
  <div v-if="hasAttachments" class="attachment-bar">
    <div
      v-for="att in attachments"
      :key="att.id"
      class="attachment-item"
      :class="{ failed: att.status === 'failed' }"
      @click="att.status === 'failed' && chatStore.retryUpload(att.id)"
    >
      <div class="attachment-preview">
        <img
          v-if="isImage(att.mimeType)"
          :src="getPreviewUrl(att.file)"
          class="attachment-thumb"
          :class="{ 'thumb-dimmed': att.status !== 'success' }"
          alt=""
        />
        <div v-else class="attachment-icon-placeholder">
          <FileText :size="20" />
        </div>

        <div v-if="att.status === 'uploading'" class="progress-overlay">
          <span class="progress-text">{{ att.progress }}%</span>
        </div>

        <div v-if="att.status === 'failed'" class="failed-badge">
          <AlertTriangle :size="14" />
        </div>

        <button
          v-if="att.status !== 'uploading'"
          class="delete-btn"
          @click.stop="chatStore.removeAttachment(att.id)"
        >
          <X :size="10" />
        </button>
      </div>

      <span class="attachment-name">{{ att.filename }}</span>
    </div>

    <button class="attachment-item add-more-btn" @click="triggerUpload">
      <div class="attachment-preview add-more-preview">
        <Plus :size="20" />
      </div>
    </button>
  </div>
</template>

<style scoped>
.attachment-bar {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding-bottom: 8px;
  flex-wrap: wrap;
}

.attachment-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  max-width: 72px;
}

.attachment-preview {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
}

.attachment-item.failed .attachment-preview {
  border-color: #ef4444;
  cursor: pointer;
}

.attachment-item.failed .attachment-preview:hover {
  background: rgba(239, 68, 68, 0.05);
}

.attachment-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-dimmed {
  opacity: 0.5;
}

.attachment-icon-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--foreground-muted);
}

.progress-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
}

.progress-text {
  color: #fff;
  font-size: 11px;
  font-weight: 600;
}

.failed-badge {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.delete-btn {
  position: absolute;
  top: -4px;
  right: -4px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid var(--border-medium);
  background: var(--surface-card);
  color: var(--foreground-secondary);
  display: none;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.attachment-preview:hover .delete-btn {
  display: flex;
}

.delete-btn:hover {
  background: #ef4444;
  color: #fff;
  border-color: #ef4444;
}

.attachment-name {
  font-size: 10px;
  color: var(--foreground-muted);
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

.add-more-btn {
  cursor: pointer;
  border: none;
  background: none;
  padding: 0;
  font-family: inherit;
}

.add-more-preview {
  border-style: dashed;
  border-color: var(--border-medium);
  color: var(--foreground-muted);
  cursor: pointer;
  transition: all 0.15s;
}

.add-more-preview:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}
</style>
