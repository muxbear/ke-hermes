<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChevronLeft, Search, Plus, Edit2, Trash2,
  CheckCircle2, XCircle, ShieldBan, KeyRound,
  UserRoundCog, Eye, Lock, Unlock,
} from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAccountManagementStore } from '@/stores/accountManagement'
import type { AccountInfo, AccountCreateRequest, AccountUpdateRequest } from '@/types/admin'

const router = useRouter()
const store = useAccountManagementStore()

onMounted(() => {
  store.loadAccounts()
})

// 搜索防抖刷新
watch(() => store.searchQuery, () => {
  store.currentPage = 1
  store.loadAccounts()
})
watch(() => store.currentPage, () => store.loadAccounts())
watch(() => store.pageSize, () => {
  store.currentPage = 1
  store.loadAccounts()
})

// ─── 创建/编辑弹窗 ─────────────────────────────────────────
const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const editAccountId = ref<string | null>(null)
const form = ref<AccountCreateRequest & { id?: string }>({
  username: '', nickname: '', password: '', email: '', phone: '', isActive: true,
})

function openCreate() {
  dialogMode.value = 'create'
  editAccountId.value = null
  form.value = { username: '', nickname: '', password: '', email: '', phone: '', isActive: true }
  dialogVisible.value = true
}

function openEdit(account: AccountInfo) {
  dialogMode.value = 'edit'
  editAccountId.value = account.id
  form.value = {
    username: account.username, nickname: account.nickname, password: '',
    email: account.email, phone: account.phone, isActive: account.isActive,
  }
  dialogVisible.value = true
}

async function handleSubmit() {
  if (!form.value.username.trim()) { ElMessage.warning('请输入用户名'); return }

  if (dialogMode.value === 'create') {
    if (!form.value.password) { ElMessage.warning('请输入密码'); return }
    await store.handleCreate({ ...form.value, username: form.value.username.trim() })
    ElMessage.success('账号创建成功')
  } else if (editAccountId.value) {
    const data: AccountUpdateRequest = { username: form.value.username.trim(), nickname: form.value.nickname, email: form.value.email, phone: form.value.phone, isActive: form.value.isActive }
    await store.handleUpdate(editAccountId.value, data)
    ElMessage.success('账号更新成功')
  }
  dialogVisible.value = false
}

// ─── 删除 ──────────────────────────────────────────────────
async function handleDelete(account: AccountInfo) {
  try {
    await ElMessageBox.confirm(`确定删除账号「${account.username}」吗？`, '确认删除', {
      confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning',
    })
    await store.handleDelete(account.id)
    ElMessage.success('账号已删除')
  } catch { /* cancelled */ }
}

// ─── 启用/禁用 ─────────────────────────────────────────────
async function handleToggleStatus(account: AccountInfo) {
  const a = await store.handleToggleStatus(account.id)
  ElMessage.success(a.isActive ? '账号已启用' : '账号已禁用')
}

// ─── 解锁 ──────────────────────────────────────────────────
async function handleUnlock(account: AccountInfo) {
  try {
    await ElMessageBox.confirm(`确定解锁账号「${account.username}」吗？`, '确认解锁', {
      confirmButtonText: '解锁', cancelButtonText: '取消', type: 'info',
    })
    await store.handleUnlock(account.id)
    ElMessage.success('账号已解锁')
  } catch { /* cancelled */ }
}

// ─── 重置密码 ──────────────────────────────────────────────
const resetPwdVisible = ref(false)
const resetPwdResult = ref('')

async function handleResetPassword(account: AccountInfo) {
  try {
    await ElMessageBox.confirm(
      `确定重置「${account.username}」的密码吗？重置后当前密码将失效。`,
      '确认重置密码',
      { confirmButtonText: '重置', cancelButtonText: '取消', type: 'warning' },
    )
    const tempPwd = await store.handleResetPassword(account.id)
    resetPwdResult.value = tempPwd
    resetPwdVisible.value = true
  } catch { /* cancelled */ }
}

// ─── 查看详情 ──────────────────────────────────────────────
const detailVisible = ref(false)
const detailAccount = ref<AccountInfo | null>(null)

async function openDetail(account: AccountInfo) {
  detailAccount.value = await store.loadAccountDetail(account.id)
  detailVisible.value = true
}

const pageSizeOptions = [10, 20, 50]
</script>

