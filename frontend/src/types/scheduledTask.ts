/** 任务运行状态 */
export type TaskStatus = 'active' | 'paused' | 'error'

/** 单次执行结果状态 */
export type RunStatus = 'success' | 'failed' | 'running' | 'skipped'

/** 任务目标类型 */
export type TargetType = 'agent' | 'skill' | 'tool' | 'prompt'

/** 定时任务实体 */
export interface CronTask {
  id: string
  name: string
  description: string
  cron: string
  cronLabel: string
  status: TaskStatus
  target: string
  targetType: TargetType
  lastRun: string | null
  nextRun: string
  successRate: number
  totalRuns: number
  avgDuration: string
  tags: string[]
}

/** 执行记录 */
export interface RunRecord {
  id: string
  taskId: string
  taskName: string
  status: RunStatus
  startTime: string
  duration: string
  output: string
  trigger: 'scheduled' | 'manual'
}

/** 创建任务请求 */
export interface CreateTaskRequest {
  name: string
  description: string
  cron: string
  cronLabel: string
  target: string
  targetType: TargetType
  tags: string
}

/** 状态元数据 */
export const TASK_STATUS_META: Record<TaskStatus, { label: string; color: string; dot: string; bg: string }> = {
  active: { label: '运行中', color: '#6ee7b7', dot: '#6ee7b7', bg: 'rgba(16,185,129,0.1)' },
  paused: { label: '已暂停', color: '#fbbf24', dot: '#fbbf24', bg: 'rgba(245,158,11,0.1)' },
  error: { label: '异常', color: '#f87171', dot: '#f87171', bg: 'rgba(239,68,68,0.1)' },
}

export const RUN_STATUS_META: Record<RunStatus, { label: string; color: string; icon: string }> = {
  success: { label: '成功', color: '#6ee7b7', icon: 'CheckCircle2' },
  failed: { label: '失败', color: '#f87171', icon: 'XCircle' },
  running: { label: '运行中', color: '#a5b4fc', icon: 'Activity' },
  skipped: { label: '跳过', color: '#6b7280', icon: 'AlertCircle' },
}

export const TARGET_TYPE_LABELS: Record<TargetType, string> = {
  agent: '代理 Agent',
  skill: '技能 Skill',
  tool: '工具 Tool',
  prompt: '提示词 Prompt',
}

export const TARGET_TYPE_COLORS: Record<TargetType, string> = {
  agent: '#a5b4fc',
  skill: '#c4b5fd',
  tool: '#fbbf24',
  prompt: '#60a5fa',
}

export const CRON_PRESETS = [
  { label: '每分钟', value: '* * * * *' },
  { label: '每 5 分钟', value: '*/5 * * * *' },
  { label: '每 15 分钟', value: '*/15 * * * *' },
  { label: '每小时', value: '0 * * * *' },
  { label: '每天 00:00', value: '0 0 * * *' },
  { label: '每天 02:00', value: '0 2 * * *' },
  { label: '每周一 03:00', value: '0 3 * * 1' },
  { label: '每月 1 日', value: '0 0 1 * *' },
]
