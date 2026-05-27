<script setup lang="ts">
import { computed } from 'vue'
import { Pencil, Trash2, CircleCheck, CircleAlert } from 'lucide-vue-next'
import type { Skill } from '@/types/skill'
import { CATEGORY_LABELS } from '@/types/skill'
import { getSkillIcon } from './iconMap'

const props = defineProps<{ skill: Skill }>()

const emit = defineEmits<{
  (e: 'edit', skill: Skill): void
  (e: 'delete', skill: Skill): void
  (e: 'toggle', skill: Skill): void
}>()

const iconComponent = computed(() => getSkillIcon(props.skill.icon))
const categoryLabel = computed(() => CATEGORY_LABELS[props.skill.category] || props.skill.category)

interface ValidationError {
  field: string
  message: string
}

const validationErrors = computed<ValidationError[]>(() => {
  if (!props.skill.validation_errors) return []
  try {
    return JSON.parse(props.skill.validation_errors)
  } catch {
    return []
  }
})

const validationTooltip = computed(() => {
  if (validationErrors.value.length === 0) return ''
  return validationErrors.value.map(e => `[${e.field}] ${e.message}`).join('\n')
})
</script>

<template>
  <div class="skill-card">
    <div class="card-header">
      <div class="card-header__left">
        <div class="icon-box">
          <component :is="iconComponent" :size="18" />
        </div>
        <span class="skill-name">{{ skill.name }}</span>
        <el-tag v-if="skill.is_builtin" size="small" type="info">内置</el-tag>
        <!-- 校验状态指示 -->
        <el-tooltip
          v-if="!skill.valid && validationTooltip"
          :content="validationTooltip"
          placement="top"
          :show-after="300"
        >
          <CircleAlert :size="16" class="validation-badge validation-badge--error" />
        </el-tooltip>
        <CircleCheck
          v-else-if="skill.valid"
          :size="16"
          class="validation-badge validation-badge--success"
        />
      </div>
      <el-switch
        :model-value="skill.enabled"
        size="small"
        @change="emit('toggle', skill)"
      />
    </div>

    <p class="card-description">
      {{ skill.description || '暂无描述' }}
    </p>

    <div class="card-footer">
      <el-tag size="small" type="info">{{ categoryLabel }}</el-tag>
      <div v-if="!skill.is_builtin" class="card-actions">
        <el-button text size="small" @click.stop="emit('edit', skill)">
          <Pencil :size="14" />
        </el-button>
        <el-button text size="small" @click.stop="emit('delete', skill)">
          <Trash2 :size="14" />
        </el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.skill-card {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  transition: border-color var(--transition-fast);
}

.skill-card:hover {
  border-color: rgba(59, 130, 246, 0.25);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header__left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-box {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--accent-primary-light);
  color: var(--accent-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.skill-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

/* 校验状态徽章 */
.validation-badge {
  flex-shrink: 0;
  cursor: default;
}

.validation-badge--success {
  color: #22c55e;
}

.validation-badge--error {
  color: #ef4444;
  cursor: help;
}

.card-description {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin: 0;
  min-height: 18px;
}

.card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-actions {
  display: flex;
  gap: 4px;
}
</style>