<template>
  <div class="am-page">
    <!-- Top Bar -->
    <div class="am-topbar">
      <button class="back-btn" @click="router.push('/admin')">
        <ChevronLeft :size="16" />返回
      </button>
      <span class="topbar-divider" />
      <span class="topbar-title">账号管理</span>
    </div>

    <!-- Toolbar -->
    <div class="am-toolbar">
      <div class="search-wrap">
        <Search :size="16" class="search-icon" />
        <input v-model="store.searchQuery" type="text" class="search-input" placeholder="搜索用户名、昵称、邮箱、手机..." />
      </div>
      <button class="add-btn" @click="openCreate">
        <Plus :size="16" />添加账号
      </button>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="loading-state">加载中...</div>

    <!-- Table -->
    <div v-else class="am-table-wrap">
      <table class="am-table">
        <thead>
          <tr>
            <th>用户名</th>
            <th>昵称</th>
            <th>邮箱</th>
            <th>手机</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in store.accounts" :key="a.id">
            <td class="mono">{{ a.username }}</td>
            <td>{{ a.nickname }}</td>
            <td>{{ a.email }}</td>
            <td>{{ a.phone }}</td>
            <td>
              <span :class="['status-tag', a.isActive ? 'active' : 'inactive']">
                {{ a.isActive ? '正常' : '已禁用' }}
              </span>
            </td>
            <td>{{ a.createdAt?.slice(0, 10) }}</td>
            <td>
              <div class="row-actions">
                <button class="action-btn" title="查看详情" @click="openDetail(a)"><Eye :size="14" /></button>
                <button class="action-btn" title="编辑" @click="openEdit(a)"><Edit2 :size="14" /></button>
                <button class="action-btn" :title="a.isActive ? '禁用' : '启用'" @click="handleToggleStatus(a)">
                  <ShieldBan v-if="a.isActive" :size="14" />
                  <CheckCircle2 v-else :size="14" />
                </button>
                <button class="action-btn" title="解锁" @click="handleUnlock(a)"><Unlock :size="14" /></button>
                <button class="action-btn" title="重置密码" @click="handleResetPassword(a)"><KeyRound :size="14" /></button>
                <button class="action-btn danger" title="删除" @click="handleDelete(a)"><Trash2 :size="14" /></button>
              </div>
            </td>
          </tr>
          <tr v-if="store.accounts.length === 0">
            <td colspan="7" class="empty-cell">暂无账号数据</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="store.total > 0" class="pagination-bar">
      <div class="page-info">共 {{ store.total }} 条</div>
      <div class="page-controls">
        <select v-model.number="store.pageSize" class="page-size-select">
          <option v-for="s in pageSizeOptions" :key="s" :value="s">{{ s }} 条/页</option>
        </select>
        <button class="page-btn" :disabled="store.currentPage <= 1" @click="store.currentPage--">‹</button>
        <span class="page-current">{{ store.currentPage }} / {{ store.totalPages }}</span>
        <button class="page-btn" :disabled="store.currentPage >= store.totalPages" @click="store.currentPage++">›</button>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <Teleport to="body">
      <div v-if="dialogVisible" class="dialog-overlay" @click.self="dialogVisible = false">
        <div class="dialog-panel">
          <div class="dialog-header">
            <h3>{{ dialogMode === 'create' ? '添加账号' : '编辑账号' }}</h3>
            <button class="dialog-close" @click="dialogVisible = false">&times;</button>
          </div>
          <div class="dialog-body">
            <div class="form-row">
              <label>用户名 *</label>
              <input v-model="form.username" type="text" placeholder="英文/数字" :disabled="dialogMode === 'edit'" />
            </div>
            <div class="form-row">
              <label>昵称</label>
              <input v-model="form.nickname" type="text" placeholder="显示名称" />
            </div>
            <div class="form-row" v-if="dialogMode === 'create'">
              <label>密码 *</label>
              <input v-model="form.password" type="password" placeholder="至少 6 位" />
            </div>
            <div class="form-row">
              <label>邮箱</label>
              <input v-model="form.email" type="email" placeholder="xxx@example.com" />
            </div>
            <div class="form-row">
              <label>手机号</label>
              <input v-model="form.phone" type="text" placeholder="13800000000" />
            </div>
            <div class="form-row" v-if="dialogMode === 'edit'">
              <label>状态</label>
              <select v-model="form.isActive">
                <option :value="true">正常</option>
                <option :value="false">已禁用</option>
              </select>
            </div>
          </div>
          <div class="dialog-footer">
            <button class="dialog-cancel" @click="dialogVisible = false">取消</button>
            <button class="dialog-submit" :disabled="store.saving" @click="handleSubmit">
              {{ store.saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Detail Dialog -->
    <Teleport to="body">
      <div v-if="detailVisible" class="dialog-overlay" @click.self="detailVisible = false">
        <div class="dialog-panel">
          <div class="dialog-header">
            <h3><UserRoundCog :size="18" /> 账号详情</h3>
            <button class="dialog-close" @click="detailVisible = false">&times;</button>
          </div>
          <div v-if="detailAccount" class="dialog-body">
            <div class="detail-grid">
              <div class="detail-item"><label>ID</label><span class="mono">{{ detailAccount.id }}</span></div>
              <div class="detail-item"><label>用户名</label><span>{{ detailAccount.username }}</span></div>
              <div class="detail-item"><label>昵称</label><span>{{ detailAccount.nickname || '-' }}</span></div>
              <div class="detail-item"><label>邮箱</label><span>{{ detailAccount.email || '-' }}</span></div>
              <div class="detail-item"><label>手机</label><span>{{ detailAccount.phone || '-' }}</span></div>
              <div class="detail-item"><label>状态</label>
                <span :class="['status-tag', detailAccount.isActive ? 'active' : 'inactive']">
                  {{ detailAccount.isActive ? '正常' : '已禁用' }}
                </span>
              </div>
              <div class="detail-item"><label>创建时间</label><span>{{ detailAccount.createdAt }}</span></div>
              <div class="detail-item"><label>更新时间</label><span>{{ detailAccount.updatedAt }}</span></div>
            </div>
          </div>
          <div class="dialog-footer">
            <button class="dialog-cancel" @click="detailVisible = false">关闭</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Reset Password Result -->
    <Teleport to="body">
      <div v-if="resetPwdVisible" class="dialog-overlay" @click.self="resetPwdVisible = false">
        <div class="dialog-panel narrow">
          <div class="dialog-header">
            <h3><KeyRound :size="18" /> 密码已重置</h3>
            <button class="dialog-close" @click="resetPwdVisible = false">&times;</button>
          </div>
          <div class="dialog-body">
            <p class="pwd-note">请将以下临时密码发送给用户，登录后建议立即修改：</p>
            <div class="pwd-display">{{ resetPwdResult }}</div>
          </div>
          <div class="dialog-footer">
            <button class="dialog-submit" @click="resetPwdVisible = false">已复制，关闭</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.am-page { height: 100%; display: flex; flex-direction: column; background: var(--surface-primary); color: var(--foreground-primary); overflow: hidden; }

/* Top Bar */
.am-topbar { display: flex; align-items: center; gap: 12px; padding: 12px 24px; background: var(--surface-card); border-bottom: 1px solid var(--border-subtle); flex-shrink: 0; }
.back-btn { display: flex; align-items: center; gap: 4px; padding: 6px 10px; background: transparent; border: none; color: var(--foreground-secondary); font-size: var(--font-size-sm); cursor: pointer; border-radius: var(--radius-sm); }
.back-btn:hover { color: var(--foreground-primary); }
.topbar-divider { width: 1px; height: 20px; background: var(--border-subtle); }
.topbar-title { font-size: var(--font-size-md); font-weight: var(--font-weight-medium); color: var(--foreground-primary); }

/* Toolbar */
.am-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 24px; flex-shrink: 0; }
.search-wrap { position: relative; flex: 1; max-width: 360px; }
.search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: var(--foreground-muted); }
.search-input { width: 100%; padding: 7px 12px 7px 32px; background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--foreground-primary); font-size: var(--font-size-sm); outline: none; }
.search-input:focus { border-color: var(--accent-primary); }
.add-btn { display: inline-flex; align-items: center; gap: 6px; padding: 7px 18px; background: var(--accent-primary); border: none; border-radius: var(--radius-md); color: #fff; font-size: var(--font-size-sm); cursor: pointer; white-space: nowrap; }
.add-btn:hover { filter: brightness(1.1); }
.loading-state { padding: 40px; text-align: center; color: var(--foreground-muted); font-size: var(--font-size-sm); }

/* Table */
.am-table-wrap { flex: 1; overflow: auto; padding: 0 24px; }
.am-table { width: 100%; border-collapse: collapse; font-size: var(--font-size-sm); }
.am-table thead { position: sticky; top: 0; background: var(--surface-card); color: var(--foreground-muted); font-size: var(--font-size-xs); z-index: 1; }
.am-table th { padding: 8px 12px; text-align: left; font-weight: var(--font-weight-medium); border-bottom: 1px solid var(--border-subtle); }
.am-table td { padding: 8px 12px; border-bottom: 1px solid var(--border-subtle); }
.am-table tbody tr:hover { background: rgba(59,130,246,0.04); }
.mono { font-family: monospace; font-size: var(--font-size-xs); }
.empty-cell { text-align: center; padding: 40px !important; color: var(--foreground-muted); }

/* Status Tags */
.status-tag { display: inline-block; padding: 2px 10px; border-radius: var(--radius-full); font-size: var(--font-size-xs); }
.status-tag.active { background: rgba(16,185,129,0.15); color: #6ee7b7; border: 1px solid rgba(16,185,129,0.3); }
.status-tag.inactive { background: rgba(244,63,94,0.15); color: #fb7185; border: 1px solid rgba(244,63,94,0.3); }

/* Row Actions */
.row-actions { display: flex; gap: 2px; }
.action-btn { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: none; border: none; border-radius: var(--radius-sm); color: var(--foreground-muted); cursor: pointer; }
.action-btn:hover { color: var(--accent-primary); background: rgba(59,130,246,0.1); }
.action-btn.danger:hover { color: #fb7185; background: rgba(244,63,94,0.1); }

/* Pagination */
.pagination-bar { display: flex; align-items: center; justify-content: space-between; padding: 12px 24px; border-top: 1px solid var(--border-subtle); flex-shrink: 0; }
.page-info { font-size: var(--font-size-sm); color: var(--foreground-muted); }
.page-controls { display: flex; align-items: center; gap: 8px; }
.page-size-select { padding: 4px 8px; background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); color: var(--foreground-primary); font-size: var(--font-size-xs); outline: none; cursor: pointer; }
.page-btn { width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: var(--surface-card); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); color: var(--foreground-primary); font-size: 14px; cursor: pointer; }
.page-btn:hover:not(:disabled) { background: rgba(59,130,246,0.1); }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.page-current { font-size: var(--font-size-sm); color: var(--foreground-primary); min-width: 60px; text-align: center; }

/* Dialog */
.dialog-overlay { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center; background: var(--color-overlay); }
.dialog-panel { background: var(--color-modal-bg); border: 1px solid var(--border-subtle); border-radius: var(--radius-xl); width: 520px; max-width: 90vw; max-height: 85vh; overflow-y: auto; box-shadow: var(--shadow-card); }
.dialog-panel.narrow { width: 420px; }
.dialog-header { display: flex; align-items: center; justify-content: space-between; padding: 18px 20px 14px; }
.dialog-header h3 { font-size: var(--font-size-md); font-weight: var(--font-weight-medium); margin: 0; color: var(--foreground-primary); display: flex; align-items: center; gap: 8px; }
.dialog-close { background: none; border: none; color: var(--foreground-muted); font-size: 20px; cursor: pointer; padding: 4px; }
.dialog-close:hover { color: var(--foreground-primary); }
.dialog-body { padding: 0 20px 14px; }
.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 0 20px 18px; }

/* Form */
.form-row { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
.form-row label { font-size: var(--font-size-sm); color: var(--foreground-muted); }
.form-row input, .form-row select { padding: 8px 12px; background: var(--surface-primary); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--foreground-primary); font-size: var(--font-size-sm); outline: none; }
.form-row input:focus, .form-row select:focus { border-color: var(--accent-primary); }
.form-row input:disabled { opacity: 0.5; }

.dialog-cancel { padding: 8px 18px; background: var(--surface-primary); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); color: var(--foreground-secondary); font-size: var(--font-size-sm); cursor: pointer; }
.dialog-cancel:hover { background: rgba(30,41,59,0.6); }
.dialog-submit { padding: 8px 18px; background: var(--accent-primary); border: none; border-radius: var(--radius-md); color: #fff; font-size: var(--font-size-sm); cursor: pointer; }
.dialog-submit:hover { filter: brightness(1.1); }
.dialog-submit:disabled { opacity: 0.6; cursor: not-allowed; }

/* Detail */
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.detail-item { display: flex; flex-direction: column; gap: 2px; padding: 8px 12px; background: var(--surface-primary); border: 1px solid var(--border-subtle); border-radius: var(--radius-md); }
.detail-item label { font-size: 10px; color: var(--foreground-muted); }
.detail-item span { font-size: var(--font-size-sm); color: var(--foreground-primary); word-break: break-all; }

/* Password Reset Result */
.pwd-note { font-size: var(--font-size-sm); color: var(--foreground-muted); margin-bottom: 12px; }
.pwd-display { padding: 12px; background: var(--surface-primary); border: 1px solid rgba(59,130,246,0.3); border-radius: var(--radius-md); font-family: monospace; font-size: 18px; color: var(--accent-primary); text-align: center; letter-spacing: 2px; user-select: all; }
</style>
