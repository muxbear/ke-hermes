import instance from './request'
import type { McpTool, InstallMcpRequest } from '@/types/mcp'

export async function fetchMcpTools(params?: {
  category?: string
  search?: string
  sort?: string
}): Promise<McpTool[]> {
  const res = await instance.get('/mcp/tools', { params })
  return res.data.data as McpTool[]
}

export async function fetchMcpToolById(id: string): Promise<McpTool> {
  const res = await instance.get(`/mcp/tools/${id}`)
  return res.data.data as McpTool
}

export async function installMcpTool(data: InstallMcpRequest): Promise<void> {
  await instance.post(`/mcp/tools/${data.mcp_id}/install`, data)
}

export async function uninstallMcpTool(id: string): Promise<void> {
  await instance.delete(`/mcp/tools/${id}/uninstall`)
}
