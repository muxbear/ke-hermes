<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChevronLeft, Plus, Edit2, Trash2, Search, Users, Building2,
  FolderTree, Save, X, CheckCircle2, XCircle, Phone, Mail,
  MapPin, Hash, Calendar, LayoutGrid, List, Shield,
  ChevronRight, ChevronDown, Briefcase, Layers,
} from 'lucide-vue-next'
import { ElMessage } from 'element-plus'
import { useOrgDeptStore } from '@/stores/orgDept'
import { ORG_TYPE_CONFIG } from '@/types/admin'
import type { OrgNode, OrgType, OrgStatus } from '@/types/admin'
import OrgTreeNode from '@/components/admin/OrgTreeNode.vue'

const router = useRouter()
const store = useOrgDeptStore()

onMounted(() => {
  store.fetchAll()
})

watch(() => store.treeSearch, (q) => {
  if (!q.trim()) return
  const next = new Set(store.expandedIds)
  store.nodes.forEach((n) => {
    if (store.visibleTreeIds.has(n.id) && store.nodes.some((c) => c.parentId === n.id)) {
      next.add(n.id)
    }
  })
  store.expandedIds = next
})

// ─── 弹窗状态 ───────────────────────────────────────────────
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editNodeId = ref<string | null>(null)
const form = ref({
  name: '', code: '', parentId: null as string | null,
  type: 'dept' as OrgType, level: 0, leader: '', phone: '',
  email: '', address: '', desc: '', employeeCount: 0, sort: 1,
  status: 'active' as OrgStatus,
})

function openCreate(parentId: string) {
  const parent = store.nodes.find((n) => n.id === parentId)
  const defaultType: OrgType =
    parent?.type === 'group' ? 'center' : parent?.type === 'center' ? 'dept' : 'team'
  form.value = {
    name: '', code: '', parentId,
    type: defaultType, level: (parent?.level ?? -1) + 1,
    leader: '', phone: '', email: '', address: '', desc: '',
    employeeCount: 0, sort: store.getChildren(parentId).length + 1,
    status: 'active',
  }
  dialogMode.value = 'create'
  editNodeId.value = null
  dialogVisible.value = true
}

function openEdit(node: OrgNode) {
  form.value = {
    name: node.name, code: node.code, parentId: node.parentId,
    type: node.type, level: node.level, leader: node.leader,
    phone: node.phone, email: node.email, address: node.address,
    desc: node.desc, employeeCount: node.employeeCount, sort: node.sort,
    status: node.status,
  }
  dialogMode.value = 'edit'
  editNodeId.value = node.id
  dialogVisible.value = true
}

function closeDialog() {
  dialogVisible.value = false
  editNodeId.value = null
}

async function handleSave() {
  if (!form.value.name.trim() || !form.value.code.trim()) return
  if (dialogMode.value === 'create') {
    await store.handleCreate({ ...form.value, name: form.value.name.trim(), code: form.value.code.trim().toUpperCase() })
    ElMessage.success('节点创建成功')
  } else if (editNodeId.value) {
    await store.handleUpdate({
      ...form.value,
      id: editNodeId.value,
      name: form.value.name.trim(),
      code: form.value.code.trim().toUpperCase(),
      createdAt: store.nodes.find(n => n.id === editNodeId.value)?.createdAt ?? '',
      employeeCount: form.value.employeeCount,
    } as OrgNode)
    ElMessage.success('节点更新成功')
  }
  closeDialog()
}

// ─── 删除确认 ───────────────────────────────────────────────
const deleteConfirm = ref<{ ids: string[]; names: string[] } | null>(null)

function openDelete(ids: string[]) {
  deleteConfirm.value = {
    ids,
    names: ids.map((id) => store.nodes.find((n) => n.id === id)?.name ?? id),
  }
}

async function handleDelete() {
  if (!deleteConfirm.value) return
  await store.handleDelete(deleteConfirm.value.ids)
  ElMessage.success('删除成功')
  deleteConfirm.value = null
}

// ─── Helper ────────────────────────────────────────────────
function iconNameToComponent(name: string) {
  const map: Record<string, any> = { Building2, Briefcase, Layers, Users }
  return map[name] ?? Building2
}

function getStatusBadgeClass(status: string) {
  return status === 'active' ? 'badge-emerald' : 'badge-slate'
}
</script>

