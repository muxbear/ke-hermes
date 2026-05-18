<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'login' | 'register'
  }>(),
  {
    variant: 'login',
  },
)
</script>

<template>
  <div class="register-link" v-if="variant === 'login'">
    <span class="link-text">还没有账号？</span>
    <RouterLink to="/register" class="link-action">立即注册</RouterLink>
  </div>
  <div class="register-link" v-else>
    <span class="link-text">已有账号？</span>
    <RouterLink to="/login" class="link-action">立即登录</RouterLink>
  </div>
</template>

<style scoped>
.register-link {
  display: flex;
  justify-content: center;
  gap: 4px;
  padding-top: 8px;
}

.link-text {
  font-size: var(--font-size-register-link);
  color: var(--color-text-secondary);
}

.link-action {
  font-size: var(--font-size-register-link);
  font-weight: var(--font-weight-semibold);
  color: var(--color-accent);
  text-decoration: none;
}

.link-action:hover {
  text-decoration: underline;
}
</style>
