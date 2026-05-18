<script setup lang="ts">
import LoginCard from '@/components/auth/LoginCard.vue'
import RegisterForm from '@/components/auth/RegisterForm.vue'
import RegisterLink from '@/components/auth/RegisterLink.vue'
</script>

<template>
  <div class="register-view">
    <LoginCard>
      <h2 class="register-title">创建账号</h2>
      <RegisterForm />
      <RegisterLink variant="register" />
    </LoginCard>
  </div>
</template>

<style scoped>
.register-view {
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
</style>
