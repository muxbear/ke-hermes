<script setup lang="ts">
import type { SystemStats } from '@/types/admin'

const props = defineProps<{
  stats: SystemStats
}>()
</script>

<template>
  <div class="sys-info-card">
    <div class="card-header">
      <span class="card-label">系统信息</span>
    </div>
    <div class="version-row">
      <span class="version-number">{{ stats.version }}</span>
      <span class="version-badge">开发预览</span>
    </div>
    <p class="uptime-text">已稳定运行 {{ stats.uptime }} 天 · 许可证：内部使用</p>
    <div class="stats-grid">
      <div class="stat-item">
        <div class="stat-value">{{ stats.onlineInstances }}</div>
        <div class="stat-label">在线实例</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.registeredUsers }}</div>
        <div class="stat-label">注册用户</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{{ stats.activeAlerts }}</div>
        <div class="stat-label">告警</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sys-info-card {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(147, 51, 234, 0.06), transparent);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 20px;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}
.card-label {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}
.version-row {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  margin-top: 12px;
}
.version-number {
  font-size: 30px;
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
}
.version-badge {
  margin-bottom: 4px;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: rgba(37, 99, 235, 0.2);
  color: #93c5fd;
  font-size: var(--font-size-xs);
}
.uptime-text {
  margin-top: 4px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 16px;
}
.stat-item {
  background: rgba(15, 23, 42, 0.6);
  border-radius: var(--radius-md);
  padding: 8px;
  text-align: center;
}
.stat-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}
.stat-label {
  font-size: 11px;
  color: var(--foreground-muted);
}
</style>
