<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Edit3, Trash2, X, CheckCircle2, AlertCircle,
  Eye, EyeOff, Bot, Cpu, Zap, Settings2, Activity,
} from 'lucide-vue-next'
import { useModelStore } from '@/stores/model'
import type { Provider, AIModel, ModelType, ModelStatus, ModelParam } from '@/types/model'
import {
  MODEL_TYPE_META, MODEL_STATUS_META, PROVIDER_STATUS_META,
} from '@/types/model'

const store = useModelStore()

/* ---- Modal state ---- */
const editingProvider = ref<Provider | null>(null)
const showNewProvider = ref(false)
const editingModel = ref<AIModel | null>(null)
const showNewModel = ref(false)
const viewingModel = ref<AIModel | null>(null)
const deleteTarget = ref<{ type: 'provider' | 'model'; id: string; name: string } | null>(null)

/* ---- Provider form ---- */
const providerForm = ref({ name: '', logo: '🤖', apiBase: '', apiKey: '', description: '', website: '' })
const showApiKey = ref(false)

function openNewProvider() {
  providerForm.value = { name: '', logo: '🤖', apiBase: '', apiKey: '', description: '', website: '' }
  showApiKey.value = false
  showNewProvider.value = true
}

function openEditProvider(p: Provider) {
  providerForm.value = { name: p.name, logo: p.logo, apiBase: p.apiBase, apiKey: p.apiKey, description: p.description, website: p.website }
  editingProvider.value = p
  showApiKey.value = false
}

async function handleSaveProvider() {
  if (!providerForm.value.name.trim() || !providerForm.value.apiBase.trim()) return
  try {
    const data: Provider = {
      id: editingProvider.value?.id ?? `p${Date.now()}`,
      ...providerForm.value,
      status: (editingProvider.value?.status ?? 'unconfigured') as Provider['status'],
      models: editingProvider.value?.models ?? [],
    }
    await store.saveProvider(data)
    ElMessage.success(editingProvider.value ? '提供商已更新' : '提供商已添加')
    editingProvider.value = null
    showNewProvider.value = false
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  }
}

function closeProviderModal() {
  editingProvider.value = null
  showNewProvider.value = false
}

/* ---- Model form ---- */
const modelForm = ref({
  displayName: '', name: '', type: 'llm' as ModelType,
  status: 'active' as ModelStatus, contextWindow: undefined as number | undefined,
  description: '', params: [] as ModelParam[],
})

function openNewModel() {
  modelForm.value = {
    displayName: '', name: '', type: 'llm', status: 'active',
    contextWindow: undefined, description: '',
    params: [
      { key: 'temperature', label: 'Temperature', value: 0.7, min: 0, max: 2, step: 0.1, type: 'number' },
      { key: 'max_tokens', label: 'Max Tokens', value: 4096, min: 1, max: 32768, step: 1, type: 'number' },
    ],
  }
  showNewModel.value = true
}

function openEditModel(m: AIModel) {
  modelForm.value = {
    displayName: m.displayName, name: m.name, type: m.type,
    status: m.status, contextWindow: m.contextWindow, description: m.description,
    params: m.params.map((p) => ({ ...p })),
  }
  editingModel.value = m
}

async function handleSaveModel() {
  if (!modelForm.value.name.trim() || !modelForm.value.displayName.trim()) return
  if (!store.selectedProvider) return
  try {
    const data: AIModel = {
      id: editingModel.value?.id ?? `m${Date.now()}`,
      ...modelForm.value,
      usedByAgents: editingModel.value?.usedByAgents ?? [],
      callCount: editingModel.value?.callCount ?? 0,
      contextWindow: modelForm.value.contextWindow,
    }
    await store.saveModel(store.selectedProvider.id, data)
    ElMessage.success(editingModel.value ? '模型已更新' : '模型已添加')
    editingModel.value = null
    showNewModel.value = false
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '保存失败')
  }
}

function closeModelModal() {
  editingModel.value = null
  showNewModel.value = false
}

function updateParam(key: string, value: number | string) {
  modelForm.value.params = modelForm.value.params.map((p) =>
    p.key === key ? { ...p, value } : p,
  )
}

/* ---- Delete ---- */
function confirmDelete(type: 'provider' | 'model', id: string, name: string) {
  deleteTarget.value = { type, id, name }
}

async function handleDelete() {
  if (!deleteTarget.value) return
  try {
    if (deleteTarget.value.type === 'provider') {
      await store.deleteProvider(deleteTarget.value.id)
      ElMessage.success('提供商已删除')
    } else {
      if (!store.selectedProvider) return
      await store.deleteModel(store.selectedProvider.id, deleteTarget.value.id)
      ElMessage.success('模型已删除')
    }
  } catch (err: unknown) {
    ElMessage.error(err instanceof Error ? err.message : '删除失败')
  }
  deleteTarget.value = null
}

