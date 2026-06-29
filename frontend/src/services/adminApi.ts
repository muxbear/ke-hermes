// 管理后台 API 服务
import instance from './request'
import type {
  AdminTileConfig,
  SystemStats,
  UpdateLogEntry,
  Department,
  SystemUser,
  CreateUserRequest,
  UpdateUserRequest,
  RoleDef,
  PermResource,
  PermType,
  DataResource,
  DataScope,
  OrgNode,
  AccountInfo,
  AccountCreateRequest,
  AccountUpdateRequest,
  AccountListResponse,
  AccountResetPasswordResponse,
} from '@/types/admin'

// ─── Helpers ───────────────────────────────────────────────────────────────────

function toSnakeCase(obj: Record<string, unknown>): Record<string, unknown> {
  const result: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(obj)) {
    if (value === undefined) continue
    const snakeKey = key.replace(/[A-Z]/g, (m) => '_' + m.toLowerCase())
    result[snakeKey] = value
  }
  return result
}

// ─── 管理仪表盘 (仍为 mock — 后续可迁移) ──────────────────────────────────────

export async function fetchAdminTiles(): Promise<AdminTileConfig[]> {
  return [
    { id: 'system', icon: 'Settings', title: '系统设置', description: '站点信息、时区、语言、备份与基础安全策略。', gradient: 'from-blue-500/20 to-blue-500/5', group: 'basic' },
    { id: 'menu-config', icon: 'LayoutList', title: '菜单配置', description: '管理系统功能菜单及页面操作权限（按钮、开关），与角色权限联动。', route: '/admin/menu-config', gradient: 'from-cyan-500/20 to-cyan-500/5', group: 'basic' },
    { id: 'notifications', icon: 'Bell', title: '通知配置', description: '邮件、Webhook、IM 渠道与告警规则。', gradient: 'from-amber-500/20 to-amber-500/5', group: 'basic' },
    { id: 'org', icon: 'Building2', title: '机构部门', description: '管理机构信息、部门层级与组织架构。', route: '/admin/org', gradient: 'from-emerald-500/20 to-emerald-500/5', group: 'basic' },
    { id: 'users', icon: 'Users', title: '人员管理', description: '维护账号、部门与组织架构，分配负责人。', route: '/admin/users', gradient: 'from-violet-500/20 to-violet-500/5', group: 'people' },
    { id: 'rbac', icon: 'ShieldCheck', title: '角色权限', description: 'RBAC 角色定义、菜单与数据权限粒度配置。', route: '/admin/rbac', gradient: 'from-fuchsia-500/20 to-fuchsia-500/5', group: 'people' },
    { id: 'api-keys', icon: 'UserRoundCog', title: '账号管理', description: '管理系统账号、登录策略与密码安全设置。', route: '/admin/accounts', gradient: 'from-indigo-500/20 to-indigo-500/5', group: 'people' },
    { id: 'plugins', icon: 'Puzzle', title: '插件管理', description: '浏览、安装、启停官方与第三方插件。', gradient: 'from-teal-500/20 to-teal-500/5', group: 'extension' },
    { id: 'integrations', icon: 'Plug', title: '第三方集成', description: 'SSO、对象存储、向量库、企业 IM 接入。', gradient: 'from-orange-500/20 to-orange-500/5', group: 'extension' },
    { id: 'audit', icon: 'ScrollText', title: '审计日志', description: '登录、配置变更、模型调用全量操作追溯。', gradient: 'from-rose-500/20 to-rose-500/5', group: 'extension' },
  ]
}

export async function fetchSystemStats(): Promise<SystemStats> {
  return { version: 'v0.0.1', uptime: 12, onlineInstances: 8, registeredUsers: 142, activeAlerts: 3 }
}

export async function fetchUpdateLogs(): Promise<UpdateLogEntry[]> {
  return [
    { tag: 'v0.0.1', date: '2026-06-08', title: 'ke-hermes 首个开发预览版上线', primary: true },
    { tag: 'Beta', date: '2026-05-22', title: '新增 DeepSeek 提供商与定时任务模块' },
    { tag: 'Beta', date: '2026-05-10', title: '工具中心支持工具包拖拽上传与自动解析' },
  ]
}

