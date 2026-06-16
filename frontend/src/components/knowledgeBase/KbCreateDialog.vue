<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { Plus, Settings2 } from 'lucide-vue-next'
import type { IndexConfig, SparseAlgo } from '@/types/knowledgeBase'
import { CHUNK_STRATEGY_OPTIONS } from '@/types/knowledgeBase'
import {
  fetchAvailableProviders,
  fetchAvailableModels,
  type AvailableProvider,
  type AvailableModel,
} from '@/services/knowledgeBaseApi'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  close: []
  create: [data: { name: string; description: string; tags: string[]; config: IndexConfig }]
}>()

const defaultConfig: IndexConfig = {
  chunkStrategy: 'recursive', chunkSize: 512, chunkOverlap: 64,
  embeddingModel: '', embeddingDim: 1024,
  sparseAlgo: 'bm25', bm25K1: 1.5, bm25B: 0.75,
  entityModel: '', relationModel: '', enableGraph: true,
  rerankerModel: 'bge-reranker-v2-m3', enableReranker: true,
  topK: 10, hybridAlpha: 0.5,
}

const name = ref('')
const description = ref('')
const tagsInput = ref('')
const config = ref<IndexConfig>({ ...defaultConfig })
const dialogVisible = ref(false)

// ── embedding 提供商 + 模型 ──
const embProviders = ref<AvailableProvider[]>([])
const embProviderId = ref('')
const embModels = ref<AvailableModel[]>([])

const embProviderModels = computed(() => {
  if (!embProviderId.value) return []
  const p = embProviders.value.find(x => x.id === embProviderId.value)
  return p?.models || []
})

// ── LLM 提供商 + 模型 ──
const llmProviders = ref<AvailableProvider[]>([])
const llmProviderId = ref('')
const llmModels = ref<AvailableModel[]>([])

const llmProviderModels = computed(() => {
  if (!llmProviderId.value) return []
  const p = llmProviders.value.find(x => x.id === llmProviderId.value)
  return p?.models || []
})

watch(() => props.visible, async (v) => {
  dialogVisible.value = v
  if (v) {
    reset()
    await loadProviders()
  }
})

async function loadProviders() {
  try {
    const [ep, lp] = await Promise.all([
      fetchAvailableProviders('embedding'),
      fetchAvailableProviders('llm'),
    ])
    embProviders.value = ep
    llmProviders.value = lp

    // 默认选中第一个提供商
    if (ep.length > 0) {
      embProviderId.value = ep[0].id
      if (ep[0].models.length > 0) {
        config.value.embeddingModel = ep[0].models[0].name
        // embedding dim 来自模型名称推断
        const m = ep[0].models[0]
        config.value.embeddingDim = inferDim(m.name, m.display_name)
      }
    }
    if (lp.length > 0) {
      llmProviderId.value = lp[0].id
      if (lp[0].models.length > 0 && !config.value.entityModel) {
        config.value.entityModel = lp[0].models[0].name
      }
    }
  } catch {
    embProviders.value = []
    llmProviders.value = []
  }
}

function inferDim(name: string, display: string): number {
  const combined = `${name} ${display}`.toLowerCase()
  if (combined.includes('4096')) return 4096
  if (combined.includes('3072')) return 3072
  if (combined.includes('1536')) return 1536
  if (combined.includes('1024')) return 1024
  if (combined.includes('768')) return 768
  if (combined.includes('512')) return 512
  return 1024
}

function onEmbProviderChange(pid: string) {
  embProviderId.value = pid
  const p = embProviders.value.find(x => x.id === pid)
  if (p && p.models.length > 0) {
    config.value.embeddingModel = p.models[0].name
    config.value.embeddingDim = inferDim(p.models[0].name, p.models[0].display_name)
  }
}

function onEmbModelChange(name: string) {
  config.value.embeddingModel = name
  const p = embProviders.value.find(x => x.id === embProviderId.value)
  const m = p?.models.find(x => x.name === name)
  if (m) config.value.embeddingDim = inferDim(m.name, m.display_name)
}

function onLlmProviderChange(pid: string) {
  llmProviderId.value = pid
  const p = llmProviders.value.find(x => x.id === pid)
  if (p && p.models.length > 0) {
    config.value.entityModel = p.models[0].name
  }
}

function reset() {
  name.value = ''
  description.value = ''
  tagsInput.value = ''
  config.value = { ...defaultConfig }
  embProviderId.value = ''
  llmProviderId.value = ''
}

function handleClose() {
  dialogVisible.value = false
  emit('close')
}

