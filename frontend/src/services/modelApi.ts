/**
 * Model API — 模型管理接口（Mock 实现，后端就绪后替换）
 */
import type { Provider, AIModel, ModelType, ModelStatus } from '@/types/model'

/* ------------------------------------------------------------------ */
/*  Mock 数据                                                          */
/* ------------------------------------------------------------------ */

let providers: Provider[] = [
  {
    id: 'openai', name: 'OpenAI', logo: '🤖', status: 'connected',
    apiBase: 'https://api.openai.com/v1', apiKey: 'sk-proj-••••••••••••••••XyZ9',
    description: '全球领先的 AI 研究公司，提供 GPT 系列语言模型、DALL-E 图像生成及 Whisper 语音识别。',
    website: 'https://openai.com',
    models: [
      { id: 'gpt-4o', name: 'gpt-4o', displayName: 'GPT-4o', type: 'llm', status: 'active', contextWindow: 128000, usedByAgents: ['main-alpha', 'sub-analyst', 'sub-writer'], callCount: 4821, description: '最新旗舰多模态模型，支持文本与视觉输入。', releaseDate: '2024-05', params: [{ key: 'temperature', label: 'Temperature', value: 0.7, min: 0, max: 2, step: 0.1, type: 'number' }, { key: 'max_tokens', label: 'Max Tokens', value: 4096, min: 1, max: 16384, step: 1, type: 'number' }, { key: 'top_p', label: 'Top P', value: 1, min: 0, max: 1, step: 0.01, type: 'number' }] },
      { id: 'gpt-4o-mini', name: 'gpt-4o-mini', displayName: 'GPT-4o Mini', type: 'llm', status: 'active', contextWindow: 128000, usedByAgents: ['sub-summary'], callCount: 2310, description: '轻量级高效版本，成本低，适合高频调用场景。', releaseDate: '2024-07', params: [{ key: 'temperature', label: 'Temperature', value: 0.7, min: 0, max: 2, step: 0.1, type: 'number' }, { key: 'max_tokens', label: 'Max Tokens', value: 2048, min: 1, max: 8192, step: 1, type: 'number' }] },
      { id: 'dall-e-3', name: 'dall-e-3', displayName: 'DALL-E 3', type: 'image-gen', status: 'active', usedByAgents: ['main-alpha'], callCount: 218, description: '高质量文本到图像生成模型。', releaseDate: '2023-10', params: [{ key: 'size', label: '图像尺寸', value: '1024x1024', type: 'select', options: ['1024x1024', '1792x1024', '1024x1792'] }, { key: 'quality', label: '图像质量', value: 'standard', type: 'select', options: ['standard', 'hd'] }] },
      { id: 'text-embedding-3-large', name: 'text-embedding-3-large', displayName: 'Embedding 3 Large', type: 'embedding', status: 'active', contextWindow: 8191, usedByAgents: ['sub-analyst'], callCount: 9842, description: '高维文本向量化模型，用于语义搜索与知识库索引。', releaseDate: '2024-01', params: [{ key: 'dimensions', label: '向量维度', value: 3072, min: 256, max: 3072, step: 1, type: 'number' }] },
      { id: 'whisper-1', name: 'whisper-1', displayName: 'Whisper', type: 'audio', status: 'active', usedByAgents: [], callCount: 145, description: '多语言语音识别转录模型。', releaseDate: '2022-09', params: [{ key: 'language', label: '语言', value: 'zh', type: 'text' }] },
    ],
  },
  {
    id: 'anthropic', name: 'Anthropic', logo: '⚡', status: 'connected',
    apiBase: 'https://api.anthropic.com/v1', apiKey: 'sk-ant-••••••••••••••••Api1',
    description: '专注 AI 安全的研究公司，Claude 系列模型以强大的推理和长文本处理著称。',
    website: 'https://anthropic.com',
    models: [
      { id: 'claude-3-5-sonnet', name: 'claude-3-5-sonnet-20241022', displayName: 'Claude 3.5 Sonnet', type: 'llm', status: 'active', contextWindow: 200000, usedByAgents: ['main-beta', 'sub-code'], callCount: 3284, description: '最强 Claude 模型，卓越编码与推理能力。', releaseDate: '2024-10', params: [{ key: 'temperature', label: 'Temperature', value: 0.7, min: 0, max: 1, step: 0.01, type: 'number' }, { key: 'max_tokens', label: 'Max Tokens', value: 8192, min: 1, max: 8192, step: 1, type: 'number' }] },
      { id: 'claude-3-5-haiku', name: 'claude-3-5-haiku-20241022', displayName: 'Claude 3.5 Haiku', type: 'llm', status: 'active', contextWindow: 200000, usedByAgents: ['sub-summary'], callCount: 1892, description: '速度最快的 Claude 模型，兼顾性能与成本。', releaseDate: '2024-11', params: [{ key: 'temperature', label: 'Temperature', value: 0.5, min: 0, max: 1, step: 0.01, type: 'number' }, { key: 'max_tokens', label: 'Max Tokens', value: 4096, min: 1, max: 8192, step: 1, type: 'number' }] },
      { id: 'claude-3-opus', name: 'claude-3-opus-20240229', displayName: 'Claude 3 Opus', type: 'llm', status: 'deprecated', contextWindow: 200000, usedByAgents: [], callCount: 421, description: '上一代旗舰模型，已被 3.5 系列取代。', releaseDate: '2024-02', params: [{ key: 'temperature', label: 'Temperature', value: 0.7, min: 0, max: 1, step: 0.01, type: 'number' }] },
    ],
  },
  {
    id: 'google', name: 'Google', logo: '🌐', status: 'connected',
    apiBase: 'https://generativelanguage.googleapis.com/v1beta', apiKey: 'AIza••••••••••••••••Key2',
    description: 'Google DeepMind 推出的 Gemini 系列，支持超长上下文与多模态能力。',
    website: 'https://ai.google.dev',
    models: [
      { id: 'gemini-1.5-pro', name: 'gemini-1.5-pro', displayName: 'Gemini 1.5 Pro', type: 'llm', status: 'active', contextWindow: 2000000, usedByAgents: ['main-alpha'], callCount: 1543, description: '200 万 token 超长上下文旗舰模型。', releaseDate: '2024-02', params: [{ key: 'temperature', label: 'Temperature', value: 1, min: 0, max: 2, step: 0.1, type: 'number' }, { key: 'max_tokens', label: 'Max Output Tokens', value: 8192, min: 1, max: 8192, step: 1, type: 'number' }] },
      { id: 'gemini-2.0-flash', name: 'gemini-2.0-flash', displayName: 'Gemini 2.0 Flash', type: 'llm', status: 'beta', contextWindow: 1000000, usedByAgents: [], callCount: 234, description: '新一代高速多模态模型，支持实时流式输出。', releaseDate: '2024-12', params: [{ key: 'temperature', label: 'Temperature', value: 1, min: 0, max: 2, step: 0.1, type: 'number' }] },
      { id: 'imagen-3', name: 'imagen-3', displayName: 'Imagen 3', type: 'image-gen', status: 'active', usedByAgents: [], callCount: 89, description: '高保真文生图模型，支持照片级写实风格。', releaseDate: '2024-08', params: [{ key: 'aspect_ratio', label: '宽高比', value: '1:1', type: 'select', options: ['1:1', '16:9', '9:16', '4:3'] }] },
      { id: 'text-embedding-004', name: 'text-embedding-004', displayName: 'Text Embedding 004', type: 'embedding', status: 'active', contextWindow: 2048, usedByAgents: ['sub-analyst'], callCount: 3201, description: 'Google 最新文本向量化模型。', releaseDate: '2024-04', params: [{ key: 'output_dimensionality', label: '输出维度', value: 768, type: 'number' }] },
    ],
  },
  {
    id: 'mistral', name: 'Mistral AI', logo: '💨', status: 'connected',
    apiBase: 'https://api.mistral.ai/v1', apiKey: '••••••••••••••••mist',
    description: '欧洲领先 AI 公司，以高效开源模型著称，提供强大的代码与推理能力。',
    website: 'https://mistral.ai',
    models: [
      { id: 'mistral-large-2', name: 'mistral-large-2407', displayName: 'Mistral Large 2', type: 'llm', status: 'active', contextWindow: 128000, usedByAgents: ['sub-code'], callCount: 892, description: 'Mistral 旗舰模型，顶级代码生成与推理。', releaseDate: '2024-07', params: [{ key: 'temperature', label: 'Temperature', value: 0.7, min: 0, max: 1, step: 0.01, type: 'number' }, { key: 'max_tokens', label: 'Max Tokens', value: 4096, min: 1, max: 131072, step: 1, type: 'number' }] },
      { id: 'mistral-small', name: 'mistral-small-2409', displayName: 'Mistral Small', type: 'llm', status: 'active', contextWindow: 32000, usedByAgents: [], callCount: 412, description: '轻量高效，适合简单对话与分类任务。', releaseDate: '2024-09', params: [{ key: 'temperature', label: 'Temperature', value: 0.7, min: 0, max: 1, step: 0.01, type: 'number' }] },
      { id: 'mistral-embed', name: 'mistral-embed', displayName: 'Mistral Embed', type: 'embedding', status: 'active', contextWindow: 8192, usedByAgents: [], callCount: 1230, description: '高性能文本向量化，低延迟批量处理。', releaseDate: '2023-11', params: [] },
    ],
  },
  {
    id: 'ollama', name: 'Ollama', logo: '🦙', status: 'connected',
    apiBase: 'http://localhost:11434/v1', apiKey: '（本地服务，无需密钥）',
    description: '本地大模型运行框架，支持离线部署 Llama、Qwen、DeepSeek 等开源模型。',
    website: 'https://ollama.com',
    models: [
      { id: 'llama3.1-8b', name: 'llama3.1:8b', displayName: 'Llama 3.1 8B', type: 'llm', status: 'active', contextWindow: 131072, usedByAgents: ['sub-local'], callCount: 1821, description: 'Meta 开源旗舰小参数量模型，性能优秀。', releaseDate: '2024-07', params: [{ key: 'temperature', label: 'Temperature', value: 0.8, min: 0, max: 2, step: 0.1, type: 'number' }, { key: 'num_ctx', label: '上下文长度', value: 4096, min: 512, max: 131072, step: 512, type: 'number' }] },
      { id: 'qwen2.5-7b', name: 'qwen2.5:7b', displayName: 'Qwen 2.5 7B', type: 'llm', status: 'active', contextWindow: 128000, usedByAgents: [], callCount: 943, description: '阿里云通义千问开源版，中文能力突出。', releaseDate: '2024-09', params: [{ key: 'temperature', label: 'Temperature', value: 0.7, min: 0, max: 2, step: 0.1, type: 'number' }] },
      { id: 'deepseek-r1-7b', name: 'deepseek-r1:7b', displayName: 'DeepSeek-R1 7B', type: 'llm', status: 'active', contextWindow: 65536, usedByAgents: ['sub-code'], callCount: 672, description: '强推理链思考模型，数学与代码表现突出。', releaseDate: '2025-01', params: [{ key: 'temperature', label: 'Temperature', value: 0.6, min: 0, max: 2, step: 0.1, type: 'number' }] },
    ],
  },
  {
    id: 'bytedance', name: '字节跳动', logo: '🎯', status: 'error',
    apiBase: 'https://ark.cn-beijing.volces.com/api/v3', apiKey: '••••••••••••••••byte',
    description: '字节跳动火山引擎方舟平台，提供豆包系列大语言模型及多模态能力。',
    website: 'https://www.volcengine.com',
    models: [
      { id: 'doubao-pro-32k', name: 'doubao-pro-32k', displayName: '豆包 Pro 32K', type: 'llm', status: 'active', contextWindow: 32000, usedByAgents: [], callCount: 0, description: '豆包旗舰对话模型，性价比高。', releaseDate: '2024-06', params: [{ key: 'temperature', label: 'Temperature', value: 0.7, min: 0, max: 1, step: 0.01, type: 'number' }] },
    ],
  },
]

