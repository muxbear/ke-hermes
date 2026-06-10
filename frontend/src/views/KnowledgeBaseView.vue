<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Database, Plus, Search, Filter, FileText, Layers, Network, Activity,
  LayoutGrid, List, Sparkle, Scissors, Hash, Edit2, Trash2, Eye,
} from 'lucide-vue-next'
import { useKnowledgeBaseStore } from '@/stores/knowledgeBase'
import type { KB, ViewMode, CreateKBRequest, IndexConfig } from '@/types/knowledgeBase'
import { KB_STATUS_CONFIG } from '@/types/knowledgeBase'
import { CHUNK_STRATEGY_OPTIONS } from '@/types/knowledgeBase'
import KbStatCard from '@/components/knowledgeBase/KbStatCard.vue'
import KbCard from '@/components/knowledgeBase/KbCard.vue'
import KbCreateDialog from '@/components/knowledgeBase/KbCreateDialog.vue'
import KbDetail from '@/components/knowledgeBase/KbDetail.vue'

const store = useKnowledgeBaseStore()

const createVisible = ref(false)
const confirmDeleteId = ref<string | null>(null)

onMounted(() => {
  store.fetchKbs()
})

onUnmounted(() => {
  store.stopIndexAnimation()
})

// ─── Actions ──────────────────────────────────────────────────────────────

async function handleCreate(data: CreateKBRequest) {
  try {
    const kb = await store.createKb(data)
    ElMessage.success('知识库创建成功')
    store.selectKb(kb.id)
    createVisible.value = false
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '操作失败'
    ElMessage.error(msg)
  }
}

function handleSelectKb(kb: KB) {
  store.selectKb(kb.id)
}

function handleBack() {
  store.clearSelection()
}

async function handleUpdateKb(patch: Partial<KB>) {
  if (!store.selectedKb) return
  try {
    await store.updateKb(store.selectedKb.id, patch)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '更新失败'
    ElMessage.error(msg)
  }
}

async function handleDeleteConfirm(kb: KB) {
  confirmDeleteId.value = kb.id
}

async function handleDeleteExecute() {
  if (!confirmDeleteId.value) return
  try {
    await store.deleteKb(confirmDeleteId.value)
    ElMessage.success('知识库已删除')
    confirmDeleteId.value = null
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '删除失败'
    ElMessage.error(msg)
  }
}

function setViewMode(mode: ViewMode) {
  store.viewMode = mode
}
</script>

