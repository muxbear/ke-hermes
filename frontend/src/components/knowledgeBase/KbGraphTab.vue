<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls, ControlButton } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import {
  Network, RefreshCw, Search,
  Lock, Unlock, ChevronRight, X,
} from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import type { KB, Entity } from '@/types/knowledgeBase'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import { reExtractGraph as reExtractGraphApi } from '@/services/knowledgeBaseApi'
import { useKnowledgeGraph } from '@/composables/useKnowledgeGraph'

const props = defineProps<{ kb: KB }>()

const store = useKnowledgeBaseStore()
const {
  nodeTypes, edgeTypes,
  graphNodes, graphEdges,
  selectedEntityId, searchQuery,
  connectedNodeIds, matchedSearchIds,
  loadingLayout,
  selectEntity, applyForceLayout, init, applyNodeData,
} = useKnowledgeGraph()

const { fitView, zoomIn, zoomOut } = useVueFlow()
const reExtracting = ref(false)
const filterType = ref<string>('all')
const isLocked = ref(false)
const searchInputRef = ref<HTMLInputElement | null>(null)

const ENTITY_COLORS: Record<string, string> = {
  '人物': '#60a5fa',
  '组织': '#a78bfa',
  '产品': '#34d399',
  '概念': '#fbbf24',
  '算法': '#f87171',
}

const entityTypes = computed(() =>
  Array.from(new Set(props.kb.entitiesData.map((e) => e.type))),
)

// 类型过滤后的实体和关系
const filteredEntities = computed(() =>
  filterType.value === 'all'
    ? props.kb.entitiesData
    : props.kb.entitiesData.filter((e) => e.type === filterType.value),
)

const filteredEntityIds = computed(() => new Set(filteredEntities.value.map((e) => e.id)))

const filteredRelations = computed(() =>
  props.kb.relationsData.filter(
    (r) => filteredEntityIds.value.has(r.from) && filteredEntityIds.value.has(r.to),
  ),
)

const selectedEntity = computed(() =>
  selectedEntityId.value
    ? props.kb.entitiesData.find((e) => e.id === selectedEntityId.value) ?? null
    : null,
)

const selectedEntityRelations = computed(() => {
  if (!selectedEntityId.value) return []
  return props.kb.relationsData.filter(
    (r) => r.from === selectedEntityId.value || r.to === selectedEntityId.value,
  )
})

// 关联实体（联动高亮时显示在右侧面板）
const relatedEntities = computed(() => {
  if (!selectedEntityId.value) return []
  const relatedIds = new Set<string>()
  for (const r of props.kb.relationsData) {
    if (r.from === selectedEntityId.value) relatedIds.add(r.to)
    if (r.to === selectedEntityId.value) relatedIds.add(r.from)
  }
  return props.kb.entitiesData
    .filter((e) => relatedIds.has(e.id))
    .sort((a, b) => b.mentions - a.mentions)
})

// 实体列表（按提及排序）
const sortedEntities = computed(() =>
  [...filteredEntities.value].sort((a, b) => b.mentions - a.mentions),
)

// 搜索过滤实体列表
const searchedEntities = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return sortedEntities.value
  return sortedEntities.value.filter((e) => e.name.toLowerCase().includes(q))
})

// 初始化图谱
watch(
  () => [props.kb.entitiesData, props.kb.relationsData],
  () => {
    init(filteredEntities.value, filteredRelations.value)
  },
  { immediate: true },
)

// 类型过滤变化时重新初始化
watch(filterType, () => {
  selectedEntityId.value && selectEntity(null)
  init(filteredEntities.value, filteredRelations.value)
})

// 搜索变化时更新节点 dimmed 状态
watch(searchQuery, () => {
  applyNodeData()
})

async function handleReExtract() {
  reExtracting.value = true
  try {
    const result = await reExtractGraphApi(props.kb.id)
    ElMessage.success(`知识图谱重建完成：${result.entities} 个实体，${result.relations} 个关系`)
    await store.selectKb(props.kb.id)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '图谱重建失败'
    ElMessage.error(msg)
  } finally {
    reExtracting.value = false
  }
}

