<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from 'lucide-vue-next'
import { useSkillStore } from '@/stores/skill'
import type { Skill, SkillCreateRequest } from '@/types/skill'
import { CATEGORY_LABELS, CATEGORY_FILTERS } from '@/types/skill'
import SkillCard from '@/components/skill/SkillCard.vue'
import SkillDialog from '@/components/skill/SkillDialog.vue'

const skillStore = useSkillStore()

// Category filter
const activeCategory = ref('')
const filteredSkills = computed(() => {
  if (!activeCategory.value) return skillStore.skills
  return skillStore.skills.filter((s) => s.category === activeCategory.value)
})

// Dialog
const dialogVisible = ref(false)
const editingSkill = ref<Skill | null>(null)

function openCreateDialog() {
  editingSkill.value = null
  dialogVisible.value = true
}

function openEditDialog(skill: Skill) {
  editingSkill.value = skill
  dialogVisible.value = true
}

function closeDialog() {
  dialogVisible.value = false
  editingSkill.value = null
}

// Actions
async function handleSave(data: SkillCreateRequest) {
  try {
    if (editingSkill.value) {
      await skillStore.editSkill(editingSkill.value.id, data)
      ElMessage.success('技能已更新')
    } else {
      await skillStore.addSkill(data)
      ElMessage.success('技能创建成功')
    }
    closeDialog()
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '操作失败'
    ElMessage.error(msg)
  }
}

async function handleToggle(skill: Skill) {
  try {
    await skillStore.toggleSkillEnabled(skill.id, !skill.enabled)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '操作失败'
    ElMessage.error(msg)
  }
}

