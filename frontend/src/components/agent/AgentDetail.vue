<script setup lang="ts">
import {
  Settings,
  Sparkles,
  FileText,
  Clock,
  Plus,
  Trash2,
  Zap,
  Activity,
  Pause,
  ChevronRight,
  Pencil,
} from 'lucide-vue-next'
import { ref, computed, watch } from 'vue'
import type { Agent, ConfigType } from '@/types/agent'
import { STATUS_LABELS } from '@/types/agent'
import { useAgentStore } from '@/stores/agent'
import MarkdownEditor from '@/components/agent/MarkdownEditor.vue'
import FileEditDialog from '@/components/agent/FileEditDialog.vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  agent: Agent
  agents: Agent[]
}>()

const emit = defineEmits<{
  (e: 'add-config', type: ConfigType): void
  (e: 'remove-config', type: ConfigType, value: string): void
  (e: 'add-skill'): void
  (e: 'remove-skill', skillId: string): void
  (e: 'toggle-status'): void
  (e: 'select-agent', id: string): void
  (e: 'save-file-content', filename: string, content: string): void
}>()

const agentStore = useAgentStore()
const activeTab = ref<ConfigType | 'skill'>('file')
const selectedFile = ref<string | null>(null)
const editContent = ref('')

// Watch store for content changes
watch(
  () => agentStore.currentFileContent,
  (val) => {
    if (val) {
      editContent.value = val.content
    }
  },
)

// Reset editor + load descriptions when agent changes
watch(
  () => props.agent.id,
  () => {
    selectedFile.value = null
    editContent.value = ''
    agentStore.clearFileContent()
    agentStore.fetchFileDescriptions(props.agent.id)
    agentStore.fetchCronJobs(props.agent.id)
  },
  { immediate: true },
)

function selectFile(filename: string) {
  selectedFile.value = filename
  agentStore.fetchFileContent(props.agent.id, filename)
}

function handleSave(content: string) {
  if (selectedFile.value) {
    emit('save-file-content', selectedFile.value, content)
  }
}

function handleRemoveFile(filename: string) {
  if (selectedFile.value === filename) {
    selectedFile.value = null
    editContent.value = ''
    agentStore.clearFileContent()
  }
  emit('remove-config', 'file', filename)
}

// File edit dialog state
const editDialogVisible = ref(false)
const editingFilename = ref('')
const editingDescription = ref('')

function openEditDialog(filename: string) {
  editingFilename.value = filename
  editingDescription.value = agentStore.currentFileContent?.description || ''
  editDialogVisible.value = true
}

async function handleFileEdit(filename: string, description: string) {
  const agentId = props.agent.id
  try {
    await agentStore.updateConfig('file', editingFilename.value, filename, description)
    // If renamed, update selected file
    if (filename !== editingFilename.value) {
      selectedFile.value = filename
    }
    editDialogVisible.value = false
    ElMessage.success('已更新')
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '更新失败')
  }
}

// Auto-select newly added file
watch(
  () => props.agent.files,
  (newFiles, oldFiles) => {
    if (!oldFiles || newFiles.length <= oldFiles.length) return
    const added = newFiles.find((f) => !oldFiles.includes(f))
    if (added) selectFile(added)
  },
)

const activeSection = computed(() =>
  configSections.find((s) => s.type === activeTab.value) ?? configSections[0],
)

/** 配置区域定义 */
interface ConfigSection {
  type: ConfigType | 'skill'
  label: string
  icon: typeof Zap
  colorClass: string
  iconBg: string
  key: 'tools' | 'skills' | 'files' | 'cronJobs'
}