function handleNodeClick({ node }: { node: { id: string } }) {
  selectEntity(selectedEntityId.value === node.id ? null : node.id)
}

function handleNodeDoubleClick({ node }: { node: { id: string } }) {
  selectEntity(node.id)
  nextTick(() => {
    fitView({ nodes: [node.id], duration: 400, padding: 0.5 })
  })
}

function handlePaneClick() {
  selectEntity(null)
}

function handlePaneReady() {
  setTimeout(() => fitView({ duration: 400, padding: 0.12, maxZoom: 1.8 }), 300)
}

function handleSearchEnter() {
  if (!searchQuery.value.trim()) return
  const matched = searchedEntities.value
  if (matched.length === 1) {
    selectEntity(matched[0].id)
    nextTick(() => fitView({ nodes: [matched[0].id], duration: 400, padding: 0.5 }))
  }
}

function handleExportPng() {
  // 使用 Vue Flow 内置的截图能力
  const el = document.querySelector('.vue-flow__viewport') as HTMLElement | null
  if (!el) return
  // 简单导出：创建 canvas
  const svgEl = el.querySelector('svg')
  if (!svgEl) {
    ElMessage.warning('无法导出：未找到图谱画布')
    return
  }
  const serializer = new XMLSerializer()
  const svgStr = serializer.serializeToString(svgEl)
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  const img = new Image()
  const blob = new Blob([svgStr], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  img.onload = () => {
    canvas.width = img.width * 2
    canvas.height = img.height * 2
    ctx!.scale(2, 2)
    ctx!.fillStyle = '#0f172a'
    ctx!.fillRect(0, 0, canvas.width, canvas.height)
    ctx!.drawImage(img, 0, 0)
    URL.revokeObjectURL(url)
    canvas.toBlob((b) => {
      if (!b) return
      const a = document.createElement('a')
      a.href = URL.createObjectURL(b)
      a.download = `knowledge-graph-${props.kb.id}.png`
      a.click()
      ElMessage.success('图谱已导出')
    }, 'image/png')
  }
  img.src = url
}

function handleResetLayout() {
  applyForceLayout()
  nextTick(() => {
    setTimeout(() => fitView({ duration: 400, padding: 0.12, maxZoom: 1.8 }), 100)
  })
}

function navigateToEntity(entityId: string) {
  selectEntity(entityId)
  nextTick(() => fitView({ nodes: [entityId], duration: 400, padding: 0.5 }))
}

function minimapNodeColor(node: { data?: { color?: string } }) {
  return node.data?.color || '#94a3b8'
}
</script>

<template>
  <div class="graph-tab">
    <!-- 工具栏 -->
    <div class="graph-toolbar">
      <div class="toolbar-left">
        <h3 class="toolbar-title"><Network :size="18" />知识图谱</h3>
        <span v-if="filteredEntities.length" class="toolbar-count">
          {{ filteredEntities.length }}个实体 · {{ filteredRelations.length }}条关系
        </span>
      </div>
      <div class="toolbar-right">
        <!-- 搜索 -->
        <div class="search-box">
          <Search :size="14" class="search-icon" />
          <input
            ref="searchInputRef"
            v-model="searchQuery"
            type="text"
            placeholder="搜索实体..."
            class="search-input"
            @keyup.enter="handleSearchEnter"
          />
          <button v-if="searchQuery" class="search-clear" @click="searchQuery = ''">
            <X :size="14" />
          </button>
        </div>

        <el-select v-model="filterType" size="small" style="width: 110px">
          <el-option label="全部类型" value="all" />
          <el-option v-for="t in entityTypes" :key="t" :label="t" :value="t" />
        </el-select>

        <button class="toolbar-btn" :title="isLocked ? '解锁布局（允许拖拽节点）' : '锁定布局（禁止拖拽节点）'" @click="isLocked = !isLocked">
          <Lock v-if="isLocked" :size="16" />
          <Unlock v-else :size="16" />
        </button>

        <button class="toolbar-btn" title="重新计算力导向布局" :disabled="loadingLayout" @click="handleResetLayout">
          <RefreshCw :size="16" :class="{ 'spin': loadingLayout }" />
        </button>

        <button class="toolbar-btn" title="导出为 PNG 图片" @click="handleExportPng">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        </button>

        <el-button size="small" type="primary" :loading="reExtracting" @click="handleReExtract">
          重建图谱
        </el-button>
      </div>
    </div>

    <!-- 主布局 -->
    <div class="graph-body">
      <!-- 画布 -->
      <div class="graph-canvas">
        <VueFlow
          :nodes="graphNodes"
          :edges="graphEdges"
          :node-types="nodeTypes"
          :edge-types="edgeTypes"
          :nodes-draggable="!isLocked"
          :pan-on-drag="!isLocked ? [0, 1, 2] : []"
          :zoom-on-scroll="!isLocked"
          :default-viewport="{ x: 0, y: 0, zoom: 1 }"
          :min-zoom="0.05"
          :max-zoom="4"
          class="graph-flow"
          @node-click="handleNodeClick"
          @node-double-click="handleNodeDoubleClick"
          @pane-click="handlePaneClick"
          @pane-ready="handlePaneReady"
        >
          <Background :gap="20" :size="1" pattern-color="#1e293b" />
          <Controls position="bottom-right" :show-interactive="false" :show-zoom="false" :show-fit-view="false">
            <ControlButton title="放大" @click="zoomIn({ duration: 200 })">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="7"/>
                <path d="M21 21l-4-4"/>
                <path d="M11 8v6M8 11h6"/>
              </svg>
            </ControlButton>
            <ControlButton title="缩小" @click="zoomOut({ duration: 200 })">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="7"/>
                <path d="M21 21l-4-4"/>
                <path d="M8 11h6"/>
              </svg>
            </ControlButton>
            <ControlButton title="适应视图（显示全部节点）" @click="fitView({ duration: 300, padding: 0.12, maxZoom: 1.8 })">
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M8 3H5a2 2 0 0 0-2 2v3"/>
                <path d="M21 8V5a2 2 0 0 0-2-2h-3"/>
                <path d="M3 16v3a2 2 0 0 0 2 2h3"/>
                <path d="M16 21h3a2 2 0 0 0 2-2v-3"/>
              </svg>
            </ControlButton>
          </Controls>
          <MiniMap
            position="bottom-left"
            style="background: rgba(15, 23, 42, 0.9); border: 1px solid #334155; border-radius: 8px;"
            :node-color="minimapNodeColor"
            :mask-color="'rgba(30, 41, 59, 0.4)'"
          />
        </VueFlow>
      </div>

      <!-- 右侧面板 -->
      <div class="graph-panel" :class="{ 'graph-panel--collapsed': false }">
        <!-- 实体列表 -->
        <div class="panel-section">
          <h4 class="panel-title">实体列表 ({{ searchedEntities.length }})</h4>
          <div class="entity-list">
            <div
              v-for="e in searchedEntities"
              :key="e.id"
              :class="[
                'entity-item',
                {
                  'entity-item--selected': selectedEntityId === e.id,
                  'entity-item--connected': connectedNodeIds.has(e.id) && selectedEntityId !== e.id,
                  'entity-item--dimmed': selectedEntityId && !connectedNodeIds.has(e.id),
                },
              ]"
              @click="navigateToEntity(e.id)"
            >
              <div class="entity-item-dot" :style="{ background: ENTITY_COLORS[e.type] || '#94a3b8' }" />
              <div class="entity-item-info">
                <span class="entity-item-name">{{ e.name }}</span>
                <span class="entity-item-meta">{{ e.type }} · {{ e.mentions }}次</span>
              </div>
              <ChevronRight :size="14" class="entity-item-arrow" />
            </div>
            <div v-if="searchedEntities.length === 0" class="entity-empty">
              {{ searchQuery ? '未找到匹配实体' : '暂无实体数据' }}
            </div>
          </div>
        </div>

        <!-- 选中实体详情 -->
        <div v-if="selectedEntity" class="panel-section panel-detail">
          <div class="detail-header">
            <h4 class="panel-title">实体详情</h4>
            <button class="detail-close" @click="selectEntity(null)">
              <X :size="14" />
            </button>
          </div>
          <div class="detail-body">
            <div class="detail-hero">
              <div
                class="detail-avatar"
                :style="{ background: ENTITY_COLORS[selectedEntity.type] || '#94a3b8' }"
              >
                {{ selectedEntity.name.charAt(0) }}
              </div>
              <div class="detail-hero-text">
                <span class="detail-name">{{ selectedEntity.name }}</span>
                <span class="detail-type">
                  <el-tag size="small" :color="ENTITY_COLORS[selectedEntity.type]" style="border: none; color: #fff;">
                    {{ selectedEntity.type }}
                  </el-tag>
                </span>
              </div>
            </div>
            <div class="detail-stats">
              <div class="detail-stat">
                <span class="detail-stat-value">{{ selectedEntity.mentions }}</span>
                <span class="detail-stat-label">提及次数</span>
              </div>
              <div class="detail-stat">
                <span class="detail-stat-value">{{ selectedEntityRelations.length }}</span>
                <span class="detail-stat-label">关联关系</span>
              </div>
            </div>

            <!-- 关联关系 -->
            <div v-if="selectedEntityRelations.length" class="detail-relations">
              <h5 class="detail-section-title">关联关系</h5>
              <div
                v-for="r in selectedEntityRelations"
                :key="r.id"
                class="relation-row"
              >
                <span
                  class="relation-entity"
                  :class="{ 'relation-link': r.from !== selectedEntityId }"
                  @click="r.from !== selectedEntityId && navigateToEntity(r.from)"
                >
                  {{ props.kb.entitiesData.find(e => e.id === r.from)?.name || r.from }}
                </span>
                <span class="relation-label">{{ r.label }}</span>
                <span
                  class="relation-entity"
                  :class="{ 'relation-link': r.to !== selectedEntityId }"
                  @click="r.to !== selectedEntityId && navigateToEntity(r.to)"
                >
                  {{ props.kb.entitiesData.find(e => e.id === r.to)?.name || r.to }}
                </span>
              </div>
            </div>

            <!-- 关联实体 -->
            <div v-if="relatedEntities.length" class="detail-relations">
              <h5 class="detail-section-title">关联实体</h5>
              <div
                v-for="e in relatedEntities"
                :key="e.id"
                class="entity-item entity-item--sm"
                @click="navigateToEntity(e.id)"
              >
                <div class="entity-item-dot" :style="{ background: ENTITY_COLORS[e.type] || '#94a3b8' }" />
                <span class="entity-item-name">{{ e.name }}</span>
                <span class="entity-item-meta">{{ e.type }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.graph-tab {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

/* ── 工具栏 ── */
.graph-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
  margin-bottom: 12px;
  flex-shrink: 0;
  gap: 16px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0;
  white-space: nowrap;
}

.toolbar-count {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  white-space: nowrap;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 8px;
  color: #64748b;
  pointer-events: none;
}

.search-input {
  width: 180px;
  height: 30px;
  padding: 0 28px 0 28px;
  font-size: 12px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  color: var(--foreground-primary);
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: #60a5fa;
}

.search-input::placeholder {
  color: #64748b;
}

.search-clear {
  position: absolute;
  right: 4px;
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 2px;
  display: flex;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  background: #1e293b;
  border: 1px solid #475569;
  border-radius: 6px;
  color: #cbd5e1;
  cursor: pointer;
  transition: all 0.15s;
}

.toolbar-btn:hover {
  background: #3b82f6;
  border-color: #3b82f6;
  color: #fff;
}

.toolbar-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ── 主布局 ── */
.graph-body {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.graph-canvas {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
  overflow: hidden;
  min-height: 0;
}

.graph-flow {
  width: 100%;
  height: 100%;
}

/* ── 面板 ── */
.graph-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  overflow-y: auto;
}

.panel-section {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
  padding: 14px;
  flex-shrink: 0;
}

.panel-detail {
  flex-shrink: 0;
}

.panel-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0 0 10px 0;
}