/* ---- Helpers ---- */
function formatContext(w: number | undefined): string {
  if (!w) return '—'
  if (w >= 1000000) return `${(w / 1000000).toFixed(0)}M`
  if (w >= 1000) return `${(w / 1000).toFixed(0)}K`
  return String(w)
}

function paramLabel(k: string): string {
  if (k === 'temperature') return 'Temperature'
  if (k === 'max_tokens') return 'Max Tokens'
  if (k === 'top_p') return 'Top P'
  return k
}

/* ---- Lifecycle ---- */
onMounted(() => {
  store.fetchAll()
})
</script>

<template>
  <div class="models-page">
    <!-- ═══ Page Header ═══ -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">模型</h1>
        <p class="page-subtitle">AI 大模型提供商与模型管理中心</p>
      </div>
      <button class="btn-primary" @click="openNewProvider">
        <Plus :size="16" />
        添加提供商
      </button>
    </div>

    <!-- ═══ Stats Row ═══ -->
    <div class="stats-row">
      <div class="stat-chip">
        <Cpu :size="16" color="#a5b4fc" />
        <span class="stat-chip-label">提供商</span>
        <span class="stat-chip-value">{{ store.providers.length }}</span>
      </div>
      <div class="stat-chip">
        <Zap :size="16" color="#c4b5fd" />
        <span class="stat-chip-label">模型总数</span>
        <span class="stat-chip-value">{{ store.totalModels }}</span>
      </div>
      <div class="stat-divider" />
      <button
        v-for="(count, type) in store.typeCounts"
        :key="type"
        class="stat-chip stat-chip--clickable"
        :class="{ active: store.modelTypeFilter === type }"
        :style="store.modelTypeFilter === type ? { background: MODEL_TYPE_META[type].bg, borderColor: MODEL_TYPE_META[type].border, color: MODEL_TYPE_META[type].color } : {}"
        @click="store.modelTypeFilter = store.modelTypeFilter === type ? 'all' : type"
      >
        {{ MODEL_TYPE_META[type].emoji }} {{ MODEL_TYPE_META[type].label }}
        <span class="stat-chip-value">{{ count }}</span>
      </button>
    </div>

    <!-- ═══ Two-panel body ═══ -->
    <div class="panels">
      <!-- ── Left: Provider List ──────────────────────────────────────────── -->
      <div class="panel-left">
        <div class="panel-left-search">
          <Search :size="14" class="search-icon" />
          <input
            v-model="store.providerSearch"
            type="text"
            placeholder="搜索提供商…"
            class="search-input"
          />
        </div>
        <div class="panel-left-list">
          <div
            v-for="p in store.filteredProviders"
            :key="p.id"
            class="provider-item"
            :class="{ active: store.selectedProviderId === p.id }"
            @click="store.selectProvider(p.id)"
          >
            <span class="provider-logo">{{ p.logo }}</span>
            <div class="provider-info">
              <p class="provider-name">{{ p.name }}</p>
              <div class="provider-meta">
                <span
                  class="provider-dot"
                  :style="{ background: PROVIDER_STATUS_META[p.status].dot }"
                />
                <span :style="{ color: PROVIDER_STATUS_META[p.status].color }">
                  {{ PROVIDER_STATUS_META[p.status].label }}
                </span>
                <span class="provider-count">· {{ p.models.length }} 个模型</span>
              </div>
            </div>
            <div class="provider-actions">
              <button class="action-btn" title="编辑" @click.stop="openEditProvider(p)">
                <Edit3 :size="12" />
              </button>
              <button class="action-btn action-btn--danger" title="删除" @click.stop="confirmDelete('provider', p.id, p.name)">
                <Trash2 :size="12" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Right: Provider Detail ──────────────────────────────────────── -->
      <div v-if="store.selectedProvider" class="panel-right">
        <!-- Provider header -->
        <div class="provider-header">
          <div class="provider-header-top">
            <div class="provider-header-info">
              <span class="provider-header-logo">{{ store.selectedProvider.logo }}</span>
              <div>
                <div class="provider-header-name-row">
                  <h2 class="provider-header-name">{{ store.selectedProvider.name }}</h2>
                  <span
                    class="provider-status-dot"
                    :style="{ background: PROVIDER_STATUS_META[store.selectedProvider.status].dot }"
                  />
                  <span :style="{ color: PROVIDER_STATUS_META[store.selectedProvider.status].color, fontSize: 'var(--font-size-xs)' }">
                    {{ PROVIDER_STATUS_META[store.selectedProvider.status].label }}
                  </span>
                </div>
                <p class="provider-header-desc">{{ store.selectedProvider.description }}</p>
              </div>
            </div>
            <div class="provider-header-extras">
              <span class="provider-api-base">{{ store.selectedProvider.apiBase }}</span>
              <button class="btn-secondary" @click="openEditProvider(store.selectedProvider)">
                <Settings2 :size="14" />
                配置
              </button>
            </div>
          </div>

          <!-- Tabs -->
          <div class="provider-tabs">
            <button
              class="provider-tab"
              :class="{ active: store.rightTab === 'models' }"
              @click="store.setRightTab('models')"
            >
              模型列表
            </button>
            <button
              class="provider-tab"
              :class="{ active: store.rightTab === 'usage' }"
              @click="store.setRightTab('usage')"
            >
              使用统计
            </button>
          </div>
        </div>

        <!-- Tab content -->
        <div class="tab-content">
          <!-- ── Models Tab ──────────────────────────────────────────────── -->
          <template v-if="store.rightTab === 'models'">
            <!-- Toolbar -->
            <div class="models-toolbar">
              <div class="search-wrap">
                <Search :size="14" class="search-icon" />
                <input
                  v-model="store.modelSearch"
                  type="text"
                  placeholder="搜索模型名称或 ID…"
                  class="search-input"
                />
              </div>
              <div class="type-filters">
                <button
                  class="type-filter"
                  :class="{ active: store.modelTypeFilter === 'all' }"
                  @click="store.modelTypeFilter = 'all'"
                >
                  全部
                </button>
                <button
                  v-for="(count, type) in store.providerTypeCounts"
                  :key="type"
                  class="type-filter"
                  :class="{ active: store.modelTypeFilter === type }"
                  :style="store.modelTypeFilter === type ? { background: MODEL_TYPE_META[type].bg, color: MODEL_TYPE_META[type].color } : {}"
                  @click="store.modelTypeFilter = store.modelTypeFilter === type ? 'all' : type"
                >
                  {{ MODEL_TYPE_META[type].emoji }} {{ MODEL_TYPE_META[type].label }}
                </button>
              </div>
              <button class="btn-add-model" @click="openNewModel">
                <Plus :size="14" />
                添加模型
              </button>
            </div>

            <!-- Table header -->
            <div class="model-table-header">
              <span class="col-name">模型</span>
              <span class="col-type">类型</span>
              <span class="col-ctx">上下文</span>
              <span class="col-status">状态</span>
              <span class="col-calls">调用次数</span>
              <span class="col-actions">操作</span>
            </div>

            <!-- Empty -->
            <div v-if="store.filteredModels.length === 0" class="empty-state">
              <Cpu :size="40" class="empty-icon" />
              <p class="empty-title">暂无匹配的模型</p>
              <p class="empty-desc">尝试清除搜索条件或添加新模型</p>
            </div>

            <!-- Model rows -->
            <div class="model-rows">
              <div
                v-for="m in store.filteredModels"
                :key="m.id"
                class="model-row"
              >
                <div class="model-name-cell">
                  <p class="model-display-name">{{ m.displayName }}</p>
                  <p class="model-id">{{ m.name }}</p>
                </div>
                <span
                  class="model-type-badge"
                  :style="{
                    color: MODEL_TYPE_META[m.type].color,
                    background: MODEL_TYPE_META[m.type].bg,
                    borderColor: MODEL_TYPE_META[m.type].border,
                  }"
                >
                  {{ MODEL_TYPE_META[m.type].emoji }} {{ MODEL_TYPE_META[m.type].label }}
                </span>
                <span class="model-ctx">{{ formatContext(m.contextWindow) }}</span>
                <span
                  class="model-status-badge"
                  :style="{
                    color: MODEL_STATUS_META[m.status].color,
                    background: MODEL_STATUS_META[m.status].bg.split(' ')[0],
                    border: MODEL_STATUS_META[m.status].bg.split(' ').slice(1).join(' '),
                  }"
                >
                  {{ MODEL_STATUS_META[m.status].label }}
                </span>
                <div class="model-calls">
                  <span class="calls-num">{{ m.callCount.toLocaleString() }}</span>
                  <span v-if="m.usedByAgents.length > 0" class="calls-agents">
                    <Bot :size="12" />{{ m.usedByAgents.length }}
                  </span>
                </div>
                <div class="model-actions">
                  <button title="查看详情" class="action-btn" @click="viewingModel = m">
                    <Activity :size="14" />
                  </button>
                  <button title="编辑" class="action-btn" @click="openEditModel(m)">
                    <Edit3 :size="14" />
                  </button>
                  <button title="删除" class="action-btn action-btn--danger" @click="confirmDelete('model', m.id, m.displayName)">
                    <Trash2 :size="14" />
                  </button>
                </div>
              </div>
            </div>
          </template>

          <!-- ── Usage Tab ────────────────────────────────────────────────── -->
          <template v-if="store.rightTab === 'usage'">
            <div class="usage-stats">
              <div class="usage-stat-card">
                <p class="usage-stat-label">模型总数</p>
                <p class="usage-stat-value">{{ store.providerStats.total }}</p>
              </div>
              <div class="usage-stat-card">
                <p class="usage-stat-label">总调用次数</p>
                <p class="usage-stat-value usage-stat-value--indigo">{{ store.providerStats.totalCalls }}</p>
              </div>
              <div class="usage-stat-card">
                <p class="usage-stat-label">正在使用</p>
                <p class="usage-stat-value usage-stat-value--emerald">{{ store.providerStats.inUse }}</p>
              </div>
              <div class="usage-stat-card">
                <p class="usage-stat-label">已弃用</p>
                <p class="usage-stat-value usage-stat-value--gray">{{ store.providerStats.deprecated }}</p>
              </div>
            </div>

            <div class="usage-ranking">
              <div class="usage-ranking-header">
                <h3>各模型调用量排行</h3>
              </div>
              <div class="usage-ranking-list">
                <div
                  v-for="(m, i) in [...store.selectedProvider.models].sort((a, b) => b.callCount - a.callCount)"
                  :key="m.id"
                  class="usage-rank-row"
                >
                  <span class="rank-num">{{ i + 1 }}</span>
                  <span class="rank-emoji" :style="{ color: MODEL_TYPE_META[m.type].color }">
                    {{ MODEL_TYPE_META[m.type].emoji }}
                  </span>
                  <div class="rank-info">
                    <div class="rank-name-row">
                      <span class="rank-name">{{ m.displayName }}</span>
                      <span class="rank-calls">{{ m.callCount.toLocaleString() }} 次</span>
                    </div>
                    <div class="rank-bar-track">
                      <div
                        class="rank-bar-fill"
                        :style="{
                          width: `${(m.callCount / Math.max(...store.selectedProvider.models.map(x => x.callCount), 1)) * 100}%`,
                        }"
                      />
                    </div>
                  </div>
                  <div class="rank-agents">
                    <span
                      v-for="a in m.usedByAgents"
                      :key="a"
                      class="rank-agent-tag"
                    >{{ a }}</span>
                    <span v-if="m.usedByAgents.length === 0" class="rank-no-agent">无代理</span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- Empty state when no provider selected -->
      <div v-else class="panel-right panel-right--empty">
        <Cpu :size="48" class="empty-big-icon" />
        <p>请选择一个模型提供商</p>
      </div>
    </div>

    <!-- ═══ Edit Provider Modal ═══ -->
    <Teleport to="body">
      <div v-if="showNewProvider || editingProvider" class="modal-overlay" @click.self="closeProviderModal">
        <div class="modal-card">
          <div class="modal-header">
            <div>
              <h2 class="modal-title">{{ editingProvider ? `编辑 ${editingProvider.name}` : '添加模型提供商' }}</h2>
              <p class="modal-desc">配置 API 接入信息</p>
            </div>
            <button class="modal-close" @click="closeProviderModal">
              <X :size="16" />
            </button>
          </div>

          <div class="modal-body">
            <div class="form-row-2">
              <div class="form-group form-group--sm">
                <label class="form-label">图标</label>
                <input v-model="providerForm.logo" class="form-input form-input--emoji" />
              </div>
              <div class="form-group">
                <label class="form-label">名称 *</label>
                <input v-model="providerForm.name" placeholder="例：OpenAI" class="form-input" />
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">API Base URL *</label>
              <input v-model="providerForm.apiBase" placeholder="https://api.example.com/v1" class="form-input form-input--mono" />
            </div>
            <div class="form-group">
              <label class="form-label">API Key</label>
              <div class="input-with-btn">
                <input
                  :type="showApiKey ? 'text' : 'password'"
                  v-model="providerForm.apiKey"
                  placeholder="sk-..."
                  class="form-input form-input--mono"
                />
                <button class="input-btn" @click="showApiKey = !showApiKey">
                  <EyeOff v-if="showApiKey" :size="16" />
                  <Eye v-else :size="16" />
                </button>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">描述</label>
              <textarea v-model="providerForm.description" rows="2" placeholder="提供商简介…" class="form-textarea" />
            </div>
            <div class="form-group">
              <label class="form-label">官网</label>
              <input v-model="providerForm.website" placeholder="https://..." class="form-input" />
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-cancel" @click="closeProviderModal">取消</button>
            <button
              class="btn-primary"
              :disabled="!providerForm.name.trim() || !providerForm.apiBase.trim()"
              @click="handleSaveProvider"
            >
              {{ editingProvider ? '保存' : '添加' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══ Edit Model Modal ═══ -->
    <Teleport to="body">
      <div v-if="showNewModel || editingModel" class="modal-overlay" @click.self="closeModelModal">
        <div class="modal-card modal-card--wide">
          <div class="modal-header">
            <div>
              <h2 class="modal-title">{{ editingModel ? `编辑 ${editingModel.displayName}` : '添加模型' }}</h2>
              <p class="modal-desc">{{ store.selectedProvider?.name }}</p>
            </div>
            <button class="modal-close" @click="closeModelModal">
              <X :size="16" />
            </button>
          </div>

          <div class="modal-body">
            <!-- Basic info -->
            <div class="modal-section">
              <p class="modal-section-title">基本信息</p>
              <div class="form-row-2">
                <div class="form-group">
                  <label class="form-label">显示名称 *</label>
                  <input v-model="modelForm.displayName" placeholder="GPT-4o" class="form-input" />
                </div>
                <div class="form-group">
                  <label class="form-label">模型 ID *</label>
                  <input v-model="modelForm.name" placeholder="gpt-4o" class="form-input form-input--mono" />
                </div>
              </div>
              <div class="form-row-3">
                <div class="form-group">
                  <label class="form-label">模型类型</label>
                  <select v-model="modelForm.type" class="form-select">
                    <option v-for="(meta, t) in MODEL_TYPE_META" :key="t" :value="t">
                      {{ meta.emoji }} {{ meta.label }}
                    </option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">状态</label>
                  <select v-model="modelForm.status" class="form-select">
                    <option value="active">正常</option>
                    <option value="beta">Beta</option>
                    <option value="deprecated">已弃用</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">上下文窗口</label>
                  <input
                    type="number"
                    :value="modelForm.contextWindow"
                    @input="modelForm.contextWindow = ($event.target as HTMLInputElement).value ? Number(($event.target as HTMLInputElement).value) : undefined"
                    placeholder="128000"
                    class="form-input"
                  />
                </div>
              </div>
              <div class="form-group">
                <label class="form-label">描述</label>
                <textarea v-model="modelForm.description" rows="2" placeholder="模型简介…" class="form-textarea" />
              </div>
            </div>

            <!-- Params -->
            <div v-if="modelForm.params.length > 0" class="modal-section">
              <p class="modal-section-title">默认参数</p>
              <div class="form-row-2">
                <div v-for="p in modelForm.params" :key="p.key" class="form-group">
                  <div class="param-header">
                    <label class="form-label">{{ paramLabel(p.key) }}</label>
                    <span class="param-value-display">{{ p.value }}</span>
                  </div>
                  <template v-if="p.type === 'number' && p.min !== undefined">
                    <input
                      type="range"
                      :min="p.min"
                      :max="p.max"
                      :step="p.step"
                      :value="Number(p.value)"
                      @input="updateParam(p.key, Number(($event.target as HTMLInputElement).value))"
                      class="range-input"
                    />
                  </template>
                  <template v-else-if="p.type === 'select'">
                    <select
                      :value="String(p.value)"
                      @change="updateParam(p.key, ($event.target as HTMLSelectElement).value)"
                      class="form-select"
                    >
                      <option v-for="o in p.options" :key="o" :value="o">{{ o }}</option>
                    </select>
                  </template>
                  <template v-else>
                    <input
                      :value="String(p.value)"
                      @input="updateParam(p.key, ($event.target as HTMLInputElement).value)"
                      class="form-input"
                    />
                  </template>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button class="btn-cancel" @click="closeModelModal">取消</button>
            <button
              class="btn-primary"
              :disabled="!modelForm.name.trim() || !modelForm.displayName.trim()"
              @click="handleSaveModel"
            >
              {{ editingModel ? '保存' : '添加' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══ Usage Detail Drawer ═══ -->
    <Teleport to="body">
      <div v-if="viewingModel" class="drawer-overlay" @click.self="viewingModel = null">
        <div class="drawer-panel">
          <div class="drawer-header">
            <div>
              <h3>{{ viewingModel.displayName }}</h3>
              <span
                class="drawer-type-badge"
                :style="{
                  color: MODEL_TYPE_META[viewingModel.type].color,
                  background: MODEL_TYPE_META[viewingModel.type].bg,
                  borderColor: MODEL_TYPE_META[viewingModel.type].border,
                }"
              >
                {{ MODEL_TYPE_META[viewingModel.type].emoji }} {{ MODEL_TYPE_META[viewingModel.type].label }}
              </span>
            </div>
            <button class="modal-close" @click="viewingModel = null">
              <X :size="16" />
            </button>
          </div>

          <div class="drawer-body">
            <div class="drawer-info-card">
              <div class="drawer-info-row">
                <span class="drawer-label">模型 ID</span>
                <span class="drawer-value drawer-value--mono">{{ viewingModel.name }}</span>
              </div>
              <div v-if="viewingModel.contextWindow" class="drawer-info-row">
                <span class="drawer-label">上下文窗口</span>
                <span class="drawer-value">{{ formatContext(viewingModel.contextWindow) }} tokens</span>
              </div>
              <div class="drawer-info-row">
                <span class="drawer-label">系统调用总次数</span>
                <span class="drawer-value">{{ viewingModel.callCount.toLocaleString() }}</span>
              </div>
              <div class="drawer-info-row">
                <span class="drawer-label">发布时间</span>
                <span class="drawer-value">{{ viewingModel.releaseDate ?? '—' }}</span>
              </div>
            </div>

            <div>
              <p class="drawer-section-title">使用此模型的代理</p>
              <div v-if="viewingModel.usedByAgents.length === 0" class="drawer-empty">
                暂无代理使用此模型
              </div>
              <div v-else class="drawer-agent-list">
                <div v-for="a in viewingModel.usedByAgents" :key="a" class="drawer-agent-item">
                  <div class="drawer-agent-icon">
                    <Bot :size="14" color="#a5b4fc" />
                  </div>
                  <div>
                    <p class="drawer-agent-name">{{ a }}</p>
                    <p class="drawer-agent-role">Agent</p>
                  </div>
                  <span class="drawer-agent-dot" />
                </div>
              </div>
            </div>

            <div v-if="viewingModel.params.length > 0">
              <p class="drawer-section-title">默认参数</p>
              <div class="drawer-params">
                <div v-for="p in viewingModel.params" :key="p.key" class="drawer-info-row">
                  <span class="drawer-label">{{ paramLabel(p.key) }}</span>
                  <span class="drawer-value drawer-value--mono">{{ p.value }}</span>
                </div>
              </div>
            </div>

            <p class="drawer-description">{{ viewingModel.description }}</p>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- ═══ Delete Confirm ═══ -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
        <div class="modal-card modal-card--sm">
          <h3 class="modal-title">确认删除</h3>
          <p class="confirm-text">
            确定要删除 <strong>"{{ deleteTarget.name }}"</strong> 吗？此操作不可撤销。
          </p>
          <div class="modal-footer">
            <button class="btn-cancel" @click="deleteTarget = null">取消</button>
            <button class="btn-danger" @click="handleDelete">删除</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.models-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--surface-primary);
  overflow: hidden;
}

/* ---- Page Header ---- */
.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
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

.btn-primary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border-radius: var(--radius-lg);
  border: none;
  background: #4f46e5;
  color: #fff;
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: background 0.15s ease;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3);
  flex-shrink: 0;
}

