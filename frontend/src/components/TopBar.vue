<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { Search, Bell, CircleUser, LogOut, ChevronRight } from 'lucide-vue-next'
import { useUiStore } from '@/stores/ui'
import { useAuthStore } from '@/stores/auth'
import { useAuth } from '@/composables/useAuth'

const route = useRoute()
const uiStore = useUiStore()
const authStore = useAuthStore()
const { logout } = useAuth()

const userMenuOpen = ref(false)
const searchFocused = ref(false)

const displayName = computed(() => {
  return authStore.user?.nickname || '未登录'
})

const breadcrumb = computed(() => {
  const map: Record<string, { group: string; item: string }> = {
    '/': { group: '聊天', item: '对话' },
    '/agents': { group: '代理', item: '代理' },
    '/skills': { group: '代理', item: '技能 Hub' },
    '/overview': { group: '控制', item: '概览' },
    '/models': { group: '控制', item: '模型' },
    '/scheduled-tasks': { group: '控制', item: '定时任务' },
    '/mcp': { group: 'MCP', item: 'MCP 广场' },
  }
  const path = route.path
  if (path.startsWith('/mcp/')) return map['/mcp']
  return map[path] ?? null
})

function toggleUserMenu() {
  userMenuOpen.value = !userMenuOpen.value
}

async function handleLogout() {
  userMenuOpen.value = false
  await logout()
}

function handleClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement
  if (!target.closest('.user-menu-wrap')) {
    userMenuOpen.value = false
  }
}

function handleSearchInput(e: Event) {
  const target = e.target as HTMLInputElement
  uiStore.searchQuery = target.value
}

function clearSearch() {
  uiStore.searchQuery = ''
}

// Click outside to close user menu
import { watch } from 'vue'
watch(userMenuOpen, (open) => {
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
  <div class="topbar">
    <div class="topbar-left">
      <div v-if="breadcrumb" class="breadcrumb">
        <span class="breadcrumb-group">{{ breadcrumb.group }}</span>
        <ChevronRight :size="14" class="breadcrumb-sep" />
        <span class="breadcrumb-item">{{ breadcrumb.item }}</span>
      </div>
    </div>
    <div class="topbar-right">
      <div class="search-box" :class="{ focused: searchFocused }">
        <Search :size="16" class="search-icon" />
        <input
          :value="uiStore.searchQuery"
          type="text"
          placeholder="搜索对话、技能、设置..."
          @input="handleSearchInput"
          @focus="searchFocused = true"
          @blur="searchFocused = false"
        />
        <button
          v-if="uiStore.searchQuery"
          class="search-clear"
          @click="clearSearch"
        >
          &times;
        </button>
      </div>
      <button class="action-btn" title="通知">
        <Bell :size="18" />
      </button>

      <!-- User menu -->
      <div class="user-menu-wrap">
        <button class="user-btn" :class="{ active: userMenuOpen }" @click.stop="toggleUserMenu">
          <CircleUser :size="18" />
          <span class="user-name">{{ displayName }}</span>
        </button>

        <Transition name="menu">
          <div v-if="userMenuOpen" class="user-dropdown">
            <div class="user-dropdown-header">
              <span class="user-avatar">
                {{ displayName.charAt(0) }}
              </span>
              <span class="user-fullname">{{ displayName }}</span>
            </div>
            <div class="user-dropdown-divider" />
            <button class="user-dropdown-item logout" @click="handleLogout">
              <LogOut :size="14" />
              <span>退出登录</span>
            </button>
          </div>
        </Transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
.topbar {
  height: var(--topbar-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: var(--surface-card);
  border-bottom: 1px solid var(--border-subtle);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--font-size-sm);
}

.breadcrumb-group {
  color: var(--foreground-muted);
}

.breadcrumb-sep {
  color: var(--foreground-muted);
  flex-shrink: 0;
}

.breadcrumb-item {
  color: var(--foreground-primary);
  font-weight: var(--font-weight-medium);
}

.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 360px;
  padding: 6px 12px;
  border-radius: var(--radius-full);
  background: var(--surface-secondary);
  border: 1px solid transparent;
  transition: border-color var(--transition-fast), background var(--transition-fast);
}

.search-box.focused {
  border-color: var(--accent-primary);
  background: var(--color-bg-input);
}

.search-icon {
  color: var(--foreground-muted);
  flex-shrink: 0;
}

.search-box input {
  width: 100%;
  border: none;
  outline: none;
  background: none;
  font-size: var(--font-size-base);
  color: var(--foreground-primary);
}

.search-box input::placeholder {
  color: var(--foreground-muted);
}

.search-clear {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: none;
  background: var(--foreground-muted);
  color: var(--surface-primary);
  font-size: 12px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  border: none;
  background: transparent;
  color: var(--foreground-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.action-btn:hover {
  background: var(--surface-secondary);
}

/* User menu */
.user-menu-wrap {
  position: relative;
}

.user-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px 4px 6px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-subtle);
  background: var(--surface-secondary);
  color: var(--foreground-secondary);
  font-size: var(--font-size-sm);
  cursor: pointer;
  transition: border-color var(--transition-fast);
}

.user-btn:hover,
.user-btn.active {
  border-color: var(--accent-primary);
  color: var(--foreground-primary);
}

.user-name {
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 200px;
  background: var(--surface-card);
  border: 1px solid var(--border-medium);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  z-index: 200;
  overflow: hidden;
}

.user-dropdown-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--accent-primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: var(--font-weight-bold);
  flex-shrink: 0;
}

.user-fullname {
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--foreground-primary);
}

.user-dropdown-divider {
  height: 1px;
  background: var(--border-subtle);
}

.user-dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 16px;
  border: none;
  background: none;
  color: var(--foreground-secondary);
  font-size: var(--font-size-base);
  cursor: pointer;
}

.user-dropdown-item:hover {
  background: var(--surface-secondary);
  color: var(--foreground-primary);
}

.user-dropdown-item.logout:hover {
  background: rgba(240, 69, 69, 0.1);
  color: var(--color-text-error);
}

/* Menu transition */
.menu-enter-active,
.menu-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.menu-enter-from,
.menu-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
