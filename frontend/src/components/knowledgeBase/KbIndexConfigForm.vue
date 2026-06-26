<script setup lang="ts">
import { ref, computed, onMounted, watchEffect, reactive } from 'vue'
import {
  Scissors, Sparkle, Hash, Network, Target,
} from 'lucide-vue-next'
import type { IndexConfig, SparseAlgo } from '@/types/knowledgeBase'
import {
  CHUNK_STRATEGY_OPTIONS,
  RERANKER_MODEL_OPTIONS,
} from '@/types/knowledgeBase'
import {
  fetchAvailableProviders,
  type AvailableProvider,
} from '@/services/knowledgeBaseApi'

const props = defineProps<{
  modelValue: IndexConfig
}>()

const emit = defineEmits<{
  'update:modelValue': [config: IndexConfig]
}>()

let draft = reactive<IndexConfig>({ ...props.modelValue })

watchEffect(() => {
  Object.assign(draft, props.modelValue)
})

function set<K extends keyof IndexConfig>(key: K, value: IndexConfig[K]) {
  ;(draft as Record<string, unknown>)[key] = value
  emit('update:modelValue', { ...draft })
}

// ── embedding 提供商 + 模型 ──
const embProviders = ref<AvailableProvider[]>([])
const embProviderId = ref('')
const embProviderModels = computed(() => {
  if (!embProviderId.value) return []
  const p = embProviders.value.find(x => x.id === embProviderId.value)
  return p?.models || []
})

// ── LLM 提供商 + 模型 ──
const llmProviders = ref<AvailableProvider[]>([])
const llmProviderId = ref('')
const llmProviderModels = computed(() => {
  if (!llmProviderId.value) return []
  const p = llmProviders.value.find(x => x.id === llmProviderId.value)
  return p?.models || []
})

onMounted(async () => {
  try {
    const [ep, lp] = await Promise.all([
      fetchAvailableProviders('embedding'),
      fetchAvailableProviders('llm'),
    ])
    embProviders.value = ep
    llmProviders.value = lp

    // 根据当前 draft 中的模型名反查 provider
    if (draft.embeddingModel) {
      for (const p of ep) {
        if (p.models.some(m => m.name === draft.embeddingModel)) {
          embProviderId.value = p.id
          break
        }
      }
    }
    if (!embProviderId.value && ep.length > 0) {
      embProviderId.value = ep[0].id
    }

    if (draft.entityModel) {
      for (const p of lp) {
        if (p.models.some(m => m.name === draft.entityModel)) {
          llmProviderId.value = p.id
          break
        }
      }
    }
    if (!llmProviderId.value && lp.length > 0) {
      llmProviderId.value = lp[0].id
    }
  } catch {
    /* ignore */
  }
})

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
    set('embeddingModel', p.models[0].name)
    set('embeddingDim', inferDim(p.models[0].name, p.models[0].display_name))
  }
}

function onEmbModelChange(name: string) {
  set('embeddingModel', name)
  const p = embProviders.value.find(x => x.id === embProviderId.value)
  const m = p?.models.find(x => x.name === name)
  if (m) set('embeddingDim', inferDim(m.name, m.display_name))
}

function onLlmProviderChange(pid: string) {
  llmProviderId.value = pid
  const p = llmProviders.value.find(x => x.id === pid)
  if (p && p.models.length > 0) {
    set('entityModel', p.models[0].name)
  }
}
</script>

