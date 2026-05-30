import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CronTask, RunRecord, TaskStatus, RunStatus, CreateTaskRequest } from '@/types/scheduledTask'
import * as api from '@/services/scheduledTaskApi'

export const useScheduledTaskStore = defineStore('scheduledTask', () => {
  /* ---------- state ---------- */
  const tasks = ref<CronTask[]>([])
  const runs = ref<RunRecord[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const taskSearch = ref('')
  const taskFilter = ref<'all' | TaskStatus>('all')
  const runFilter = ref<'all' | RunStatus>('all')
  const expandedTaskId = ref<string | null>(null)

  /* ---------- computed ---------- */
  const activeTasks = computed(() => tasks.value.filter((t) => t.status === 'active'))
  const nextTask = computed(() => activeTasks.value.find((t) => t.nextRun !== '待计算') ?? null)

  const filteredTasks = computed(() => {
    return tasks.value.filter((t) => {
      const q = taskSearch.value.toLowerCase()
      const matchSearch =
        !q ||
        t.name.toLowerCase().includes(q) ||
        t.target.toLowerCase().includes(q)
      const matchFilter = taskFilter.value === 'all' || t.status === taskFilter.value
      return matchSearch && matchFilter
    })
  })

  const filteredRuns = computed(() => {
    if (runFilter.value === 'all') return runs.value
    return runs.value.filter((r) => r.status === runFilter.value)
  })

  const taskStats = computed(() => ({
    total: tasks.value.length,
    active: tasks.value.filter((t) => t.status === 'active').length,
    paused: tasks.value.filter((t) => t.status === 'paused').length,
    error: tasks.value.filter((t) => t.status === 'error').length,
  }))

  const runStats = computed(() => ({
    total: runs.value.length,
    success: runs.value.filter((r) => r.status === 'success').length,
    failed: runs.value.filter((r) => r.status === 'failed').length,
    running: runs.value.filter((r) => r.status === 'running').length,
  }))

  /* ---------- actions ---------- */
  async function fetchAll() {
    loading.value = true
    error.value = null
    try {
      const [taskData, runData] = await Promise.all([api.fetchTasks(), api.fetchRuns()])
      tasks.value = taskData
      runs.value = runData
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : '加载定时任务失败'
    } finally {
      loading.value = false
    }
  }

  async function createTask(data: CreateTaskRequest) {
    try {
      const created = await api.createTask(data)
      tasks.value.unshift(created)
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('创建任务失败')
    }
  }

  async function toggleTaskStatus(id: string) {
    try {
      const updated = await api.toggleTaskStatus(id)
      const idx = tasks.value.findIndex((t) => t.id === id)
      if (idx !== -1) tasks.value[idx] = updated
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('切换状态失败')
    }
  }

  async function cloneTask(id: string) {
    try {
      const cloned = await api.cloneTask(id)
      tasks.value.unshift(cloned)
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('克隆失败')
    }
  }

  async function deleteTask(id: string) {
    try {
      await api.deleteTask(id)
      tasks.value = tasks.value.filter((t) => t.id !== id)
      if (expandedTaskId.value === id) {
        expandedTaskId.value = null
      }
    } catch (err: unknown) {
      throw err instanceof Error ? err : new Error('删除失败')
    }
  }

  function toggleExpand(id: string) {
    expandedTaskId.value = expandedTaskId.value === id ? null : id
  }

  return {
    tasks,
    runs,
    loading,
    error,
    taskSearch,
    taskFilter,
    runFilter,
    expandedTaskId,
    activeTasks,
    nextTask,
    filteredTasks,
    filteredRuns,
    taskStats,
    runStats,
    fetchAll,
    createTask,
    toggleTaskStatus,
    cloneTask,
    deleteTask,
    toggleExpand,
  }
})
