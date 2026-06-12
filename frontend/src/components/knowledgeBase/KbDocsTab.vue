<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Search, Upload, Edit2, Trash2, RefreshCw, FolderOpen,
  FileType2, FileCode2, FileText, FileSpreadsheet, FileImage, Globe,
} from 'lucide-vue-next'
import type { KB, KBDoc, DocType } from '@/types/knowledgeBase'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import KbDocStatusBadge from './KbDocStatusBadge.vue'
import KbUploadDialog from './KbUploadDialog.vue'
import KbIndexingPipeline from './KbIndexingPipeline.vue'

const props = defineProps<{
  kb: KB
}>()

const store = useKnowledgeBaseStore()

const search = ref('')
const uploadVisible = ref(false)
const selectedDoc = ref<KBDoc | null>(null)

const docTypeIcons: Record<DocType, typeof FileText> = {
  pdf: FileType2, md: FileCode2, docx: FileText, csv: FileSpreadsheet, image: FileImage, html: Globe,
}

const filteredDocs = computed(() => {
  const q = search.value.trim().toLowerCase()
  if (!q) return props.kb.documents
  return props.kb.documents.filter((d) => d.name.toLowerCase().includes(q))
})

const uploading = ref(false)

async function handleUpload(files: File[]) {
  uploadVisible.value = false
  try {
    uploading.value = true
    await store.uploadDocs(props.kb.id, files)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '上传失败'
    ElMessage.error(msg)
  } finally {
    uploading.value = false
  }
}

async function handleDelete(docId: string) {
  try {
    await store.deleteDoc(props.kb.id, docId)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '删除失败'
    ElMessage.error(msg)
  }
}

async function handleRetry(docId: string) {
  try {
    await store.retryDoc(props.kb.id, docId)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '重试失败'
    ElMessage.error(msg)
  }
}
</script>

<template>
  <div class="docs-tab">
    <div class="docs-layout" :class="{ 'has-panel': selectedDoc }">
      <div class="docs-table-area">
        <!-- 工具栏 -->
        <div class="docs-toolbar">
          <div class="search-wrap">
            <Search :size="16" class="search-icon" />
            <input
              v-model="search"
              type="text"
              placeholder="检索文档…"
              class="search-input"
            />
          </div>
          <button class="btn-upload" :disabled="uploading" @click="uploadVisible = true">
            <Upload :size="16" class="btn-icon" />{{ uploading ? '上传中…' : '上传文档' }}
          </button>
        </div>

        <!-- 文档表格 -->
        <div class="card">
          <table class="docs-table">
            <thead>
              <tr>
                <th class="col-doc">文档</th>
                <th class="col-size">大小</th>
                <th class="col-chunks">分片</th>
                <th class="col-er">实体/关系</th>
                <th class="col-status">状态</th>
                <th class="col-action">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="doc in filteredDocs"
                :key="doc.id"
                :class="['doc-row', { 'doc-row--sel': selectedDoc?.id === doc.id }]"
                @click="selectedDoc = doc"
              >
                <td>
                  <div class="doc-cell">
                    <component :is="docTypeIcons[doc.type]" :size="16" class="doc-type-icon" />
                    <div class="doc-cell-info">
                      <div class="doc-cell-name">{{ doc.name }}</div>
                      <div class="doc-cell-date">{{ doc.uploadedAt }}</div>
                    </div>
                  </div>
                </td>
                <td class="cell-text">{{ doc.size }}</td>
                <td class="cell-text">{{ doc.chunks || '-' }}</td>
                <td class="cell-text">{{ doc.entities || '-' }} / {{ doc.relations || '-' }}</td>
                <td>
                  <div class="status-cell">
                    <KbDocStatusBadge :status="doc.status" />
                    <el-progress
                      v-if="doc.status !== 'indexed' && doc.status !== 'queued' && doc.status !== 'failed'"
                      :percentage="Math.round(doc.progress)"
                      :stroke-width="3"
                      :show-text="false"
                      class="inline-progress"
                    />
                  </div>
                </td>
                <td class="col-action">
                  <button
                    v-if="doc.status === 'failed'"
                    class="action-btn"
                    @click.stop="handleRetry(doc.id)"
                    title="重试"
                  >
                    <RefreshCw :size="14" />
                  </button>
                  <button class="action-btn" @click.stop title="编辑">
                    <Edit2 :size="14" />
                  </button>
                  <button class="action-btn action-del" @click.stop="handleDelete(doc.id)" title="删除">
                    <Trash2 :size="14" />
                  </button>
                </td>
              </tr>
              <tr v-if="filteredDocs.length === 0">
                <td colspan="6" class="empty-cell">
                  <FolderOpen :size="32" class="empty-icon" />
                  <p>暂无文档，点击右上角上传</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 索引流水线面板 -->
      <div v-if="selectedDoc" class="docs-panel">
        <KbIndexingPipeline :doc="selectedDoc" @close="selectedDoc = null" />
      </div>
    </div>

    <KbUploadDialog
      :visible="uploadVisible"
      @close="uploadVisible = false"
      @upload="handleUpload"
    />
  </div>