.btn-primary:hover { background: #4338ca; }
.btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: none;
  color: var(--foreground-muted);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-secondary:hover { background: rgba(255,255,255,0.06); color: var(--foreground-primary); }

/* ---- Stats Row ---- */
.stats-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
  flex-wrap: wrap;
}

.stat-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  background: rgba(255,255,255,0.02);
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.stat-chip-label { color: var(--foreground-muted); }
.stat-chip-value { font-weight: 700; color: var(--foreground-primary); }
.stat-divider { width: 1px; height: 20px; background: var(--border-subtle); }

.stat-chip--clickable {
  cursor: pointer;
  transition: all 0.15s ease;
}

.stat-chip--clickable:hover {
  border-color: rgba(255,255,255,0.15);
  color: var(--foreground-primary);
}

.stat-chip--clickable.active {
  font-weight: 500;
}

/* ---- Two-panel layout ---- */
.panels {
  display: flex;
  flex: 1;
  min-height: 0;
}

/* ---- Left Panel ---- */
.panel-left {
  width: 256px;
  min-width: 256px;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-subtle);
  background: rgba(0,0,0,0.1);
}

.panel-left-search {
  padding: 12px;
  position: relative;
}

.panel-left .search-icon {
  position: absolute;
  left: 22px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--foreground-muted);
}

