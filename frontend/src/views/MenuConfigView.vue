<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ChevronLeft, Plus, Edit2, Trash2, Check, X, Info, Lock, Search,
  Layers, KeyRound, Route, Save, MousePointerClick,
} from 'lucide-vue-next'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useMenuConfigStore } from '@/stores/menuConfig'
import { PERM_TYPE_CONFIG, PERM_STATUS_CONFIG, BTN_VARIANT_LABEL } from '@/types/admin'
import type { PermResource, PermType, PermStatus, BtnVariant } from '@/types/admin'
import MenuConfigTreeNode from '@/components/admin/MenuConfigTreeNode.vue'

const router = useRouter()
const store = useMenuConfigStore()

onMounted(() => { store.fetchAll() })

// 弹窗
const dialogOpen = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const dialogForm = ref({
  id: '',
  parentId: null as string | null,
  type: 'menu' as PermType,
  label: '',
  permKey: '',
  path: '',
  icon: 'Folder',
  sortOrder: 1,
  status: 'active' as PermStatus,
  description: '',
  btnVariant: 'default' as BtnVariant,
  danger: false,
})

const parentOptions = computed(() => {
  if (dialogForm.value.type === 'catalog') return []
  if (dialogForm.value.type === 'menu') return store.resources.filter((r) => r.type === 'catalog')
  return store.resources.filter((r) => r.type === 'menu')
})

function openCreate(parent: PermResource | null, type?: PermType) {
  dialogMode.value = 'create'
  let defaultType: PermType = type ?? 'menu'
  if (parent) {
    defaultType = parent.type === 'catalog' ? 'menu' : 'button'
  } else {
    defaultType = 'catalog'
  }
  dialogForm.value = {
    id: '',
    parentId: parent?.id ?? null,
    type: defaultType,
    label: '',
    permKey: '',
    path: '',
    icon: defaultType === 'button' ? 'MousePointerClick' : defaultType === 'catalog' ? 'Folder' : 'FolderTree',
    sortOrder: 1,
    status: 'active',
    description: '',
    btnVariant: 'default',
    danger: false,
  }
  dialogOpen.value = true
}

function openEdit(r: PermResource) {
  dialogMode.value = 'edit'
  dialogForm.value = {
    id: r.id,
    parentId: r.parentId,
    type: r.type,
    label: r.label,
    permKey: r.permKey,
    path: r.path ?? '',
    icon: r.icon,
    sortOrder: r.sortOrder,
    status: r.status,
    description: r.description ?? '',
    btnVariant: r.btnVariant ?? 'default',
    danger: r.danger ?? false,
  }
  dialogOpen.value = true
}

async function submitForm() {
  const f = dialogForm.value
  if (!f.label.trim() || !f.permKey.trim()) {
    ElMessage.warning('请填写名称和权限标识')
    return
  }
  if (dialogMode.value === 'create') {
    await store.handleCreate({
      parentId: f.parentId,
      type: f.type,
      label: f.label.trim(),
      permKey: f.permKey.trim(),
      path: f.path.trim() || undefined,
      icon: f.icon,
      sortOrder: f.sortOrder,
      status: f.status,
      description: f.description.trim() || undefined,
      btnVariant: f.type === 'button' ? f.btnVariant : undefined,
      danger: f.type === 'button' ? f.danger : undefined,
    })
  } else {
    await store.handleUpdate({
      id: f.id,
      label: f.label.trim(),
      permKey: f.permKey.trim(),
      path: f.path.trim() || undefined,
      icon: f.icon,
      sortOrder: f.sortOrder,
      status: f.status,
      description: f.description.trim() || undefined,
      btnVariant: f.type === 'button' ? f.btnVariant : undefined,
      danger: f.type === 'button' ? f.danger : undefined,
    })
  }
  dialogOpen.value = false
}

