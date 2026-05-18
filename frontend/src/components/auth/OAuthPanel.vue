<script setup lang="ts">
import type { OAuthProvider } from '@/types/components'

const emit = defineEmits<{
  select: [provider: OAuthProvider]
}>()

const providers: OAuthProvider[] = [
  { name: '微信', icon: 'W', bgColor: 'var(--color-oauth-wechat)', textColor: '#fff', shadowColor: 'rgba(7,193,96,0.25)' },
  { name: '支付宝', icon: 'A', bgColor: 'var(--color-oauth-alipay)', textColor: '#fff', shadowColor: 'rgba(23,119,249,0.25)' },
  { name: '飞书', icon: 'F', bgColor: 'var(--color-oauth-feishu)', textColor: '#fff', shadowColor: 'rgba(51,112,250,0.25)' },
  { name: '钉钉', icon: 'D', bgColor: 'var(--color-oauth-dingtalk)', textColor: '#fff', shadowColor: 'rgba(0,137,249,0.25)' },
  { name: '企业微信', icon: 'W', bgColor: 'var(--color-oauth-wework)', textColor: '#fff', shadowColor: 'rgba(7,193,96,0.2)' },
]
</script>

<template>
  <div class="oauth-panel">
    <div class="oauth-divider">
      <span class="divider-line" />
      <span class="divider-text">第三方账号登录</span>
      <span class="divider-line" />
    </div>

    <div class="oauth-icons">
      <button
        v-for="provider in providers"
        :key="provider.name"
        class="oauth-icon-btn"
        :style="{
          background: provider.bgColor,
          color: provider.textColor,
          boxShadow: `0px 3px 8px ${provider.shadowColor}`,
        }"
        :title="provider.name"
        @click="emit('select', provider)"
      >
        {{ provider.icon }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.oauth-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.oauth-divider {
  display: flex;
  align-items: center;
  gap: 12px;
}

.divider-line {
  flex: 1;
  height: 1px;
  background: var(--color-border-input);
}

.divider-text {
  font-size: var(--font-size-oauth-label);
  color: var(--color-text-muted);
  flex-shrink: 0;
}

.oauth-icons {
  display: flex;
  justify-content: center;
  gap: var(--size-oauth-gap);
}

.oauth-icon-btn {
  width: var(--size-oauth-icon);
  height: var(--size-oauth-icon);
  border-radius: var(--radius-oauth-icon);
  border: none;
  font-size: var(--font-size-oauth-text);
  font-weight: var(--font-weight-bold);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.oauth-icon-btn:hover {
  transform: translateY(-2px);
}
</style>
