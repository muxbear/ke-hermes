<script setup lang="ts">
import { ref, computed, watch, reactive } from 'vue'
import { X, Upload, RefreshCw, FileArchive, CheckCheck, XCircle, UploadCloud } from 'lucide-vue-next'
import type { Tool, ToolCreateRequest, ToolCategory, ToolStatus } from '@/types/tool'
import { CATEGORY_META } from '@/types/tool'

const props = defineProps<{
  visible: boolean
  tool: Tool | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', data: ToolCreateRequest): void
}>()

const isNew = computed(() => !props.tool)

const form = reactive({
  name: '',
  displayName: '',
  description: '',
  category: 'other' as ToolCategory,
  status: 'enabled' as ToolStatus,
  version: '1.0.0',
  tagsInput: '',
})

// -- Package upload --
type ParseState = 'idle' | 'parsing' | 'done' | 'error'
const parseState = ref<ParseState>('idle')
const pkg = ref<{ file: File; size: string } | null>(null)
const pkgFile = ref<File | null>(null)

watch(
  () => props.tool,
  (t) => {
    if (t) {
      form.name = t.name
      form.displayName = t.displayName
      form.description = t.description
      form.category = t.category
      form.status = t.status
      form.version = t.version
      form.tagsInput = t.tags.join(', ')
    } else {
      form.name = ''
      form.displayName = ''
      form.description = ''
      form.category = 'other'
      form.status = 'enabled'
      form.version = '1.0.0'
      form.tagsInput = ''
    }
    // Reset upload state
    pkg.value = null
    parseState.value = 'idle'
    pkgFile.value = null
  },
  { immediate: true },
)
const dragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

const ACCEPTED_EXTS = ['.zip', '.tar.gz', '.tgz', '.tar.bz2', '.tar.xz']

function isValidPkg(name: string) {
  return ACCEPTED_EXTS.some((ext) => name.toLowerCase().endsWith(ext))
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function handleFile(file: File) {
  if (!isValidPkg(file.name)) return
  pkg.value = { file, size: formatBytes(file.size) }
  pkgFile.value = file
  parseState.value = 'idle'
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  dragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) handleFile(file)
}

function handleFileInput(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) handleFile(file)
  target.value = ''
}

function clearPkg() {
  pkg.value = null
  pkgFile.value = null
  parseState.value = 'idle'
}

