<script setup lang="ts">
import type { UpdateLogEntry } from '@/types/admin'

defineProps<{
  logs: UpdateLogEntry[]
}>()
</script>

<template>
  <div class="update-log-card">
    <div class="card-header">
      <span class="card-title">更新动态</span>
      <button class="more-btn">更多</button>
    </div>
    <ul class="log-list">
      <li v-for="log in logs" :key="log.title" class="log-item">
        <span class="log-badge" :class="{ 'is-primary': log.primary }">
          {{ log.tag }}
        </span>
        <div class="log-body">
          <p class="log-title">{{ log.title }}</p>
          <p class="log-date">{{ log.date }}</p>
        </div>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.update-log-card {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 20px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
}
.more-btn {
  background: none;
  border: none;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  cursor: pointer;
}
.more-btn:hover {
  color: var(--accent-primary);
}
.log-list {
  list-style: none;
  margin: 12px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.log-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.log-badge {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: rgba(30, 41, 59, 0.8);
  color: var(--foreground-muted);
  font-size: 11px;
  flex-shrink: 0;
}
.log-badge.is-primary {
  background: rgba(37, 99, 235, 0.2);
  color: #93c5fd;
}
.log-body {
  min-width: 0;
  flex: 1;
}
.log-title {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.log-date {
  font-size: 11px;
  color: var(--foreground-muted);
  margin-top: 2px;
}
</style>
