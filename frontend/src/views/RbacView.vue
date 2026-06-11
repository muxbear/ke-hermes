<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChevronLeft, Plus, Check, Lock, ShieldCheck, Save, Search,
  ChevronRight, ChevronDown, LayoutGrid, FolderTree, PenLine,
  Database, FolderTree as FolderTreeIcon, Shield, Sparkles,
  Info,
} from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRbacStore } from '@/stores/rbac'
import { isSuperAdmin } from '@/services/adminApi'
import { PERM_TYPE_CONFIG } from '@/types/admin'
import type { PermResource } from '@/types/admin'
import RoleListItem from '@/components/admin/RoleListItem.vue'
import PermissionTreeNode from '@/components/admin/PermissionTreeNode.vue'
import DataScopeSelector from '@/components/admin/DataScopeSelector.vue'

const router = useRouter()
const store = useRbacStore()

onMounted(() => {
  store.fetchAll()
})

const expandedIds = ref<Set<string>>(new Set(store.permResources.filter((r) => r.type === 'catalog').map((r) => r.id)))

function toggleExpand(id: string) {
  const next = new Set(expandedIds.value)
  next.has(id) ? next.delete(id) : next.add(id)
  expandedIds.value = next
}

// 角色创建弹窗
const showAddRole = ref(false)
const newRoleForm = ref({ name: '', description: '', copyFrom: 'member' })

async function handleCreateRole() {
  if (!newRoleForm.value.name.trim()) {
    ElMessage.warning('请输入角色名称')
    return
  }
  await store.handleCreateRole({ ...newRoleForm.value })
  showAddRole.value = false
  newRoleForm.value = { name: '', description: '', copyFrom: 'member' }
  ElMessage.success('角色创建成功')
}