// ─── 机构部门 API ──────────────────────────────────────────────────────────────

export async function fetchOrgNodes(): Promise<OrgNode[]> {
  const res = await instance.get('/departments')
  return res.data.data
}

export async function createOrgNode(data: Omit<OrgNode, 'id' | 'createdAt'>): Promise<OrgNode> {
  const res = await instance.post('/departments', toSnakeCase(data as Record<string, unknown>))
  return res.data.data
}

export async function updateOrgNode(data: OrgNode): Promise<OrgNode | null> {
  const res = await instance.put(`/departments/${data.id}`, toSnakeCase(data as Record<string, unknown>))
  return res.data.data
}

export async function deleteOrgNodes(ids: string[]): Promise<boolean> {
  const res = await instance.delete('/departments', { data: { ids } })
  return res.data.code === 0
}

// ─── 部门树 (人员管理侧栏) ────────────────────────────────────────────────────

export async function fetchDepartments(): Promise<Department[]> {
  const res = await instance.get('/departments/tree')
  return res.data.data
}

// ─── 人员管理 API ─────────────────────────────────────────────────────────────

export async function fetchUsers(deptId?: string): Promise<SystemUser[]> {
  const res = await instance.get('/personnel', {
    params: deptId ? { dept_id: deptId } : undefined,
  })
  return res.data.data
}

export async function createUser(data: CreateUserRequest): Promise<SystemUser> {
  const res = await instance.post('/personnel', toSnakeCase(data as Record<string, unknown>))
  return res.data.data
}

export async function updateUser(data: UpdateUserRequest): Promise<SystemUser | null> {
  const res = await instance.put(
    `/personnel/${data.id}`,
    toSnakeCase({ ...data, id: undefined } as Record<string, unknown>),
  )
  return res.data.data
}

export async function deleteUser(id: string): Promise<boolean> {
  const res = await instance.delete(`/personnel/${id}`)
  return res.data.code === 0
}

// ─── 账号管理 API ─────────────────────────────────────────────────────────────

export async function fetchAccounts(
  params: { search?: string; page?: number; pageSize?: number } = {},
): Promise<AccountListResponse> {
  const res = await instance.get('/accounts', { params })
  return res.data.data
}

export async function fetchAccount(id: string): Promise<AccountInfo> {
  const res = await instance.get(`/accounts/${id}`)
  return res.data.data
}

export async function createAccount(data: AccountCreateRequest): Promise<AccountInfo> {
  const res = await instance.post('/accounts', toSnakeCase(data as Record<string, unknown>))
  return res.data.data
}

export async function updateAccount(
  id: string,
  data: AccountUpdateRequest,
): Promise<AccountInfo> {
  const res = await instance.put(
    `/accounts/${id}`,
    toSnakeCase(data as Record<string, unknown>),
  )
  return res.data.data
}

export async function deleteAccount(id: string): Promise<{ deleted: boolean }> {
  const res = await instance.delete(`/accounts/${id}`)
  return res.data.data
}

export async function toggleAccountStatus(id: string): Promise<AccountInfo> {
  const res = await instance.post(`/accounts/${id}/toggle-status`)
  return res.data.data
}

export async function unlockAccount(id: string): Promise<{ unlocked: boolean }> {
  const res = await instance.post(`/accounts/${id}/unlock`)
  return res.data.data
}

export async function resetAccountPassword(
  id: string,
): Promise<AccountResetPasswordResponse> {
  const res = await instance.post(`/accounts/${id}/reset-password`)
  return res.data.data
}

// ─── RBAC Mock ───────────────────────────────────────────────────────────────