<template>
  <div class="kb-page">
    <!-- 详情模式 -->
    <KbDetail
      v-if="store.selectedKb"
      :kb="store.selectedKb"
      @back="handleBack"
      @delete="handleDeleteConfirm(store.selectedKb!)"
      @update="handleUpdateKb"
    />

    <!-- 列表模式 -->
    <template v-else>
      <!-- 页面标题 -->
      <div class="page-header">
        <div class="page-header__info">
          <div class="title-row">
            <div class="title-icon-box">
              <Database :size="20" />
            </div>
            <div>
              <h1>知识库</h1>
              <p>企业多模态 RAG 知识库管理与维护</p>
            </div>
          </div>
        </div>
        <el-button type="primary" size="large" @click="createVisible = true" class="btn-create">
          <Plus :size="16" class="btn-icon" />新建知识库
        </el-button>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-row">
        <KbStatCard
          :icon="Database" color="blue-cyan" label="知识库"
          :value="store.stats.totalKbs" sub="个"
        />
        <KbStatCard
          :icon="FileText" color="purple-pink" label="文档"
          :value="store.stats.totalDocs" sub="篇"
        />
        <KbStatCard
          :icon="Layers" color="emerald-teal" label="分片"
          :value="store.stats.totalChunks.toLocaleString()" sub="块"
        />
        <KbStatCard
          :icon="Network" color="amber-orange" label="实体"
          :value="store.stats.totalEntities.toLocaleString()" sub="个"
        />
        <KbStatCard
          :icon="Activity" color="rose-red" label="索引中"
          :value="store.stats.indexing" sub="任务"
          :pulse="store.stats.indexing > 0"
        />
      </div>

      <!-- 搜索筛选栏 -->
      <div class="toolbar">
        <div class="search-wrap">
          <Search :size="16" class="search-icon" />
          <input
            v-model="store.searchQuery"
            type="text"
            placeholder="按名称、描述、标签检索知识库…"
            class="search-input"
          />
        </div>
        <button class="filter-btn">
          <Filter :size="16" class="btn-icon" />筛选
        </button>
        <div class="view-toggle">
          <button
            :class="['view-btn', { active: store.viewMode === 'grid' }]"
            @click="setViewMode('grid')"
          >
            <LayoutGrid :size="14" />卡片
          </button>
          <button
            :class="['view-btn', { active: store.viewMode === 'list' }]"
            @click="setViewMode('list')"
          >
            <List :size="14" />列表
          </button>
        </div>
      </div>

      <!-- 内容区域（自适应滚动） -->
      <div class="kb-content" v-loading="store.loading">
        <!-- 网格视图 -->
        <div v-if="store.viewMode === 'grid'" class="kb-grid">
          <KbCard
            v-for="kb in store.filteredKbs"
            :key="kb.id"
            :kb="kb"
            @click="handleSelectKb(kb)"
          />
          <div class="create-card" @click="createVisible = true">
            <div class="create-icon-box"><Plus :size="24" /></div>
            <div class="create-text">新建知识库</div>
            <div class="create-sub">向量 + BM25 + 知识图谱</div>
          </div>
          <el-empty
            v-if="store.filteredKbs.length === 0"
            description="暂无匹配的知识库"
          />
        </div>

        <!-- 列表视图 -->
        <div v-else class="kb-table-wrapper">
          <table class="kb-table">
            <thead>
              <tr>
                <th class="col-name">名称</th>
                <th class="col-status">状态</th>
                <th class="col-docs">文档</th>
                <th class="col-chunks">分片</th>
                <th class="col-er">实体 / 关系</th>
                <th class="col-size">大小</th>
                <th class="col-scheme">索引方案</th>
                <th class="col-tags">标签</th>
                <th class="col-date">更新时间</th>
                <th class="col-action">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="kb in store.filteredKbs"
                :key="kb.id"
                class="kb-row"
                @click="handleSelectKb(kb)"
              >
                <td class="col-name">
                  <div class="table-name-cell">
                    <div class="table-kb-icon"><Database :size="16" /></div>
                    <div class="table-name-info">
                      <div class="table-name">{{ kb.name }}</div>
                      <div class="table-name-desc">{{ kb.description }}</div>
                    </div>
                  </div>
                </td>
                <td class="col-status">
                  <el-tag :class="['status-tag', KB_STATUS_CONFIG[kb.status].cls]" size="small" disable-transitions>
                    {{ KB_STATUS_CONFIG[kb.status].label }}
                  </el-tag>
                </td>
                <td class="col-docs cell-num">{{ kb.docs }}</td>
                <td class="col-chunks cell-num">{{ kb.chunks.toLocaleString() }}</td>
                <td class="col-er cell-num">{{ kb.entities.toLocaleString() }} / {{ kb.relations.toLocaleString() }}</td>
                <td class="col-size cell-num">{{ kb.size }}</td>
                <td class="col-scheme">
                  <div class="table-configs">
                    <el-tag size="small" class="config-tag config-blue"><Sparkle :size="10" />{{ kb.config.embeddingModel }}</el-tag>
                    <el-tag v-if="kb.config.sparseAlgo !== 'none'" size="small" class="config-tag config-amber"><Hash :size="10" />{{ kb.config.sparseAlgo.toUpperCase() }}</el-tag>
                    <el-tag v-if="kb.config.enableGraph" size="small" class="config-tag config-green"><Network :size="10" />图谱</el-tag>
                  </div>
                </td>
                <td class="col-tags">
                  <div class="table-tags">
                    <el-tag v-for="t in kb.tags.slice(0, 3)" :key="t" size="small" class="table-tag">{{ t }}</el-tag>
                  </div>
                </td>
                <td class="col-date">{{ kb.updatedAt }}</td>
                <td class="col-action">
                  <button class="action-btn" @click.stop="handleSelectKb(kb)"><Eye :size="14" /></button>
                  <button class="action-btn action-del" @click.stop="handleDeleteConfirm(kb)"><Trash2 :size="14" /></button>
                </td>
              </tr>
              <tr v-if="store.filteredKbs.length === 0">
                <td colspan="10" class="empty-cell">
                  <Database :size="32" class="empty-icon" />
                  <p>暂无匹配的知识库</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- 新建知识库对话框 -->
      <KbCreateDialog
        :visible="createVisible"
        @close="createVisible = false"
        @create="handleCreate"
      />
    </template>

    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="confirmDeleteId"
      :visible="!!confirmDeleteId"
      title="确认删除知识库?"
      width="420px"
      @update:visible="confirmDeleteId = null"
    >
      <template #default>
        <p class="delete-warning">
          将永久删除该知识库及其全部文档、向量、图谱数据。此操作不可撤销。
        </p>
      </template>
      <template #footer>
        <el-button @click="confirmDeleteId = null">取消</el-button>
        <el-button type="danger" @click="handleDeleteExecute">删除</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.kb-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px 32px;
  height: 100%;
  background: var(--surface-primary);
  overflow: hidden;
}

/* Content area with scroll */
.kb-content {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

/* Page Header */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3);
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
  margin: 2px 0 0;
}

