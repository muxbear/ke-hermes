// 管理后台相关类型定义

// ─── 管理卡片 ─────────────────────────────────────────────────────────────────

export interface AdminTileConfig {
  id: string
  icon: string
  title: string
  description: string
  route?: string
  gradient: string
  group: 'basic' | 'people' | 'extension'
}

// ─── 系统信息 ─────────────────────────────────────────────────────────────────

export interface SystemStats {
  version: string
  uptime: number
  onlineInstances: number
  registeredUsers: number
  activeAlerts: number
}

// ─── 更新日志 ─────────────────────────────────────────────────────────────────

export interface UpdateLogEntry {
  tag: string
  date: string
  title: string
  primary?: boolean
}

// ─── 部门 ─────────────────────────────────────────────────────────────────────

export interface Department {
  id: string
  name: string
  parentId: string | null
  managerId: string | null
  description: string
  memberCount: number
  children: Department[]
}

// ─── 系统用户 ─────────────────────────────────────────────────────────────────

export type UserStatus = 'active' | 'inactive' | 'pending'

export interface SystemUser {
  id: string
  name: string
  employeeId: string
  deptId: string
  position: string
  email: string
  phone: string
  status: UserStatus
  joinDate: string
  avatar?: string
}

export interface CreateUserRequest {
  name: string
  employeeId: string
  deptId: string
  position: string
  email: string
  phone: string
  status: UserStatus
}

export interface UpdateUserRequest extends Partial<CreateUserRequest> {
  id: string
}

// ─── RBAC 角色 ────────────────────────────────────────────────────────────────

export interface RoleDef {
  id: string
  key: string
  name: string
  description: string
  isBuiltin: boolean
  userCount: number
  status: 'active' | 'inactive'
  color: string
  badgeColor: string
}

export interface DataResource {
  id: string
  label: string
  desc: string
  icon: string
}

export type DataScope = 'all' | 'dept_and_children' | 'dept' | 'self' | 'custom' | 'none'

export interface DataScopeOption {
  value: DataScope
  label: string
  desc: string
  color: string
}

export const DATA_SCOPE_OPTIONS: DataScopeOption[] = [
  { value: 'all', label: '全部数据', desc: '查看系统内所有数据记录', color: 'border-red-500/40 bg-red-500/15 text-red-300' },
  { value: 'dept_and_children', label: '本部门及以下', desc: '查看本部门及所有下级部门数据', color: 'border-amber-500/40 bg-amber-500/15 text-amber-300' },
  { value: 'dept', label: '本部门', desc: '仅查看本部门数据', color: 'border-blue-500/40 bg-blue-500/15 text-blue-300' },
  { value: 'self', label: '仅本人', desc: '仅查看本人创建或负责的记录', color: 'border-emerald-500/40 bg-emerald-500/15 text-emerald-300' },
  { value: 'custom', label: '自定义部门', desc: '手动选择若干个可见部门', color: 'border-violet-500/40 bg-violet-500/15 text-violet-300' },
  { value: 'none', label: '无权限', desc: '不授予该资源的任何数据访问', color: 'border-slate-500/40 bg-slate-500/15 text-slate-400' },
]

// ─── 权限资源（RBAC + 菜单配置共用）────────────────────────────────────────────

export type PermType = 'catalog' | 'menu' | 'button'
export type PermStatus = 'active' | 'hidden' | 'disabled'
export type BtnVariant = 'primary' | 'default' | 'danger' | 'ghost'

export interface PermResource {
  id: string
  parentId: string | null
  type: PermType
  label: string
  permKey: string
  path?: string
  icon: string
  sortOrder: number
  status: PermStatus
  isBuiltin: boolean
  description?: string
  btnVariant?: BtnVariant
  danger?: boolean
}

export const PERM_TYPE_CONFIG: Record<PermType, { label: string; color: string; bg: string }> = {
  catalog: { label: '目录', color: 'text-amber-300', bg: 'bg-amber-500/15 border-amber-500/30' },
  menu: { label: '菜单', color: 'text-sky-300', bg: 'bg-sky-500/15 border-sky-500/30' },
  button: { label: '按钮', color: 'text-violet-300', bg: 'bg-violet-500/15 border-violet-500/30' },
}

export const PERM_STATUS_CONFIG: Record<PermStatus, { label: string; color: string }> = {
  active: { label: '启用', color: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30' },
  hidden: { label: '隐藏', color: 'bg-slate-500/15 text-slate-300 border-slate-500/30' },
  disabled: { label: '停用', color: 'bg-rose-500/15 text-rose-300 border-rose-500/30' },
}

export const BTN_VARIANT_LABEL: Record<BtnVariant, { label: string; color: string }> = {
  primary: { label: '主要', color: 'bg-blue-500/15 text-blue-300 border-blue-500/30' },
  default: { label: '默认', color: 'bg-slate-500/15 text-slate-300 border-slate-500/30' },
  danger: { label: '危险', color: 'bg-rose-500/15 text-rose-300 border-rose-500/30' },
  ghost: { label: '幽灵', color: 'bg-zinc-500/15 text-zinc-300 border-zinc-500/30' },
}

// ─── 机构部门 ─────────────────────────────────────────────────────────────────

export type OrgType = 'group' | 'center' | 'dept' | 'team'

export type OrgStatus = 'active' | 'inactive'

export interface OrgNode {
  id: string
  name: string
  code: string
  parentId: string | null
  type: OrgType
  level: number
  leader: string
  phone: string
  email: string
  address: string
  desc: string
  employeeCount: number
  sort: number
  createdAt: string
  status: OrgStatus
}

export interface OrgTypeConfig {
  label: string
  icon: string
  cls: string
}

export const ORG_TYPE_CONFIG: Record<OrgType, OrgTypeConfig> = {
  group:  { label: '集团/公司',  icon: 'Building2', cls: 'badge-blue' },
  center: { label: '中心/事业部', icon: 'Briefcase', cls: 'badge-purple' },
  dept:   { label: '部门',       icon: 'Layers',    cls: 'badge-cyan' },
  team:   { label: '小组/团队',  icon: 'Users',     cls: 'badge-emerald' },
}

// ─── 角色覆盖 ─────────────────────────────────────────────────────────────────

export interface RoleCoverage {
  roleKey: string
  roleName: string
  hasPermission: boolean
}
