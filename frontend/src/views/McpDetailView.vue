<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, Download, Star, Clock, Check, ExternalLink } from 'lucide-vue-next'
import { useMcpStore } from '@/stores/mcp'
import { MCP_CATEGORY_LABELS } from '@/types/mcp'

const route = useRoute()
const router = useRouter()
const mcpStore = useMcpStore()

const activeTab = ref('overview')

const tabs = [
  { key: 'overview', label: '概述' },
  { key: 'config', label: '配置' },
  { key: 'usage', label: '使用说明' },
  { key: 'reviews', label: '评价' },
]

function goBack() {
  router.push({ name: 'mcp-square' })
}

function handleInstall() {
  const tool = mcpStore.currentTool
  if (!tool) return
  if (tool.installed) {
    mcpStore.uninstallTool(tool.id)
  } else {
    mcpStore.installTool(tool.id)
  }
}

function formatInstallCount(count: number): string {
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}K`
  }
  return String(count)
}

onMounted(() => {
  const id = route.params.id as string
  mcpStore.fetchToolById(id)
})

watch(
  () => route.params.id,
  (newId) => {
    if (newId) mcpStore.fetchToolById(newId as string)
  },
)
</script>

<template>
  <div class="mcp-detail">
    <div v-if="mcpStore.detailLoading" class="loading-wrap">
      <el-skeleton :rows="10" animated />
    </div>

    <template v-else-if="mcpStore.currentTool">
      <!-- Breadcrumb -->
      <div class="breadcrumb">
        <button class="back-link" @click="goBack">
          <ArrowLeft :size="16" />
          返回 MCP 广场
        </button>
        <span class="sep">/</span>
        <span class="current-page">{{ mcpStore.currentTool.name }}</span>
      </div>

      <!-- Header Card -->
      <div class="header-card">
        <div class="header-left">
          <div class="large-icon">
            <span class="large-icon-text">{{ mcpStore.currentTool.icon }}</span>
          </div>
          <div class="header-info">
            <div class="name-row">
              <h1 class="tool-name">{{ mcpStore.currentTool.name }}</h1>
              <span v-if="mcpStore.currentTool.official" class="official-badge">官方</span>
              <span class="version-badge">{{ mcpStore.currentTool.version }}</span>
            </div>
            <div class="meta-row">
              <span>{{ mcpStore.currentTool.author }}</span>
              <span class="meta-sep">·</span>
              <span>
                <Download :size="13" />
                {{ formatInstallCount(mcpStore.currentTool.installs) }} 次安装
              </span>
              <span class="meta-sep">·</span>
              <span class="rating-meta">
                <Star :size="13" />
                {{ mcpStore.currentTool.rating }}
              </span>
              <span class="meta-sep">·</span>
              <span>
                <Clock :size="13" />
                {{ mcpStore.currentTool.updated_at }}
              </span>
            </div>
          </div>
        </div>
        <button
          class="install-btn-lg"
          :class="{ installed: mcpStore.currentTool.installed }"
          @click="handleInstall"
        >
          {{ mcpStore.currentTool.installed ? '已安装' : '安装' }}
        </button>
      </div>

      <!-- Tab Bar -->
      <div class="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Overview Tab -->
        <div v-if="activeTab === 'overview'" class="two-columns">
          <div class="left-col">
            <div class="content-card">
              <h3 class="card-title">简介</h3>
              <p class="card-desc">{{ mcpStore.currentTool.description }}</p>
            </div>

            <div class="content-card">
              <h3 class="card-title">核心功能</h3>
              <ul class="feature-list">
                <li v-for="(feat, i) in mcpStore.currentTool.features" :key="i">
                  <Check :size="14" class="check-icon" />
                  {{ feat }}
                </li>
              </ul>
            </div>
          </div>

          <div class="right-col">
            <div class="content-card">
              <h3 class="card-title">信息</h3>
              <div class="info-list">
                <div class="info-row">
                  <span class="info-label">版本</span>
                  <span class="info-value">{{ mcpStore.currentTool.version }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">作者</span>
                  <span class="info-value">{{ mcpStore.currentTool.author }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">许可证</span>
                  <span class="info-value">{{ mcpStore.currentTool.license }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">仓库</span>
                  <a class="info-value link" href="#">
                    {{ mcpStore.currentTool.repository }}
                    <ExternalLink :size="11" />
                  </a>
                </div>
                <div class="info-row">
                  <span class="info-label">分类</span>
                  <span class="info-value">
                    {{ MCP_CATEGORY_LABELS[mcpStore.currentTool.category] || mcpStore.currentTool.category }}
                  </span>
                </div>
                <div class="info-row">
                  <span class="info-label">更新</span>
                  <span class="info-value">{{ mcpStore.currentTool.updated_at }}</span>
                </div>
              </div>
            </div>

            <div class="content-card">
              <h3 class="card-title">分类标签</h3>
              <div class="tags-row">
                <span
                  v-for="tag in mcpStore.currentTool.tags"
                  :key="tag"
                  class="tag"
                >
                  {{ tag }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Config Tab -->
        <div v-if="activeTab === 'config'" class="content-card">
          <h3 class="card-title">配置参数</h3>
          <div v-if="mcpStore.currentTool.config_schema.length > 0" class="config-list">
            <div
              v-for="field in mcpStore.currentTool.config_schema"
              :key="field.name"
              class="config-row"
            >
              <div class="config-header">
                <span class="config-name">{{ field.name }}</span>
                <span v-if="field.required" class="required-badge">必填</span>
                <span class="config-type">{{ field.type }}</span>
              </div>
              <p class="config-desc">{{ field.description }}</p>
            </div>
          </div>
          <el-empty v-else description="暂无配置参数" />
        </div>

        <!-- Usage Tab -->
        <div v-if="activeTab === 'usage'" class="content-card">
          <h3 class="card-title">使用说明</h3>
          <p class="card-desc">安装完成后，MCP 工具将自动在智能体会话中可用。你可以通过以下方式使用：</p>
          <div class="info-list">
            <div class="info-row">
              <span class="info-label">安装方式</span>
              <span class="info-value">一键安装</span>
            </div>
            <div class="info-row">
              <span class="info-label">运行环境</span>
              <span class="info-value">Docker 容器</span>
            </div>
            <div class="info-row">
              <span class="info-label">自动启动</span>
              <span class="info-value">是</span>
            </div>
          </div>
        </div>

        <!-- Reviews Tab -->
        <div v-if="activeTab === 'reviews'" class="content-card">
          <h3 class="card-title">用户评价</h3>
          <el-empty description="暂无评价" />
        </div>
      </div>
    </template>

    <div v-else class="empty-wrap">
      <el-empty :description="mcpStore.error || '未找到该 MCP 工具'"">
        <el-button @click="goBack">返回 MCP 广场</el-button>
      </el-empty>
    </div>
  </div>
</template>

<style scoped>
.mcp-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px 32px;
  height: 100%;
  overflow-y: auto;
  background: var(--surface-primary);
}

.loading-wrap,
.empty-wrap {
  padding: 48px 0;
}

/* Breadcrumb */
.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-md);
}

.back-link {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  color: var(--accent-primary);
  font-size: var(--font-size-md);
  cursor: pointer;
  padding: 0;
}

.back-link:hover {
  opacity: 0.8;
}

.sep {
  color: var(--foreground-muted);
}

.current-page {
  color: var(--foreground-secondary);
}

/* Header Card */
.header-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 32px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.large-icon {
  width: 72px;
  height: 72px;
  border-radius: 16px;
  background: rgba(59, 130, 246, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.large-icon-text {
  font-size: 36px;
  line-height: 1;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tool-name {
  font-size: 20px;
  font-weight: var(--font-weight-bold);
  color: var(--foreground-primary);
  margin: 0;
}

.official-badge {
  font-size: 11px;
  font-weight: var(--font-weight-semibold);
  color: var(--accent-primary);
  background: rgba(59, 130, 246, 0.15);
  padding: 4px 10px;
  border-radius: 6px;
}

.version-badge {
  font-size: 11px;
  color: var(--foreground-secondary);
  background: rgba(38, 51, 89, 0.3);
  padding: 4px 10px;
  border-radius: 6px;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-md);
  color: var(--foreground-secondary);
  flex-wrap: wrap;
}

.meta-row :deep(svg) {
  vertical-align: -2px;
}

.meta-sep {
  color: var(--foreground-muted);
}

.rating-meta {
  color: #f59e0b;
}

.install-btn-lg {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 24px;
  border-radius: 12px;
  border: none;
  background: var(--accent-primary);
  color: #fff;
  font-size: 16px;
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition: background var(--transition-fast);
  flex-shrink: 0;
}

.install-btn-lg:hover {
  background: #2563eb;
}

.install-btn-lg.installed {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

/* Tab Bar */
.tab-bar {
  display: flex;
  gap: 0;
  padding: 4px;
  background: var(--surface-card);
  border-radius: 12px;
}

.tab-btn {
  padding: 10px 20px;
  border-radius: 10px;
  border: none;
  background: none;
  color: var(--foreground-secondary);
  font-size: var(--font-size-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.tab-btn:hover {
  color: var(--foreground-primary);
}

.tab-btn.active {
  background: rgba(59, 130, 246, 0.2);
  color: var(--accent-primary);
  font-weight: var(--font-weight-semibold);
}

/* Two Column Layout */
.two-columns {
  display: flex;
  gap: 24px;
}

.left-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

.right-col {
  width: 340px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex-shrink: 0;
}

/* Content Cards */
.content-card {
  padding: 24px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
}

.card-title {
  font-size: 16px;
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0 0 16px;
}

.card-desc {
  font-size: var(--font-size-md);
  color: var(--foreground-secondary);
  line-height: 1.7;
  margin: 0;
}

/* Feature List */
.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.feature-list li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: var(--font-size-md);
  color: var(--foreground-secondary);
  line-height: 1.5;
}

.check-icon {
  color: #22c55e;
  margin-top: 3px;
  flex-shrink: 0;
}

/* Info List */
.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.info-label {
  font-size: var(--font-size-base);
  color: var(--foreground-secondary);
}

.info-value {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
}

.info-value.link {
  color: var(--accent-primary);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-value.link:hover {
  text-decoration: underline;
}

/* Tags */
.tags-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  background: rgba(38, 51, 89, 0.2);
  padding: 6px 12px;
  border-radius: 8px;
}

/* Config */
.config-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-row {
  padding: 16px;
  background: var(--surface-secondary);
  border-radius: 10px;
}

.config-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.config-name {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  font-family: 'JetBrains Mono', monospace;
}

.required-badge {
  font-size: var(--font-size-xs);
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}

.config-type {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  background: rgba(38, 51, 89, 0.3);
  padding: 2px 6px;
  border-radius: 4px;
}

.config-desc {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
  margin: 0;
}
</style>
