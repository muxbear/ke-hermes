import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { RoleDef, PermResource, DataResource, DataScope } from '@/types/admin'
import {
  fetchRoles,
  fetchPermissionResources,
  fetchDataResources,
  fetchRolePerms,
  saveRolePerms,
  createRole,
  deleteRole,
  isSuperAdmin,
  INITIAL_ROLES,
  DEFAULT_ROLE_PERMS,
} from '@/services/adminApi'

export const useRbacStore = defineStore('rbac', () => {
  const roles = ref<RoleDef[]>([])
  const permResources = ref<PermResource[]>([])
  const dataResources = ref<DataResource[]>([])
  const activeRoleId = ref<string>('r1')
  const activeTab = ref<'func' | 'data'>('func')
  const searchQuery = ref('')
  const loading = ref(false)
  const saving = ref(false)

  // 权限状态：每个角色独立
  const permsMap = ref<Record<string, { granted: Set<string>; dataScope: Record<string, DataScope> }>>({})

  const activeRole = computed(() => roles.value.find((r) => r.id === activeRoleId.value) ?? null)
  const isSuper = computed(() => activeRole.value ? isSuperAdmin(activeRole.value.key) : false)
  const readonly = computed(() => {
    if (!activeRole.value) return true
    return activeRole.value.isBuiltin || isSuper.value
  })

  const activePermState = computed(() => {
    return permsMap.value[activeRoleId.value] ?? { granted: new Set<string>(), dataScope: {} }
  })

  const activeGranted = computed(() => activePermState.value.granted)

  function getChildren(permId: string): PermResource[] {
    return permResources.value.filter((r) => r.parentId === permId)
  }

  function getRoots(): PermResource[] {
    return permResources.value.filter((r) => r.parentId === null)
  }

  function getDescendantPermKeys(permId: string): string[] {
    const keys: string[] = []
    function walk(id: string) {
      const children = getChildren(id)
      for (const c of children) {
        keys.push(c.permKey)
        walk(c.id)
      }
    }
    walk(permId)
    return keys
  }

  function getAncestorChain(permId: string): string[] {
    const chain: string[] = []
    let current = permResources.value.find((r) => r.id === permId)
    while (current?.parentId) {
      chain.push(current.parentId)
      current = permResources.value.find((r) => r.id === current!.parentId)
    }
    return chain
  }

  // 计算三态：all | partial | none
  function getCheckState(permId: string): 'all' | 'partial' | 'none' {
    if (isSuper.value) return 'all'

    const node = permResources.value.find((r) => r.id === permId)
    if (!node) return 'none'

    const subKeys = getDescendantPermKeys(permId)
    if (subKeys.length === 0) {
      return activeGranted.value.has(node.permKey) ? 'all' : 'none'
    }

    const count = subKeys.filter((k) => activeGranted.value.has(k)).length
    if (count === 0) return 'none'
    if (count === subKeys.length) return 'all'
    return 'partial'
  }

  function togglePerm(permId: string) {
    if (readonly.value) return

    const node = permResources.value.find((r) => r.id === permId)
    if (!node) return

    const subKeys = [node.permKey, ...getDescendantPermKeys(permId)]
    const ancestors = getAncestorChain(permId)

    const currentGranted = permsMap.value[activeRoleId.value]?.granted ?? new Set()
    const newGranted = new Set(currentGranted)

    // 判断是全部勾选还是有部分未勾选
    const allChecked = subKeys.every((k) => currentGranted.has(k))

    if (allChecked) {
      // 全部勾选 → 全部取消
      for (const k of subKeys) newGranted.delete(k)
    } else {
      // 否则 → 全部勾选
      for (const k of subKeys) newGranted.add(k)
    }

    if (!permsMap.value[activeRoleId.value]) {
      permsMap.value[activeRoleId.value] = { granted: newGranted, dataScope: {} }
    } else {
      permsMap.value[activeRoleId.value] = {
        ...permsMap.value[activeRoleId.value],
        granted: newGranted,
      }
    }
  }

  function setDataScope(resourceId: string, scope: DataScope) {
    if (readonly.value) return
    const current = permsMap.value[activeRoleId.value] ?? { granted: new Set(), dataScope: {} }
    permsMap.value[activeRoleId.value] = {
      ...current,
      dataScope: { ...current.dataScope, [resourceId]: scope },
    }
  }

  async function fetchAll() {
    loading.value = true
    try {
      const [r, pr, dr] = await Promise.all([
        fetchRoles(),
        fetchPermissionResources(),
        fetchDataResources(),
      ])
      roles.value = r
      permResources.value = pr
      dataResources.value = dr

      // 初始化每个角色的权限
      for (const role of roles.value) {
        const state = await fetchRolePerms(role.id)
        permsMap.value[role.id] = state
      }
    } finally {
      loading.value = false
    }
  }

  function selectRole(roleId: string) {
    activeRoleId.value = roleId
  }

  async function handleSave() {
    saving.value = true
    try {
      const state = activePermState.value
      await saveRolePerms(activeRoleId.value, [...state.granted], state.dataScope)
      return true
    } finally {
      saving.value = false
    }
  }

  async function handleCreateRole(data: { name: string; description: string; copyFrom: string }) {
    const r = await createRole(data)
    roles.value.push(r)
    // 初始化权限
    const src = data.copyFrom ? DEFAULT_ROLE_PERMS[data.copyFrom] : undefined
    permsMap.value[r.id] = {
      granted: new Set(src?.perms ?? []),
      dataScope: { ...(src?.dataScope ?? {}) },
    }
    activeRoleId.value = r.id
    return r
  }

  async function handleDeleteRole(id: string) {
    await deleteRole(id)
    roles.value = roles.value.filter((r) => r.id !== id)
    delete permsMap.value[id]
    if (activeRoleId.value === id) {
      activeRoleId.value = roles.value[0]?.id ?? ''
    }
  }

  return {
    roles,
    permResources,
    dataResources,
    activeRoleId,
    activeTab,
    searchQuery,
    loading,
    saving,
    activeRole,
    isSuper,
    readonly,
    activeGranted,
    activePermState,
    getChildren,
    getRoots,
    getCheckState,
    togglePerm,
    setDataScope,
    fetchAll,
    selectRole,
    handleSave,
    handleCreateRole,
    handleDeleteRole,
  }
})
