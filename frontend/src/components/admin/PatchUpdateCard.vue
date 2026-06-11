<script setup lang="ts">
import { Download } from 'lucide-vue-next'
</script>

<template>
  <div class="patch-card">
    <div class="card-header">
      <span class="card-title">补丁更新</span>
      <button class="download-btn">
        <Download :size="16" />
      </button>
    </div>
    <p class="patch-desc">
      如果当前版本运行后出现严重影响使用的问题，我们会第一时间以补丁的形式发布。
    </p>
  </div>
</template>

<style scoped>
.patch-card {
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
.download-btn {
  background: none;
  border: none;
  color: var(--foreground-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}
.download-btn:hover {
  background: rgba(30, 41, 59, 0.8);
  color: var(--accent-primary);
}
.patch-desc {
  margin-top: 8px;
  font-size: var(--font-size-xs);
  line-height: 1.6;
  color: var(--foreground-muted);
}
</style>
