<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ChevronLeft, Search, Trash2, Save, X, Check,
  PencilLine, CheckCircle2, Layers,
} from 'lucide-vue-next'
import type { KBDoc } from '@/types/knowledgeBase'

interface DocChunk {
  id: string
  index: number
  content: string
  tokenCount: number
  charCount: number
  pageRef: string
  section: string
  entities: string[]
  edited?: boolean
}

const props = defineProps<{
  doc: KBDoc
  kbId?: string
}>()

const emit = defineEmits<{
  back: []
}>()

// ─── Mock data ────────────────────────────────────────────────────────────────
const CHUNK_SAMPLE_CONTENTS = [
  '本手册旨在规范公司员工的行为准则，明确各项管理制度，保障员工权益，促进公司健康有序发展。所有员工应认真阅读并严格遵守本手册中的各项规定。',
  '员工工作时间为上午9:00至下午18:00，午休时间为12:00至13:00。弹性工作制员工须与直属上司协商确定具体时间安排，并报 HR 备案后执行。',
  '公司实行标准工时制，每周工作5天，每天工作8小时。如需加班，须提前申请并经上级审批。法定节假日加班按国家规定执行三倍工资标准。',
  '基本工资由职位级别、工作年限、个人能力等因素综合确定。绩效奖金根据季度考核结果发放，优秀员工可获得月薪的50%-100%作为额外奖励。',
  '公司为全体员工提供五险一金，包括养老保险、医疗保险、失业保险、工伤保险、生育保险及住房公积金。具体缴纳比例按当地政策执行。',
  '员工每年享有带薪年假，具体天数根据工作年限计算：满1年5天，满3年10天，满5年15天。年假须提前一周申请，由部门主管审批。',
  '所有员工必须遵守公司的保密制度，不得泄露公司的商业秘密、技术资料、客户信息等。离职时需签署保密协议，并归还所有公司资产。',
  '绩效考核采用KPI与OKR相结合的方式，每季度进行一次正式考核。考核结果分为优秀、良好、合格、待改进四个等级。',
  '公司鼓励员工持续学习与发展，每年提供专业培训经费5000元/人。员工可申请参加外部培训、行业会议或学历提升课程。',
]
const CHUNK_SECTIONS = [
  '第一章 总则', '第二章 工作制度', '第三章 薪酬福利',
  '第四章 绩效考核', '第五章 行为规范', '第六章 保密制度',
]
const CHUNK_ENTITY_SETS = [
  ['员工', '公司'], ['HR', '工作制度'], ['薪酬', '绩效'],
  ['五险一金', '福利'], ['年假', '休假'], ['考核', 'KPI'],
]

function generateMockChunks(): DocChunk[] {
  const count = Math.min(Math.max(props.doc.chunks || 12, 1), 20)
  return Array.from({ length: count }, (_, i) => {
    const content = CHUNK_SAMPLE_CONTENTS[i % CHUNK_SAMPLE_CONTENTS.length]
    return {
      id: `${props.doc.id}-ck${i + 1}`,
      index: i + 1,
      content,
      tokenCount: Math.floor(content.length / 2.5 + (i % 3) * 15),
      charCount: content.length,
      pageRef: `第 ${Math.floor(i / 2) + 1} 页`,
      section: CHUNK_SECTIONS[Math.floor(i / 2) % CHUNK_SECTIONS.length],
      entities: [...CHUNK_ENTITY_SETS[i % CHUNK_ENTITY_SETS.length]],
      edited: false,
    }
  })
}

const chunks = ref<DocChunk[]>(generateMockChunks())
const search = ref('')
const editingId = ref<string | null>(null)
const editContent = ref('')
const selected = ref<Set<string>>(new Set())
const savedCount = ref(0)

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return chunks.value
  return chunks.value.filter(
    (c) =>
      c.content.toLowerCase().includes(q) ||
      c.section.toLowerCase().includes(q),
  )
})

