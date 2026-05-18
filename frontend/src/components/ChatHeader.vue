<script setup lang="ts">
import { ref } from 'vue'
import { Sparkles, ChevronDown } from 'lucide-vue-next'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()

const models = ['DeepSeek V4', 'Claude Opus 4.7', 'GPT-4o', 'Gemini 2.5 Pro']
const dropdownOpen = ref(false)

function selectModel(model: string) {
  uiStore.selectedModel = model
  dropdownOpen.value = false
}

function toggleDropdown() {
  dropdownOpen.value = !dropdownOpen.value
}

function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.model-selector')) {
    dropdownOpen.value = false
  }
}

// Only listen when dropdown is open
import { watch, onMounted, onUnmounted } from 'vue'
watch(dropdownOpen, (open) => {
  if (open) {
    document.addEventListener('click', handleClickOutside)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div class="chat-header">
    <div class="header-left">
      <span class="header-avatar">
        <Sparkles :size="16" />
      </span>
      <span class="header-title">Hermes 智能体</span>
    </div>
    <div class="header-right">
      <div class="model-selector" @click.stop="toggleDropdown">
        <span class="model-name">{{ uiStore.selectedModel }}</span>
        <ChevronDown :size="14" :class="{ rotated: dropdownOpen }" />
        <Transition name="dropdown">
          <div v-if="dropdownOpen" class="model-dropdown">
            <div
              v-for="model in models"
              :key="model"
              class="model-option"
              :class="{ active: uiStore.selectedModel === model }"
              @click="selectModel(model)"
            >
              {{ model }}
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-header {
  height: var(--chat-header-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: var(--surface-card);
  border-bottom: 1px solid var(--border-subtle);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: var(--accent-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  font-size: 15px;
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.model-selector {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-lg);
  background: var(--surface-secondary);
  border: 1px solid var(--border-medium);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--foreground-primary);
  cursor: pointer;
  user-select: none;
}

.model-selector:hover {
  border-color: var(--accent-primary);
}

.model-name {
  color: var(--foreground-primary);
}

.rotated {
  transform: rotate(180deg);
  transition: transform var(--transition-fast);
}

.model-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  right: 0;
  min-width: 200px;
  background: var(--surface-card);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  z-index: 200;
  overflow: hidden;
}

.model-option {
  padding: 10px 14px;
  font-size: var(--font-size-base);
  color: var(--foreground-secondary);
  cursor: pointer;
  transition: background 0.1s ease;
}

.model-option:hover {
  background: var(--surface-secondary);
  color: var(--foreground-primary);
}

.model-option.active {
  background: var(--accent-primary-light);
  color: var(--accent-primary);
  font-weight: var(--font-weight-semibold);
}

.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
