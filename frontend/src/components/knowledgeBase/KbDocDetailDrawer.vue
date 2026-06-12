<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  ChevronLeft, Search, Layers, Network, ChevronUp, ChevronDown,
  Copy, ScrollText, Activity, Check,
} from 'lucide-vue-next'
import type { KBDoc, DocType } from '@/types/knowledgeBase'
import KbDocStatusBadge from './KbDocStatusBadge.vue'

interface DocChunk {
  id: string
  index: number
  content: string
  tokenCount: number
  charCount: number
  pageRef: string
  section: string
  entities: string[]
  edited?: boolean
}

const props = defineProps<{
  doc: KBDoc
  kbId?: string
}>()

const emit = defineEmits<{
  back: []
}>()

// ─── Mock data ────────────────────────────────────────────────────────────────
const CHUNK_SAMPLE_CONTENTS = [
  '本手册旨在规范公司员工的行为准则，明确各项管理制度，保障员工权益，促进公司健康有序发展。所有员工应认真阅读并严格遵守本手册中的各项规定。',
  '员工工作时间为上午9:00至下午18:00，午休时间为12:00至13:00。弹性工作制员工须与直属上司协商确定具体时间安排，并报 HR 备案后执行。',
  '公司实行标准工时制，每周工作5天，每天工作8小时。如需加班，须提前申请并经上级审批。法定节假日加班按国家规定执行三倍工资标准。',
  '基本工资由职位级别、工作年限、个人能力等因素综合确定。绩效奖金根据季度考核结果发放，优秀员工可获得月薪的50%-100%作为额外奖励。',
  '公司为全体员工提供五险一金，包括养老保险、医疗保险、失业保险、工伤保险、生育保险及住房公积金。具体缴纳比例按当地政策执行。',
  '员工每年享有带薪年假，具体天数根据工作年限计算：满1年5天，满3年10天，满5年15天。年假须提前一周申请，由部门主管审批。',
  '所有员工必须遵守公司的保密制度，不得泄露公司的商业秘密、技术资料、客户信息等。离职时需签署保密协议，并归还所有公司资产。',
  '绩效考核采用KPI与OKR相结合的方式，每季度进行一次正式考核。考核结果分为优秀、良好、合格、待改进四个等级。',
  '公司鼓励员工持续学习与发展，每年提供专业培训经费5000元/人。员工可申请参加外部培训、行业会议或学历提升课程。',
]
const CHUNK_SECTIONS = [
  '第一章 总则', '第二章 工作制度', '第三章 薪酬福利',
  '第四章 绩效考核', '第五章 行为规范', '第六章 保密制度',
]
const CHUNK_ENTITY_SETS = [
  ['员工', '公司'], ['HR', '工作制度'], ['薪酬', '绩效'],
  ['五险一金', '福利'], ['年假', '休假'], ['考核', 'KPI'],
]

function generateMockChunks(): DocChunk[] {
  const count = Math.min(Math.max(props.doc.chunks || 12, 1), 20)
  return Array.from({ length: count }, (_, i) => {
    const content = CHUNK_SAMPLE_CONTENTS[i % CHUNK_SAMPLE_CONTENTS.length]
    return {
      id: `${props.doc.id}-ck${i + 1}`,
      index: i + 1,
      content,
      tokenCount: Math.floor(content.length / 2.5 + (i % 3) * 15),
      charCount: content.length,
      pageRef: `第 ${Math.floor(i / 2) + 1} 页`,
      section: CHUNK_SECTIONS[Math.floor(i / 2) % CHUNK_SECTIONS.length],
      entities: [...CHUNK_ENTITY_SETS[i % CHUNK_ENTITY_SETS.length]],
      edited: false,
    }
  })
}

const docTypeIcons: Record<DocType, string> = {
  pdf: 'pdf', md: 'md', docx: 'docx', csv: 'csv', image: 'image', html: 'html',
}

const chunks = ref<DocChunk[]>(generateMockChunks())
const search = ref('')
const selectedChunk = ref<DocChunk>(chunks.value[0])
const copiedId = ref<string | null>(null)

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return chunks.value
  return chunks.value.filter(
    (c) =>
      c.content.toLowerCase().includes(q) ||
      c.section.toLowerCase().includes(q),
  )
})

