/** 技能实体 */
export interface Skill {
  id: string
  name: string
  description: string
  icon: string
  category: string
  prompt: string
  enabled: boolean
  is_builtin: boolean
  valid: boolean
  source: string
  license: string
  user_id: string | null
  created_at: string
  updated_at: string
}

/** 创建/更新技能请求 */
export interface SkillCreateRequest {
  name: string
  description?: string
  icon?: string
  category?: string
  prompt?: string
}

/** 分类中文映射 */
export const CATEGORY_LABELS: Record<string, string> = {
  search: '搜索',
  code: '代码',
  creative: '创意',
  analysis: '分析',
  tools: '工具',
  custom: '自定义',
}

/** 分类筛选选项 */
export const CATEGORY_FILTERS = [
  { key: '', label: '全部' },
  { key: 'search', label: '搜索' },
  { key: 'code', label: '代码' },
  { key: 'creative', label: '创意' },
  { key: 'analysis', label: '分析' },
  { key: 'tools', label: '工具' },
]
