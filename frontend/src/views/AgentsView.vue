<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, X, Eye, EyeOff } from 'lucide-vue-next'
import { useAgentStore } from '@/stores/agent'
import type { ConfigType, Agent } from '@/types/agent'
import AgentListItem from '@/components/agent/AgentListItem.vue'
import AgentDetail from '@/components/agent/AgentDetail.vue'
import AgentGraph from '@/components/agent/AgentGraph.vue'
import AddConfigDialog from '@/components/agent/AddConfigDialog.vue'
import SkillSelectDialog from '@/components/agent/SkillSelectDialog.vue'
import AgentFormDialog from '@/components/agent/AgentFormDialog.vue'

const agentStore = useAgentStore()

/* ---- Dialog state ---- */
const dialogVisible = ref(false)
const dialogType = ref<ConfigType>('tool')
const skillDialogVisible = ref(false)
const showRelationGraph = ref(false)

// Agent form dialog (create/edit)
const agentFormVisible = ref(false)
const agentFormMode = ref<'create' | 'edit'>('create')
const editingAgent = ref<Agent | null>(null)

function openDialog(type: ConfigType) {
  dialogType.value = type
  dialogVisible.value = true
}

async function handleAddConfig(type: ConfigType, value: string, description?: string) {
  try {
    await agentStore.addConfig(type, value, description || '')
    ElMessage.success(`${type === 'tool' ? '工具' : type === 'file' ? '文件' : 'Cron Job'}已添加`)
    dialogVisible.value = false
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
  }
}

async function handleAddSkill(skillId: string) {
  try {
    await agentStore.addSkill(skillId)
    ElMessage.success('技能已添加')
    skillDialogVisible.value = false
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
  }
}

async function handleRemoveSkill(skillId: string) {
  try {
    await agentStore.removeSkill(skillId)
    ElMessage.success('技能已移除')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
  }
}

async function handleUpdateConfig(type: ConfigType, value: string, newValue?: string, description?: string) {
  const agentId = agentStore.selectedAgent?.id
  if (!agentId) return
  try {
    await agentStore.updateConfig(type, value, newValue || '', description || '')
    ElMessage.success(newValue && newValue !== value ? '已重命名' : '已更新')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '更新失败')
  }
}

async function handleRemoveConfig(type: ConfigType, value: string) {
  try {
    await agentStore.removeConfig(type, value)
    ElMessage.success('已移除')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
  }
}

async function handleSaveFileContent(filename: string, content: string) {
  const agentId = agentStore.selectedAgent?.id
  if (!agentId) return
  try {
    await agentStore.saveFileContent(agentId, filename, content)
    ElMessage.success(`${filename} 已保存`)
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  }
}

async function handleToggleStatus(id: string) {
  try {
    await agentStore.toggleStatus(id)
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
  }
}

async function handleClone(agent: Agent) {
  try {
    await agentStore.cloneAgent(agent.id)
    ElMessage.success('克隆成功')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '克隆失败')
  }
}

async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm('确定要删除此代理吗？此操作不可撤销。', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await agentStore.deleteAgent(id)
    ElMessage.success('已删除')
  } catch (err: unknown) {
    if (err instanceof Error && err.message !== 'cancel') {
      ElMessage.error(err.message)
    }
  }
}

function handleNewSubAgent() {
  // 如果当前选中的是子智能体，先切换到主智能体
  if (agentStore.selectedAgent?.type === 'sub') {
    const main = agentStore.mainAgent
    if (main) agentStore.selectAgent(main.id)
  }
  editingAgent.value = null
  agentFormMode.value = 'create'
  agentFormVisible.value = true
}

function handleEditAgent(agent: Agent) {
  editingAgent.value = agent
  agentFormMode.value = 'edit'
  agentFormVisible.value = true
}

