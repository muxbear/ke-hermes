import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { PermResource, PermType, PermStatus, BtnVariant, RoleCoverage } from '@/types/admin'
import {
  fetchMenuResources,
  createMenuResource,
  updateMenuResource,
  deleteMenuResource,
  fetchRoleCoverages,
} from '@/services/adminApi'

export const useMenuConfigStore = defineStore('menuConfig', () => {
  const resources = ref<PermResource[]>([])
  const selectedId = ref<string | null>(null)
  const expandedIds = ref<Set<string>>(new Set())
  const activeTab = ref<'basic' | 'buttons' | 'roles'>('basic')
  const searchQuery = ref('')
  const loading = ref(false)
  const saving = ref(false)
  const saved = ref(false)

  const selected = computed(() => resources.value.find((r) => r.id === selectedId.value) ?? null)

  const buttonsOfSelected = computed(() => {
    const sel = selected.value
    if (!sel || sel.type !== 'menu') return []
    return resources.value
      .filter((r) => r.parentId === sel.id && r.type === 'button')
      .sort((a, b) => a.sortOrder - b.sortOrder)
  })

  const childrenOf = (parentId: string | null) =>
    resources.value
      .filter((r) => r.parentId === parentId)
      .sort((a, b) => a.sortOrder - b.sortOrder)

  const roots = computed(() => childrenOf(null))

  async function fetchAll() {
    loading.value = true
    try {
      resources.value = await fetchMenuResources()
      if (!selectedId.value && resources.value.length > 0) {
        selectedId.value = resources.value[0].id
      }
      expandedIds.value = new Set(resources.value.filter((r) => r.type === 'catalog').map((r) => r.id))
    } finally {
      loading.value = false
    }
  }

  function selectResource(id: string) {
    selectedId.value = id
    const r = resources.value.find((x) => x.id === id)
    if (r && r.type !== 'button') {
      activeTab.value = 'basic'
    }
  }

  function toggleExpand(id: string) {
    const next = new Set(expandedIds.value)
    next.has(id) ? next.delete(id) : next.add(id)
    expandedIds.value = next
  }

  async function handleCreate(data: {
    parentId: string | null
    type: PermType
    label: string
    permKey: string
    path?: string
    icon: string
    sortOrder: number
    status: PermStatus
    description?: string
    btnVariant?: BtnVariant
    danger?: boolean
  }) {
    saving.value = true
    try {
      const r = await createMenuResource(data)
      resources.value.push(r)
      selectedId.value = r.id
      if (data.parentId) expandedIds.value = new Set([...expandedIds.value, data.parentId])
      showSaved()
      return r
    } finally { saving.value = false }
  }

  async function handleUpdate(data: {
    id: string
    label: string
    permKey: string
    path?: string
    icon: string
    sortOrder: number
    status: PermStatus
    description?: string
    btnVariant?: BtnVariant
    danger?: boolean
  }) {
    saving.value = true
    try {
      const r = await updateMenuResource(data)
      if (r) {
        const idx = resources.value.findIndex((x) => x.id === r.id)
        if (idx !== -1) resources.value[idx] = r
      }
      showSaved()
      return r
    } finally { saving.value = false }
  }

  async function handleDelete(id: string) {
    saving.value = true
    try {
      await deleteMenuResource(id)
      const idsToDelete = new Set<string>([id])
      let changed = true
      while (changed) {
        changed = false
        for (const r of resources.value) {
          if (r.parentId && idsToDelete.has(r.parentId) && !idsToDelete.has(r.id)) {
            idsToDelete.add(r.id)
            changed = true
          }
        }
      }
      resources.value = resources.value.filter((r) => !idsToDelete.has(r.id))
      if (idsToDelete.has(selectedId.value ?? '')) {
        selectedId.value = resources.value[0]?.id ?? null
      }
      return true
    } finally { saving.value = false }
  }

  function showSaved() {
    saved.value = true
    setTimeout(() => (saved.value = false), 2000)
  }

  // 角色覆盖（模拟）
  const roleCoverages = computed<RoleCoverage[]>(() => {
    if (!selected.value) return []
    return [
      { roleKey: 'super_admin', roleName: '超级管理员', hasPermission: true },
      { roleKey: 'admin', roleName: '管理员', hasPermission: true },
      { roleKey: 'manager', roleName: '部门主管', hasPermission: selected.value.type !== 'button' },
      { roleKey: 'member', roleName: '普通成员', hasPermission: selected.value.type === 'menu' || selected.value.type === 'catalog' },
      { roleKey: 'guest', roleName: '访客', hasPermission: false },
    ]
  })

  return {
    resources,
    selectedId,
    expandedIds,
    activeTab,
    searchQuery,
    loading,
    saving,
    saved,
    selected,
    buttonsOfSelected,
    roots,
    roleCoverages,
    childrenOf,
    fetchAll,
    selectResource,
    toggleExpand,
    handleCreate,
    handleUpdate,
    handleDelete,
  }
})
