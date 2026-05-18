<script setup lang="ts">
import LoginCard from '@/components/auth/LoginCard.vue'
import EmailRegisterForm from '@/components/auth/EmailRegisterForm.vue'
import RegisterLink from '@/components/auth/RegisterLink.vue'
</script>

<template>
  <div class="email-register-view">
    <LoginCard>
      <h2 class="register-title">邮箱注册</h2>
      <EmailRegisterForm />
      <RouterLink to="/register" class="back-link">手机号注册</RouterLink>
    </LoginCard>
  </div>
</template>

<style scoped>
.email-register-view {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.register-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
  text-align: center;
  margin-bottom: 8px;
}

.back-link {
  display: block;
  text-align: center;
  font-size: var(--font-size-register-link);
  color: var(--color-text-muted);
  text-decoration: none;
}

.back-link:hover {
  color: var(--color-accent);
}
</style>
