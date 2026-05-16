<script setup>
import { Search, Bell, CircleUser } from 'lucide-vue-next'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()
</script>

<template>
  <div class="topbar">
    <div class="topbar-left">
      <div class="search-box">
        <Search :size="16" class="search-icon" />
        <input
          v-model="uiStore.searchQuery"
          type="text"
          placeholder="搜索对话、技能、设置..."
        />
      </div>
    </div>
    <div class="topbar-right">
      <button class="action-btn">
        <Bell :size="18" />
      </button>
      <button class="action-btn">
        <CircleUser :size="18" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.topbar {
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: var(--surface-card);
  border-bottom: 1px solid var(--border-subtle);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 360px;
  padding: 6px 12px;
  border-radius: var(--radius-full);
  background: var(--surface-secondary);
}

.search-icon {
  color: var(--foreground-muted);
  flex-shrink: 0;
}

.search-box input {
  width: 100%;
  border: none;
  outline: none;
  background: none;
  font-size: var(--font-size-base);
  color: var(--foreground-primary);
}

.search-box input::placeholder {
  color: var(--foreground-muted);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  border: none;
  background: transparent;
  color: var(--foreground-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.action-btn:hover {
  background: var(--surface-secondary);
}
</style>