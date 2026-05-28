<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, shallowRef } from 'vue'
import * as echarts from 'echarts'
import {
  Users,
  Activity,
  BarChart3,
  Server,
  Wrench,
  Zap,
  Target,
  Bot,
  Layers,
  Globe,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  Shield,
  MessageSquare,
  RefreshCw,
  Clock,
} from 'lucide-vue-next'

/* ---- Types ---- */
type Period = 'day' | 'month' | 'year'
type EventType = 'info' | 'success' | 'warn' | 'error'

interface StatCard {
  label: string
  value: string | number
  sub?: string
  icon: typeof Users
  trend?: number
  iconBg: string
  borderColor: string
}

interface ResourceItem {
  label: string
  value: string
  icon: typeof Wrench
  color: string
  borderColor: string
}

interface TopUser {
  name: string
  role: string
  calls: number
  tokens: string
  online: boolean
}

interface ModelProvider {
  name: string
  models: number
  color: string
  icon: string
  usage: number
  popular: string
}

interface SystemMetric {
  label: string
  value: string
  pct: number
  color: string
}

interface LogEvent {
  time: string
  type: EventType
  msg: string
  icon: typeof Bot
}

/* ---- State ---- */
const period = ref<Period>('day')
const currentTime = ref(new Date())
let clockTimer: ReturnType<typeof setInterval> | null = null

const chartRef = shallowRef<HTMLDivElement | null>(null)
const pieRef = shallowRef<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null
let pieInstance: echarts.ECharts | null = null

/* ---- Mock Data ---- */
const dailyData = [
  { time: '00:00', users: 12, requests: 45 },
  { time: '02:00', users: 5, requests: 18 },
  { time: '04:00', users: 3, requests: 10 },
  { time: '06:00', users: 8, requests: 28 },
  { time: '08:00', users: 34, requests: 124 },
  { time: '10:00', users: 67, requests: 289 },
  { time: '12:00', users: 82, requests: 341 },
  { time: '14:00', users: 91, requests: 378 },
  { time: '16:00', users: 76, requests: 312 },
  { time: '18:00', users: 54, requests: 218 },
  { time: '20:00', users: 39, requests: 156 },
  { time: '22:00', users: 21, requests: 88 },
]

const monthlyData = [
  { time: '1日', users: 420, requests: 1840 },
  { time: '5日', users: 510, requests: 2210 },
  { time: '10日', users: 680, requests: 2890 },
  { time: '15日', users: 590, requests: 2540 },
  { time: '20日', users: 730, requests: 3120 },
  { time: '25日', users: 820, requests: 3560 },
  { time: '30日', users: 760, requests: 3280 },
]

const yearlyData = [
  { time: '1月', users: 3200, requests: 14200 },
  { time: '2月', users: 3800, requests: 16800 },
  { time: '3月', users: 4200, requests: 18400 },
  { time: '4月', users: 5100, requests: 22400 },
  { time: '5月', users: 6800, requests: 29800 },
  { time: '6月', users: 7200, requests: 31200 },
  { time: '7月', users: 6500, requests: 28400 },
  { time: '8月', users: 7800, requests: 34100 },
  { time: '9月', users: 8200, requests: 35800 },
  { time: '10月', users: 9100, requests: 39800 },
  { time: '11月', users: 10200, requests: 44500 },
  { time: '12月', users: 11400, requests: 49800 },
]

const modelProviders: ModelProvider[] = [
  { name: 'OpenAI', models: 8, color: '#10B981', icon: '🤖', usage: 42, popular: 'GPT-4o' },
  { name: 'Anthropic', models: 5, color: '#8B5CF6', icon: '⚡', usage: 31, popular: 'Claude 3.5' },
  { name: 'Google', models: 6, color: '#3B82F6', icon: '🌐', usage: 15, popular: 'Gemini 1.5' },
  { name: 'Mistral', models: 4, color: '#F59E0B', icon: '💨', usage: 7, popular: 'Mistral Large' },
  { name: 'Ollama', models: 12, color: '#EC4899', icon: '🦙', usage: 5, popular: 'Llama 3.1' },
]

const topUsers: TopUser[] = [
  { name: 'wangke', role: '管理员', calls: 1482, tokens: '2.8M', online: true },
  { name: 'lihua', role: '开发者', calls: 934, tokens: '1.6M', online: true },
  { name: 'zhangwei', role: '分析师', calls: 721, tokens: '1.2M', online: false },
  { name: 'chenyan', role: '开发者', calls: 618, tokens: '0.9M', online: true },
  { name: 'wuming', role: '测试员', calls: 389, tokens: '0.6M', online: false },
]

