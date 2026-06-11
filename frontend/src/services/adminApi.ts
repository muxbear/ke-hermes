// 管理后台 API 服务（Mock 数据）
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
} from '@/types/admin'

function delay(ms = 300): Promise<void> {
  return new Promise((r) => setTimeout(r, ms))
}

// ─── 管理仪表盘 Mock ──────────────────────────────────────────────────────────

export async function fetchAdminTiles(): Promise<AdminTileConfig[]> {
  await delay()
  return [
    { id: 'system', icon: 'Settings', title: '系统设置', description: '站点信息、时区、语言、备份与基础安全策略。', gradient: 'from-blue-500/20 to-blue-500/5', group: 'basic' },
    { id: 'menu-config', icon: 'LayoutList', title: '菜单配置', description: '管理系统功能菜单及页面操作权限（按钮、开关），与角色权限联动。', route: '/admin/menu-config', gradient: 'from-cyan-500/20 to-cyan-500/5', group: 'basic' },
    { id: 'notifications', icon: 'Bell', title: '通知配置', description: '邮件、Webhook、IM 渠道与告警规则。', gradient: 'from-amber-500/20 to-amber-500/5', group: 'basic' },
    { id: 'billing', icon: 'CreditCard', title: '计费与配额', description: '按租户/模型设置 Token 上限与计费方案。', gradient: 'from-emerald-500/20 to-emerald-500/5', group: 'basic' },
    { id: 'users', icon: 'Users', title: '人员管理', description: '维护账号、部门与组织架构，分配负责人。', route: '/admin/users', gradient: 'from-violet-500/20 to-violet-500/5', group: 'people' },
    { id: 'rbac', icon: 'ShieldCheck', title: '角色权限', description: 'RBAC 角色定义、菜单与数据权限粒度配置。', route: '/admin/rbac', gradient: 'from-fuchsia-500/20 to-fuchsia-500/5', group: 'people' },
    { id: 'api-keys', icon: 'Key', title: '密钥管理', description: 'API Key 颁发、轮换、过期与调用审计。', gradient: 'from-indigo-500/20 to-indigo-500/5', group: 'people' },
    { id: 'audit', icon: 'ScrollText', title: '审计日志', description: '登录、配置变更、模型调用全量操作追溯。', gradient: 'from-rose-500/20 to-rose-500/5', group: 'people' },
    { id: 'ai-config', icon: 'Cpu', title: 'AI 配置', description: '默认模型、提示词模板、安全围栏与速率限制。', gradient: 'from-blue-500/20 to-purple-500/10', group: 'extension' },
    { id: 'feature-config', icon: 'ToggleRight', title: '功能配置', description: '对话、知识库、定时任务等模块的高级参数。', gradient: 'from-sky-500/20 to-sky-500/5', group: 'extension' },
    { id: 'plugins', icon: 'Puzzle', title: '插件管理', description: '浏览、安装、启停官方与第三方插件。', gradient: 'from-teal-500/20 to-teal-500/5', group: 'extension' },
    { id: 'integrations', icon: 'Plug', title: '第三方集成', description: 'SSO、对象存储、向量库、企业 IM 接入。', gradient: 'from-orange-500/20 to-orange-500/5', group: 'extension' },
    { id: 'data', icon: 'DatabaseBackup', title: '数据管理', description: '数据导入导出、备份恢复与租户级清理。', gradient: 'from-lime-500/20 to-lime-500/5', group: 'extension' },
    { id: 'devops', icon: 'Code2', title: '二次开发', description: '开放接口、SDK、Webhook 与 DevOps 资源。', gradient: 'from-pink-500/20 to-pink-500/5', group: 'extension' },
  ]
}

export async function fetchSystemStats(): Promise<SystemStats> {
  await delay(250)
  return { version: 'v0.0.1', uptime: 12, onlineInstances: 8, registeredUsers: 142, activeAlerts: 3 }
}

export async function fetchUpdateLogs(): Promise<UpdateLogEntry[]> {
  await delay(200)
  return [
    { tag: 'v0.0.1', date: '2026-06-08', title: 'ke-hermes 首个开发预览版上线', primary: true },
    { tag: 'Beta', date: '2026-05-22', title: '新增 DeepSeek 提供商与定时任务模块' },
    { tag: 'Beta', date: '2026-05-10', title: '工具中心支持工具包拖拽上传与自动解析' },
  ]
}

// ─── 人员管理 Mock ─────────────────────────────────────────────────────────────

