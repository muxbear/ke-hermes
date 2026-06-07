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
