<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { X, Sparkles, Search, Loader2, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { fetchSkills, searchSkills } from '@/services/skillApi'
import type { Skill } from '@/types/skill'
import { getSkillIcon } from '@/components/skill/iconMap'

const props = defineProps<{
  visible: boolean
  agentName: string
  existingSkillIds: string[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'add', skillId: string): void
}>()

const PAGE_SIZE = 10

const searchQuery = ref('')
const loading = ref(false)
const skills = ref<Skill[]>([])
const total = ref(0)
const page = ref(1)
const selectedSkill = ref<Skill | null>(null)
const activeCategory = ref('')
const activeStatus = ref<'all' | 'enabled' | 'disabled'>('all')

const categories = ['', 'search', 'code', 'creative', 'analysis', 'tools', 'custom']
const categoryLabels: Record<string, string> = {
  '': '全部',
  search: '搜索',
  code: '代码',
  creative: '创意',
  analysis: '分析',
  tools: '工具',
  custom: '自定义',
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / PAGE_SIZE)))

let debounceTimer: ReturnType<typeof setTimeout> | null = null

function buildParams() {
  const params: Record<string, unknown> = { page: page.value, page_size: PAGE_SIZE }
  if (activeCategory.value) params.category = activeCategory.value
  if (activeStatus.value !== 'all') params.enabled = activeStatus.value === 'enabled'
  return params
}

async function loadData() {
  loading.value = true
  try {
    const params = buildParams()
    const q = searchQuery.value.trim()
    const result = q
      ? await searchSkills(q, params)
      : await fetchSkills(params)
    skills.value = result.items
    total.value = result.total
  } catch {
    skills.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onSearchInput() {
  page.value = 1
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(loadData, 300)
}

function onFilterChange() {
  page.value = 1
  loadData()
}

function goToPage(p: number) {
  if (p < 1 || p > totalPages.value) return
  page.value = p
  loadData()
}

function selectSkill(skill: Skill) {
  if (isAlreadyAdded(skill.id)) return
  selectedSkill.value = skill
}

function isAlreadyAdded(skillId: string) {
  return props.existingSkillIds.includes(skillId)
}

function isSelected(skillId: string) {
  return selectedSkill.value?.id === skillId
}

function handleConfirm() {
  if (selectedSkill.value && !isAlreadyAdded(selectedSkill.value.id)) {
    emit('add', selectedSkill.value.id)
  }
}

function handleClose() {
  resetForm()
  emit('close')
}

function resetForm() {
  searchQuery.value = ''
  skills.value = []
  total.value = 0
  page.value = 1
  selectedSkill.value = null
  activeCategory.value = ''
  activeStatus.value = 'all'
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      resetForm()
      loadData()
    }
  },
)
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="dialog-overlay" @click.self="handleClose">
        <div class="dialog-modal">
          <!-- Header -->
          <div class="dialog-header">
            <div class="header-left">
              <div class="dialog-icon">
                <Sparkles :size="18" style="color: #a78bfa" />
              </div>
              <div>
                <h3 class="dialog-title">添加技能</h3>
                <p class="dialog-desc">
                  为 <span class="highlight">"{{ agentName }}"</span> 选择技能
                </p>
              </div>
            </div>
            <button class="modal-close" @click="handleClose">
              <X :size="18" />
            </button>
          </div>

          <!-- Body -->
          <div class="dialog-body">
            <!-- Search box -->
            <div class="search-box">
              <Search :size="14" class="search-icon" />
              <input
                v-model="searchQuery"
                type="text"
                class="search-input"
                placeholder="输入技能名称搜索..."
                @input="onSearchInput"
              />
            </div>

            <!-- Filters -->
            <div class="filter-row">
              <div class="filter-group">
                <span class="filter-label">类别：</span>
                <el-button
                  v-for="cat in categories"
                  :key="cat"
                  :type="activeCategory === cat ? 'primary' : 'default'"
                  :plain="activeCategory !== cat"
                  size="small"
                  round
                  @click="activeCategory = cat; onFilterChange()"
                >
                  {{ categoryLabels[cat] }}
                </el-button>
              </div>
              <div class="filter-group">
                <span class="filter-label">状态：</span>
                <el-button
                  v-for="s in (['all', 'enabled', 'disabled'] as const)"
                  :key="s"
                  :type="activeStatus === s ? 'primary' : 'default'"
                  :plain="activeStatus !== s"
                  size="small"
                  round
                  @click="activeStatus = s; onFilterChange()"
                >
                  {{ s === 'all' ? '全部' : s === 'enabled' ? '已启用' : '已禁用' }}
                </el-button>
              </div>
            </div>

            <!-- Skill list -->
            <div class="skill-list">
              <div v-if="loading" class="list-state">
                <Loader2 :size="20" class="spin" />
                <span>加载中...</span>
              </div>
              <div v-else-if="skills.length === 0" class="list-state">
                <Search :size="20" class="empty-icon" />
                <span>暂无匹配的技能</span>
              </div>
              <template v-else>
                <div
                  v-for="skill in skills"
                  :key="skill.id"
                  class="skill-item"
                  :class="{
                    selected: isSelected(skill.id),
                    'already-added': isAlreadyAdded(skill.id),
                  }"
                  @click="selectSkill(skill)"
                >
                  <div class="skill-item-left">
                    <component :is="getSkillIcon(skill.icon)" :size="16" class="skill-item-icon" />
                    <span class="skill-item-name">{{ skill.name }}</span>
                    <span class="skill-item-category">{{ categoryLabels[skill.category] || skill.category }}</span>
                  </div>
                  <div class="skill-item-right">
                    <span v-if="isAlreadyAdded(skill.id)" class="added-badge">已添加</span>
                    <span v-else-if="isSelected(skill.id)" class="selected-dot" />
                  </div>
                </div>
              </template>
            </div>

            <!-- Pagination -->
            <div v-if="total > 0" class="pagination">
              <button
                class="page-btn"
                :disabled="page <= 1"
                @click="goToPage(page - 1)"
              >
                <ChevronLeft :size="14" />
              </button>
              <span class="page-info">{{ page }} / {{ totalPages }}</span>
              <button
                class="page-btn"
                :disabled="page >= totalPages"
                @click="goToPage(page + 1)"
              >
                <ChevronRight :size="14" />
              </button>
            </div>

            <!-- Selected skill description -->
            <div v-if="selectedSkill" class="desc-area">
              <div class="desc-header">
                <component :is="getSkillIcon(selectedSkill.icon)" :size="14" />
                <span class="desc-title">{{ selectedSkill.name }}</span>
                <span class="desc-cat">{{ categoryLabels[selectedSkill.category] || selectedSkill.category }}</span>
              </div>
              <p class="desc-text">{{ selectedSkill.description || '暂无描述' }}</p>
            </div>
          </div>

          <!-- Footer -->
          <div class="dialog-footer">
            <button class="btn btn-ghost" @click="handleClose">取消</button>
            <button
              class="btn btn-primary"
              :disabled="!selectedSkill || isAlreadyAdded(selectedSkill.id)"
              @click="handleConfirm"
            >
              确认添加
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-overlay);
  z-index: 9999;
}

