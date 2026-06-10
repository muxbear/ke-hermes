<script setup lang="ts">
import { ref, reactive, watchEffect } from 'vue'
import {
  Scissors, Sparkle, Hash, Network, Target, Cpu, Save, CheckCircle2,
} from 'lucide-vue-next'
import type { IndexConfig, SparseAlgo } from '@/types/knowledgeBase'
import {
  CHUNK_STRATEGY_OPTIONS,
  EMBEDDING_MODEL_OPTIONS,
  LLM_MODEL_OPTIONS,
  RERANKER_MODEL_OPTIONS,
} from '@/types/knowledgeBase'
import KbConfigSummary from './KbConfigSummary.vue'

const props = defineProps<{
  config: IndexConfig
}>()

const emit = defineEmits<{
  save: [config: IndexConfig]
}>()

const draft = reactive<IndexConfig>({ ...props.config })
const saved = ref(false)

watchEffect(() => {
  Object.assign(draft, props.config)
})

function set<K extends keyof IndexConfig>(key: K, value: IndexConfig[K]) {
  ;(draft as Record<string, unknown>)[key] = value
}

function onEmbeddingChange(v: string) {
  const m = EMBEDDING_MODEL_OPTIONS.find((x) => x.value === v)
  draft.embeddingModel = v
  if (m) draft.embeddingDim = m.dim
}

function handleSave() {
  emit('save', { ...draft })
  saved.value = true
  setTimeout(() => (saved.value = false), 1800)
}

function handleReset() {
  Object.assign(draft, props.config)
}
</script>

<template>
  <div class="config-tab">
    <div class="config-layout">
      <!-- 配置表单 -->
      <div class="config-main">
        <!-- 文档切片 -->
        <div class="section-card">
          <h3 class="section-title">
            <span class="section-icon icon-cyan"><Scissors :size="16" /></span>文档切片
          </h3>

          <div class="field">
            <label class="field-label">切片算法</label>
            <el-select v-model="draft.chunkStrategy" style="width: 100%" popper-class="config-select-popper">
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
          <div class="field">
            <label class="field-label">Embedding 模型</label>
            <el-select
              :model-value="draft.embeddingModel"
              @update:model-value="onEmbeddingChange"
              style="width: 100%"
              popper-class="config-select-popper"
            >
              <el-option
                v-for="m in EMBEDDING_MODEL_OPTIONS"
                :key="m.value"
                :label="`${m.label} · ${m.dim}d`"
                :value="m.value"
              />
            </el-select>
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
              <label class="field-label">实体抽取模型</label>
              <el-select
                :model-value="draft.entityModel"
                @update:model-value="(v: string) => set('entityModel', v)"
                style="width: 100%"
                popper-class="config-select-popper"
              >
                <el-option v-for="m in LLM_MODEL_OPTIONS" :key="m" :label="m" :value="m" />
              </el-select>
            </div>
            <div class="field flex-1">
              <label class="field-label">关系抽取模型</label>
              <el-select
                :model-value="draft.relationModel"
                @update:model-value="(v: string) => set('relationModel', v)"
                style="width: 100%"
                popper-class="config-select-popper"
              >
                <el-option v-for="m in LLM_MODEL_OPTIONS" :key="m" :label="m" :value="m" />
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
              <label class="field-label">混合权重 α: {{ draft.hybridAlpha.toFixed(2) }} (向量↔BM25)</label>
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
              <Save :size="16" class="btn-icon" />保存并重新索引
            </button>
            <div v-if="saved" class="save-feedback">
              <CheckCircle2 :size="14" />已保存
            </div>
            <button class="btn-reset" @click="handleReset">
              恢复
            </button>
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

/* Section card */
.section-card {
  padding: 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
  display: flex;
  flex-direction: column;
  gap: 16px;
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

/* Preview panel */
.config-side {
  position: relative;
}

.preview-panel {
  position: sticky;
  top: 100px;
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

.save-feedback {
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: center;
  font-size: var(--font-size-xs);
  color: #6ee7b7;
}

.btn-reset {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-input);
  color: var(--foreground-primary);
  font-size: var(--font-size-base);
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-reset:hover {
  background: rgba(255, 255, 255, 0.08);
}

.btn-icon {
  margin-right: 2px;
}
</style>

<!-- 全局样式覆盖: config tab 内的 Element Plus 组件 -->
<style>
/* Select 触发器 */
.config-tab .el-select .el-input__wrapper {
  background: rgba(15, 23, 46, 0.6) !important;
  border-color: rgba(255, 255, 255, 0.1) !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}

.config-tab .el-select .el-input__wrapper:hover {
  border-color: rgba(255, 255, 255, 0.18) !important;
}

.config-tab .el-select .el-input__inner {
  color: #e2e8f0 !important;
}

/* Select 下拉面板 */
.config-select-popper {
  background: #0f172e !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 10px !important;
}

.config-select-popper .el-select-dropdown__item {
  color: #e2e8f0 !important;
  padding: 8px 12px !important;
  font-size: 13px !important;
}

.config-select-popper .el-select-dropdown__item.is-hovering,
.config-select-popper .el-select-dropdown__item:hover {
  background: rgba(59, 130, 246, 0.12) !important;
}

.config-select-popper .el-select-dropdown__item.is-selected {
  color: #93c5fd !important;
  font-weight: 500 !important;
}

/* Slider 轨道 */
.config-tab .el-slider__runway {
  background: rgba(255, 255, 255, 0.08) !important;
}

.config-tab .el-slider__bar {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6) !important;
}

.config-tab .el-slider__button {
  border-color: #3b82f6 !important;
  background: #fff !important;
}

/* Switch */
.config-tab .el-switch.is-checked .el-switch__core {
  background: #3b82f6 !important;
  border-color: #3b82f6 !important;
}
</style>