function handleCreate() {
  if (!name.value.trim()) return
  config.value.relationModel = config.value.entityModel
  emit('create', {
    name: name.value.trim(),
    description: description.value.trim(),
    tags: tagsInput.value.split(',').map(t => t.trim()).filter(Boolean),
    config: config.value,
  })
  dialogVisible.value = false
}
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    width="680px"
    :close-on-click-modal="false"
    @close="handleClose"
    class="create-kb-dialog"
    destroy-on-close
  >
    <template #header>
      <div class="dialog-header">
        <h2 class="dialog-title">新建知识库</h2>
        <p class="dialog-desc">创建后可在「索引配置」中随时调整</p>
      </div>
    </template>

    <div class="dialog-body">
      <!-- 名称 + 标签 -->
      <div class="form-row-2">
        <div class="field">
          <label class="field-label">名称 *</label>
          <input v-model="name" type="text" class="field-input" placeholder="例: 产品技术文档" maxlength="50" />
        </div>
        <div class="field">
          <label class="field-label">标签（逗号分隔）</label>
          <input v-model="tagsInput" type="text" class="field-input" placeholder="产品, 技术" maxlength="100" />
        </div>
      </div>

      <!-- 描述 -->
      <div class="field">
        <label class="field-label">描述</label>
        <textarea v-model="description" class="field-textarea" rows="2" placeholder="简要描述知识库的内容与用途" maxlength="200"></textarea>
      </div>

      <div class="divider" />

      <!-- 初始索引方案 -->
      <h4 class="section-title"><Settings2 :size="16" class="section-icon" />初始索引方案</h4>

      <div class="form-row-2">
        <div class="field">
          <label class="field-label">切片算法</label>
          <el-select v-model="config.chunkStrategy" style="width: 100%" popper-class="dialog-select-popper">
            <el-option v-for="s in CHUNK_STRATEGY_OPTIONS" :key="s.value" :label="s.label" :value="s.value">
              <div class="opt-with-desc">
                <span>{{ s.label }}</span>
                <span class="opt-desc">{{ s.desc }}</span>
              </div>
            </el-option>
          </el-select>
        </div>
        <div class="field">
          <label class="field-label">稀疏检索</label>
          <el-select v-model="config.sparseAlgo" style="width: 100%" popper-class="dialog-select-popper">
            <el-option label="BM25" value="bm25" />
            <el-option label="BM25+" value="bm25_plus" />
            <el-option label="TF-IDF" value="tf_idf" />
            <el-option label="不启用" value="none" />
          </el-select>
        </div>
      </div>

      <!-- Embedding —— 提供商 + 模型 -->
      <div class="form-row-2">
        <div class="field">
          <label class="field-label">Embedding 提供商</label>
          <el-select :model-value="embProviderId" @update:model-value="onEmbProviderChange" style="width: 100%" popper-class="dialog-select-popper">
            <el-option v-for="p in embProviders" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </div>
        <div class="field">
          <label class="field-label">Embedding 模型</label>
          <el-select :model-value="config.embeddingModel" @update:model-value="onEmbModelChange" style="width: 100%" popper-class="dialog-select-popper">
            <el-option v-for="m in embProviderModels" :key="m.id" :label="`${m.display_name || m.name}`" :value="m.name" />
          </el-select>
        </div>
      </div>

      <!-- 实体抽取 —— 提供商 + 模型 -->
      <div class="form-row-2">
        <div class="field">
          <label class="field-label">LLM 提供商</label>
          <el-select :model-value="llmProviderId" @update:model-value="onLlmProviderChange" style="width: 100%" popper-class="dialog-select-popper">
            <el-option v-for="p in llmProviders" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </div>
        <div class="field">
          <label class="field-label">抽取模型</label>
          <el-select v-model="config.entityModel" style="width: 100%" popper-class="dialog-select-popper">
            <el-option v-for="m in llmProviderModels" :key="m.id" :label="m.display_name || m.name" :value="m.name" />
          </el-select>
        </div>
      </div>

      <!-- 知识图谱开关 -->
      <div class="graph-row">
        <el-switch v-model="config.enableGraph" />
        <span class="graph-label">启用知识图谱</span>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <button class="btn-cancel" @click="handleClose">取消</button>
        <button class="btn-create" :disabled="!name.trim()" @click="handleCreate">
          <Plus :size="16" />创建
        </button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
/* ─── Dialog header ─── */
.dialog-header { padding: 0; }
.dialog-title { font-size: 17px; font-weight: var(--font-weight-semibold); color: var(--foreground-primary); margin: 0; }
.dialog-desc { font-size: var(--font-size-sm); color: var(--foreground-secondary); margin: 6px 0 0; }