.panel-left .search-input {
  width: 100%;
  padding: 6px 12px 6px 30px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: rgba(255,255,255,0.04);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
}

.panel-left .search-input::placeholder { color: var(--foreground-muted); }
.panel-left .search-input:focus { border-color: var(--color-accent); }

.panel-left-list {
  flex: 1;
  overflow-y: auto;
}

.provider-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  cursor: pointer;
  transition: background 0.1s ease;
}

.provider-item:hover { background: rgba(255,255,255,0.03); }

.provider-item.active {
  background: rgba(79,70,229,0.12);
  border-right: 2px solid #4f46e5;
}

.provider-logo { font-size: 20px; flex-shrink: 0; }

.provider-info {
  flex: 1;
  min-width: 0;
}

.provider-name {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--foreground-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.provider-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  margin-top: 2px;
}

.provider-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.provider-count {
  color: var(--foreground-muted);
}

.provider-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.1s ease;
}

.provider-item:hover .provider-actions { opacity: 1; }

.action-btn {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
}

.action-btn:hover { background: rgba(255,255,255,0.08); color: var(--foreground-primary); }
.action-btn--danger:hover { background: rgba(239,68,68,0.15); color: #f87171; }

/* ---- Right Panel ---- */
.panel-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

.panel-right--empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--foreground-muted);
  gap: 12px;
  font-size: var(--font-size-sm);
}