async function handleAgentFormSubmit(data: { name: string; description: string; providerId: string; modelId: string }) {
  try {
    if (agentFormMode.value === 'create') {
      await agentStore.createSubAgent(data.name, data.description, data.providerId || undefined, data.modelId || undefined)
      ElMessage.success('子智能体创建成功')
    } else {
      const agentId = editingAgent.value?.id
      if (!agentId) return
      await agentStore.updateAgent(agentId, {
        name: data.name,
        description: data.description,
        providerId: data.providerId || undefined,
        modelId: data.modelId || undefined,
      })
      ElMessage.success('智能体已更新')
    }
    agentFormVisible.value = false
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
  }
}

onMounted(() => {
  agentStore.fetchAgents()
})
</script>

<template>
  <div class="agents-page">
    <!-- Error Banner -->
    <div v-if="agentStore.error" class="error-banner">
      <el-alert :title="agentStore.error" type="warning" show-icon :closable="true">
        <template #default>
          <el-button text size="small" @click="agentStore.fetchAgents()">重试</el-button>
        </template>
      </el-alert>
    </div>

    <!-- Two-panel layout -->
    <div class="panels">
      <!-- Left Panel: Agent List -->
      <div class="panel-left">
        <div class="panel-left-header">
          <div class="panel-left-title-row">
            <span class="panel-title">智能体列表<span class="count-badge">{{ agentStore.agents.length }}</span></span>
            <div class="panel-title-actions">
              <button
                class="eye-btn"
                :title="showRelationGraph ? '隐藏关系图' : '显示关系图'"
                @click="showRelationGraph = !showRelationGraph"
              >
                <Eye v-if="showRelationGraph" :size="16" />
                <EyeOff v-else :size="16" />
              </button>
            </div>
          </div>
          <div class="search-box">
            <Search :size="14" class="search-icon" />
            <input
              v-model="agentStore.searchQuery"
              class="search-input"
              placeholder="搜索智能体..."
            />
            <button
              v-if="agentStore.searchQuery"
              class="search-clear"
              @click="agentStore.searchQuery = ''"
            >
              <X :size="12" />
            </button>
          </div>
        </div>

        <div v-loading="agentStore.loading" class="panel-left-body">
          <template v-if="!agentStore.loading && agentStore.filteredAgents.length > 0">
            <AgentListItem
              v-for="agent in agentStore.filteredAgents"
              :key="agent.id"
              :agent="agent"
              :agents="agentStore.agents"
              :selected-id="agentStore.selectedAgentId"
              :expanded-ids="agentStore.expandedIds"
              :search-query="agentStore.searchQuery"
              @select="(a) => agentStore.selectAgent(a.id)"
              @toggle-expand="(id) => agentStore.toggleExpand(id)"
              @toggle-status="handleToggleStatus"
              @clone="handleClone"
              @delete="handleDelete"
              @new-sub-agent="handleNewSubAgent"
              @edit="handleEditAgent"
            />
          </template>

          <!-- Empty state -->
          <div v-else-if="!agentStore.loading" class="list-empty">
            <p>{{ agentStore.searchQuery ? '未找到匹配的智能体' : '暂无代理' }}</p>
            <el-button
              v-if="!agentStore.searchQuery"
              type="primary"
              size="small"
              @click="handleNewSubAgent"
            >
              <Plus :size="14" style="margin-right: 4px" />
              创建第一个智能体
            </el-button>
          </div>
        </div>
      </div>

      <!-- Right Panel: Agent Detail or Relation Graph -->
      <div class="panel-right">
        <Transition name="graph-mode" mode="out-in">
          <AgentGraph v-if="showRelationGraph" key="graph" />
          <template v-else key="detail">
            <AgentDetail
              v-if="agentStore.selectedAgent"
              :agent="agentStore.selectedAgent"
              :agents="agentStore.agents"
              @add-config="openDialog"
              @remove-config="handleRemoveConfig"
              @add-skill="skillDialogVisible = true"
              @remove-skill="handleRemoveSkill"
              @save-file-content="handleSaveFileContent"
              @toggle-status="handleToggleStatus(agentStore.selectedAgent!.id)"
              @select-agent="(id) => agentStore.selectAgent(id)"
            />
            <div v-else class="detail-empty">
              <p>请在左侧选择一个智能体</p>
            </div>
          </template>
        </Transition>
      </div>
    </div>

    <!-- Add Config Dialog -->
    <AddConfigDialog
      v-if="agentStore.selectedAgent"
      :visible="dialogVisible"
      :type="dialogType"
      :agent-name="agentStore.selectedAgent.name"
      :agent-type="agentStore.selectedAgent.type"
      @close="dialogVisible = false"
      @add="handleAddConfig"
    />

    <!-- Skill Select Dialog -->
    <SkillSelectDialog
      v-if="agentStore.selectedAgent"
      :visible="skillDialogVisible"
      :agent-name="agentStore.selectedAgent.name"
      :existing-skill-ids="agentStore.selectedAgent.skills.map(s => s.id)"
      @close="skillDialogVisible = false"
      @add="handleAddSkill"
    />

    <!-- Agent Form Dialog (Create / Edit) -->
    <AgentFormDialog
      :visible="agentFormVisible"
      :mode="agentFormMode"
      :agent="editingAgent"
      :agent-name="agentStore.selectedAgent?.name ?? ''"
      :agent-type="agentStore.selectedAgent?.type ?? 'main'"
      @close="agentFormVisible = false"
      @submit="handleAgentFormSubmit"
    />
  </div>
