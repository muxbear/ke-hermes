<script setup lang="ts">
import { computed } from 'vue'
import {
  FileText, Layers, Network, GitBranch, Activity, Cpu, Tag,
} from 'lucide-vue-next'
import type { KB } from '@/types/knowledgeBase'
import KbStatCard from './KbStatCard.vue'
import KbDocStatusBadge from './KbDocStatusBadge.vue'
import KbConfigSummary from './KbConfigSummary.vue'

const props = defineProps<{
  kb: KB
}>()

const recentDocs = computed(() => props.kb.documents.slice(0, 5))
</script>

<template>
  <div class="overview-tab">
    <div class="overview-grid">
      <!-- 左侧：统计 + 最近活动 -->
      <div class="overview-main">
        <div class="stats-row">
          <KbStatCard
            icon="FileText" color="blue-cyan" label="文档总数"
            :value="kb.docs" sub="篇"
          />
          <KbStatCard
            icon="Layers" color="purple-pink" label="分片"
            :value="kb.chunks" sub="块"
          />
          <KbStatCard
            icon="Network" color="emerald-teal" label="实体"
            :value="kb.entities" sub="个"
          />
          <KbStatCard
            icon="GitBranch" color="amber-orange" label="关系"
            :value="kb.relations" sub="条"
          />
        </div>

        <div class="card">
          <h3 class="card-title"><Activity :size="16" class="title-icon--blue" />最近索引活动</h3>
          <div v-if="recentDocs.length > 0" class="activity-list">
            <div v-for="doc in recentDocs" :key="doc.id" class="activity-item">
              <div class="activity-header">
                <span class="activity-name">{{ doc.name }}</span>
                <KbDocStatusBadge :status="doc.status" />
              </div>
              <el-progress
                :percentage="Math.round(doc.progress)"
                :stroke-width="4"
                :show-text="false"
                class="activity-progress"
              />
            </div>
          </div>
          <div v-else class="empty-text">暂无文档</div>
        </div>
      </div>

      <!-- 右侧：方案 + 标签 -->
      <div class="overview-side">
        <div class="card">
          <h3 class="card-title"><Cpu :size="16" class="title-icon--purple" />当前索引方案</h3>
          <KbConfigSummary :config="kb.config" />
        </div>

        <div class="card">
          <h3 class="card-title"><Tag :size="16" class="title-icon--amber" />标签</h3>
          <div class="tag-list">
            <el-tag
              v-for="t in kb.tags"
              :key="t"
              size="small"
              class="kb-tag"
            >
              {{ t }}
            </el-tag>
            <span v-if="kb.tags.length === 0" class="empty-text">暂无标签</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overview-tab {
  width: 100%;
  height: 100%;
  overflow-y: auto;
}

.overview-grid {
  display: grid;
  grid-template-columns: 8fr 4fr;
  gap: 16px;
}

.overview-main,
.overview-side {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.card {
  padding: 20px;
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
  margin: 0 0 12px;
}

.title-icon--blue { color: #93c5fd; }
.title-icon--purple { color: #c4b5fd; }
.title-icon--amber { color: #fcd34d; }

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.activity-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.activity-name {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
}

.activity-progress {
  width: 100%;
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.kb-tag {
  background: rgba(100, 116, 139, 0.1);
  color: var(--foreground-primary);
  border-color: rgba(100, 116, 139, 0.3);
}

.empty-text {
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
  text-align: center;
  padding: 24px 0;
}
</style>