.empty-big-icon { color: var(--border-medium); }

/* ---- Provider Header ---- */
.provider-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-subtle);
  flex-shrink: 0;
}

.provider-header-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.provider-header-info {
  display: flex;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.provider-header-logo { font-size: 32px; flex-shrink: 0; }

.provider-header-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.provider-header-name {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--foreground-primary);
}

.provider-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.provider-header-desc {
  margin-top: 2px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.provider-header-extras {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.provider-api-base {
  font-family: 'Courier New', monospace;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

/* ---- Provider Tabs ---- */
.provider-tabs {
  display: flex;
  gap: 0;
  margin-top: 12px;
}

.provider-tab {
  padding: 6px 16px;
  font-size: var(--font-size-sm);
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.15s ease;
}

.provider-tab:hover { color: var(--foreground-secondary); }

.provider-tab.active {
  color: #a5b4fc;
  border-bottom-color: #4f46e5;
}

/* ---- Tab Content ---- */
.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

/* ---- Models Toolbar ---- */
.models-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.search-wrap {
  position: relative;
  flex: 1;
  max-width: 320px;
}

.search-wrap .search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--foreground-muted);
}

.search-wrap .search-input {
  width: 100%;
  padding: 6px 12px 6px 30px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: rgba(255,255,255,0.04);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
}

.search-wrap .search-input::placeholder { color: var(--foreground-muted); }
.search-wrap .search-input:focus { border-color: var(--color-accent); }

.type-filters {
  display: flex;
  gap: 4px;
}

.type-filter {
  padding: 4px 10px;
  border-radius: 6px;
  border: none;
  background: rgba(255,255,255,0.06);
  color: var(--foreground-muted);
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all 0.15s ease;
}

.type-filter:hover { background: rgba(255,255,255,0.1); color: var(--foreground-primary); }

.type-filter.active {
  background: rgba(79,70,229,0.6);
  color: #fff;
}

.btn-add-model {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  padding: 6px 14px;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(79,70,229,0.3);
  background: rgba(79,70,229,0.1);
  color: #a5b4fc;
  font-size: var(--font-size-xs);
  cursor: pointer;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.btn-add-model:hover { background: rgba(79,70,229,0.5); color: #fff; }

/* ---- Model Table Header ---- */
.model-table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr auto;
  gap: 16px;
  padding: 8px 12px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

/* ---- Model Rows ---- */
.model-rows {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.model-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr auto;
  gap: 16px;
  align-items: center;
  padding: 10px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid rgba(38,51,89,0.15);
  background: rgba(255,255,255,0.02);
  transition: background 0.1s ease;
}

.model-row:hover { background: rgba(255,255,255,0.04); }

.model-display-name {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--foreground-primary);
}

.model-id {
  font-family: 'Courier New', monospace;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  margin-top: 2px;
}

.model-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  border: 1px solid;
  font-size: var(--font-size-xs);
  width: fit-content;
}

.model-ctx {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.model-status-badge {
  display: inline-flex;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  width: fit-content;
}

.model-calls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.calls-num {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
}

.calls-agents {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-xs);
  color: #a5b4fc;
}

.model-actions {
  display: flex;
  align-items: center;
  gap: 2px;
}

/* ---- Empty State ---- */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 16px;
  text-align: center;
}