let departments: Department[] = [
  { id: 'd1', name: '公司总部', parentId: null, managerId: null, description: '公司组织架构根节点', memberCount: 142, children: [] },
  { id: 'd2', name: '技术部', parentId: 'd1', managerId: 'u2', description: '负责产品研发、架构设计和技术运维', memberCount: 48, children: [] },
  { id: 'd3', name: '产品部', parentId: 'd1', managerId: null, description: '负责产品规划、需求分析和用户体验设计', memberCount: 22, children: [] },
  { id: 'd4', name: '运营部', parentId: 'd1', managerId: null, description: '负责市场运营、品牌推广和用户增长', memberCount: 18, children: [] },
  { id: 'd5', name: '前端组', parentId: 'd2', managerId: 'u1', description: 'Web 前端和移动端开发', memberCount: 16, children: [] },
  { id: 'd6', name: '后端组', parentId: 'd2', managerId: null, description: '服务端开发、API 和中间件', memberCount: 20, children: [] },
  { id: 'd7', name: 'AI 组', parentId: 'd2', managerId: null, description: '大模型应用、RAG 和智能体开发', memberCount: 12, children: [] },
  { id: 'd8', name: '设计组', parentId: 'd3', managerId: null, description: 'UI/UX 设计和视觉规范', memberCount: 6, children: [] },
  { id: 'd9', name: '市场部', parentId: 'd4', managerId: null, description: '品牌宣传和内容运营', memberCount: 10, children: [] },
  { id: 'd10', name: '客服部', parentId: 'd4', managerId: null, description: '客户支持和售后服务', memberCount: 8, children: [] },
]

// 建立父子关系引用（children）
function buildDepartmentTree(): Department[] {
  const map = new Map<string, Department>()
  const roots: Department[] = []
  for (const d of departments) {
    map.set(d.id, { ...d, children: [] })
  }
  for (const d of map.values()) {
    if (d.parentId && map.has(d.parentId)) {
      map.get(d.parentId)!.children.push(d)
    } else if (!d.parentId) {
      roots.push(d)
    }
  }
  return roots
}

let users: SystemUser[] = [
  { id: 'u1', name: '王科', employeeId: 'EMP001', deptId: 'd5', position: '前端组长', email: 'wangke@example.com', phone: '13800001001', status: 'active', joinDate: '2025-08-01' },
  { id: 'u2', name: '李明', employeeId: 'EMP002', deptId: 'd2', position: '技术总监', email: 'liming@example.com', phone: '13800001002', status: 'active', joinDate: '2025-06-15' },
  { id: 'u3', name: '张薇', deptId: 'd7', employeeId: 'EMP003', position: 'AI 工程师', email: 'zhangwei@example.com', phone: '13800001003', status: 'active', joinDate: '2026-01-10' },
  { id: 'u4', name: '赵强', employeeId: 'EMP004', deptId: 'd6', position: '后端工程师', email: 'zhaoqiang@example.com', phone: '13800001004', status: 'inactive', joinDate: '2025-10-20' },
  { id: 'u5', name: '孙丽', employeeId: 'EMP005', deptId: 'd8', position: 'UI 设计师', email: 'sunli@example.com', phone: '13800001005', status: 'active', joinDate: '2026-02-15' },
  { id: 'u6', name: '周杰', employeeId: 'EMP006', deptId: 'd3', position: '产品经理', email: 'zhoujie@example.com', phone: '13800001006', status: 'active', joinDate: '2025-09-01' },
  { id: 'u7', name: '吴芳', employeeId: 'EMP007', deptId: 'd9', position: '市场专员', email: 'wufang@example.com', phone: '13800001007', status: 'pending', joinDate: '2026-06-01' },
  { id: 'u8', name: '郑浩', employeeId: 'EMP008', deptId: 'd10', position: '客服主管', email: 'zhenghao@example.com', phone: '13800001008', status: 'active', joinDate: '2025-11-15' },
  { id: 'u9', name: '陈敏', employeeId: 'EMP009', deptId: 'd5', position: '前端工程师', email: 'chenmin@example.com', phone: '13800001009', status: 'active', joinDate: '2026-03-01' },
  { id: 'u10', name: '刘洋', employeeId: 'EMP010', deptId: 'd6', position: '后端工程师', email: 'liuyang@example.com', phone: '13800001010', status: 'active', joinDate: '2025-08-20' },
  { id: 'u11', name: '黄蕾', employeeId: 'EMP011', deptId: 'd8', position: '交互设计师', email: 'huanglei@example.com', phone: '13800001011', status: 'active', joinDate: '2026-04-15' },
  { id: 'u12', name: '马超', employeeId: 'EMP012', deptId: 'd7', position: '算法工程师', email: 'machao@example.com', phone: '13800001012', status: 'inactive', joinDate: '2025-12-01' },
]