const recentEvents: LogEvent[] = [
  { time: '14:32:11', type: 'info', msg: 'Agent main-alpha 完成任务 #2841', icon: Bot },
  { time: '14:31:58', type: 'success', msg: '技能 web-search 调用成功，耗时 1.2s', icon: Zap },
  { time: '14:30:44', type: 'info', msg: '新会话建立：用户 user_4821', icon: MessageSquare },
  { time: '14:29:03', type: 'warn', msg: '定时任务 report-gen 执行延迟 3.1s', icon: Target },
  { time: '14:27:51', type: 'success', msg: '模型切换：GPT-4o → Claude 3.5 Sonnet', icon: RefreshCw },
  { time: '14:25:30', type: 'info', msg: 'MCP 工具 file-reader 注册成功', icon: Wrench },
  { time: '14:23:17', type: 'error', msg: 'Agent sub-beta 连接超时，已自动重试', icon: Activity },
  { time: '14:21:05', type: 'success', msg: '定时任务 data-sync 执行完成', icon: Target },
]

const systemMetrics: SystemMetric[] = [
  { label: 'API 响应时间', value: '128ms', pct: 85, color: '#6366F1' },
  { label: 'CPU 使用率', value: '34%', pct: 34, color: '#10B981' },
  { label: '内存占用', value: '2.1GB / 8GB', pct: 26, color: '#8B5CF6' },
  { label: '磁盘使用率', value: '48%', pct: 48, color: '#F59E0B' },
  { label: '成功率', value: '99.2%', pct: 99, color: '#10B981' },
]

/* ---- Computed ---- */
const timeStr = computed(() =>
  currentTime.value.toLocaleTimeString('zh-CN', { hour12: false }),
)
const dateStr = computed(() =>
  currentTime.value.toLocaleDateString('zh-CN', {
    year: 'numeric', month: 'long', day: 'numeric', weekday: 'long',
  }),
)

const statCards: StatCard[] = [
  {
    label: '注册用户总数', value: '1,284', sub: '本月新增 +128',
    icon: Users, trend: 12, iconBg: 'indigo', borderColor: 'rgba(99,102,241,0.2)',
  },
  {
    label: '今日活跃用户', value: '247', sub: '峰值 91 人 · 14:00',
    icon: Activity, trend: 8, iconBg: 'purple', borderColor: 'rgba(139,92,246,0.2)',
  },
  {
    label: '今日总请求数', value: '2,089', sub: '~382K tokens',
    icon: BarChart3, trend: -3, iconBg: 'blue', borderColor: 'rgba(59,130,246,0.2)',
  },
  {
    label: '系统运行时长', value: '19d 4h', sub: '上次重启 2026-05-09',
    icon: Server, iconBg: 'emerald', borderColor: 'rgba(16,185,129,0.2)',
  },
]

const resourceItems: ResourceItem[] = [
  { label: '总工具数', value: '63', icon: Wrench, color: '#F59E0B', borderColor: 'rgba(245,158,11,0.2)' },
  { label: '活跃技能', value: '19 / 63', icon: Zap, color: '#8B5CF6', borderColor: 'rgba(139,92,246,0.2)' },
  { label: '定时任务', value: '8', icon: Target, color: '#3B82F6', borderColor: 'rgba(59,130,246,0.2)' },
  { label: '主代理', value: '4', icon: Bot, color: '#6366F1', borderColor: 'rgba(99,102,241,0.2)' },
  { label: '子代理', value: '12', icon: Layers, color: '#EC4899', borderColor: 'rgba(236,72,153,0.2)' },
  { label: 'MCP 服务', value: '6', icon: Globe, color: '#10B981', borderColor: 'rgba(16,185,129,0.2)' },
]

/* ---- Chart Options ---- */
function makeAreaChartOptions(data: typeof dailyData): echarts.EChartsOption {
  return {
    grid: { top: 8, right: 16, left: 40, bottom: 8 },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.time),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#6B7280', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#1F2937', type: 'dashed' } },
      axisLabel: { color: '#6B7280', fontSize: 11 },
    },
    tooltip: {
      backgroundColor: '#111827',
      borderColor: '#374151',
      textStyle: { color: '#fff', fontSize: 12 },
    },
    series: [
      {
        name: '活跃用户',
        type: 'line',
        data: data.map((d) => d.users),
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#6366F1', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99,102,241,0.5)' },
            { offset: 1, color: 'rgba(99,102,241,0)' },
          ]),
        },
      },
      {
        name: '请求数',
        type: 'line',
        data: data.map((d) => d.requests),
        smooth: true,
        symbol: 'none',
        lineStyle: { color: '#8B5CF6', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(139,92,246,0.4)' },
            { offset: 1, color: 'rgba(139,92,246,0)' },
          ]),
        },
      },
    ],
  }
}

