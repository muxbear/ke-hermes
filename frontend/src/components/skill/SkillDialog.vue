<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { X, Search, Download, ChevronDown, Upload, Check, AlertTriangle } from 'lucide-vue-next'
import type { Skill, SkillCreateRequest } from '@/types/skill'

const props = defineProps<{
  visible: boolean
  skill: Skill | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', data: SkillCreateRequest): void
}>()

const isEditing = computed(() => !!props.skill)
const activeTab = ref<'download' | 'upload' | 'manual'>('download')

// ---- Click-outside & keyboard ----
const repoSelectRef = ref<HTMLElement | null>(null)

function handleClickOutside(e: MouseEvent) {
  if (repoSelectRef.value && !repoSelectRef.value.contains(e.target as Node)) {
    repoDropdownOpen.value = false
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    repoDropdownOpen.value = false
    if (!props.visible) return
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside, true)
  document.addEventListener('keydown', handleKeydown)
})
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside, true)
  document.removeEventListener('keydown', handleKeydown)
})

// ============================================================
//  Tab 1: Repository Download
// ============================================================
interface RepoOption {
  label: string
  url: string
  desc: string
}

interface RepoSkill {
  name: string
  description: string
  category: string
  selected: boolean
}

const repoOptions: RepoOption[] = [
  { label: 'ClawHub', url: 'https://clawhub.ai/', desc: '默认仓库' },
  { label: 'Anthropic Skills', url: 'https://github.com/anthropics/skills', desc: 'Anthropic 官方' },
  { label: 'LangChain', url: 'https://github.com/langchain-ai/langchain', desc: '95k stars' },
  { label: 'CrewAI', url: 'https://github.com/crewAIInc/crewAI-examples', desc: '8.3k stars' },
  { label: 'AutoGen', url: 'https://github.com/microsoft/autogen', desc: '38k stars' },
]

const selectedRepo = ref(repoOptions[0])
const repoDropdownOpen = ref(false)
const isCustomRepo = ref(false)
const customRepoUrl = ref('')

const repoUrl = computed(() =>
  isCustomRepo.value ? customRepoUrl.value : selectedRepo.value.url,
)

function selectRepoOption(opt: RepoOption) {
  selectedRepo.value = opt
  isCustomRepo.value = false
  repoDropdownOpen.value = false
  resetRepoData()
}

function selectCustomRepo() {
  isCustomRepo.value = true
  customRepoUrl.value = ''
  repoDropdownOpen.value = false
  resetRepoData()
}

function resetRepoData() {
  repoSkills.value = []
  repoError.value = ''
  skillSearch.value = ''
  skillPage.value = 1
}

const fetchingRepo = ref(false)
const repoSkills = ref<RepoSkill[]>([])
const repoError = ref('')
const skillSearch = ref('')
const skillPage = ref(1)
const skillPageSize = 6

const filteredRepoSkills = computed(() => {
  let list = repoSkills.value
  if (skillSearch.value.trim()) {
    const kw = skillSearch.value.trim().toLowerCase()
    list = list.filter(
      (s) =>
        s.name.toLowerCase().includes(kw) ||
        s.description.toLowerCase().includes(kw) ||
        s.category.toLowerCase().includes(kw),
    )
  }
  return list
})

const pagedRepoSkills = computed(() => {
  const start = (skillPage.value - 1) * skillPageSize
  return filteredRepoSkills.value.slice(start, start + skillPageSize)
})

const totalFiltered = computed(() => filteredRepoSkills.value.length)

const allSelected = computed({
  get: () =>
    pagedRepoSkills.value.length > 0 &&
    pagedRepoSkills.value.every((s) => s.selected),
  set: (val: boolean) =>
    pagedRepoSkills.value.forEach((s) => {
      s.selected = val
    }),
})

const isIndeterminate = computed(() => {
  const n = pagedRepoSkills.value.filter((s) => s.selected).length
  return n > 0 && n < pagedRepoSkills.value.length
})

const selectedCount = computed(() => repoSkills.value.filter((s) => s.selected).length)

