<script setup lang="ts">
import {
  Settings,
  Sparkles,
  GitBranch,
  Users,
  Plus,
  Trash2,
  Zap,
  Activity,
  Play,
  Pause,
  ChevronRight,
} from 'lucide-vue-next'
import type { Agent, ConfigType } from '@/types/agent'
import { CONFIG_TYPE_MAP, STATUS_LABELS } from '@/types/agent'

defineProps<{
  agent: Agent
  agents: Agent[]
}>()

const emit = defineEmits<{
  (e: 'addConfig', type: ConfigType): void
  (e: 'removeConfig', type: ConfigType, value: string): void
  (e: 'toggleStatus'): void
  (e: 'selectAgent', id: string): void
}>()

/** 配置区域定义 */
interface ConfigSection {
  type: ConfigType
  label: string
  icon: typeof Zap
  colorClass: string
  iconBg: string
  key: 'tools' | 'skills' | 'prompts'
}

const configSections: ConfigSection[] = [
  {
    type: 'tool',
    label: '工具 (Tools)',
    icon: Settings,
    colorClass: 'section--blue',
    iconBg: 'rgba(59, 130, 246, 0.1)',
    key: 'tools',
  },
  {
    type: 'skill',
    label: '技能 (Skills)',
    icon: Sparkles,
    colorClass: 'section--purple',
    iconBg: 'rgba(139, 92, 246, 0.1)',
    key: 'skills',
  },
  {
    type: 'prompt',
    label: '提示词 (Prompts)',
    icon: GitBranch,
    colorClass: 'section--green',
    iconBg: 'rgba(34, 197, 94, 0.1)',
    key: 'prompts',
  },
]

function getStatusColor(status: string): string {
  switch (status) {
    case 'active':
      return 'status--active'
    case 'error':
      return 'status--error'
    default:
      return 'status--inactive'
  }
}

function getSubAgent(id: string, agents: Agent[]): Agent | undefined {
  return agents.find((a) => a.id === id)
}
</script>