.empty-icon { color: var(--border-medium); margin-bottom: 12px; }
.empty-title { font-size: var(--font-size-md); color: var(--foreground-muted); }
.empty-desc { margin-top: 4px; font-size: var(--font-size-xs); color: var(--foreground-muted); }

/* ---- Usage Tab ---- */
.usage-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.usage-stat-card {
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-subtle);
  background: rgba(255,255,255,0.02);
  padding: 16px;
}

.usage-stat-label { font-size: var(--font-size-xs); color: var(--foreground-muted); }

.usage-stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--foreground-primary);
  margin-top: 4px;
}

.usage-stat-value--indigo { color: #a5b4fc; }
.usage-stat-value--emerald { color: #6ee7b7; }
.usage-stat-value--gray { color: #6b7280; }

.usage-ranking {
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-subtle);
  overflow: hidden;
}

.usage-ranking-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-subtle);
}

.usage-ranking-header h3 {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--foreground-primary);
}

.usage-ranking-list {
  display: flex;
  flex-direction: column;
}

.usage-rank-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(38,51,89,0.12);
}

.rank-num {
  width: 20px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  text-align: center;
  flex-shrink: 0;
}

.rank-emoji { font-size: 14px; flex-shrink: 0; }

.rank-info {
  flex: 1;
  min-width: 0;
}