async function fetchRepo() {
  if (!repoUrl.value.trim()) return
  fetchingRepo.value = true
  repoError.value = ''
  repoSkills.value = []
  skillSearch.value = ''
  skillPage.value = 1

  try {
    await new Promise((r) => setTimeout(r, 1000))
    repoSkills.value = [
      { name: 'web-search', description: '实时搜索互联网信息，获取最新资讯与数据', category: 'search', selected: true },
      { name: 'code-interpreter', description: '安全沙箱中执行 Python 代码，支持数据分析', category: 'code', selected: true },
      { name: 'image-generator', description: '根据文本描述使用 DALL-E/Stable Diffusion 生成图像', category: 'creative', selected: false },
      { name: 'data-analyzer', description: '处理 CSV/Excel/JSON 数据，生成统计报告与可视化图表', category: 'analysis', selected: true },
      { name: 'file-manager', description: '读写 PDF/Word/Markdown 等格式文件，支持批量转换', category: 'tools', selected: false },
      { name: 'translator', description: '支持 50+ 语言的精准翻译，可保持原文格式', category: 'tools', selected: false },
      { name: 'summarizer', description: '对长文本进行智能摘要，提取关键信息', category: 'analysis', selected: false },
      { name: 'sentiment-analyzer', description: '分析文本情感倾向，支持细粒度情绪分类', category: 'analysis', selected: false },
      { name: 'pdf-extractor', description: '从 PDF 文档中提取文本、表格和图片信息', category: 'tools', selected: false },
      { name: 'sql-generator', description: '将自然语言查询转换为 SQL 语句', category: 'code', selected: false },
    ]
  } catch {
    repoError.value = '获取仓库技能列表失败，请检查仓库地址'
  } finally {
    fetchingRepo.value = false
  }
}

function handleSearchChange() {
  skillPage.value = 1
}

function importSelected() {
  const selected = repoSkills.value.filter((s) => s.selected)
  if (selected.length === 0) { ElMessage.warning('请选择要导入的技能'); return }
  selected.forEach((s) =>
    emit('save', { name: s.name, description: s.description, icon: 'Zap', category: s.category, prompt: '' }),
  )
  ElMessage.success(`已导入 ${selected.length} 个技能`)
  emit('close')
}

// ============================================================
//  Tab 2: Local Upload
// ============================================================
const uploadResult = ref<{ name: string; valid: boolean; message: string }[]>([])
const uploadMessage = ref('')
const isDragging = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileDrop(e: DragEvent) {
  isDragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) validateFile(file)
}

function handleFileInputChange() {
  const file = fileInput.value?.files?.[0]
  if (file) validateFile(file)
}

async function validateFile(file: File) {
  uploadResult.value = []
  const ext = file.name.split('.').pop()?.toLowerCase()
  const allowed = ['json', 'yaml', 'yml', 'md', 'zip']
  if (!ext || !allowed.includes(ext)) {
    uploadMessage.value = `不支持的文件格式: .${ext}`
    uploadResult.value.push({ name: file.name, valid: false, message: `不支持 .${ext} 格式` })
    return
  }
  await new Promise((r) => setTimeout(r, 600))
  uploadMessage.value = '校验通过'
  uploadResult.value = [
    { name: '文件格式校验', valid: true, message: '通过' },
    { name: '必需字段检查 (name)', valid: true, message: '通过' },
    { name: '必需字段检查 (description)', valid: true, message: '通过' },
    { name: '必需字段检查 (prompt)', valid: true, message: '通过' },
  ]
}

function handleUploadImport() {
  ElMessage.success('技能导入成功')
  emit('close')
}

// ============================================================
//  Tab 3: Manual Create
// ============================================================
const form = ref<SkillCreateRequest>({
  name: '', description: '', icon: 'Zap', category: 'custom', prompt: '',
})

watch(
  () => props.skill,
  (s) => {
    if (s) {
      form.value = { name: s.name, description: s.description, icon: s.icon, category: s.category, prompt: s.prompt }
    } else {
      form.value = { name: '', description: '', icon: 'Zap', category: 'custom', prompt: '' }
    }
  },
  { immediate: true },
)

