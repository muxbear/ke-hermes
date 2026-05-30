<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Play, Pause, Trash2, Plus, RefreshCw, Clock, CheckCircle2,
  XCircle, AlertCircle, ChevronDown, ChevronRight, Search,
  Filter, Calendar, Zap, Bot, Wrench, Edit3, Copy, Terminal,
  Activity, TrendingUp, X, Info,
} from 'lucide-vue-next'
import { useScheduledTaskStore } from '@/stores/scheduledTask'
import type { CronTask, RunRecord, TaskStatus, RunStatus, TargetType, CreateTaskRequest } from '@/types/scheduledTask'
import {
  TASK_STATUS_META, RUN_STATUS_META, TARGET_TYPE_LABELS,
  TARGET_TYPE_COLORS, CRON_PRESETS,
} from '@/types/scheduledTask'

const store = useScheduledTaskStore()

/* ---- Local state ---- */
const showCreate = ref(false)
const selectedRun = ref<RunRecord | null>(null)
const refreshing = ref(false)
const currentTime = ref(new Date())

let clockTimer: ReturnType<typeof setInterval> | null = null

/* ---- Create form ---- */
const form = ref<CreateTaskRequest>({
  name: '', description: '', cron: '0 * * * *',
  cronLabel: '每小时', target: '', targetType: 'agent', tags: '',
})

/* ---- Helpers ---- */
function targetIcon(type: TargetType) {
  const map: Record<TargetType, typeof Bot> = { agent: Bot, skill: Zap, tool: Wrench, prompt: Terminal }
  return map[type]
}

function targetColor(type: TargetType) {
  return TARGET_TYPE_COLORS[type]
}

function statusClass(status: RunStatus) {
  return RUN_STATUS_META[status].color
}

function runIcon(status: RunStatus) {
  const map: Record<string, typeof CheckCircle2> = {
    success: CheckCircle2, failed: XCircle, running: Activity, skipped: AlertCircle,
  }
  return map[status]
}

function successRateColor(rate: number) {
  if (rate >= 95) return '#10B981'
  if (rate >= 80) return '#F59E0B'
  return '#EF4444'
}

/* ---- Actions ---- */
async function handleRefresh() {
  refreshing.value = true
  await store.fetchAll()
  setTimeout(() => { refreshing.value = false }, 500)
}

function openCreate() {
  form.value = { name: '', description: '', cron: '0 * * * *', cronLabel: '每小时', target: '', targetType: 'agent', tags: '' }
  showCreate.value = true
}

async function handleCreate() {
  if (!form.value.name.trim() || !form.value.target.trim()) return
  try {
    await store.createTask({ ...form.value })
    ElMessage.success('定时任务已创建')
    showCreate.value = false
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '创建失败')
  }
}

function handlePreset(preset: { label: string; value: string }) {
  form.value.cron = preset.value
  form.value.cronLabel = preset.label
}

async function handleToggle(id: string) {
  try {
    await store.toggleTaskStatus(id)
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
  }
}

async function handleClone(id: string) {
  try {
    await store.cloneTask(id)
    ElMessage.success('已复制')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '复制失败')
  }
}

async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm('确定要删除此定时任务吗？', '确认删除', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning',
    })
    await store.deleteTask(id)
    ElMessage.success('已删除')
  } catch (err: unknown) {
    if (err instanceof Error && err.message !== 'cancel') {
      ElMessage.error(err.message)
    }
  }
}

/* ---- Lifecycle ---- */
onMounted(() => {
  store.fetchAll()
  clockTimer = setInterval(() => { currentTime.value = new Date() }, 1000)
})

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
})
</script>

