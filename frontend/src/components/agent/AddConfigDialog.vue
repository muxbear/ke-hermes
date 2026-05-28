<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Zap, Sparkles, Clock, FileText, Users } from 'lucide-vue-next'
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

// Local v-model for el-dialog, synced with parent prop
const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => { if (!val) handleClose() },
})

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

// Reset form when dialog opens
watch(
  () => props.visible,
  (val) => {
    if (val) resetForm()
  },
)
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    width="480px"
    :close-on-click-modal="false"
    append-to-body
  >
    <template #header>
      <div class="dialog-header">
        <div class="dialog-icon" :class="config.bgClass">
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
    </template>

    <form class="dialog-form" @submit.prevent="handleSubmit">
      <div class="form-field">
        <label class="field-label">{{ config.label }}名称</label>
        <el-input
          v-model="nameValue"
          :placeholder="placeholders.name"
          autofocus
        />
      </div>
      <div class="form-field">
        <label class="field-label">描述 (可选)</label>
        <el-input
          v-model="descValue"
          type="textarea"
          :rows="3"
          :placeholder="placeholders.desc"
        />
      </div>
    </form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :disabled="!nameValue.trim()" native-type="submit">
        添加{{ config.label }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.dialog-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
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

.config--blue { background: rgba(59, 130, 246, 0.1); }
.config--purple { background: rgba(139, 92, 246, 0.1); }
.config--green { background: rgba(34, 197, 94, 0.1); }
.config--orange { background: rgba(249, 115, 22, 0.1); }
.config--yellow { background: rgba(234, 179, 8, 0.1); }

.dialog-title {
  font-size: 16px;
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0;
}

.dialog-desc {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  margin: 4px 0 0;
}

.highlight {
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.dialog-warning {
  font-size: var(--font-size-xs);
  color: #f59e0b;
  margin: 6px 0 0;
}

.dialog-form {
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
  color: var(--foreground-primary);
}

/* Element Plus dialog overrides */
:deep(.el-dialog) {
  background: var(--surface-card) !important;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card) !important;
}

:deep(.el-dialog__header) {
  padding: 20px 24px 0 !important;
  margin-right: 0 !important;
}

:deep(.el-dialog__body) {
  padding: 16px 24px !important;
}

:deep(.el-dialog__footer) {
  padding: 0 24px 20px !important;
}

:deep(.el-input__wrapper) {
  background: var(--color-bg-input) !important;
  border-color: var(--color-border-input) !important;
}

:deep(.el-textarea__inner) {
  background: var(--color-bg-input) !important;
  border-color: var(--color-border-input) !important;
  color: var(--foreground-primary) !important;
}

:deep(.el-input__inner) {
  color: var(--foreground-primary) !important;
}
</style>