async function handleDelete(r: PermResource) {
  if (r.isBuiltin) {
    ElMessage.warning('内置资源不可删除')
    return
  }
  try {
    await ElMessageBox.confirm(`确定删除「${r.label}」及其所有下级资源吗？`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await store.handleDelete(r.id)
    ElMessage.success('已删除')
  } catch { /* cancelled */ }
}

function getChildrenList(parentId: string | null): PermResource[] {
  return store.resources
    .filter((r) => r.parentId === parentId)
    .sort((a, b) => a.sortOrder - b.sortOrder)
}

function handleBack() {
  router.push('/admin')
}
</script>

<template>
  <div class="mc-page">
    <div class="mc-topbar">
      <div class="topbar-left">
        <button class="back-btn" @click="handleBack">
          <ChevronLeft :size="16" />返回
        </button>
        <div class="topbar-brand">
          <div class="brand-icon">
            <Layers :size="20" />
          </div>
          <div>
            <h1 class="brand-title">菜单与权限资源</h1>
            <p class="brand-sub">统一管理 目录 / 菜单 / 按钮 三类权限资源</p>
          </div>
        </div>
      </div>
      <div class="topbar-actions">
        <span v-if="store.saved" class="saved-badge">
          <Check :size="12" />已保存
        </span>
        <button class="create-root-btn" @click="openCreate(null, 'catalog')">
          <Plus :size="16" />新建顶级目录
        </button>
      </div>
    </div>

    <div v-if="store.loading" class="loading-state">加载中...</div>

    <div v-else class="mc-body">
      <!-- 左侧树 -->
      <aside class="mc-left">
        <div class="tree-toolbar">
          <div class="search-wrap">
            <Search :size="14" />
            <input
              v-model="store.searchQuery"
              type="text"
              class="search-input"
              placeholder="搜索名称或 permKey..."
            />
          </div>
          <button class="tool-btn" @click="store.expandedIds = new Set(store.resources.map(r => r.id))">
            全展开
          </button>
          <button class="tool-btn" @click="store.expandedIds = new Set()">
            全折叠
          </button>
        </div>
        <div class="tree-area">
          <MenuConfigTreeNode
            v-for="root in store.roots"
            :key="root.id"
            :resource="root"
            :depth="0"
            :selected-id="store.selectedId"
            :expanded-ids="store.expandedIds"
            :children-list="getChildrenList(root.id)"
            @select="store.selectResource"
            @toggle-expand="store.toggleExpand"
            @add-child="openCreate"
            @edit="openEdit"
            @delete="handleDelete"
          />
        </div>
      </aside>

      <!-- 右侧详情 -->
      <main class="mc-main">
        <div v-if="!store.selected" class="empty-detail">
          <Info :size="40" />
          请选择左侧资源查看详情
        </div>

        <div v-else class="detail-panel">
          <div class="detail-header">
            <div class="detail-title-row">
              <div class="detail-icon" :class="PERM_TYPE_CONFIG[store.selected.type].bg">
                <component :is="store.selected.icon" :size="24" :class="PERM_TYPE_CONFIG[store.selected.type].color" />
              </div>
              <div>
                <div class="detail-title">
                  {{ store.selected.label }}
                  <span class="type-badge" :class="PERM_TYPE_CONFIG[store.selected.type].bg">
                    {{ PERM_TYPE_CONFIG[store.selected.type].label }}
                  </span>
                  <span class="status-badge" :class="PERM_STATUS_CONFIG[store.selected.status].color">
                    {{ PERM_STATUS_CONFIG[store.selected.status].label }}
                  </span>
                  <span v-if="store.selected.isBuiltin" class="builtin-badge">
                    <Lock :size="12" />内置
                  </span>
                </div>
                <div class="detail-meta">
                  <span><KeyRound :size="12" />{{ store.selected.permKey }}</span>
                  <span v-if="store.selected.path"><Route :size="12" />{{ store.selected.path }}</span>
                </div>
              </div>
            </div>
            <div class="detail-actions">
              <button class="action-btn" @click="openEdit(store.selected!)"><Edit2 :size="14" />编辑</button>
              <button v-if="!store.selected!.isBuiltin" class="action-btn danger" @click="handleDelete(store.selected!)"><Trash2 :size="14" />删除</button>
            </div>
          </div>

          <div class="detail-tabs">
            <button :class="{ active: store.activeTab === 'basic' }" @click="store.activeTab = 'basic'">基本信息</button>
            <button v-if="store.selected.type === 'menu'" :class="{ active: store.activeTab === 'buttons' }" @click="store.activeTab = 'buttons'">
              下级按钮 ({{ store.buttonsOfSelected.length }})
            </button>
            <button v-if="store.selected.type !== 'button'" :class="{ active: store.activeTab === 'roles' }" @click="store.activeTab = 'roles'">角色覆盖</button>
          </div>

          <!-- 基本信息 -->
          <div v-if="store.activeTab === 'basic'" class="detail-section">
            <div class="info-row"><span>资源类型</span><span>{{ PERM_TYPE_CONFIG[store.selected.type].label }}</span></div>
            <div class="info-row"><span>名称</span><span>{{ store.selected.label }}</span></div>
            <div class="info-row"><span>权限标识</span><code>{{ store.selected.permKey }}</code></div>
            <div v-if="store.selected.path" class="info-row"><span>路径</span><span>{{ store.selected.path }}</span></div>
            <div class="info-row"><span>排序</span><span>{{ store.selected.sortOrder }}</span></div>
            <div v-if="store.selected.type === 'button' && store.selected.btnVariant" class="info-row">
              <span>按钮样式</span>
              <span>{{ BTN_VARIANT_LABEL[store.selected.btnVariant].label }}</span>
            </div>
            <div v-if="store.selected.description" class="info-row"><span>描述</span><p>{{ store.selected.description }}</p></div>
          </div>

          <!-- 下级按钮 -->
          <div v-if="store.activeTab === 'buttons' && store.selected.type === 'menu'" class="detail-section">
            <div class="section-header">
              <span>{{ store.buttonsOfSelected.length }} 个按钮权限</span>
              <button class="add-btn" @click="openCreate(store.selected!, 'button')">
                <Plus :size="14" />添加按钮
              </button>
            </div>
            <div v-if="store.buttonsOfSelected.length === 0" class="empty-hint">暂无按钮权限</div>
            <table v-else class="btn-table">
              <thead>
                <tr>
                  <th>按钮</th><th>permKey</th><th>样式</th><th>状态</th><th>角色覆盖</th><th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="b in store.buttonsOfSelected" :key="b.id">
                  <td><component :is="b.icon" :size="14" class="mr-1" />{{ b.label }}</td>
                  <td class="mono">{{ b.permKey }}</td>
                  <td><span class="variant-tag" :class="BTN_VARIANT_LABEL[b.btnVariant ?? 'default'].color">{{ BTN_VARIANT_LABEL[b.btnVariant ?? 'default'].label }}</span></td>
                  <td>{{ PERM_STATUS_CONFIG[b.status].label }}</td>
                  <td>{{ store.roleCoverages.filter(rc => rc.hasPermission).length }} 个角色</td>
                  <td>
                    <button class="sm-btn" @click="openEdit(b)"><Edit2 :size="14" /></button>
                    <button v-if="!b.isBuiltin" class="sm-btn danger" @click="handleDelete(b)"><Trash2 :size="14" /></button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 角色覆盖 -->
          <div v-if="store.activeTab === 'roles' && store.selected.type !== 'button'" class="detail-section">
            <p class="section-desc">下列角色已被授予该资源的访问权限（基于默认角色权限模板）</p>
            <div class="role-grid">
              <div
                v-for="rc in store.roleCoverages"
                :key="rc.roleKey"
                class="role-cell"
                :class="{ granted: rc.hasPermission }"
              >
                <div>
                  <div class="role-cell-name">{{ rc.roleName }}</div>
                  <div class="role-cell-key">{{ rc.roleKey }}</div>
                </div>
                <span v-if="rc.hasPermission" class="grant-badge"><Check :size="12" />已授权</span>
                <span v-else class="deny-badge">未授权</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>

    <!-- 弹窗 -->
    <Teleport to="body">
      <div v-if="dialogOpen" class="dialog-overlay" @click.self="dialogOpen = false">
        <div class="dialog-panel">
          <div class="dialog-header">
            <h3>{{ dialogMode === 'create' ? '新建资源' : '编辑资源' }}</h3>
            <button class="dialog-close" @click="dialogOpen = false">&times;</button>
          </div>
          <p class="dialog-sub">目录用于分组，菜单对应页面，按钮对应页面内的操作权限点</p>
          <div class="dialog-body">
            <div class="form-row-2col">
              <div class="form-row">
                <label>资源类型</label>
                <select
                  v-model="dialogForm.type"
                  :disabled="dialogMode === 'edit'"
                  @change="dialogForm.type === 'catalog' && (dialogForm.parentId = null)"
                >
                  <option value="catalog">目录</option>
                  <option value="menu">菜单</option>
                  <option value="button">按钮</option>
                </select>
              </div>
              <div class="form-row">
                <label>上级</label>
                <select v-model="dialogForm.parentId" :disabled="dialogForm.type === 'catalog'">
                  <option v-if="dialogForm.type === 'catalog'" :value="null">无（顶级）</option>
                  <option v-for="p in parentOptions" :key="p.id" :value="p.id">{{ p.label }}</option>
                </select>
              </div>
            </div>
            <div class="form-row-2col">
              <div class="form-row">
                <label>名称 *</label>
                <input v-model="dialogForm.label" type="text" placeholder="例：智能体管理" />
              </div>
              <div class="form-row">
                <label>权限标识 *</label>
                <input v-model="dialogForm.permKey" type="text" placeholder="例：agent:manage" class="mono" />
              </div>
            </div>
            <div v-if="dialogForm.type !== 'button'" class="form-row-2col">
              <div class="form-row">
                <label>路径</label>
                <input v-model="dialogForm.path" type="text" placeholder="/agents" class="mono" />
              </div>
              <div class="form-row">
                <label>图标</label>
                <select v-model="dialogForm.icon">
                  <option value="MessageSquare">MessageSquare</option>
                  <option value="Database">Database</option>
                  <option value="LayoutGrid">LayoutGrid</option>
                  <option value="Cpu">Cpu</option>
                  <option value="Bot">Bot</option>
                  <option value="Wrench">Wrench</option>
                  <option value="Zap">Zap</option>
                  <option value="Puzzle">Puzzle</option>
                  <option value="Shield">Shield</option>
                  <option value="Users">Users</option>
                  <option value="Timer">Timer</option>
                  <option value="Settings">Settings</option>
                  <option value="Folder">Folder</option>
                  <option value="FolderTree">FolderTree</option>
                  <option value="MousePointerClick">MousePointerClick</option>
                </select>
              </div>
            </div>
            <div v-if="dialogForm.type === 'button'" class="form-row-2col">
              <div class="form-row">
                <label>按钮样式</label>
                <select v-model="dialogForm.btnVariant">
                  <option value="default">默认</option>
                  <option value="primary">主要</option>
                  <option value="danger">危险</option>
                  <option value="ghost">幽灵</option>
                </select>
              </div>
              <div class="form-row danger-toggle">
                <label>高危操作</label>
                <input type="checkbox" v-model="dialogForm.danger" />
              </div>
            </div>
            <div class="form-row-2col">
              <div class="form-row">
                <label>排序</label>
                <input v-model.number="dialogForm.sortOrder" type="number" />
              </div>
              <div class="form-row">
                <label>状态</label>
                <select v-model="dialogForm.status">
                  <option value="active">启用</option>
                  <option value="hidden">隐藏</option>
                  <option value="disabled">停用</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <label>描述</label>
              <textarea v-model="dialogForm.description" rows="2" placeholder="说明该资源的用途" />
            </div>
          </div>
          <div class="dialog-footer">
            <button class="dialog-cancel" @click="dialogOpen = false">取消</button>
            <button class="dialog-submit" @click="submitForm"><Save :size="14" />保存</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.mc-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--surface-primary);
}
.mc-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  background: rgba(15, 23, 42, 0.7);
}
.topbar-left { display: flex; align-items: center; gap: 16px; }
.back-btn {
  display: flex; align-items: center; gap: 4px;
  background: none; border: none;
  color: var(--foreground-muted); font-size: var(--font-size-sm);
  cursor: pointer; padding: 4px 8px; border-radius: var(--radius-sm);
}
.back-btn:hover { color: var(--foreground-primary); }
.topbar-brand { display: flex; align-items: center; gap: 12px; }
.brand-icon {
  width: 40px; height: 40px;
  border-radius: var(--radius-xl);
  background: linear-gradient(135deg, #3b82f6, #9333ea);
  display: flex; align-items: center; justify-content: center;
  color: #fff;
}
.brand-title { font-size: var(--font-size-md); font-weight: var(--font-weight-semibold); color: var(--foreground-primary); margin: 0; }
.brand-sub { font-size: var(--font-size-xs); color: var(--foreground-muted); margin: 2px 0 0; }
.topbar-actions { display: flex; align-items: center; gap: 8px; }
.saved-badge {
  display: flex; align-items: center; gap: 4px;
  padding: 4px 10px;
  background: rgba(16,185,129,0.15); color: #6ee7b7;
  border: 1px solid rgba(16,185,129,0.3);
  border-radius: var(--radius-md); font-size: var(--font-size-xs);
}
.create-root-btn {
  display: flex; align-items: center; gap: 6px;
  padding: 8px 14px;
  background: linear-gradient(135deg, #3b82f6, #9333ea);
  border: none; border-radius: var(--radius-md);
  color: #fff; font-size: var(--font-size-sm); cursor: pointer;
}
.create-root-btn:hover { filter: brightness(1.1); }
.loading-state { padding: 48px; text-align: center; color: var(--foreground-muted); }
.mc-body {
  flex: 1; min-height: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  overflow: hidden;
}
.mc-left {
  border-right: 1px solid var(--border-subtle);
  background: rgba(15, 23, 42, 0.4);
  display: flex; flex-direction: column;
  overflow: hidden;
}
.tree-toolbar {
  display: flex; align-items: center; gap: 6px;
  padding: 12px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}
.search-wrap { position: relative; flex: 1; }
.search-wrap svg { position: absolute; left: 8px; top: 50%; transform: translateY(-50%); color: var(--foreground-muted); }
.search-input {
  width: 100%;
  padding: 4px 10px 4px 28px;
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
}
.tool-btn {
  padding: 4px 10px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-muted);
  font-size: var(--font-size-xs);
  cursor: pointer;
}
.tool-btn:hover { background: rgba(30,41,59,0.6); }
.tree-area {
  flex: 1; overflow-y: auto;
  padding: 8px;
}
.mc-main {
  overflow-y: auto;
  padding: 24px;
}
.empty-detail {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  height: 100%; color: var(--foreground-muted); gap: 12px;
}
.detail-panel {
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 24px;
}
.detail-header {
  display: flex; align-items: flex-start; justify-content: space-between;
}
.detail-title-row { display: flex; align-items: flex-start; gap: 12px; }
.detail-icon {
  width: 48px; height: 48px;
  border-radius: var(--radius-xl);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.detail-title {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  font-size: var(--font-size-md); font-weight: var(--font-weight-semibold); color: var(--foreground-primary);
}
.type-badge {
  font-size: 11px; padding: 2px 8px; border-radius: var(--radius-sm);
}
.status-badge {
  font-size: 11px; padding: 2px 8px; border-radius: var(--radius-sm);
}
.builtin-badge {
  font-size: 11px; padding: 2px 8px; border-radius: var(--radius-sm);
  background: rgba(100,116,139,0.1); color: var(--foreground-muted);
  border: 1px solid rgba(100,116,139,0.3);
  display: flex; align-items: center; gap: 3px;
}
.detail-meta {
  display: flex; gap: 16px; margin-top: 4px;
  font-size: var(--font-size-xs); color: var(--foreground-muted);
}
.detail-meta span { display: flex; align-items: center; gap: 4px; font-family: monospace; }
.detail-actions { display: flex; gap: 8px; }
.detail-actions .action-btn {
  display: flex; align-items: center; gap: 4px;
  padding: 6px 12px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
}
.detail-actions .action-btn:hover { background: rgba(30,41,59,0.6); }
.detail-actions .action-btn.danger { color: #fca5a5; border-color: rgba(239,68,68,0.3); }
.detail-actions .action-btn.danger:hover { background: rgba(239,68,68,0.1); }
.detail-tabs {
  display: flex; gap: 0;
  margin: 20px 0 16px;
  background: rgba(15,23,42,0.4);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.detail-tabs button {
  padding: 8px 16px;
  background: none; border: none;
  color: var(--foreground-muted);
  font-size: var(--font-size-sm);
  cursor: pointer;
}
.detail-tabs button.active {
  background: var(--accent-primary); color: #fff;
}
.detail-section { display: flex; flex-direction: column; gap: 8px; }
.info-row {
  display: grid; grid-template-columns: 140px 1fr;
  gap: 12px; align-items: center;
  padding: 6px 0;
}
.info-row > span:first-child { font-size: var(--font-size-sm); color: var(--foreground-muted); }
.info-row > span:last-child { font-size: var(--font-size-sm); color: var(--foreground-secondary); }
.info-row code { font-family: monospace; font-size: var(--font-size-xs); color: #93c5fd; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.section-header span { font-size: var(--font-size-sm); color: var(--foreground-muted); }
.add-btn {
  display: flex; align-items: center; gap: 4px;
  padding: 4px 12px;
  background: linear-gradient(135deg, #3b82f6, #9333ea);
  border: none; border-radius: var(--radius-md);
  color: #fff; font-size: var(--font-size-xs); cursor: pointer;
}
.empty-hint {
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 40px;
  text-align: center;
  color: var(--foreground-muted);
  font-size: var(--font-size-sm);
}
.btn-table { width: 100%; border-collapse: collapse; font-size: var(--font-size-sm); }
.btn-table th {
  text-align: left; padding: 8px 12px;
  font-size: var(--font-size-xs); font-weight: var(--font-weight-semibold);
  color: var(--foreground-muted); border-bottom: 1px solid var(--border-subtle);
}
.btn-table td { padding: 8px 12px; color: var(--foreground-primary); border-bottom: 1px solid var(--border-subtle); }
.btn-table tr:hover td { background: rgba(30,41,59,0.2); }
.mono { font-family: monospace; font-size: var(--font-size-xs); }
.mr-1 { margin-right: 4px; }
.variant-tag { font-size: 10px; padding: 1px 6px; border-radius: var(--radius-sm); }
.sm-btn {
  padding: 4px; background: none; border: none;
  color: var(--foreground-muted); cursor: pointer;
  border-radius: var(--radius-sm); display: inline-flex; align-items: center;
}
.sm-btn:hover { background: rgba(30,41,59,0.6); }
.sm-btn.danger:hover { background: rgba(239,68,68,0.15); color: #fca5a5; }
.section-desc { font-size: var(--font-size-sm); color: var(--foreground-muted); }
.role-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.role-cell {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px; border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  background: rgba(15,23,42,0.4);
}
.role-cell.granted {
  background: rgba(16,185,129,0.05);
  border-color: rgba(16,185,129,0.3);
}
.role-cell-name { font-size: var(--font-size-sm); color: var(--foreground-primary); }
.role-cell-key { font-size: var(--font-size-xs); font-family: monospace; color: var(--foreground-muted); }
.grant-badge {
  display: flex; align-items: center; gap: 4px;
  font-size: 11px; padding: 2px 8px; border-radius: var(--radius-sm);
  background: rgba(16,185,129,0.15); color: #6ee7b7;
  border: 1px solid rgba(16,185,129,0.3);
}
.deny-badge {
  font-size: 11px; padding: 2px 8px; border-radius: var(--radius-sm);
  background: rgba(100,116,139,0.15); color: var(--foreground-muted);
}

/* 弹窗 */
.dialog-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.dialog-panel {
  background: var(--surface-card); border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl); width: 640px; max-height: 90vh; overflow-y: auto;
}
.dialog-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px 0; }
.dialog-header h3 { font-size: var(--font-size-md); color: var(--foreground-primary); margin: 0; }
.dialog-close { background: none; border: none; font-size: 22px; color: var(--foreground-muted); cursor: pointer; }
.dialog-sub { padding: 0 24px; margin: 4px 0 0; font-size: var(--font-size-sm); color: var(--foreground-muted); }
.dialog-body { padding: 16px 24px; display: flex; flex-direction: column; gap: 14px; }
.form-row-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-row { display: flex; flex-direction: column; gap: 4px; }
.form-row label { font-size: var(--font-size-sm); color: var(--foreground-muted); }
.form-row input, .form-row select, .form-row textarea {
  padding: 8px 12px;
  background: var(--surface-primary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
  resize: vertical;
}
.form-row input:focus, .form-row select:focus { border-color: var(--accent-primary); }
.mono { font-family: monospace; }
.danger-toggle { display: flex; flex-direction: row; align-items: center; gap: 12px; }
.danger-toggle input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--accent-primary); }
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
  display: flex; align-items: center; gap: 4px;
  padding: 8px 18px;
  background: linear-gradient(135deg, #3b82f6, #9333ea);
  border: none; border-radius: var(--radius-md);
  color: #fff; font-size: var(--font-size-sm);
  cursor: pointer;
}
</style>
