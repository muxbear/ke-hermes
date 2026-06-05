/**
 * Model API — 模型管理接口
 */
import instance from './request'
import type { Provider, AIModel, ModelParam } from '@/types/model'

/* ------------------------------------------------------------------ */
/*  snake_case ↔ camelCase 转换                                       */
/* ------------------------------------------------------------------ */

function toModelParam(raw: Record<string, unknown>): ModelParam {
  return {
    key: raw.key as string,
    label: raw.label as string,
    value: raw.value as number | string,
    min: raw.min as number | undefined,
    max: raw.max as number | undefined,
    step: raw.step as number | undefined,
    type: raw.type as 'number' | 'text' | 'select',
    options: raw.options as string[] | undefined,
  }
}

function toModel(raw: Record<string, unknown>): AIModel {
  return {
    id: raw.id as string,
    name: raw.name as string,
    displayName: raw.display_name as string,
    type: raw.type as AIModel['type'],
    status: raw.status as AIModel['status'],
    contextWindow: raw.context_window as number | undefined,
    usedByAgents: (raw.used_by_agents as string[]) ?? [],
    callCount: (raw.call_count as number) ?? 0,
    params: ((raw.params as Record<string, unknown>[]) ?? []).map(toModelParam),
    description: (raw.description as string) ?? '',
    releaseDate: raw.release_date as string | undefined,
  }
}

function toProvider(raw: Record<string, unknown>): Provider {
  return {
    id: raw.id as string,
    name: raw.name as string,
    logo: raw.logo as string,
    status: raw.status as Provider['status'],
    apiBase: raw.api_base as string,
    apiKey: raw.api_key as string,
    models: ((raw.models as Record<string, unknown>[]) ?? []).map(toModel),
    description: (raw.description as string) ?? '',
    website: (raw.website as string) ?? '',
  }
}

function toModelPayload(data: AIModel): Record<string, unknown> {
  return {
    name: data.name,
    display_name: data.displayName,
    type: data.type,
    status: data.status,
    context_window: data.contextWindow ?? null,
    call_count: data.callCount,
    description: data.description,
    release_date: data.releaseDate ?? null,
    params: data.params,
    used_by_agents: data.usedByAgents,
  }
}

function toProviderPayload(data: Provider): Record<string, unknown> {
  return {
    name: data.name,
    logo: data.logo,
    api_base: data.apiBase,
    api_key: data.apiKey,
    status: data.status,
    description: data.description,
    website: data.website,
  }
}

/* ------------------------------------------------------------------ */
/*  API 函数                                                           */
/* ------------------------------------------------------------------ */

export async function fetchProviders(): Promise<Provider[]> {
  const res = await instance.get('/providers')
  return (res.data.data as Record<string, unknown>[]).map(toProvider)
}

export async function createProvider(data: Provider): Promise<Provider> {
  const res = await instance.post('/providers', toProviderPayload(data))
  return toProvider(res.data.data as Record<string, unknown>)
}

export async function updateProvider(id: string, data: Provider): Promise<Provider> {
  const res = await instance.put(`/providers/${id}`, toProviderPayload(data))
  return toProvider(res.data.data as Record<string, unknown>)
}

export async function deleteProvider(id: string): Promise<void> {
  await instance.delete(`/providers/${id}`)
}

export async function createModel(providerId: string, data: AIModel): Promise<AIModel> {
  const res = await instance.post(`/providers/${providerId}/models`, toModelPayload(data))
  return toModel(res.data.data as Record<string, unknown>)
}

export async function updateModel(providerId: string, modelId: string, data: AIModel): Promise<AIModel> {
  const res = await instance.put(`/providers/${providerId}/models/${modelId}`, toModelPayload(data))
  return toModel(res.data.data as Record<string, unknown>)
}

export async function deleteModel(providerId: string, modelId: string): Promise<void> {
  await instance.delete(`/providers/${providerId}/models/${modelId}`)
}