export const INITIAL_ROLES: RoleDef[] = [
  { id: 'r1', key: 'super_admin', name: '超级管理员', description: '拥有系统的全部权限，可直接访问所有功能模块及数据。', isBuiltin: true, userCount: 1, status: 'active', color: 'from-red-500/20 to-red-500/5', badgeColor: 'bg-red-500/15 text-red-300 border-red-500/30' },
  { id: 'r2', key: 'admin', name: '管理员', description: '除超级管理员特权外的系统管理与配置权限。', isBuiltin: true, userCount: 3, status: 'active', color: 'from-blue-500/20 to-blue-500/5', badgeColor: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
  { id: 'r3', key: 'manager', name: '部门主管', description: '可管理部门成员、分配任务及查看部门级数据报表。', isBuiltin: true, userCount: 8, status: 'active', color: 'from-emerald-500/20 to-emerald-500/5', badgeColor: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
  { id: 'r4', key: 'member', name: '普通成员', description: '可使用基本功能，查看个人数据。', isBuiltin: true, userCount: 130, status: 'active', color: 'from-slate-500/20 to-slate-500/5', badgeColor: 'bg-slate-500/15 text-slate-300 border-slate-500/30' },
  { id: 'r5', key: 'guest', name: '访客', description: '仅可查看公开内容，不能编辑或删除任何数据。', isBuiltin: true, userCount: 0, status: 'active', color: 'from-zinc-500/20 to-zinc-500/5', badgeColor: 'bg-zinc-500/15 text-zinc-300 border-zinc-500/30' },
]

let roles: RoleDef[] = [...INITIAL_ROLES]

export const PERM_RESOURCES: PermResource[] = [
  { id: 'g-chat', parentId: null, type: 'catalog', label: '聊天', permKey: 'chat', icon: 'MessageSquare', sortOrder: 1, status: 'active', isBuiltin: true, description: '对话交互相关权限' },
  { id: 'm-chat', parentId: 'g-chat', type: 'menu', label: '对话', permKey: 'chat:conversation', path: '/', icon: 'MessageSquare', sortOrder: 1, status: 'active', isBuiltin: true, description: '对话主页面' },
  { id: 'b-chat-send', parentId: 'm-chat', type: 'button', label: '发送消息', permKey: 'chat:send', icon: 'Send', sortOrder: 1, status: 'active', isBuiltin: true, btnVariant: 'primary' },
  { id: 'b-chat-create', parentId: 'm-chat', type: 'button', label: '新建对话', permKey: 'chat:create', icon: 'Plus', sortOrder: 2, status: 'active', isBuiltin: true, btnVariant: 'primary' },
  { id: 'b-chat-delete', parentId: 'm-chat', type: 'button', label: '删除对话', permKey: 'chat:delete', icon: 'Trash2', sortOrder: 3, status: 'active', isBuiltin: true, btnVariant: 'danger', danger: true },

  { id: 'g-kb', parentId: null, type: 'catalog', label: '知识库', permKey: 'knowledge', icon: 'Database', sortOrder: 2, status: 'active', isBuiltin: true, description: '知识库模块权限' },
  { id: 'm-kb', parentId: 'g-kb', type: 'menu', label: '知识库', permKey: 'knowledge:base', path: '/knowledge-base', icon: 'Database', sortOrder: 1, status: 'active', isBuiltin: true, description: '知识库管理页面' },
  { id: 'b-kb-create', parentId: 'm-kb', type: 'button', label: '新建知识库', permKey: 'knowledge:create', icon: 'Plus', sortOrder: 1, status: 'active', isBuiltin: true, btnVariant: 'primary' },
  { id: 'b-kb-upload', parentId: 'm-kb', type: 'button', label: '上传文档', permKey: 'knowledge:upload', icon: 'Upload', sortOrder: 2, status: 'active', isBuiltin: true, btnVariant: 'primary' },
  { id: 'b-kb-delete', parentId: 'm-kb', type: 'button', label: '删除知识库', permKey: 'knowledge:delete', icon: 'Trash2', sortOrder: 3, status: 'active', isBuiltin: true, btnVariant: 'danger', danger: true },

  { id: 'g-ctrl', parentId: null, type: 'catalog', label: '控制', permKey: 'control', icon: 'LayoutGrid', sortOrder: 3, status: 'active', isBuiltin: true, description: '控制面板相关权限' },
  { id: 'm-ctrl-overview', parentId: 'g-ctrl', type: 'menu', label: '概览', permKey: 'control:overview', path: '/overview', icon: 'LayoutGrid', sortOrder: 1, status: 'active', isBuiltin: true, description: '系统概览仪表盘' },
  { id: 'm-ctrl-scheduled', parentId: 'g-ctrl', type: 'menu', label: '定时任务', permKey: 'control:scheduled', path: '/scheduled-tasks', icon: 'Timer', sortOrder: 2, status: 'active', isBuiltin: true, description: '定时任务管理' },
  { id: 'b-ctrl-task-create', parentId: 'm-ctrl-scheduled', type: 'button', label: '新建任务', permKey: 'control:task:create', icon: 'Plus', sortOrder: 1, status: 'active', isBuiltin: true, btnVariant: 'primary' },
  { id: 'b-ctrl-task-run', parentId: 'm-ctrl-scheduled', type: 'button', label: '执行任务', permKey: 'control:task:run', icon: 'Play', sortOrder: 2, status: 'active', isBuiltin: true, btnVariant: 'primary' },

  { id: 'g-agent', parentId: null, type: 'catalog', label: '智能体', permKey: 'agent', icon: 'Bot', sortOrder: 4, status: 'active', isBuiltin: true, description: '智能体管理权限' },
  { id: 'm-agent', parentId: 'g-agent', type: 'menu', label: '智能体', permKey: 'agent:manage', path: '/agents', icon: 'Bot', sortOrder: 1, status: 'active', isBuiltin: true, description: '智能体管理' },
  { id: 'm-agent-models', parentId: 'g-agent', type: 'menu', label: '模型', permKey: 'agent:models', path: '/models', icon: 'Cpu', sortOrder: 2, status: 'active', isBuiltin: true, description: '模型管理' },
  { id: 'm-agent-tools', parentId: 'g-agent', type: 'menu', label: '工具', permKey: 'agent:tools', path: '/tools', icon: 'Wrench', sortOrder: 3, status: 'active', isBuiltin: true, description: '工具管理' },
  { id: 'm-agent-skills', parentId: 'g-agent', type: 'menu', label: '技能', permKey: 'agent:skills', path: '/skills', icon: 'Zap', sortOrder: 4, status: 'active', isBuiltin: true, description: '技能管理' },

  { id: 'g-mcp', parentId: null, type: 'catalog', label: 'MCP', permKey: 'mcp', icon: 'Puzzle', sortOrder: 5, status: 'active', isBuiltin: true, description: 'MCP 相关权限' },
  { id: 'm-mcp', parentId: 'g-mcp', type: 'menu', label: 'MCP 广场', permKey: 'mcp:square', path: '/mcp', icon: 'Puzzle', sortOrder: 1, status: 'active', isBuiltin: true, description: 'MCP 工具广场' },

  { id: 'g-admin', parentId: null, type: 'catalog', label: '管理', permKey: 'admin', icon: 'Shield', sortOrder: 6, status: 'active', isBuiltin: true, description: '后台管理权限' },
  { id: 'm-admin', parentId: 'g-admin', type: 'menu', label: '后台', permKey: 'admin:dashboard', path: '/admin', icon: 'Shield', sortOrder: 1, status: 'active', isBuiltin: true, description: '管理仪表盘' },
  { id: 'm-admin-users', parentId: 'g-admin', type: 'menu', label: '人员管理', permKey: 'admin:users', path: '/admin/users', icon: 'Users', sortOrder: 2, status: 'active', isBuiltin: true, description: '人员与部门管理' },
  { id: 'm-admin-rbac', parentId: 'g-admin', type: 'menu', label: '角色权限', permKey: 'admin:rbac', path: '/admin/rbac', icon: 'ShieldCheck', sortOrder: 3, status: 'active', isBuiltin: true, description: '基于角色的访问控制' },
  { id: 'm-admin-menu', parentId: 'g-admin', type: 'menu', label: '菜单配置', permKey: 'admin:menu', path: '/admin/menu-config', icon: 'LayoutList', sortOrder: 4, status: 'active', isBuiltin: true, description: '菜单与权限资源管理' },
  { id: 'b-admin-user-create', parentId: 'm-admin-users', type: 'button', label: '新建用户', permKey: 'admin:user:create', icon: 'UserPlus', sortOrder: 1, status: 'active', isBuiltin: true, btnVariant: 'primary' },
  { id: 'b-admin-user-edit', parentId: 'm-admin-users', type: 'button', label: '编辑用户', permKey: 'admin:user:edit', icon: 'Edit2', sortOrder: 2, status: 'active', isBuiltin: true, btnVariant: 'default' },
  { id: 'b-admin-user-delete', parentId: 'm-admin-users', type: 'button', label: '删除用户', permKey: 'admin:user:delete', icon: 'Trash2', sortOrder: 3, status: 'active', isBuiltin: true, btnVariant: 'danger', danger: true },
  { id: 'b-admin-role-create', parentId: 'm-admin-rbac', type: 'button', label: '新建角色', permKey: 'admin:role:create', icon: 'Plus', sortOrder: 1, status: 'active', isBuiltin: true, btnVariant: 'primary' },
  { id: 'b-admin-role-save', parentId: 'm-admin-rbac', type: 'button', label: '保存权限', permKey: 'admin:role:save', icon: 'Save', sortOrder: 2, status: 'active', isBuiltin: true, btnVariant: 'primary' },
]

export const DATA_RESOURCES: DataResource[] = [
  { id: 'data-conversation', label: '对话记录', desc: '聊天消息与对话历史', icon: 'MessageSquare' },
  { id: 'data-knowledge', label: '知识库内容', desc: '文档、切片与索引数据', icon: 'Database' },
  { id: 'data-agent', label: '智能体配置', desc: '智能体定义、提示词与参数', icon: 'Bot' },
  { id: 'data-mcp', label: 'MCP 工具集', desc: '已安装的 MCP 工具与配置', icon: 'Puzzle' },
  { id: 'data-scheduled', label: '定时任务', desc: 'Cron 任务及运行记录', icon: 'Timer' },
  { id: 'data-user', label: '用户信息', desc: '账号、部门与联系方式', icon: 'Users' },
  { id: 'data-log', label: '审计日志', desc: '操作审计与安全事件', icon: 'ScrollText' },
]

export const DEFAULT_ROLE_PERMS: Record<string, { perms: Set<string>; dataScope: Record<string, DataScope> }> = {
  super_admin: {
    perms: new Set(PERM_RESOURCES.map((r) => r.permKey)),
    dataScope: Object.fromEntries(DATA_RESOURCES.map((r) => [r.id, 'all' as DataScope])),
  },
  admin: {
    perms: new Set(PERM_RESOURCES.filter((r) => r.status === 'active').map((r) => r.permKey)),
    dataScope: Object.fromEntries(DATA_RESOURCES.map((r) => [r.id, 'all' as DataScope])),
  },
  manager: {
    perms: new Set(['chat:conversation', 'chat:send', 'chat:create', 'knowledge:base', 'knowledge:upload', 'control:overview', 'control:scheduled', 'control:task:create', 'agent:manage', 'agent:tools', 'agent:skills', 'mcp:square', 'admin:dashboard', 'admin:users']),
    dataScope: Object.fromEntries(DATA_RESOURCES.map((r) => [r.id, 'dept_and_children' as DataScope])),
  },
  member: {
    perms: new Set(['chat:conversation', 'chat:send', 'chat:create', 'knowledge:base', 'knowledge:upload', 'control:overview', 'agent:manage', 'agent:tools', 'mcp:square']),
    dataScope: Object.fromEntries(DATA_RESOURCES.map((r) => [r.id, 'self' as DataScope])),
  },
  guest: {
    perms: new Set(['chat:conversation', 'control:overview', 'mcp:square']),
    dataScope: Object.fromEntries(DATA_RESOURCES.map((r) => [r.id, 'none' as DataScope])),
  },
}

export function isSuperAdmin(key: string): boolean {
  return key === 'super_admin'
}

// ─── RBAC API (Mock) ────────────────────────────────────────────────────────

let rolePermSets: Record<string, PermRoleState> = {}

interface PermRoleState {
  granted: Set<string>
  dataScope: Record<string, DataScope>
}

function initRolePerms(): void {
  if (Object.keys(rolePermSets).length > 0) return
  for (const role of roles) {
    const preset = DEFAULT_ROLE_PERMS[role.key]
    rolePermSets[role.id] = {
      granted: new Set(preset?.perms ?? []),
      dataScope: { ...(preset?.dataScope ?? {}) },
    }
  }
}

export async function fetchRoles(): Promise<RoleDef[]> {
  return [...roles]
}

export async function fetchPermissionResources(): Promise<PermResource[]> {
  return [...PERM_RESOURCES]
}

export async function fetchDataResources(): Promise<DataResource[]> {
  return [...DATA_RESOURCES]
}

export async function fetchRolePerms(roleId: string): Promise<PermRoleState> {
  initRolePerms()
  const state = rolePermSets[roleId]
  return state ? { granted: new Set(state.granted), dataScope: { ...state.dataScope } } : { granted: new Set(), dataScope: {} }
}

export async function saveRolePerms(
  roleId: string,
  granted: string[],
  dataScope: Record<string, DataScope>,
): Promise<boolean> {
  rolePermSets[roleId] = { granted: new Set(granted), dataScope: { ...dataScope } }
  return true
}

export async function createRole(data: { name: string; description: string; copyFrom: string }): Promise<RoleDef> {
  const newRole: RoleDef = {
    id: `r-${Date.now()}`,
    key: `custom_${Date.now()}`,
    name: data.name,
    description: data.description,
    isBuiltin: false,
    userCount: 0,
    status: 'active',
    color: 'from-teal-500/20 to-teal-500/5',
    badgeColor: 'bg-teal-500/15 text-teal-400 border-teal-500/30',
  }
  roles.push(newRole)
  const src = data.copyFrom ? DEFAULT_ROLE_PERMS[data.copyFrom] : undefined
  rolePermSets[newRole.id] = {
    granted: new Set(src?.perms ?? []),
    dataScope: { ...(src?.dataScope ?? {}) },
  }
  return newRole
}

export async function deleteRole(id: string): Promise<boolean> {
  const role = roles.find((r) => r.id === id)
  if (!role || role.isBuiltin) return false
  roles = roles.filter((r) => r.id !== id)
  delete rolePermSets[id]
  return true
}

// ─── 菜单配置 API (Mock) ───────────────────────────────────────────────────

let menuResources: PermResource[] = [...PERM_RESOURCES]

export async function fetchMenuResources(): Promise<PermResource[]> {
  return [...menuResources]
}

export async function createMenuResource(data: Partial<PermResource> & { label: string; permKey: string; type: PermType }): Promise<PermResource> {
  const newRes: PermResource = {
    id: `${data.type}-${Date.now()}`,
    parentId: data.parentId ?? null,
    type: data.type,
    label: data.label,
    permKey: data.permKey,
    path: data.path,
    icon: data.icon ?? (data.type === 'button' ? 'MousePointerClick' : data.type === 'catalog' ? 'Folder' : 'FolderTree'),
    sortOrder: data.sortOrder ?? 1,
    status: data.status ?? 'active',
    isBuiltin: false,
    description: data.description,
    btnVariant: data.type === 'button' ? (data.btnVariant ?? 'default') : undefined,
    danger: data.type === 'button' ? (data.danger ?? false) : undefined,
  }
  menuResources.push(newRes)
  return newRes
}

export async function updateMenuResource(data: Partial<PermResource> & { id: string }): Promise<PermResource | null> {
  const idx = menuResources.findIndex((r) => r.id === data.id)
  if (idx === -1) return null
  menuResources[idx] = { ...menuResources[idx], ...data }
  return menuResources[idx]
}

export async function deleteMenuResource(id: string): Promise<boolean> {
  const resource = menuResources.find((r) => r.id === id)
  if (!resource || resource.isBuiltin) return false
  const idsToDelete = new Set<string>([id])
  let changed = true
  while (changed) {
    changed = false
    for (const r of menuResources) {
      if (r.parentId && idsToDelete.has(r.parentId) && !idsToDelete.has(r.id)) {
        idsToDelete.add(r.id)
        changed = true
      }
    }
  }
  menuResources = menuResources.filter((r) => !idsToDelete.has(r.id))
  return true
}

export async function fetchRoleCoverages(permKey: string): Promise<RoleCoverageResult[]> {
  initRolePerms()
  return roles.map((role) => {
    const state = rolePermSets[role.id]
    const has = state?.granted.has(permKey) ?? false
    return { roleKey: role.key, roleName: role.name, hasPermission: has }
  })
}

export interface RoleCoverageResult {
  roleKey: string
  roleName: string
  hasPermission: boolean
}
