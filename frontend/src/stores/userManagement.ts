import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import type { Department, SystemUser, CreateUserRequest, UpdateUserRequest } from '@/types/admin'
import { fetchDepartments, fetchUsers, createUser, updateUser, deleteUser } from '@/services/adminApi'

export const useUserManagementStore = defineStore('userManagement', () => {
  const departments = ref<Department[]>([])
  const users = ref<SystemUser[]>([])
  const selectedDeptId = ref<string | null>(null)
  const selectedUser = ref<SystemUser | null>(null)
  const searchQuery = ref('')
  const viewMode = ref<'card' | 'table'>('card')
  const loading = ref(false)
  const saving = ref(false)

  const filteredUsers = computed(() => {
    let list = users.value
    if (selectedDeptId.value) {
      list = list.filter((u) => u.deptId === selectedDeptId.value)
    }
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.trim().toLowerCase()
      list = list.filter(
        (u) =>
          u.name.toLowerCase().includes(q) ||
          u.employeeId.toLowerCase().includes(q) ||
          u.email.toLowerCase().includes(q) ||
          u.position.toLowerCase().includes(q),
      )
    }
    return list
  })

  function findDeptName(deptId: string): string {
    function find(ds: Department[]): string | null {
      for (const d of ds) {
        if (d.id === deptId) return d.name
        const r = find(d.children)
        if (r) return r
      }
      return null
    }
    return find(departments.value) ?? '未知部门'
  }

  async function fetchAll() {
    loading.value = true
    try {
      const [depts, us] = await Promise.all([fetchDepartments(), fetchUsers()])
      departments.value = depts
      users.value = us
    } finally {
      loading.value = false
    }
  }

  function selectDepartment(id: string | null) {
    selectedDeptId.value = id
    selectedUser.value = null
  }

  function selectUser(user: SystemUser) {
    selectedUser.value = user
  }

  async function handleCreateUser(data: CreateUserRequest) {
    saving.value = true
    try {
      const u = await createUser(data)
      users.value.unshift(u)
      return u
    } finally {
      saving.value = false
    }
  }

  async function handleUpdateUser(data: UpdateUserRequest) {
    saving.value = true
    try {
      const u = await updateUser(data)
      if (u) {
        const idx = users.value.findIndex((x) => x.id === u.id)
        if (idx !== -1) users.value[idx] = u
        if (selectedUser.value?.id === u.id) selectedUser.value = u
      }
      return u
    } finally {
      saving.value = false
    }
  }

  async function handleDeleteUser(id: string) {
    saving.value = true
    try {
      const ok = await deleteUser(id)
      if (ok) {
        users.value = users.value.filter((u) => u.id !== id)
        if (selectedUser.value?.id === id) selectedUser.value = null
      }
      return ok
    } finally {
      saving.value = false
    }
  }

  return {
    departments,
    users,
    selectedDeptId,
    selectedUser,
    searchQuery,
    viewMode,
    loading,
    saving,
    filteredUsers,
    findDeptName,
    fetchAll,
    selectDepartment,
    selectUser,
    handleCreateUser,
    handleUpdateUser,
    handleDeleteUser,
  }
})