<template>
  <div class="agent-detail">
    <!-- Header -->
    <div class="detail-header">
      <div class="header-info">
        <div class="header-top-row">
          <h2 class="agent-title">{{ agent.name }}</h2>
          <span class="status-badge" :class="getStatusColor(agent.status)">
            <Activity v-if="agent.status === 'active'" :size="11" />
            <Pause v-else-if="agent.status === 'inactive'" :size="11" />
            <Zap v-else :size="11" />
            {{ STATUS_LABELS[agent.status] ?? agent.status }}
          </span>
          <span
            v-if="agent.type === 'main'"
            class="type-badge type-badge--main"
          >
            <Sparkles :size="11" />
            主代理
          </span>
          <span v-else class="type-badge type-badge--sub">
            <ChevronRight :size="11" />
            子代理
          </span>
        </div>
        <p class="agent-desc">{{ agent.description || '暂无描述' }}</p>
        <div class="header-stats">
          <span class="hstat">
            <Activity :size="13" />
            调用: {{ agent.callCount ?? 0 }}
          </span>
          <span class="hstat">最后活跃: {{ agent.lastActive ?? '未知' }}</span>
          <span class="hstat hstat--blue">
            <Zap :size="13" />
            {{ agent.tools?.length ?? 0 }}
          </span>
          <span class="hstat hstat--purple">
            <Sparkles :size="13" />
            {{ agent.skills?.length ?? 0 }}
          </span>
          <span class="hstat hstat--green">
            <GitBranch :size="13" />
            {{ agent.prompts?.length ?? 0 }}
          </span>
        </div>
      </div>
      <div class="header-actions">
        <button class="action-btn action-btn--blue" @click="emit('addConfig', 'tool')">
          <Plus :size="14" /> 工具
        </button>
        <button class="action-btn action-btn--purple" @click="emit('addConfig', 'skill')">
          <Plus :size="14" /> 技能
        </button>
        <button class="action-btn action-btn--green" @click="emit('addConfig', 'prompt')">
          <Plus :size="14" /> 提示词
        </button>
        <div class="action-divider" />
        <button class="action-btn action-btn--default" @click="emit('toggleStatus')">
          <Pause v-if="agent.status === 'active'" :size="14" />
          <Play v-else :size="14" />
          {{ agent.status === 'active' ? '停止' : '启动' }}
        </button>
      </div>
    </div>

    <!-- Config Sections -->
    <div class="config-sections">
      <div
        v-for="section in configSections"
        :key="section.type"
        class="config-section"
      >
        <div class="section-header">
          <div class="section-title-row">
            <div class="section-icon" :style="{ background: section.iconBg }">
              <component :is="section.icon" :size="16" />
            </div>
            <div>
              <h3 class="section-label">{{ section.label }}</h3>
              <span class="section-count">
                {{ agent[section.key]?.length ?? 0 }} 个已配置
              </span>
            </div>
          </div>
          <button
            class="add-btn"
            :class="section.colorClass"
            @click="emit('addConfig', section.type)"
          >
            <Plus :size="13" />
            添加
          </button>
        </div>

        <div class="tags-wrap">
          <template v-if="agent[section.key] && agent[section.key].length > 0">
            <span
              v-for="item in agent[section.key]"
              :key="item"
              class="config-tag"
              :class="section.colorClass"
            >
              <component :is="section.icon" :size="12" class="tag-icon" />
              {{ item }}
              <button
                class="tag-delete"
                @click="emit('removeConfig', section.type, item)"
              >
                <Trash2 :size="11" />
              </button>
            </span>
          </template>
          <div v-else class="empty-section">
            <component :is="section.icon" :size="20" class="empty-icon" />
            <p>暂无{{ CONFIG_TYPE_MAP[section.type].label }}</p>
            <span class="empty-hint">点击上方"添加"按钮</span>
          </div>
        </div>
      </div>

      <!-- Subagents Section (main agent only) -->
      <div v-if="agent.type === 'main'" class="config-section">
        <div class="section-header">
          <div class="section-title-row">
            <div class="section-icon" style="background: rgba(249, 115, 22, 0.1)">
              <Users :size="16" style="color: #f97316" />
            </div>
            <div>
              <h3 class="section-label">子代理 (Subagents)</h3>
              <span class="section-count">
                {{ agent.subAgents?.length ?? 0 }} 个子代理
              </span>
            </div>
          </div>
          <button
            class="add-btn section--orange"
            @click="emit('addConfig', 'subagent')"
          >
            <Plus :size="13" />
            添加
          </button>
        </div>

        <div class="subagent-list">
          <template
            v-if="agent.subAgents && agent.subAgents.length > 0"
          >
            <div
              v-for="subId in agent.subAgents"
              :key="subId"
              class="subagent-card"
              @click="emit('selectAgent', subId)"
            >
              <div class="sub-card-left">
                <div class="sub-icon-box">
                  <ChevronRight :size="14" style="color: #f97316" />
                </div>
                <div>
                  <p class="sub-name">
                    {{ getSubAgent(subId, agents)?.name ?? subId }}
                  </p>
                  <p class="sub-desc">
                    {{ getSubAgent(subId, agents)?.description ?? '' }}
                  </p>
                </div>
              </div>
              <div class="sub-card-right">
                <span
                  v-if="getSubAgent(subId, agents)"
                  class="status-badge-sm"
                  :class="getStatusColor(getSubAgent(subId, agents)!.status)"
                />
                <button
                  class="sub-delete"
                  @click.stop="emit('removeConfig', 'subagent', subId)"
                >
                  <Trash2 :size="14" />
                </button>
              </div>
            </div>
          </template>
          <p v-else class="no-sub">暂无子代理</p>
        </div>
      </div>

      <!-- Sub agent nesting notice -->
      <div v-else class="nesting-notice">
        <GitBranch :size="24" class="notice-icon" />
        <p class="notice-title">子代理不支持嵌套</p>
        <p class="notice-desc">如需添加子代理，请选择主代理</p>
        <button
          class="action-btn action-btn--default"
          @click="emit('selectAgent', agents.find(a => a.type === 'main')?.id ?? '')"
        >
          切换到主代理
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-detail {
  display: flex;
  flex-direction: column;
  gap: 0;
  height: 100%;
  overflow: hidden;
}

/* ---- Header ---- */
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.header-info {
  flex: 1;
  min-width: 0;
}

