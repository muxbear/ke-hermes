import instance from './request'
import type { Skill, SkillCreateRequest } from '@/types/skill'

export async function fetchSkills(category?: string): Promise<Skill[]> {
  const params = category ? { category } : {}
  const res = await instance.get('/skills', { params })
  return res.data.data as Skill[]
}

export async function createSkill(data: SkillCreateRequest): Promise<Skill> {
  const res = await instance.post('/skills', data)
  return res.data.data as Skill
}

export async function fetchSkill(id: string): Promise<Skill> {
  const res = await instance.get(`/skills/${id}`)
  return res.data.data as Skill
}

export async function updateSkill(
  id: string,
  data: Partial<SkillCreateRequest>,
): Promise<Skill> {
  const res = await instance.put(`/skills/${id}`, data)
  return res.data.data as Skill
}

export async function deleteSkill(id: string): Promise<void> {
  await instance.delete(`/skills/${id}`)
}

export async function toggleSkill(
  id: string,
  enabled: boolean,
): Promise<Skill> {
  const res = await instance.patch(`/skills/${id}/toggle`, { enabled })
  return res.data.data as Skill
}