function handleParse() {
  if (!pkg.value) return
  parseState.value = 'parsing'
  setTimeout(() => {
    try {
      const base = pkg.value!.file.name.replace(/\.(zip|tar\.gz|tgz|tar\.bz2|tar\.xz)$/i, '')
      const versionMatch = base.match(/-(\d+\.\d+[.\d]*)$/)
      const rawName = versionMatch ? base.slice(0, base.lastIndexOf(versionMatch[0])) : base
      const ver = versionMatch ? versionMatch[1] : form.version
      const dn = rawName.replace(/[_-]/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
      form.name = rawName.toLowerCase().replace(/[- ]/g, '_')
      form.displayName = dn
      form.version = ver
      form.tagsInput = form.tagsInput || rawName.replace(/[_-]/g, ', ')
      parseState.value = 'done'
    } catch {
      parseState.value = 'error'
    }
  }, 900)
}

function handleSave() {
  if (!form.name.trim() || !form.displayName.trim()) return
  emit('save', {
    name: form.name.trim(),
    displayName: form.displayName.trim(),
    description: form.description,
    category: form.category,
    status: form.status,
    version: form.version,
    tags: form.tagsInput.split(',').map((t) => t.trim()).filter(Boolean),
  })
}

const categoryOptions = computed(() =>
  (Object.keys(CATEGORY_META) as ToolCategory[]).map((k) => ({
    key: k,
    label: CATEGORY_META[k].label,
  })),
)
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="tool-overlay" @click.self="emit('close')">
        <div class="tool-modal">
          <!-- Header -->
          <div class="modal-header">
            <div>
              <h2 class="modal-title">{{ isNew ? '添加第三方工具' : `编辑 ${tool?.displayName || ''}` }}</h2>
              <p class="modal-sub">{{ isNew ? '上传工具包或手动填写配置信息' : '修改工具基本信息与参数' }}</p>
            </div>
            <button class="modal-close" @click="emit('close')">
              <X :size="18" />
            </button>
          </div>

          <!-- Body -->
          <div class="modal-body">
            <div class="form-grid">
              <!-- Name row -->
              <div class="form-row form-row--2col">
                <div class="field">
                  <label class="field-label">显示名称 <span class="required">*</span></label>
                  <input
                    v-model="form.displayName"
                    type="text"
                    class="text-input"
                    placeholder="邮件发送"
                  />
                </div>
                <div class="field">
                  <label class="field-label">工具标识 <span class="required">*</span></label>
                  <input
                    v-model="form.name"
                    type="text"
                    class="text-input text-input--mono"
                    placeholder="send_email"
                  />
                </div>
              </div>

              <!-- Category + Status + Version -->
              <div class="form-row form-row--3col">
                <div class="field">
                  <label class="field-label">分类</label>
                  <select v-model="form.category" class="text-input">
                    <option v-for="opt in categoryOptions" :key="opt.key" :value="opt.key">
                      {{ opt.label }}
                    </option>
                  </select>
                </div>
                <div class="field">
                  <label class="field-label">状态</label>
                  <select v-model="form.status" class="text-input">
                    <option value="enabled">已启用</option>
                    <option value="disabled">已禁用</option>
                    <option value="unavailable">不可用</option>
                  </select>
                </div>
                <div class="field">
                  <label class="field-label">版本</label>
                  <input
                    v-model="form.version"
                    type="text"
                    class="text-input"
                    placeholder="1.0.0"
                  />
                </div>
              </div>

              <!-- Tags -->
              <div class="field">
                <label class="field-label">标签（逗号分隔）</label>
                <input
                  v-model="form.tagsInput"
                  type="text"
                  class="text-input"
                  placeholder="email, smtp, notification"
                />
              </div>

              <!-- Description -->
              <div class="field">
                <label class="field-label">描述</label>
                <textarea
                  v-model="form.description"
                  class="text-input textarea"
                  rows="2"
                  placeholder="工具功能简介…"
                />
              </div>

              <!-- Package upload (new only) -->
              <div v-if="isNew" class="field">
                <div class="field-label-row">
                  <Upload :size="14" class="label-icon" />
                  <label class="field-label">工具包上传</label>
                  <span class="label-badge">可选</span>
                </div>

                <!-- File selected state -->
                <div v-if="pkg" class="pkg-selected">
                  <div class="pkg-info">
                    <div class="pkg-icon">
                      <FileArchive :size="20" />
                    </div>
                    <div class="pkg-meta">
                      <span class="pkg-name">{{ pkg.file.name }}</span>
                      <span class="pkg-size">{{ pkg.size }}</span>
                    </div>
                    <div class="pkg-actions">
                      <template v-if="parseState === 'idle'">
                        <button class="btn btn-parse" @click="handleParse">
                          <RefreshCw :size="12" />解析包信息
                        </button>
                      </template>
                      <span v-else-if="parseState === 'parsing'" class="state-tag state-tag--parsing">
                        <RefreshCw :size="12" class="spin" />解析中…
                      </span>
                      <span v-else-if="parseState === 'done'" class="state-tag state-tag--done">
                        <CheckCheck :size="12" />解析成功
                      </span>
                      <span v-else-if="parseState === 'error'" class="state-tag state-tag--error">
                        <XCircle :size="12" />解析失败
                      </span>
                      <button class="btn-remove" @click="clearPkg">
                        <X :size="14" />
                      </button>
                    </div>
                  </div>
                  <p v-if="parseState === 'done'" class="pkg-hint">
                    已从压缩包中提取工具配置，表单字段已自动填充，你可以继续修改。
                  </p>
                </div>

                <!-- Drop zone -->
                <div
                  v-else
                  class="dropzone"
                  :class="{ dragging }"
                  @click="fileInput?.click()"
                  @dragover.prevent="dragging = true"
                  @dragleave.prevent="dragging = false"
                  @drop.prevent="handleDrop"
                >
                  <input
                    ref="fileInput"
                    type="file"
                    accept=".zip,.tar.gz,.tgz,.tar.bz2,.tar.xz"
                    hidden
                    @change="handleFileInput"
                  />
                  <UploadCloud :size="28" class="dz-icon" />
                  <p class="dz-text">
                    拖放压缩包至此，或 <span class="dz-link">点击选择文件</span>
                  </p>
                  <p class="dz-formats">支持 .zip · .tar.gz · .tgz · .tar.bz2 · .tar.xz</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="modal-footer">
            <span v-if="pkg && parseState === 'done'" class="footer-hint">
              <CheckCheck :size="14" />已附加压缩包：{{ pkg.file.name }}
            </span>
            <span v-else />
            <div class="footer-btns">
              <button class="btn btn-ghost" @click="emit('close')">取消</button>
              <button
                class="btn btn-primary"
                :disabled="!form.name.trim() || !form.displayName.trim()"
                @click="handleSave"
              >
                <Upload v-if="isNew" :size="14" />
                {{ isNew ? '添加工具' : '保存' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Overlay */
.tool-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-overlay);
  backdrop-filter: blur(4px);
  z-index: 9999;
}

.tool-modal {
  width: 560px;
  max-width: 92vw;
  max-height: 92vh;
  display: flex;
  flex-direction: column;
  background: var(--color-modal-bg);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-card);
  box-shadow: 0px 12px 60px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

/* Header */
.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

.modal-title {
  font-size: 17px;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.modal-sub {
  margin: 4px 0 0;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.modal-close {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text-primary);
}

/* Body */
.modal-body {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.form-row {
  display: grid;
  gap: 12px;
}

.form-row--2col { grid-template-columns: 1fr 1fr; }
.form-row--3col { grid-template-columns: 1fr 1fr 1fr; }

/* Field */
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.label-icon { color: var(--accent-primary); }

.field-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-label);
}

.label-badge {
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.1);
  font-size: 10px;
  color: var(--foreground-muted);
}