const selectedIdx = computed(() => chunks.value.findIndex((c) => c.id === selectedChunk.value?.id))
const prevChunk = computed(() => selectedIdx.value > 0 ? chunks.value[selectedIdx.value - 1] : null)
const nextChunk = computed(() => selectedIdx.value < chunks.value.length - 1 ? chunks.value[selectedIdx.value + 1] : null)

function highlightText(text: string, query: string): string {
  if (!query.trim()) return text
  return text.replace(
    new RegExp(`(${query.trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'),
    '<mark class="search-highlight">$1</mark>',
  )
}

function copyChunkContent() {
  if (!selectedChunk.value) return
  navigator.clipboard.writeText(selectedChunk.value.content)
  copiedId.value = selectedChunk.value.id
  setTimeout(() => { copiedId.value = null }, 2000)
}
</script>

<template>
  <div class="doc-detail-view">
    <!-- Header -->
    <div class="detail-header">
      <div class="detail-header-left">
        <button class="back-btn" @click="$emit('back')">
          <ChevronLeft :size="16" />返回文档列表
        </button>
        <div class="header-divider" />
        <div class="doc-title-row">
          <span class="doc-name">{{ doc.name }}</span>
          <KbDocStatusBadge :status="doc.status" />
        </div>
      </div>
      <div class="detail-header-right">
        <span class="header-metric"><Layers :size="14" class="metric-icon layers-icon" />{{ doc.chunks }} 分片</span>
        <span class="header-metric"><Network :size="14" class="metric-icon network-icon" />{{ doc.entities }} 实体</span>
        <span class="header-meta-text">{{ doc.size }} · {{ doc.uploadedAt }}</span>
      </div>
    </div>

    <!-- Split view -->
    <div class="split-layout">
      <!-- Left: chunk list -->
      <div class="chunk-list-panel">
        <div class="search-wrap">
          <Search :size="16" class="search-icon" />
          <input
            v-model="search"
            type="text"
            placeholder="在分片中搜索…"
            class="search-input"
          />
        </div>
        <div class="chunk-count-label">
          显示 {{ filtered.length }} / {{ chunks.length }} 个分片
        </div>
        <div class="chunk-scroll-area">
          <div
            v-for="chunk in filtered"
            :key="chunk.id"
            :class="['chunk-card', { 'chunk-card--sel': selectedChunk?.id === chunk.id }]"
            @click="selectedChunk = chunk"
          >
            <div class="chunk-card-top">
              <div class="chunk-card-badges">
                <span :class="['chunk-index-badge', { 'chunk-index-badge--sel': selectedChunk?.id === chunk.id }]">
                  #{{ chunk.index }}
                </span>
                <span class="chunk-page-ref">{{ chunk.pageRef }}</span>
              </div>
              <span class="chunk-token-count">{{ chunk.tokenCount }} tokens</span>
            </div>
            <div class="chunk-section-label">{{ chunk.section }}</div>
            <p
              class="chunk-content-preview"
              v-html="search ? highlightText(chunk.content, search) : chunk.content"
            />
            <div v-if="chunk.entities.length > 0" class="chunk-entity-tags">
              <span v-for="e in chunk.entities" :key="e" class="entity-tag">{{ e }}</span>
            </div>
          </div>
          <div v-if="filtered.length === 0" class="chunk-empty">
            <Layers :size="24" class="chunk-empty-icon" />
            没有匹配的分片
          </div>
        </div>
      </div>

      <!-- Right: detail & context -->
      <div class="chunk-detail-panel">
        <template v-if="selectedChunk">
          <!-- Metadata bar -->
          <div class="metadata-bar">
            <div class="metadata-items">
              <span class="metadata-item">章节: <strong>{{ selectedChunk.section }}</strong></span>
              <span class="metadata-item">页码: <strong>{{ selectedChunk.pageRef }}</strong></span>
              <span class="metadata-item">Token: <strong>{{ selectedChunk.tokenCount }}</strong></span>
              <span class="metadata-item">字符: <strong>{{ selectedChunk.charCount }}</strong></span>
            </div>
            <div class="metadata-actions">
              <button
                class="nav-btn"
                :disabled="!prevChunk"
                @click="prevChunk && (selectedChunk = prevChunk)"
                title="上一个分片"
              >
                <ChevronUp :size="14" />
              </button>
              <button
                class="nav-btn"
                :disabled="!nextChunk"
                @click="nextChunk && (selectedChunk = nextChunk)"
                title="下一个分片"
              >
                <ChevronDown :size="14" />
              </button>
              <button class="nav-btn" title="复制分片内容" @click="copyChunkContent">
                <Check v-if="copiedId === selectedChunk.id" :size="14" class="copy-check-icon" />
                <Copy v-else :size="14" />
              </button>
            </div>
          </div>
          <div v-if="selectedChunk.entities.length > 0" class="metadata-entities">
            <span class="entity-label">实体:</span>
            <span v-for="e in selectedChunk.entities" :key="e" class="entity-tag">{{ e }}</span>
          </div>

          <!-- Original context view -->
          <div class="context-scroll-area">
            <div class="context-card">
              <div class="context-card-header">
                <ScrollText :size="14" class="context-header-icon" />
                原文对照视图
                <span class="context-header-right">分片 {{ selectedChunk.index }} / {{ chunks.length }}</span>
              </div>
              <div class="context-card-body">
                <!-- Previous chunk -->
                <div v-if="prevChunk" class="context-prev">
                  <div class="context-ctx-label">
                    <ChevronUp :size="10" />上文 (#{{ prevChunk.index }} · {{ prevChunk.section }})
                  </div>
                  <p class="context-ctx-text">{{ prevChunk.content }}</p>
                </div>

                <!-- Current chunk -->
                <div class="context-current">
                  <div class="context-current-label">
                    <div class="current-dot" />
                    当前分片 #{{ selectedChunk.index }} · {{ selectedChunk.section }}
                  </div>
                  <p
                    class="context-current-text"
                    v-html="search ? highlightText(selectedChunk.content, search) : selectedChunk.content"
                  />
                </div>

                <!-- Next chunk -->
                <div v-if="nextChunk" class="context-next">
                  <div class="context-ctx-label">
                    <ChevronDown :size="10" />下文 (#{{ nextChunk.index }} · {{ nextChunk.section }})
                  </div>
                  <p class="context-ctx-text">{{ nextChunk.content }}</p>
                </div>
              </div>
            </div>

            <!-- Stats card -->
            <div class="stats-card">
              <h4 class="stats-title"><Activity :size="14" class="stats-title-icon" />分片统计</h4>
              <div class="stats-grid">
                <div class="stat-item">
                  <div class="stat-value">{{ selectedChunk.tokenCount }}</div>
                  <div class="stat-label">Token 数</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ selectedChunk.charCount }}</div>
                  <div class="stat-label">字符数</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ selectedChunk.entities.length }}</div>
                  <div class="stat-label">实体数</div>
                </div>
              </div>
              <div class="stats-position">
                <div class="stats-position-header">
                  <span>分片位置</span>
                  <span>{{ selectedChunk.index }} / {{ chunks.length }}</span>
                </div>
                <div class="stats-position-bar">
                  <div
                    class="stats-position-fill"
                    :style="{ width: `${(selectedChunk.index / chunks.length) * 100}%` }"
                  />
                </div>
              </div>
            </div>
          </div>
        </template>
        <div v-else class="detail-empty">
          <Layers :size="32" class="detail-empty-icon" />
          <div>从左侧选择一个分片查看详情</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.doc-detail-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  min-height: 0;
}

/* Header */
.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.detail-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: #cbd5e1;
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: color 0.15s;
}

.back-btn:hover {
  color: #fff;
}

.header-divider {
  width: 1px;
  height: 20px;
  background: rgba(255, 255, 255, 0.1);
}

.doc-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-name {
  font-size: 14px;
  color: #fff;
}

.detail-header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
}

.header-metric {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #94a3b8;
}

.metric-icon {
  flex-shrink: 0;
}

.layers-icon { color: #c4b5fd; }
.network-icon { color: #6ee7b7; }

.header-meta-text {
  color: #64748b;
}

/* Split layout */
.split-layout {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

/* Left panel - chunk list */
.chunk-list-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.search-wrap {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 36px;
  padding: 0 12px 0 36px;
  background: rgba(15, 23, 46, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #f2f5fa;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.search-input::placeholder {
  color: #596680;
}

.search-input:focus {
  border-color: rgba(59, 130, 246, 0.4);
}

.chunk-count-label {
  font-size: 12px;
  color: #64748b;
}

.chunk-scroll-area {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 8px;
}

.chunk-scroll-area::-webkit-scrollbar {
  width: 4px;
}

.chunk-scroll-area::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

/* Chunk cards */
.chunk-card {
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(15, 23, 46, 0.4);
  cursor: pointer;
  transition: all 0.2s;
}

.chunk-card:hover {
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(15, 23, 46, 0.6);
}

.chunk-card--sel {
  background: rgba(59, 130, 246, 0.15) !important;
  border-color: rgba(59, 130, 246, 0.4) !important;
}

.chunk-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.chunk-card-badges {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chunk-index-badge {
  font-size: 10px;
  padding: 0 6px;
  height: 16px;
  line-height: 16px;
  border-radius: 4px;
  background: rgba(100, 116, 139, 0.1);
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.chunk-index-badge--sel {
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
  border-color: rgba(59, 130, 246, 0.4);
}

.chunk-page-ref {
  font-size: 10px;
  color: #64748b;
}

.chunk-token-count {
  font-size: 10px;
  color: #64748b;
}

.chunk-section-label {
  font-size: 10px;
  color: #64748b;
  margin-bottom: 4px;
}

.chunk-content-preview {
  margin: 0;
  font-size: 12px;
  color: #cbd5e1;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.search-highlight {
  background: rgba(250, 204, 21, 0.3);
  color: #fde68a;
  padding: 0 2px;
  border-radius: 2px;
}

.chunk-entity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}

.entity-tag {
  font-size: 9px;
  padding: 0 6px;
  height: 14px;
  line-height: 14px;
  border-radius: 4px;
  background: rgba(168, 85, 247, 0.1);
  color: #c4b5fd;
  border: 1px solid rgba(168, 85, 247, 0.2);
}

.chunk-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: #64748b;
  font-size: 13px;
  gap: 8px;
}

.chunk-empty-icon {
  opacity: 0.4;
}

/* Right panel */
.chunk-detail-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
}

.metadata-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: rgba(15, 23, 46, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.metadata-items {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
}

.metadata-item {
  color: #94a3b8;
}

.metadata-item strong {
  color: #e2e8f0;
}

.metadata-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s;
}

.nav-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.08);
  color: #e2e8f0;
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.copy-check-icon {
  color: #10b981;
}

.metadata-entities {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 4px;
}

.entity-label {
  font-size: 10px;
  color: #64748b;
}

/* Context view */
.context-scroll-area {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.context-scroll-area::-webkit-scrollbar {
  width: 4px;
}

.context-scroll-area::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.context-card {
  border-radius: 12px;
  background: rgba(15, 23, 46, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.context-card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 12px;
  color: #94a3b8;
}

.context-header-icon {
  color: #93c5fd;
}

.context-header-right {
  margin-left: auto;
  color: #475569;
}

.context-card-body {
  padding: 16px;
}

.context-prev,
.context-next {
  border-left: 2px solid rgba(51, 65, 85, 0.6);
  padding-left: 16px;
  padding-top: 12px;
  padding-bottom: 12px;
}

.context-ctx-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  color: #475569;
  margin-bottom: 6px;
}

.context-ctx-text {
  margin: 0;
  font-size: 13px;
  color: #475569;
  line-height: 1.6;
}

.context-current {
  border-left: 2px solid #3b82f6;
  padding-left: 16px;
  padding-top: 16px;
  padding-bottom: 16px;
  background: rgba(59, 130, 246, 0.05);
  border-radius: 0 8px 8px 0;
  margin: 4px 0;
}

.context-current-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: #60a5fa;
  margin-bottom: 8px;
}

.current-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3b82f6;
  animation: dot-pulse 1.5s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.context-current-text {
  margin: 0;
  font-size: 14px;
  color: #e2e8f0;
  line-height: 1.6;
}

/* Stats card */
.stats-card {
  margin-top: 12px;
  padding: 16px;
  background: rgba(15, 23, 46, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.stats-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
  margin: 0 0 12px;
}

.stats-title-icon {
  color: #93c5fd;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.stat-label {
  font-size: 10px;
  color: #64748b;
  margin-top: 2px;
}

.stats-position-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 10px;
  color: #64748b;
  margin-bottom: 4px;
}

.stats-position-bar {
  height: 8px;
  border-radius: 4px;
  background: #1e293b;
  overflow: hidden;
}

.stats-position-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  transition: width 0.3s ease;
}

/* Empty state */
.detail-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #64748b;
  font-size: 13px;
  gap: 8px;
}

.detail-empty-icon {
  opacity: 0.4;
}
</style>
