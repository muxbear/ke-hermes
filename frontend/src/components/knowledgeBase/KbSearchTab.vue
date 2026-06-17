<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, Zap, Sparkle, Hash, Wand2, FileSearch } from 'lucide-vue-next'
import type { KB, SearchMode, SearchResult } from '@/types/knowledgeBase'
import * as kbApi from '@/services/knowledgeBaseApi'

const props = defineProps<{
  kb: KB
}>()

const mode = ref<SearchMode>('hybrid')
const query = ref('')
const results = ref<SearchResult[]>([])
const searched = ref(false)
const searching = ref(false)

const modeOptions: { key: SearchMode; label: string; desc: string; icon: typeof Sparkle }[] = [
  { key: 'hybrid', label: '混合检索', desc: '向量 + BM25 融合', icon: Wand2 },
  { key: 'vector', label: '向量检索', desc: '稠密语义', icon: Sparkle },
  { key: 'bm25', label: 'BM25', desc: '稀疏关键词', icon: Hash },
]

const currentConfig = computed(() => [
  `Embedding: ${props.kb.config.embeddingModel}`,
  `Top-K: ${props.kb.config.topK}`,
  props.kb.config.enableReranker ? `Reranker: ${props.kb.config.rerankerModel}` : '',
].filter(Boolean).join(' · '))

async function runSearch() {
  const q = query.value.trim()
  if (!q) return
  searching.value = true
  try {
    results.value = await kbApi.searchKnowledgeBase(
      props.kb.id,
      q,
      mode.value,
      props.kb.config.topK || 5,
    )
    searched.value = true
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '检索失败'
    results.value = []
    searched.value = true
    console.error('Search failed:', msg)
  } finally {
    searching.value = false
  }
}

function highlightText(text: string): { text: string; hl: boolean }[] {
  const q = query.value.trim()
  if (!q) return [{ text, hl: false }]
  const parts = text.split(new RegExp(`(${q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'))
  return parts.map((p) => ({
    text: p,
    hl: p.toLowerCase() === q.toLowerCase(),
  }))
}
</script>

<template>
  <div class="search-tab">
    <!-- 检索面板 -->
    <div class="card search-panel">
      <!-- 模式选择 -->
      <div class="mode-row">
        <button
          v-for="opt in modeOptions"
          :key="opt.key"
          :class="['mode-card', { 'mode-active': mode === opt.key }]"
          @click="mode = opt.key"
        >
          <div class="mode-header">
            <component :is="opt.icon" :size="16" :class="mode === opt.key ? 'text-blue-300' : 'text-slate-400'" />
            <span :class="mode === opt.key ? 'text-white' : 'text-slate-300'">{{ opt.label }}</span>
          </div>
          <div class="mode-desc">{{ opt.desc }}</div>
        </button>
      </div>

      <!-- 查询输入 -->
      <div class="query-row">
        <div class="search-input-wrap">
          <Search :size="18" class="q-search-icon" />
          <input
            v-model="query"
            type="text"
            placeholder="输入查询语句…"
            class="q-input"
            @keyup.enter="runSearch"
          />
        </div>
        <button class="btn-search" @click="runSearch" :disabled="searching">
          <Zap :size="16" class="btn-icon" />检索
        </button>
      </div>

      <div class="config-info">
        {{ currentConfig }}
      </div>
    </div>

    <!-- 检索结果 -->
    <div v-if="searched" class="results-section">
      <div class="results-count">命中 {{ results.length }} 条结果</div>
      <div v-for="(r, i) in results" :key="r.id" class="card result-card">
        <div class="result-header">
          <el-tag size="small" type="info" class="result-rank">#{{ i + 1 }}</el-tag>
          <span class="result-doc">{{ r.doc }}</span>
          <div class="result-scores">
            <span class="score-label">综合</span>
            <span class="score-value score-primary">{{ r.score.toFixed(2) }}</span>
            <span class="score-label">| 向量</span>
            <span class="score-value">{{ r.vec.toFixed(2) }}</span>
            <span class="score-label">| BM25</span>
            <span class="score-value">{{ r.bm25.toFixed(2) }}</span>
          </div>
        </div>
        <p class="result-chunk">
          <template v-for="(part, j) in highlightText(r.chunk)" :key="j">
            <mark v-if="part.hl" class="highlight">{{ part.text }}</mark>
            <span v-else>{{ part.text }}</span>
          </template>
        </p>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!searched" class="card empty-card">
      <FileSearch :size="40" class="empty-icon" />
      <div class="empty-text">输入查询语句后开始检索</div>
    </div>
  </div>
</template>

<style scoped>
.search-tab {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card {
  padding: 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
}

.search-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.mode-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.mode-card {
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
  border: none;
  outline: none;
  font-family: inherit;
}

.mode-card:hover {
  border-color: rgba(255, 255, 255, 0.2);
}

.mode-active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2));
  border-color: rgba(59, 130, 246, 0.4);
}

.mode-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.mode-header span {
  font-size: var(--font-size-sm);
}

.mode-desc {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin-top: 6px;
}

.query-row {
  display: flex;
  gap: 10px;
}

.search-input-wrap {
  position: relative;
  flex: 1;
}

.q-search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--foreground-secondary);
  pointer-events: none;
  z-index: 1;
}

.q-input {
  width: 100%;
  height: 44px;
  padding: 0 16px 0 42px;
  background: rgba(15, 23, 46, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-input);
  color: var(--foreground-primary);
  font-size: var(--font-size-base);
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.q-input::placeholder {
  color: var(--foreground-muted);
}

.q-input:focus {
  border-color: rgba(59, 130, 246, 0.4);
}

.btn-search {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 44px;
  padding: 0 20px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border: none;
  border-radius: var(--radius-input);
  color: #fff;
  font-size: var(--font-size-base);
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.2s;
  white-space: nowrap;
}

.btn-search:hover {
  opacity: 0.9;
}

.btn-search:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.config-info {
  font-size: var(--font-size-xs);
  color: var(--foreground-secondary);
}

.results-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.results-count {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}

.result-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.result-rank {
  flex-shrink: 0;
}

.result-doc {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
  flex: 1;
}

.result-scores {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
}

.score-label {
  color: var(--foreground-muted);
}

.score-value {
  color: var(--foreground-primary);
}

.score-primary {
  color: #6ee7b7;
  font-weight: var(--font-weight-semibold);
}

.result-chunk {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
  line-height: 1.7;
  margin: 0;
}

.highlight {
  background: rgba(250, 204, 21, 0.3);
  color: #fde68a;
  padding: 0 2px;
  border-radius: 2px;
}

.empty-card {
  text-align: center;
  padding: 64px 20px;
}

.empty-icon {
  color: var(--foreground-muted);
  margin-bottom: 12px;
  opacity: 0.5;
}

.empty-text {
  font-size: var(--font-size-base);
  color: var(--foreground-secondary);
}

.btn-icon {
  margin-right: 4px;
}

.text-blue-300 { color: #93c5fd; }
.text-slate-400 { color: var(--foreground-secondary); }
.text-white { color: var(--foreground-primary); }
.text-slate-300 { color: var(--foreground-primary); }
</style>
