import instance from './request'
import type { Tool, ToolCreateRequest, ToolListResponse } from '@/types/tool'

// ─── Mock data ────────────────────────────────────────────────────────────────

const MOCK_TOOLS: Tool[] = [
  // Built-in
  { id: 'b-execute-code', name: 'execute_code', displayName: '代码执行', description: '在沙箱环境中执行 Python / JavaScript 代码，返回标准输出与错误信息。', category: 'code', source: 'builtin', status: 'enabled', version: '1.3.0', author: 'ke-hermes', usedByAgents: ['main-alpha', 'sub-code'], tags: ['python', 'js', 'sandbox'], params: [{ key: 'language', label: '编程语言', required: true, type: 'string' }, { key: 'timeout', label: '超时(s)', required: false, type: 'number' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'b-shell-cmd', name: 'shell_command', displayName: 'Shell 命令', description: '在受限 Shell 环境中执行系统命令，支持管道和重定向。', category: 'code', source: 'builtin', status: 'enabled', version: '1.1.0', author: 'ke-hermes', usedByAgents: ['sub-code'], tags: ['shell', 'bash', 'cli'], params: [{ key: 'command', label: '命令', required: true, type: 'string' }, { key: 'cwd', label: '工作目录', required: false, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'b-http-request', name: 'http_request', displayName: 'HTTP 请求', description: '发送 HTTP/HTTPS 请求，支持 GET / POST / PUT / DELETE，自定义 Header 与 Body。', category: 'network', source: 'builtin', status: 'enabled', version: '2.0.1', author: 'ke-hermes', usedByAgents: ['main-alpha', 'main-beta'], tags: ['http', 'api', 'rest'], params: [{ key: 'url', label: 'URL', required: true, type: 'string' }, { key: 'method', label: '方法', required: true, type: 'string' }, { key: 'headers', label: 'Header', required: false, type: 'object' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'b-web-search', name: 'web_search', displayName: '网页搜索', description: '调用搜索引擎对互联网进行实时检索，返回摘要及来源 URL。', category: 'network', source: 'builtin', status: 'enabled', version: '1.5.2', author: 'ke-hermes', usedByAgents: ['main-alpha', 'sub-analyst'], tags: ['search', 'google', 'bing'], params: [{ key: 'query', label: '搜索词', required: true, type: 'string' }, { key: 'limit', label: '结果数', required: false, type: 'number' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'b-web-scraper', name: 'web_scraper', displayName: '网页抓取', description: '抓取指定 URL 的页面内容，支持提取正文、链接与结构化数据。', category: 'network', source: 'builtin', status: 'enabled', version: '1.2.0', author: 'ke-hermes', usedByAgents: ['sub-analyst'], tags: ['scrape', 'html', 'extract'], params: [{ key: 'url', label: '目标 URL', required: true, type: 'string' }, { key: 'selector', label: 'CSS 选择器', required: false, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'b-read-file', name: 'read_file', displayName: '文件读取', description: '读取本地或远程文件内容，支持文本、JSON、CSV、PDF 等格式。', category: 'file', source: 'builtin', status: 'enabled', version: '1.0.4', author: 'ke-hermes', usedByAgents: ['sub-analyst'], tags: ['file', 'read', 'pdf'], params: [{ key: 'path', label: '文件路径', required: true, type: 'string' }, { key: 'encoding', label: '编码', required: false, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'b-write-file', name: 'write_file', displayName: '文件写入', description: '将内容写入文件，支持覆盖、追加模式，自动创建父目录。', category: 'file', source: 'builtin', status: 'enabled', version: '1.0.4', author: 'ke-hermes', usedByAgents: [], tags: ['file', 'write'], params: [{ key: 'path', label: '文件路径', required: true, type: 'string' }, { key: 'content', label: '内容', required: true, type: 'string' }, { key: 'mode', label: '模式', required: false, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'b-sql-query', name: 'sql_query', displayName: 'SQL 查询', description: '连接数据库执行 SQL 语句，支持 MySQL、PostgreSQL、SQLite。', category: 'data', source: 'builtin', status: 'enabled', version: '1.1.0', author: 'ke-hermes', usedByAgents: ['sub-analyst'], tags: ['sql', 'database', 'query'], params: [{ key: 'dsn', label: '连接串', required: true, type: 'string' }, { key: 'query', label: 'SQL', required: true, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'b-get-datetime', name: 'get_datetime', displayName: '当前时间', description: '获取当前日期时间，支持指定时区与格式化输出。', category: 'system', source: 'builtin', status: 'enabled', version: '1.0.0', author: 'ke-hermes', usedByAgents: ['main-alpha'], tags: ['time', 'date', 'timezone'], params: [{ key: 'timezone', label: '时区', required: false, type: 'string' }, { key: 'format', label: '格式串', required: false, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'b-image-gen', name: 'image_generate', displayName: '图像生成', description: '根据文本提示生成图像，支持 DALL-E、Stable Diffusion 后端切换。', category: 'ai', source: 'builtin', status: 'disabled', version: '2.0.0', author: 'ke-hermes', usedByAgents: [], tags: ['image', 'ai', 'dalle'], params: [{ key: 'prompt', label: '提示词', required: true, type: 'string' }, { key: 'size', label: '尺寸', required: false, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'b-text-embed', name: 'text_embedding', displayName: '文本向量化', description: '将文本转化为高维向量，用于语义搜索与相似度计算。', category: 'ai', source: 'builtin', status: 'enabled', version: '1.2.0', author: 'ke-hermes', usedByAgents: ['sub-analyst'], tags: ['embedding', 'vector', 'nlp'], params: [{ key: 'text', label: '文本', required: true, type: 'string' }, { key: 'model', label: '模型 ID', required: false, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  // Third-party
  { id: 'tp-send-email', name: 'send_email', displayName: '邮件发送', description: '通过 SMTP 发送电子邮件，支持附件、HTML 正文与抄送。', category: 'message', source: 'third-party', status: 'enabled', version: '1.0.2', author: '社区', usedByAgents: ['main-alpha'], tags: ['email', 'smtp', 'notification'], params: [{ key: 'to', label: '收件人', required: true, type: 'string' }, { key: 'subject', label: '主题', required: true, type: 'string' }, { key: 'body', label: '正文', required: true, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'tp-slack', name: 'slack_message', displayName: 'Slack 消息', description: '向指定 Slack 频道或用户发送消息，支持 Block Kit 富文本格式。', category: 'message', source: 'third-party', status: 'enabled', version: '2.1.0', author: '社区', usedByAgents: ['main-alpha'], tags: ['slack', 'im', 'notification'], params: [{ key: 'channel', label: '频道', required: true, type: 'string' }, { key: 'text', label: '消息', required: true, type: 'string' }, { key: 'token', label: 'Token', required: true, type: 'secret' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'tp-github', name: 'github_api', displayName: 'GitHub API', description: '调用 GitHub REST API，支持仓库操作、Issue 管理、PR 评审等。', category: 'code', source: 'third-party', status: 'enabled', version: '3.0.1', author: '社区', usedByAgents: ['sub-code'], tags: ['github', 'git', 'devops'], params: [{ key: 'token', label: 'Access Token', required: true, type: 'secret' }, { key: 'action', label: '操作', required: true, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'tp-weather', name: 'weather_api', displayName: '天气查询', description: '查询全球城市实时天气与 7 天预报，数据来源 OpenWeatherMap。', category: 'network', source: 'third-party', status: 'enabled', version: '1.0.0', author: '社区', usedByAgents: [], tags: ['weather', 'forecast'], params: [{ key: 'city', label: '城市', required: true, type: 'string' }, { key: 'apikey', label: 'API Key', required: true, type: 'secret' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'tp-feishu', name: 'feishu_message', displayName: '飞书消息', description: '通过飞书机器人向群组或个人发送消息卡片与富文本通知。', category: 'message', source: 'third-party', status: 'disabled', version: '1.1.0', author: '社区', usedByAgents: [], tags: ['feishu', 'lark', 'im'], params: [{ key: 'webhook', label: 'Webhook URL', required: true, type: 'secret' }, { key: 'msg', label: '消息内容', required: true, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'tp-notion', name: 'notion_api', displayName: 'Notion 操作', description: '读写 Notion 数据库页面，支持创建、更新、查询条目。', category: 'data', source: 'third-party', status: 'unavailable', version: '1.0.0', author: '社区', usedByAgents: [], tags: ['notion', 'database', 'notes'], params: [{ key: 'token', label: 'Integration Token', required: true, type: 'secret' }, { key: 'database', label: '数据库 ID', required: true, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
  { id: 'tp-ocr', name: 'ocr_tool', displayName: 'OCR 识别', description: '提取图片中的文字内容，支持中英文混排与表格结构化识别。', category: 'ai', source: 'third-party', status: 'enabled', version: '2.0.0', author: '社区', usedByAgents: ['sub-analyst'], tags: ['ocr', 'vision', 'text'], params: [{ key: 'image_url', label: '图片 URL', required: true, type: 'string' }, { key: 'language', label: '语言', required: false, type: 'string' }], created_at: '2025-01-01', updated_at: '2025-06-01' },
]

let tools = [...MOCK_TOOLS]

function delay(ms = 300) {
  return new Promise((r) => setTimeout(r, ms))
}

// ─── API functions ────────────────────────────────────────────────────────────

export async function fetchTools(params?: {
  source?: string
  category?: string
  status?: string
  keyword?: string
  page?: number
  page_size?: number
}): Promise<ToolListResponse> {
  await delay()
  let list = [...tools]
  if (params?.source) list = list.filter((t) => t.source === params.source)
  if (params?.category) list = list.filter((t) => t.category === params.category)
  if (params?.status) list = list.filter((t) => t.status === params.status)
  if (params?.keyword) {
    const kw = params.keyword.toLowerCase()
    list = list.filter(
      (t) =>
        t.displayName.toLowerCase().includes(kw) ||
        t.name.toLowerCase().includes(kw) ||
        t.tags.some((tag) => tag.toLowerCase().includes(kw)),
    )
  }
  const page = params?.page || 1
  const pageSize = params?.page_size || 100
  const start = (page - 1) * pageSize
  return { items: list.slice(start, start + pageSize), total: list.length, page, page_size: pageSize }
}

export async function fetchTool(id: string): Promise<Tool> {
  await delay()
  const t = tools.find((t) => t.id === id)
  if (!t) throw new Error('工具不存在')
  return { ...t }
}

export async function createTool(data: ToolCreateRequest): Promise<Tool> {
  await delay()
  const tool: Tool = {
    id: `tp-${Date.now()}`,
    name: data.name,
    displayName: data.displayName,
    description: data.description || '',
    category: data.category || 'other',
    source: 'third-party',
    status: data.status || 'enabled',
    version: data.version || '1.0.0',
    author: '自定义',
    usedByAgents: [],
    tags: data.tags || [],
    params: data.params || [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  tools.unshift(tool)
  return tool
}

export async function updateTool(id: string, data: Partial<ToolCreateRequest>): Promise<Tool> {
  await delay()
  const idx = tools.findIndex((t) => t.id === id)
  if (idx === -1) throw new Error('工具不存在')
  tools[idx] = {
    ...tools[idx],
    ...data,
    tags: data.tags ?? tools[idx].tags,
    params: data.params ?? tools[idx].params,
    updated_at: new Date().toISOString(),
  }
  return tools[idx]
}

export async function deleteTool(id: string): Promise<{ deleted: boolean; id: string }> {
  await delay()
  tools = tools.filter((t) => t.id !== id)
  return { deleted: true, id }
}

export async function toggleTool(id: string, enabled: boolean): Promise<Tool> {
  await delay()
  const tool = tools.find((t) => t.id === id)
  if (!tool) throw new Error('工具不存在')
  tool.status = enabled ? 'enabled' : 'disabled'
  return tool
}