export async function fetchDepartments(): Promise<Department[]> {
  await delay()
  return buildDepartmentTree()
}

export async function fetchUsers(deptId?: string): Promise<SystemUser[]> {
  await delay()
  if (deptId) return users.filter((u) => u.deptId === deptId)
  return [...users]
}

export async function createUser(data: CreateUserRequest): Promise<SystemUser> {
  await delay(400)
  const newUser: SystemUser = {
    id: `u${Date.now()}`,
    name: data.name,
    employeeId: data.employeeId,
    deptId: data.deptId,
    position: data.position,
    email: data.email,
    phone: data.phone,
    status: data.status,
    joinDate: new Date().toISOString().slice(0, 10),
  }
  users.unshift(newUser)
  // 更新部门人数
  const dept = departments.find((d) => d.id === data.deptId)
  if (dept) dept.memberCount++
  return { ...newUser }
}

export async function updateUser(data: UpdateUserRequest): Promise<SystemUser | null> {
  await delay(300)
  const idx = users.findIndex((u) => u.id === data.id)
  if (idx === -1) return null
  const oldDeptId = users[idx].deptId
  users[idx] = { ...users[idx], ...data }
  // 更新部门人数
  if (data.deptId && data.deptId !== oldDeptId) {
    const oldDept = departments.find((d) => d.id === oldDeptId)
    if (oldDept) oldDept.memberCount--
    const newDept = departments.find((d) => d.id === data.deptId)
    if (newDept) newDept.memberCount++
  }
  return { ...users[idx] }
}

export async function deleteUser(id: string): Promise<boolean> {
  await delay(300)
  const idx = users.findIndex((u) => u.id === id)
  if (idx === -1) return false
  const deptId = users[idx].deptId
  users.splice(idx, 1)
  const dept = departments.find((d) => d.id === deptId)
  if (dept) dept.memberCount--
  return true
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

// 默认角色权限（permKey -> Set）
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

// ─── RBAC API ─────────────────────────────────────────────────────────────────

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
  await delay()
  return [...roles]
}

export async function fetchPermissionResources(): Promise<PermResource[]> {
  await delay()
  return [...PERM_RESOURCES]
}

export async function fetchDataResources(): Promise<DataResource[]> {
  await delay()
  return [...DATA_RESOURCES]
}

export async function fetchRolePerms(roleId: string): Promise<PermRoleState> {
  await delay()
  initRolePerms()
  const state = rolePermSets[roleId]
  return state ? { granted: new Set(state.granted), dataScope: { ...state.dataScope } } : { granted: new Set(), dataScope: {} }
}

export async function saveRolePerms(
  roleId: string,
  granted: string[],
  dataScope: Record<string, DataScope>,
): Promise<boolean> {
  await delay(400)
  rolePermSets[roleId] = { granted: new Set(granted), dataScope: { ...dataScope } }
  return true
}

export async function createRole(data: { name: string; description: string; copyFrom: string }): Promise<RoleDef> {
  await delay(400)
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
  await delay(300)
  const role = roles.find((r) => r.id === id)
  if (!role || role.isBuiltin) return false
  roles = roles.filter((r) => r.id !== id)
  delete rolePermSets[id]
  return true
}

// ─── 菜单配置 API ─────────────────────────────────────────────────────────────

let menuResources: PermResource[] = [...PERM_RESOURCES]

export async function fetchMenuResources(): Promise<PermResource[]> {
  await delay()
  return [...menuResources]
}

export async function createMenuResource(data: Partial<PermResource> & { label: string; permKey: string; type: PermType }): Promise<PermResource> {
  await delay(400)
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
  await delay(300)
  const idx = menuResources.findIndex((r) => r.id === data.id)
  if (idx === -1) return null
  menuResources[idx] = { ...menuResources[idx], ...data }
  return menuResources[idx]
}

export async function deleteMenuResource(id: string): Promise<boolean> {
  await delay(300)
  const resource = menuResources.find((r) => r.id === id)
  if (!resource || resource.isBuiltin) return false
  // 递归删除子资源
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
  await delay(200)
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
