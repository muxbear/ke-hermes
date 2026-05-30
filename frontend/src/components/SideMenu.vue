<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  PanelLeftClose,
  PanelLeftOpen,
  ChevronDown,
  MessageSquare,
  MessagesSquare,
  LayoutDashboard,
  Server,
  Timer,
  BarChart3,
  Bot,
  Zap,
  Network,
  CloudMoon,
  FileText,
  Settings,
  Shield,
  Brain,
  Search,
  X,
} from 'lucide-vue-next'
import type { Component } from 'vue'
import { useUiStore } from '@/stores/ui'

const router = useRouter()
const route = useRoute()
const uiStore = useUiStore()

interface MenuItem {
  icon: Component
  text: string
  route?: string
  pinyin?: string
}

interface MenuGroup {
  label: string
  items: MenuItem[]
}

interface SearchResult {
  group: string
  item: MenuItem
}

const collapsedGroups = ref<Set<string>>(new Set())
const searchQuery = ref('')
const searchFocused = ref(false)
const searchRef = ref<HTMLDivElement | null>(null)
const searchInputRef = ref<HTMLInputElement | null>(null)

function toggleGroup(label: string) {
  if (collapsedGroups.value.has(label)) {
    collapsedGroups.value.delete(label)
  } else {
    collapsedGroups.value.add(label)
  }
  collapsedGroups.value = new Set(collapsedGroups.value)
}

function isItemActive(item: MenuItem): boolean {
  if (item.route) {
    if (item.route === '/') return route.path === '/'
    return route.path.startsWith(item.route)
  }
  return false
}

function handleItemClick(item: MenuItem) {
  if (item.route) {
    router.push(item.route)
  }
  searchQuery.value = ''
  searchFocused.value = false
}

function clearSearch() {
  searchQuery.value = ''
  searchFocused.value = false
  searchInputRef.value?.blur()
}

const menuGroups: MenuGroup[] = [
  {
    label: '聊天',
    items: [
      { icon: MessageSquare, text: '对话', route: '/', pinyin: 'duihua' },
    ],
  },
  {
    label: '控制',
    items: [
      { icon: LayoutDashboard, text: '概览', route: '/overview', pinyin: 'gailan' },
      { icon: Server, text: '实例', pinyin: 'shili' },
      { icon: MessagesSquare, text: '会话', pinyin: 'huihua' },
      { icon: Brain, text: '模型', route: '/models', pinyin: 'moxing' },
      { icon: BarChart3, text: '使用情况', pinyin: 'shiyongqingkuang' },
      { icon: Timer, text: '定时任务', route: '/scheduled-tasks', pinyin: 'dingshirenwu' },
    ],
  },
  {
    label: '代理',
    items: [
      { icon: Bot, text: '代理', route: '/agents', pinyin: 'daili' },
      { icon: Zap, text: '技能', route: '/skills', pinyin: 'jineng' },
      { icon: Network, text: '节点', pinyin: 'jiedian' },
    ],
  },
  {
    label: 'MCP',
    items: [
      { icon: CloudMoon, text: 'MCP 广场', route: '/mcp', pinyin: 'mcpguangchang' },
      { icon: CloudMoon, text: 'MCP 管理', pinyin: 'mcpguanli' },
    ],
  },
  {
    label: '设置',
    items: [
      { icon: Settings, text: '配置', pinyin: 'peizhi' },
      { icon: FileText, text: '文档', pinyin: 'wendang' },
    ],
  },
  {
    label: '后台',
    items: [
      { icon: Shield, text: '后台', pinyin: 'houtai' },
    ],
  },
]

/* ---- Search ---- */
const searchResults = computed<SearchResult[]>(() => {
  if (!searchQuery.value.trim()) return []

  const q = searchQuery.value.trim().toLowerCase()
  const results: SearchResult[] = []

  // Also allow matching on abbreviations: e.g. "rw" → 任务, "mr" → 模型
  for (const group of menuGroups) {
    for (const item of group.items) {
      if (!item.route) continue
      const haystack = [
        item.text.toLowerCase(),
        item.pinyin?.toLowerCase() ?? '',
        // first-letter abbreviation: 定时任务 → dsrw, 模型 → mx
        (item.pinyin ?? '').replace(/[a-z]+/g, (m) => m[0]),
      ].join(' ')

      if (haystack.includes(q)) {
        results.push({ group: group.label, item })
      }
    }
  }
  return results
})