const dirtyCount = computed(() => chunks.value.filter((c) => c.edited).length)
const allSelected = computed(() =>
  filtered.value.length > 0 && selected.value.size === filtered.value.length,
)

function startEdit(chunk: DocChunk) {
  editingId.value = chunk.id
  editContent.value = chunk.content
}

function saveEdit(id: string) {
  const idx = chunks.value.findIndex((c) => c.id === id)
  if (idx !== -1) {
    chunks.value[idx] = {
      ...chunks.value[idx],
      content: editContent.value,
      charCount: editContent.value.length,
      tokenCount: Math.ceil(editContent.value.length / 2.5),
      edited: true,
    }
  }
  editingId.value = null
}

function cancelEdit() {
  editingId.value = null
  editContent.value = ''
}

function deleteChunk(id: string) {
  chunks.value = chunks.value.filter((c) => c.id !== id)
  const sel = new Set(selected.value)
  sel.delete(id)
  selected.value = sel
}

function deleteSelected() {
  const ids = new Set(selected.value)
  chunks.value = chunks.value.filter((c) => !ids.has(c.id))
  selected.value = new Set()
}

function toggleSelect(id: string) {
  const sel = new Set(selected.value)
  if (sel.has(id)) {
    sel.delete(id)
  } else {
    sel.add(id)
  }
  selected.value = sel
}

function toggleSelectAll() {
  if (allSelected.value) {
    selected.value = new Set()
  } else {
    selected.value = new Set(filtered.value.map((c) => c.id))
  }
}

function saveAll() {
  const count = dirtyCount.value
  chunks.value = chunks.value.map((c) => ({ ...c, edited: false }))
  savedCount.value = count
  ElMessage.success(`已保存 ${count} 处分片修改`)
  setTimeout(() => { savedCount.value = 0 }, 2500)
}
</script>