function makePieChartOptions(): echarts.EChartsOption {
  const pieData = modelProviders.map((p) => ({ name: p.name, value: p.usage }))
  return {
    series: [
      {
        type: 'pie',
        radius: ['55%', '80%'],
        center: ['50%', '50%'],
        data: pieData,
        label: { show: false },
        emphasis: { scale: false },
        itemStyle: {
          borderColor: '#111827',
          borderWidth: 3,
        },
        color: modelProviders.map((p) => p.color),
      },
    ],
    tooltip: {
      backgroundColor: '#111827',
      borderColor: '#374151',
      textStyle: { color: '#fff', fontSize: 12 },
      formatter: (params: { name: string; value: number }) =>
        `${params.name}: ${params.value}%`,
    },
  }
}

/* ---- Lifecycle ---- */
function initChart() {
  if (chartRef.value && !chartInstance) {
    chartInstance = echarts.init(chartRef.value)
    updateChart()
  }
  if (pieRef.value && !pieInstance) {
    pieInstance = echarts.init(pieRef.value)
    pieInstance.setOption(makePieChartOptions())
  }
}

function updateChart() {
  if (!chartInstance) return
  const data = period.value === 'day' ? dailyData : period.value === 'month' ? monthlyData : yearlyData
  chartInstance.setOption(makeAreaChartOptions(data), true)
}

function handleResize() {
  chartInstance?.resize()
  pieInstance?.resize()
}

watch(period, () => updateChart())

onMounted(() => {
  clockTimer = setInterval(() => {
    currentTime.value = new Date()
  }, 1000)
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  pieInstance?.dispose()
})

/* ---- Helpers ---- */
function formatLargeNum(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K'
  return String(n)
}

function eventColor(type: EventType): string {
  const map: Record<EventType, string> = {
    info: 'var(--color-accent)',
    success: '#10B981',
    warn: '#F59E0B',
    error: '#EF4444',
  }
  return map[type]
}

function eventBgColor(type: EventType): string {
  const map: Record<EventType, string> = {
    info: 'rgba(59,130,246,0.1)',
    success: 'rgba(16,185,129,0.1)',
    warn: 'rgba(245,158,11,0.1)',
    error: 'rgba(239,68,68,0.1)',
  }
  return map[type]
}

function eventDotColor(type: EventType): string {
  const map: Record<EventType, string> = {
    info: '#3B82F6',
    success: '#10B981',
    warn: '#F59E0B',
    error: '#EF4444',
  }
  return map[type]
}
</script>

