<script setup lang="ts">
import { ref, computed } from 'vue'
import { Network, Download, RefreshCw } from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import type { KB } from '@/types/knowledgeBase'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import { reExtractGraph as reExtractGraphApi } from '@/services/knowledgeBaseApi'

const props = defineProps<{
  kb: KB
}>()

const store = useKnowledgeBaseStore()
const hoveredId = ref<string | null>(null)
const filterType = ref<string>('all')
const reExtracting = ref(false)

const ENTITY_COLORS: Record<string, string> = {
  '人物': '#60a5fa',
  '组织': '#a78bfa',
  '产品': '#34d399',
  '概念': '#fbbf24',
  '算法': '#f87171',
}

async function handleReExtract() {
  reExtracting.value = true
  try {
    const result = await reExtractGraphApi(props.kb.id)
    ElMessage.success(
      `知识图谱重建完成：${result.entities} 个实体，${result.relations} 个关系`
    )
    // 刷新图谱数据
    await store.selectKb(props.kb.id)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '图谱重建失败'
    ElMessage.error(msg)
  } finally {
    reExtracting.value = false
  }
}

const entityTypes = computed(() =>
  Array.from(new Set(props.kb.entitiesData.map((e) => e.type))),
)

const visibleEntities = computed(() =>
  filterType.value === 'all'
    ? props.kb.entitiesData
    : props.kb.entitiesData.filter((e) => e.type === filterType.value),
)

const visibleIds = computed(() => new Set(visibleEntities.value.map((e) => e.id)))

const visibleRelations = computed(() =>
  props.kb.relationsData.filter(
    (r) => visibleIds.value.has(r.from) && visibleIds.value.has(r.to),
  ),
)

const sortedEntities = computed(() =>
  [...visibleEntities.value].sort((a, b) => b.mentions - a.mentions),
)
</script>

<template>
  <div class="graph-tab">
    <div class="graph-layout">
      <div class="graph-main">
        <div class="card">
          <div class="graph-toolbar">
            <h3 class="card-title"><Network :size="16" class="title-icon" />知识图谱</h3>
            <div class="graph-actions">
              <el-select v-model="filterType" size="small" style="width: 120px">
                <el-option label="全部类型" value="all" />
                <el-option v-for="t in entityTypes" :key="t" :label="t" :value="t" />
              </el-select>
              <el-button size="small" :loading="reExtracting" @click="handleReExtract">
                <RefreshCw :size="14" class="btn-icon" />重建图谱
              </el-button>
              <el-button size="small">
                <Download :size="14" class="btn-icon" />导出
              </el-button>
            </div>
          </div>

          <div class="graph-canvas-wrap">
            <svg viewBox="0 0 720 480" class="graph-svg">
              <defs>
                <marker
                  id="arrowhead"
                  viewBox="0 0 10 10"
                  refX="9"
                  refY="5"
                  markerWidth="5"
                  markerHeight="5"
                  orient="auto"
                >
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
                </marker>
              </defs>

              <!-- 关系线 -->
              <g v-for="r in visibleRelations" :key="r.id">
                <line
                  v-if="kb.entitiesData.find(e => e.id === r.from) && kb.entitiesData.find(e => e.id === r.to)"
                  :x1="kb.entitiesData.find(e => e.id === r.from)!.x"
                  :y1="kb.entitiesData.find(e => e.id === r.from)!.y"
                  :x2="kb.entitiesData.find(e => e.id === r.to)!.x"
                  :y2="kb.entitiesData.find(e => e.id === r.to)!.y"
                  :stroke="hoveredId && (hoveredId === r.from || hoveredId === r.to) ? '#60a5fa' : '#475569'"
                  :stroke-width="hoveredId && (hoveredId === r.from || hoveredId === r.to) ? 2 : 1"
                  :opacity="hoveredId ? (hoveredId === r.from || hoveredId === r.to ? 1 : 0.2) : 0.6"
                  marker-end="url(#arrowhead)"
                />
                <text
                  v-if="kb.entitiesData.find(e => e.id === r.from) && kb.entitiesData.find(e => e.id === r.to)"
                  :x="(kb.entitiesData.find(e => e.id === r.from)!.x + kb.entitiesData.find(e => e.id === r.to)!.x) / 2"
                  :y="(kb.entitiesData.find(e => e.id === r.from)!.y + kb.entitiesData.find(e => e.id === r.to)!.y) / 2 - 4"
                  fill="#94a3b8"
                  font-size="10"
                  text-anchor="middle"
                >
                  {{ r.label }}
                </text>
              </g>

              <!-- 实体节点 -->
              <g
                v-for="e in visibleEntities"
                :key="e.id"
                @mouseenter="hoveredId = e.id"
                @mouseleave="hoveredId = null"
                style="cursor: pointer"
              >
                <circle
                  :cx="e.x" :cy="e.y"
                  :r="16 + Math.min(14, e.mentions / 4)"
                  :fill="ENTITY_COLORS[e.type] || '#94a3b8'"
                  :fill-opacity="hoveredId === e.id ? 0.4 : 0.2"
                  :stroke="ENTITY_COLORS[e.type] || '#94a3b8'"
                  :stroke-width="hoveredId === e.id ? 2.5 : 1.5"
                />
                <text
                  :x="e.x" :y="e.y + 4"
                  fill="#fff"
                  font-size="11"
                  text-anchor="middle"
                >
                  {{ e.name }}
                </text>
              </g>
            </svg>
          </div>

          <!-- 图例 -->
          <div class="legend">
            <div v-for="(color, type) in ENTITY_COLORS" :key="type" class="legend-item">
              <div class="legend-dot" :style="{ background: color }" />
              <span class="legend-label">{{ type }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 实体列表 -->
      <div class="graph-side">
        <div class="card">
          <h4 class="card-title">实体列表</h4>
          <div class="entity-list">
            <div
              v-for="e in sortedEntities"
              :key="e.id"
              :class="['entity-item', { 'entity-hovered': hoveredId === e.id }]"
              @mouseenter="hoveredId = e.id"
              @mouseleave="hoveredId = null"
            >
              <div class="entity-header">
                <span class="entity-name">{{ e.name }}</span>
                <el-tag
                  size="small"
                  :color="ENTITY_COLORS[e.type]"
                  class="entity-type-tag"
                >
                  {{ e.type }}
                </el-tag>
              </div>
              <div class="entity-mentions">{{ e.mentions }} 次提及</div>
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
}

.graph-layout {
  display: grid;
  grid-template-columns: 9fr 3fr;
  gap: 16px;
  height: 100%;
}

.graph-main,
.graph-side {
  min-height: 0;
  overflow-y: auto;
}

.card {
  padding: 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
}

.graph-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0;
}

.title-icon {
  color: #93c5fd;
}

.graph-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-icon {
  margin-right: 4px;
}

.graph-canvas-wrap {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.graph-svg {
  width: 100%;
  height: 480px;
}

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-xs);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.legend-label {
  color: var(--foreground-secondary);
}

.entity-list {
  max-height: 512px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.entity-item {
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all 0.15s;
}

.entity-item:hover,
.entity-hovered {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
}

.entity-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.entity-name {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
}

.entity-type-tag {
  font-size: 10px;
  padding: 0 4px;
  height: 18px;
  line-height: 18px;
  border: none;
}

.entity-mentions {
  font-size: 10px;
  color: var(--foreground-muted);
  margin-top: 2px;
}
</style>
