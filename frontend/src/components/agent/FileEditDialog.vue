<script setup lang="ts">
import { ref, watch } from 'vue'
import { X, FileText } from 'lucide-vue-next'

const props = defineProps<{
  visible: boolean
  filename: string
  description: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', filename: string, description: string): void
}>()

const editName = ref('')
const editDesc = ref('')

watch(
  () => props.visible,
  (val) => {
    if (val) {
      editName.value = props.filename
      editDesc.value = props.description || ''
    }
  },
)

function handleSubmit() {
  if (!editName.value.trim()) return
  emit('save', editName.value.trim(), editDesc.value.trim())
}

function handleClose() {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="dialog-overlay" @click.self="handleClose">
        <div class="dialog-modal">
          <div class="dialog-header">
            <div class="header-left">
              <div class="dialog-icon">
                <FileText :size="18" style="color: #eab308" />
              </div>
              <div>
                <h3 class="dialog-title">编辑文件</h3>
                <p class="dialog-desc">修改文件名和描述</p>
              </div>
            </div>
            <button class="modal-close" @click="handleClose">
              <X :size="18" />
            </button>
          </div>

          <form class="dialog-body" @submit.prevent="handleSubmit">
            <div class="form-field">
              <label class="field-label">文件名称</label>
              <input
                v-model="editName"
                type="text"
                class="text-input"
                placeholder="例如: config.yaml"
                autofocus
              />
            </div>
            <div class="form-field">
              <label class="field-label">描述</label>
              <textarea
                v-model="editDesc"
                class="text-input textarea"
                :rows="3"
                placeholder="描述此文件的用途..."
              />
            </div>

            <div class="dialog-footer">
              <button type="button" class="btn btn-ghost" @click="handleClose">取消</button>
              <button type="submit" class="btn btn-primary" :disabled="!editName.trim()">
                保存
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-overlay);
  z-index: 9999;
}

.dialog-modal {
  width: 440px;
  max-width: 92vw;
  display: flex;
  flex-direction: column;
  background: var(--color-modal-bg);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-card);
  box-shadow: 0px 12px 60px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

.dialog-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.dialog-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-lg);
  background: rgba(234, 179, 8, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dialog-title {
  font-size: 17px;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.dialog-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 4px 0 0;
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
  transition: all var(--transition-fast);
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text-primary);
}

.dialog-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-label);
}

.text-input {
  width: 100%;
  padding: 10px 14px;
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

.text-input::placeholder {
  color: var(--color-text-muted);
}

.text-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0px 0px 0px 2px rgba(59, 130, 246, 0.12);
}

.textarea {
  resize: vertical;
  min-height: 60px;
  line-height: 1.5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  border: none;
  border-radius: var(--radius-button);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  font-family: var(--font-family-base);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-accent);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-dark);
}

.btn-ghost {
  background: rgba(135, 148, 173, 0.08);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-input);
}

.btn-ghost:hover {
  background: rgba(135, 148, 173, 0.14);
  color: var(--color-text-primary);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-normal);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