<template>
  <div class="od-page">
    <!-- Header -->
    <div class="od-topbar">
      <div class="od-topbar-left">
        <button class="od-back-btn" @click="router.push('/admin')">
          <ChevronLeft :size="16" />
          <span>返回</span>
        </button>
        <div class="od-topbar-divider"></div>
        <div class="od-topbar-icon">
          <FolderTree :size="20" />
        </div>
        <div>
          <h1 class="od-topbar-title">机构部门</h1>
          <p class="od-topbar-sub">组织架构管理 · 部门层级配置与人员归属</p>
        </div>
      </div>
      <div class="od-topbar-right">
        <span class="od-stats">
          共 {{ store.totalNodes }} 个节点 · {{ store.totalEmployees }} 人
        </span>
      </div>
    </div>

    <!-- Body -->
    <div class="od-body">
      <!-- Left Tree Panel -->
      <div class="od-tree-panel">
        <div class="od-tree-search">
          <Search :size="14" class="od-tree-search-icon" />
          <input
            v-model="store.treeSearch"
            type="text"
            placeholder="搜索节点名称/编码…"
            class="od-tree-search-input"
          />
          <button
            v-if="store.treeSearch"
            class="od-tree-search-clear"
            @click="store.treeSearch = ''"
          >
            <X :size="12" />
          </button>
        </div>
        <div v-if="store.treeSearch" class="od-tree-search-count">
          找到 {{ store.visibleTreeIds.size }} 个匹配节点
        </div>
        <div class="od-tree-scroll">
          <OrgTreeNode
            v-for="node in store.roots.filter(n => store.visibleTreeIds.has(n.id))"
            :key="node.id"
            :node="node"
            :depth="0"
            :selected-id="store.selectedId"
            :expanded-ids="store.expandedIds"
            :visible-ids="store.visibleTreeIds"
            :search-query="store.treeSearch"
            @select="store.selectNode"
            @toggle="store.toggleExpand"
            @add-child="openCreate"
            @edit="openEdit"
            @delete="(n: OrgNode) => openDelete([n.id])"
          />
        </div>
      </div>

      <!-- Right Content Area -->
      <div class="od-content">
        <!-- Empty State -->
        <div v-if="!store.selectedNode" class="od-empty">
          <FolderTree :size="40" class="od-empty-icon" />
          <div class="od-empty-text">从左侧选择一个节点</div>
        </div>

        <!-- Leaf Detail View -->
        <template v-else-if="store.isLeaf && store.selectedNode">
          <div class="od-leaf">
            <div class="od-leaf-header">
              <div>
                <div class="od-breadcrumb">
                  <span
                    v-for="(a, i) in store.ancestors"
                    :key="a.id"
                    class="od-breadcrumb-item"
                  >
                    <ChevronRight v-if="i > 0" :size="12" class="od-breadcrumb-sep" />
                    <span :class="{ active: i === store.ancestors.length - 1 }">{{ a.name }}</span>
                  </span>
                </div>
                <div class="od-leaf-title-row">
                  <div class="od-leaf-icon-lg">
                    <component :is="iconNameToComponent(ORG_TYPE_CONFIG[store.selectedNode.type].icon)" :size="24" />
                  </div>
                  <div>
                    <div class="od-leaf-tags">
                      <h2 class="od-leaf-name">{{ store.selectedNode.name }}</h2>
                      <span :class="['od-badge', ORG_TYPE_CONFIG[store.selectedNode.type].cls]">
                        {{ ORG_TYPE_CONFIG[store.selectedNode.type].label }}
                      </span>
                      <span :class="['od-badge', getStatusBadgeClass(store.selectedNode.status)]">
                        <CheckCircle2 v-if="store.selectedNode.status === 'active'" :size="12" />
                        <XCircle v-else :size="12" />
                        {{ store.selectedNode.status === 'active' ? '启用' : '停用' }}
                      </span>
                    </div>
                    <p class="od-leaf-desc">{{ store.selectedNode.desc || '暂无描述' }}</p>
                  </div>
                </div>
              </div>
              <div class="od-leaf-header-actions">
                <button class="od-btn-outline" @click="openEdit(store.selectedNode!)">
                  <Edit2 :size="14" />编辑
                </button>
                <button class="od-btn-outline-danger" @click="openDelete([store.selectedNode!.id])">
                  <Trash2 :size="14" />删除
                </button>
              </div>
            </div>

            <div class="od-leaf-body">
              <div class="od-leaf-main">
                <div class="od-panel">
                  <h3 class="od-panel-title"><Building2 :size="16" />基本信息</h3>
                  <div class="od-info-grid">
                    <div class="od-info-cell">
                      <div class="od-info-cell-icon"><Hash :size="14" /></div>
                      <div>
                        <div class="od-info-cell-label">部门编码</div>
                        <div class="od-info-cell-value">{{ store.selectedNode.code }}</div>
                      </div>
                    </div>
                    <div class="od-info-cell">
                      <div class="od-info-cell-icon"><Users :size="14" /></div>
                      <div>
                        <div class="od-info-cell-label">负责人</div>
                        <div class="od-info-cell-value">{{ store.selectedNode.leader || '未设置' }}</div>
                      </div>
                    </div>
                    <div class="od-info-cell">
                      <div class="od-info-cell-icon"><Phone :size="14" /></div>
                      <div>
                        <div class="od-info-cell-label">联系电话</div>
                        <div class="od-info-cell-value">{{ store.selectedNode.phone || '未设置' }}</div>
                      </div>
                    </div>
                    <div class="od-info-cell">
                      <div class="od-info-cell-icon"><Mail :size="14" /></div>
                      <div>
                        <div class="od-info-cell-label">邮箱</div>
                        <div class="od-info-cell-value">{{ store.selectedNode.email || '未设置' }}</div>
                      </div>
                    </div>
                    <div class="od-info-cell">
                      <div class="od-info-cell-icon"><MapPin :size="14" /></div>
                      <div>
                        <div class="od-info-cell-label">办公地址</div>
                        <div class="od-info-cell-value">{{ store.selectedNode.address || '未设置' }}</div>
                      </div>
                    </div>
                    <div class="od-info-cell">
                      <div class="od-info-cell-icon"><Users :size="14" /></div>
                      <div>
                        <div class="od-info-cell-label">员工人数</div>
                        <div class="od-info-cell-value">{{ store.selectedNode.employeeCount }} 人</div>
                      </div>
                    </div>
                    <div class="od-info-cell">
                      <div class="od-info-cell-icon">
                        <Building2 :size="14" />
                      </div>
                      <div>
                        <div class="od-info-cell-label">上级节点</div>
                        <div class="od-info-cell-value">
                          {{ store.nodes.find(n => n.id === store.selectedNode?.parentId)?.name ?? '根节点' }}
                        </div>
                      </div>
                    </div>
                    <div class="od-info-cell">
                      <div class="od-info-cell-icon"><Calendar :size="14" /></div>
                      <div>
                        <div class="od-info-cell-label">创建日期</div>
                        <div class="od-info-cell-value">{{ store.selectedNode.createdAt }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="od-leaf-side">
                <div class="od-panel">
                  <h3 class="od-panel-title"><Shield :size="16" />节点信息</h3>
                  <div class="od-side-rows">
                    <div class="od-side-row">
                      <span class="od-side-label">层级深度</span>
                      <span class="od-side-value">第 {{ store.selectedNode.level + 1 }} 层</span>
                    </div>
                    <div class="od-side-row">
                      <span class="od-side-label">节点类型</span>
                      <span :class="['od-badge', 'od-badge-sm', ORG_TYPE_CONFIG[store.selectedNode.type].cls]">
                        {{ ORG_TYPE_CONFIG[store.selectedNode.type].label }}
                      </span>
                    </div>
                    <div class="od-side-row">
                      <span class="od-side-label">状态</span>
                      <span :class="['od-badge', 'od-badge-sm', getStatusBadgeClass(store.selectedNode.status)]">
                        {{ store.selectedNode.status === 'active' ? '启用' : '停用' }}
                      </span>
                    </div>
                    <div class="od-side-row">
                      <span class="od-side-label">员工人数</span>
                      <span class="od-side-value">{{ store.selectedNode.employeeCount }} 人</span>
                    </div>
                    <div class="od-side-row">
                      <span class="od-side-label">排序权重</span>
                      <span class="od-side-value">{{ store.selectedNode.sort }}</span>
                    </div>
                  </div>
                </div>
                <div class="od-panel">
                  <h3 class="od-panel-title">快速操作</h3>
                  <button class="od-quick-btn" @click="openEdit(store.selectedNode!)">
                    <Edit2 :size="14" class="text-cyan" />编辑节点信息
                  </button>
                  <button class="od-quick-btn danger" @click="openDelete([store.selectedNode!.id])">
                    <Trash2 :size="14" class="text-rose" />删除此节点
                  </button>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- Children View (parent node) -->
        <template v-else-if="store.selectedNode">
          <div class="od-children">
            <div class="od-children-header">
              <div>
                <div class="od-breadcrumb">
                  <span
                    v-for="(a, i) in store.ancestors"
                    :key="a.id"
                    class="od-breadcrumb-item"
                  >
                    <ChevronRight v-if="i > 0" :size="12" class="od-breadcrumb-sep" />
                    <span :class="{ active: i === store.ancestors.length - 1 }">{{ a.name }}</span>
                  </span>
                </div>
                <div class="od-children-title-row">
                  <div class="od-children-icon">
                    <component :is="iconNameToComponent(ORG_TYPE_CONFIG[store.selectedNode.type].icon)" :size="20" />
                  </div>
                  <div>
                    <div class="od-children-tags">
                      <h2 class="od-children-name">{{ store.selectedNode.name }}</h2>
                      <span :class="['od-badge', ORG_TYPE_CONFIG[store.selectedNode.type].cls]">
                        {{ ORG_TYPE_CONFIG[store.selectedNode.type].label }}
                      </span>
                      <span :class="['od-badge', getStatusBadgeClass(store.selectedNode.status)]">
                        {{ store.selectedNode.status === 'active' ? '启用' : '停用' }}
                      </span>
                    </div>
                    <div class="od-children-sub">
                      {{ store.selectedNode.desc }} · {{ store.selectedNode.employeeCount }} 人 · {{ store.children.length }} 个直属子节点
                    </div>
                  </div>
                </div>
              </div>
              <div class="od-children-actions">
                <button
                  v-if="store.selectedRows.size > 0"
                  class="od-btn-outline-danger"
                  @click="openDelete(Array.from(store.selectedRows))"
                >
                  <Trash2 :size="14" />批量删除 ({{ store.selectedRows.size }})
                </button>
                <div class="od-view-toggle">
                  <button
                    :class="['od-view-toggle-btn', { active: store.viewMode === 'card' }]"
                    @click="store.viewMode = 'card'"
                  >
                    <LayoutGrid :size="14" />卡片
                  </button>
                  <button
                    :class="['od-view-toggle-btn', { active: store.viewMode === 'table' }]"
                    @click="store.viewMode = 'table'"
                  >
                    <List :size="14" />列表
                  </button>
                </div>
              </div>
            </div>

            <!-- Card Grid -->
            <div v-if="store.viewMode === 'card'" class="od-card-grid">
              <div
                v-for="child in store.children"
                :key="child.id"
                :class="['od-card', { selected: store.selectedRows.has(child.id) }]"
                @click="store.selectNode(child.id)"
              >
                <div class="od-card-top">
                  <div class="od-card-top-left">
                    <input
                      type="checkbox"
                      :checked="store.selectedRows.has(child.id)"
                      class="od-checkbox"
                      @change="store.toggleRow(child.id)"
                      @click.stop
                    />
                    <div class="od-card-icon">
                      <component :is="iconNameToComponent(ORG_TYPE_CONFIG[child.type].icon)" :size="16" />
                    </div>
                  </div>
                  <span :class="['od-badge', 'od-badge-sm', getStatusBadgeClass(child.status)]">
                    {{ child.status === 'active' ? '启用' : '停用' }}
                  </span>
                </div>
                <div class="od-card-name">{{ child.name }}</div>
                <div class="od-card-code">{{ child.code }}</div>
                <span :class="['od-badge', 'od-badge-sm', ORG_TYPE_CONFIG[child.type].cls]">
                  {{ ORG_TYPE_CONFIG[child.type].label }}
                </span>
                <p class="od-card-desc">{{ child.desc || '暂无描述' }}</p>
                <div class="od-card-divider"></div>
                <div class="od-card-bottom">
                  <div class="od-card-info">
                    <div class="od-card-info-row">
                      <Users :size="12" />{{ child.leader || '未设置' }}
                    </div>
                    <div class="od-card-info-row">
                      <Users :size="12" />{{ child.employeeCount }} 人
                      <template v-if="store.nodes.filter(n => n.parentId === child.id).length > 0">
                        · {{ store.nodes.filter(n => n.parentId === child.id).length }} 子节点
                      </template>
                    </div>
                  </div>
                  <div class="od-card-card-actions" @click.stop>
                    <button class="od-icon-btn" title="编辑" @click="openEdit(child)">
                      <Edit2 :size="14" />
                    </button>
                    <button class="od-icon-btn danger" title="删除" @click="openDelete([child.id])">
                      <Trash2 :size="14" />
                    </button>
                  </div>
                </div>
              </div>
              <div class="od-card-add" @click="openCreate(store.selectedNode!.id)">
                <div class="od-card-add-icon"><Plus :size="20" /></div>
                <div class="od-card-add-text">新建子节点</div>
              </div>
            </div>

            <!-- Table View -->
            <div v-else class="od-table-wrap">
              <table class="od-table">
                <thead>
                  <tr>
                    <th class="od-th-check">
                      <input
                        type="checkbox"
                        :checked="store.selectedRows.size === store.children.length && store.children.length > 0"
                        class="od-checkbox"
                        @change="store.toggleAllRows(store.children.map(c => c.id))"
                      />
                    </th>
                    <th>名称 / 编码</th>
                    <th>类型</th>
                    <th>负责人</th>
                    <th>联系方式</th>
                    <th class="od-th-center">员工数</th>
                    <th class="od-th-center">子节点</th>
                    <th>状态</th>
                    <th class="od-th-right">操作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="store.children.length === 0">
                    <td colspan="9" class="od-td-empty">
                      <Users :size="32" />
                      <div>暂无直属子节点，点击右上角新建</div>
                    </td>
                  </tr>
                  <tr
                    v-for="child in store.children"
                    :key="child.id"
                    :class="['od-tr', { selected: store.selectedRows.has(child.id) }]"
                    @click="store.selectNode(child.id)"
                  >
                    <td>
                      <input
                        type="checkbox"
                        :checked="store.selectedRows.has(child.id)"
                        class="od-checkbox"
                        @change="store.toggleRow(child.id)"
                        @click.stop
                      />
                    </td>
                    <td>
                      <div class="od-td-name">
                        <div class="od-td-icon">
                          <component :is="iconNameToComponent(ORG_TYPE_CONFIG[child.type].icon)" :size="16" />
                        </div>
                        <div>
                          <div class="od-td-title">{{ child.name }}</div>
                          <div class="od-td-code">{{ child.code }}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span :class="['od-badge', 'od-badge-sm', ORG_TYPE_CONFIG[child.type].cls]">
                        {{ ORG_TYPE_CONFIG[child.type].label }}
                      </span>
                    </td>
                    <td class="od-td-text">{{ child.leader || '-' }}</td>
                    <td>
                      <div class="od-td-text">{{ child.phone || '-' }}</div>
                      <div class="od-td-muted">{{ child.email || '-' }}</div>
                    </td>
                    <td class="od-td-center">{{ child.employeeCount }}</td>
                    <td class="od-td-center">
                      {{ store.nodes.filter(n => n.parentId === child.id).length }}
                    </td>
                    <td>
                      <span :class="['od-badge', 'od-badge-sm', getStatusBadgeClass(child.status)]">
                        {{ child.status === 'active' ? '启用' : '停用' }}
                      </span>
                    </td>
                    <td class="od-td-actions" @click.stop>
                      <button class="od-icon-btn" title="编辑" @click="openEdit(child)">
                        <Edit2 :size="14" />
                      </button>
                      <button class="od-icon-btn danger" title="删除" @click="openDelete([child.id])">
                        <Trash2 :size="14" />
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Add/Edit Dialog -->
    <Teleport to="body">
      <div v-if="dialogVisible" class="od-overlay" @click.self="closeDialog">
        <div class="od-dialog">
          <div class="od-dialog-header">
            <h2 class="od-dialog-title">
              <Plus v-if="dialogMode === 'create'" :size="16" class="text-blue" />
              <Edit2 v-else :size="16" class="text-cyan" />
              {{ dialogMode === 'create' ? '新建子节点' : `编辑节点 · ${form.name}` }}
            </h2>
            <button class="od-dialog-close" @click="closeDialog"><X :size="16" /></button>
          </div>
          <div class="od-dialog-body">
            <div class="od-form-grid">
              <div class="od-form-full">
                <label class="od-label">节点名称 *</label>
                <input v-model="form.name" class="od-input" placeholder="例: 研发中心" />
              </div>
              <div>
                <label class="od-label">编码 *</label>
                <input
                  v-model="form.code"
                  class="od-input"
                  placeholder="例: RD"
                  @input="form.code = form.code.toUpperCase()"
                />
              </div>
              <div>
                <label class="od-label">节点类型</label>
                <select v-model="form.type" class="od-input">
                  <option v-for="(cfg, key) in ORG_TYPE_CONFIG" :key="key" :value="key">
                    {{ cfg.label }}
                  </option>
                </select>
              </div>
              <div>
                <label class="od-label">负责人</label>
                <input v-model="form.leader" class="od-input" placeholder="姓名" />
              </div>
              <div>
                <label class="od-label">联系电话</label>
                <input v-model="form.phone" class="od-input" placeholder="010-XXXXXXXX" />
              </div>
              <div>
                <label class="od-label">邮箱</label>
                <input v-model="form.email" class="od-input" placeholder="xxx@company.com" />
              </div>
              <div>
                <label class="od-label">员工人数</label>
                <input v-model.number="form.employeeCount" type="number" min="0" class="od-input" />
              </div>
              <div>
                <label class="od-label">排序权重</label>
                <input v-model.number="form.sort" type="number" min="1" class="od-input" />
              </div>
              <div class="od-form-full">
                <label class="od-label">办公地址</label>
                <input v-model="form.address" class="od-input" placeholder="楼栋 / 楼层" />
              </div>
              <div class="od-form-full">
                <label class="od-label">备注描述</label>
                <textarea v-model="form.desc" class="od-textarea" rows="2" placeholder="部门职能简介（可选）"></textarea>
              </div>
              <div class="od-form-full">
                <div class="od-status-toggle">
                  <div>
                    <div class="od-status-label">启用状态</div>
                    <div class="od-status-desc">停用后该节点不参与人员归属分配</div>
                  </div>
                  <label class="od-switch">
                    <input v-model="form.status" true-value="active" false-value="inactive" type="checkbox" />
                    <span class="od-switch-slider"></span>
                  </label>
                </div>
              </div>
            </div>
          </div>
          <div class="od-dialog-footer">
            <button class="od-btn-cancel" @click="closeDialog">取消</button>
            <button
              class="od-btn-save"
              :disabled="!form.name.trim() || !form.code.trim()"
              @click="handleSave"
            >
              <Save :size="14" />保存
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete Confirm Dialog -->
    <Teleport to="body">
      <div v-if="deleteConfirm" class="od-overlay" @click.self="deleteConfirm = null">
        <div class="od-alert">
          <div class="od-alert-header">
            <Trash2 :size="18" class="text-rose" />
            <span>确认删除{{ deleteConfirm.ids.length > 1 ? `这 ${deleteConfirm.ids.length} 个节点` : '此节点' }}？</span>
          </div>
          <div class="od-alert-tags">
            <span v-for="(name, i) in deleteConfirm.names" :key="i" class="od-alert-tag">
              {{ name }}
            </span>
          </div>
          <p class="od-alert-desc">删除后其下所有子节点也将一并移除，且操作无法撤销。</p>
          <div class="od-alert-actions">
            <button class="od-btn-cancel" @click="deleteConfirm = null">取消</button>
            <button class="od-btn-danger" @click="handleDelete">
              <Trash2 :size="14" />确认删除
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
/* ========================================
   OrgDeptView — 机构部门管理页面
   ======================================== */

/* === Page Layout === */
.od-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--surface-primary);
  color: var(--foreground-primary);
}

