<script setup lang="ts">
import { ref } from 'vue'
import {
  Database, ChevronLeft, RefreshCw, Trash2,
  Activity, FileText, Network, FileSearch, Settings2,
} from 'lucide-vue-next'
import type { KB } from '@/types/knowledgeBase'
import { KB_STATUS_CONFIG } from '@/types/knowledgeBase'
import KbOverviewTab from './KbOverviewTab.vue'
import KbDocsTab from './KbDocsTab.vue'
import KbGraphTab from './KbGraphTab.vue'
import KbSearchTab from './KbSearchTab.vue'
import KbConfigTab from './KbConfigTab.vue'

const props = defineProps<{
  kb: KB
}>()

const emit = defineEmits<{
  back: []
  delete: []
  update: [patch: Partial<KB>]
}>()

const activeTab = ref('overview')

const statusCfg = KB_STATUS_CONFIG[props.kb.status]

function handleConfigSave(config: typeof props.kb.config) {
  emit('update', { config })
}
</script>

<template>
  <div class="kb-detail">
    <!-- 粘性顶栏 -->
    <div class="detail-header">
      <div class="detail-header-inner">
        <div class="header-left">
          <el-button text @click="$emit('back')" class="back-btn">
            <ChevronLeft :size="16" />返回
          </el-button>
          <div class="kb-icon-box">
            <Database :size="20" />
          </div>
          <div class="header-info">
            <div class="header-name-row">
              <h1 class="header-name">{{ kb.name }}</h1>
              <el-tag :class="['status-tag', statusCfg.cls]" size="small" disable-transitions>
                {{ statusCfg.label }}
              </el-tag>
            </div>
            <p class="header-desc">{{ kb.description }}</p>
          </div>
        </div>
        <div class="header-actions">
          <el-button>
            <RefreshCw :size="16" class="btn-icon" />重新索引
          </el-button>
          <el-button class="btn-delete" @click="$emit('delete')">
            <Trash2 :size="16" class="btn-icon" />删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- Tab 内容 -->
    <div class="detail-body">
      <el-tabs v-model="activeTab" class="kb-tabs">
        <el-tab-pane name="overview">
          <template #label>
            <Activity :size="14" class="tab-icon" />概览
          </template>
          <KbOverviewTab :kb="kb" />
        </el-tab-pane>

        <el-tab-pane name="docs">
          <template #label>
            <FileText :size="14" class="tab-icon" />文档 ({{ kb.documents.length }})
          </template>
          <KbDocsTab
            :kb="kb"
            @updateDoc="(p) => $emit('update', p)"
            @deleteDoc="(id) => $emit('update', { documents: kb.documents.filter(d => d.id !== id) })"
            @retryDoc="(id) => $emit('update', {
              documents: kb.documents.map(d => d.id === id ? { ...d, status: 'parsing', progress: 5 } : d)
            })"
          />
        </el-tab-pane>

        <el-tab-pane name="graph">
          <template #label>
            <Network :size="14" class="tab-icon" />知识图谱
          </template>
          <KbGraphTab :kb="kb" />
        </el-tab-pane>

        <el-tab-pane name="search">
          <template #label>
            <FileSearch :size="14" class="tab-icon" />检索
          </template>
          <KbSearchTab :kb="kb" />
        </el-tab-pane>

        <el-tab-pane name="config">
          <template #label>
            <Settings2 :size="14" class="tab-icon" />索引配置
          </template>
          <KbConfigTab :config="kb.config" @save="handleConfigSave" />
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<style scoped>
.kb-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--surface-primary);
  overflow: hidden;
}

.detail-header {
  position: sticky;
  top: 0;
  z-index: 30;
  background: rgba(6, 11, 26, 0.85);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-subtle);
}

.detail-header-inner {
  max-width: 1600px;
  margin: 0 auto;
  padding: 16px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  color: var(--foreground-primary);
}

.kb-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.header-info {
  min-width: 0;
}

.header-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
  margin: 0;
}

.status-tag {
  flex-shrink: 0;
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

.header-desc {
  font-size: var(--font-size-xs);
  color: var(--foreground-secondary);
  margin: 2px 0 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.btn-delete {
  color: #fda4af;
  border-color: rgba(244, 63, 94, 0.3);
  background: rgba(244, 63, 94, 0.1);
}

.btn-delete:hover {
  background: rgba(244, 63, 94, 0.2);
}

.detail-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding: 24px 32px;
}

.detail-body :deep(.el-tabs) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.detail-body :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
}

.detail-body :deep(.el-tab-pane) {
  height: 100%;
  overflow-y: auto;
}

.kb-tabs {
  --el-tabs-header-height: 40px;
}

.tab-icon {
  margin-right: 4px;
  vertical-align: -2px;
}

.btn-icon {
  margin-right: 4px;
}
</style>
