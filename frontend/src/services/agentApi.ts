/**
 * Agent API — 后端真实接口调用
 */
import type { Agent, AgentCreateRequest, AgentFileContent, ConfigType } from '@/types/agent'
import request from '@/services/request'

/* ------------------------------------------------------------------ */
/*  字段转换                                                            */
/* ------------------------------------------------------------------ */

/** 后端 snake_case → 前端 camelCase */
function toAgent(raw: Record<string, unknown>): Agent {
  return {
    id: raw.id as string,
    name: raw.name as string,
    type: (raw.type as string) || 'sub',
    status: (raw.status as string) || 'inactive',
    description: (raw.description as string) || '',
    tools: (raw.tools as string[]) || [],
    skills: (raw.skills as string[]) || [],
    prompts: (raw.prompts as string[]) || [],
    files: (raw.files as string[]) || [],
    subAgents: (raw.sub_agents as string[]) || [],
    parentId: (raw.parent_id as string) ?? undefined,
    lastActive: (raw.last_active as string) ?? undefined,
    callCount: (raw.call_count as number) ?? 0,
    undeletable: (raw.undeletable as boolean) ?? false,
  }
}

/* ------------------------------------------------------------------ */
/*  API 函数                                                           */
/* ------------------------------------------------------------------ */

export async function fetchAgents(): Promise<Agent[]> {
  const res = await request.get('/agents')
  const agents: Agent[] = (res.data.data?.agents || []).map(toAgent)
  return agents
}

export async function createAgent(data: AgentCreateRequest): Promise<Agent> {
  const res = await request.post('/agents', {
    name: data.name,
    description: data.description || '',
    parent_id: data.parentId || undefined,
  })
  return toAgent(res.data.data)
}

export async function deleteAgent(id: string): Promise<void> {
  await request.delete(`/agents/${id}`)
}

export async function toggleAgentStatus(id: string): Promise<Agent> {
  const res = await request.patch(`/agents/${id}/status`)
  return toAgent(res.data.data)
}

export async function cloneAgent(id: string): Promise<Agent> {
  const res = await request.post(`/agents/${id}/clone`)
  return toAgent(res.data.data)
}

export async function addConfig(
  agentId: string,
  type: ConfigType,
  value: string,
  description: string = '',
): Promise<Agent> {
  const res = await request.post(`/agents/${agentId}/config`, { type, value, description })
  return toAgent(res.data.data)
}

export async function updateConfig(
  agentId: string,
  type: ConfigType,
  value: string,
  newValue: string = '',
  description: string = '',
): Promise<Agent> {
  const res = await request.put(`/agents/${agentId}/config`, {
    type,
    value,
    new_value: newValue,
    description,
  })
  return toAgent(res.data.data)
}

export async function removeConfig(
  agentId: string,
  type: ConfigType,
  value: string,
): Promise<Agent> {
  const res = await request.delete(`/agents/${agentId}/config`, {
    data: { type, value },
  })
  return toAgent(res.data.data)
}

/* ------------------------------------------------------------------ */
/*  文件内容 API                                                        */
/* ------------------------------------------------------------------ */

function toFileContent(raw: Record<string, unknown>): AgentFileContent {
  return {
    filename: raw.filename as string,
    content: (raw.content as string) || '',
    description: (raw.description as string) || '',
    createdAt: raw.created_at as string,
    updatedAt: raw.updated_at as string,
  }
}

export async function fetchFileContent(
  agentId: string,
  filename: string,
): Promise<AgentFileContent> {
  const res = await request.get(
    `/agents/${agentId}/files/${encodeURIComponent(filename)}`,
  )
  return toFileContent(res.data.data)
}

export async function saveFileContent(
  agentId: string,
  filename: string,
  content: string,
): Promise<AgentFileContent> {
  const res = await request.put(
    `/agents/${agentId}/files/${encodeURIComponent(filename)}`,
    { content },
  )
  return toFileContent(res.data.data)
}

export async function fetchFileDescriptions(
  agentId: string,
): Promise<Record<string, string>> {
  const res = await request.get(`/agents/${agentId}/file-descriptions`)
  const items: Array<{ filename: string; description: string }> = res.data.data || []
  const map: Record<string, string> = {}
  for (const item of items) {
    map[item.filename] = item.description
  }
  return map
}