</template>

<style scoped>
.agents-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 24px;
  height: 100%;
  background: var(--surface-primary);
  overflow: hidden;
}

/* ---- Error Banner ---- */
.error-banner {
  flex-shrink: 0;
}

/* ---- Two-panel layout ---- */
.panels {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

/* ---- Left Panel ---- */
.panel-left {
  width: 300px;
  min-width: 300px;
  display: flex;
  flex-direction: column;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.panel-left-header {
  padding: 14px 14px 0;
  flex-shrink: 0;
}

.panel-left-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.panel-title-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.text-btn {
  background: none;
  border: none;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  cursor: pointer;
  padding: 2px 4px;
  border-radius: var(--radius-sm);
}

.text-btn:hover {
  color: var(--foreground-primary);
}

.count-badge {
  font-size: var(--font-size-xs);
  padding: 1px 7px;
  margin-left: 6px;
  border-radius: var(--radius-full);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: var(--color-accent);
}

.eye-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: color 0.15s ease;
}

.eye-btn:hover {
  color: var(--foreground-primary);
  background: var(--surface-secondary);
}

.search-box {
  position: relative;
  margin-top: 10px;
  margin-bottom: 6px;
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--foreground-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 7px 30px 7px 30px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.03);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
  transition: border-color 0.15s ease;
}

.search-input::placeholder {
  color: var(--foreground-muted);
}

.search-input:focus {
  border-color: var(--color-accent);
}

.search-clear {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--foreground-muted);
  cursor: pointer;
  padding: 2px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.search-clear:hover {
  color: var(--foreground-primary);
  background: var(--border-subtle);
}

.panel-left-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-height: 0;
}

.list-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 16px;
  text-align: center;
  color: var(--foreground-muted);
  font-size: var(--font-size-sm);
  gap: 12px;
}

/* ---- Right Panel ---- */
.panel-right {
  flex: 1;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.detail-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--foreground-muted);
  font-size: var(--font-size-sm);
}

.graph-mode-enter-active {
  transition: all 0.35s ease-out;
}

.graph-mode-leave-active {
  transition: all 0.2s ease-in;
}

.graph-mode-enter-from {
  opacity: 0;
  transform: scale(0.96);
}

.graph-mode-leave-to {
  opacity: 0;
}
</style>