/* === Top Bar === */
.od-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  background: var(--surface-card);
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.od-topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.od-back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: transparent;
  border: none;
  color: var(--foreground-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: color var(--transition-duration);
}
.od-back-btn:hover { color: var(--foreground-primary); }
.od-topbar-divider {
  width: 1px; height: 20px;
  background: var(--border-subtle);
}
.od-topbar-icon {
  width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(168,85,247,0.2));
  color: var(--accent-primary);
}
.od-topbar-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  margin: 0;
  color: var(--foreground-primary);
}
.od-topbar-sub {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin: 1px 0 0;
}
.od-topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.od-stats {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

/* === Body === */
.od-body {
  display: flex;
  flex: 1;
  min-height: 0;
  gap: 0;
}

/* === Left Tree Panel === */
.od-tree-panel {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-subtle);
  background: var(--surface-card);
}
.od-tree-search {
  position: relative;
  padding: 12px;
}
.od-tree-search-icon {
  position: absolute;
  left: 22px; top: 50%;
  transform: translateY(-50%);
  color: var(--foreground-muted);
}
.od-tree-search-input {
  width: 100%;
  padding: 7px 28px 7px 30px;
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
}
.od-tree-search-input:focus { border-color: var(--accent-primary); }
.od-tree-search-clear {
  position: absolute;
  right: 20px; top: 50%;
  transform: translateY(-50%);
  background: none; border: none;
  color: var(--foreground-muted);
  cursor: pointer; padding: 2px;
}
.od-tree-search-clear:hover { color: var(--foreground-primary); }
.od-tree-search-count {
  padding: 0 12px 8px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}
