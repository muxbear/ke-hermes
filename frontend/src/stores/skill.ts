import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Skill, SkillCreateRequest } from '@/types/skill'
import * as skillApi from '@/services/skillApi'

export const useSkillStore = defineStore('skill', () => {
  const skills = ref<Skill[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const builtinSkills = computed(() => skills.value.filter((s) => s.is_builtin))
  const customSkills = computed(() => skills.value.filter((s) => !s.is_builtin))
  const enabledSkills = computed(() => skills.value.filter((s) => s.enabled))
  const disabledSkills = computed(() => skills.value.filter((s) => !s.enabled))

  const categoryStats = computed(() => {
    const map: Record<string, { total: number; enabled: number; disabled: number }> = {}
    for (const s of skills.value) {
      if (!map[s.category]) {
        map[s.category] = { total: 0, enabled: 0, disabled: 0 }
      }
      map[s.category].total++
      if (s.enabled) {
        map[s.category].enabled++
      } else {
        map[s.category].disabled++
      }
    }
    return map
  })

  async function fetchSkills(category?: string) {
    loading.value = true
    error.value = null
    try {
      skills.value = await skillApi.fetchSkills(category)
    } catch (err: unknown) {
      if (err instanceof Error && err.message.includes('404')) {
        error.value = 'Skills API 尚未部署，后端接口开发中'
      } else {
        error.value = err instanceof Error ? err.message : '加载技能列表失败'
      }
    } finally {
      loading.value = false
    }
  }

  async function addSkill(data: SkillCreateRequest): Promise<Skill> {
    const newSkill = await skillApi.createSkill(data)
    skills.value.unshift(newSkill)
    return newSkill
  }

  async function editSkill(
    id: string,
    data: Partial<SkillCreateRequest>,
  ): Promise<Skill> {
    const updated = await skillApi.updateSkill(id, data)
    const idx = skills.value.findIndex((s) => s.id === id)
    if (idx !== -1) skills.value[idx] = updated
    return updated
  }

  async function removeSkill(id: string) {
    await skillApi.deleteSkill(id)
    skills.value = skills.value.filter((s) => s.id !== id)
  }

  async function toggleSkillEnabled(id: string, enabled: boolean) {
    const skill = skills.value.find((s) => s.id === id)
    if (skill) skill.enabled = enabled
    try {
      await skillApi.toggleSkill(id, enabled)
    } catch {
      if (skill) skill.enabled = !enabled
      throw new Error('切换失败')
    }
  }

  return {
    skills,
    loading,
    error,
    builtinSkills,
    customSkills,
    enabledSkills,
    disabledSkills,
    categoryStats,
    fetchSkills,
    addSkill,
    editSkill,
    removeSkill,
    toggleSkillEnabled,
  }
})