async function handleDeleteRole(id: string) {
  const role = store.roles.find((r) => r.id === id)
  if (!role) return
  if (role.isBuiltin) {
    ElMessage.warning('内置角色不可删除')
    return
  }
  try {
    await ElMessageBox.confirm(`确定删除角色「${role.name}」吗？`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await store.handleDeleteRole(id)
    ElMessage.success('角色已删除')
  } catch { /* cancelled */ }
}

async function handleSave() {
  const ok = await store.handleSave()
  if (ok) ElMessage.success('权限配置已保存')
}

function handleBack() {
  router.push('/admin')
}

function getPermChildren(parentId: string | null): PermResource[] {
  return store.permResources
    .filter((r) => r.parentId === parentId)
    .sort((a, b) => a.sortOrder - b.sortOrder)
}

// 获取节点的子权限键列表
function getDescendantPermKeys(permId: string): string[] {
  const keys: string[] = []
  function walk(id: string) {
    const children = store.permResources.filter((r) => r.parentId === id)
    for (const c of children) {
      keys.push(c.permKey)
      walk(c.id)
    }
  }
  walk(permId)
  return keys
}

function getPermStats(node: PermResource) {
  const subKeys = getDescendantPermKeys(node.id)
  const subCount = subKeys.length
  const checkedCount = store.isSuper ? subCount : subKeys.filter((k) => store.activeGranted.has(k)).length
  return { subCount, checkedCount }
}
</script>

<template>
  <div class="rbac-page">
    <div class="rbac-topbar">
      <div class="topbar-left">
        <button class="back-btn" @click="handleBack">
          <ChevronLeft :size="16" />
          后台
        </button>
        <span class="topbar-divider" />
        <span class="topbar-title">角色权限</span>
      </div>
      <div class="topbar-right">
        RBAC · 基于角色的访问控制 · 统一资源模型
      </div>
    </div>

    <div v-if="store.loading" class="loading-state">加载中...</div>

    <div v-else class="rbac-body">
      <aside class="rbac-left">
        <div class="left-header">
          <span>内置角色</span>
        </div>
        <div class="role-list">
          <RoleListItem
            v-for="role in store.roles.filter((r) => r.isBuiltin)"
            :key="role.id"
            :role="role"
            :is-active="store.activeRoleId === role.id"
            @select="store.selectRole(role.id)"
          />
          <template v-if="store.roles.some((r) => !r.isBuiltin)">
            <div class="left-header custom-header">自定义角色</div>
            <RoleListItem
              v-for="role in store.roles.filter((r) => !r.isBuiltin)"
              :key="role.id"
              :role="role"
              :is-active="store.activeRoleId === role.id"
              @select="store.selectRole(role.id)"
            />
          </template>
        </div>
        <div class="left-footer">
          <button class="add-role-btn" @click="showAddRole = true">
            <Plus :size="14" />
            新建自定义角色
          </button>
        </div>
      </aside>

      <main class="rbac-main" v-if="store.activeRole">
        <div class="main-header">
          <div class="header-left">
            <div class="role-avatar" :class="store.activeRole.color">
              <Sparkles v-if="isSuperAdmin(store.activeRole.key)" :size="20" />
              <Shield v-else :size="20" />
            </div>
            <div>
              <div class="header-role-name">
                {{ store.activeRole.name }}
                <span v-if="store.activeRole.isBuiltin" class="badge builtin-badge">
                  <Lock :size="10" />系统内置
                </span>
                <span v-if="store.isSuper" class="badge super-badge">
                  <ShieldCheck :size="10" />全权限保护
                </span>
              </div>
              <p class="header-role-desc">{{ store.activeRole.description }}</p>
            </div>
          </div>
          <div class="header-right">
            <div class="header-stats">
              <div class="stat">
                <div class="stat-val">{{ store.activeRole.userCount }}</div>
                <div class="stat-label">绑定成员</div>
              </div>
              <div class="stat">
                <div class="stat-val blue">{{ 0 }}</div>
                <div class="stat-label">可访问菜单</div>
              </div>
              <div class="stat">
                <div class="stat-val purple">{{ 0 }}</div>
                <div class="stat-label">操作按钮</div>
              </div>
            </div>
            <button
              v-if="!store.readonly"
              class="save-btn"
              :disabled="store.saving"
              @click="handleSave"
            >
              <Save :size="16" />
              {{ store.saving ? '保存中...' : '保存配置' }}
            </button>
          </div>
        </div>

        <!-- Tab 切换 -->
        <div class="tab-bar">
          <button
            class="tab-btn"
            :class="{ active: store.activeTab === 'func' }"
            @click="store.activeTab = 'func'"
          >
            <FolderTreeIcon :size="14" />功能权限
          </button>
          <button
            class="tab-btn"
            :class="{ active: store.activeTab === 'data' }"
            @click="store.activeTab = 'data'"
          >
            <Database :size="14" />数据权限
          </button>
        </div>

        <!-- 功能权限 Tab -->
        <div v-if="store.activeTab === 'func'" class="tab-content">
          <div v-if="store.isSuper" class="notice notice-red">
            <ShieldCheck :size="16" />
            <span><b>超级管理员</b>拥有系统全部权限，无需也不可配置。在权限校验链路中超管直接放行。</span>
          </div>
          <div v-else-if="store.readonly" class="notice notice-amber">
            <Lock :size="16" />
            内置角色的权限由系统固定。如需自定义，请新建自定义角色并复制该角色权限。
          </div>

          <div class="perm-toolbar">
            <div class="search-wrap">
              <Search :size="14" />
              <input
                v-model="store.searchQuery"
                type="text"
                class="search-input"
                placeholder="按名称或 permKey 搜索..."
              />
            </div>
            <button class="tool-btn" @click="expandedIds = new Set(store.permResources.map(r => r.id))">
              <ChevronDown :size="12" />展开全部
            </button>
            <button class="tool-btn" @click="expandedIds = new Set()">
              <ChevronRight :size="12" />折叠全部
            </button>
            <div class="legend">
              <span><LayoutGrid :size="12" /> 目录</span>
              <span><FolderTreeIcon :size="12" /> 菜单</span>
              <span><PenLine :size="12" /> 按钮</span>
            </div>
          </div>

          <div class="perm-tree">
            <PermissionTreeNode
              v-for="root in getPermChildren(null)"
              :key="root.id"
              :node="root"
              :depth="0"
              :check-state="store.getCheckState(root.id)"
              :expanded-ids="expandedIds"
              :readonly="store.readonly"
              :children-list="getPermChildren(root.id)"
              :sub-count="getPermStats(root).subCount"
              :checked-count="getPermStats(root).checkedCount"
              @toggle="store.togglePerm"
              @toggle-expand="toggleExpand"
            />
          </div>
        </div>

        <!-- 数据权限 Tab -->
        <div v-if="store.activeTab === 'data'" class="tab-content">
          <div v-if="store.isSuper" class="notice notice-red">
            <ShieldCheck :size="16" />
            超级管理员对所有数据资源拥有完整可见范围。
          </div>
          <div v-else-if="store.readonly" class="notice notice-amber">
            <Lock :size="16" />内置角色的数据权限范围已锁定。
          </div>

          <div class="notice notice-blue">
            <Info :size="16" />
            <div>
              <span class="font-medium">数据权限粒度（主流 5 档）：</span>
              <span class="opacity-70">
                <b>全部数据</b> · <b>本部门及以下</b>（含下级部门） · <b>本部门</b> · <b>仅本人</b> ·
                <b>自定义部门</b>（手动选择若干部门） · <b>无权限</b>。每项资源可独立配置。
              </span>
            </div>
          </div>

          <div class="scope-list">
            <DataScopeSelector
              v-for="res in store.dataResources"
              :key="res.id"
              :resource-id="res.id"
              :resource-label="res.label"
              :current-scope="store.isSuper ? 'all' : (store.activePermState.dataScope[res.id] ?? 'none')"
              :disabled="store.readonly"
              @change="store.setDataScope"
            />
          </div>
        </div>
      </main>
    </div>

    <!-- 新建角色弹窗 -->
    <Teleport to="body">
      <div v-if="showAddRole" class="dialog-overlay" @click.self="showAddRole = false">
        <div class="dialog-panel">
          <div class="dialog-header">
            <h3>新建自定义角色</h3>
            <button class="dialog-close" @click="showAddRole = false">&times;</button>
          </div>
          <p class="dialog-sub">创建后可在权限配置中精细调整各模块权限。</p>
          <div class="dialog-body">
            <div class="form-row">
              <label>角色名称 *</label>
              <input v-model="newRoleForm.name" type="text" placeholder="如：运营专员" />
            </div>
            <div class="form-row">
              <label>角色描述</label>
              <textarea v-model="newRoleForm.description" rows="3" placeholder="描述该角色的职责范围..." />
            </div>
            <div class="form-row">
              <label>复制权限自</label>
              <div class="copy-options">
                <button
                  v-for="opt in [
                    { k: 'admin', l: '管理员' },
                    { k: 'manager', l: '部门主管' },
                    { k: 'member', l: '普通成员' },
                    { k: 'guest', l: '访客' },
                    { k: '', l: '从空白开始' },
                  ]"
                  :key="opt.l"
                  class="copy-opt"
                  :class="{ active: newRoleForm.copyFrom === opt.k }"
                  @click="newRoleForm.copyFrom = opt.k"
                >
                  {{ opt.l }}
                </button>
              </div>
            </div>
          </div>
          <div class="dialog-footer">
            <button class="dialog-cancel" @click="showAddRole = false">取消</button>
            <button class="dialog-submit" @click="handleCreateRole">创建角色</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.rbac-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--surface-primary);
}
.rbac-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
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
.back-btn:hover { color: var(--foreground-primary); }
.topbar-divider { width: 1px; height: 16px; background: var(--border-subtle); }
.topbar-title { font-size: var(--font-size-sm); color: var(--foreground-secondary); }
.topbar-right {
  font-size: var(--font-size-xs);
  color: #93c5fd;
  background: rgba(59,130,246,0.1);
  padding: 4px 12px;
  border-radius: var(--radius-md);
}
.loading-state { padding: 48px; text-align: center; color: var(--foreground-muted); }
.rbac-body { flex: 1; min-height: 0; display: flex; }
.rbac-left {
  width: 256px;
  flex-shrink: 0;
  border-right: 1px solid var(--border-subtle);
  background: var(--surface-card);
  display: flex;
  flex-direction: column;
}
.left-header {
  padding: 12px 16px 6px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.custom-header { margin-top: 8px; }
.role-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.left-footer {
  padding: 12px;
  border-top: 1px solid var(--border-subtle);
}
.add-role-btn {
  width: 100%;
  padding: 8px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-muted);
  font-size: var(--font-size-sm);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}