.od-tree-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 4px 6px;
}

/* === Right Content === */
.od-content {
  flex: 1; min-width: 0;
  overflow-y: auto;
  padding: 20px 24px;
}
.od-empty {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 200px; color: var(--foreground-muted);
}
.od-empty-icon { opacity: 0.4; margin-bottom: 8px; }
.od-empty-text { font-size: var(--font-size-sm); }

/* === Breadcrumb === */
.od-breadcrumb {
  display: flex; align-items: center; gap: 2px;
  font-size: var(--font-size-xs); color: var(--foreground-muted);
  flex-wrap: wrap; margin-bottom: 6px;
}
.od-breadcrumb-item { display: flex; align-items: center; gap: 2px; }
.od-breadcrumb-sep { opacity: 0.5; }
.od-breadcrumb-item span.active { color: var(--foreground-primary); }

/* === Children View === */
.od-children { display: flex; flex-direction: column; gap: 16px; }
.od-children-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 16px; flex-wrap: wrap;
}
.od-children-title-row {
  display: flex; align-items: center; gap: 10px; margin-top: 4px;
}
.od-children-icon {
  width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-lg);
  background: rgba(59,130,246,0.12);
  border: 1px solid rgba(59,130,246,0.2);
  color: var(--accent-primary);
  flex-shrink: 0;
}
.od-children-tags {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
}
.od-children-name {
  font-size: var(--font-size-lg); font-weight: var(--font-weight-medium);
  margin: 0; color: var(--foreground-primary);
}
.od-children-sub {
  font-size: var(--font-size-xs); color: var(--foreground-muted); margin-top: 2px;
}
.od-children-actions {
  display: flex; align-items: center; gap: 8px;
  flex-shrink: 0; flex-wrap: wrap;
}

