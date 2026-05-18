<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { oauthApi } from '@/services/oauthApi'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const error = ref('')

onMounted(async () => {
  const code = route.query.code as string
  const state = route.query.state as string
  const provider = route.query.provider as string

  if (!code || !state || !provider) {
    error.value = '缺少授权参数'
    return
  }

  try {
    const res = await oauthApi.handleCallback(provider, code, state)
    const { tokens, user } = res.data.data
    authStore.setTokens(tokens, true)
    authStore.user = user
    router.push('/')
  } catch (err) {
    error.value = err instanceof Error ? err.message : '第三方登录失败'
  }
})
</script>

<template>
  <div class="oauth-callback-view">
    <div v-if="error" class="oauth-error">{{ error }}</div>
    <div v-else class="oauth-loading">正在登录...</div>
  </div>
</template>

<style scoped>
.oauth-callback-view {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background: var(--color-bg-page);
}

.oauth-loading {
  color: var(--color-text-secondary);
  font-size: 16px;
}

.oauth-error {
  color: var(--color-text-error);
  font-size: 16px;
}
</style>
