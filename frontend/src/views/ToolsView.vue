<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Wrench } from 'lucide-vue-next'
import { useToolStore } from '@/stores/tool'
import type { Tool, ToolCreateRequest, ToolCategory, ToolSource, ToolStatus } from '@/types/tool'
import { CATEGORY_META, STATUS_META } from '@/types/tool'
import ToolCard from '@/components/tool/ToolCard.vue'
import ToolDialog from '@/components/tool/ToolDialog.vue'
import ToolDetailDrawer from '@/components/tool/ToolDetailDrawer.vue'

const toolStore = useToolStore()

// -- Source tab --
type SourceTab = 'all' | ToolSource
const sourceTab = ref<SourceTab>('all')

// -- Category filter --
const categoryFilter = ref<ToolCategory | 'all'>('all')

// -- Status filter --
const statusFilter = ref<ToolStatus | 'all'>('all')

// -- Search --
const search = ref('')

// -- Dialog state --
const editing = ref<Tool | null | 'new'>(null)
const deleting = ref<Tool | null>(null)
const detail = ref<Tool | null>(null)

// -- Stats --
const builtinCount = computed(() => toolStore.tools.filter((t) => t.source === 'builtin').length)
const thirdPartyCount = computed(() => toolStore.tools.filter((t) => t.source === 'third-party').length)

const statCards = computed(() => [
  { label: '工具总数', value: toolStore.tools.length, color: '#f2f5fa', bg: 'rgba(20,29,56,0.5)', border: 'rgba(38,51,89,0.25)' },
  { label: '内置工具', value: builtinCount.value, color: '#818cf8', bg: 'rgba(99,102,241,0.04)', border: 'rgba(99,102,241,0.15)' },
  { label: '第三方工具', value: thirdPartyCount.value, color: '#a78bfa', bg: 'rgba(168,85,247,0.04)', border: 'rgba(168,85,247,0.15)' },
  { label: '已启用', value: toolStore.enabledTools.length, color: '#34d399', bg: 'rgba(16,185,129,0.04)', border: 'rgba(16,185,129,0.15)' },
  { label: '已禁用', value: toolStore.disabledTools.length, color: '#fbbf24', bg: 'rgba(245,158,11,0.04)', border: 'rgba(245,158,11,0.15)' },
  { label: '不可用', value: toolStore.unavailableTools.length, color: '#94a3b8', bg: 'rgba(148,163,184,0.03)', border: 'rgba(148,163,184,0.15)' },
])

// -- Category counts for current source tab --
const categoryCounts = computed(() => {
  const src = sourceTab.value === 'all'
    ? toolStore.tools
    : toolStore.tools.filter((t) => t.source === sourceTab.value)
  const map: Partial<Record<ToolCategory, number>> = {}
  for (const t of src) {
    map[t.category] = (map[t.category] ?? 0) + 1
  }
  return map
})

// -- Filtered tools --
const filtered = computed(() => {
  return toolStore.tools.filter((t) => {
    if (sourceTab.value !== 'all' && t.source !== sourceTab.value) return false
    if (categoryFilter.value !== 'all' && t.category !== categoryFilter.value) return false
    if (statusFilter.value !== 'all' && t.status !== statusFilter.value) return false
    if (search.value) {
      const kw = search.value.toLowerCase()
      if (
        !t.displayName.toLowerCase().includes(kw) &&
        !t.name.toLowerCase().includes(kw) &&
        !t.tags.some((tag) => tag.toLowerCase().includes(kw))
      ) return false
    }
    return true
  })
})

// -- Category entries that have tools --
const activeCategories = computed(() => {
  return (Object.keys(categoryCounts.value) as ToolCategory[]).filter(
    (c) => categoryCounts.value[c] && categoryCounts.value[c]! > 0,
  )
})

// -- Source tabs --
const sourceTabs: { key: SourceTab; label: string; count: number }[] = [
  { key: 'all', label: '全部', count: toolStore.tools.length },
  { key: 'builtin', label: '内置工具', count: builtinCount.value },
  { key: 'third-party', label: '第三方工具', count: thirdPartyCount.value },
]

// -- Status filter buttons --
const statusFilters: { key: ToolStatus | 'all'; label: string }[] = [
  { key: 'all', label: '全部' },
  { key: 'enabled', label: '已启用' },
  { key: 'disabled', label: '已禁用' },
  { key: 'unavailable', label: '不可用' },
]

// -- Actions --
function openCreate() { editing.value = 'new' }

function openEdit(tool: Tool) {
  if (tool.source === 'builtin') return
  editing.value = tool
}

function closeDialog() { editing.value = null }

async function handleSave(data: ToolCreateRequest) {
  try {
    if (editing.value && editing.value !== 'new') {
      await toolStore.editTool(editing.value.id, data)
      ElMessage.success('工具已更新')
    } else {
      await toolStore.addTool(data)
      ElMessage.success('工具创建成功')
    }
    closeDialog()
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
  }
}

