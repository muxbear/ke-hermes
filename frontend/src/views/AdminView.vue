<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  Settings,
  LayoutList,
  Bell,
  CreditCard,
  Users,
  ShieldCheck,
  Key,
  ScrollText,
  Cpu,
  ToggleRight,
  Puzzle,
  Plug,
  DatabaseBackup,
  Code2,
  HelpCircle,
  Activity,
} from 'lucide-vue-next'
import type { Component } from 'vue'
import { useAdminStore } from '@/stores/admin'
import AdminTile from '@/components/admin/AdminTile.vue'
import SystemInfoCard from '@/components/admin/SystemInfoCard.vue'
import UpdateLogCard from '@/components/admin/UpdateLogCard.vue'
import PatchUpdateCard from '@/components/admin/PatchUpdateCard.vue'
import RecommendedResourcesCard from '@/components/admin/RecommendedResourcesCard.vue'

const store = useAdminStore()
const router = useRouter()

onMounted(() => {
  store.fetchAll()
})

const iconMap: Record<string, Component> = {
  Settings,
  LayoutList,
  Bell,
  CreditCard,
  Users,
  ShieldCheck,
  Key,
  ScrollText,
  Cpu,
  ToggleRight,
  Puzzle,
  Plug,
  DatabaseBackup,
  Code2,
  Activity,
  HelpCircle,
}

const gradients: Record<string, string> = {
  'from-blue-500/20 to-blue-500/5': 'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(59,130,246,0.05))',
  'from-cyan-500/20 to-cyan-500/5': 'linear-gradient(135deg, rgba(6,182,212,0.2), rgba(6,182,212,0.05))',
  'from-amber-500/20 to-amber-500/5': 'linear-gradient(135deg, rgba(245,158,11,0.2), rgba(245,158,11,0.05))',
  'from-emerald-500/20 to-emerald-500/5': 'linear-gradient(135deg, rgba(16,185,129,0.2), rgba(16,185,129,0.05))',
  'from-violet-500/20 to-violet-500/5': 'linear-gradient(135deg, rgba(139,92,246,0.2), rgba(139,92,246,0.05))',
  'from-fuchsia-500/20 to-fuchsia-500/5': 'linear-gradient(135deg, rgba(217,70,239,0.2), rgba(217,70,239,0.05))',
  'from-indigo-500/20 to-indigo-500/5': 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(99,102,241,0.05))',
  'from-rose-500/20 to-rose-500/5': 'linear-gradient(135deg, rgba(244,63,94,0.2), rgba(244,63,94,0.05))',
  'from-blue-500/20 to-purple-500/10': 'linear-gradient(135deg, rgba(59,130,246,0.2), rgba(168,85,247,0.1))',
  'from-sky-500/20 to-sky-500/5': 'linear-gradient(135deg, rgba(14,165,233,0.2), rgba(14,165,233,0.05))',
  'from-teal-500/20 to-teal-500/5': 'linear-gradient(135deg, rgba(20,184,166,0.2), rgba(20,184,166,0.05))',
  'from-orange-500/20 to-orange-500/5': 'linear-gradient(135deg, rgba(249,115,22,0.2), rgba(249,115,22,0.05))',
  'from-lime-500/20 to-lime-500/5': 'linear-gradient(135deg, rgba(132,204,22,0.2), rgba(132,204,22,0.05))',
  'from-pink-500/20 to-pink-500/5': 'linear-gradient(135deg, rgba(236,72,153,0.2), rgba(236,72,153,0.05))',
}

const groups = [
  { key: 'basic' as const, label: '基础设置' },
  { key: 'people' as const, label: '人员与权限' },
  { key: 'extension' as const, label: '扩展与集成' },
]

const groupTiles = computed(() =>
  groups.map((g) => ({
    ...g,
    tiles: store.tiles.filter((t) => t.group === g.key),
  })),
)

function getTileIcon(name: string): Component {
  return iconMap[name] || HelpCircle
}

function handleTileClick(tile: { id: string; route?: string }) {
  if (tile.route) {
    router.push(tile.route)
  }
}
</script>

<template>
  <div class="admin-page">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">管理控制台</h1>
        <p class="page-subtitle">管理员控制台 · 集中管理系统、人员、扩展与集成</p>
      </div>
      <div class="header-right">
        <button class="manual-btn">
          <HelpCircle :size="16" />
          管理手册
        </button>
      </div>
    </div>

    <div v-if="store.loading" class="loading-state">
      <span>加载中...</span>
    </div>

    <div v-else class="admin-content">
      <div class="tiles-area">
        <section v-for="group in groupTiles" :key="group.key" class="tile-group">
          <div class="group-header">
            <h2 class="group-label">{{ group.label }}</h2>
            <div class="group-divider" />
          </div>
          <div class="tile-grid">
            <AdminTile
              v-for="tile in group.tiles"
              :key="tile.id"
              :icon="getTileIcon(tile.icon)"
              :title="tile.title"
              :description="tile.description"
              :gradient="gradients[tile.gradient] || ''"
              :route="tile.route"
            />
          </div>
        </section>
      </div>

      <aside class="sidebar-area">
        <SystemInfoCard v-if="store.stats" :stats="store.stats" />
        <UpdateLogCard :logs="store.updateLogs" />
        <PatchUpdateCard />
        <RecommendedResourcesCard />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.admin-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 24px 0;
  flex-shrink: 0;
}
.page-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0;
}
.page-subtitle {
  margin-top: 4px;
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
}
.manual-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.manual-btn:hover {
  background: rgba(30, 41, 59, 0.8);
}
.loading-state {
  padding: 48px;
  text-align: center;
  color: var(--foreground-muted);
}
.admin-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 24px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}
@media (min-width: 1280px) {
  .admin-content {
    grid-template-columns: 1fr 340px;
  }
}
.tiles-area {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.tile-group {
  display: flex;
  flex-direction: column;
}
.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.group-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-secondary);
  margin: 0;
  flex-shrink: 0;
}
.group-divider {
  flex: 1;
  height: 1px;
  background: var(--border-subtle);
}
.tile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}
.sidebar-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
@media (max-width: 1279px) {
  .sidebar-area {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
  }
}
</style>
