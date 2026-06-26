<script setup lang="ts">
import { ref, reactive, watchEffect } from 'vue'
import { Save, CheckCircle2, Cpu } from 'lucide-vue-next'
import type { IndexConfig } from '@/types/knowledgeBase'
import KbConfigSummary from './KbConfigSummary.vue'
import KbIndexConfigForm from './KbIndexConfigForm.vue'

const props = defineProps<{
  config: IndexConfig
}>()

const emit = defineEmits<{
  save: [config: IndexConfig]
  saveAndReindex: [config: IndexConfig]
}>()

const draft = reactive<IndexConfig>({ ...props.config })
const saved = ref(false)

watchEffect(() => {
  Object.assign(draft, props.config)
})

function handleSave() {
  draft.relationModel = draft.entityModel
  emit('save', { ...draft })
  saved.value = true
  setTimeout(() => (saved.value = false), 1800)
}

function handleSaveAndReindex() {
  draft.relationModel = draft.entityModel
  emit('saveAndReindex', { ...draft })
  saved.value = true
  setTimeout(() => (saved.value = false), 1800)
}
</script>

<template>
  <div class="config-tab">
    <div class="config-layout">
      <!-- 配置表单 -->
      <div class="config-main">
        <KbIndexConfigForm v-model="draft" />
      </div>

      <!-- 预览面板 -->
      <div class="config-side">
        <div class="preview-panel">
          <h3 class="preview-title">
            <span class="preview-icon"><Cpu :size="16" /></span>配置预览
          </h3>
          <KbConfigSummary :config="draft" />
          <div class="divider" />
          <div class="preview-actions">
            <button class="btn-save" @click="handleSave">
              <Save :size="16" class="btn-icon" />保存配置
            </button>
            <button class="btn-reindex" @click="handleSaveAndReindex">
              重新索引
            </button>
            <div v-if="saved" class="save-feedback">
              <CheckCircle2 :size="14" />已保存
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.config-tab {
  width: 100%;
  height: 100%;
}

.config-layout {
  display: grid;
  grid-template-columns: 8fr 4fr;
  gap: 16px;
  height: 100%;
}

.config-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  min-height: 0;
  padding-right: 4px;
}

/* Preview panel */
.config-side {
  position: relative;
}

.preview-panel {
  position: sticky;
  top: 0;
  padding: 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0;
}

.preview-icon {
  display: flex;
  align-items: center;
  color: #93c5fd;
}

.divider {
  height: 1px;
  background: var(--border-subtle);
}

.preview-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.btn-save {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 10px 16px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border: none;
  border-radius: var(--radius-input);
  color: #fff;
  font-size: var(--font-size-base);
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-save:hover {
  opacity: 0.9;
}

.btn-reindex {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px 16px;
  background: rgba(59, 130, 246, 0.12);
  border: 1px solid rgba(59, 130, 246, 0.25);
  border-radius: var(--radius-input);
  color: #93c5fd;
  font-size: var(--font-size-base);
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-reindex:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.4);
  color: #bfdbfe;
}

.save-feedback {
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: center;
  font-size: var(--font-size-xs);
  color: #6ee7b7;
}

.btn-icon {
  margin-right: 2px;
}
</style>
