<script setup lang="ts">
import { ref } from 'vue'
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
}

interface MenuGroup {
  label: string
  items: MenuItem[]
}

const collapsedGroups = ref<Set<string>>(new Set())

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
}

const menuGroups: MenuGroup[] = [
  {
    label: '聊天',
    items: [
      { icon: MessageSquare, text: '对话', route: '/' },
    ],
  },
  {
    label: '控制',
    items: [
      { icon: LayoutDashboard, text: '概览', route: '/overview' },
      { icon: Server, text: '实例' },
      { icon: MessagesSquare, text: '会话' },
      { icon: BarChart3, text: '使用情况' },
      { icon: Timer, text: '定时任务' },
    ],
  },
  {
    label: '代理',
    items: [
      { icon: Bot, text: '代理', route: '/agents' },
      { icon: Zap, text: '技能 Hub', route: '/skills' },
      { icon: Network, text: '节点' },
    ],
  },
  {
    label: 'MCP',
    items: [
      { icon: CloudMoon, text: 'MCP 广场', route: '/mcp' },      
      { icon: CloudMoon, text: 'MCP 管理' },      
    ],
  },
  {
    label: '设置',
    items: [
      { icon: Settings, text: '配置' },
      { icon: FileText, text: '文档' },
    ],
  },
  {
    label: '后台',
    items: [
      { icon: Shield, text: '后台' },
    ],
  },
]
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

    <div class="side-spacer" />

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
  gap: 20px;
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
  gap: 12px;
}

.side-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 16px;
}

.sidebar.collapsed .side-top {
  justify-content: center;
  padding-bottom: 12px;
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

.menu-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
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

.side-spacer {
  flex: 1;
}

.ver-row {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  padding-top: 12px;
  white-space: nowrap;
  transition: opacity var(--transition-duration) ease;
}

.sidebar.collapsed .ver-row {
  opacity: 0;
  height: 0;
  overflow: hidden;
  padding: 0;
}
</style>