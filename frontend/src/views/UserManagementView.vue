<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChevronLeft,
  Search,
  Plus,
  Edit2,
  Trash2,
  Grid3X3,
  List,
  UserPlus,
  Mail,
  Phone,
  Calendar,
  Building2,
  CheckCircle2,
  XCircle,
  Clock,
  MoreHorizontal,
  Link2,
  Eye,
} from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserManagementStore } from '@/stores/userManagement'
import DepartmentTreeNode from '@/components/admin/DepartmentTreeNode.vue'
import { fetchAccounts, fetchAccount } from '@/services/adminApi'
import type { Department, SystemUser, CreateUserRequest, UserStatus, AccountInfo } from '@/types/admin'

const router = useRouter()
const store = useUserManagementStore()

onMounted(async () => {
  await store.fetchAll()
})

const expandedDeptIds = ref<Set<string>>(new Set())

// 默认展开到第 2 级节点
watch(() => store.departments, (depts) => {
  if (depts.length === 0) return
  const ids = new Set<string>()
  function collect(ds: Department[], depth: number) {
    for (const d of ds) {
      ids.add(d.id)
      if (depth < 1 && d.children.length > 0) {
        collect(d.children, depth + 1)
      }
    }
  }
  collect(depts, 0)
  expandedDeptIds.value = ids
})

function handleDeptSelect(id: string) {
  store.selectDepartment(id)
}
function handleDeptToggle(id: string) {
  const next = new Set(expandedDeptIds.value)
  next.has(id) ? next.delete(id) : next.add(id)
  expandedDeptIds.value = next
}

// 用户表单弹窗
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editUserId = ref<string | null>(null)
const form = ref<CreateUserRequest>({
  name: '',
  employeeId: '',
  deptId: '',
  position: '',
  email: '',
  phone: '',
  status: 'active',
})

// 将部门树扁平化，用于弹窗下拉选择
const flatDepts = computed(() => {
  const result: Department[] = []
  function walk(ds: Department[]) {
    for (const d of ds) {
      result.push(d)
      if (d.children.length > 0) walk(d.children)
    }
  }
  walk(store.departments)
  return result
})

function openCreateDialog() {
  dialogMode.value = 'create'
  editUserId.value = null
  form.value = {
    name: '', employeeId: '',
    deptId: store.selectedDeptId ?? '',
    position: '',
    email: '', phone: '', status: 'active',
  }
  dialogVisible.value = true
}

function openEditDialog(user: SystemUser) {
  dialogMode.value = 'edit'
  editUserId.value = user.id
  form.value = {
    name: user.name,
    employeeId: user.employeeId,
    deptId: user.deptId,
    position: user.position,
    email: user.email,
    phone: user.phone,
    status: user.status,
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.name.trim() || !form.value.email.trim()) {
    ElMessage.warning('请填写姓名和邮箱')
    return
  }
  if (dialogMode.value === 'create') {
    await store.handleCreateUser(form.value)
    ElMessage.success('用户创建成功')
  } else if (editUserId.value) {
    await store.handleUpdateUser({ id: editUserId.value, ...form.value })
    ElMessage.success('用户已更新')
  }
  dialogVisible.value = false
}