<template>
  <div class="doc-edit-view">
    <!-- Header -->
    <div class="edit-header">
      <div class="edit-header-left">
        <button class="back-btn" @click="$emit('back')">
          <ChevronLeft :size="16" />返回文档列表
        </button>
        <div class="header-divider" />
        <div class="edit-title-row">
          <PencilLine :size="16" class="edit-title-icon" />
          <span class="edit-title">编辑分片</span>
          <span class="title-dot">·</span>
          <span class="edit-doc-name">{{ doc.name }}</span>
        </div>
      </div>
      <div class="edit-header-right">
        <span v-if="dirtyCount > 0" class="dirty-indicator">
          <div class="dirty-dot" />
          {{ dirtyCount }} 处未保存
        </span>
        <span v-if="savedCount > 0" class="saved-indicator">
          <CheckCircle2 :size="14" />已保存 {{ savedCount }} 处
        </span>
        <button
          class="save-btn"
          :disabled="dirtyCount === 0"
          @click="saveAll"
        >
          <Save :size="14" />保存更改
        </button>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="edit-toolbar">
      <div class="search-wrap">
        <Search :size="16" class="search-icon" />
        <input
          v-model="search"
          type="text"
          placeholder="搜索分片内容或章节…"
          class="search-input"
        />
      </div>
      <span class="chunk-summary">
        共 {{ chunks.length }} 个分片，显示 {{ filtered.length }} 个
      </span>
      <button
        v-if="selected.size > 0"
        class="delete-selected-btn"
        @click="deleteSelected"
      >
        <Trash2 :size="14" />删除所选 ({{ selected.size }})
      </button>
    </div>

    <!-- Chunk table -->
    <div class="chunk-table">
      <!-- Table header -->
      <div class="table-header">
        <label class="checkbox-cell">
          <input
            type="checkbox"
            :checked="allSelected"
            @change="toggleSelectAll"
          />
        </label>
        <span class="col-index">序号</span>
        <span class="col-content">内容</span>
        <span class="col-token">Token</span>
        <span class="col-chars">字符</span>
        <span class="col-actions">操作</span>
      </div>

      <!-- Table body -->
      <div class="table-body">
        <div
          v-for="chunk in filtered"
          :key="chunk.id"
          :class="['table-row', { 'table-row--sel': selected.has(chunk.id), 'table-row--edited': chunk.edited }]"
        >
          <div class="row-main">
            <label class="checkbox-cell">
              <input
                type="checkbox"
                :checked="selected.has(chunk.id)"
                @change="toggleSelect(chunk.id)"
              />
            </label>
            <div class="col-index">
              <span class="index-badge">#{{ chunk.index }}</span>
              <span v-if="chunk.edited" class="edited-tag">已修改</span>
            </div>
            <div class="col-content">
              <div class="content-meta">{{ chunk.section }} · {{ chunk.pageRef }}</div>
              <template v-if="editingId === chunk.id">
                <textarea
                  v-model="editContent"
                  rows="4"
                  class="edit-textarea"
                  autofocus
                />
                <div class="edit-footer">
                  <span class="edit-counts">
                    {{ editContent.length }} 字符 · ~{{ Math.ceil(editContent.length / 2.5) }} tokens
                  </span>
                  <div class="edit-actions">
                    <button class="edit-btn-cancel" @click="cancelEdit">
                      <X :size="12" />取消
                    </button>
                    <button class="edit-btn-confirm" @click="saveEdit(chunk.id)">
                      <Check :size="12" />确认
                    </button>
                  </div>
                </div>
              </template>
              <p v-else class="content-text">{{ chunk.content }}</p>
              <div v-if="editingId !== chunk.id && chunk.entities.length > 0" class="entity-tags-row">
                <span v-for="e in chunk.entities" :key="e" class="entity-tag">{{ e }}</span>
              </div>
            </div>
            <span class="col-token">{{ chunk.tokenCount }}</span>
            <span class="col-chars">{{ chunk.charCount }}</span>
            <div class="col-actions">
              <button
                v-if="editingId !== chunk.id"
                class="row-action-btn edit-action"
                title="编辑"
                @click="startEdit(chunk)"
              >
                <PencilLine :size="14" />
              </button>
              <button
                v-if="editingId !== chunk.id"
                class="row-action-btn delete-action"
                title="删除"
                @click="deleteChunk(chunk.id)"
              >
                <Trash2 :size="14" />
              </button>
            </div>
          </div>
        </div>
        <div v-if="filtered.length === 0" class="table-empty">
          <Layers :size="32" class="empty-icon" />
          <div>没有匹配的分片</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.doc-edit-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
  min-height: 0;
}

/* Header */
.edit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.edit-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: #cbd5e1;
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: color 0.15s;
}

.back-btn:hover {
  color: #fff;
}

.header-divider {
  width: 1px;
  height: 20px;
  background: rgba(255, 255, 255, 0.1);
}

.edit-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.edit-title-icon {
  color: #fcd34d;
}

.edit-title {
  font-size: 14px;
  color: #fff;
}

.title-dot {
  color: #64748b;
}

.edit-doc-name {
  font-size: 14px;
  color: #94a3b8;
}

.edit-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.dirty-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #fcd34d;
}

.dirty-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #fbbf24;
  animation: dot-pulse 1.5s ease-in-out infinite;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}

.saved-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #6ee7b7;
}

.save-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 14px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.2s;
}

.save-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.save-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Toolbar */
.edit-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.search-wrap {
  position: relative;
  flex: 1;
}

.search-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  color: #94a3b8;
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 36px;
  padding: 0 12px 0 36px;
  background: rgba(15, 23, 46, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  color: #f2f5fa;
  font-size: 13px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.search-input::placeholder {
  color: #596680;
}

.search-input:focus {
  border-color: rgba(59, 130, 246, 0.4);
}

.chunk-summary {
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
}

.delete-selected-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 12px;
  background: rgba(244, 63, 94, 0.1);
  border: 1px solid rgba(244, 63, 94, 0.3);
  border-radius: 8px;
  color: #fda4af;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}

.delete-selected-btn:hover {
  background: rgba(244, 63, 94, 0.2);
}

/* Chunk table */
.chunk-table {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  background: rgba(15, 23, 46, 0.4);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
  min-height: 0;
}

.table-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 12px;
  color: #94a3b8;
  flex-shrink: 0;
}