.rank-name-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.rank-name {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
}

.rank-calls {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  flex-shrink: 0;
}

.rank-bar-track {
  height: 6px;
  border-radius: 3px;
  background: rgba(255,255,255,0.06);
  overflow: hidden;
}

.rank-bar-fill {
  height: 100%;
  border-radius: 3px;
  background: #4f46e5;
  transition: width 0.7s ease;
}

.rank-agents {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.rank-agent-tag {
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: rgba(79,70,229,0.1);
  border: 1px solid rgba(79,70,229,0.2);
  font-size: 10px;
  color: #a5b4fc;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 80px;
}

.rank-no-agent {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

/* ---- Modal ---- */
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(4px);
}

.modal-card {
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-medium);
  background: var(--color-bg-card);
  padding: 24px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.5);
}

.modal-card--wide { max-width: 560px; }
.modal-card--sm { max-width: 360px; }

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.modal-title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--foreground-primary);
}

.modal-desc {
  margin-top: 2px;
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.modal-close {
  padding: 6px;
  border-radius: var(--radius-sm);
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
}

.modal-close:hover { background: rgba(255,255,255,0.08); color: var(--foreground-primary); }

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.modal-section {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  background: rgba(255,255,255,0.02);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal-section-title {
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--foreground-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group--sm { width: 80px; flex-shrink: 0; }

.form-label {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.form-input {
  padding: 8px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: rgba(255,255,255,0.04);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
  transition: border-color 0.15s ease;
}

.form-input::placeholder { color: var(--foreground-muted); }
.form-input:focus { border-color: var(--color-accent); }

.form-input--mono {
  font-family: 'Courier New', monospace;
  color: #a5b4fc;
}

.form-input--emoji {
  text-align: center;
  font-size: 18px;
}

.form-textarea {
  padding: 8px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: rgba(255,255,255,0.04);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
  resize: none;
}

.form-textarea::placeholder { color: var(--foreground-muted); }
.form-textarea:focus { border-color: var(--color-accent); }

.form-select {
  padding: 8px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: rgba(255,255,255,0.04);
  color: var(--foreground-primary);
  font-size: var(--font-size-sm);
  outline: none;
  cursor: pointer;
}

.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }
.form-row-2 .form-group--sm + .form-group { flex: 1; }
.form-row-2:has(.form-group--sm) { grid-template-columns: 80px 1fr; }

.form-row-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }

.input-with-btn {
  position: relative;
}

.input-with-btn .form-input {
  padding-right: 40px;
}

.input-btn {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  padding: 4px;
  border: none;
  background: none;
  color: var(--foreground-muted);
  cursor: pointer;
}

.input-btn:hover { color: var(--foreground-primary); }

.param-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.param-value-display {
  font-family: 'Courier New', monospace;
  font-size: var(--font-size-xs);
  color: #a5b4fc;
}

.range-input {
  width: 100%;
  accent-color: #4f46e5;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 24px;
}

.btn-cancel {
  padding: 8px 16px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-medium);
  background: none;
  color: var(--foreground-muted);
  font-size: var(--font-size-sm);
  cursor: pointer;
}

.btn-cancel:hover { background: rgba(255,255,255,0.06); color: var(--foreground-primary); }

.btn-danger {
  padding: 8px 16px;
  border-radius: var(--radius-lg);
  border: none;
  background: #dc2626;
  color: #fff;
  font-size: var(--font-size-sm);
  cursor: pointer;
}

.btn-danger:hover { background: #b91c1c; }

.confirm-text {
  margin-top: 8px;
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
  line-height: 1.5;
}

.confirm-text strong {
  color: var(--foreground-primary);
  font-weight: 500;
}

/* ---- Drawer ---- */
.drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  display: flex;
  justify-content: flex-end;
  background: rgba(0,0,0,0.4);
}

.drawer-panel {
  width: 384px;
  height: 100%;
  background: var(--color-bg-card);
  border-left: 1px solid var(--border-subtle);
  padding: 24px;
  overflow-y: auto;
}

.drawer-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
}