async function handleDeleteUser(user: SystemUser) {
  try {
    await ElMessageBox.confirm(
      `确定删除用户「${user.name}」吗？此操作不可撤销。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' },
    )
    await store.handleDeleteUser(user.id)
    ElMessage.success('用户已删除')
  } catch {
    // cancelled
  }
}

// ─── 绑定账号 ───────────────────────────────────────────────
const bindVisible = ref(false)
const bindPersonnelId = ref<string | null>(null)
const bindSearch = ref('')
const bindAccounts = ref<AccountInfo[]>([])
const bindLoading = ref(false)
const bindSelected = ref<string | null>(null)

async function openBindDialog(user: SystemUser) {
  bindPersonnelId.value = user.id
  bindSearch.value = ''
  bindAccounts.value = []
  bindSelected.value = null
  bindVisible.value = true
  await searchAccounts()
}

async function searchAccounts() {
  bindLoading.value = true
  try {
    const res = await fetchAccounts({ search: bindSearch.value || undefined, page: 1, pageSize: 20 })
    bindAccounts.value = res.items
  } finally {
    bindLoading.value = false
  }
}

async function handleBindSubmit() {
  if (!bindPersonnelId.value || !bindSelected.value) return
  const account = bindAccounts.value.find(a => a.id === bindSelected.value)
  if (!account) return

  try {
    await ElMessageBox.confirm(
      `确定将人员绑定到账号「${account.username}」吗？`,
      '确认绑定',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'info' },
    )
    await store.handleUpdateUser({ id: bindPersonnelId.value, account_id: account.id } as any)
    ElMessage.success(`已绑定账号「${account.username}」`)
    bindVisible.value = false
  } catch { /* cancelled */ }
}

// ─── 查看详情（右侧抽屉）────────────────────────────────────
const detailVisible = ref(false)
const detailUser = ref<SystemUser | null>(null)
const detailAccount = ref<AccountInfo | null>(null)
const detailLoading = ref(false)

async function openDetail(user: SystemUser) {
  detailUser.value = user
  detailAccount.value = null
  detailVisible.value = true
  if (user.accountId) {
    detailLoading.value = true
    try {
      detailAccount.value = await fetchAccount(user.accountId)
    } catch { /* ignore */ }
    finally { detailLoading.value = false }
  }
}

const statusConfig: Record<UserStatus, { label: string; cls: string; icon: typeof CheckCircle2 }> = {
  active: { label: '在职', cls: 'status-active', icon: CheckCircle2 },
  inactive: { label: '离职', cls: 'status-inactive', icon: XCircle },
  pending: { label: '待入职', cls: 'status-pending', icon: Clock },
}

function handleBack() {
  router.push('/admin')
}

// ─── 分页 ───────────────────────────────────────────────
const currentPage = ref(1)
const pageSize = ref(10)
const pageSizeOptions = [10, 20, 50]

const totalFiltered = computed(() => store.filteredUsers.length)

const paginatedUsers = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return store.filteredUsers.slice(start, start + pageSize.value)
})

// 筛选条件变化时重置到第 1 页
watch([() => store.selectedDeptId, () => store.searchQuery], () => {
  currentPage.value = 1
})
</script>

<template>
  <div class="um-page">
    <div class="um-topbar">
      <button class="back-btn" @click="handleBack">
        <ChevronLeft :size="16" />
        后台
      </button>
      <span class="topbar-divider" />
      <span class="topbar-title">人员管理</span>
    </div>

    <div class="um-body">
      <aside class="um-left">
        <div class="left-header">
          <span class="left-title">组织架构</span>
        </div>
        <div class="dept-tree">
          <DepartmentTreeNode
            v-for="dept in store.departments"
            :key="dept.id"
            :department="dept"
            :depth="0"
            :selected-id="store.selectedDeptId"
            :expanded-ids="expandedDeptIds"
            @select="handleDeptSelect"
            @toggle="handleDeptToggle"
          />
        </div>
      </aside>

      <main class="um-main">
        <div class="main-toolbar">
          <div class="search-wrap">
            <Search :size="16" class="search-icon" />
            <input
              v-model="store.searchQuery"
              type="text"
              class="search-input"
              placeholder="搜索姓名、工号、邮箱..."
            />
          </div>
          <div class="toolbar-actions">
            <div class="view-toggle">
              <button
                :class="{ active: store.viewMode === 'card' }"
                @click="store.viewMode = 'card'"
              >
                <Grid3X3 :size="16" />
              </button>
              <button
                :class="{ active: store.viewMode === 'table' }"
                @click="store.viewMode = 'table'"
              >
                <List :size="16" />
              </button>
            </div>
            <button class="add-user-btn" @click="openCreateDialog">
              <UserPlus :size="16" />
              添加成员
            </button>
          </div>
        </div>

        <div v-if="store.loading" class="loading-state">加载中...</div>

        <!-- 卡片视图 -->
        <div v-else-if="store.viewMode === 'card'" class="user-grid">
          <div
            v-for="user in paginatedUsers"
            :key="user.id"
            class="user-card"
            :class="{ active: store.selectedUser?.id === user.id }"
            @click="store.selectUser(user)"
          >
            <div class="user-card-top">
              <div class="user-avatar">
                {{ user.name.charAt(0) }}
              </div>
              <div class="user-info">
                <span class="user-name">{{ user.name }}</span>
                <span class="user-position">{{ user.position }}</span>
              </div>
              <span class="user-status" :class="statusConfig[user.status].cls">
                {{ statusConfig[user.status].label }}
              </span>
            </div>
            <div class="user-card-meta">
              <span class="meta-item">
                <Mail :size="12" />{{ user.email }}
              </span>
              <span class="meta-item">
                <Building2 :size="12" />{{ store.findDeptName(user.deptId) }}
              </span>
            </div>
            <div class="user-card-actions">
              <button class="action-btn" title="查看详情" @click.stop="openDetail(user)"><Eye :size="14" /></button>
              <button class="action-btn" title="绑定账号" @click.stop="openBindDialog(user)"><Link2 :size="14" /></button>
              <button class="action-btn" title="编辑" @click.stop="openEditDialog(user)"><Edit2 :size="14" /></button>
              <button class="action-btn danger" title="删除" @click.stop="handleDeleteUser(user)"><Trash2 :size="14" /></button>
            </div>
          </div>
          <div v-if="totalFiltered === 0" class="empty-state">
            暂无用户数据
          </div>
        </div>

        <!-- 表格视图 -->
        <div v-else class="user-table-wrap">
          <table class="user-table">
            <thead>
              <tr>
                <th>姓名</th>
                <th>工号</th>
                <th>部门</th>
                <th>职位</th>
                <th>邮箱</th>
                <th>状态</th>
                <th>入职日期</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="user in paginatedUsers"
                :key="user.id"
                :class="{ active: store.selectedUser?.id === user.id }"
                @click="store.selectUser(user)"
              >
                <td>{{ user.name }}</td>
                <td class="mono">{{ user.employeeId }}</td>
                <td>{{ store.findDeptName(user.deptId) }}</td>
                <td>{{ user.position }}</td>
                <td>{{ user.email }}</td>
                <td>
                  <span class="status-tag" :class="statusConfig[user.status].cls">
                    {{ statusConfig[user.status].label }}
                  </span>
                </td>
                <td>{{ user.joinDate }}</td>
                <td>
                  <div class="row-actions">
                    <button class="action-btn" title="详情" @click.stop="openDetail(user)"><Eye :size="14" /></button>
                    <button class="action-btn" title="绑定账号" @click.stop="openBindDialog(user)"><Link2 :size="14" /></button>
                    <button class="action-btn" title="编辑" @click.stop="openEditDialog(user)"><Edit2 :size="14" /></button>
                    <button class="action-btn danger" title="删除" @click.stop="handleDeleteUser(user)"><Trash2 :size="14" /></button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="totalFiltered === 0" class="empty-state">
            暂无用户数据
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="totalFiltered > 0" class="pagination-bar">
          <div class="page-info">
            共 {{ totalFiltered }} 条
          </div>
          <div class="page-controls">
            <select v-model.number="pageSize" class="page-size-select">
              <option v-for="s in pageSizeOptions" :key="s" :value="s">{{ s }} 条/页</option>
            </select>
            <button
              class="page-btn"
              :disabled="currentPage <= 1"
              @click="currentPage--"
            >
              ‹
            </button>
            <span class="page-current">{{ currentPage }} / {{ Math.ceil(totalFiltered / pageSize) || 1 }}</span>
            <button
              class="page-btn"
              :disabled="currentPage >= Math.ceil(totalFiltered / pageSize)"
              @click="currentPage++"
            >
              ›
            </button>
          </div>
        </div>
      </main>
    </div>

    <!-- 创建/编辑用户弹窗 -->
    <Teleport to="body">
      <div v-if="dialogVisible" class="dialog-overlay" @click.self="dialogVisible = false">
        <div class="dialog-panel">
          <div class="dialog-header">
            <h3>{{ dialogMode === 'create' ? '添加成员' : '编辑用户' }}</h3>
            <button class="dialog-close" @click="dialogVisible = false">&times;</button>
          </div>
          <div class="dialog-body">
            <div class="form-row">
              <label>姓名 *</label>
              <input v-model="form.name" type="text" placeholder="例：张三" />
            </div>
            <div class="form-row">
              <label>工号 *</label>
              <input v-model="form.employeeId" type="text" placeholder="例：EMP001" />
            </div>
            <div class="form-row">
              <label>部门</label>
              <select v-model="form.deptId">
                <option value="">请选择部门</option>
                <option v-for="d in flatDepts" :key="d.id" :value="d.id">
                  {{ d.name }}
                </option>
              </select>
            </div>
            <div class="form-row">
              <label>职位</label>
              <input v-model="form.position" type="text" placeholder="例：前端工程师" />
            </div>
            <div class="form-row">
              <label>邮箱 *</label>
              <input v-model="form.email" type="email" placeholder="例：zhangsan@example.com" />
            </div>
            <div class="form-row">
              <label>手机号</label>
              <input v-model="form.phone" type="text" placeholder="例：13800000001" />
            </div>
            <div class="form-row">
              <label>状态</label>
              <select v-model="form.status">
                <option value="active">在职</option>
                <option value="inactive">离职</option>
                <option value="pending">待入职</option>
              </select>
            </div>
          </div>
          <div class="dialog-footer">
            <button class="dialog-cancel" @click="dialogVisible = false">取消</button>
            <button class="dialog-submit" @click="handleSubmit" :disabled="store.saving">
              {{ store.saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 绑定账号弹窗 -->
    <Teleport to="body">
      <div v-if="bindVisible" class="dialog-overlay" @click.self="bindVisible = false">
        <div class="dialog-panel">
          <div class="dialog-header">
            <h3><Link2 :size="16" /> 绑定账号</h3>
            <button class="dialog-close" @click="bindVisible = false">&times;</button>
          </div>
          <div class="dialog-body">
            <div class="bind-search">
              <input v-model="bindSearch" type="text" class="bind-search-input" placeholder="搜索用户名、昵称、邮箱..."
                @keyup.enter="searchAccounts" />
              <button class="add-btn" @click="searchAccounts">搜索</button>
            </div>
            <div v-if="bindLoading" class="loading-state">搜索中...</div>
            <div v-else class="bind-list">
              <div
                v-for="a in bindAccounts"
                :key="a.id"
                :class="['bind-item', { selected: bindSelected === a.id }]"
                @click="bindSelected = a.id"
              >
                <div class="bind-item-info">
                  <span class="bind-username">{{ a.username }}</span>
                  <span class="bind-nickname">{{ a.nickname || '-' }}</span>
                </div>
                <span class="bind-email">{{ a.email || '-' }}</span>
              </div>
              <div v-if="bindAccounts.length === 0" class="empty-state">未找到匹配账号</div>
            </div>
          </div>
          <div class="dialog-footer">
            <button class="dialog-cancel" @click="bindVisible = false">取消</button>
            <button class="dialog-submit" :disabled="!bindSelected" @click="handleBindSubmit">确定</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- 人员详情右侧抽屉 -->
    <Teleport to="body">
      <div v-if="detailVisible" class="drawer-overlay" @click.self="detailVisible = false">
        <div class="drawer-panel">
          <div class="drawer-header">
            <h3>人员详情</h3>
            <button class="dialog-close" @click="detailVisible = false">&times;</button>
          </div>
          <div v-if="detailUser" class="drawer-body">
            <div class="drawer-avatar">
              <span class="drawer-avatar-text">{{ detailUser.name.charAt(0) }}</span>
            </div>
            <h2 class="drawer-name">{{ detailUser.name }}</h2>
            <div class="drawer-status">
              <span :class="['status-tag', statusConfig[detailUser.status].cls]">
                {{ statusConfig[detailUser.status].label }}
              </span>
            </div>
            <div class="drawer-divider" />
            <div class="drawer-fields">
              <div class="drawer-field">
                <span class="drawer-label">工号</span>
                <span class="drawer-value mono">{{ detailUser.employeeId }}</span>
              </div>
              <div class="drawer-field">
                <span class="drawer-label">部门</span>
                <span class="drawer-value">{{ store.findDeptName(detailUser.deptId) }}</span>
              </div>
              <div class="drawer-field">
                <span class="drawer-label">职位</span>
                <span class="drawer-value">{{ detailUser.position || '-' }}</span>
              </div>
              <div class="drawer-field">
                <span class="drawer-label">邮箱</span>
                <span class="drawer-value">{{ detailUser.email || '-' }}</span>
              </div>
              <div class="drawer-field">
                <span class="drawer-label">手机号</span>
                <span class="drawer-value">{{ detailUser.phone || '-' }}</span>
              </div>
              <div class="drawer-field">
                <span class="drawer-label">入职日期</span>
                <span class="drawer-value">{{ detailUser.joinDate || '-' }}</span>
              </div>
            </div>
            <div class="drawer-divider" />
            <div class="drawer-section-title">关联账号</div>
            <div v-if="detailLoading" class="loading-state">加载中...</div>
            <div v-else-if="detailAccount" class="drawer-account">
              <div class="drawer-field">
                <span class="drawer-label">用户名</span>
                <span class="drawer-value">{{ detailAccount.username }}</span>
              </div>
              <div class="drawer-field">
                <span class="drawer-label">昵称</span>
                <span class="drawer-value">{{ detailAccount.nickname || '-' }}</span>
              </div>
              <div class="drawer-field">
                <span class="drawer-label">邮箱</span>
                <span class="drawer-value">{{ detailAccount.email || '-' }}</span>
              </div>
              <div class="drawer-field">
                <span class="drawer-label">手机</span>
                <span class="drawer-value">{{ detailAccount.phone || '-' }}</span>
              </div>
              <div class="drawer-field">
                <span class="drawer-label">状态</span>
                <span :class="['status-tag', detailAccount.isActive ? 'active' : 'inactive']">
                  {{ detailAccount.isActive ? '正常' : '已禁用' }}
                </span>
              </div>
            </div>
            <div v-else class="drawer-no-account">未绑定账号</div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.um-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--surface-primary);
}
.um-topbar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--foreground-muted);
  font-size: var(--font-size-sm);
  cursor: pointer;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
}
.back-btn:hover {
  color: var(--foreground-primary);
}
.topbar-divider {
  width: 1px;
  height: 16px;
  background: var(--border-subtle);
}
.topbar-title {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}
.um-body {
  flex: 1;
  min-height: 0;
  display: flex;
}
.um-left {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid var(--border-subtle);
  background: var(--surface-card);
  display: flex;
  flex-direction: column;
}
.left-header {
  padding: 16px;
  border-bottom: 1px solid var(--border-subtle);
}
.left-title {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.dept-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.um-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.main-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  gap: 16px;
  flex-shrink: 0;
}
.search-wrap {
  position: relative;
  flex: 1;
  max-width: 360px;
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
  padding: 6px 12px 6px 32px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
}
.search-input:focus {
  border-color: var(--accent-primary);
}
.search-input::placeholder {
  color: var(--foreground-muted);
}
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.view-toggle {
  display: flex;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.view-toggle button {
  padding: 6px 10px;
  background: none;
  border: none;
  color: var(--foreground-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
}
.view-toggle button.active {
  background: var(--accent-primary);
  color: #fff;
}
.add-user-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  background: var(--accent-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  cursor: pointer;
}
.add-user-btn:hover {
  filter: brightness(1.1);
}
.loading-state,
.empty-state {
  padding: 48px;
  text-align: center;
  color: var(--foreground-muted);
}

/* 卡片视图 */
.user-grid {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 24px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
  align-content: start;
}
.user-card {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 16px;
  cursor: pointer;
  transition: border-color var(--transition-fast), background var(--transition-fast);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.user-card.active,
.user-card:hover {
  border-color: rgba(59, 130, 246, 0.4);
}
.user-card-top {
  display: flex;
  align-items: center;
  gap: 10px;
}
.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--accent-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  flex-shrink: 0;
}
.user-info {
  flex: 1;
  min-width: 0;
}
.user-name {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
}
.user-position {
  display: block;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin-top: 1px;
}
.user-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}
.status-active { background: rgba(16,185,129,0.15); color: #6ee7b7; }
.status-inactive { background: rgba(239,68,68,0.15); color: #fca5a5; }
.status-pending { background: rgba(245,158,11,0.15); color: #fcd34d; }
.user-card-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}
.user-card-actions {
  display: flex;
  gap: 4px;
  justify-content: flex-end;
}
.action-btn {
  padding: 4px 8px;
  background: none;
  border: none;
  color: var(--foreground-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
}
.action-btn:hover { background: rgba(30,41,59,0.6); color: var(--foreground-primary); }
.action-btn.danger:hover { background: rgba(239,68,68,0.15); color: #fca5a5; }

/* 表格视图 */
.user-table-wrap {
  flex: 1;
  overflow-y: auto;
  padding: 0 24px 24px;
}
.user-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}
.user-table th {
  text-align: left;
  padding: 10px 12px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-muted);
  border-bottom: 1px solid var(--border-subtle);
  background: var(--surface-card);
  position: sticky;
  top: 0;
  z-index: 1;
}
.user-table td {
  padding: 10px 12px;
  color: var(--foreground-primary);
  border-bottom: 1px solid var(--border-subtle);
}
.user-table tr:hover td {
  background: rgba(30, 41, 59, 0.3);
}
.user-table tr.active td {
  background: rgba(59, 130, 246, 0.08);
}
.mono { font-family: monospace; font-size: var(--font-size-xs); }
.status-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
}
.row-actions {
  display: flex;
  gap: 4px;
}

/* 弹窗 */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.dialog-panel {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-card);
}
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}
.dialog-header h3 {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0;
}
.dialog-close {
  background: none;
  border: none;
  font-size: 22px;
  color: var(--foreground-muted);
  cursor: pointer;
}
.dialog-close:hover { color: var(--foreground-primary); }
.dialog-body {
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.form-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.form-row label {
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
}
.form-row input,
.form-row select {
  padding: 8px 12px;
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
}
.form-row input:focus,
.form-row select:focus {
  border-color: var(--accent-primary);
}
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 0 24px 20px;
}
.dialog-cancel {
  padding: 8px 18px;
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
}
.dialog-cancel:hover { background: rgba(30,41,59,0.6); }
.dialog-submit {
  padding: 8px 18px;
  background: var(--accent-primary);
  border: none;
  border-radius: var(--radius-md);
  color: #fff;
  font-size: var(--font-size-sm);
  cursor: pointer;
}
.dialog-submit:hover { filter: brightness(1.1); }
.dialog-submit:disabled { opacity: 0.6; cursor: not-allowed; }

/* === 分页 === */
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0 0;
  border-top: 1px solid var(--border-subtle);
  margin-top: 16px;
}
.page-info {
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
}
.page-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}
.page-size-select {
  padding: 4px 8px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--foreground-primary);
  font-size: var(--font-size-xs);
  outline: none;
  cursor: pointer;
}
.page-btn {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--foreground-primary);
  font-size: 14px;
  cursor: pointer;
  transition: background var(--transition-duration);
}
.page-btn:hover:not(:disabled) { background: rgba(59,130,246,0.1); }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.page-current {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
  min-width: 60px;
  text-align: center;
}

/* Bind Account Dialog */
.bind-search { display: flex; gap: 8px; margin-bottom: 14px; }
.bind-search-input {
  flex: 1; padding: 8px 12px;
  background: var(--surface-primary); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md); color: var(--foreground-primary);
  font-size: var(--font-size-sm); outline: none;
}
.bind-search-input:focus { border-color: var(--accent-primary); }
.bind-list { max-height: 300px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; }
.bind-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px; border-radius: var(--radius-md); cursor: pointer;
  border: 1px solid transparent;
  transition: all var(--transition-duration);
}
.bind-item:hover { background: rgba(59,130,246,0.06); }
.bind-item.selected { background: rgba(59,130,246,0.1); border-color: rgba(59,130,246,0.3); }
.bind-item-info { display: flex; flex-direction: column; gap: 2px; }
.bind-username { font-size: var(--font-size-sm); color: var(--foreground-primary); }
.bind-nickname { font-size: var(--font-size-xs); color: var(--foreground-muted); }
.bind-email { font-size: var(--font-size-xs); color: var(--foreground-muted); }

/* Right Drawer */
.drawer-overlay { position: fixed; inset: 0; z-index: 1000; background: rgba(0,0,0,0.3); }
.drawer-panel {
  position: fixed; top: 0; right: 0; height: 100%; width: 380px; max-width: 90vw;
  background: var(--color-modal-bg); border-left: 1px solid var(--border-subtle);
  box-shadow: -4px 0 24px rgba(0,0,0,0.3);
  display: flex; flex-direction: column;
  animation: slideIn 0.25s ease;
}
@keyframes slideIn { from { transform: translateX(100%); } to { transform: translateX(0); } }
.drawer-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 20px; border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.drawer-header h3 { font-size: var(--font-size-md); margin: 0; color: var(--foreground-primary); }
.drawer-body { flex: 1; overflow-y: auto; padding: 24px 20px; }
.drawer-avatar {
  width: 56px; height: 56px; border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-primary), rgba(168,85,247,0.8));
  display: flex; align-items: center; justify-content: center; margin-bottom: 12px;
}
.drawer-avatar-text { color: #fff; font-size: 22px; font-weight: var(--font-weight-medium); }
.drawer-name { font-size: var(--font-size-lg); color: var(--foreground-primary); margin: 0 0 8px; }
.drawer-status { margin-bottom: 16px; }
.drawer-divider { height: 1px; background: var(--border-subtle); margin: 16px 0; }
.drawer-fields { display: flex; flex-direction: column; gap: 12px; }
.drawer-field { display: flex; flex-direction: column; gap: 3px; }
.drawer-label { font-size: var(--font-size-xs); color: var(--foreground-muted); }
.drawer-value { font-size: var(--font-size-sm); color: var(--foreground-primary); }
.drawer-section-title { font-size: var(--font-size-sm); font-weight: var(--font-weight-medium); color: var(--foreground-primary); margin-bottom: 8px; }
.drawer-no-account { font-size: var(--font-size-sm); color: var(--foreground-muted); padding: 12px 0; }
</style>