async function handleToggle(id: string) {
  const tool = toolStore.tools.find((t) => t.id === id)
  if (!tool) return
  try {
    const nextEnabled = tool.status !== 'enabled'
    await toolStore.toggleToolEnabled(id, nextEnabled)
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
  }
}

async function handleDelete(id: string) {
  const tool = toolStore.tools.find((t) => t.id === id)
  if (!tool) return
  deleting.value = tool
  try {
    await ElMessageBox.confirm(
      `确定要删除工具"${tool.displayName}"吗？`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    await toolStore.removeTool(id)
    ElMessage.success('工具已删除')
  } catch (err: unknown) {
    if (err instanceof Error && err.message !== 'cancel') {
      ElMessage.error(err.message)
    }
  } finally {
    deleting.value = null
  }
}

function openDetail(tool: Tool) { detail.value = tool }
function closeDetail() { detail.value = null }

// -- Scroll pagination --
const pageRef = ref<HTMLElement | null>(null)

function handleScroll() {
  const el = pageRef.value
  if (!el || toolStore.loadingMore || !toolStore.hasMore) return
  const { scrollTop, scrollHeight, clientHeight } = el
  if (scrollTop + clientHeight >= scrollHeight - 120) {
    toolStore.loadMore()
  }
}

onMounted(() => {
  toolStore.fetchTools()
  const el = pageRef.value
  if (el) el.addEventListener('scroll', handleScroll, { passive: true })
})

onUnmounted(() => {
  const el = pageRef.value
  if (el) el.removeEventListener('scroll', handleScroll)
})
</script>

<template>
  <div ref="pageRef" class="tools-page">
    <!-- ── Header ── -->
    <div class="page-header">
      <div class="page-header__info">
        <h1 class="page-title">工具</h1>
        <p class="page-sub">内置工具与第三方工具统一管理</p>
      </div>
      <el-button type="primary" size="large" @click="openCreate">
        <Plus :size="16" class="btn-icon" />
        添加第三方工具
      </el-button>
    </div>

    <!-- ── Stats ── -->
    <div class="stats-bar">
      <div
        v-for="s in statCards"
        :key="s.label"
        class="stat-card"
        :style="{ background: s.bg, borderColor: s.border }"
      >
        <span class="stat-label">{{ s.label }}</span>
        <span class="stat-value" :style="{ color: s.color }">{{ s.value }}</span>
      </div>
    </div>

    <!-- ── Source Tabs ── -->
    <div class="source-tabs">
      <button
        v-for="tab in sourceTabs"
        :key="tab.key"
        class="source-tab"
        :class="{ active: sourceTab === tab.key }"
        @click="sourceTab = tab.key; categoryFilter = 'all'"
      >
        {{ tab.label }}
        <span class="source-tab__count">{{ tab.count }}</span>
      </button>
    </div>

    <!-- ── Filters + Search ── -->
    <div class="filters-row">
      <!-- Search -->
      <div class="search-box">
        <Search :size="14" class="search-icon" />
        <input
          v-model="search"
          type="text"
          class="search-input"
          placeholder="搜索工具名称、标签…"
        />
      </div>

      <!-- Category filter chips -->
      <div class="category-chips">
        <button
          class="chip-btn"
          :class="{ active: categoryFilter === 'all' }"
          @click="categoryFilter = 'all'"
        >
          全部分类
        </button>
        <button
          v-for="c in activeCategories"
          :key="c"
          class="chip-btn"
          :class="{ active: categoryFilter === c }"
          :style="categoryFilter === c
            ? { background: CATEGORY_META[c].bg, color: CATEGORY_META[c].color, borderColor: CATEGORY_META[c].border }
            : {}"
          @click="categoryFilter = categoryFilter === c ? 'all' : c"
        >
          <span>{{ CATEGORY_META[c].label }}</span>
          <span class="chip-count">{{ categoryCounts[c] }}</span>
        </button>
      </div>

      <!-- Status filter -->
      <div class="status-filters">
        <button
          v-for="sf in statusFilters"
          :key="sf.key"
          class="status-btn"
          :class="{ active: statusFilter === sf.key }"
          @click="statusFilter = sf.key"
        >
          {{ sf.label }}
        </button>
      </div>
    </div>

    <!-- ── Tool Grid ── -->
    <div class="section-header">
      <span class="section-title">工具列表</span>
      <span class="section-count">共 {{ filtered.length }} 个工具</span>
    </div>

    <div v-loading="toolStore.loading" class="tools-content">
      <!-- Loading -->
      <div v-if="toolStore.loading" class="tools-grid">
        <div v-for="i in 6" :key="i" class="skeleton-card">
          <el-skeleton :rows="3" animated />
        </div>
      </div>

      <!-- Empty -->
      <el-empty
        v-else-if="filtered.length === 0"
        :description="sourceTab !== 'all' || categoryFilter !== 'all' || search ? '当前筛选条件下没有匹配的工具' : '暂无工具'"
      >
        <el-button v-if="sourceTab === 'all' && !search" type="primary" @click="openCreate">
          添加第三方工具
        </el-button>
      </el-empty>

      <!-- Grid -->
      <div v-else class="tools-grid">
        <ToolCard
          v-for="tool in filtered"
          :key="tool.id"
          :tool="tool"
          @edit="openEdit"
          @delete="handleDelete"
          @toggle="handleToggle"
          @detail="openDetail"
        />
      </div>
    </div>

    <!-- Load more -->
    <div v-if="!toolStore.loading && filtered.length > 0" class="load-more">
      <div v-if="toolStore.loadingMore" class="load-more__loading">
        <el-skeleton :rows="1" animated />
        <span class="load-more__text">加载更多工具…</span>
      </div>
      <div v-else-if="toolStore.hasMore" class="load-more__hint">
        向下滚动加载更多
      </div>
      <div v-else class="load-more__end">
        — 已展示全部 {{ toolStore.total }} 个工具 —
      </div>
    </div>

    <!-- ── Dialogs ── -->
    <ToolDialog
      :visible="editing !== null"
      :tool="editing !== 'new' ? editing : null"
      @close="closeDialog"
      @save="handleSave"
    />

    <ToolDetailDrawer
      v-if="detail"
      :tool="detail"
      @close="closeDetail"
      @edit="(t: Tool) => { closeDetail(); openEdit(t) }"
      @delete="(id: string) => { closeDetail(); handleDelete(id) }"
    />
  </div>
</template>

<style scoped>
.tools-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px 32px;
  height: 100%;
  overflow-y: auto;
  background: var(--surface-primary);
}

