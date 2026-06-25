/** 技能简要信息（嵌入在 Agent 中） */
export interface SkillBrief {
  id: string
  name: string
  description: string
  category: string
  icon: string
  enabled: boolean
}

/** 定时任务简要信息 */
export interface CronJobBrief {
  id: string
  agentId: string
  name: string
  description: string
  cronExpression: string
  cronLabel: string
  status: string
  targetType: string
  target: string
  lastRun: string | null
  nextRun: string | null
  tags: string[]
  createdAt: string
  updatedAt: string
}

/** 记忆作用域：agent / user / mixture / org */
export type MemoryScope = 'agent' | 'user' | 'mixture' | 'org'

/** 文件简要信息（按作用域分组返回） */
export interface FileBrief {
  filename: string
  scope: MemoryScope
  description: string
  readOnly: boolean
}

/** 代理实体 */
export interface Agent {
  id: string
  name: string
  type: 'main' | 'sub'
  status: 'active' | 'inactive' | 'error'
  tools: string[]
  skills: SkillBrief[]
  systemPrompt: string
  files: string[]
  /** 按作用域分组的文件列表（与 files 同步，由后端返回） */
  filesByScope?: Record<MemoryScope, FileBrief[]>
  cronJobs: CronJobBrief[]
  subAgents?: string[]
  parentId?: string
  providerId?: string
  modelId?: string
  description?: string
  lastActive?: string
  callCount?: number
  undeletable?: boolean
}

/** 创建代理请求 */
export interface AgentCreateRequest {
  name: string
  description?: string
  systemPrompt?: string
  parentId?: string
  providerId?: string
  modelId?: string
}

/** 更新代理请求 */
export interface AgentUpdateRequest {
  name: string
  description?: string
  systemPrompt?: string
  providerId?: string
  modelId?: string
}

/** 文件内容 */
export interface AgentFileContent {
  filename: string
  content: string
  description: string
  scope: MemoryScope
  readOnly: boolean
  createdAt: string
  updatedAt: string
}

/** 配置项类型 (技能不再走通用 config 流程) */
export type ConfigType = 'tool' | 'prompt' | 'subagent' | 'file'

/** 状态中文标签 */
export const STATUS_LABELS: Record<string, string> = {
  active: '运行中',
  inactive: '已停止',
  error: '错误',
}

/** 配置类型映射（颜色 + 标签） */
export const CONFIG_TYPE_MAP: Record<
  ConfigType,
  { label: string; color: string; bgClass: string }
> = {
  tool: { label: '工具', color: '#3b82f6', bgClass: 'config--blue' },
  prompt: { label: '提示词', color: '#22c55e', bgClass: 'config--green' },
  subagent: { label: '子智能体', color: '#f97316', bgClass: 'config--orange' },
  file: { label: '文件', color: '#eab308', bgClass: 'config--yellow' },
}

/** 记忆作用域样式映射（颜色 + 标签 + CSS class） */
export const SCOPE_STYLE_MAP: Record<
  MemoryScope,
  { label: string; shortLabel: string; color: string; bgClass: string }
> = {
  agent: {
    label: '智能体级记忆',
    shortLabel: '智能体级',
    color: '#eab308',
    bgClass: 'scope--yellow',
  },
  user: {
    label: '用户级记忆',
    shortLabel: '用户级',
    color: '#3b82f6',
    bgClass: 'scope--blue',
  },
  mixture: {
    label: '混合级记忆',
    shortLabel: '混合级',
    color: '#a855f7',
    bgClass: 'scope--purple',
  },
  org: {
    label: '组织级记忆',
    shortLabel: '组织级（只读）',
    color: '#6b7280',
    bgClass: 'scope--gray',
  },
}

/** 作用域展示顺序（org 嵌套在 agent 区块内） */
export const SCOPE_DISPLAY_ORDER: MemoryScope[] = ['agent', 'org', 'user', 'mixture']