<template>
  <div class="scheduled-tasks-page">
    <!-- ═══ Page Header ═══ -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">定时任务</h1>
        <p class="page-subtitle">唤醒和重复运行 · 周期性自动化执行</p>
      </div>
      <div class="header-right">
        <button class="btn-secondary" @click="handleRefresh">
          <RefreshCw :size="14" :class="{ spinning: refreshing }" />
          刷新
        </button>
        <button class="btn-primary" @click="openCreate">
          <Plus :size="16" />
          新建任务
        </button>
      </div>
    </div>

    <!-- ═══ Status Bar ═══ -->
    <div class="status-grid">
      <div class="status-card status-card--green">
        <p class="status-card-label">已启用</p>
        <div class="status-card-row">
          <span class="status-dot status-dot--green" />
          <span class="status-card-value status-card-value--green">是</span>
        </div>
        <p class="status-card-sub">调度器运行中</p>
      </div>

      <div class="status-card status-card--default">
        <p class="status-card-label">任务总数</p>
        <p class="status-card-big">{{ store.taskStats.total }}</p>
        <div class="status-card-tags">
          <span class="tag tag--green">{{ store.taskStats.active }} 运行中</span>
          <span class="tag tag--amber">{{ store.taskStats.paused }} 已暂停</span>
          <span class="tag tag--red">{{ store.taskStats.error }} 异常</span>
        </div>
      </div>

      <div class="status-card status-card--indigo">
        <p class="status-card-label">下次唤醒</p>
        <p class="status-card-value status-card-value--indigo">
          {{ store.nextTask?.nextRun ?? '不适用' }}
        </p>
        <p v-if="store.nextTask" class="status-card-sub">{{ store.nextTask.name }}</p>
      </div>

      <div class="status-card status-card--purple">
        <p class="status-card-label">今日执行次数</p>
        <p class="status-card-big">{{ store.runStats.total }}</p>
        <div class="status-card-tags">
          <span class="tag tag--green">{{ store.runStats.success }} 成功</span>
          <span class="tag tag--red">{{ store.runStats.failed }} 失败</span>
        </div>
      </div>
    </div>

    <!-- ═══ Task List ═══ -->
    <div class="section-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">任务列表</h2>
          <p class="section-desc">所有已配置的定时任务</p>
        </div>
        <span class="section-count">显示 {{ store.filteredTasks.length }} / 共 {{ store.tasks.length }}</span>
      </div>

      <!-- Filters -->
      <div class="section-filters">
        <div class="search-wrap">
          <Search :size="14" class="search-icon" />
          <input
            v-model="store.taskSearch"
            type="text"
            placeholder="搜索任务名称、目标…"
            class="search-input"
          />
        </div>
        <div class="filter-tabs">
          <button
            v-for="f in (['all', 'active', 'paused', 'error'] as const)"
            :key="f"
            class="filter-tab"
            :class="{ active: store.taskFilter === f }"
            @click="store.taskFilter = f"
          >
            {{ f === 'all' ? '全部' : TASK_STATUS_META[f].label }}
          </button>
        </div>
      </div>

      <!-- Desktop table header -->
      <div class="task-table-header">
        <span class="col-name">任务</span>
        <span class="col-cron">Cron 周期</span>
        <span class="col-last">上次执行</span>
        <span class="col-next">下次执行</span>
        <span class="col-rate">成功率</span>
        <span class="col-actions">操作</span>
      </div>

      <!-- Empty state -->
      <div v-if="store.filteredTasks.length === 0" class="empty-state">
        <Calendar :size="40" class="empty-icon" />
        <p class="empty-title">暂无定时任务</p>
        <p class="empty-desc">尚未创建任何任务，或筛选条件无匹配结果</p>
        <button class="btn-primary" @click="openCreate">
          <Plus :size="16" />
          新建任务
        </button>
      </div>

      <!-- Task rows -->
      <div class="task-rows">
        <div v-for="task in store.filteredTasks" :key="task.id" class="task-row-wrap">
          <div class="task-row" @click="store.toggleExpand(task.id)">
            <div class="task-name-cell">
              <button class="expand-btn" @click.stop="store.toggleExpand(task.id)">
                <ChevronDown v-if="store.expandedTaskId === task.id" :size="14" />
                <ChevronRight v-else :size="14" />
              </button>
              <div class="task-name-content">
                <div class="task-name-row">
                  <span class="task-name">{{ task.name }}</span>
                  <span
                    class="status-badge"
                    :style="{ color: TASK_STATUS_META[task.status].color, background: TASK_STATUS_META[task.status].bg }"
                  >
                    <span class="status-badge-dot" :style="{ background: TASK_STATUS_META[task.status].dot }" />
                    {{ TASK_STATUS_META[task.status].label }}
                  </span>
                </div>
                <div class="task-target-row">
                  <component :is="targetIcon(task.targetType)" :size="12" :color="targetColor(task.targetType)" />
                  <span class="task-target">{{ task.target }}</span>
                  <span v-for="tag in task.tags" :key="tag" class="task-tag">{{ tag }}</span>
                </div>
              </div>
            </div>

            <div class="task-cron-cell">
              <p class="cron-expr">{{ task.cron }}</p>
              <p class="cron-label">{{ task.cronLabel }}</p>
            </div>

            <div class="task-cell task-last-cell">{{ task.lastRun ?? '从未执行' }}</div>
            <div class="task-cell task-next-cell">{{ task.nextRun }}</div>

            <div class="task-rate-cell">
              <div class="rate-top">
                <span class="rate-value" :style="{ color: successRateColor(task.successRate) }">
                  {{ task.successRate }}%
                </span>
                <span class="rate-count">{{ task.totalRuns }}次</span>
              </div>
              <div class="rate-bar-track">
                <div
                  class="rate-bar-fill"
                  :style="{ width: `${task.successRate}%`, background: successRateColor(task.successRate) }"
                />
              </div>
            </div>

            <div class="task-actions-cell" @click.stop>
              <button :title="task.status === 'active' ? '暂停' : '启用'" class="action-btn" @click="handleToggle(task.id)">
                <Pause v-if="task.status === 'active'" :size="14" />
                <Play v-else :size="14" />
              </button>
              <button title="编辑" class="action-btn">
                <Edit3 :size="14" />
              </button>
              <button title="复制" class="action-btn" @click="handleClone(task.id)">
                <Copy :size="14" />
              </button>
              <button title="删除" class="action-btn action-btn--danger" @click="handleDelete(task.id)">
                <Trash2 :size="14" />
              </button>
            </div>
          </div>

          <!-- Expanded detail -->
          <div v-if="store.expandedTaskId === task.id" class="task-detail">
            <div class="detail-grid">
              <div>
                <p class="detail-label">任务描述</p>
                <p class="detail-value">{{ task.description || '无描述' }}</p>
              </div>
              <div>
                <p class="detail-label">目标类型</p>
                <div class="detail-target">
                  <component :is="targetIcon(task.targetType)" :size="14" :color="targetColor(task.targetType)" />
                  <span>{{ TARGET_TYPE_LABELS[task.targetType] }}</span>
                </div>
              </div>
              <div>
                <p class="detail-label">平均耗时</p>
                <p class="detail-value">{{ task.avgDuration }}</p>
              </div>
              <div>
                <p class="detail-label">历史执行</p>
                <p class="detail-value">{{ task.totalRuns }} 次</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Run History ═══ -->
    <div class="section-card">
      <div class="section-header">
        <div>
          <h2 class="section-title">运行历史</h2>
          <p class="section-desc">所有任务的最近执行记录</p>
        </div>
        <span class="section-count">显示 {{ store.filteredRuns.length }} / 共 {{ store.runs.length }}</span>
      </div>

      <!-- Run filters -->
      <div class="section-filters">
        <Filter :size="14" class="filter-icon" />
        <div class="filter-tabs">
          <button
            v-for="f in (['all', 'success', 'running', 'failed', 'skipped'] as const)"
            :key="f"
            class="filter-tab"
            :class="{ active: store.runFilter === f }"
            @click="store.runFilter = f"
          >
            {{ f === 'all' ? '全部' : RUN_STATUS_META[f].label }}
          </button>
        </div>
      </div>

      <!-- Desktop table header -->
      <div class="run-table-header">
        <span class="col-name">任务</span>
        <span class="col-status">状态</span>
        <span class="col-time">开始时间</span>
        <span class="col-dur">耗时</span>
        <span class="col-detail">详情</span>
      </div>

      <div v-if="store.filteredRuns.length === 0" class="empty-state-sm">
        没有匹配的运行记录。
      </div>

      <div class="run-rows">
        <div
          v-for="run in store.filteredRuns"
          :key="run.id"
          class="run-row"
          @click="selectedRun = run"
        >
          <div class="run-name-cell">
            <p class="run-task-name">{{ run.taskName }}</p>
            <p class="run-trigger">{{ run.trigger === 'manual' ? '👆 手动触发' : '⏰ 定时触发' }}</p>
          </div>
          <div class="run-status-cell" :style="{ color: RUN_STATUS_META[run.status].color }">
            <component :is="runIcon(run.status)" :size="14" :class="{ spinning: run.status === 'running' }" />
            <span>{{ RUN_STATUS_META[run.status].label }}</span>
          </div>
          <span class="run-time">{{ run.startTime }}</span>
          <span class="run-dur">{{ run.duration }}</span>
          <button class="info-btn">
            <Info :size="14" />
          </button>
        </div>
      </div>
    </div>

    <!-- ═══ Create Task Modal ═══ -->
    <Teleport to="body">
      <div v-if="showCreate" class="modal-overlay" @click.self="showCreate = false">
        <div class="modal-card">
          <div class="modal-header">
            <div>
              <h2 class="modal-title">新建定时任务</h2>
              <p class="modal-desc">配置一个周期性执行的任务</p>
            </div>
            <button class="modal-close" @click="showCreate = false">
              <X :size="16" />
            </button>
          </div>

          <div class="modal-body">
            <!-- Name -->
            <div class="form-group">
              <label class="form-label">任务名称 *</label>
              <input v-model="form.name" placeholder="例：每日报告生成" class="form-input" />
            </div>

            <!-- Description -->
            <div class="form-group">
              <label class="form-label">描述</label>
              <textarea v-model="form.description" placeholder="简要描述任务用途…" rows="2" class="form-textarea" />
            </div>

            <!-- Cron -->
            <div class="form-group">
              <label class="form-label">Cron 表达式 *</label>
              <input v-model="form.cron" placeholder="* * * * *" class="form-input form-input--mono" />
              <div class="cron-presets">
                <button
                  v-for="p in CRON_PRESETS"
                  :key="p.value"
                  class="preset-btn"
                  :class="{ active: form.cron === p.value }"
                  @click="handlePreset(p)"
                >
                  {{ p.label }}
                </button>
              </div>
            </div>

            <!-- Target -->
            <div class="form-row">
              <div class="form-group">
                <label class="form-label">目标类型</label>
                <select v-model="form.targetType" class="form-select">
                  <option value="agent">代理 Agent</option>
                  <option value="skill">技能 Skill</option>
                  <option value="tool">工具 Tool</option>
                  <option value="prompt">提示词 Prompt</option>
                </select>
              </div>
              <div class="form-group">
                <label class="form-label">目标名称 *</label>
                <input v-model="form.target" placeholder="例：main-alpha" class="form-input" />
              </div>
            </div>

            <!-- Tags -->
            <div class="form-group">
              <label class="form-label">标签（逗号分隔）</label>
              <input v-model="form.tags" placeholder="报告, 通知, 数据" class="form-input" />
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-cancel" @click="showCreate = false">取消</button>
            <button
              class="btn-primary"
              :disabled="!form.name.trim() || !form.target.trim()"
              @click="handleCreate"
            >
              创建任务
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══ Run Detail Drawer ═══ -->
    <Teleport to="body">
      <div v-if="selectedRun" class="drawer-overlay" @click.self="selectedRun = null">
        <div class="drawer-panel">
          <div class="drawer-header">
            <h3 class="drawer-title">执行详情</h3>
            <button class="drawer-close" @click="selectedRun = null">
              <X :size="16" />
            </button>
          </div>
          <div class="drawer-body">
            <div class="drawer-info-card">
              <div class="drawer-info-row">
                <span class="drawer-label">任务名称</span>
                <span class="drawer-value">{{ selectedRun.taskName }}</span>
              </div>
              <div class="drawer-info-row">
                <span class="drawer-label">触发方式</span>
                <span class="drawer-value">{{ selectedRun.trigger === 'manual' ? '👆 手动触发' : '⏰ 定时触发' }}</span>
              </div>
              <div class="drawer-info-row">
                <span class="drawer-label">开始时间</span>
                <span class="drawer-value">{{ selectedRun.startTime }}</span>
              </div>
              <div class="drawer-info-row">
                <span class="drawer-label">耗时</span>
                <span class="drawer-value">{{ selectedRun.duration }}</span>
              </div>
              <div class="drawer-info-row">
                <span class="drawer-label">状态</span>
                <span class="drawer-value" :style="{ color: RUN_STATUS_META[selectedRun.status].color }">
                  <component :is="runIcon(selectedRun.status)" :size="14" />
                  {{ RUN_STATUS_META[selectedRun.status].label }}
                </span>
              </div>
            </div>
            <div class="drawer-output">
              <p class="drawer-label">输出 / 日志</p>
              <div class="drawer-code">
                <pre>{{ selectedRun.output }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.scheduled-tasks-page {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
  background: var(--surface-primary);
}

/* ---- Page Header ---- */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(90deg, #818CF8, #A78BFA, #60A5FA);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  margin-top: 4px;
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: var(--surface-card);
  color: var(--foreground-muted);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-secondary:hover {
  background: var(--surface-secondary);
  color: var(--foreground-primary);
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: var(--radius-lg);
  border: none;
  background: #4f46e5;
  color: #fff;
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: background 0.15s ease;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3);
}

.btn-primary:hover {
  background: #4338ca;
}

.btn-primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* ---- Status Bar ---- */
.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.status-card {
  border-radius: var(--radius-xl);
  padding: 16px;
  border: 1px solid;
}

.status-card--green {
  border-color: rgba(16, 185, 129, 0.2);
  background: rgba(16, 185, 129, 0.05);
}

.status-card--default {
  border-color: var(--border-subtle);
  background: rgba(255, 255, 255, 0.03);
}

.status-card--indigo {
  border-color: rgba(99, 102, 241, 0.2);
  background: rgba(99, 102, 241, 0.05);
}

.status-card--purple {
  border-color: rgba(139, 92, 246, 0.2);
  background: rgba(139, 92, 246, 0.05);
}

.status-card-label {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.status-card-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-dot--green {
  background: #10B981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.status-card-value {
  font-weight: 600;
  font-size: var(--font-size-md);
}

.status-card-value--green { color: #6ee7b7; }
.status-card-value--indigo { color: #a5b4fc; }

.status-card-big {
  font-size: 28px;
  font-weight: 700;
  color: var(--foreground-primary);
  margin-top: 8px;
}

.status-card-sub {
  margin-top: 4px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-card-tags {
  display: flex;
  gap: 8px;
  margin-top: 4px;
  font-size: var(--font-size-xs);
}

.tag--green { color: #6ee7b7; }
.tag--amber { color: #fbbf24; }
.tag--red { color: #f87171; }

/* ---- Section Card ---- */
.section-card {
  background: rgba(20, 29, 56, 0.7);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  margin-bottom: 24px;
  overflow: hidden;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-subtle);
}

.section-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--foreground-primary);
}

.section-desc {
  margin-top: 2px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.section-count {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

/* ---- Filters ---- */
.section-filters {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border-subtle);
}

.search-wrap {
  position: relative;
  flex: 1;
  max-width: 280px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--foreground-muted);
}

.search-input {
  width: 100%;
  padding: 6px 12px 6px 30px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: rgba(255, 255, 255, 0.04);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
  transition: border-color 0.15s ease;
}

.search-input::placeholder { color: var(--foreground-muted); }
.search-input:focus { border-color: var(--color-accent); }

.filter-icon {
  color: var(--foreground-muted);
  flex-shrink: 0;
}

.filter-tabs {
  display: flex;
  gap: 2px;
  background: rgba(255, 255, 255, 0.04);
  padding: 3px;
  border-radius: var(--radius-lg);
}

.filter-tab {
  padding: 4px 12px;
  font-size: var(--font-size-xs);
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.filter-tab:hover { color: var(--foreground-primary); }

.filter-tab.active {
  background: #4f46e5;
  color: #fff;
}

/* ---- Table Headers ---- */
.task-table-header,
.run-table-header {
  display: grid;
  gap: 16px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border-subtle);
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.task-table-header {
  grid-template-columns: 2fr 1.2fr 1fr 1fr 1fr auto;
}

.run-table-header {
  grid-template-columns: 2fr 1fr 1fr 1fr auto;
}

/* ---- Task Rows ---- */
.task-rows,
.run-rows {
  display: flex;
  flex-direction: column;
}

.task-row-wrap {
  border-bottom: 1px solid rgba(38, 51, 89, 0.15);
}

.task-row {
  display: grid;
  grid-template-columns: 2fr 1.2fr 1fr 1fr 1fr auto;
  gap: 16px;
  align-items: center;
  padding: 14px 20px;
  cursor: pointer;
  transition: background 0.1s ease;
}

.task-row:hover { background: rgba(255, 255, 255, 0.02); }

.task-name-cell {
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.expand-btn {
  margin-top: 2px;
  padding: 2px;
  border-radius: var(--radius-sm);
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
  flex-shrink: 0;
}

.expand-btn:hover { color: var(--foreground-primary); }

.task-name-content { min-width: 0; }

.task-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.task-name {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--foreground-primary);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  border: 1px solid;
}

.status-badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.task-target-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
}

.task-target {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.task-tag {
  padding: 1px 6px;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.06);
  font-size: 10px;
  color: var(--foreground-muted);
}

.task-cron-cell {
  display: flex;
  flex-direction: column;
}

.cron-expr {
  font-family: 'Courier New', monospace;
  font-size: var(--font-size-xs);
  color: #a5b4fc;
}

.cron-label {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.task-cell {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.task-next-cell { color: var(--foreground-secondary); }

.task-rate-cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.rate-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.rate-value {
  font-size: var(--font-size-xs);
  font-weight: 500;
}

.rate-count {
  font-size: 10px;
  color: var(--foreground-muted);
}

.rate-bar-track {
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
}

.rate-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.task-actions-cell {
  display: flex;
  align-items: center;
  gap: 2px;
}

.action-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn:hover { background: rgba(255, 255, 255, 0.08); color: var(--foreground-primary); }
.action-btn--danger:hover { background: rgba(239, 68, 68, 0.15); color: #f87171; }

/* ---- Task Detail (expanded) ---- */
.task-detail {
  border-top: 1px solid rgba(38, 51, 89, 0.15);
  background: rgba(0, 0, 0, 0.15);
  padding: 14px 20px 14px 48px;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.detail-label {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.detail-value {
  margin-top: 4px;
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}

.detail-target {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}

/* ---- Run Rows ---- */
.run-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr auto;
  gap: 16px;
  align-items: center;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.1s ease;
  border-bottom: 1px solid rgba(38, 51, 89, 0.12);
}

.run-row:hover { background: rgba(255, 255, 255, 0.02); }

.run-name-cell { min-width: 0; }

.run-task-name {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
}

.run-trigger {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.run-status-cell {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-xs);
}

.run-time,
.run-dur {
  font-family: 'Courier New', monospace;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.info-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
}

.info-btn:hover { background: rgba(255, 255, 255, 0.08); color: var(--foreground-primary); }

/* ---- Empty State ---- */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 16px;
  text-align: center;
}

.empty-icon {
  color: var(--border-medium);
  margin-bottom: 12px;
}

.empty-title {
  font-size: var(--font-size-md);
  font-weight: 500;
  color: var(--foreground-muted);
}

.empty-desc {
  margin-top: 4px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin-bottom: 16px;
}

.empty-state-sm {
  padding: 40px 16px;
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
}

/* ---- Modal ---- */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
}

.modal-card {
  width: 100%;
  max-width: 480px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-medium);
  background: var(--color-bg-card);
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.modal-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--foreground-primary);
}

.modal-desc {
  margin-top: 2px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.modal-close {
  padding: 6px;
  border-radius: var(--radius-sm);
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
}

.modal-close:hover { background: rgba(255, 255, 255, 0.08); color: var(--foreground-primary); }

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-label {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.form-input {
  padding: 8px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: rgba(255, 255, 255, 0.04);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
  transition: border-color 0.15s ease;
}

.form-input::placeholder { color: var(--foreground-muted); }
.form-input:focus { border-color: var(--color-accent); }

.form-input--mono {
  font-family: 'Courier New', monospace;
  color: #a5b4fc;
}

.form-textarea {
  padding: 8px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: rgba(255, 255, 255, 0.04);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
  resize: none;
  transition: border-color 0.15s ease;
}

.form-textarea::placeholder { color: var(--foreground-muted); }
.form-textarea:focus { border-color: var(--color-accent); }

.form-select {
  padding: 8px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: rgba(255, 255, 255, 0.04);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
  cursor: pointer;
}

.form-select:focus { border-color: var(--color-accent); }

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.cron-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}

.preset-btn {
  padding: 4px 10px;
  border-radius: 6px;
  border: none;
  background: rgba(255, 255, 255, 0.06);
  color: var(--foreground-muted);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all 0.15s ease;
}

.preset-btn:hover { background: rgba(255, 255, 255, 0.1); color: var(--foreground-primary); }

.preset-btn.active {
  background: #4f46e5;
  color: #fff;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 24px;
}

.btn-cancel {
  padding: 8px 16px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: none;
  color: var(--foreground-muted);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-cancel:hover { background: rgba(255, 255, 255, 0.06); color: var(--foreground-primary); }

/* ---- Drawer ---- */
.drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  display: flex;
  justify-content: flex-end;
  background: rgba(0, 0, 0, 0.4);
}

.drawer-panel {
  width: 384px;
  height: 100%;
  background: var(--color-bg-card);
  border-left: 1px solid var(--border-subtle);
  padding: 24px;
  overflow-y: auto;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.drawer-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--foreground-primary);
}

.drawer-close {
  padding: 6px;
  border-radius: var(--radius-sm);
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
}

.drawer-close:hover { background: rgba(255, 255, 255, 0.08); color: var(--foreground-primary); }

.drawer-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.drawer-info-card {
  border-radius: var(--radius-lg);
  background: rgba(255, 255, 255, 0.03);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.drawer-info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.drawer-label {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.drawer-value {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.drawer-output {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.drawer-code {
  border-radius: var(--radius-lg);
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-subtle);
  padding: 12px;
}

.drawer-code pre {
  white-space: pre-wrap;
  font-family: 'Courier New', monospace;
  font-size: var(--font-size-xs);
  color: var(--foreground-secondary);
  margin: 0;
}

/* ---- Responsive ---- */
@media (max-width: 1200px) {
  .status-grid { grid-template-columns: repeat(2, 1fr); }
  .detail-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
