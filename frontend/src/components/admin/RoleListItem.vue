<script setup lang="ts">
import { Shield, Sparkles, Lock } from 'lucide-vue-next'
import type { RoleDef } from '@/types/admin'
import { isSuperAdmin } from '@/services/adminApi'

defineProps<{
  role: RoleDef
  isActive: boolean
}>()

defineEmits<{
  select: []
}>()
</script>

<template>
  <div
    class="role-item"
    :class="{ 'is-active': isActive }"
    @click="$emit('select')"
  >
    <div class="role-top">
      <div class="role-icon" :class="role.color">
        <Sparkles v-if="isSuperAdmin(role.key)" :size="16" />
        <Shield v-else :size="16" />
      </div>
      <div class="role-info">
        <div class="role-name">
          {{ role.name }}
          <Lock v-if="role.isBuiltin" :size="12" class="builtin-lock" />
        </div>
        <div class="role-count">{{ role.userCount }} 名成员</div>
      </div>
      <div v-if="isActive" class="active-dot" />
    </div>
    <p class="role-desc">{{ role.description }}</p>
  </div>
</template>

<style scoped>
.role-item {
  padding: 12px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: border-color var(--transition-fast), background var(--transition-fast);
  background: var(--surface-card);
}
.role-item:hover {
  border-color: var(--foreground-muted);
}
.role-item.is-active {
  border-color: rgba(59, 130, 246, 0.5);
  background: rgba(37, 99, 235, 0.1);
}
.role-top {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}
.role-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.role-icon.from-red-500\/20 { background-image: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.05)); color: #fca5a5; }
.role-icon.from-blue-500\/20 { background-image: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(59,130,246,0.05)); color: #93c5fd; }
.role-icon.from-emerald-500\/20 { background-image: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(16,185,129,0.05)); color: #6ee7b7; }
.role-icon.from-slate-500\/20 { background-image: linear-gradient(135deg, rgba(100,116,139,0.2), rgba(100,116,139,0.05)); color: #94a3b8; }
.role-icon.from-zinc-500\/20 { background-image: linear-gradient(135deg, rgba(113,113,122,0.2), rgba(113,113,122,0.05)); color: #a1a1aa; }
.role-icon.from-teal-500\/20 { background-image: linear-gradient(135deg, rgba(20,184,166,0.2), rgba(20,184,166,0.05)); color: #5eead4; }
.role-info {
  flex: 1;
  min-width: 0;
}
.role-name {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
}
.builtin-lock {
  color: var(--foreground-muted);
}
.role-count {
  font-size: 11px;
  color: var(--foreground-muted);
}
.active-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  background: var(--accent-primary);
  flex-shrink: 0;
  margin-top: 4px;
}
.role-desc {
  margin-top: 10px;
  font-size: 11px;
  line-height: 1.5;
  color: var(--foreground-muted);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