.add-role-btn:hover { background: rgba(30,41,59,0.6); color: var(--foreground-primary); }
.rbac-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.role-avatar {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: rgba(255,255,255,0.8);
}
.role-avatar.from-red-500\/20 { background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.05)); }
.role-avatar.from-blue-500\/20 { background: linear-gradient(135deg, rgba(59,130,246,0.2), rgba(59,130,246,0.05)); }
.role-avatar.from-emerald-500\/20 { background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(16,185,129,0.05)); }
.role-avatar.from-slate-500\/20 { background: linear-gradient(135deg, rgba(100,116,139,0.2), rgba(100,116,139,0.05)); }
.role-avatar.from-zinc-500\/20 { background: linear-gradient(135deg, rgba(113,113,122,0.2), rgba(113,113,122,0.05)); }
.role-avatar.from-teal-500\/20 { background: linear-gradient(135deg, rgba(20,184,166,0.2), rgba(20,184,166,0.05)); }
.header-role-name {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}
.badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  gap: 4px;
}
.builtin-badge { background: rgba(30,41,59,0.6); color: var(--foreground-muted); border: 1px solid var(--border-subtle); }
.super-badge { background: rgba(239,68,68,0.15); color: #fca5a5; border: 1px solid rgba(239,68,68,0.4); }
.header-role-desc { margin-top: 2px; font-size: var(--font-size-xs); color: var(--foreground-muted); }
.header-right { display: flex; align-items: center; gap: 16px; }
.header-stats { display: flex; gap: 24px; }
.stat { text-align: center; }
.stat-val { font-size: var(--font-size-md); font-weight: var(--font-weight-semibold); color: var(--foreground-primary); }
.stat-val.blue { color: #60a5fa; }
.stat-val.purple { color: #c084fc; }
.stat-label { font-size: 11px; color: var(--foreground-muted); }
.save-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: var(--accent-primary);
  border: none;
  border-radius: var(--radius-md);
  color: #fff;
  font-size: var(--font-size-sm);
  cursor: pointer;
}
.save-btn:hover { filter: brightness(1.1); }
.save-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.tab-bar {
  display: flex;
  padding: 0 24px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--foreground-muted);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}
.tab-btn.active {
  border-bottom-color: var(--accent-primary);
  color: var(--foreground-primary);
}
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}
.notice {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 16px;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  margin-bottom: 12px;
  line-height: 1.5;
}
.notice-red { background: rgba(239,68,68,0.05); border: 1px solid rgba(239,68,68,0.2); color: #fca5a5; }
.notice-amber { background: rgba(245,158,11,0.05); border: 1px solid rgba(245,158,11,0.2); color: #fcd34d; }
.notice-blue { background: rgba(59,130,246,0.05); border: 1px solid rgba(59,130,246,0.2); color: #93c5fd; }
.font-medium { font-weight: var(--font-weight-medium); }
.opacity-70 { opacity: 0.7; }
.perm-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.search-wrap {
  position: relative;
  flex: 1;
  max-width: 280px;
}
.search-wrap svg { position: absolute; left: 8px; top: 50%; transform: translateY(-50%); color: var(--foreground-muted); }
.search-input {
  width: 100%;
  padding: 4px 10px 4px 28px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
}
.search-input:focus { border-color: var(--accent-primary); }
.tool-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-muted);
  font-size: var(--font-size-xs);
  cursor: pointer;
}
.tool-btn:hover { background: rgba(30,41,59,0.6); }
.legend {
  display: flex;
  gap: 12px;
  margin-left: auto;
  font-size: 11px;
  color: var(--foreground-muted);
}
.legend span { display: flex; align-items: center; gap: 4px; }
.perm-tree {
  background: rgba(15,23,42,0.6);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 8px;
}
.scope-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 弹窗 */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
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
}
.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 0;
}
.dialog-header h3 { font-size: var(--font-size-md); color: var(--foreground-primary); margin: 0; }
.dialog-close { background: none; border: none; font-size: 22px; color: var(--foreground-muted); cursor: pointer; }
.dialog-sub { padding: 0 24px; margin: 4px 0 0; font-size: var(--font-size-sm); color: var(--foreground-muted); }
.dialog-body { padding: 16px 24px; display: flex; flex-direction: column; gap: 14px; }
.form-row { display: flex; flex-direction: column; gap: 4px; }
.form-row label { font-size: var(--font-size-sm); color: var(--foreground-muted); }
.form-row input, .form-row textarea, .form-row select {
  padding: 8px 12px;
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
  resize: vertical;
}
.form-row input:focus { border-color: var(--accent-primary); }
.copy-options { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.copy-opt {
  padding: 6px 10px;
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-muted);
  font-size: var(--font-size-xs);
  cursor: pointer;
  text-align: center;
}
.copy-opt.active { border-color: rgba(59,130,246,0.5); background: rgba(59,130,246,0.15); color: #93c5fd; }
.dialog-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 0 24px 20px; }
.dialog-cancel {
  padding: 8px 18px;
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
}
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
</style>