/* === View Toggle === */
.od-view-toggle {
  display: flex; align-items: center;
  border-radius: var(--radius-md);
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  padding: 2px;
}
.od-view-toggle-btn {
  display: flex; align-items: center; gap: 4px;
  padding: 5px 10px; border: none; border-radius: var(--radius-sm);
  background: transparent; color: var(--foreground-muted);
  font-size: var(--font-size-xs); cursor: pointer;
  transition: all var(--transition-fast);
}
.od-view-toggle-btn.active {
  background: rgba(59,130,246,0.2);
  color: var(--foreground-primary);
  border: 1px solid rgba(59,130,246,0.3);
}

/* === Card Grid === */
.od-card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}

/* === Card === */
.od-card {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 18px;
  cursor: pointer;
  transition: border-color var(--transition-fast), background var(--transition-fast);
}
.od-card:hover, .od-card.selected {
  border-color: rgba(59,130,246,0.35);
  background: rgba(59,130,246,0.06);
}
.od-card.selected { border-color: rgba(59,130,246,0.4); background: rgba(59,130,246,0.08); }
.od-card-top {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 10px;
}
.od-card-top-left { display: flex; align-items: center; gap: 8px; }
.od-card-icon {
  width: 32px; height: 32px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-md);
  background: rgba(59,130,246,0.1);
  border: 1px solid rgba(59,130,246,0.15);
  color: var(--accent-primary);
}
.od-card-name {
  font-size: var(--font-size-md); color: var(--foreground-primary);
  margin-bottom: 2px;
}
.od-card-code { font-size: 10px; color: var(--foreground-muted); margin-bottom: 6px; }
.od-card-desc {
  font-size: var(--font-size-xs); color: var(--foreground-muted);
  margin: 6px 0 10px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: 28px; line-height: 1.4;
}
.od-card-divider {
  height: 1px; background: var(--border-subtle); margin-bottom: 10px;
}
.od-card-bottom {
  display: flex; align-items: center; justify-content: space-between;
}
.od-card-info { display: flex; flex-direction: column; gap: 3px; }
.od-card-info-row {
  display: flex; align-items: center; gap: 4px;
  font-size: var(--font-size-xs); color: var(--foreground-secondary);
}
.od-card-card-actions { display: flex; gap: 2px; }