.btn-create {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border: none;
}

.btn-create:hover {
  background: linear-gradient(135deg, #2563eb, #7c3aed);
}

/* Stats */
.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
}

/* Toolbar */
.toolbar {
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

.filter-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 36px;
  padding: 0 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-input);
  color: var(--foreground-primary);
  font-size: var(--font-size-base);
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.filter-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
}

.view-toggle {
  display: flex;
  align-items: center;
  background: rgba(15, 23, 46, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-lg);
  padding: 2px;
}

.view-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: 6px;
  font-size: var(--font-size-xs);
  color: var(--foreground-secondary);
  border: 1px solid transparent;
  background: none;
  cursor: pointer;
  transition: all 0.15s;
  font-family: inherit;
}

.view-btn.active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(139, 92, 246, 0.3));
  color: var(--foreground-primary);
  border-color: rgba(59, 130, 246, 0.3);
}

.view-btn:hover:not(.active) {
  color: var(--foreground-primary);
}

/* Grid */
.kb-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.create-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 280px;
  border: 2px dashed rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-card);
  cursor: pointer;
  transition: all 0.2s;
}

.create-card:hover {
  border-color: rgba(59, 130, 246, 0.4);
}

.create-icon-box {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #93c5fd;
}

.create-text {
  font-size: var(--font-size-base);
  color: var(--foreground-primary);
}

.create-sub {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

/* Table */
.kb-table-wrapper {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
  overflow: hidden;
}

.kb-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.kb-table thead {
  background: rgba(0, 0, 0, 0.3);
}

.kb-table thead th {
  padding: 10px 16px;
  text-align: left;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-secondary);
  white-space: nowrap;
  border-bottom: 1px solid var(--border-subtle);
}

.kb-table thead th.col-action {
  text-align: right;
}

.kb-row {
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.kb-row:last-child {
  border-bottom: none;
}

.kb-row:hover {
  background: rgba(255, 255, 255, 0.05);
}

.kb-table td {
  padding: 14px 16px;
  vertical-align: middle;
}

.col-name { min-width: 220px; }
.col-status { width: 90px; }
.col-docs { width: 60px; }
.col-chunks { width: 80px; }
.col-er { width: 110px; }
.col-size { width: 80px; }
.col-scheme { min-width: 200px; }
.col-tags { width: 130px; }
.col-date { width: 100px; }
.col-action { width: 90px; text-align: right; }

.empty-cell {
  text-align: center;
  padding: 64px 0 !important;
  color: var(--foreground-muted);
}

.empty-icon {
  opacity: 0.3;
  margin-bottom: 8px;
}

.empty-cell p {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
}

.table-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.table-kb-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.2));
  border: 1px solid rgba(59, 130, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #93c5fd;
  flex-shrink: 0;
}

.table-name-info {
  min-width: 0;
}

.table-name {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table-name-desc {
  font-size: 11px;
  color: var(--foreground-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 280px;
}

.cell-num {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
}

.cell-text {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
}

.cell-date {
  font-size: var(--font-size-xs);
  color: var(--foreground-secondary);
}

.table-configs {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.config-tag {
  font-size: 10px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
}

.config-blue {
  background: rgba(59, 130, 246, 0.1);
  color: #93c5fd;
  border-color: rgba(59, 130, 246, 0.3);
}

.config-amber {
  background: rgba(245, 158, 11, 0.1);
  color: #fcd34d;
  border-color: rgba(245, 158, 11, 0.3);
}

.config-green {
  background: rgba(16, 185, 129, 0.1);
  color: #6ee7b7;
  border-color: rgba(16, 185, 129, 0.3);
}

.table-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.table-tag {
  background: rgba(100, 116, 139, 0.1);
  color: var(--foreground-primary);
  border-color: rgba(100, 116, 139, 0.3);
  font-size: 10px;
}

.table-actions {
  display: flex;
  gap: 2px;
}

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

.btn-delete {
  color: #f87171;
}

.status-tag {
  display: inline-flex;
  align-items: center;
}

.status-ready {
  background: rgba(16, 185, 129, 0.15);
  color: #6ee7b7;
  border-color: rgba(16, 185, 129, 0.3);
}

.status-indexing {
  background: rgba(59, 130, 246, 0.15);
  color: #93c5fd;
  border-color: rgba(59, 130, 246, 0.3);
}

.status-error {
  background: rgba(244, 63, 94, 0.15);
  color: #fda4af;
  border-color: rgba(244, 63, 94, 0.3);
}

.status-draft {
  background: rgba(100, 116, 139, 0.15);
  color: #94a3b8;
  border-color: rgba(100, 116, 139, 0.3);
}

.delete-warning {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  margin: 0;
}

.btn-icon {
  margin-right: 4px;
}
</style>
