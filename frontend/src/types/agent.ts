/** 代理实体 */
export interface Agent {
  id: string
  name: string
  type: 'main' | 'sub'
  status: 'active' | 'inactive' | 'error'
  tools: string[]
  skills: string[]
  prompts: string[]
  files: string[]
  subAgents?: string[]
  parentId?: string
  description?: string
  lastActive?: string
  callCount?: number
  undeletable?: boolean
}

/** 创建代理请求 */
export interface AgentCreateRequest {
  name: string
  description?: string
}

/** 配置项类型 */
export type ConfigType = 'tool' | 'skill' | 'prompt' | 'subagent' | 'file'

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
  skill: { label: '技能', color: '#8b5cf6', bgClass: 'config--purple' },
  prompt: { label: '提示词', color: '#22c55e', bgClass: 'config--green' },
  subagent: { label: '子代理', color: '#f97316', bgClass: 'config--orange' },
  file: { label: '文件', color: '#eab308', bgClass: 'config--yellow' },
}
