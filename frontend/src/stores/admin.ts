import { ref } from 'vue'
import { defineStore } from 'pinia'
import type { AdminTileConfig, SystemStats, UpdateLogEntry } from '@/types/admin'
import { fetchAdminTiles, fetchSystemStats, fetchUpdateLogs } from '@/services/adminApi'

export const useAdminStore = defineStore('admin', () => {
  const tiles = ref<AdminTileConfig[]>([])
  const stats = ref<SystemStats | null>(null)
  const updateLogs = ref<UpdateLogEntry[]>([])
  const loading = ref(false)

  async function fetchAll() {
    loading.value = true
    try {
      const [t, s, l] = await Promise.all([
        fetchAdminTiles(),
        fetchSystemStats(),
        fetchUpdateLogs(),
      ])
      tiles.value = t
      stats.value = s
      updateLogs.value = l
    } finally {
      loading.value = false
    }
  }

  return { tiles, stats, updateLogs, loading, fetchAll }
})
