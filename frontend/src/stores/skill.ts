import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Skill, SkillCreateRequest } from '@/types/skill'
import * as skillApi from '@/services/skillApi'

export const useSkillStore = defineStore('skill', () => {
  const skills = ref<Skill[]>([])
  const total = ref(0)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const page = ref(1)
  const pageSize = ref(20)

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
      const res = await skillApi.fetchSkills({ category, page: 1, page_size: 100 })
      skills.value = res.items
      total.value = res.total
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : '加载技能列表失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchSkillsPaginated(p: number, ps: number, category?: string) {
    loading.value = true
    error.value = null
    try {
      const res = await skillApi.fetchSkills({ category, page: p, page_size: ps })
      skills.value = res.items
      total.value = res.total
      page.value = res.page
      pageSize.value = res.page_size
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : '加载技能列表失败'
    } finally {
      loading.value = false
    }
  }

  async function searchSkills(name: string, p = 1, ps = 20) {
    loading.value = true
    error.value = null
    try {
      const res = await skillApi.searchSkills(name, { page: p, page_size: ps })
      skills.value = res.items
      total.value = res.total
      page.value = res.page
      pageSize.value = res.page_size
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : '搜索技能失败'
    } finally {
      loading.value = false
    }
  }

  async function addSkill(data: SkillCreateRequest): Promise<Skill> {
    const newSkill = await skillApi.createSkill(data)
    skills.value.unshift(newSkill)
    total.value++
    return newSkill
  }

  async function editSkill(id: string, data: Partial<SkillCreateRequest>): Promise<Skill> {
    const updated = await skillApi.updateSkill(id, data)
    const idx = skills.value.findIndex((s) => s.id === id)
    if (idx !== -1) skills.value[idx] = updated
    return updated
  }

  async function removeSkill(id: string) {
    await skillApi.deleteSkill(id)
    skills.value = skills.value.filter((s) => s.id !== id)
    total.value--
  }

  async function batchRemoveSkills(ids: string[]) {
    const res = await skillApi.deleteSkillsBatch(ids)
    const deletedIds = new Set(res.results.filter((r) => r.deleted).map((r) => r.id))
    skills.value = skills.value.filter((s) => !deletedIds.has(s.id))
    total.value -= deletedIds.size
    return res
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

  async function uploadSkillPackage(file: File) {
    const res = await skillApi.uploadSkills(file)
    await fetchSkills()
    return res
  }

  return {
    skills,
    total,
    loading,
    error,
    page,
    pageSize,
    builtinSkills,
    customSkills,
    enabledSkills,
    disabledSkills,
    categoryStats,
    fetchSkills,
    fetchSkillsPaginated,
    searchSkills,
    addSkill,
    editSkill,
    removeSkill,
    batchRemoveSkills,
    toggleSkillEnabled,
    uploadSkillPackage,
  }
})