/* ------------------------------------------------------------------ */
/*  辅助函数                                                            */
/* ------------------------------------------------------------------ */

function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}

/* ------------------------------------------------------------------ */
/*  API 函数                                                           */
/* ------------------------------------------------------------------ */

export async function fetchProviders(): Promise<Provider[]> {
  return deepClone(providers)
}

export async function saveProvider(data: Provider): Promise<Provider> {
  const idx = providers.findIndex((p) => p.id === data.id)
  if (idx >= 0) {
    providers[idx] = deepClone(data)
    return deepClone(providers[idx])
  }
  const created = deepClone(data)
  providers.push(created)
  return deepClone(created)
}

export async function deleteProvider(id: string): Promise<void> {
  providers = providers.filter((p) => p.id !== id)
}

export async function saveModel(providerId: string, data: AIModel): Promise<Provider> {
  const p = providers.find((x) => x.id === providerId)
  if (!p) throw new Error('提供商不存在')
  const idx = p.models.findIndex((m) => m.id === data.id)
  if (idx >= 0) {
    p.models[idx] = deepClone(data)
  } else {
    p.models.push(deepClone(data))
  }
  return deepClone(p)
}

export async function deleteModel(providerId: string, modelId: string): Promise<Provider> {
  const p = providers.find((x) => x.id === providerId)
  if (!p) throw new Error('提供商不存在')
  p.models = p.models.filter((m) => m.id !== modelId)
  return deepClone(p)
}
