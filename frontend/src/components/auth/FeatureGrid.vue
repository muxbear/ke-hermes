<script setup lang="ts">
import { h, type FunctionalComponent } from 'vue'
import {
  Sparkles,
  Database,
  Terminal,
  Globe,
  ShieldCheck,
  Cpu,
  Timer,
  Settings,
  type LucideIcon,
} from 'lucide-vue-next'
import type { FeatureItem } from '@/types/components'

const iconMap: Record<string, LucideIcon> = {
  sparkles: Sparkles,
  database: Database,
  terminal: Terminal,
  globe: Globe,
  'shield-check': ShieldCheck,
  cpu: Cpu,
  timer: Timer,
  settings: Settings,
}

const features: FeatureItem[] = [
  { icon: 'sparkles', title: '自我进化与技能沉淀', description: '技能沉淀，越用越强' },
  { icon: 'database', title: '持久记忆系统', description: '三层架构，跨会话延续' },
  { icon: 'terminal', title: '丰富的工具生态', description: '40+ 工具，MCP 扩展' },
  { icon: 'globe', title: '全平台消息网关', description: '15+ 平台，指令直达' },
  { icon: 'shield-check', title: '安全与隐私', description: '沙盒隔离，零数据收集' },
  { icon: 'cpu', title: '子智能体与并行处理', description: '子智能体，多线推进' },
  { icon: 'timer', title: '调度与自动化', description: 'Cron 定时，自动推送' },
  { icon: 'settings', title: '模型灵活可切换', description: '多提供商，热切换' },
]
</script>

<template>
  <div class="feature-grid">
    <div v-for="feat in features" :key="feat.title" class="feature-item">
      <div class="feature-icon">
        <component :is="iconMap[feat.icon]" :size="20" />
      </div>
      <div class="feature-text">
        <span class="feature-title">{{ feat.title }}</span>
        <span class="feature-desc">{{ feat.description }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--size-feature-row-gap) var(--size-feature-col-gap);
  width: 100%;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: var(--size-feature-icon-text-gap);
}

.feature-icon {
  width: var(--size-feature-icon);
  height: var(--size-feature-icon);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-accent);
  opacity: 0.85;
  flex-shrink: 0;
}

.feature-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.feature-title {
  font-size: var(--font-size-feature-title);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  line-height: 1.25;
}

.feature-desc {
  font-size: var(--font-size-feature-desc);
  color: var(--color-text-secondary);
  line-height: 1.3;
}
</style>
