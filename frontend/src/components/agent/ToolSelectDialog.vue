<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { X, Search, ChevronDown, ChevronLeft, ChevronRight, Check, Zap } from 'lucide-vue-next'
import type { Tool, ToolCategory, ToolStatus } from '@/types/tool'
import { CATEGORY_META, STATUS_META } from '@/types/tool'
import { fetchTools } from '@/services/toolApi'

const props = defineProps<{
  visible: boolean
  agentName: string
  existingToolNames: string[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'add', toolName: string, description: string): void
}>()

// --- state ---
const loading = ref(false)
const tools = ref<Tool[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const keyword = ref('')
const categoryFilter = ref<ToolCategory | ''>('')
const statusFilter = ref<ToolStatus | ''>('')
const selectedToolId = ref<string | null>(null)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

const selectedTool = computed(() =>
  tools.value.find((t) => t.id === selectedToolId.value) ?? null,
)

const categoryOptions = computed(() =>
  (Object.entries(CATEGORY_META) as [ToolCategory, (typeof CATEGORY_META)[ToolCategory]][]).map(
    ([value, meta]) => ({ value, label: meta.label }),
  ),
)

const statusOptions = computed(() =>
  (Object.entries(STATUS_META) as [ToolStatus, (typeof STATUS_META)[ToolStatus]][]).map(
    ([value, meta]) => ({ value, label: meta.label }),
  ),
)

// --- debounced search ---
let searchTimer: ReturnType<typeof setTimeout> | null = null
function onSearchInput() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadTools()
  }, 300)
}

function onFilterChange() {
  page.value = 1
  loadTools()
}

async function loadTools() {
  loading.value = true
  try {
    const result = await fetchTools({
      keyword: keyword.value || undefined,
      category: categoryFilter.value || undefined,
      status: statusFilter.value || undefined,
      page: page.value,
      page_size: pageSize,
    })
    tools.value = result.items
    total.value = result.total
    // Clear selection if selected tool is no longer in the list
    if (selectedToolId.value && !tools.value.find((t) => t.id === selectedToolId.value)) {
      selectedToolId.value = null
    }
  } catch {
    tools.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function goToPage(p: number) {
  if (p < 1 || p > totalPages.value || p === page.value) return
  page.value = p
  loadTools()
}

function selectTool(id: string) {
  if (isAlreadyAdded(tools.value.find((t) => t.id === id)?.name ?? '')) return
  selectedToolId.value = id
}

function handleConfirm() {
  const tool = selectedTool.value
  if (!tool) return
  if (props.existingToolNames.includes(tool.name)) return
  emit('add', tool.name, tool.description)
  resetState()
}

function handleClose() {
  resetState()
  emit('close')
}

function resetState() {
  keyword.value = ''
  categoryFilter.value = ''
  statusFilter.value = ''
  page.value = 1
  selectedToolId.value = null
  tools.value = []
  total.value = 0
}

function isAlreadyAdded(name: string): boolean {
  return props.existingToolNames.includes(name)
}

watch(
  () => props.visible,
  (val) => {
    if (val) {
      keyword.value = ''
      categoryFilter.value = ''
      statusFilter.value = ''
      page.value = 1
      selectedToolId.value = null
      loadTools()
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
                <Zap :size="18" color="#3b82f6" />
              </div>
              <div>
                <h3 class="dialog-title">添加工具</h3>
                <p class="dialog-desc">
                  为 <span class="highlight">"{{ agentName }}"</span> 从工具库中选择工具
                </p>
              </div>
            </div>
            <button class="modal-close" @click="handleClose">
              <X :size="18" />
            </button>
          </div>

          <!-- Search & Filters -->
          <div class="dialog-toolbar">
            <div class="search-box">
              <Search :size="14" class="search-icon" />
              <input
                v-model="keyword"
                class="search-input"
                placeholder="搜索工具名称或描述..."
                @input="onSearchInput"
              />
            </div>
            <div class="filter-row">
              <div class="filter-select-wrap">
                <select
                  v-model="categoryFilter"
                  class="filter-select"
                  @change="onFilterChange"
                >
                  <option value="">全部类别</option>
                  <option
                    v-for="opt in categoryOptions"
                    :key="opt.value"
                    :value="opt.value"
                  >
                    {{ opt.label }}
                  </option>
                </select>
                <ChevronDown :size="12" class="select-arrow" />
              </div>
              <div class="filter-select-wrap">
                <select
                  v-model="statusFilter"
                  class="filter-select"
                  @change="onFilterChange"
                >
                  <option value="">全部状态</option>
                  <option
                    v-for="opt in statusOptions"
                    :key="opt.value"
                    :value="opt.value"
                  >
                    {{ opt.label }}
                  </option>
                </select>
                <ChevronDown :size="12" class="select-arrow" />
              </div>
              <span class="toolbar-count">共 {{ total }} 个工具</span>
            </div>
          </div>

          <!-- Tool List (fixed height, scrollable) -->
          <div class="list-container">
            <div v-if="loading" class="list-status">加载中...</div>
            <div v-else-if="tools.length === 0" class="list-status">
              未找到匹配的工具
            </div>
            <div v-else class="tool-list">
              <div
                v-for="tool in tools"
                :key="tool.id"
                class="tool-row"
                :class="{
                  selected: selectedToolId === tool.id,
                  disabled: isAlreadyAdded(tool.name),
                }"
                @click="selectTool(tool.id)"
              >
                <div class="tool-row-left">
                  <span class="tool-display-name">{{ tool.displayName }}</span>
                  <span class="tool-name">{{ tool.name }}</span>
                  <span
                    class="tool-badge"
                    :style="{
                      background: CATEGORY_META[tool.category]?.bg,
                      color: CATEGORY_META[tool.category]?.color,
                      borderColor: CATEGORY_META[tool.category]?.border,
                    }"
                  >
                    {{ CATEGORY_META[tool.category]?.label ?? tool.category }}
                  </span>
                  <span
                    class="tool-badge"
                    :style="{
                      background: STATUS_META[tool.status]?.bg,
                      color: STATUS_META[tool.status]?.color,
                      borderColor: STATUS_META[tool.status]?.border,
                    }"
                  >
                    {{ STATUS_META[tool.status]?.label ?? tool.status }}
                  </span>
                </div>
                <div class="tool-row-right">
                  <span v-if="isAlreadyAdded(tool.name)" class="added-mark">已添加</span>
                  <Check
                    v-else-if="selectedToolId === tool.id"
                    :size="16"
                    class="check-icon"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Pagination -->
          <div class="pagination-row">
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

          <!-- Description Panel (fixed area) -->
          <div class="desc-panel">
            <div class="desc-label">工具描述</div>
            <div class="desc-content">
              {{ selectedTool?.description || '请选择一个工具查看描述' }}
            </div>
          </div>

          <!-- Footer -->
          <div class="dialog-footer">
            <button class="btn btn-ghost" @click="handleClose">取消</button>
            <button
              class="btn btn-primary"
              :disabled="!selectedTool || isAlreadyAdded(selectedTool.name)"
              @click="handleConfirm"
            >
              添加工具
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
  width: 620px;
  max-width: 92vw;
  height: 560px;
  max-height: 85vh;
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
  padding: 20px 24px 16px;
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
  background: rgba(59, 130, 246, 0.1);
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

/* ---- Toolbar ---- */
.dialog-toolbar {
  padding: 0 24px 12px;
  flex-shrink: 0;
}

.search-box {
  position: relative;
  margin-bottom: 10px;
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
  padding: 8px 12px 8px 32px;
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-input);
  font-size: var(--font-size-sm);
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
  box-shadow: 0px 0px 0px 2px rgba(59, 130, 246, 0.12);
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-select-wrap {
  position: relative;
  flex: 1;
  max-width: 150px;
}

.filter-select {
  width: 100%;
  padding: 6px 28px 6px 10px;
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-input);
  font-size: var(--font-size-xs);
  color: var(--color-text-primary);
  font-family: var(--font-family-base);
  outline: none;
  cursor: pointer;
  appearance: none;
  transition: border-color var(--transition-fast);
}

.filter-select:focus {
  border-color: var(--color-accent);
}

.select-arrow {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-muted);
  pointer-events: none;
}