/* Page Header */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-header__info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.page-title {
  font-size: 28px;
  font-weight: var(--font-weight-bold);
  background: linear-gradient(90deg, #818cf8, #a78bfa, #60a5fa);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
  line-height: 1.3;
}

.page-sub {
  font-size: var(--font-size-base);
  color: var(--foreground-muted);
  margin: 0;
}

.btn-icon { margin-right: 6px; }

/* Stats Bar */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 18px 20px;
  border-radius: 14px;
  border: 1px solid;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}

.stat-value {
  font-size: 28px;
  font-weight: var(--font-weight-bold);
}

/* Source Tabs */
.source-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  width: fit-content;
}

.source-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: var(--foreground-secondary);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  font-family: var(--font-family-base);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.source-tab:hover { color: var(--color-text-primary); }

.source-tab.active {
  background: var(--accent-primary);
  color: #fff;
  box-shadow: 0px 2px 8px rgba(59, 130, 246, 0.3);
}

.source-tab__count {
  font-size: var(--font-size-xs);
  opacity: 0.7;
}

/* Filters Row */
.filters-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

/* Search */
.search-box {
  position: relative;
  flex-shrink: 0;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--foreground-muted);
  pointer-events: none;
}

.search-input {
  width: 240px;
  padding: 7px 12px 7px 30px;
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-input);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  font-family: var(--font-family-base);
  outline: none;
}

.search-input::placeholder { color: var(--foreground-muted); }
.search-input:focus { border-color: var(--accent-primary); }

/* Category chips */
.category-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.chip-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border: 1px solid transparent;
  border-radius: var(--radius-lg);
  background: var(--surface-secondary);
  color: var(--foreground-secondary);
  font-size: var(--font-size-sm);
  font-family: var(--font-family-base);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.chip-btn:hover { color: var(--color-text-primary); }

.chip-btn.active {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}

.chip-count {
  opacity: 0.6;
  font-size: 11px;
}

/* Status filters */
.status-filters {
  display: flex;
  gap: 2px;
  padding: 3px;
  background: var(--surface-secondary);
  border-radius: var(--radius-lg);
  margin-left: auto;
}

.status-btn {
  padding: 4px 12px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--foreground-secondary);
  font-size: var(--font-size-sm);
  font-family: var(--font-family-base);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.status-btn:hover { color: var(--color-text-primary); }

.status-btn.active {
  background: var(--accent-primary);
  color: #fff;
}

/* Section */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 15px;
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.section-count {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}

/* Tools Grid */
.tools-content {
  min-height: 200px;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 14px;
}

.skeleton-card {
  padding: 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
}

/* Load more */
.load-more {
  display: flex;
  justify-content: center;
  padding: 16px 0 8px;
}

.load-more__loading {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  max-width: 360px;
}

.load-more__text {
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
  white-space: nowrap;
}

.load-more__hint {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.load-more__end {
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
  opacity: 0.7;
}
</style>