const showDropdown = computed(() => searchFocused.value && searchResults.value.length > 0)

// Auto-expand matched groups
watch(searchResults, (results) => {
  if (!searchQuery.value.trim()) return
  const matchedGroups = new Set(results.map((r) => r.group))
  for (const g of matchedGroups) {
    collapsedGroups.value.delete(g)
  }
  collapsedGroups.value = new Set(collapsedGroups.value)
})

// Click outside to close dropdown
function handleClickOutside(e: MouseEvent) {
  if (searchRef.value && !searchRef.value.contains(e.target as HTMLElement)) {
    searchFocused.value = false
  }
}

watch(searchFocused, (focused) => {
  if (focused) {
    document.addEventListener('click', handleClickOutside)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <aside class="sidebar" :class="{ collapsed: uiStore.sidebarCollapsed }">
    <div class="side-top">
      <span class="logo">ke-hermes</span>
      <button class="collapse-btn" @click="uiStore.toggleSidebar">
        <PanelLeftClose v-if="!uiStore.sidebarCollapsed" :size="14" />
        <PanelLeftOpen v-else :size="14" />
      </button>
    </div>

    <!-- Search box -->
    <div
      ref="searchRef"
      class="search-wrap"
      :class="{ collapsed: uiStore.sidebarCollapsed }"
    >
      <div class="search-box" :class="{ focused: searchFocused }">
        <Search :size="14" class="search-icon" />
        <input
          ref="searchInputRef"
          v-model="searchQuery"
          type="text"
          placeholder="搜索菜单…"
          class="search-input"
          @focus="searchFocused = true"
        />
        <button
          v-if="searchQuery"
          class="search-clear-btn"
          @click.stop="clearSearch"
        >
          <X :size="12" />
        </button>
      </div>

      <!-- Results dropdown -->
      <Transition name="dropdown">
        <div v-if="showDropdown" class="search-dropdown">
          <div class="search-dropdown-header">
            {{ searchResults.length }} 个匹配菜单
          </div>
          <button
            v-for="result in searchResults"
            :key="`${result.group}-${result.item.text}`"
            class="search-result-item"
            @click="handleItemClick(result.item)"
          >
            <component :is="result.item.icon" :size="14" class="result-icon" />
            <div class="result-text">
              <span class="result-group">{{ result.group }}</span>
              <span class="result-sep">&rsaquo;</span>
              <span class="result-label">{{ result.item.text }}</span>
            </div>
            <ChevronDown :size="12" class="result-arrow" />
          </button>
        </div>
      </Transition>
    </div>

    <div class="menu-wrap">
      <div v-for="group in menuGroups" :key="group.label" class="menu-group">
        <div
          class="menu-label"
          :class="{ collapsed: collapsedGroups.has(group.label) }"
          @click="toggleGroup(group.label)"
        >
          <ChevronDown :size="12" class="chevron" />
          <span>{{ group.label }}</span>
        </div>
        <div
          v-show="!collapsedGroups.has(group.label)"
          v-for="item in group.items"
          :key="item.text"
          class="menu-item"
          :class="{ active: isItemActive(item) }"
          @click="handleItemClick(item)"
        >
          <component :is="item.icon" :size="16" />
          <span class="menu-text">{{ item.text }}</span>
        </div>
      </div>
    </div>

    <div class="ver-row">v0.0.1</div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 12px;
  background: var(--surface-card);
  border-right: 1px solid var(--border-subtle);
  overflow: hidden;
  transition: width var(--transition-duration) ease,
              min-width var(--transition-duration) ease;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
  min-width: var(--sidebar-collapsed-width);
}

.side-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  flex-shrink: 0;
}

.sidebar.collapsed .side-top {
  justify-content: center;
  padding-bottom: 0;
}

.logo {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--accent-primary);
  white-space: nowrap;
  transition: opacity var(--transition-duration) ease;
}