.drawer-header h3 {
  font-size: var(--font-size-md);
  font-weight: 600;
  color: var(--foreground-primary);
}

.drawer-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  border: 1px solid;
  font-size: var(--font-size-xs);
}

.drawer-body { display: flex; flex-direction: column; gap: 20px; }

.drawer-info-card {
  border-radius: var(--radius-lg);
  background: rgba(255,255,255,0.03);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.drawer-info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.drawer-label { font-size: var(--font-size-xs); color: var(--foreground-muted); }

.drawer-value {
  font-size: var(--font-size-sm);
  color: var(--foreground-secondary);
}

.drawer-value--mono {
  font-family: 'Courier New', monospace;
  color: #a5b4fc;
}

.drawer-section-title {
  font-size: var(--font-size-xs);
  font-weight: 500;
  color: var(--foreground-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.drawer-empty {
  padding: 24px;
  text-align: center;
  font-size: var(--font-size-sm);
  color: var(--foreground-muted);
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-lg);
}

.drawer-agent-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.drawer-agent-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  background: rgba(255,255,255,0.02);
}

.drawer-agent-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  background: rgba(79,70,229,0.2);
}

.drawer-agent-name {
  font-size: var(--font-size-sm);
  color: var(--foreground-primary);
}

.drawer-agent-role {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
}

.drawer-agent-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10B981;
  margin-left: auto;
}

.drawer-params {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  background: rgba(255,255,255,0.02);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.drawer-description {
  font-size: var(--font-size-xs);
  color: var(--foreground-muted);
  line-height: 1.5;
}
</style>
