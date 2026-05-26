/** MCP 工具实体 */
export interface McpTool {
  id: string
  name: string
  description: string
  icon: string
  author: string
  version: string
  license: string
  repository: string
  installs: number
  rating: number
  category: string
  tags: string[]
  features: string[]
  official: boolean
  installed: boolean
  config_schema: McpConfigField[]
  created_at: string
  updated_at: string
}

/** MCP 配置字段 */
export interface McpConfigField {
  name: string
  label: string
  type: 'string' | 'number' | 'boolean' | 'select'
  required: boolean
  default?: string | number | boolean
  options?: string[]
  description?: string
}

/** MCP 分类 */
export const MCP_CATEGORY_LABELS: Record<string, string> = {
  code_execution: '代码执行',
  search: '搜索',
  data_analysis: '数据分析',
  file_management: '文件管理',
  notification: '通知',
  database: '数据库',
  dev_tools: '开发工具',
  collaboration: '协作',
  container: '容器',
  custom: '自定义',
}

/** 分类筛选选项 */
export const MCP_CATEGORY_FILTERS = [
  { key: '', label: '全部' },
  { key: 'code_execution', label: '代码执行' },
  { key: 'search', label: '搜索' },
  { key: 'data_analysis', label: '数据分析' },
  { key: 'file_management', label: '文件管理' },
  { key: 'notification', label: '通知' },
  { key: 'database', label: '数据库' },
  { key: 'dev_tools', label: '开发工具' },
]

/** 安装 MCP 请求 */
export interface InstallMcpRequest {
  mcp_id: string
  config?: Record<string, string | number | boolean>
}