.od-card-add {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 8px; min-height: 200px;
  border: 2px dashed var(--border-subtle);
  border-radius: var(--radius-xl);
  cursor: pointer; transition: border-color var(--transition-fast);
}
.od-card-add:hover { border-color: rgba(59,130,246,0.4); }
.od-card-add-icon {
  width: 40px; height: 40px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-lg);
  background: rgba(59,130,246,0.08);
  border: 1px solid rgba(59,130,246,0.2);
  color: var(--accent-primary);
}
.od-card-add-text { font-size: var(--font-size-sm); color: var(--foreground-muted); }

/* === Table === */
.od-table-wrap {
  border-radius: var(--radius-xl);
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}
.od-table { width: 100%; border-collapse: collapse; font-size: var(--font-size-sm); }
.od-table thead {
  background: var(--surface-primary);
  color: var(--foreground-muted);
  font-size: var(--font-size-xs);
}
.od-table th {
  padding: 8px 12px;
  text-align: left;
  font-weight: var(--font-weight-medium);
}
.od-th-check { width: 36px; }
.od-th-center { text-align: center; }
.od-th-right { text-align: right; }
.od-tr {
  border-top: 1px solid var(--border-subtle);
  cursor: pointer;
  transition: background var(--transition-fast);
}
.od-tr:hover { background: rgba(59,130,246,0.04); }
.od-tr.selected { background: rgba(59,130,246,0.08); }
.od-table td { padding: 8px 12px; }
.od-td-name { display: flex; align-items: center; gap: 8px; }
.od-td-icon {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-md);
  background: rgba(59,130,246,0.08);
  color: var(--accent-primary);
  flex-shrink: 0;
}
.od-td-title { color: var(--foreground-primary); }
.od-td-code { font-size: 10px; color: var(--foreground-muted); }
.od-td-text { font-size: var(--font-size-xs); color: var(--foreground-primary); }
.od-td-muted { font-size: var(--font-size-xs); color: var(--foreground-muted); }
.od-td-center { text-align: center; color: var(--foreground-primary); }
.od-td-actions { display: flex; justify-content: flex-end; gap: 2px; }
.od-td-empty {
  text-align: center; padding: 36px 12px !important;
  color: var(--foreground-muted);
}

