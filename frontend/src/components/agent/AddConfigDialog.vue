<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { X, Zap, Sparkles, Clock, FileText, Users } from 'lucide-vue-next'
import type { ConfigType } from '@/types/agent'
import { CONFIG_TYPE_MAP } from '@/types/agent'

const props = defineProps<{
  visible: boolean
  type: ConfigType
  agentName: string
  agentType: 'main' | 'sub'
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'add', type: ConfigType, value: string): void
}>()

const nameValue = ref('')
const descValue = ref('')

const config = computed(() => CONFIG_TYPE_MAP[props.type])

const iconComponent = computed(() => {
  switch (props.type) {
    case 'tool': return Zap
    case 'skill': return Sparkles
    case 'file': return FileText
    case 'prompt': return Clock
    case 'subagent': return Users
  }
})

const placeholders = computed(() => {
  switch (props.type) {
    case 'tool': return { name: '例如: web_search, file_reader', desc: '描述此工具的功能和用途...' }
    case 'skill': return { name: '例如: code_analysis, debugging', desc: '描述此技能的能力和应用场景...' }
    case 'file': return { name: '例如: config.yaml, data.json', desc: '描述此文件的用途和内容...' }
    case 'prompt': return { name: '例如: 每天执行一次, 每小时检查', desc: '输入 Cron 表达式和执行任务...' }
    case 'subagent': return { name: '例如: 数据处理子智能体', desc: '描述此子智能体的职责和功能...' }
  }
})

function handleSubmit() {
  if (!nameValue.value.trim()) return
  emit('add', props.type, nameValue.value.trim())
  resetForm()
}

function handleClose() {
  resetForm()
  emit('close')
}

function resetForm() {
  nameValue.value = ''
  descValue.value = ''
}

watch(
  () => props.visible,
  (val) => {
    if (val) resetForm()
  },
)
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="dialog-overlay" @click.self="handleClose">
        <div class="dialog-modal">
          <!-- Header -->
          <div class="dialog-header">
            <div class="header-left">
              <div class="dialog-icon" :style="{ background: `${config.color}18` }">
                <component :is="iconComponent" :size="18" :style="{ color: config.color }" />
              </div>
              <div>
                <h3 class="dialog-title">添加{{ config.label }}</h3>
                <p class="dialog-desc">
                  为 <span class="highlight">"{{ agentName }}"</span>
                  {{ agentType === 'main' ? ' (主智能体)' : ' (子智能体)' }}
                  添加新的{{ config.label }}
                </p>
                <p
                  v-if="type === 'subagent' && agentType === 'sub'"
                  class="dialog-warning"
                >
                  注意：子智能体不能添加子智能体，将为主智能体添加
                </p>
              </div>
            </div>
            <button class="modal-close" @click="handleClose">
              <X :size="18" />
            </button>
          </div>

          <!-- Body -->
          <form class="dialog-body" @submit.prevent="handleSubmit">
            <div class="form-field">
              <label class="field-label">{{ config.label }}名称</label>
              <input
                v-model="nameValue"
                type="text"
                class="text-input"
                :placeholder="placeholders.name"
                autofocus
              />
            </div>
            <div class="form-field">
              <label class="field-label">描述 (可选)</label>
              <textarea
                v-model="descValue"
                class="text-input textarea"
                :rows="3"
                :placeholder="placeholders.desc"
              />
            </div>

            <!-- Footer (inside form) -->
            <div class="dialog-footer">
              <button type="button" class="btn btn-ghost" @click="handleClose">取消</button>
              <button
                type="submit"
                class="btn btn-primary"
                :disabled="!nameValue.trim()"
              >
                添加{{ config.label }}
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
  width: 480px;
  max-width: 92vw;
  display: flex;
  flex-direction: column;
  background: var(--color-modal-bg);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-card);
  box-shadow: 0px 12px 60px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

/* ---- Header ---- */
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

.highlight {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.dialog-warning {
  font-size: var(--font-size-xs);
  color: #f59e0b;
  margin: 6px 0 0;
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

/* ---- Body ---- */
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

/* ---- Footer ---- */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

/* ---- Buttons ---- */
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

/* ---- Transition ---- */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-normal);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