<template>
  <div class="index-config-form">
    <!-- 文档切片 -->
    <div class="section-card">
      <h3 class="section-title">
        <span class="section-icon icon-cyan"><Scissors :size="16" /></span>文档切片
      </h3>

      <div class="field">
        <label class="field-label">切片算法</label>
        <el-select :model-value="draft.chunkStrategy" style="width: 100%" popper-class="config-select-popper" @update:model-value="(v: string) => set('chunkStrategy', v as IndexConfig['chunkStrategy'])">
          <el-option
            v-for="s in CHUNK_STRATEGY_OPTIONS"
            :key="s.value"
            :label="s.label"
            :value="s.value"
          >
            <div class="select-option-with-desc">
              <span>{{ s.label }}</span>
              <span class="select-option-desc">{{ s.desc }}</span>
            </div>
          </el-option>
        </el-select>
      </div>

      <div class="field-row">
        <div class="field flex-1">
          <label class="field-label">分片大小: {{ draft.chunkSize }} tokens</label>
          <el-slider
            :model-value="draft.chunkSize"
            :min="128" :max="2048" :step="64"
            @update:model-value="(v: number) => set('chunkSize', v)"
          />
        </div>
        <div class="field flex-1">
          <label class="field-label">重叠: {{ draft.chunkOverlap }} tokens</label>
          <el-slider
            :model-value="draft.chunkOverlap"
            :min="0" :max="512" :step="16"
            @update:model-value="(v: number) => set('chunkOverlap', v)"
          />
        </div>
      </div>
    </div>

    <!-- Embedding -->
    <div class="section-card">
      <h3 class="section-title">
        <span class="section-icon icon-purple"><Sparkle :size="16" /></span>向量化 (Embedding)
      </h3>
      <div class="field-row">
        <div class="field flex-1">
          <label class="field-label">Embedding 提供商</label>
          <el-select
            :model-value="embProviderId"
            @update:model-value="onEmbProviderChange"
            style="width: 100%"
            popper-class="config-select-popper"
          >
            <el-option v-for="p in embProviders" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </div>
        <div class="field flex-1">
          <label class="field-label">Embedding 模型</label>
          <el-select
            :model-value="draft.embeddingModel"
            @update:model-value="onEmbModelChange"
            style="width: 100%"
            popper-class="config-select-popper"
          >
            <el-option v-for="m in embProviderModels" :key="m.id" :label="m.display_name || m.name" :value="m.name" />
          </el-select>
        </div>
      </div>
    </div>

    <!-- BM25 -->
    <div class="section-card">
      <h3 class="section-title">
        <span class="section-icon icon-amber"><Hash :size="16" /></span>稀疏检索 (BM25)
      </h3>
      <div class="field">
        <label class="field-label">算法</label>
        <el-select
          :model-value="draft.sparseAlgo"
          @update:model-value="(v: SparseAlgo) => set('sparseAlgo', v)"
          style="width: 100%"
          popper-class="config-select-popper"
        >
          <el-option label="BM25 (经典)" value="bm25" />
          <el-option label="BM25+ (改进版)" value="bm25_plus" />
          <el-option label="TF-IDF" value="tf_idf" />
          <el-option label="不启用" value="none" />
        </el-select>
      </div>
      <div v-if="draft.sparseAlgo !== 'none'" class="field-row">
        <div class="field flex-1">
          <label class="field-label">k1: {{ draft.bm25K1.toFixed(2) }} (词频饱和)</label>
          <el-slider
            :model-value="draft.bm25K1"
            :min="0.5" :max="3.0" :step="0.1"
            @update:model-value="(v: number) => set('bm25K1', v)"
          />
        </div>
        <div class="field flex-1">
          <label class="field-label">b: {{ draft.bm25B.toFixed(2) }} (长度归一)</label>
          <el-slider
            :model-value="draft.bm25B"
            :min="0" :max="1" :step="0.05"
            @update:model-value="(v: number) => set('bm25B', v)"
          />
        </div>
      </div>
    </div>

    <!-- 知识图谱 -->
    <div class="section-card">
      <h3 class="section-title">
        <span class="section-icon icon-green"><Network :size="16" /></span>知识图谱抽取
      </h3>
      <div class="toggle-row">
        <div class="toggle-info">
          <div class="toggle-label">启用知识图谱</div>
          <div class="toggle-desc">使用 LLM 从分片中抽取实体与关系</div>
        </div>
        <el-switch
          :model-value="draft.enableGraph"
          @update:model-value="(v: boolean) => set('enableGraph', v)"
        />
      </div>
      <div v-if="draft.enableGraph" class="field-row">
        <div class="field flex-1">
          <label class="field-label">LLM 提供商</label>
          <el-select
            :model-value="llmProviderId"
            @update:model-value="onLlmProviderChange"
            style="width: 100%"
            popper-class="config-select-popper"
          >
            <el-option v-for="p in llmProviders" :key="p.id" :label="p.name" :value="p.id" />
          </el-select>
        </div>
        <div class="field flex-1">
          <label class="field-label">抽取模型</label>
          <el-select
            :model-value="draft.entityModel"
            @update:model-value="(v: string) => set('entityModel', v)"
            style="width: 100%"
            popper-class="config-select-popper"
          >
            <el-option v-for="m in llmProviderModels" :key="m.id" :label="m.display_name || m.name" :value="m.name" />
          </el-select>
        </div>
      </div>
    </div>

    <!-- 检索与重排 -->
    <div class="section-card">
      <h3 class="section-title">
        <span class="section-icon icon-rose"><Target :size="16" /></span>检索与重排
      </h3>
      <div class="field-row">
        <div class="field flex-1">
          <label class="field-label">Top-K: {{ draft.topK }}</label>
          <el-slider
            :model-value="draft.topK"
            :min="1" :max="50" :step="1"
            @update:model-value="(v: number) => set('topK', v)"
          />
        </div>
        <div class="field flex-1">
          <label class="field-label">混合权重 &alpha;: {{ draft.hybridAlpha.toFixed(2) }} (向量&harr;BM25)</label>
          <el-slider
            :model-value="draft.hybridAlpha"
            :min="0" :max="1" :step="0.05"
            @update:model-value="(v: number) => set('hybridAlpha', v)"
          />
        </div>
      </div>
      <div class="toggle-row">
        <div class="toggle-info">
          <div class="toggle-label">启用 Reranker</div>
          <div class="toggle-desc">对召回结果进行二次精排</div>
        </div>
        <el-switch
          :model-value="draft.enableReranker"
          @update:model-value="(v: boolean) => set('enableReranker', v)"
        />
      </div>
      <div v-if="draft.enableReranker" class="field">
        <label class="field-label">Reranker 模型</label>
        <el-select
          :model-value="draft.rerankerModel"
          @update:model-value="(v: string) => set('rerankerModel', v)"
          style="width: 100%"
          popper-class="config-select-popper"
        >
          <el-option v-for="m in RERANKER_MODEL_OPTIONS" :key="m" :label="m" :value="m" />
        </el-select>
      </div>
    </div>
  </div>
