<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, X, Eye, EyeOff } from 'lucide-vue-next'
import { useAgentStore } from '@/stores/agent'
import type { ConfigType, Agent } from '@/types/agent'
import AgentListItem from '@/components/agent/AgentListItem.vue'
import AgentDetail from '@/components/agent/AgentDetail.vue'
import AddConfigDialog from '@/components/agent/AddConfigDialog.vue'

const agentStore = useAgentStore()

/* ---- Dialog state ---- */
const dialogVisible = ref(false)
const dialogType = ref<ConfigType>('tool')
const showRelationGraph = ref(false)

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
      ElMessage.success(`${type === 'tool' ? '工具' : type === 'skill' ? '技能' : type === 'file' ? '文件' : 'Cron Job'}已添加`)
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
  // 如果当前选中的是子代理，先切换到主智能体
  if (agentStore.selectedAgent?.type === 'sub') {
    const main = agentStore.mainAgent
    if (main) agentStore.selectAgent(main.id)
  }
  openDialog('subagent')
}

function branchWidth(idx: number): string {
  return `${120 + idx * 40}px`
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
            <span class="panel-title">代理列表<span class="count-badge">{{ agentStore.agents.length }}</span></span>
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
              @new-sub-agent="handleNewSubAgent"
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

      <!-- Right Panel: Agent Detail or Relation Graph -->
      <div class="panel-right">
        <!-- Relation Graph -->
        <div v-if="showRelationGraph" class="relation-graph">
          <div class="graph-title">主智能体关系图</div>
          <div class="graph-canvas">
            <template v-if="agentStore.mainAgent">
              <!-- Main agent node -->
              <div class="graph-node graph-node--main" @click="agentStore.selectAgent(agentStore.mainAgent.id)">
                <div class="node-avatar">
                  <span>{{ agentStore.mainAgent.name.charAt(0) }}</span>
                </div>
                <div class="node-info">
                  <span class="node-name">{{ agentStore.mainAgent.name }}</span>
                  <span class="node-desc">{{ agentStore.mainAgent.description }}</span>
                </div>
              </div>
              <!-- Connector lines -->
              <div v-if="agentStore.subAgents.length > 0" class="graph-lines">
                <div
                  v-for="(sub, idx) in agentStore.subAgents"
                  :key="sub.id"
                  class="graph-branch"
                >
                  <div class="line-vertical" />
                  <div class="line-horizontal" :style="{ width: branchWidth(idx) }" />
                  <!-- Sub agent node -->
                  <div class="graph-node graph-node--sub" @click="agentStore.selectAgent(sub.id)">
                    <div class="node-avatar node-avatar--sub">
                      <span>{{ sub.name.charAt(0) }}</span>
                    </div>
                    <div class="node-info">
                      <span class="node-name">{{ sub.name }}</span>
                      <span class="node-desc">{{ sub.description }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- Agent Detail (default) -->
        <template v-else>
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
        </template>
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

/* ---- Relation Graph ---- */
.relation-graph {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px 32px;
  overflow: auto;
}

.graph-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
  margin-bottom: 32px;
  text-align: center;
}

.graph-canvas {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  flex: 1;
}

.graph-node {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-subtle);
  background: var(--surface-card);
  cursor: pointer;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  min-width: 320px;
}

.graph-node:hover {
  border-color: var(--color-accent);
  box-shadow: 0 0 24px rgba(59, 130, 246, 0.12);
}

.graph-node--main {
  border-color: rgba(59, 130, 246, 0.3);
}

.graph-node--sub {
  border-color: rgba(249, 115, 22, 0.3);
}

.graph-node--sub:hover {
  border-color: #f97316;
  box-shadow: 0 0 24px rgba(249, 115, 22, 0.12);
}

.node-avatar {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-full);
  background: rgba(59, 130, 246, 0.15);
  color: var(--color-accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: var(--font-weight-bold);
  flex-shrink: 0;
}

.node-avatar--sub {
  background: rgba(249, 115, 22, 0.15);
  color: #f97316;
}

.node-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.node-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.node-desc {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 360px;
}

.graph-lines {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding-left: 80px;
  margin-top: 8px;
  gap: 0;
}

.graph-branch {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
}

.line-vertical {
  width: 2px;
  height: 24px;
  background: var(--border-subtle);
  margin-left: 60px;
}

.line-horizontal {
  height: 2px;
  background: var(--border-subtle);
  margin: 4px 0;
}
</style>