.sidebar.collapsed .logo {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.collapse-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: none;
  background: var(--surface-secondary);
  color: var(--foreground-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: var(--border-subtle);
}

/* ---- Search ---- */
.search-wrap {
  position: relative;
  flex-shrink: 0;
  margin-bottom: 8px;
  transition: opacity var(--transition-duration) ease;
}

.search-wrap.collapsed {
  opacity: 0;
  height: 0;
  overflow: hidden;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: var(--radius-lg);
  background: var(--surface-secondary);
  border: 1px solid transparent;
  transition: border-color 0.15s ease, background 0.15s ease;
}

.search-box.focused {
  border-color: var(--accent-primary);
  background: var(--color-bg-input);
}

.search-icon {
  color: var(--foreground-muted);
  flex-shrink: 0;
}

.search-input {
  width: 100%;
  border: none;
  outline: none;
  background: none;
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
}

.search-input::placeholder {
  color: var(--foreground-muted);
}

.search-clear-btn {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: var(--foreground-muted);
  color: var(--surface-primary);
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
}

/* ---- Search Dropdown ---- */
.search-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--surface-card);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  z-index: 300;
  overflow: hidden;
  max-height: 320px;
  overflow-y: auto;
}

.search-dropdown-header {
  padding: 8px 10px;
  font-size: 10px;
  color: var(--foreground-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  border-bottom: 1px solid var(--border-subtle);
}

.search-result-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border: none;
  background: none;
  color: var(--foreground-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: background 0.1s ease;
}

.search-result-item:hover {
  background: rgba(59, 130, 246, 0.12);
  color: var(--foreground-primary);
}

.result-icon {
  flex-shrink: 0;
  color: var(--foreground-muted);
}

.result-text {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.result-group {
  color: var(--foreground-muted);
  font-size: var(--font-size-xs);
  flex-shrink: 0;
}

.result-sep {
  color: var(--foreground-muted);
  flex-shrink: 0;
}

.result-label {
  color: var(--foreground-primary);
  white-space: nowrap;
}

.result-arrow {
  color: var(--foreground-muted);
  flex-shrink: 0;
  transform: rotate(-90deg);
}

/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.12s ease, transform 0.12s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* ---- Menu ---- */
.menu-wrap {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 2px;
}

.sidebar.collapsed .menu-wrap {
  gap: 8px;
}

.menu-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sidebar.collapsed .menu-group {
  gap: 2px;
}

.menu-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-bold);
  color: var(--foreground-muted);
  letter-spacing: 1px;
  white-space: nowrap;
  cursor: pointer;
  user-select: none;
  padding: 4px 0;
  transition: opacity var(--transition-duration) ease;
}

.menu-label:hover {
  color: var(--foreground-primary);
}

.menu-label .chevron {
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.menu-label.collapsed .chevron {
  transform: rotate(-90deg);
}

.sidebar.collapsed .menu-label {
  opacity: 0;
  height: 0;
  overflow: hidden;
  padding: 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  color: var(--foreground-secondary);
  cursor: pointer;
  transition: background 0.15s ease;
}

.sidebar.collapsed .menu-item {
  justify-content: center;
  padding: 8px;
  gap: 0;
}

.menu-item:hover {
  background: var(--surface-secondary);
}

.menu-item.active {
  background: rgba(59, 130, 246, 0.22);
  color: var(--foreground-primary);
}

.menu-item.active :deep(svg) {
  color: var(--color-accent);
}

.menu-text {
  white-space: nowrap;
  transition: opacity var(--transition-duration) ease;
}

.sidebar.collapsed .menu-text {
  opacity: 0;
  width: 0;
  overflow: hidden;
}

.ver-row {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  padding-top: 8px;
  white-space: nowrap;
  flex-shrink: 0;
  transition: opacity var(--transition-duration) ease;
}

.sidebar.collapsed .ver-row {
  opacity: 0;
  height: 0;
  overflow: hidden;
  padding: 0;
}
</style>
