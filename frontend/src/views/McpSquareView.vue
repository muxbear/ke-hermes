<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, ArrowUpDown, Plus } from 'lucide-vue-next'
import { useMcpStore } from '@/stores/mcp'
import type { McpTool } from '@/types/mcp'
import { MCP_CATEGORY_FILTERS } from '@/types/mcp'
import McpCard from '@/components/mcp/McpCard.vue'

const router = useRouter()
const mcpStore = useMcpStore()

const searchQuery = ref('')
const activeCategory = ref('')
const sortBy = ref('popular')

const filteredTools = computed(() => {
  let result = mcpStore.tools
  if (activeCategory.value) {
    result = result.filter((t) => t.category === activeCategory.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(
      (t) =>
        t.name.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        t.tags.some((tag) => tag.toLowerCase().includes(q)),
    )
  }
  return result
})

const sortOptions = [
  { key: 'popular', label: '最多安装' },
  { key: 'rating', label: '最高评分' },
  { key: 'recent', label: '最近更新' },
]

function handleToolClick(tool: McpTool) {
  router.push({ name: 'mcp-detail', params: { id: tool.id } })
}

function handleInstall(tool: McpTool) {
  if (tool.installed) {
    mcpStore.uninstallTool(tool.id)
  } else {
    mcpStore.installTool(tool.id)
  }
}

onMounted(() => {
  mcpStore.fetchTools()
})

function handleCreate() {
  // TODO: open create MCP dialog
}
</script>

<template>
  <div class="mcp-square">
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header__info">
        <h1>MCP 广场</h1>
        <p>发现并连接强大的 MCP 工具，扩展 AI 智能体的能力边界</p>
      </div>
      <el-button type="primary" size="large" @click="handleCreate">
        <Plus :size="16" class="btn-icon" />
        创建 MCP
      </el-button>
    </div>

    <!-- Search Bar -->
    <div class="search-bar">
      <Search :size="18" class="search-icon" />
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索 MCP 工具..."
        class="search-input"
      />
    </div>

    <!-- Stats Bar -->
    <div class="stats-bar">
      <div class="stat-card">
        <div class="stat-icon stat-icon--blue">
          <span class="stat-icon-text">📦</span>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ mcpStore.tools.length }}</span>
          <span class="stat-label">MCP 总数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--green">
          <span class="stat-icon-text">✅</span>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ mcpStore.installedTools.length }}</span>
          <span class="stat-label">已安装</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--orange">
          <span class="stat-icon-text">🔥</span>
        </div>
        <div class="stat-info">
          <span class="stat-value">156</span>
          <span class="stat-label">本周热门</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--purple">
          <span class="stat-icon-text">🔄</span>
        </div>
        <div class="stat-info">
          <span class="stat-value">34</span>
          <span class="stat-label">最近更新</span>
        </div>
      </div>
    </div>

    <!-- Category Filter -->
    <div class="category-filter">
      <button
        v-for="cat in MCP_CATEGORY_FILTERS"
        :key="cat.key"
        class="cat-btn"
        :class="{ active: activeCategory === cat.key }"
        @click="activeCategory = cat.key"
      >
        {{ cat.label }}
      </button>
    </div>

    <!-- Section Header -->
    <div class="section-header">
      <span class="section-title">热门 MCP</span>
      <div class="sort-dropdown">
        <ArrowUpDown :size="14" />
        <select v-model="sortBy" class="sort-select">
          <option
            v-for="opt in sortOptions"
            :key="opt.key"
            :value="opt.key"
          >
            {{ opt.label }}
          </option>
        </select>
      </div>
    </div>

    <!-- Error Banner -->
    <el-alert
      v-if="mcpStore.error"
      :title="mcpStore.error"
      type="warning"
      show-icon
      :closable="true"
    >
      <template #default>
        <el-button text size="small" @click="mcpStore.fetchTools()">重试</el-button>
      </template>
    </el-alert>

    <!-- Tools Grid -->
    <div v-loading="mcpStore.loading" class="tools-content">
      <div v-if="mcpStore.loading" class="tools-grid">
        <div v-for="i in 6" :key="i" class="skeleton-card">
          <el-skeleton :rows="3" animated />
        </div>
      </div>

      <el-empty
        v-else-if="filteredTools.length === 0"
        :description="
          searchQuery || activeCategory
            ? '没有找到匹配的 MCP 工具'
            : '暂无可用的 MCP 工具'
        "
      />

      <div v-else class="tools-grid">
        <McpCard
          v-for="tool in filteredTools"
          :key="tool.id"
          :tool="tool"
          @click="handleToolClick"
          @install="handleInstall"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.mcp-square {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px 32px;
  height: 100%;
  overflow-y: auto;
  background: var(--surface-primary);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-header__info h1 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
  margin: 0;
}

.page-header__info p {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  margin: 4px 0 0;
}

.btn-icon {
  margin-right: 6px;
}

/* Search Bar */
.search-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
}

.search-icon {
  color: var(--foreground-muted);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  background: none;
  outline: none;
  font-size: var(--font-size-md);
  color: var(--foreground-primary);
  caret-color: var(--accent-primary);
}

.search-input::placeholder {
  color: var(--foreground-muted);
}

/* Stats Bar */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon--blue { background: rgba(59, 130, 246, 0.15); }
.stat-icon--green { background: rgba(34, 197, 94, 0.15); }
.stat-icon--orange { background: rgba(245, 158, 11, 0.15); }
.stat-icon--purple { background: rgba(99, 102, 241, 0.15); }

.stat-icon-text {
  font-size: 20px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 22px;
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}

/* Category Filter */
.category-filter {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.cat-btn {
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid var(--border-subtle);
  background: var(--surface-card);
  color: var(--foreground-secondary);
  font-size: var(--font-size-base);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.cat-btn:hover {
  border-color: rgba(59, 130, 246, 0.3);
  color: var(--foreground-primary);
}

.cat-btn.active {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: #fff;
}

/* Section Header */
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

.sort-dropdown {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  color: var(--foreground-secondary);
}

.sort-select {
  background: none;
  border: none;
  outline: none;
  color: var(--foreground-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
}

.sort-select option {
  background: var(--surface-card);
  color: var(--foreground-primary);
}

/* Tools Grid */
.tools-content {
  min-height: 200px;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(388px, 1fr));
  gap: 16px;
}

.skeleton-card {
  padding: 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
}
</style>