</template>

<style scoped>
.docs-tab {
  width: 100%;
  height: 100%;
}

.docs-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  transition: grid-template-columns 0.2s;
  height: 100%;
}

.docs-layout.has-panel {
  grid-template-columns: 7fr 5fr;
}

.docs-table-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
  min-height: 0;
}

.docs-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
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
  color: var(--foreground-secondary);
  pointer-events: none;
  z-index: 1;
}

.search-input {
  width: 100%;
  height: 36px;
  padding: 0 12px 0 36px;
  background: rgba(15, 23, 46, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-input);
  color: var(--foreground-primary);
  font-size: var(--font-size-base);
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.search-input::placeholder {
  color: var(--foreground-muted);
}

.search-input:focus {
  border-color: rgba(59, 130, 246, 0.4);
}

.btn-upload {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 16px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border: none;
  border-radius: var(--radius-input);
  color: #fff;
  font-size: var(--font-size-base);
  font-family: inherit;
  cursor: pointer;
  transition: opacity 0.2s;
  white-space: nowrap;
}

.btn-upload:hover {
  opacity: 0.9;
}

.card {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
  overflow: hidden;
  flex: 1;
  min-height: 0;
}

/* Table */
.docs-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.docs-table thead {
  background: rgba(0, 0, 0, 0.3);
}

.docs-table thead th {
  padding: 10px 16px;
  text-align: left;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-secondary);
  white-space: nowrap;
  border-bottom: 1px solid var(--border-subtle);
}

.docs-table thead th.col-action {
  text-align: right;
}

.doc-row {
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.doc-row:last-child {
  border-bottom: none;
}

.doc-row:hover {
  background: rgba(255, 255, 255, 0.05);
}

.doc-row--sel {
  background: rgba(59, 130, 246, 0.08);
}

.docs-table td {
  padding: 12px 16px;
  vertical-align: middle;
}

.col-doc { min-width: 240px; }
.col-size { width: 90px; }
.col-chunks { width: 70px; }
.col-er { width: 100px; }
.col-status { width: 180px; }
.col-action { width: 110px; text-align: right; }

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--foreground-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--foreground-primary);
}

.action-del:hover {
  color: #f87171;
  background: rgba(244, 63, 94, 0.12);
}

.doc-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-type-icon {
  color: var(--foreground-secondary);
  flex-shrink: 0;
}

.doc-cell-info {
  min-width: 0;
}

.doc-cell-name {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-cell-date {
  font-size: 10px;
  color: var(--foreground-muted);
}

.cell-text {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
}

.status-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.inline-progress {
  width: 100px;
}

.empty-cell {
  text-align: center;
  padding: 48px 0 !important;
  color: var(--foreground-muted);
}

.empty-icon {
  opacity: 0.3;
  margin-bottom: 8px;
}

.empty-cell p {
  margin: 0;
  font-size: var(--font-size-sm);
}

.docs-panel {
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
}

.btn-icon {
  margin-right: 4px;
}
</style>