/* ── 实体列表 ── */
.entity-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 360px;
  overflow-y: auto;
}

.entity-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: rgba(0, 0, 0, 0.15);
  border: 1px solid transparent;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s;
}

.entity-item:hover {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.2);
}

.entity-item--selected {
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.4);
}

.entity-item--connected {
  background: rgba(59, 130, 246, 0.05);
}

.entity-item--dimmed {
  opacity: 0.4;
}

.entity-item--sm {
  padding: 6px 8px;
}

.entity-item-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.entity-item-info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  flex: 1;
  min-width: 0;
}

.entity-item-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--foreground-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.entity-item-meta {
  font-size: 10px;
  color: var(--foreground-muted);
}

.entity-item-arrow {
  color: #475569;
  flex-shrink: 0;
}

.entity-empty {
  padding: 20px;
  text-align: center;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

/* ── 详情 ── */
.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.detail-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: none;
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  color: #94a3b8;
  cursor: pointer;
}

.detail-close:hover {
  background: rgba(239, 68, 68, 0.15);
  color: #f87171;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-hero {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.detail-hero-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.detail-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.detail-type {
  display: flex;
}

.detail-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.detail-stat {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 10px;
  text-align: center;
}

.detail-stat-value {
  display: block;
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
}

.detail-stat-label {
  font-size: 10px;
  color: var(--foreground-muted);
  margin-top: 2px;
}