.header-top-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.agent-title {
  font-size: 18px;
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
  margin: 0;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.status--active { background: rgba(34, 197, 94, 0.15); color: #22c55e; }
.status--inactive { background: rgba(107, 114, 128, 0.15); color: #9ca3af; }
.status--error { background: rgba(239, 68, 68, 0.15); color: #ef4444; }

.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  padding: 2px 8px;
  border-radius: var(--radius-full);
}

.type-badge--main { background: rgba(59, 130, 246, 0.15); color: var(--color-accent); }
.type-badge--sub { background: rgba(139, 92, 246, 0.15); color: #a78bfa; }

.agent-desc {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  margin: 6px 0 0;
}

.header-stats {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 10px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  flex-wrap: wrap;
}

.hstat {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.hstat--blue { color: var(--color-accent); }
.hstat--purple { color: #a78bfa; }
.hstat--green { color: #4ade80; }

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  background: transparent;
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: all 0.15s ease;
  color: var(--foreground-secondary);
}

.action-btn:hover {
  background: var(--surface-secondary);
}

.action-btn--blue {
  border-color: rgba(59, 130, 246, 0.3);
  color: var(--color-accent);
}

.action-btn--blue:hover { background: rgba(59, 130, 246, 0.08); }

.action-btn--purple {
  border-color: rgba(139, 92, 246, 0.3);
  color: #a78bfa;
}

.action-btn--purple:hover { background: rgba(139, 92, 246, 0.08); }

.action-btn--green {
  border-color: rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.action-btn--green:hover { background: rgba(34, 197, 94, 0.08); }

.action-divider {
  width: 1px;
  height: 20px;
  background: var(--border-subtle);
}

/* ---- Config Sections ---- */
.config-sections {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-section {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 16px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.section-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.section--blue .section-icon,
.section-icon { color: inherit; }

.section-label {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0;
}

.section-count {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.add-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: var(--radius-lg);
  border: 1px solid;
  background: transparent;
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all 0.15s ease;
}

.section--blue .add-btn,
.add-btn.section--blue {
  border-color: rgba(59, 130, 246, 0.3);
  color: var(--color-accent);
}

.add-btn.section--blue:hover { background: rgba(59, 130, 246, 0.08); }

.section--purple .add-btn,
.add-btn.section--purple {
  border-color: rgba(139, 92, 246, 0.3);
  color: #a78bfa;
}

.add-btn.section--purple:hover { background: rgba(139, 92, 246, 0.08); }

.section--green .add-btn,
.add-btn.section--green {
  border-color: rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.add-btn.section--green:hover { background: rgba(34, 197, 94, 0.08); }

.section--orange .add-btn,
.add-btn.section--orange {
  border-color: rgba(249, 115, 22, 0.3);
  color: #f97316;
}

.add-btn.section--orange:hover { background: rgba(249, 115, 22, 0.08); }

/* ---- Tags ---- */
.tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.config-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.03);
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  transition: all 0.2s ease;
}

.config-tag:hover {
  transform: scale(1.03);
}

.config-tag.section--blue:hover {
  border-color: rgba(59, 130, 246, 0.4);
  background: rgba(59, 130, 246, 0.06);
}

.config-tag.section--purple:hover {
  border-color: rgba(139, 92, 246, 0.4);
  background: rgba(139, 92, 246, 0.06);
}

.config-tag.section--green:hover {
  border-color: rgba(34, 197, 94, 0.4);
  background: rgba(34, 197, 94, 0.06);
}

.tag-icon { opacity: 0.7; }

.section--blue .tag-icon { color: var(--color-accent); }
.section--purple .tag-icon { color: #a78bfa; }
.section--green .tag-icon { color: #4ade80; }

.tag-delete {
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
  padding: 2px;
  border-radius: var(--radius-sm);
  opacity: 0;
  transition: opacity 0.15s ease, color 0.15s ease;
}

.config-tag:hover .tag-delete {
  opacity: 1;
}

.tag-delete:hover {
  color: #ef4444;
}

/* ---- Empty section ---- */
.empty-section {
  width: 100%;
  text-align: center;
  padding: 20px;
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-lg);
  color: var(--foreground-muted);
}

.empty-icon {
  opacity: 0.4;
  margin-bottom: 6px;
}

.empty-section p {
  font-size: var(--font-size-sm);
  margin: 4px 0 0;
}

.empty-hint {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

/* ---- Subagent cards ---- */
.subagent-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.subagent-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  transition: all 0.15s ease;
}

.subagent-card:hover {
  border-color: rgba(249, 115, 22, 0.4);
  background: rgba(249, 115, 22, 0.04);
}

.sub-card-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sub-icon-box {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-lg);
  background: rgba(249, 115, 22, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.sub-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
  margin: 0;
}

.sub-desc {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin: 2px 0 0;
}

.sub-card-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-badge-sm {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-badge-sm.status--active { background: #22c55e; }
.status-badge-sm.status--inactive { background: #6b7280; }
.status-badge-sm.status--error { background: #ef4444; }

.sub-delete {
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-sm);
  transition: color 0.15s ease;
}

.sub-delete:hover {
  color: #ef4444;
}

.no-sub {
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
  padding: 8px 0;
}

/* ---- Nesting notice ---- */
.nesting-notice {
  text-align: center;
  padding: 28px 16px;
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-xl);
  background: rgba(255, 255, 255, 0.02);
}

.notice-icon {
  color: var(--foreground-muted);
  opacity: 0.5;
  margin-bottom: 8px;
}

.notice-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-secondary);
  margin: 0 0 4px;
}

.notice-desc {
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
  margin: 0 0 16px;
}
</style>
