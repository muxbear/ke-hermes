<script setup>
import {
  ChevronDown,
  PanelRightClose,
  PanelRightOpen,
  Plus,
  Trash2,
} from 'lucide-vue-next'
import { useUiStore } from '@/stores/ui'
import { useChatStore } from '@/stores/chat'
import { onMounted } from 'vue'

const uiStore = useUiStore()
const chatStore = useChatStore()

onMounted(() => {
  uiStore.fetchHistories()
})

async function handleSelectHistory(threadId) {
  uiStore.activeThreadId = threadId
  await chatStore.loadConversation(threadId)
}

async function handleDeleteHistory(threadId) {
  await uiStore.deleteHistory(threadId)
  if (chatStore.threadId === threadId) {
    chatStore.clearMessages()
  }
}

function handleNewConversation() {
  chatStore.clearMessages()
  uiStore.newConversation()
}
</script>

<template>
  <aside class="right-panel" :class="{ collapsed: uiStore.rightPanelCollapsed }">
    <div v-if="!uiStore.rightPanelCollapsed" class="panel-expanded">
      <div class="panel-header">
        <div class="panel-header-left">
          <span class="panel-title">历史对话</span>
          <ChevronDown :size="14" class="toggle-icon" />
        </div>
        <div class="panel-header-right">
          <button class="collapse-btn" @click="uiStore.toggleRightPanel">
            <PanelRightClose :size="14" />
          </button>
          <button class="new-chat-btn" @click="handleNewConversation">
            <Plus :size="14" />
            <span>新建对话</span>
          </button>
        </div>
      </div>

      <div class="history-list">
        <div
          v-for="item in uiStore.histories"
          :key="item.thread_id"
          class="history-item"
          :class="{ active: uiStore.activeThreadId === item.thread_id }"
          @click="handleSelectHistory(item.thread_id)"
        >
          <span class="history-title">{{ item.title }}</span>
          <button class="delete-btn" @click.stop="handleDeleteHistory(item.thread_id)">
            <Trash2 :size="14" />
          </button>
        </div>
      </div>
    </div>

    <div v-else class="panel-collapsed">
      <button class="expand-btn" @click="uiStore.toggleRightPanel">
        <PanelRightOpen :size="14" />
      </button>
    </div>
  </aside>
</template>

<style scoped>
.right-panel {
  height: 100%;
  background: var(--surface-card);
  transition: width var(--transition-duration) ease,
              min-width var(--transition-duration) ease;
  overflow: hidden;
}

.right-panel:not(.collapsed) {
  width: var(--right-panel-width);
  min-width: var(--right-panel-width);
  border-left: 1px solid var(--border-subtle);
}

.right-panel.collapsed {
  width: var(--right-panel-collapsed-width);
  min-width: var(--right-panel-collapsed-width);
  border-left: 1px solid var(--border-subtle);
}

.panel-expanded {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 12px;
  height: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.panel-header-left {
  display: flex;
  align-items: center;
  gap: 4px;
}

.panel-title {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.toggle-icon {
  color: var(--foreground-muted);
  cursor: pointer;
}

.panel-header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.collapse-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--foreground-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.collapse-btn:hover {
  background: var(--surface-secondary);
}

.new-chat-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: var(--radius-lg);
  border: none;
  background: var(--accent-primary);
  color: white;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
}

.new-chat-btn:hover {
  opacity: 0.85;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: var(--radius-lg);
  background: var(--surface-secondary);
  cursor: pointer;
  transition: background 0.15s ease;
}

.history-item.active {
  background: var(--accent-primary-light);
}

.history-item:hover {
  background: var(--accent-primary-light);
}

.history-item.active:hover {
  background: var(--accent-primary-light);
}

.history-title {
  font-size: var(--font-size-base);
  color: var(--foreground-secondary);
}

.history-item.active .history-title {
  color: var(--foreground-primary);
}

.delete-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--foreground-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.history-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: var(--surface-secondary);
  color: var(--foreground-secondary);
}

.panel-collapsed {
  height: 100%;
  position: relative;
}

.expand-btn {
  position: absolute;
  top: 8px;
  left: 50%;
  transform: translateX(-50%);
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: none;
  background: var(--surface-secondary);
  color: var(--foreground-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.expand-btn:hover {
  background: var(--border-subtle);
}
</style>