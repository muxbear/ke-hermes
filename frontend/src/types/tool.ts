/** 工具状态 */
export type ToolStatus = 'enabled' | 'disabled' | 'unavailable'

/** 工具来源 */
export type ToolSource = 'builtin' | 'third-party'

/** 工具功能分类 */
export type ToolCategory =
  | 'code'
  | 'network'
  | 'message'
  | 'file'
  | 'data'
  | 'ai'
  | 'system'
  | 'other'

/** 工具参数定义 */
export interface ToolParam {
  key: string
  label: string
  required: boolean
  type: string
}

/** 工具实体 */
export interface Tool {
  id: string
  name: string
  displayName: string
  description: string
  category: ToolCategory
  source: ToolSource
  status: ToolStatus
  version: string
  author: string
  usedByAgents: string[]
  tags: string[]
  params?: ToolParam[]
  created_at: string
  updated_at: string
}

/** 创建/更新工具请求 */
export interface ToolCreateRequest {
  name: string
  displayName: string
  description?: string
  category?: ToolCategory
  status?: ToolStatus
  version?: string
  tags?: string[]
  params?: ToolParam[]
}

/** 分类元数据 */
export interface CategoryMeta {
  label: string
  icon: string
  color: string
  bg: string
  border: string
}

/** 功能分类映射 */
export const CATEGORY_META: Record<ToolCategory, CategoryMeta> = {
  code: { label: '编码工具', icon: 'Code2', color: 'var(--color-tool-blue)', bg: 'rgba(59,130,246,0.08)', border: 'rgba(59,130,246,0.2)' },
  network: { label: '网络工具', icon: 'Globe', color: 'var(--color-tool-cyan)', bg: 'rgba(6,182,212,0.08)', border: 'rgba(6,182,212,0.2)' },
  message: { label: '消息工具', icon: 'MessageSquare', color: 'var(--color-tool-green)', bg: 'rgba(34,197,94,0.08)', border: 'rgba(34,197,94,0.2)' },
  file: { label: '文件工具', icon: 'FileText', color: 'var(--color-tool-amber)', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)' },
  data: { label: '数据工具', icon: 'Database', color: 'var(--color-tool-purple)', bg: 'rgba(168,85,247,0.08)', border: 'rgba(168,85,247,0.2)' },
  ai: { label: 'AI 工具', icon: 'Sparkles', color: 'var(--color-tool-pink)', bg: 'rgba(236,72,153,0.08)', border: 'rgba(236,72,153,0.2)' },
  system: { label: '系统工具', icon: 'Cpu', color: 'var(--color-tool-indigo)', bg: 'rgba(99,102,241,0.08)', border: 'rgba(99,102,241,0.2)' },
  other: { label: '其他', icon: 'Wrench', color: 'var(--color-tool-gray)', bg: 'rgba(148,163,184,0.08)', border: 'rgba(148,163,184,0.2)' },
}

/** 状态元数据 */
export interface StatusMeta {
  label: string
  color: string
  bg: string
  border: string
  icon: string
}

export const STATUS_META: Record<ToolStatus, StatusMeta> = {
  enabled: { label: '已启用', color: 'var(--color-tool-emerald)', bg: 'rgba(16,185,129,0.08)', border: 'rgba(16,185,129,0.2)', icon: 'CheckCircle2' },
  disabled: { label: '已禁用', color: 'var(--color-tool-amber)', bg: 'rgba(245,158,11,0.08)', border: 'rgba(245,158,11,0.2)', icon: 'PauseCircle' },
  unavailable: { label: '不可用', color: 'var(--color-tool-gray)', bg: 'rgba(148,163,184,0.06)', border: 'rgba(148,163,184,0.15)', icon: 'AlertCircle' },
}

/** 来源标签 */
export const SOURCE_LABELS: Record<ToolSource, string> = {
  builtin: '内置',
  'third-party': '第三方',
}

/** 工具列表响应 */
export interface ToolListResponse {
  items: Tool[]
  total: number
  page: number
  page_size: number
}