.dialog-modal {
  width: 560px;
  max-width: 92vw;
  height: 620px;
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  background: var(--color-modal-bg);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-card);
  box-shadow: 0px 12px 60px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

/* ---- Header ---- */
.dialog-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.dialog-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-lg);
  background: rgba(139, 92, 246, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.dialog-title {
  font-size: 17px;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.dialog-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 4px 0 0;
}

.highlight {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.modal-close {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text-primary);
}

/* ---- Body ---- */
.dialog-body {
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* ---- Search ---- */
.search-box {
  position: relative;
  flex-shrink: 0;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 8px 12px 8px 30px;
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-input);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  font-family: var(--font-family-base);
  outline: none;
  box-sizing: border-box;
  transition: border-color var(--transition-fast);
}

.search-input::placeholder {
  color: var(--color-text-muted);
}

.search-input:focus {
  border-color: var(--color-accent);
}

/* ---- Filters ---- */
.filter-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.filter-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
}

/* ---- Skill list ---- */
.skill-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
}

.list-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 32px;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  flex: 1;
}

.empty-icon {
  opacity: 0.4;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.skill-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.12s ease;
  border-bottom: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

.skill-item:last-child {
  border-bottom: none;
}

.skill-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.skill-item.selected {
  background: rgba(139, 92, 246, 0.08);
  border-color: rgba(139, 92, 246, 0.15);
}

.skill-item.already-added {
  opacity: 0.4;
  cursor: not-allowed;
}

.skill-item.already-added:hover {
  background: transparent;
}

.skill-item-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.skill-item-icon {
  color: #a78bfa;
  flex-shrink: 0;
}

.skill-item-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.skill-item-category {
  font-size: var(--font-size-xs);
  padding: 1px 6px;
  border-radius: var(--radius-full);
  background: rgba(139, 92, 246, 0.08);
  color: #a78bfa;
}

.skill-item-right {
  flex-shrink: 0;
}

.added-badge {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.selected-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #a78bfa;
  display: block;
}

/* ---- Pagination ---- */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-shrink: 0;
}

.page-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.page-btn:hover:not(:disabled) {
  border-color: rgba(139, 92, 246, 0.3);
  color: #a78bfa;
}

.page-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-info {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  min-width: 50px;
  text-align: center;
}

/* ---- Description area ---- */
.desc-area {
  padding: 10px 12px;
  border-radius: var(--radius-lg);
  background: rgba(139, 92, 246, 0.04);
  border: 1px solid rgba(139, 92, 246, 0.12);
  flex-shrink: 0;
}

.desc-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  color: #a78bfa;
}

.desc-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.desc-cat {
  font-size: var(--font-size-xs);
  padding: 1px 6px;
  border-radius: var(--radius-full);
  background: rgba(139, 92, 246, 0.08);
}

.desc-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
  line-height: 1.5;
}

/* ---- Footer ---- */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px;
  border-top: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

/* ---- Buttons ---- */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  border: none;
  border-radius: var(--radius-button);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  font-family: var(--font-family-base);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-accent);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-dark);
}

.btn-ghost {
  background: rgba(135, 148, 173, 0.08);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-input);
}

.btn-ghost:hover {
  background: rgba(135, 148, 173, 0.14);
  color: var(--color-text-primary);
}

/* ---- Transition ---- */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-normal);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