async function handleDelete(skill: Skill) {
  try {
    await ElMessageBox.confirm(
      `确定要删除技能"${skill.name}"吗？此操作不可撤销。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    await skillStore.removeSkill(skill.id)
    ElMessage.success('技能已删除')
  } catch (err: unknown) {
    if (err instanceof Error && err.message !== 'cancel') {
      ElMessage.error(err.message)
    }
  }
}

// Category stats for breakdown
const categoryStatsEntries = computed(() => {
  return Object.entries(skillStore.categoryStats).map(([key, stats]) => ({
    key,
    label: CATEGORY_LABELS[key] || key,
    ...stats,
  }))
})

onMounted(() => {
  skillStore.fetchSkills()
})
</script>

<template>
  <div class="skills-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header__info">
        <h1>Skills</h1>
        <p>管理和配置 AI 智能体的技能与工具能力</p>
      </div>
      <el-button type="primary" size="large" @click="openCreateDialog">
        <Plus :size="16" class="btn-icon" />
        创建技能
      </el-button>
    </div>

    <!-- Status Banner -->
    <div v-if="skillStore.error" class="status-banner">
      <el-alert
        :title="skillStore.error"
        type="warning"
        show-icon
        :closable="true"
      >
        <template #default>
          <el-button text size="small" @click="skillStore.fetchSkills()">重试</el-button>
        </template>
      </el-alert>
    </div>

    <!-- Stats Overview -->
    <div class="stats-bar">
      <div class="stat-card">
        <div class="stat-icon-box stat-icon--primary">
          <span class="stat-icon-text">{{ skillStore.skills.length }}</span>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ skillStore.skills.length }}</span>
          <span class="stat-label">技能总数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-box stat-icon--success">
          <span class="stat-icon-text">{{ skillStore.enabledSkills.length }}</span>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ skillStore.enabledSkills.length }}</span>
          <span class="stat-label">已启用</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-box stat-icon--warning">
          <span class="stat-icon-text">{{ skillStore.disabledSkills.length }}</span>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ skillStore.disabledSkills.length }}</span>
          <span class="stat-label">已禁用</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon-box stat-icon--danger">
          <span class="stat-icon-text">0</span>
        </div>
        <div class="stat-info">
          <span class="stat-value">0</span>
          <span class="stat-label">不可用</span>
        </div>
      </div>
    </div>

    <!-- Category Filter -->
    <div class="category-filter">
      <el-button
        v-for="cat in CATEGORY_FILTERS"
        :key="cat.key"
        :type="activeCategory === cat.key ? 'primary' : 'default'"
        :plain="activeCategory !== cat.key"
        size="small"
        round
        @click="activeCategory = cat.key"
      >
        {{ cat.label }}
      </el-button>
    </div>

    <!-- Category Breakdown -->
    <div v-if="categoryStatsEntries.length > 0" class="category-section">
      <div class="section-header">
        <span class="section-title">分类概览</span>
      </div>
      <div class="category-grid">
        <div
          v-for="cat in categoryStatsEntries"
          :key="cat.key"
          class="category-card"
        >
          <div class="cat-card-header">
            <span class="cat-label">{{ cat.label }}</span>
            <span class="cat-total">{{ cat.total }}</span>
          </div>
          <div class="cat-card-stats">
            <span class="cat-stat">可用 {{ cat.enabled }}</span>
            <span class="cat-stat cat-stat--muted">禁用 {{ cat.disabled }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Skills Grid -->
    <div class="section-header">
      <span class="section-title">技能列表</span>
      <span class="section-count">共 {{ filteredSkills.length }} 个技能</span>
    </div>

    <div v-loading="skillStore.loading" class="skills-content">
      <!-- Loading -->
      <div v-if="skillStore.loading" class="skills-grid">
        <div v-for="i in 6" :key="i" class="skeleton-card">
          <el-skeleton :rows="3" animated />
        </div>
      </div>

      <!-- Empty -->
      <el-empty
        v-else-if="filteredSkills.length === 0"
        :description="activeCategory ? '该分类下暂无技能' : '暂无技能，点击上方按钮创建第一个技能'"
      >
        <el-button v-if="!activeCategory" type="primary" @click="openCreateDialog">
          创建技能
        </el-button>
      </el-empty>

      <!-- Skills Grid -->
      <div v-else class="skills-grid">
        <SkillCard
          v-for="skill in filteredSkills"
          :key="skill.id"
          :skill="skill"
          @edit="openEditDialog"
          @delete="handleDelete"
          @toggle="handleToggle"
        />
      </div>
    </div>

    <!-- Skill Dialog -->
    <SkillDialog
      :visible="dialogVisible"
      :skill="editingSkill"
      @close="closeDialog"
      @save="handleSave"
    />
  </div>
</template>

<style scoped>
.skills-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px 32px;
  height: 100%;
  background: var(--surface-primary);
}

/* Page Header */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-header__info h1 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
  margin: 0;
}

.page-header__info p {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  margin: 4px 0 0;
}

.btn-icon {
  margin-right: 6px;
}

/* Status Banner */
.status-banner {
  width: 100%;
}

/* Stats Bar */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
}

.stat-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon-text {
  font-size: 16px;
  font-weight: var(--font-weight-bold);
  color: #fff;
}

.stat-icon--primary { background: rgba(59, 130, 246, 0.2); }
.stat-icon--success { background: rgba(34, 197, 94, 0.2); }
.stat-icon--warning { background: rgba(245, 158, 11, 0.2); }
.stat-icon--danger  { background: rgba(239, 68, 68, 0.2); }

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font-size: 22px;
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}

/* Category Filter */
.category-filter {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* Category Breakdown */
.category-section {
  margin-top: 0;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin-top: 8px;
}

.category-card {
  padding: 14px 16px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cat-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cat-label {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.cat-total {
  font-size: 18px;
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
}

.cat-card-stats {
  display: flex;
  gap: 12px;
}

.cat-stat {
  font-size: var(--font-size-xs);
  color: #22c55e;
}

.cat-stat--muted {
  color: var(--foreground-muted);
}

/* Section */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 15px;
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.section-count {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}

/* Skills Grid */
.skills-content {
  min-height: 200px;
}

.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px;
}

.skeleton-card {
  padding: 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
}
</style>
