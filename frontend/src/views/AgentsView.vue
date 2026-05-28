<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, X, EyeOff, Eye, Upload, Download } from 'lucide-vue-next'
import { useAgentStore } from '@/stores/agent'
import type { ConfigType, Agent } from '@/types/agent'
import AgentListItem from '@/components/agent/AgentListItem.vue'
import AgentDetail from '@/components/agent/AgentDetail.vue'
import AddConfigDialog from '@/components/agent/AddConfigDialog.vue'

const agentStore = useAgentStore()

/* ---- Dialog state ---- */
const dialogVisible = ref(false)
const dialogType = ref<ConfigType>('tool')

function openDialog(type: ConfigType) {
  dialogType.value = type
  dialogVisible.value = true
}

async function handleAddConfig(type: ConfigType, value: string) {
  try {
    if (type === 'subagent') {
      await agentStore.createSubAgent(value)
      ElMessage.success('子代理创建成功')
    } else {
      await agentStore.addConfig(type, value)
      ElMessage.success(`${type === 'tool' ? '工具' : type === 'skill' ? '技能' : '提示词'}已添加`)
    }
    dialogVisible.value = false
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '操作失败')
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
  // 如果当前选中的是子代理，先切换到主代理
  if (agentStore.selectedAgent?.type === 'sub') {
    const main = agentStore.mainAgent
    if (main) agentStore.selectAgent(main.id)
  }
  openDialog('subagent')
}

onMounted(() => {
  agentStore.fetchAgents()
})
</script>

<template>
  <div class="agents-page">
    <!-- Page Header -->
    <div class="page-header">
      <div class="page-header__info">
        <h1>代理管理中心</h1>
        <p>管理和配置您的智能代理系统</p>
      </div>
      <div class="page-header__actions">
        <el-button size="small" plain>
          <Upload :size="14" style="margin-right: 4px" />
          导入
        </el-button>
        <el-button size="small" plain>
          <Download :size="14" style="margin-right: 4px" />
          导出
        </el-button>
        <el-button type="primary" size="small" @click="handleNewSubAgent">
          <Plus :size="14" style="margin-right: 4px" />
          新建子代理
        </el-button>
      </div>
    </div>

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
            <span class="panel-title">代理列表</span>
            <div class="panel-title-actions">
              <button class="text-btn" @click="agentStore.expandAll()">展开</button>
              <button class="text-btn" @click="agentStore.collapseAll()">折叠</button>
              <span class="count-badge">{{ agentStore.agents.length }}</span>
            </div>
          </div>
          <div class="search-box">
            <Search :size="14" class="search-icon" />
            <input
              v-model="agentStore.searchQuery"
              class="search-input"
              placeholder="搜索代理..."
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
            />
          </template>

          <!-- Empty state -->
          <div v-else-if="!agentStore.loading" class="list-empty">
            <p>{{ agentStore.searchQuery ? '未找到匹配的代理' : '暂无代理' }}</p>
            <el-button
              v-if="!agentStore.searchQuery"
              type="primary"
              size="small"
              @click="handleNewSubAgent"
            >
              <Plus :size="14" style="margin-right: 4px" />
              创建第一个代理
            </el-button>
          </div>
        </div>
      </div>

      <!-- Right Panel: Agent Detail -->
      <div class="panel-right">
        <AgentDetail
          v-if="agentStore.selectedAgent"
          :agent="agentStore.selectedAgent"
          :agents="agentStore.agents"
          @add-config="openDialog"
          @remove-config="handleRemoveConfig"
          @toggle-status="handleToggleStatus(agentStore.selectedAgent!.id)"
          @select-agent="(id) => agentStore.selectAgent(id)"
        />
        <div v-else class="detail-empty">
          <p>请在左侧选择一个代理</p>
        </div>
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

/* ---- Page Header ---- */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.page-header__info h1 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
  margin: 0;
}

.page-header__info p {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  margin: 4px 0 0;
}

.page-header__actions {
  display: flex;
  gap: 8px;
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
  border-radius: var(--radius-full);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: var(--color-accent);
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
</style>
