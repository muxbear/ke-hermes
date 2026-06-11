<script setup lang="ts">
import { ref, onMounted } from 'vue'
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
} from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserManagementStore } from '@/stores/userManagement'
import DepartmentTreeNode from '@/components/admin/DepartmentTreeNode.vue'
import type { Department, SystemUser, CreateUserRequest, UserStatus } from '@/types/admin'

const router = useRouter()
const store = useUserManagementStore()

onMounted(() => {
  store.fetchAll()
})

const expandedDeptIds = ref<Set<string>>(new Set())

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

function openCreateDialog() {
  dialogMode.value = 'create'
  editUserId.value = null
  form.value = {
    name: '', employeeId: '', deptId: '', position: '',
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

const statusConfig: Record<UserStatus, { label: string; cls: string; icon: typeof CheckCircle2 }> = {
  active: { label: '在职', cls: 'status-active', icon: CheckCircle2 },
  inactive: { label: '离职', cls: 'status-inactive', icon: XCircle },
  pending: { label: '待入职', cls: 'status-pending', icon: Clock },
}

function handleBack() {
  router.push('/admin')
}
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
            v-for="user in store.filteredUsers"
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
              <button class="action-btn" @click.stop="openEditDialog(user)">
                <Edit2 :size="14" />
              </button>
              <button class="action-btn danger" @click.stop="handleDeleteUser(user)">
                <Trash2 :size="14" />
              </button>
            </div>
          </div>
          <div v-if="store.filteredUsers.length === 0" class="empty-state">
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
                v-for="user in store.filteredUsers"
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
                    <button class="action-btn" @click.stop="openEditDialog(user)">
                      <Edit2 :size="14" />
                    </button>
                    <button class="action-btn danger" @click.stop="handleDeleteUser(user)">
                      <Trash2 :size="14" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="store.filteredUsers.length === 0" class="empty-state">
            暂无用户数据
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
                <option v-for="d in store.departments" :key="d.id" :value="d.id">
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
</style>
