/**
 * Scheduled Task API — 定时任务接口（Mock 实现，后端就绪后替换）
 */
import type { CronTask, RunRecord, CreateTaskRequest } from '@/types/scheduledTask'

/* ------------------------------------------------------------------ */
/*  Mock 数据                                                          */
/* ------------------------------------------------------------------ */

let tasks: CronTask[] = [
  {
    id: 't1', name: '每日报告生成',
    description: '每天凌晨 2 点生成平台运营日报，推送至管理员',
    cron: '0 2 * * *', cronLabel: '每天 02:00',
    status: 'active', target: 'main-alpha', targetType: 'agent',
    lastRun: '今天 02:00', nextRun: '明天 02:00',
    successRate: 98, totalRuns: 62, avgDuration: '3m 12s',
    tags: ['报告', '通知'],
  },
  {
    id: 't2', name: '数据同步',
    description: '每小时同步外部数据源，更新知识库索引',
    cron: '0 * * * *', cronLabel: '每小时',
    status: 'active', target: 'data-sync-skill', targetType: 'skill',
    lastRun: '14:00', nextRun: '15:00',
    successRate: 95, totalRuns: 840, avgDuration: '48s',
    tags: ['数据', '索引'],
  },
  {
    id: 't3', name: '健康检查',
    description: '每 5 分钟探测所有代理和 MCP 服务的健康状态',
    cron: '*/5 * * * *', cronLabel: '每 5 分钟',
    status: 'active', target: 'health-check-tool', targetType: 'tool',
    lastRun: '14:25', nextRun: '14:30',
    successRate: 100, totalRuns: 4320, avgDuration: '2.1s',
    tags: ['监控'],
  },
  {
    id: 't4', name: '模型性能基准',
    description: '每周一凌晨 3 点对所有已配置模型执行 benchmark 评测',
    cron: '0 3 * * 1', cronLabel: '每周一 03:00',
    status: 'paused', target: 'sub-benchmark', targetType: 'agent',
    lastRun: '2026-05-25 03:00', nextRun: '2026-06-01 03:00',
    successRate: 89, totalRuns: 12, avgDuration: '18m 44s',
    tags: ['评测', '模型'],
  },
  {
    id: 't5', name: '日志清理',
    description: '每天凌晨 4 点清理 30 天前的运行日志和临时文件',
    cron: '0 4 * * *', cronLabel: '每天 04:00',
    status: 'error', target: 'cleanup-tool', targetType: 'tool',
    lastRun: '今天 04:00', nextRun: '明天 04:00',
    successRate: 72, totalRuns: 61, avgDuration: '1m 5s',
    tags: ['维护'],
  },
  {
    id: 't6', name: '推送通知',
    description: '每 15 分钟检查待发送通知队列，批量推送给用户',
    cron: '*/15 * * * *', cronLabel: '每 15 分钟',
    status: 'active', target: 'notify-skill', targetType: 'skill',
    lastRun: '14:15', nextRun: '14:30',
    successRate: 99, totalRuns: 2180, avgDuration: '6.3s',
    tags: ['通知'],
  },
]

const runs: RunRecord[] = [
  { id: 'r1', taskId: 't3', taskName: '健康检查', status: 'success', startTime: '14:25:00', duration: '2.3s', output: '{"ok":true,"agents":4,"mcps":6,"latency":"128ms"}', trigger: 'scheduled' },
  { id: 'r2', taskId: 't6', taskName: '推送通知', status: 'success', startTime: '14:15:01', duration: '5.8s', output: '已发送 12 条通知，队列清空。', trigger: 'scheduled' },
  { id: 'r3', taskId: 't2', taskName: '数据同步', status: 'success', startTime: '14:00:03', duration: '51s', output: '同步完成，新增 342 条记录，更新 89 条。', trigger: 'scheduled' },
  { id: 'r4', taskId: 't5', taskName: '日志清理', status: 'failed', startTime: '今天 04:00:01', duration: '8s', output: 'Error: 磁盘权限不足，无法删除 /var/log/hermes/archive/2026-04/', trigger: 'scheduled' },
  { id: 'r5', taskId: 't3', taskName: '健康检查', status: 'success', startTime: '14:20:00', duration: '1.9s', output: '{"ok":true,"agents":4,"mcps":6,"latency":"134ms"}', trigger: 'scheduled' },
  { id: 'r6', taskId: 't1', taskName: '每日报告生成', status: 'success', startTime: '今天 02:00:02', duration: '3m 08s', output: '报告生成完毕，已推送至 5 位管理员。', trigger: 'scheduled' },
  { id: 'r7', taskId: 't3', taskName: '健康检查', status: 'running', startTime: '14:28:00', duration: '—', output: '正在检测代理心跳…', trigger: 'scheduled' },
  { id: 'r8', taskId: 't2', taskName: '数据同步', status: 'success', startTime: '13:00:04', duration: '44s', output: '同步完成，新增 218 条记录，更新 51 条。', trigger: 'manual' },
]

/* ------------------------------------------------------------------ */
/*  辅助函数                                                            */
/* ------------------------------------------------------------------ */

function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}

/* ------------------------------------------------------------------ */
/*  API 函数                                                           */
/* ------------------------------------------------------------------ */

export async function fetchTasks(): Promise<CronTask[]> {
  return deepClone(tasks)
}

export async function fetchRuns(): Promise<RunRecord[]> {
  return deepClone(runs)
}

export async function createTask(data: CreateTaskRequest): Promise<CronTask> {
  const newTask: CronTask = {
    id: `t${Date.now()}`,
    name: data.name,
    description: data.description,
    cron: data.cron,
    cronLabel: data.cronLabel,
    status: 'active',
    target: data.target,
    targetType: data.targetType,
    lastRun: null,
    nextRun: '待计算',
    successRate: 100,
    totalRuns: 0,
    avgDuration: '—',
    tags: data.tags.split(',').map((t) => t.trim()).filter(Boolean),
  }
  tasks.unshift(newTask)
  return deepClone(newTask)
}

export async function toggleTaskStatus(id: string): Promise<CronTask> {
  const task = tasks.find((t) => t.id === id)
  if (!task) throw new Error('任务不存在')
  task.status = task.status === 'active' ? 'paused' : task.status === 'paused' ? 'active' : task.status
  return deepClone(task)
}

export async function deleteTask(id: string): Promise<void> {
  const idx = tasks.findIndex((t) => t.id === id)
  if (idx === -1) throw new Error('任务不存在')
  tasks.splice(idx, 1)
}

export async function cloneTask(id: string): Promise<CronTask> {
  const task = tasks.find((t) => t.id === id)
  if (!task) throw new Error('任务不存在')
  const cloned: CronTask = {
    ...deepClone(task),
    id: `t${Date.now()}`,
    name: `${task.name} (副本)`,
    status: 'paused',
    lastRun: null,
    nextRun: '待计算',
    totalRuns: 0,
  }
  tasks.unshift(cloned)
  return deepClone(cloned)
}
