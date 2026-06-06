<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { X, Users } from 'lucide-vue-next'
import type { Agent } from '@/types/agent'
import type { Provider } from '@/types/model'
import { fetchProviders } from '@/services/modelApi'

const props = withDefaults(
  defineProps<{
    visible: boolean
    mode: 'create' | 'edit'
    agent?: Agent | null
    agentName?: string
    agentType?: string
  }>(),
  { agent: null, agentName: '', agentType: 'main' },
)

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'submit', data: { name: string; description: string; providerId: string; modelId: string }): void
}>()

const nameValue = ref('')
const descValue = ref('')
const selectedProviderId = ref('')
const selectedModelId = ref('')
const providers = ref<Provider[]>([])
const loadingProviders = ref(false)

const isCreate = computed(() => props.mode === 'create')
const dialogTitle = computed(() => (isCreate.value ? '新建子智能体' : '编辑智能体'))

const selectedProvider = computed(() =>
  providers.value.find((p) => p.id === selectedProviderId.value) ?? null,
)

const availableModels = computed(() => selectedProvider.value?.models ?? [])

function resetForm() {
  nameValue.value = ''
  descValue.value = ''
  selectedProviderId.value = ''
  selectedModelId.value = ''
}

function populateForm(agent: Agent) {
  nameValue.value = agent.name
  descValue.value = agent.description ?? ''
  selectedProviderId.value = agent.providerId ?? ''
  selectedModelId.value = agent.modelId ?? ''
}

async function loadProviders() {
  if (providers.value.length > 0) return
  loadingProviders.value = true
  try {
    providers.value = await fetchProviders()
  } catch {
    providers.value = []
  } finally {
    loadingProviders.value = false
  }
}

function handleSubmit() {
  if (!nameValue.value.trim()) return
  emit('submit', {
    name: nameValue.value.trim(),
    description: descValue.value.trim(),
    providerId: selectedProviderId.value,
    modelId: selectedModelId.value,
  })
}

function handleClose() {
  emit('close')
}

watch(
  () => props.visible,
  async (val) => {
    if (!val) return
    if (props.mode === 'edit' && props.agent) {
      populateForm(props.agent)
    } else {
      resetForm()
    }
    await loadProviders()
  },
)

watch(selectedProviderId, () => {
  if (selectedModelId.value && !availableModels.value.find((m) => m.id === selectedModelId.value)) {
    selectedModelId.value = ''
  }
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="dialog-overlay" @click.self="handleClose">
        <div class="dialog-modal">
          <!-- Header -->
          <div class="dialog-header">
            <div class="header-left">
              <div class="dialog-icon">
                <Users :size="18" style="color: #f97316" />
              </div>
              <div>
                <h3 class="dialog-title">{{ dialogTitle }}</h3>
                <p v-if="isCreate" class="dialog-desc">
                  为 <span class="highlight">"{{ agentName }}"</span>
                  {{ agentType === 'main' ? ' (主智能体)' : ' (子智能体)' }}
                  创建新的子智能体
                </p>
                <p v-else class="dialog-desc">
                  修改智能体 <span class="highlight">"{{ agent?.name }}"</span> 的配置
                </p>
              </div>
            </div>
            <button class="modal-close" @click="handleClose">
              <X :size="18" />
            </button>
          </div>

          <!-- Body -->
          <form class="dialog-body" @submit.prevent="handleSubmit">
            <div class="form-field">
              <label class="field-label">智能体名称</label>
              <input
                v-model="nameValue"
                type="text"
                class="text-input"
                placeholder="例如: 数据处理子智能体"
                autofocus
              />
            </div>

            <!-- Model selection -->
            <div class="form-field">
              <label class="field-label">模型提供商</label>
              <div class="custom-select-wrapper">
                <select
                  v-model="selectedProviderId"
                  class="text-input custom-select"
                  :disabled="loadingProviders"
                >
                  <option value="">-- 请选择提供商 --</option>
                  <option
                    v-for="p in providers"
                    :key="p.id"
                    :value="p.id"
                  >
                    {{ p.logo }} {{ p.name }}
                  </option>
                </select>
              </div>
            </div>
            <div class="form-field">
              <label class="field-label">模型</label>
              <div class="custom-select-wrapper">
                <select
                  v-model="selectedModelId"
                  class="text-input custom-select"
                  :disabled="!selectedProviderId"
                >
                  <option value="">-- 请选择模型 --</option>
                  <option
                    v-for="m in availableModels"
                    :key="m.id"
                    :value="m.id"
                  >
                    {{ m.displayName }} ({{ m.type }})
                  </option>
                </select>
              </div>
            </div>

            <div class="form-field">
              <label class="field-label">描述 (可选)</label>
              <textarea
                v-model="descValue"
                class="text-input textarea"
                :rows="3"
                placeholder="描述此智能体的职责和功能..."
              />
            </div>

            <!-- Footer -->
            <div class="dialog-footer">
              <button type="button" class="btn btn-ghost" @click="handleClose">取消</button>
              <button
                type="submit"
                class="btn btn-primary"
                :disabled="!nameValue.trim()"
              >
                {{ isCreate ? '创建' : '保存' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-overlay);
  z-index: 9999;
}

.dialog-modal {
  width: 480px;
  max-width: 92vw;
  display: flex;
  flex-direction: column;
  background: var(--color-modal-bg);
  border: 1px solid var(--color-border-card);
  border-radius: var(--radius-card);
  box-shadow: 0px 12px 60px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

/* ---- Header ---- */
.dialog-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.dialog-icon {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: rgba(249, 115, 22, 0.12);
}

.dialog-title {
  font-size: 17px;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.dialog-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 4px 0 0;
}

.highlight {
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
  flex-shrink: 0;
  transition: all var(--transition-fast);
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-text-primary);
}

/* ---- Body ---- */
.dialog-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-label);
}

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

.text-input::placeholder {
  color: var(--color-text-muted);
}

.text-input:focus {
  border-color: var(--color-accent);
  box-shadow: 0px 0px 0px 2px rgba(59, 130, 246, 0.12);
}

.textarea {
  resize: vertical;
  min-height: 60px;
  line-height: 1.5;
}

.custom-select-wrapper {
  position: relative;
}

.custom-select {
  appearance: none;
  cursor: pointer;
  padding-right: 32px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%238794a8' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
}

.custom-select:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ---- Footer ---- */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border-input);
  flex-shrink: 0;
}

/* ---- Buttons ---- */
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

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-accent);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-accent-dark);
}

.btn-ghost {
  background: rgba(135, 148, 173, 0.08);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-input);
}

.btn-ghost:hover {
  background: rgba(135, 148, 173, 0.14);
  color: var(--color-text-primary);
}

/* ---- Transition ---- */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-normal);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