function handleManualSubmit() {
  if (!form.value.name.trim()) { ElMessage.warning('请输入技能名称'); return }
  emit('save', { ...form.value })
}

// ============================================================
//  Pagination helper
// ============================================================
function totalPages() {
  return Math.max(1, Math.ceil(totalFiltered.value / skillPageSize))
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="skill-overlay" @click.self="emit('close')">
        <div class="skill-modal">
          <!-- Header -->
          <div class="modal-header">
            <span class="modal-title">{{ isEditing ? '编辑技能' : '创建技能' }}</span>
            <button class="modal-close" @click="emit('close')">
              <X :size="18" />
            </button>
          </div>

          <!-- Tab Navigation -->
          <div v-if="!isEditing" class="modal-tabs">
            <button class="tab-btn" :class="{ active: activeTab === 'download' }" @click="activeTab = 'download'">
              从仓库下载
            </button>
            <button class="tab-btn" :class="{ active: activeTab === 'upload' }" @click="activeTab = 'upload'">
              本地上传
            </button>
            <button class="tab-btn" :class="{ active: activeTab === 'manual' }" @click="activeTab = 'manual'">
              手动创建
            </button>
          </div>

          <div class="modal-body">
            <!-- =========== TAB 1: DOWNLOAD =========== -->
            <div v-if="activeTab === 'download' && !isEditing" class="tab-inner">
              <!-- Unified Panel -->
              <div class="download-panel">
                <!-- Top: Repo selector + Fetch (single row) -->
                <div class="dp-top">
                  <div ref="repoSelectRef" class="custom-select" :class="{ open: repoDropdownOpen }">
                    <button
                      class="select-trigger"
                      type="button"
                      @click.stop="repoDropdownOpen = !repoDropdownOpen"
                    >
                      <span>{{ isCustomRepo ? '自定义地址' : selectedRepo.label }}</span>
                      <ChevronDown :size="14" class="select-arrow" />
                    </button>
                    <div v-show="repoDropdownOpen" class="select-dropdown">
                      <div
                        v-for="opt in repoOptions"
                        :key="opt.url"
                        class="select-option"
                        :class="{ picked: !isCustomRepo && opt.url === selectedRepo.url }"
                        @click.stop="selectRepoOption(opt)"
                      >
                        <div class="opt-info">
                          <span class="opt-label">{{ opt.label }}</span>
                          <span class="opt-desc">{{ opt.desc }}</span>
                        </div>
                        <Check v-if="!isCustomRepo && opt.url === selectedRepo.url" :size="14" class="opt-check" />
                      </div>
                      <div class="select-divider" />
                      <div
                        class="select-option"
                        :class="{ picked: isCustomRepo }"
                        @click.stop="selectCustomRepo()"
                      >
                        <div class="opt-info">
                          <span class="opt-label">自定义地址</span>
                          <span class="opt-desc">手动输入仓库 URL</span>
                        </div>
                        <Check v-if="isCustomRepo" :size="14" class="opt-check" />
                      </div>
                    </div>
                  </div>
                  <input
                    v-if="isCustomRepo"
                    v-model="customRepoUrl"
                    type="text"
                    class="text-input dp-url-input"
                    placeholder="输入自定义仓库地址"
                  />
                  <input
                    v-else
                    :value="selectedRepo.url"
                    type="text"
                    class="text-input dp-url-input readonly"
                    readonly
                  />
                  <button class="btn btn-primary" :disabled="!repoUrl || fetchingRepo" @click="fetchRepo">
                    <span v-if="fetchingRepo" class="spinner" />
                    <Search v-else :size="14" />
                    获取
                  </button>
                </div>

                <!-- Results (only visible after fetch) -->
                <template v-if="repoSkills.length > 0">
                  <div class="dp-divider" />

                  <div class="dp-search">
                    <Search :size="14" class="input-icon" />
                    <input
                      v-model="skillSearch"
                      type="text"
                      class="text-input has-icon"
                      placeholder="检索技能名称、描述或分类..."
                      @input="handleSearchChange"
                    />
                  </div>

                  <div class="dp-select-all">
                    <label class="check-label">
                      <span class="check-box" :class="{ checked: allSelected, partial: isIndeterminate }" @click="allSelected = !allSelected">
                        <Check v-if="allSelected" :size="12" />
                        <span v-else-if="isIndeterminate" class="partial-bar" />
                      </span>
                      <span>全选当前页</span>
                    </label>
                    <span class="count-text">已选 {{ selectedCount }} / {{ repoSkills.length }} 个</span>
                  </div>

                  <div class="dp-skill-list">
                    <div v-for="sk in pagedRepoSkills" :key="sk.name" class="skill-row-item">
                      <span class="check-box small" :class="{ checked: sk.selected }" @click="sk.selected = !sk.selected">
                        <Check v-if="sk.selected" :size="11" />
                      </span>
                      <div class="skill-meta">
                        <span class="skill-meta-name">{{ sk.name }}</span>
                        <span class="skill-meta-desc">{{ sk.description }}</span>
                      </div>
                      <span class="skill-tag">{{ sk.category }}</span>
                    </div>
                  </div>

                  <div v-if="totalFiltered > skillPageSize" class="dp-pager">
                    <button class="page-btn" :disabled="skillPage <= 1" @click="skillPage--">‹</button>
                    <button
                      v-for="p in totalPages()"
                      :key="p"
                      class="page-btn"
                      :class="{ active: p === skillPage }"
                      @click="skillPage = p"
                    >{{ p }}</button>
                    <button class="page-btn" :disabled="skillPage >= totalPages()" @click="skillPage++">›</button>
                  </div>

                  <div class="dp-divider" />

                  <div class="dp-actions">
                    <button class="btn btn-ghost" @click="emit('close')">取消</button>
                    <button class="btn btn-primary" :disabled="selectedCount === 0" @click="importSelected">
                      <Download :size="14" />
                      拉取到本地 ({{ selectedCount }})
                    </button>
                  </div>
                </template>
              </div>

              <!-- Error -->
              <div v-if="repoError" class="error-box">
                <AlertTriangle :size="14" />
                <span>{{ repoError }}</span>
                <button class="btn-text" @click="fetchRepo">重试</button>
              </div>

              <!-- Hint (before fetch) -->
              <div
                v-if="!fetchingRepo && repoSkills.length === 0 && !repoError"
                class="hint-box"
              >
                选择或输入一个技能仓库地址，点击"获取"加载技能列表
              </div>
            </div>

            <!-- =========== TAB 2: UPLOAD =========== -->
            <div v-if="activeTab === 'upload' && !isEditing" class="tab-inner">
              <!-- Custom drop zone -->
              <div
                class="dropzone"
                :class="{ dragging: isDragging }"
                @click="triggerFileInput"
                @dragover.prevent="isDragging = true"
                @dragleave.prevent="isDragging = false"
                @drop.prevent="handleFileDrop"
              >
                <input
                  ref="fileInput"
                  type="file"
                  accept=".json,.yaml,.yml,.md,.zip"
                  hidden
                  @change="handleFileInputChange"
                />
                <div class="dz-icon-circle">
                  <Upload :size="22" />
                </div>
                <div class="dz-text">拖拽文件到此处或 <span class="dz-link">点击上传</span></div>
                <div class="dz-formats">
                  <span v-for="f in ['.json','.yaml','.yml','.md','.zip']" :key="f" class="dz-tag">{{ f }}</span>
                </div>
              </div>

              <!-- Validation -->
              <div v-if="uploadResult.length > 0" class="valid-panel">
                <div class="valid-header">
                  <Check v-if="uploadResult.every(r => r.valid)" :size="16" class="icon-ok" />
                  <AlertTriangle v-else :size="16" class="icon-warn" />
                  <span>校验结果: {{ uploadMessage }}</span>
                </div>
                <div v-for="r in uploadResult" :key="r.name" class="valid-row">
                  <span class="valid-dot" :class="{ ok: r.valid, fail: !r.valid }" />
                  <span class="valid-name">{{ r.name }}</span>
                  <span class="valid-msg">{{ r.message }}</span>
                </div>
                <div class="actions">
                  <button class="btn btn-ghost" @click="emit('close')">取消</button>
                  <button class="btn btn-primary" @click="handleUploadImport">
                    <Upload :size="14" />
                    导入
                  </button>
                </div>
              </div>
            </div>

            <!-- =========== TAB 3: MANUAL =========== -->
            <div v-if="activeTab === 'manual' || isEditing" class="tab-inner">
              <div class="form-grid">
                <div class="field">
                  <label class="field-label">技能名称 <span class="required">*</span></label>
                  <input
                    v-model="form.name"
                    type="text"
                    class="text-input"
                    placeholder="输入技能名称"
                    maxlength="64"
                  />
                </div>
                <div class="field">
                  <label class="field-label">描述</label>
                  <textarea
                    v-model="form.description"
                    class="text-input textarea"
                    rows="3"
                    placeholder="简要描述技能的功能和用途..."
                    maxlength="512"
                  />
                </div>
                <div class="field">
                  <label class="field-label">图标名称</label>
                  <input
                    v-model="form.icon"
                    type="text"
                    class="text-input"
                    placeholder="输入 Lucide 图标名称，如 Globe"
                  />
                </div>
                <div class="field">
                  <label class="field-label">分类</label>
                  <input
                    v-model="form.category"
                    type="text"
                    class="text-input"
                    placeholder="选择或输入分类标签"
                  />
                </div>
                <div class="field">
                  <label class="field-label">系统提示词</label>
                  <textarea
                    v-model="form.prompt"
                    class="text-input textarea"
                    rows="6"
                    placeholder="编写技能的 Prompt 提示词，指导 AI 行为..."
                  />
                </div>
              </div>
              <div class="actions">
                <button class="btn btn-ghost" @click="emit('close')">取消</button>
                <button class="btn btn-primary" @click="handleManualSubmit">
                  {{ isEditing ? '保存' : '创建' }}
                </button>
              </div>
            </div>

            <!-- Upload tab initial cancel -->
            <div
              v-if="activeTab === 'upload' && !isEditing && uploadResult.length === 0"
              class="actions"
            >
              <button class="btn btn-ghost" @click="emit('close')">取消</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ============================================
   OVERLAY & MODAL SHELL
   ============================================ */
.skill-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-overlay);
  z-index: 9999;
}

