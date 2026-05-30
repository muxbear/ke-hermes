/** 模型类型 */
export type ModelType = 'llm' | 'vision' | 'audio' | 'video' | 'embedding' | 'image-gen' | 'speech'

/** 模型状态 */
export type ModelStatus = 'active' | 'beta' | 'deprecated'

/** 提供商连接状态 */
export type ProviderStatus = 'connected' | 'error' | 'unconfigured'

/** 模型参数 */
export interface ModelParam {
  key: string
  label: string
  value: number | string
  min?: number
  max?: number
  step?: number
  type: 'number' | 'text' | 'select'
  options?: string[]
}

/** AI 模型实体 */
export interface AIModel {
  id: string
  name: string
  displayName: string
  type: ModelType
  status: ModelStatus
  contextWindow?: number
  usedByAgents: string[]
  callCount: number
  params: ModelParam[]
  description: string
  releaseDate?: string
}

/** 模型提供商 */
export interface Provider {
  id: string
  name: string
  logo: string
  status: ProviderStatus
  apiBase: string
  apiKey: string
  models: AIModel[]
  description: string
  website: string
}

/** 模型类型元数据 */
export const MODEL_TYPE_META: Record<ModelType, { label: string; color: string; bg: string; border: string; emoji: string }> = {
  llm:        { label: '大语言模型', color: '#a5b4fc', bg: 'rgba(99,102,241,0.1)',  border: 'rgba(99,102,241,0.25)',  emoji: '💬' },
  vision:     { label: '视觉模型',   color: '#c4b5fd', bg: 'rgba(139,92,246,0.1)',  border: 'rgba(139,92,246,0.25)',  emoji: '👁️' },
  audio:      { label: '音频模型',   color: '#6ee7b7', bg: 'rgba(16,185,129,0.1)',  border: 'rgba(16,185,129,0.25)',  emoji: '🎵' },
  video:      { label: '视频模型',   color: '#f472b6', bg: 'rgba(236,72,153,0.1)',  border: 'rgba(236,72,153,0.25)',  emoji: '🎬' },
  embedding:  { label: '向量模型',   color: '#67e8f9', bg: 'rgba(6,182,212,0.1)',   border: 'rgba(6,182,212,0.25)',   emoji: '🔢' },
  'image-gen':{ label: '图像生成',   color: '#fbbf24', bg: 'rgba(245,158,11,0.1)',  border: 'rgba(245,158,11,0.25)',  emoji: '🎨' },
  speech:     { label: '语音合成',   color: '#5eead4', bg: 'rgba(20,184,166,0.1)',  border: 'rgba(20,184,166,0.25)',  emoji: '🗣️' },
}

/** 提供商状态元数据 */
export const PROVIDER_STATUS_META: Record<ProviderStatus, { label: string; color: string; dot: string }> = {
  connected:    { label: '已连接',   color: '#6ee7b7', dot: '#10B981' },
  error:        { label: '连接异常', color: '#f87171', dot: '#EF4444' },
  unconfigured: { label: '未配置',   color: '#6b7280', dot: '#4B5563' },
}

/** 模型状态元数据 */
export const MODEL_STATUS_META: Record<ModelStatus, { label: string; color: string; bg: string }> = {
  active:     { label: '正常',   color: '#6ee7b7', bg: 'rgba(16,185,129,0.1) border: 1px solid rgba(16,185,129,0.2)' },
  beta:       { label: 'Beta',   color: '#fbbf24', bg: 'rgba(245,158,11,0.1) border: 1px solid rgba(245,158,11,0.2)' },
  deprecated: { label: '已弃用', color: '#6b7280', bg: 'rgba(75,85,99,0.2) border: 1px solid rgba(75,85,99,0.3)' },
}