const configSections: ConfigSection[] = [
  {
    type: 'file',
    label: '文件 (Files)',
    icon: FileText,
    colorClass: 'section--yellow',
    iconBg: 'rgba(234, 179, 8, 0.1)',
    key: 'files',
  },
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
    type: 'cronjob',
    label: '定时任务 (Cron Jobs)',
    icon: Clock,
    colorClass: 'section--green',
    iconBg: 'rgba(34, 197, 94, 0.1)',
    key: 'cronJobs',
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
            主智能体
          </span>
          <span v-else class="type-badge type-badge--sub">
            <ChevronRight :size="11" />
            子智能体
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
          <span class="hstat hstat--yellow">
            <FileText :size="13" />
            {{ agent.files?.length ?? 0 }}
          </span>
          <span class="hstat hstat--green">
            <Clock :size="13" />
            {{ agentStore.cronJobs?.length ?? 0 }}
          </span>
        </div>
      </div>
      <div v-if="agent.systemPrompt" class="system-prompt-row">
        <el-tooltip :content="agent.systemPrompt" placement="bottom" :show-after="300">
          <pre class="prompt-content">{{ agent.systemPrompt }}</pre>
        </el-tooltip>
      </div>
      <div class="header-actions">
        <button
          v-for="section in configSections"
          :key="section.type"
          class="tab-btn"
          :class="[section.colorClass, { active: activeTab === section.type }]"
          @click="activeTab = section.type"
        >
          <component :is="section.icon" :size="14" />
          {{ section.label }}
        </button>
      </div>
    </div>

    <!-- Config Sections -->
    <div class="config-sections">
      <!-- Files tab: split layout -->
      <template v-if="activeTab === 'file'">
        <!-- File selector -->
        <div class="file-selector">
          <div class="section-header">
            <div class="section-title-row">
              <div class="section-icon" :style="{ background: activeSection.iconBg }">
                <component :is="activeSection.icon" :size="16" />
              </div>
              <div>
                <h3 class="section-label">{{ activeSection.label }}</h3>
                <span class="section-count">
                  {{ agent.files?.length ?? 0 }} 个已配置
                </span>
              </div>
            </div>
            <button
              class="add-btn section--yellow"
              @click="emit('add-config', 'file')"
            >
              <Plus :size="13" />
              添加
            </button>
          </div>

          <div class="tags-wrap">
            <template v-if="agent.files && agent.files.length > 0">
              <el-tooltip
                v-for="item in agent.files"
                :key="item"
                :content="agentStore.fileDescriptions[item] || '暂无描述'"
                placement="top"
                :show-after="500"
                :hide-after="0"
              >
                <span
                  class="config-tag section--yellow"
                  :class="{ 'tag-selected': selectedFile === item }"
                  @click="selectFile(item)"
                >
                  <FileText :size="12" class="tag-icon" />
                  {{ item }}
                  <button
                    class="tag-edit"
                    @click.stop="openEditDialog(item)"
                  >
                    <Pencil :size="11" />
                  </button>
                  <button
                    class="tag-delete"
                    @click.stop="handleRemoveFile(item)"
                  >
                    <Trash2 :size="11" />
                  </button>
                </span>
              </el-tooltip>
            </template>
            <div v-else class="empty-section">
              <FileText :size="20" class="empty-icon" />
              <p>暂无文件</p>
              <span class="empty-hint">点击上方"添加"按钮</span>
            </div>
          </div>
        </div>

        <!-- Markdown Editor -->
        <div class="file-editor-wrap">
          <MarkdownEditor
            :content="editContent"
            :filename="selectedFile"
            :loading="agentStore.fileLoading"
            @save="handleSave"
          />
        </div>
      </template>

      <!-- Other tabs: standard tag layout -->
      <div v-else class="config-section">
        <div class="section-header">
          <div class="section-title-row">
            <div class="section-icon" :style="{ background: activeSection.iconBg }">
              <component :is="activeSection.icon" :size="16" />
            </div>
            <div>
              <h3 class="section-label">{{ activeSection.label }}</h3>
              <span class="section-count">
                {{ agent[activeSection.key]?.length ?? 0 }} 个已配置
              </span>
            </div>
          </div>
          <button
            class="add-btn"
            :class="activeSection.colorClass"
            @click="activeTab === 'skill' ? emit('add-skill') : emit('add-config', activeSection.type as ConfigType)"
          >
            <Plus :size="13" />
            添加
          </button>
        </div>

        <!-- Skills tab: render SkillBrief objects with tooltip -->
        <div v-if="activeTab === 'skill'" class="tags-wrap">
          <template v-if="agent.skills && agent.skills.length > 0">
            <el-tooltip
              v-for="skill in agent.skills"
              :key="skill.id"
              :content="skill.description || '暂无描述'"
              placement="top"
              :show-after="400"
              :hide-after="0"
            >
              <span class="config-tag section--purple">
                <Sparkles :size="12" class="tag-icon" />
                {{ skill.name }}
                <button
                  class="tag-delete"
                  @click.stop="emit('remove-skill', skill.id)"
                >
                  <Trash2 :size="11" />
                </button>
              </span>
            </el-tooltip>
          </template>
          <div v-else class="empty-section">
            <Sparkles :size="20" class="empty-icon" />
            <p>暂无技能</p>
            <span class="empty-hint">点击上方"添加"按钮从技能库中选择</span>
          </div>
        </div>

        <!-- Cron Jobs tab -->
        <div v-else-if="activeTab === 'cronjob'" class="tags-wrap">
          <template v-if="agentStore.cronJobs && agentStore.cronJobs.length > 0">
            <el-tooltip
              v-for="job in agentStore.cronJobs"
              :key="job.id"
              placement="top"
              :show-after="400"
              :hide-after="0"
            >
              <template #content>
                <div class="cron-tooltip">
                  <div>{{ job.description || '暂无描述' }}</div>
                  <div>Cron: {{ job.cronExpression }}</div>
                  <div>状态: {{ job.status }}</div>
                </div>
              </template>
              <span class="config-tag section--green">
                <Clock :size="12" class="tag-icon" />
                {{ job.name }}
                <span class="cron-hint">{{ job.cronLabel || job.cronExpression }}</span>
              </span>
            </el-tooltip>
          </template>
          <div v-else class="empty-section">
            <Clock :size="20" class="empty-icon" />
            <p>暂无定时任务</p>
            <span class="empty-hint">点击上方"添加"按钮创建定时任务</span>
          </div>
        </div>

        <!-- Generic config tags for non-skill tabs -->
        <div v-else class="tags-wrap">
          <template v-if="agent[activeSection.key] && agent[activeSection.key].length > 0">
            <span
              v-for="item in agent[activeSection.key]"
              :key="item"
              class="config-tag"
              :class="activeSection.colorClass"
            >
              <component :is="activeSection.icon" :size="12" class="tag-icon" />
              {{ item }}
              <button
                class="tag-delete"
                @click="emit('remove-config', activeSection.type as ConfigType, item)"
              >
                <Trash2 :size="11" />
              </button>
            </span>
          </template>
          <div v-else class="empty-section">
            <component :is="activeSection.icon" :size="20" class="empty-icon" />
            <p>暂无{{ activeSection.type === 'tool' ? '工具' : activeSection.label }}</p>
            <span class="empty-hint">点击上方"添加"按钮</span>
          </div>
        </div>
      </div>
    </div>

    <!-- File Edit Dialog -->
    <FileEditDialog
      :visible="editDialogVisible"
      :filename="editingFilename"
      :description="editingDescription"
      @close="editDialogVisible = false"
      @save="handleFileEdit"
    />
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
.hstat--yellow { color: #eab308; }
.hstat--green { color: #4ade80; }

.system-prompt-row {
  flex-basis: 100%;
  padding: 6px 24px;
  border-bottom: 1px solid var(--border-subtle);
  background: rgba(59, 130, 246, 0.04);
}

.prompt-content {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--font-family-base);
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  cursor: pointer;
}

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

.action-btn--yellow {
  border-color: rgba(234, 179, 8, 0.3);
  color: #eab308;
}

.action-btn--yellow:hover { background: rgba(234, 179, 8, 0.08); }

.action-btn--green {
  border-color: rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.action-btn--green:hover { background: rgba(34, 197, 94, 0.08); }

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  border: 1px solid var(--border-subtle);
  border-bottom: 2px solid transparent;
  background: transparent;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all 0.15s ease;
  color: var(--foreground-muted);
}

.tab-btn:hover {
  color: var(--foreground-primary);
  background: var(--surface-secondary);
}

.tab-btn.active {
  color: var(--foreground-primary);
  background: var(--surface-secondary);
  border-bottom-color: currentColor;
}

.tab-btn.section--yellow.active { border-bottom-color: #eab308; color: #eab308; }
.tab-btn.section--blue.active { border-bottom-color: var(--color-accent); color: var(--color-accent); }
.tab-btn.section--purple.active { border-bottom-color: #a78bfa; color: #a78bfa; }
.tab-btn.section--green.active { border-bottom-color: #4ade80; color: #4ade80; }

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

/* ---- File selector ---- */
.file-selector {
  flex-shrink: 0;
}

/* ---- Tag selected state ---- */
.config-tag.tag-selected {
  border-color: #eab308 !important;
  background: rgba(234, 179, 8, 0.12) !important;
  cursor: pointer;
}

.file-selector .config-tag {
  cursor: pointer;
}

/* ---- File editor wrap ---- */
.file-editor-wrap {
  flex: 1;
  min-height: 300px;
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

.section--yellow .add-btn,
.add-btn.section--yellow {
  border-color: rgba(234, 179, 8, 0.3);
  color: #eab308;
}

.add-btn.section--yellow:hover { background: rgba(234, 179, 8, 0.08); }

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

.config-tag.section--yellow:hover {
  border-color: rgba(234, 179, 8, 0.4);
  background: rgba(234, 179, 8, 0.06);
}

.config-tag.section--green:hover {
  border-color: rgba(34, 197, 94, 0.4);
  background: rgba(34, 197, 94, 0.06);
}

.tag-icon { opacity: 0.7; }

.section--blue .tag-icon { color: var(--color-accent); }
.section--purple .tag-icon { color: #a78bfa; }
.section--yellow .tag-icon { color: #eab308; }
.section--green .tag-icon { color: #4ade80; }

.cron-hint {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin-left: 4px;
}

.cron-hint::before {
  content: '· ';
}

.tag-edit,
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

.config-tag:hover .tag-edit,
.config-tag:hover .tag-delete {
  opacity: 1;
}

.tag-edit:hover {
  color: var(--color-accent);
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