.required { color: #ef4444; }

.text-input {
  width: 100%;
  padding: 9px 12px;
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-input);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  font-family: var(--font-family-base);
  outline: none;
  box-sizing: border-box;
  transition: border-color var(--transition-fast);
}

.text-input::placeholder { color: var(--color-text-muted); }
.text-input:focus { border-color: var(--accent-primary); }

.text-input--mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  color: #818cf8;
}

.textarea {
  resize: vertical;
  min-height: 60px;
  line-height: 1.5;
}

select.text-input {
  cursor: pointer;
  appearance: auto;
}

/* Package upload */
.pkg-selected {
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: var(--radius-lg);
  background: rgba(99, 102, 241, 0.04);
  padding: 12px;
}

.pkg-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pkg-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: rgba(99, 102, 241, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #818cf8;
  flex-shrink: 0;
}

.pkg-meta {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pkg-name {
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pkg-size {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.pkg-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.btn-parse {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: 6px;
  border: none;
  background: #4f46e5;
  color: #fff;
  font-size: 12px;
  font-family: var(--font-family-base);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.btn-parse:hover { background: #4338ca; }

.state-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 5px 10px;
  border-radius: 6px;
  font-size: 12px;
}

.state-tag--parsing { color: #818cf8; }
.state-tag--done { background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.25); color: #34d399; }
.state-tag--error { background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.25); color: #f87171; }

.btn-remove {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-remove:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text-primary);
}

.pkg-hint {
  margin-top: 8px;
  font-size: 11px;
  color: var(--foreground-muted);
}

/* Dropzone */
.dropzone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 28px 16px;
  border: 2px dashed var(--color-border-input);
  border-radius: var(--radius-lg);
  background: rgba(15, 23, 46, 0.4);
  cursor: pointer;
  transition: border-color var(--transition-fast), background var(--transition-fast);
  text-align: center;
}

.dropzone:hover,
.dropzone.dragging {
  border-color: var(--accent-primary);
  background: rgba(59, 130, 246, 0.03);
}

.dz-icon { color: var(--foreground-muted); margin-bottom: 8px; }

.dropzone.dragging .dz-icon { color: #818cf8; }

.dz-text {
  font-size: var(--font-size-base);
  color: var(--foreground-secondary);
}

.dz-link { color: #818cf8; text-decoration: underline; text-underline-offset: 2px; }

.dz-formats {
  margin-top: 4px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

/* Footer */
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

.footer-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-xs);
  color: #34d399;
}

.footer-btns {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 18px;
  border: none;
  border-radius: var(--radius-button);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  font-family: var(--font-family-base);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-primary {
  background: var(--accent-primary);
  color: #fff;
}

.btn-primary:hover:not(:disabled) { background: var(--color-accent-dark); }

.btn-ghost {
  background: rgba(135, 148, 173, 0.08);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-input);
}

.btn-ghost:hover { background: rgba(135, 148, 173, 0.14); color: var(--color-text-primary); }

/* Animations */
.spin { animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

.modal-enter-active,
.modal-leave-active { transition: opacity 0.2s ease; }
.modal-enter-from,
.modal-leave-to { opacity: 0; }
</style>