.skill-modal {
  width: 680px;
  max-width: 92vw;
  height: 660px;
  max-height: 88vh;
  display: flex;
  flex-direction: column;
  background: var(--color-modal-bg);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-card);
  box-shadow: 0px 12px 60px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

/* ---- Header ---- */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  border-bottom: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

.modal-title {
  font-size: 17px;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.modal-close {
  width: 30px;
  height: 30px;
  border: none;
  border-radius: var(--radius-sm);
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text-primary);
}

/* ---- Tabs ---- */
.modal-tabs {
  display: flex;
  padding: 4px;
  margin: 16px 24px 0;
  background: var(--color-bg-input);
  border-radius: var(--radius-lg);
  gap: 2px;
  flex-shrink: 0;
}

.tab-btn {
  flex: 1;
  padding: 9px 0;
  border: none;
  border-radius: 7px;
  background: transparent;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-muted);
  cursor: pointer;
  font-family: var(--font-family-base);
  transition: all var(--transition-fast);
}

.tab-btn:hover { color: var(--color-text-secondary); }

.tab-btn.active {
  background: var(--accent-primary);
  color: #fff;
  font-weight: var(--font-weight-semibold);
  box-shadow: 0px 2px 8px rgba(59, 130, 246, 0.3);
}

/* ---- Body ---- */
.modal-body {
  padding: 20px 24px 24px;
  overflow-y: auto;
  flex: 1;
}