<template>
  <div class="overview-page">
    <!-- ═══ Page Header ═══ -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">概览</h1>
        <p class="page-subtitle">平台状态、用户洞察与资源分布</p>
      </div>
      <div class="header-right">
        <p class="header-time">{{ timeStr }}</p>
        <p class="header-date">{{ dateStr }}</p>
        <div class="header-status">
          <span class="status-dot" />
          <span class="status-text">系统正常运行</span>
        </div>
      </div>
    </div>

    <!-- ═══ Top KPI Cards ═══ -->
    <div class="stat-grid">
      <div
        v-for="card in statCards"
        :key="card.label"
        class="stat-card"
        :style="{ borderColor: card.borderColor }"
      >
        <div class="stat-card-inner">
          <div class="stat-card-body">
            <span class="stat-label">{{ card.label }}</span>
            <span class="stat-value">{{ card.value }}</span>
            <span v-if="card.sub" class="stat-sub">{{ card.sub }}</span>
            <div v-if="card.trend !== undefined" class="stat-trend" :class="card.trend >= 0 ? 'up' : 'down'">
              <ArrowUpRight v-if="card.trend >= 0" :size="12" />
              <ArrowDownRight v-else :size="12" />
              {{ Math.abs(card.trend) }}% 较昨日
            </div>
          </div>
          <div class="stat-icon-wrap" :class="`icon-${card.iconBg}`">
            <component :is="card.icon" :size="20" />
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Resource Cards ═══ -->
    <div class="resource-grid">
      <div
        v-for="item in resourceItems"
        :key="item.label"
        class="resource-card"
        :style="{ borderColor: item.borderColor }"
      >
        <component :is="item.icon" :size="20" :color="item.color" class="res-icon" />
        <span class="res-label">{{ item.label }}</span>
        <span class="res-value" :style="{ color: item.color }">{{ item.value }}</span>
      </div>
    </div>

    <!-- ═══ Usage Chart + Personnel ═══ -->
    <div class="chart-row">
      <!-- Chart -->
      <div class="chart-card chart-span-2">
        <div class="chart-card-header">
          <div>
            <h3 class="card-title">用户使用频次</h3>
            <p class="card-desc">活跃用户 & 请求数趋势</p>
          </div>
          <div class="period-tabs">
            <button
              v-for="p in (['day', 'month', 'year'] as Period[])"
              :key="p"
              class="period-tab"
              :class="{ active: period === p }"
              @click="period = p"
            >
              {{ p === 'day' ? '日' : p === 'month' ? '月' : '年' }}
            </button>
          </div>
        </div>
        <div ref="chartRef" class="chart-container"></div>
        <div class="chart-legend">
          <span class="legend-item">
            <span class="legend-line" style="background: #6366F1" />
            活跃用户
          </span>
          <span class="legend-item">
            <span class="legend-line" style="background: #8B5CF6" />
            请求数
          </span>
        </div>
      </div>

      <!-- Personnel -->
      <div class="chart-card">
        <h3 class="card-title">人员概况</h3>
        <p class="card-desc">按调用量排行</p>
        <div class="personnel-list">
          <div v-for="(u, i) in topUsers" :key="u.name" class="personnel-row">
            <span class="personnel-rank">{{ i + 1 }}</span>
            <div class="personnel-avatar">{{ u.name[0].toUpperCase() }}</div>
            <div class="personnel-info">
              <div class="personnel-name-row">
                <span class="personnel-name">{{ u.name }}</span>
                <span v-if="u.online" class="online-dot" />
              </div>
              <span class="personnel-role">{{ u.role }}</span>
            </div>
            <div class="personnel-stats">
              <span class="personnel-calls">{{ u.calls.toLocaleString() }} 次</span>
              <span class="personnel-tokens">{{ u.tokens }}</span>
            </div>
          </div>
        </div>
        <div class="personnel-summary">
          <div class="summary-item">
            <span class="summary-num">24</span>
            <span class="summary-label">总成员</span>
          </div>
          <div class="summary-item">
            <span class="summary-num online">8</span>
            <span class="summary-label">在线</span>
          </div>
          <div class="summary-item">
            <span class="summary-num admin">5</span>
            <span class="summary-label">管理员</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ Model Providers + Token ═══ -->
    <div class="provider-row">
      <!-- Providers -->
      <div class="chart-card">
        <h3 class="card-title">模型提供商</h3>
        <p class="card-desc">
          共 {{ modelProviders.reduce((a, b) => a + b.models, 0) }} 个模型 ·
          {{ modelProviders.length }} 个提供商
        </p>
        <div class="provider-list">
          <div v-for="p in modelProviders" :key="p.name" class="provider-item">
            <span class="provider-icon">{{ p.icon }}</span>
            <div class="provider-meta">
              <div class="provider-top">
                <span class="provider-name">{{ p.name }}</span>
                <span class="provider-models">{{ p.models }} 个模型</span>
              </div>
              <div class="provider-bar-track">
                <div
                  class="provider-bar-fill"
                  :style="{ width: `${p.usage}%`, background: p.color }"
                />
              </div>
              <div class="provider-bottom">
                <span class="provider-popular">热门: {{ p.popular }}</span>
                <span class="provider-usage" :style="{ color: p.color }">{{ p.usage }}% 使用率</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pie + Token -->
      <div class="chart-card">
        <h3 class="card-title">使用分布</h3>
        <p class="card-desc">各提供商调用占比</p>
        <div class="pie-section">
          <div ref="pieRef" class="pie-container"></div>
          <div class="pie-legend">
            <div v-for="p in modelProviders" :key="p.name" class="pie-legend-item">
              <span class="pie-dot" :style="{ background: p.color }" />
              <span class="pie-name">{{ p.name }}</span>
              <span class="pie-pct">{{ p.usage }}%</span>
            </div>
          </div>
        </div>
        <div class="token-bar">
          <div class="token-item">
            <span class="token-label">今日 Token 消耗</span>
            <span class="token-value">382,400</span>
          </div>
          <div class="token-item">
            <span class="token-label">月累计</span>
            <span class="token-value accent">5.64M</span>
          </div>
          <div class="token-icon">
            <TrendingUp :size="18" />
          </div>
        </div>
      </div>
    </div>

    <!-- ═══ System Health + Event Log ═══ -->
    <div class="bottom-row">
      <!-- System Health -->
      <div class="chart-card">
        <h3 class="card-title">系统健康</h3>
        <div class="health-list">
          <div v-for="m in systemMetrics" :key="m.label" class="health-item">
            <div class="health-top">
              <span class="health-label">{{ m.label }}</span>
              <span class="health-value">{{ m.value }}</span>
            </div>
            <div class="health-bar-track">
              <div
                class="health-bar-fill"
                :style="{ width: `${m.pct}%`, background: m.color }"
              />
            </div>
          </div>
        </div>
        <div class="health-status">
          <Shield :size="16" />
          <span>所有核心服务运行正常</span>
        </div>
      </div>

      <!-- Event Log -->
      <div class="chart-card event-log-card">
        <div class="chart-card-header">
          <div class="event-title-row">
            <h3 class="card-title">实时事件日志</h3>
            <span class="live-badge">
              <span class="live-dot" />
              LIVE
            </span>
          </div>
          <span class="event-count">{{ recentEvents.length }} 条最新事件</span>
        </div>
        <div class="event-list">
          <div
            v-for="(ev, i) in recentEvents"
            :key="i"
            class="event-row"
            :style="{ background: eventBgColor(ev.type) }"
          >
            <span class="event-dot" :style="{ background: eventDotColor(ev.type) }" />
            <component :is="ev.icon" :size="14" :color="eventDotColor(ev.type)" class="event-icon" />
            <span class="event-msg" :style="{ color: eventDotColor(ev.type) }">{{ ev.msg }}</span>
            <span class="event-time">{{ ev.time }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overview-page {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
  background: var(--surface-primary);
}

/* ---- Page Header ---- */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(90deg, #818CF8, #A78BFA, #60A5FA);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  margin-top: 4px;
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
}

.header-right {
  text-align: right;
}

.header-time {
  font-size: 20px;
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #A5B4FC;
}

.header-date {
  margin-top: 2px;
  font-size: 11px;
  color: var(--foreground-muted);
}

.header-status {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 6px;
  margin-top: 4px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10B981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.status-text {
  font-size: 11px;
  color: #10B981;
}

/* ---- KPI Cards ---- */
.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: var(--surface-card);
  border: 1px solid;
  border-radius: var(--radius-xl);
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: -24px;
  right: -24px;
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(129, 140, 248, 0.2), transparent);
  pointer-events: none;
}

