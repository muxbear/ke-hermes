<script setup>
import {
  PanelLeftClose,
  PanelLeftOpen,
  MessageSquare,
  Timer,
  Bot,
  Zap,
  Settings,
} from 'lucide-vue-next'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()

const menuGroups = [
  {
    label: '聊天',
    items: [
      { icon: MessageSquare, text: '对话', active: true },
    ],
  },
  {
    label: '控制',
    items: [
      { icon: Timer, text: '定时任务', active: false },
    ],
  },
  {
    label: '代理',
    items: [
      { icon: Bot, text: '代理列表', active: false },
      { icon: Zap, text: 'Skills', active: false },
    ],
  },
  {
    label: '设置',
    items: [
      { icon: Settings, text: '配置', active: false },
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
        <span class="menu-label">{{ group.label }}</span>
        <div
          v-for="item in group.items"
          :key="item.text"
          class="menu-item"
          :class="{ active: item.active }"
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
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-bold);
  color: var(--foreground-muted);
  letter-spacing: 1px;
  white-space: nowrap;
  transition: opacity var(--transition-duration) ease;
}

.sidebar.collapsed .menu-label {
  opacity: 0;
  height: 0;
  overflow: hidden;
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
  background: var(--accent-primary-light);
  color: var(--accent-primary);
}

.menu-item.active :deep(svg) {
  color: var(--accent-primary);
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