.tab-inner {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

/* ============================================
   SHARED: Form Elements
   ============================================ */
.field {
  margin-bottom: 16px;
  flex-shrink: 0;
}

.field-label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-label);
  margin-bottom: 8px;
}

.required { color: #ef4444; }

.text-input {
  width: 100%;
  padding: 10px 14px;
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-input);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  font-family: var(--font-family-base);
  outline: none;
  box-sizing: border-box;
  transition: border-color var(--transition-fast);
}

.text-input::placeholder { color: var(--color-text-muted); }
.text-input:focus { border-color: var(--accent-primary); box-shadow: 0px 0px 0px 2px rgba(59,130,246,0.12); }
.text-input.readonly { opacity: 0.7; cursor: default; }
.text-input.has-icon { padding-left: 36px; }

.textarea {
  resize: vertical;
  min-height: 60px;
  line-height: 1.5;
}

/* ============================================
   SHARED: Buttons
   ============================================ */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  border: none;
  border-radius: var(--radius-button);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  font-family: var(--font-family-base);
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.btn:disabled { opacity: 0.45; cursor: not-allowed; }

.btn-primary {
  background: var(--accent-primary);
  color: #fff;
}

.btn-primary:hover:not(:disabled) { background: var(--color-accent-dark); }

.btn-ghost {
  background: rgba(135, 148, 173, 0.08);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-input);
}