/* ─── Dialog body ─── */
.dialog-body { display: flex; flex-direction: column; gap: 14px; max-height: 60vh; overflow-y: auto; padding-right: 4px; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-size: var(--font-size-xs); color: var(--foreground-primary); opacity: 0.85; }
.field-input { height: 36px; padding: 0 12px; background: rgba(15, 23, 46, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: var(--foreground-primary); font-size: var(--font-size-base); font-family: inherit; outline: none; transition: border-color 0.2s; }
.field-input::placeholder { color: var(--foreground-muted); }
.field-input:focus { border-color: rgba(59, 130, 246, 0.45); }
.field-textarea { padding: 10px 12px; background: rgba(15, 23, 46, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: var(--foreground-primary); font-size: var(--font-size-base); font-family: inherit; outline: none; resize: vertical; transition: border-color 0.2s; }
.field-textarea::placeholder { color: var(--foreground-muted); }
.field-textarea:focus { border-color: rgba(59, 130, 246, 0.45); }
.divider { height: 1px; background: rgba(255, 255, 255, 0.06); margin: 4px 0; }
.section-title { display: flex; align-items: center; gap: 8px; font-size: var(--font-size-sm); font-weight: var(--font-weight-semibold); color: var(--foreground-primary); margin: 0; }
.section-icon { color: #93c5fd; }
.graph-row { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: rgba(0, 0, 0, 0.2); border: 1px solid var(--border-subtle); border-radius: 10px; }
.graph-label { font-size: var(--font-size-sm); color: var(--foreground-primary); }
.opt-with-desc { display: flex; flex-direction: column; gap: 2px; }
.opt-desc { font-size: var(--font-size-xs); color: var(--foreground-muted); }

/* ─── Dialog footer ─── */
.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; }
.btn-cancel { display: inline-flex; align-items: center; justify-content: center; height: 38px; padding: 0 20px; background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; color: var(--foreground-primary); font-size: var(--font-size-base); font-family: inherit; cursor: pointer; transition: all 0.15s; }
.btn-cancel:hover { background: rgba(255, 255, 255, 0.08); border-color: rgba(255, 255, 255, 0.18); }
.btn-create { display: inline-flex; align-items: center; justify-content: center; gap: 6px; height: 38px; padding: 0 22px; background: linear-gradient(135deg, #3b82f6, #8b5cf6); border: none; border-radius: 10px; color: #fff; font-size: var(--font-size-base); font-family: inherit; cursor: pointer; transition: opacity 0.2s; }
.btn-create:hover { opacity: 0.9; }
.btn-create:disabled { opacity: 0.4; cursor: not-allowed; }
</style>

<style>
.create-kb-dialog { --el-dialog-bg-color: #0f172e; --el-dialog-border-color: rgba(255, 255, 255, 0.1); }
.create-kb-dialog .el-dialog { border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.1); }
.create-kb-dialog .el-dialog__header { padding: 24px 28px 0; }
.create-kb-dialog .el-dialog__body { padding: 20px 28px; }
.create-kb-dialog .el-dialog__footer { padding: 0 28px 24px; }

/* Select 触发器 */
.create-kb-dialog .el-select .el-input__wrapper {
  background: var(--color-bg-input) !important;
  border: 1px solid var(--border-medium) !important;
  border-radius: var(--radius-input) !important;
  box-shadow: none !important;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast) !important;
}
.create-kb-dialog .el-select .el-input__wrapper:hover {
  border-color: rgba(255, 255, 255, 0.18) !important;
}
.create-kb-dialog .el-select .el-input__wrapper.is-focus {
  border-color: var(--color-accent) !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}
.create-kb-dialog .el-select .el-input__inner {
  color: var(--foreground-primary) !important;
  font-size: var(--font-size-sm) !important;
}
.create-kb-dialog .el-select .el-input__inner::placeholder {
  color: var(--foreground-muted) !important;
}

/* Select 下拉面板 */
.dialog-select-popper {
  background: var(--color-bg-input) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: var(--radius-input) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.55) !important;
  padding: 4px !important;
}
.dialog-select-popper .el-select-dropdown__item {
  color: var(--foreground-primary) !important;
  padding: 8px 12px !important;
  font-size: var(--font-size-sm) !important;
  border-radius: 6px !important;
  margin: 2px 0 !important;
  transition: background var(--transition-fast) !important;
}
.dialog-select-popper .el-select-dropdown__item:hover {
  background: rgba(59, 130, 246, 0.12) !important;
}
.dialog-select-popper .el-select-dropdown__item.is-selected {
  color: #93c5fd !important;
  font-weight: var(--font-weight-medium) !important;
  background: rgba(59, 130, 246, 0.08) !important;
}

.create-kb-dialog .el-switch.is-checked .el-switch__core { background: #3b82f6 !important; border-color: #3b82f6 !important; }
</style>