</template>

<style scoped>
.index-config-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Section card */
.section-card {
  padding: 16px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0;
}

.section-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* Field */
.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-row {
  display: flex;
  gap: 16px;
}

.flex-1 { flex: 1; }

.field-label {
  font-size: var(--font-size-xs);
  color: var(--foreground-secondary);
  line-height: 1.4;
}

/* Toggle */
.toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  margin-top: 4px;
}

.toggle-label {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
}

.toggle-desc {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin-top: 2px;
}

/* Select option with description */
.select-option-with-desc {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.select-option-desc {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

/* Colors */
.icon-cyan { color: #67e8f9; }
.icon-purple { color: #c4b5fd; }
.icon-amber { color: #fcd34d; }
.icon-green { color: #6ee7b7; }
.icon-rose { color: #fda4af; }
</style>

<!-- 全局样式覆盖: 索引配置表单内的 Element Plus 组件 -->
<style>
.index-config-form .el-select .el-input__wrapper {
  background: var(--color-bg-input) !important;
  border: 1px solid var(--border-medium) !important;
  border-radius: var(--radius-input) !important;
  box-shadow: none !important;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast) !important;
  padding-left: 12px !important;
  padding-right: 12px !important;
}

.index-config-form .el-select .el-input__wrapper:hover {
  border-color: rgba(255, 255, 255, 0.18) !important;
}

.index-config-form .el-select .el-input__wrapper.is-focus {
  border-color: var(--color-accent) !important;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

.index-config-form .el-select .el-input__inner {
  color: var(--foreground-primary) !important;
  font-size: var(--font-size-sm) !important;
}

.index-config-form .el-select .el-input__inner::placeholder {
  color: var(--foreground-muted) !important;
}

/* Select 下拉面板 */
.config-select-popper {
  background: var(--color-bg-input) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: var(--radius-input) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.55) !important;
  padding: 4px !important;
}

.config-select-popper .el-select-dropdown__item {
  color: var(--foreground-primary) !important;
  padding: 8px 12px !important;
  font-size: var(--font-size-sm) !important;
  border-radius: 6px !important;
  margin: 2px 0 !important;
  transition: background var(--transition-fast) !important;
}

.config-select-popper .el-select-dropdown__item.is-hovering,
.config-select-popper .el-select-dropdown__item:hover {
  background: rgba(59, 130, 246, 0.12) !important;
}

.config-select-popper .el-select-dropdown__item.is-selected {
  color: #93c5fd !important;
  font-weight: var(--font-weight-medium) !important;
  background: rgba(59, 130, 246, 0.08) !important;
}

/* Slider 轨道 */
.index-config-form .el-slider__runway {
  background: rgba(255, 255, 255, 0.08) !important;
}

.index-config-form .el-slider__bar {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
}

.index-config-form .el-slider__button {
  border-color: #3b82f6 !important;
  background: #fff !important;
}

/* Switch */
.index-config-form .el-switch.is-checked .el-switch__core {
  background: #3b82f6 !important;
  border-color: #3b82f6 !important;
}
</style>
