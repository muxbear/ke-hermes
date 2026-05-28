/**
 * Agent API — Mock 实现
 * 后端 Agent CRUD API 就绪后，仅需替换本文件内部实现。
 */
import type { Agent, AgentCreateRequest, ConfigType } from '@/types/agent'

/* ------------------------------------------------------------------ */
/*  Mock 数据                                                          */
/* ------------------------------------------------------------------ */

let mockAgents: Agent[] = [
  {
    id: 'main-agent',
    name: '主智能体',
    type: 'main',
    status: 'active',
    tools: ['web_search', 'file_reader', 'code_executor'],
    skills: ['code_analysis', 'debugging', 'optimization'],
    prompts: ['每天执行一次', '每小时检查'],
    files: ['AGENTS.md', 'SOUL.md', 'TOOLS.md', 'IDENTITY.md', 'USER.md', 'HEARTBEAT.md', 'MEMORY.md'],
    subAgents: ['sub-1', 'sub-2'],
    description: '负责整体任务协调和分发',
    lastActive: '2分钟前',
    callCount: 1247,
  },
  {
    id: 'sub-1',
    name: '通用子智能体',
    type: 'sub',
    status: 'active',
    undeletable: true,
    tools: ['web_search', 'file_reader', 'code_executor'],
    skills: ['code_analysis', 'debugging', 'optimization'],
    prompts: ['系统提示词', '代码审查提示词'],
    files: ['AGENTS.md', 'SOUL.md', 'TOOLS.md', 'IDENTITY.md', 'USER.md', 'HEARTBEAT.md', 'MEMORY.md'],
    parentId: 'main-agent',
    description: '通用子智能体，具备与主智能体相同的全部工具，适合处理复杂的、多步骤的独立任务，可以隔离上下文和 token 消耗。',
    lastActive: '5分钟前',
    callCount: 834,
  },
  {
    id: 'sub-2',
    name: '研究子智能体',
    type: 'sub',
    status: 'inactive',
    tools: ['data_processor', 'json_parser'],
    skills: ['data_transformation', 'validation'],
    prompts: ['数据处理提示词'],
    files: ['AGENTS.md', 'SOUL.md', 'TOOLS.md', 'IDENTITY.md', 'USER.md', 'HEARTBEAT.md', 'MEMORY.md'],
    parentId: 'main-agent',
    description: '专门用于使用网络搜索进行深入研究并综合分析结果。',
    lastActive: '1小时前',
    callCount: 456,
  },
]

/* ------------------------------------------------------------------ */
/*  工具函数                                                           */
/* ------------------------------------------------------------------ */

function delay(ms = 200): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}

/* ------------------------------------------------------------------ */
/*  API 函数                                                           */
/* ------------------------------------------------------------------ */

export async function fetchAgents(): Promise<Agent[]> {
  await delay()
  return deepClone(mockAgents)
}

export async function createAgent(data: AgentCreateRequest): Promise<Agent> {
  await delay()
  const newAgent: Agent = {
    id: `sub-${Date.now()}`,
    name: data.name,
    type: 'sub',
    status: 'inactive',
    tools: [],
    skills: [],
    prompts: [],
    files: ['AGENTS.md', 'SOUL.md', 'TOOLS.md', 'IDENTITY.md', 'USER.md', 'HEARTBEAT.md', 'MEMORY.md'],
    parentId: 'main-agent',
    description: data.description || '新创建的子代理',
    lastActive: '刚刚',
    callCount: 0,
  }
  mockAgents.push(newAgent)

  // 将新子代理 ID 加入主智能体的 subAgents
  const main = mockAgents.find((a) => a.type === 'main')
  if (main && main.subAgents) {
    main.subAgents.push(newAgent.id)
  }

  return deepClone(newAgent)
}

export async function deleteAgent(id: string): Promise<void> {
  await delay()
  const target = mockAgents.find((a) => a.id === id)
  if (target?.undeletable) throw new Error('此代理不可删除')
  mockAgents = mockAgents.filter((a) => a.id !== id)

  // 从主智能体 subAgents 中移除
  const main = mockAgents.find((a) => a.type === 'main')
  if (main && main.subAgents) {
    main.subAgents = main.subAgents.filter((sid) => sid !== id)
  }
}

export async function toggleAgentStatus(id: string): Promise<Agent> {
  await delay()
  const agent = mockAgents.find((a) => a.id === id)
  if (!agent) throw new Error('代理不存在')

  agent.status = agent.status === 'active' ? 'inactive' : 'active'
  agent.lastActive = '刚刚'
  return deepClone(agent)
}

export async function cloneAgent(id: string): Promise<Agent> {
  await delay()
  const agent = mockAgents.find((a) => a.id === id)
  if (!agent) throw new Error('代理不存在')

  const cloned: Agent = {
    ...deepClone(agent),
    id: `${agent.id}-clone-${Date.now()}`,
    name: `${agent.name} (副本)`,
    status: 'inactive',
    callCount: 0,
    lastActive: '刚刚',
  }
  mockAgents.push(cloned)

  // 如果克隆的是子代理，加入主智能体的 subAgents
  if (cloned.type === 'sub') {
    const main = mockAgents.find((a) => a.type === 'main')
    if (main && main.subAgents) {
      main.subAgents.push(cloned.id)
    }
  }

  return deepClone(cloned)
}

export async function addConfig(
  agentId: string,
  type: ConfigType,
  value: string,
): Promise<Agent> {
  await delay()
  const agent = mockAgents.find((a) => a.id === agentId)
  if (!agent) throw new Error('代理不存在')

  if (type === 'subagent') {
    // 子代理不允许添加子代理
    if (agent.type !== 'main') throw new Error('子代理不能添加子代理')
    const newSub = await createAgent({ name: value })
    return mockAgents.find((a) => a.id === agentId)! // 返回更新后的主智能体
  }

  const key = type === 'tool' ? 'tools' : type === 'skill' ? 'skills' : type === 'file' ? 'files' : 'prompts'
  if (!agent[key].includes(value)) {
    agent[key].push(value)
  }
  return deepClone(agent)
}

export async function removeConfig(
  agentId: string,
  type: ConfigType,
  value: string,
): Promise<Agent> {
  await delay()
  const agent = mockAgents.find((a) => a.id === agentId)
  if (!agent) throw new Error('代理不存在')

  if (type === 'subagent') {
    await deleteAgent(value)
    const updated = mockAgents.find((a) => a.id === agentId)
    if (!updated) throw new Error('代理不存在')
    return deepClone(updated)
  }

  const key = type === 'tool' ? 'tools' : type === 'skill' ? 'skills' : type === 'file' ? 'files' : 'prompts'
  agent[key] = agent[key].filter((item: string) => item !== value)
  return deepClone(agent)
}