.table-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.table-body::-webkit-scrollbar {
  width: 4px;
}

.table-body::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.table-row {
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background-color 0.15s;
}

.table-row:last-child {
  border-bottom: none;
}

.table-row:hover {
  background: rgba(255, 255, 255, 0.02);
}

.table-row--sel {
  background: rgba(59, 130, 246, 0.05);
}

.table-row--edited {
  border-left: 2px solid rgba(245, 158, 11, 0.6);
}

.row-main {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
}

/* Column widths */
.checkbox-cell {
  display: flex;
  align-items: flex-start;
  padding-top: 2px;
  flex-shrink: 0;
}

.checkbox-cell input[type="checkbox"] {
  width: 14px;
  height: 14px;
  cursor: pointer;
  accent-color: #3b82f6;
}

.col-index {
  width: 56px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.index-badge {
  display: inline-block;
  font-size: 10px;
  padding: 0 6px;
  height: 16px;
  line-height: 16px;
  border-radius: 4px;
  background: rgba(100, 116, 139, 0.1);
  color: #94a3b8;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.edited-tag {
  font-size: 9px;
  color: #fbbf24;
  white-space: nowrap;
}

.col-content {
  flex: 1;
  min-width: 0;
}

.content-meta {
  font-size: 10px;
  color: #64748b;
  margin-bottom: 6px;
}

.content-text {
  margin: 0;
  font-size: 13px;
  color: #cbd5e1;
  line-height: 1.6;
}

.edit-textarea {
  width: 100%;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(59, 130, 246, 0.4);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 13px;
  font-family: inherit;
  line-height: 1.6;
  resize: none;
  outline: none;
  box-sizing: border-box;
}

.edit-textarea:focus {
  border-color: rgba(59, 130, 246, 0.6);
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.3);
}

.edit-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.edit-counts {
  font-size: 10px;
  color: #64748b;
}

.edit-actions {
  display: flex;
  gap: 6px;
}

.edit-btn-cancel {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 28px;
  padding: 0 10px;
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  border-radius: 6px;
}

.edit-btn-cancel:hover {
  color: #fff;
}

.edit-btn-confirm {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 28px;
  padding: 0 10px;
  border: 1px solid rgba(59, 130, 246, 0.3);
  background: rgba(59, 130, 246, 0.2);
  color: #93c5fd;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  border-radius: 6px;
}

.edit-btn-confirm:hover {
  background: rgba(59, 130, 246, 0.3);
}

.entity-tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 8px;
}

.entity-tag {
  font-size: 9px;
  padding: 0 6px;
  height: 14px;
  line-height: 14px;
  border-radius: 4px;
  background: rgba(168, 85, 247, 0.1);
  color: #c4b5fd;
  border: 1px solid rgba(168, 85, 247, 0.2);
}

.col-token {
  width: 64px;
  flex-shrink: 0;
  text-align: right;
  font-size: 12px;
  color: #64748b;
  padding-top: 4px;
}

.col-chars {
  width: 64px;
  flex-shrink: 0;
  text-align: right;
  font-size: 12px;
  color: #64748b;
  padding-top: 4px;
}

.col-actions {
  width: 80px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
}

.row-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s;
}

.edit-action {
  color: #60a5fa;
}

.edit-action:hover {
  background: rgba(59, 130, 246, 0.15);
  color: #93c5fd;
}

.delete-action {
  color: #f87171;
}

.delete-action:hover {
  background: rgba(244, 63, 94, 0.15);
  color: #fda4af;
}

.table-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 0;
  color: #64748b;
  font-size: 13px;
  gap: 8px;
}

.empty-icon {
  opacity: 0.4;
}
</style>