/* === Leaf Detail === */
.od-leaf { display: flex; flex-direction: column; gap: 16px; }
.od-leaf-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  gap: 16px; flex-wrap: wrap;
}
.od-leaf-title-row { display: flex; align-items: center; gap: 12px; margin-top: 4px; }
.od-leaf-icon-lg {
  width: 44px; height: 44px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-lg);
  background: rgba(59,130,246,0.12);
  border: 1px solid rgba(59,130,246,0.2);
  color: var(--accent-primary);
  flex-shrink: 0;
}
.od-leaf-tags { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.od-leaf-name {
  font-size: var(--font-size-lg); font-weight: var(--font-weight-medium);
  margin: 0; color: var(--foreground-primary);
}
.od-leaf-desc { font-size: var(--font-size-xs); color: var(--foreground-muted); margin-top: 2px; }
.od-leaf-header-actions { display: flex; gap: 8px; flex-shrink: 0; }
.od-leaf-body { display: grid; grid-template-columns: 2fr 1fr; gap: 14px; }
.od-leaf-main { min-width: 0; }
.od-leaf-side { display: flex; flex-direction: column; gap: 12px; }

/* === Panel === */
.od-panel {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 18px;
}
.od-panel-title {
  display: flex; align-items: center; gap: 8px;
  font-size: var(--font-size-sm); font-weight: var(--font-weight-medium);
  color: var(--foreground-primary); margin: 0 0 14px;
}

/* === Info Grid === */
.od-info-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
}
.od-info-cell {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 12px;
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
}
.od-info-cell-icon {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  border-radius: var(--radius-md);
  background: rgba(100,116,139,0.1);
  color: var(--foreground-muted);
  flex-shrink: 0;
}
.od-info-cell-label {
  font-size: 10px; color: var(--foreground-muted); margin-bottom: 1px;
}
.od-info-cell-value {
  font-size: var(--font-size-sm); color: var(--foreground-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* === Sidebar Rows === */
.od-side-rows { display: flex; flex-direction: column; gap: 8px; }
.od-side-row {
  display: flex; align-items: center; justify-content: space-between;
  font-size: var(--font-size-xs);
}
.od-side-label { color: var(--foreground-muted); }
.od-side-value { color: var(--foreground-primary); }

/* === Quick Actions === */
.od-quick-btn {
  width: 100%; display: flex; align-items: center; gap: 8px;
  padding: 8px 12px; margin-bottom: 6px;
  background: rgba(255,255,255,0.03);
  border: none; border-radius: var(--radius-md);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm); cursor: pointer;
  transition: background var(--transition-fast);
}
.od-quick-btn:hover { background: rgba(255,255,255,0.06); }
.od-quick-btn.danger:hover { background: rgba(244,63,94,0.1); color: #fb7185; }
.od-quick-btn:last-child { margin-bottom: 0; }

/* === Buttons === */
.od-btn-primary {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 18px; border: none; border-radius: var(--radius-md);
  background: var(--accent-primary); color: #fff;
  font-size: var(--font-size-sm); cursor: pointer;
  transition: filter var(--transition-fast);
}
.od-btn-primary:hover { filter: brightness(1.1); }
.od-btn-outline {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 7px 14px; border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-primary);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm); cursor: pointer;
  transition: background var(--transition-fast);
}
.od-btn-outline:hover { background: rgba(255,255,255,0.04); }
.od-btn-outline-danger {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 7px 14px; border: 1px solid rgba(244,63,94,0.3);
  border-radius: var(--radius-md);
  background: rgba(244,63,94,0.08);
  color: #fb7185;
  font-size: var(--font-size-sm); cursor: pointer;
}
.od-btn-outline-danger:hover { background: rgba(244,63,94,0.15); }
.od-btn-cancel {
  padding: 7px 18px; border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: var(--surface-primary);
  color: var(--foreground-secondary);
  font-size: var(--font-size-sm); cursor: pointer;
}
.od-btn-cancel:hover { background: rgba(255,255,255,0.04); }
.od-btn-save {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 18px; border: none; border-radius: var(--radius-md);
  background: var(--accent-primary); color: #fff;
  font-size: var(--font-size-sm); cursor: pointer;
}
.od-btn-save:hover { filter: brightness(1.1); }
.od-btn-save:disabled { opacity: 0.5; cursor: not-allowed; }
.od-btn-danger {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 18px; border: none; border-radius: var(--radius-md);
  background: #e11d48; color: #fff;
  font-size: var(--font-size-sm); cursor: pointer;
}
.od-btn-danger:hover { background: #f43f5e; }
.od-icon-btn {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: none; border: none;
  border-radius: var(--radius-sm);
  color: var(--foreground-muted);
  cursor: pointer; transition: all var(--transition-fast);
}
.od-icon-btn:hover { color: #22d3ee; background: rgba(6,182,212,0.12); }
.od-icon-btn.danger:hover { color: #fb7185; background: rgba(244,63,94,0.12); }

/* === Badges === */
.od-badge {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 2px 8px; border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  border: 1px solid;
  white-space: nowrap;
}
.od-badge-sm { font-size: 10px; padding: 1px 6px; }
.badge-blue   { background: rgba(59,130,246,0.15);  color: #93c5fd; border-color: rgba(59,130,246,0.3); }
.badge-purple { background: rgba(168,85,247,0.15);  color: #c4b5fd; border-color: rgba(168,85,247,0.3); }
.badge-cyan   { background: rgba(6,182,212,0.15);   color: #67e8f9; border-color: rgba(6,182,212,0.3); }
.badge-emerald{ background: rgba(16,185,129,0.15);  color: #6ee7b7; border-color: rgba(16,185,129,0.3); }
.badge-slate  { background: rgba(100,116,139,0.15);  color: #94a3b8; border-color: rgba(100,116,139,0.3); }

/* === Checkbox === */
.od-checkbox {
  width: 15px; height: 15px;
  border-radius: 4px;
  border: 1px solid var(--border-medium);
  cursor: pointer;
  accent-color: var(--accent-primary);
}

/* === Dialog Overlay === */
.od-overlay {
  position: fixed; inset: 0; z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  background: var(--color-overlay);
}

/* === Add/Edit Dialog === */
.od-dialog {
  background: var(--color-modal-bg);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  width: 580px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-card);
}
.od-dialog-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 20px 14px;
}
.od-dialog-title {
  display: flex; align-items: center; gap: 8px;
  font-size: var(--font-size-md); font-weight: var(--font-weight-medium);
  margin: 0; color: var(--foreground-primary);
}
.od-dialog-close {
  background: none; border: none;
  color: var(--foreground-muted); cursor: pointer; padding: 4px;
}
.od-dialog-close:hover { color: var(--foreground-primary); }
.od-dialog-body { padding: 0 20px 14px; }
.od-dialog-footer {
  display: flex; justify-content: flex-end; gap: 10px;
  padding: 0 20px 18px;
}

/* === Form === */
.od-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.od-form-full { grid-column: 1 / -1; }
.od-label {
  display: block; font-size: var(--font-size-sm);
  color: var(--foreground-secondary); margin-bottom: 4px;
}
.od-input {
  width: 100%; padding: 7px 10px;
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
}
.od-input:focus { border-color: var(--accent-primary); }
.od-textarea {
  width: 100%; padding: 7px 10px;
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none; resize: vertical;
}
.od-textarea:focus { border-color: var(--accent-primary); }

/* === Status Toggle === */
.od-status-toggle {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px;
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}
.od-status-label { font-size: var(--font-size-sm); color: var(--foreground-primary); }
.od-status-desc { font-size: var(--font-size-xs); color: var(--foreground-muted); }
.od-switch {
  position: relative; width: 40px; height: 22px;
  display: inline-block;
}
.od-switch input { opacity: 0; width: 0; height: 0; }
.od-switch-slider {
  position: absolute; inset: 0;
  background: rgba(100,116,139,0.4);
  border-radius: 22px;
  cursor: pointer;
  transition: background var(--transition-fast);
}
.od-switch-slider::before {
  content: ''; position: absolute;
  width: 16px; height: 16px;
  left: 3px; top: 3px;
  background: #fff; border-radius: 50%;
  transition: transform var(--transition-fast);
}
.od-switch input:checked + .od-switch-slider { background: var(--accent-primary); }
.od-switch input:checked + .od-switch-slider::before { transform: translateX(18px); }

/* === Alert Dialog === */
.od-alert {
  background: var(--color-modal-bg);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 22px;
  width: 420px;
  max-width: 90vw;
  box-shadow: var(--shadow-card);
}
.od-alert-header {
  display: flex; align-items: center; gap: 8px;
  font-size: var(--font-size-md); font-weight: var(--font-weight-medium);
  color: var(--foreground-primary); margin-bottom: 12px;
}
.od-alert-tags { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 10px; }
.od-alert-tag {
  display: inline-block; padding: 2px 8px;
  background: var(--surface-primary);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs); color: var(--foreground-primary);
}
.od-alert-desc { font-size: var(--font-size-sm); color: var(--foreground-muted); margin-bottom: 16px; }
.od-alert-actions { display: flex; justify-content: flex-end; gap: 10px; }

/* === Utility === */
.text-blue { color: var(--accent-primary); }
.text-cyan { color: #22d3ee; }
.text-rose { color: #fb7185; }
</style>
