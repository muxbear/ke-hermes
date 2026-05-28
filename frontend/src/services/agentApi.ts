/**
 * Agent API — 后端真实接口调用
 */
import type { Agent, AgentCreateRequest, ConfigType } from '@/types/agent'
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
): Promise<Agent> {
  const res = await request.post(`/agents/${agentId}/config`, { type, value })
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
