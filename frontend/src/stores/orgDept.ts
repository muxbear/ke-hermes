import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import {
  fetchOrgNodes,
  createOrgNode,
  updateOrgNode,
  deleteOrgNodes,
} from '@/services/adminApi'
import type { OrgNode, OrgType } from '@/types/admin'

export const useOrgDeptStore = defineStore('orgDept', () => {
  const nodes = ref<OrgNode[]>([])
  const selectedId = ref<string | null>(null)
  const expandedIds = ref<Set<string>>(new Set())
  const treeSearch = ref('')
  const viewMode = ref<'card' | 'table'>('card')
  const selectedRows = ref<Set<string>>(new Set())
  const loading = ref(false)
  const saving = ref(false)

  const selectedNode = computed<OrgNode | null>(() =>
    nodes.value.find((n) => n.id === selectedId.value) ?? null,
  )

  const children = computed<OrgNode[]>(() =>
    getChildren(selectedId.value),
  )

  const isLeaf = computed(() =>
    children.value.length === 0 && !!selectedNode.value,
  )

  const ancestors = computed<OrgNode[]>(() =>
    selectedId.value ? getAncestors(selectedId.value) : [],
  )

  const roots = computed<OrgNode[]>(() => getChildren(null))

  const totalNodes = computed(() => nodes.value.length)

  const totalEmployees = computed(() =>
    nodes.value.reduce((s, n) => s + n.employeeCount, 0),
  )

  const visibleTreeIds = computed<Set<string>>(() => {
    const q = treeSearch.value.trim().toLowerCase()
    if (!q) return new Set(nodes.value.map((n) => n.id))
    const matching = nodes.value.filter(
      (n) =>
        n.name.toLowerCase().includes(q) ||
        n.code.toLowerCase().includes(q) ||
        n.leader.toLowerCase().includes(q),
    )
    const visible = new Set<string>()
    matching.forEach((n) => {
      getAncestors(n.id).forEach((a) => visible.add(a.id))
    })
    return visible
  })

  function getChildren(parentId: string | null): OrgNode[] {
    return nodes.value
      .filter((n) => n.parentId === parentId)
      .sort((a, b) => a.sort - b.sort)
  }

  function getDescendantIds(id: string): string[] {
    const kids = getChildren(id)
    return [
      ...kids.map((c) => c.id),
      ...kids.flatMap((c) => getDescendantIds(c.id)),
    ]
  }

  function getAncestors(id: string): OrgNode[] {
    const node = nodes.value.find((n) => n.id === id)
    if (!node) return []
    if (!node.parentId) return [node]
    return [...getAncestors(node.parentId), node]
  }

  async function fetchAll() {
    loading.value = true
    try {
      nodes.value = await fetchOrgNodes()
      if (!selectedId.value && nodes.value.length > 0) {
        selectedId.value = nodes.value[0].id
      }
      // 默认展开前两层
      const toExpand = new Set<string>()
      nodes.value
        .filter((n) => n.level <= 1)
        .filter((n) => nodes.value.some((c) => c.parentId === n.id))
        .forEach((n) => toExpand.add(n.id))
      expandedIds.value = toExpand
    } finally {
      loading.value = false
    }
  }

  function selectNode(id: string) {
    selectedId.value = id
    selectedRows.value = new Set()
  }

  function toggleExpand(id: string) {
    const next = new Set(expandedIds.value)
    next.has(id) ? next.delete(id) : next.add(id)
    expandedIds.value = next
  }

  function toggleRow(id: string) {
    const next = new Set(selectedRows.value)
    next.has(id) ? next.delete(id) : next.add(id)
    selectedRows.value = next
  }

  function toggleAllRows(ids: string[]) {
    if (selectedRows.value.size === ids.length && ids.length > 0) {
      selectedRows.value = new Set()
    } else {
      selectedRows.value = new Set(ids)
    }
  }

  async function handleCreate(data: {
    name: string; code: string; parentId: string | null; type: OrgType
    level: number; leader: string; phone: string; email: string
    address: string; desc: string; employeeCount: number; sort: number; status: 'active' | 'inactive'
  }) {
    saving.value = true
    try {
      const node = await createOrgNode(data)
      nodes.value.push(node)
      if (data.parentId) {
        expandedIds.value = new Set([...expandedIds.value, data.parentId])
      }
      return node
    } finally {
      saving.value = false
    }
  }

  async function handleUpdate(data: OrgNode) {
    saving.value = true
    try {
      const updated = await updateOrgNode(data)
      if (updated) {
        const idx = nodes.value.findIndex((n) => n.id === data.id)
        if (idx !== -1) nodes.value[idx] = updated
      }
    } finally {
      saving.value = false
    }
  }

  async function handleDelete(ids: string[]) {
    saving.value = true
    try {
      await deleteOrgNodes(ids)
      const toDelete = new Set(ids)
      ids.forEach((id) => getDescendantIds(id).forEach((d) => toDelete.add(d)))
      nodes.value = nodes.value.filter((n) => !toDelete.has(n.id))
      if (toDelete.has(selectedId.value!)) {
        const node = nodes.value.find((n) => n.id === selectedId.value)
        selectedId.value = node?.parentId ?? nodes.value.find((n) => !toDelete.has(n.id))?.id ?? null
      }
      selectedRows.value = new Set()
    } finally {
      saving.value = false
    }
  }

  return {
    nodes, selectedId, expandedIds, treeSearch, viewMode, selectedRows,
    loading, saving,
    selectedNode, children, isLeaf, ancestors, roots,
    totalNodes, totalEmployees, visibleTreeIds,
    getChildren, getDescendantIds, getAncestors,
    fetchAll,
    selectNode, toggleExpand, toggleRow, toggleAllRows,
    handleCreate, handleUpdate, handleDelete,
  }
})