.toolbar-count {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  white-space: nowrap;
  margin-left: auto;
}

/* ---- Tool List (fixed height) ---- */
.list-container {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0 24px;
}

.list-status {
  text-align: center;
  padding: 32px 16px;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.tool-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tool-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-lg);
  background: var(--color-bg-input);
  cursor: pointer;
  transition: all 0.15s ease;
  gap: 8px;
}

.tool-row:hover:not(.disabled) {
  border-color: rgba(59, 130, 246, 0.4);
  background: rgba(59, 130, 246, 0.04);
}

.tool-row.selected {
  border-color: var(--color-accent);
  background: rgba(59, 130, 246, 0.08);
}

.tool-row.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.tool-row-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
}

.tool-display-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  white-space: nowrap;
}

.tool-name {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  font-family: monospace;
}

.tool-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: var(--radius-full);
  border: 1px solid;
  white-space: nowrap;
}

.tool-row-right {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.added-mark {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
}

.check-icon {
  color: var(--color-accent);
  flex-shrink: 0;
}

/* ---- Pagination ---- */
.pagination-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px 24px;
  flex-shrink: 0;
}

.page-btn {
  width: 28px;
  height: 28px;
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-sm);
  background: var(--color-bg-input);
  color: var(--color-text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.page-btn:hover:not(:disabled) {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.page-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.page-info {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  min-width: 48px;
  text-align: center;
}

/* ---- Description Panel ---- */
.desc-panel {
  padding: 10px 24px;
  border-top: 1px solid var(--color-border-input);
  flex-shrink: 0;
  min-height: 52px;
  max-height: 90px;
  overflow-y: auto;
}

.desc-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-label);
  margin-bottom: 4px;
}

.desc-content {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* ---- Footer ---- */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 24px 16px;
  border-top: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

/* ---- Buttons ---- */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: none;
  border-radius: var(--radius-button);
  font-size: var(--font-size-sm);
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