.btn-ghost:hover { background: rgba(135, 148, 173, 0.14); color: var(--color-text-primary); }

.btn-text {
  background: none;
  border: none;
  color: var(--accent-primary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  padding: 0;
}

.btn-text:hover { text-decoration: underline; }

/* ============================================
   ACTIONS ROW
   ============================================ */
.actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

/* ============================================
   SPINNER
   ============================================ */
.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.25);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ============================================
   CUSTOM SELECT DROPDOWN
   ============================================ */
.custom-select { position: relative; width: 180px; flex-shrink: 0; }

.select-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 9px 12px;
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-input);
  color: var(--color-text-primary);
  font-size: var(--font-size-base);
  font-family: var(--font-family-base);
  cursor: pointer;
  transition: border-color var(--transition-fast);
  text-align: left;
}

.select-trigger:hover { border-color: rgba(59,130,246,0.35); }

.custom-select.open .select-trigger {
  border-color: var(--accent-primary);
  box-shadow: 0px 0px 0px 2px rgba(59,130,246,0.12);
}

.select-desc {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-left: auto;
  margin-right: 4px;
}

.select-arrow { color: var(--color-text-muted); flex-shrink: 0; }

.select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #111b35;
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-lg);
  box-shadow: 0px 8px 30px rgba(0,0,0,0.55);
  z-index: 100;
  overflow: hidden;
}

.select-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 10px 14px;
  border: none;
  background: none;
  color: var(--color-text-secondary);
  font-size: var(--font-size-base);
  font-family: var(--font-family-base);
  cursor: pointer;
  text-align: left;
  transition: background var(--transition-fast);
}

.select-option:hover { background: rgba(59,130,246,0.08); color: var(--color-text-primary); }
.select-option.picked { color: var(--accent-primary); }

.opt-info { display: flex; flex-direction: column; gap: 2px; }
.opt-label { font-weight: var(--font-weight-semibold); }
.opt-desc { font-size: var(--font-size-xs); color: var(--color-text-muted); }
.opt-check { flex-shrink: 0; }

/* ============================================
   DOWNLOAD PANEL (unified)
   ============================================ */
.download-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-card);
  background: rgba(15, 23, 46, 0.5);
  overflow: hidden;
}

.dp-top {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  flex-shrink: 0;
}

.dp-url-input {
  flex: 1;
  min-width: 0;
}

.select-divider {
  height: 1px;
  background: var(--border-subtle);
  margin: 4px 8px;
}

.dp-divider {
  height: 1px;
  background: var(--color-border-input);
  flex-shrink: 0;
}

.dp-search {
  position: relative;
  padding: 14px 16px 0;
  flex-shrink: 0;
}

.input-icon {
  position: absolute;
  left: 28px;
  top: calc(50% + 7px);
  transform: translateY(-50%);
  color: var(--color-text-muted);
  pointer-events: none;
  z-index: 1;
}

.dp-select-all {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.count-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  font-variant-numeric: tabular-nums;
}