.stat-card-inner {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  position: relative;
}

.stat-card-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--foreground-primary);
}

.stat-sub {
  font-size: 11px;
  color: #596680;
}

.stat-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
}

.stat-trend.up { color: #10B981; }
.stat-trend.down { color: #EF4444; }

.stat-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.icon-indigo { background: #4F46E5; }
.icon-purple { background: #7C3AED; }
.icon-blue { background: #2563EB; }
.icon-emerald { background: #059669; }

/* ---- Resource Cards ---- */
.resource-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.resource-card {
  background: var(--surface-card);
  border: 1px solid;
  border-radius: var(--radius-xl);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.res-icon {
  flex-shrink: 0;
}

.res-label {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.res-value {
  font-size: 20px;
  font-weight: 700;
}

/* ---- Chart Row ---- */
.chart-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.chart-span-2 {
  /* handled by grid column */
}

.chart-card {
  background: var(--surface-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 20px;
}

.chart-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-title {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--foreground-primary);
}

.card-desc {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin-top: 4px;
}

.period-tabs {
  display: flex;
  gap: 2px;
  background: rgba(255,255,255,0.04);
  padding: 3px;
  border-radius: var(--radius-lg);
}

.period-tab {
  padding: 4px 12px;
  font-size: var(--font-size-xs);
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.15s ease;
}

.period-tab:hover { color: var(--foreground-primary); }

.period-tab.active {
  background: #4F46E5;
  color: #fff;
}

.chart-container {
  width: 100%;
  height: 220px;
}

.chart-legend {
  display: flex;
  gap: 16px;
  margin-top: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.legend-line {
  display: inline-block;
  width: 16px;
  height: 2px;
  border-radius: 1px;
}

/* ---- Personnel ---- */
.personnel-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.personnel-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.personnel-rank {
  width: 16px;
  font-size: var(--font-size-xs);
  color: #596680;
  text-align: center;
  flex-shrink: 0;
}

.personnel-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6366F1, #8B5CF6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-xs);
  font-weight: 700;
  color: #fff;
  flex-shrink: 0;
}

.personnel-info {
  flex: 1;
  min-width: 0;
}

.personnel-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.personnel-name {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.online-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10B981;
  flex-shrink: 0;
}

.personnel-role {
  font-size: 11px;
  color: var(--foreground-muted);
}

.personnel-stats {
  text-align: right;
  flex-shrink: 0;
}

.personnel-calls {
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: #A5B4FC;
  display: block;
}

.personnel-tokens {
  font-size: 11px;
  color: var(--foreground-muted);
}

.personnel-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 16px;
  padding: 12px;
  background: rgba(255,255,255,0.03);
  border-radius: var(--radius-lg);
}

.summary-item {
  text-align: center;
}

.summary-num {
  font-size: var(--font-size-md);
  font-weight: 700;
  color: var(--foreground-primary);
  display: block;
}

.summary-num.online { color: #10B981; }
.summary-num.admin { color: #A5B4FC; }

.summary-label {
  font-size: 11px;
  color: var(--foreground-muted);
}

/* ---- Provider Row ---- */
.provider-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.provider-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 12px;
}

.provider-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.provider-icon { font-size: 18px; flex-shrink: 0; }

.provider-meta { flex: 1; min-width: 0; }

.provider-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.provider-name {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
}

.provider-models {
  font-size: 11px;
  color: var(--foreground-muted);
}

.provider-bar-track {
  height: 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 3px;
  overflow: hidden;
}

.provider-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.7s ease;
}

.provider-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 2px;
}

.provider-popular { font-size: 10px; color: #596680; }

.provider-usage {
  font-size: 10px;
  font-weight: 500;
}

/* ---- Pie Section ---- */
.pie-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 8px;
}

.pie-container {
  width: 180px;
  height: 180px;
  flex-shrink: 0;
}

.pie-legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pie-legend-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pie-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.pie-name {
  flex: 1;
  font-size: var(--font-size-xs);
  color: var(--foreground-secondary);
  margin-left: 8px;
}

.pie-pct {
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--foreground-primary);
}

.token-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 12px;
  padding: 12px 16px;
  background: linear-gradient(90deg, rgba(79,70,229,0.15), rgba(139,92,246,0.15));
  border: 1px solid rgba(99,102,241,0.2);
  border-radius: var(--radius-xl);
}

.token-item {
  display: flex;
  flex-direction: column;
}

.token-label {
  font-size: 11px;
  color: var(--foreground-muted);
}

.token-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--foreground-primary);
  margin-top: 2px;
}

.token-value.accent { color: #A5B4FC; }

.token-icon {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: rgba(79,70,229,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #A5B4FC;
  margin-left: auto;
}

/* ---- Bottom Row ---- */
.bottom-row {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 16px;
}

/* ---- Health ---- */
.health-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.health-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.health-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.health-label {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.health-value {
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--foreground-primary);
}

.health-bar-track {
  height: 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 3px;
  overflow: hidden;
}

.health-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.7s ease;
}

.health-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 8px 12px;
  background: rgba(16,185,129,0.08);
  border: 1px solid rgba(16,185,129,0.2);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-xs);
  color: #10B981;
}

/* ---- Event Log ---- */
.event-log-card .chart-card-header {
  margin-bottom: 12px;
}

.event-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.live-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  background: rgba(79,70,229,0.2);
  border-radius: var(--radius-full);
  font-size: 10px;
  font-weight: 600;
  color: #A5B4FC;
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #A5B4FC;
  animation: pulse 2s infinite;
}

.event-count {
  font-size: 11px;
  color: #596680;
}

.event-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 260px;
  overflow-y: auto;
  padding-right: 4px;
}

.event-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-lg);
}

.event-icon { flex-shrink: 0; }

.event-msg {
  flex: 1;
  font-size: var(--font-size-xs);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.event-time {
  font-size: 11px;
  font-family: 'Courier New', monospace;
  color: #596680;
  flex-shrink: 0;
}

/* ---- Responsive ---- */
@media (max-width: 1400px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .resource-grid { grid-template-columns: repeat(3, 1fr); }
  .chart-row { grid-template-columns: 1fr; }
  .provider-row { grid-template-columns: 1fr; }
  .bottom-row { grid-template-columns: 1fr; }
}
</style>
