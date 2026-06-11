<script setup lang="ts">
import { ChevronRight } from 'lucide-vue-next'

const resources = [
  { title: 'API 接口文档', url: '#' },
  { title: '智能体最佳实践', url: '#' },
  { title: '部署与运维手册', url: '#' },
]
</script>

<template>
  <div class="resources-card">
    <span class="card-title">推荐资源</span>
    <ul class="resource-list">
      <li v-for="r in resources" :key="r.title" class="resource-item">
        <span>{{ r.title }}</span>
        <ChevronRight :size="16" />
      </li>
    </ul>
  </div>
</template>

<style scoped>
.resources-card {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 20px;
}
.card-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
}
.resource-list {
  list-style: none;
  margin: 12px 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.resource-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  cursor: pointer;
  padding: 4px 0;
  transition: color var(--transition-fast);
}
.resource-item:hover {
  color: var(--accent-primary);
}
</style>