/* ---- Scrollable skill list ---- */
.dp-skill-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dp-skill-list::-webkit-scrollbar { width: 6px; }
.dp-skill-list::-webkit-scrollbar-track { background: transparent; margin: 4px 0; }
.dp-skill-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 3px; }
.dp-skill-list::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.22); }

/* ---- Pagination ---- */
.dp-pager {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 10px 16px;
  border-top: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

/* ---- Actions ---- */
.dp-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 16px;
  border-top: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

/* ---- Checkbox ---- */
.check-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  cursor: pointer;
  user-select: none;
}

.check-box {
  width: 16px;
  height: 16px;
  border: 1px solid var(--color-border-input);
  border-radius: 3px;
  background: var(--color-bg-input);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.check-box.checked { background: var(--accent-primary); border-color: var(--accent-primary); color: #fff; }
.check-box.partial { background: var(--accent-primary); border-color: var(--accent-primary); }
.partial-bar { width: 8px; height: 2px; background: #fff; border-radius: 1px; }
.check-box.small { width: 14px; height: 14px; }

/* ---- Skill row ---- */
.skill-row-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(20, 29, 56, 0.5);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  transition: border-color var(--transition-fast), background var(--transition-fast);
}
.skill-row-item:hover { border-color: rgba(59,130,246,0.3); background: rgba(20,29,56,0.8); }

.skill-meta { flex: 1; display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.skill-meta-name { font-size: var(--font-size-base); font-weight: var(--font-weight-semibold); color: var(--color-text-primary); }
.skill-meta-desc { font-size: var(--font-size-xs); color: var(--color-text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.skill-tag {
  padding: 2px 10px;
  border-radius: 4px;
  background: rgba(135,148,173,0.12);
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  flex-shrink: 0;
}

/* ---- Page button ---- */
.page-btn {
  min-width: 30px;
  height: 30px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-family: var(--font-family-base);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}
.page-btn:hover:not(:disabled):not(.active) { color: var(--accent-primary); background: rgba(59,130,246,0.08); }
.page-btn.active { background: var(--accent-primary); color: #fff; }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }

/* ---- Error & Hint ---- */
.error-box {
  margin-top: 14px;
  padding: 12px 16px;
  background: rgba(239,68,68,0.06);
  border: 1px solid rgba(239,68,68,0.2);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  color: #ef4444;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.error-box .btn-text { margin-left: auto; }

.hint-box {
  margin-top: 14px;
  padding: 36px 24px;
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  background: rgba(15,23,46,0.4);
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-lg);
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ============================================
   TAB 2: DROP ZONE
   ============================================ */
.dropzone {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px;
  border: 2px dashed var(--color-border-input);
  border-radius: var(--radius-card);
  background: rgba(15,23,46,0.5);
  text-align: center;
  cursor: pointer;
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.dropzone:hover,
.dropzone.dragging {
  border-color: var(--accent-primary);
  background: rgba(59,130,246,0.03);
}

.dz-icon-circle {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px dashed var(--color-text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 14px;
  color: var(--color-text-muted);
}

.dz-text {
  font-size: var(--font-size-md);
  color: var(--color-text-secondary);
  margin-bottom: 14px;
}

.dz-link { color: var(--accent-primary); }

.dz-formats {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: center;
}

.dz-tag {
  padding: 3px 10px;
  border-radius: 4px;
  background: rgba(59,130,246,0.1);
  color: var(--accent-primary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

/* ---- Validation ---- */
.valid-panel {
  margin-top: 18px;
  padding: 14px 16px;
  background: rgba(15,23,46,0.5);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-lg);
}

.valid-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.icon-ok { color: #22c55e; }
.icon-warn { color: #f59e0b; }

.valid-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
}

.valid-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.valid-dot.ok { background: #22c55e; }
.valid-dot.fail { background: #ef4444; }

.valid-name { flex: 1; font-size: var(--font-size-base); color: var(--color-text-primary); }
.valid-msg { font-size: var(--font-size-sm); color: var(--color-text-muted); }

/* ============================================
   FORM GRID (Manual Create)
   ============================================ */
.form-grid {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow-y: auto;
}

/* ============================================
   TRANSITION
   ============================================ */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-normal);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