.detail-section-title {
  font-size: 11px;
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 8px 0;
}

.relation-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 0;
  font-size: 12px;
}

.relation-entity {
  color: #94a3b8;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.relation-link {
  color: #60a5fa;
  cursor: pointer;
}

.relation-link:hover {
  text-decoration: underline;
}

.relation-label {
  background: rgba(59, 130, 246, 0.15);
  color: #93c5fd;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 11px;
  white-space: nowrap;
  flex-shrink: 0;
}

/* 窄屏堆叠 */
@media (max-width: 900px) {
  .graph-body {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr auto;
  }
  .graph-panel {
    max-height: 300px;
  }
}
</style>

<!-- 全局样式（不带 scoped，Vue Flow 需要） -->
<style>
@import '@vue-flow/core/dist/style.css';
@import '@vue-flow/core/dist/theme-default.css';
@import '@vue-flow/controls/dist/style.css';
@import '@vue-flow/minimap/dist/style.css';

/* Vue Flow 深色主题适配 */
.vue-flow {
  background: transparent !important;
}

.vue-flow__background pattern circle {
  fill: #1e293b !important;
}

.vue-flow__minimap {
  border-radius: 8px !important;
}

.vue-flow__controls {
  border-radius: 8px !important;
  overflow: hidden;
  border: 1px solid #475569 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4) !important;
}

.vue-flow__controls-button {
  background: #1e293b !important;
  border-color: #475569 !important;
  color: #e2e8f0 !important;
  width: 40px !important;
  height: 40px !important;
}

.vue-flow__controls-button:hover {
  background: #3b82f6 !important;
  border-color: #3b82f6 !important;
  color: #fff !important;
}

.vue-flow__controls-button svg {
  fill: none !important;
  stroke: currentColor !important;
  width: 26px !important;
  height: 26px !important;
}

.vue-flow__edge.selected .vue-flow__edge-path {
  stroke: #60a5fa !important;
}
</style>
