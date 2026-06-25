/**
 * Agent API — 后端真实接口调用
 */
import type {
  Agent,
  AgentCreateRequest,
  AgentFileContent,
  AgentUpdateRequest,
  ConfigType,
  CronJobBrief,
  FileBrief,
  MemoryScope,
  SkillBrief,
} from '@/types/agent'
import request from '@/services/request'

/* ------------------------------------------------------------------ */
/*  字段转换                                                            */
/* ------------------------------------------------------------------ */

/** 后端 snake_case FileBrief → 前端 camelCase */
function toFileBrief(raw: Record<string, unknown>): FileBrief {
  return {
    filename: raw.filename as string,
    scope: raw.scope as MemoryScope,
    description: (raw.description as string) || '',
    readOnly: (raw.read_only as boolean) ?? false,
  }
}

/** 后端 snake_case → 前端 camelCase */
function toAgent(raw: Record<string, unknown>): Agent {
  const filesByScopeRaw = (raw.files_by_scope as Record<string, unknown>) || {}
  const filesByScope: Record<MemoryScope, FileBrief[]> = {
    agent: [],
    user: [],
    mixture: [],
    org: [],
  }
  for (const key of Object.keys(filesByScopeRaw)) {
    const scope = key as MemoryScope
    const items = (filesByScopeRaw[key] as Array<Record<string, unknown>>) || []
    filesByScope[scope] = items.map(toFileBrief)
  }
  return {
    id: raw.id as string,
    name: raw.name as string,
    type: (raw.type as string) || 'sub',
    status: (raw.status as string) || 'inactive',
    description: (raw.description as string) || '',
    tools: (raw.tools as string[]) || [],
    skills: (raw.skills as SkillBrief[]) || [],
    systemPrompt: (raw.system_prompt as string) || '',
    files: (raw.files as string[]) || [],
    filesByScope,
    subAgents: (raw.sub_agents as string[]) || [],
    parentId: (raw.parent_id as string) ?? undefined,
    providerId: (raw.provider_id as string) ?? undefined,
    modelId: (raw.model_id as string) ?? undefined,
    lastActive: (raw.last_active as string) ?? undefined,
    callCount: (raw.call_count as number) ?? 0,
    undeletable: (raw.undeletable as boolean) ?? false,
    cronJobs: [],
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
    system_prompt: data.systemPrompt || '',
    parent_id: data.parentId || undefined,
    provider_id: data.providerId || undefined,
    model_id: data.modelId || undefined,
  })
  return toAgent(res.data.data)
}

export async function updateAgent(id: string, data: AgentUpdateRequest): Promise<Agent> {
  const res = await request.put(`/agents/${id}`, {
    name: data.name,
    description: data.description || '',
    system_prompt: data.systemPrompt || '',
    provider_id: data.providerId || undefined,
    model_id: data.modelId || undefined,
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
  scope?: MemoryScope,
): Promise<Agent> {
  const res = await request.post(`/agents/${agentId}/config`, {
    type,
    value,
    description,
    scope,
  })
  return toAgent(res.data.data)
}

export async function updateConfig(
  agentId: string,
  type: ConfigType,
  value: string,
  newValue: string = '',
  description: string = '',
  scope?: MemoryScope,
): Promise<Agent> {
  const res = await request.put(`/agents/${agentId}/config`, {
    type,
    value,
    new_value: newValue,
    description,
    scope,
  })
  return toAgent(res.data.data)
}

export async function removeConfig(
  agentId: string,
  type: ConfigType,
  value: string,
  scope?: MemoryScope,
): Promise<Agent> {
  const res = await request.delete(`/agents/${agentId}/config`, {
    data: { type, value, scope },
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
    scope: (raw.scope as MemoryScope) || 'agent',
    readOnly: (raw.read_only as boolean) ?? false,
    createdAt: raw.created_at as string,
    updatedAt: raw.updated_at as string,
  }
}

export async function fetchFileContent(
  agentId: string,
  filename: string,
  scope?: MemoryScope,
): Promise<AgentFileContent> {
  const params = scope ? { scope } : undefined
  const res = await request.get(
    `/agents/${agentId}/files/${encodeURIComponent(filename)}`,
    { params },
  )
  return toFileContent(res.data.data)
}

export async function saveFileContent(
  agentId: string,
  filename: string,
  content: string,
  scope?: MemoryScope,
): Promise<AgentFileContent> {
  const params = scope ? { scope } : undefined
  const res = await request.put(
    `/agents/${agentId}/files/${encodeURIComponent(filename)}`,
    { content },
    { params },
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

/* ------------------------------------------------------------------ */
/*  智能体-技能关联 API                                                   */
/* ------------------------------------------------------------------ */

export async function fetchAgentSkills(agentId: string): Promise<SkillBrief[]> {
  const res = await request.get(`/agents/${agentId}/skills`)
  return (res.data.data as SkillBrief[]) || []
}

export async function addAgentSkill(agentId: string, skillId: string): Promise<SkillBrief[]> {
  const res = await request.post(`/agents/${agentId}/skills`, { skill_id: skillId })
  return (res.data.data as SkillBrief[]) || []
}

export async function removeAgentSkill(agentId: string, skillId: string): Promise<void> {
  await request.delete(`/agents/${agentId}/skills/${skillId}`)
}

/* ------------------------------------------------------------------ */
/*  智能体-定时任务关联 API                                               */
/* ------------------------------------------------------------------ */

function toCronJob(raw: Record<string, unknown>): CronJobBrief {
  return {
    id: raw.id as string,
    agentId: raw.agent_id as string,
    name: raw.name as string,
    description: (raw.description as string) || '',
    cronExpression: raw.cron_expression as string,
    cronLabel: (raw.cron_label as string) || '',
    status: (raw.status as string) || 'active',
    targetType: (raw.target_type as string) || 'agent',
    target: raw.target as string,
    lastRun: (raw.last_run as string) ?? null,
    nextRun: (raw.next_run as string) ?? null,
    tags: (raw.tags as string[]) || [],
    createdAt: raw.created_at as string,
    updatedAt: raw.updated_at as string,
  }
}

export async function fetchAgentCronJobs(agentId: string): Promise<CronJobBrief[]> {
  const res = await request.get(`/agents/${agentId}/cron-jobs`)
  return ((res.data.data as Record<string, unknown>[]) || []).map(toCronJob)
}
