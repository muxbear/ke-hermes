<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Upload, X, FileType2, FileCode2, FileText, FileSpreadsheet, FileImage, Globe } from 'lucide-vue-next'
import type { DocType } from '@/types/knowledgeBase'
import { DOC_TYPE_CONFIG } from '@/types/knowledgeBase'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
  upload: [files: File[]]
}>()

const dialogVisible = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)
const files = ref<File[]>([])

const docTypeIcons: Record<DocType, typeof FileText> = {
  pdf: FileType2, md: FileCode2, docx: FileText, csv: FileSpreadsheet, image: FileImage, html: Globe,
}

const ALLOWED_TYPES = '.pdf,.docx,.xlsx,.pptx,.csv,.json,.md,.html,.txt,.png,.jpg,.jpeg'

const hasFiles = computed(() => files.value.length > 0)

watch(() => props.visible, (v) => {
  dialogVisible.value = v
  if (v) reset()
})

function reset() {
  files.value = []
}

function handleClose() {
  dialogVisible.value = false
  emit('close')
}

function getFileType(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase()
  return ext && ext in DOC_TYPE_CONFIG ? ext : 'md'
}

function getFileIcon(name: string) {
  const ft = getFileType(name) as DocType
  return docTypeIcons[ft] || FileText
}

function getFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files) {
    for (let i = 0; i < input.files.length; i++) {
      const file = input.files[i]
      if (file.size > 100 * 1024 * 1024) {
        // Skip files > 100MB
        continue
      }
      files.value.push(file)
    }
  }
  // Reset input so the same file can be selected again
  input.value = ''
}

function handleDragOver(e: DragEvent) {
  e.preventDefault()
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  if (e.dataTransfer?.files) {
    for (let i = 0; i < e.dataTransfer.files.length; i++) {
      files.value.push(e.dataTransfer.files[i])
    }
  }
}

function removeFile(index: number) {
  files.value = files.value.filter((_, i) => i !== index)
}

function handleUpload() {
  if (!hasFiles.value) return
  emit('upload', [...files.value])
  dialogVisible.value = false
}
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    width="520px"
    :close-on-click-modal="false"
    @close="handleClose"
    class="upload-doc-dialog"
    destroy-on-close
  >
    <template #header>
      <div class="dialog-header">
        <h2 class="dialog-title">上传文档</h2>
        <p class="dialog-desc">支持 PDF / Word / Markdown / HTML / CSV / JSON / TXT / 图片</p>
      </div>
    </template>

    <div class="dialog-body">
      <!-- 文件选择 -->
      <input
        ref="fileInput"
        type="file"
        :accept="ALLOWED_TYPES"
        multiple
        style="display: none"
        @change="handleFileChange"
      />

      <!-- 拖拽区 -->
      <div
        class="dropzone"
        @click="triggerFileInput"
        @dragover="handleDragOver"
        @drop="handleDrop"
      >
        <Upload :size="32" class="dropzone-icon" />
        <div class="dropzone-text">拖拽文件到此处或点击选择</div>
        <div class="dropzone-sub">支持 PDF / Word / Excel / Markdown / HTML / CSV / JSON / TXT / 图片，单文件最大 100MB</div>
      </div>

      <!-- 文件列表 -->
      <div v-if="hasFiles" class="file-list">
        <div v-for="(f, i) in files" :key="i" class="file-item">
          <component :is="getFileIcon(f.name)" :size="16" class="file-item-icon" />
          <span class="file-item-name">{{ f.name }}</span>
          <span class="file-item-size">{{ getFileSize(f.size) }}</span>
          <button class="file-item-del" @click="removeFile(i)">
            <X :size="14" />
          </button>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <button class="btn-cancel" @click="handleClose">取消</button>
        <button class="btn-upload" :disabled="!hasFiles" @click="handleUpload">
          <Upload :size="16" />开始索引 ({{ files.length }})
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
/* ─── Header ─── */
.dialog-header {
  padding: 0;
}

.dialog-title {
  font-size: 17px;
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0;
}

.dialog-desc {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  margin: 6px 0 0;
}

/* ─── Body ─── */
.dialog-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Dropzone */
.dropzone {
  border: 2px dashed rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-xl);
  padding: 32px 20px;
  text-align: center;
  transition: border-color 0.2s;
  cursor: pointer;
}

.dropzone:hover {
  border-color: rgba(59, 130, 246, 0.4);
}

.dropzone-icon {
  color: #93c5fd;
  margin-bottom: 10px;
}

.dropzone-text {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
}

.dropzone-sub {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin-top: 4px;
}

/* File list */
.file-list {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-lg);
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 12px;
  font-size: var(--font-size-sm);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.file-item:last-child {
  border-bottom: none;
}

.file-item-icon {
  color: var(--foreground-secondary);
  flex-shrink: 0;
}

.file-item-name {
  flex: 1;
  color: var(--foreground-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-item-size {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  flex-shrink: 0;
}

.file-item-del {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--foreground-muted);
  cursor: pointer;
  transition: all 0.15s;
}

.file-item-del:hover {
  background: rgba(244, 63, 94, 0.12);
  color: #f87171;
}

/* ─── Footer ─── */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-cancel {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 38px;
  padding: 0 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: var(--foreground-primary);
  font-size: var(--font-size-base);
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-cancel:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
}

.btn-upload {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 38px;
  padding: 0 22px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border: none;
  border-radius: 10px;
  color: #fff;
  font-size: var(--font-size-base);
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-upload:hover { opacity: 0.9; }

.btn-upload:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>

<!-- 全局：对话框底色 -->
<style>
.upload-doc-dialog {
  --el-dialog-bg-color: #0f172e;
  --el-dialog-border-color: rgba(255, 255, 255, 0.1);
}

.upload-doc-dialog .el-dialog {
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.upload-doc-dialog .el-dialog__header {
  padding: 24px 28px 0;
}

.upload-doc-dialog .el-dialog__body {
  padding: 20px 28px;
}

.upload-doc-dialog .el-dialog__footer {
  padding: 0 28px 24px;
}
</style>
