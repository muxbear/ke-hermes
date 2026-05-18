<script setup lang="ts">
import { reactive } from 'vue'
import { Mail, KeyRound, User, Lock } from 'lucide-vue-next'
import PasswordInput from '@/components/common/PasswordInput.vue'
import CountdownButton from '@/components/common/CountdownButton.vue'
import FormError from '@/components/common/FormError.vue'
import AgreementCheckbox from './AgreementCheckbox.vue'
import { useCountdown } from '@/composables/useCountdown'

const { countdown, start: startCountdown } = useCountdown()

const form = reactive({
  email: '',
  emailCode: '',
  nickname: '',
  password: '',
  confirmPassword: '',
})

const agreementChecked = reactive({ value: false })
const errors = reactive({
  email: '',
  emailCode: '',
  nickname: '',
  password: '',
  confirmPassword: '',
})

function validate(): boolean {
  errors.email = ''
  errors.emailCode = ''
  errors.nickname = ''
  errors.password = ''
  errors.confirmPassword = ''

  if (!form.email.trim() || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
    errors.email = '请输入正确的邮箱地址'
    return false
  }
  if (!/^\d{6}$/.test(form.emailCode)) {
    errors.emailCode = '验证码为 6 位数字'
    return false
  }
  if (form.nickname.trim().length < 2 || form.nickname.trim().length > 20) {
    errors.nickname = '昵称 2-20 个字符'
    return false
  }
  if (form.password.length < 8 || form.password.length > 32) {
    errors.password = '8-32 个字符'
    return false
  }
  if (form.password !== form.confirmPassword) {
    errors.confirmPassword = '两次密码输入不一致'
    return false
  }
  if (!agreementChecked.value) {
    return false
  }
  return true
}

function onSubmit() {
  if (!validate()) return
  // TODO: 调用邮箱注册 API
}
</script>

<template>
  <div class="email-register-form">
    <div class="input-wrapper">
      <el-input v-model="form.email" placeholder="请输入邮箱" size="large" class="auth-input">
        <template #prefix><Mail :size="18" class="input-icon" /></template>
      </el-input>
      <FormError :message="errors.email" />
    </div>

    <div class="sms-row">
      <el-input v-model="form.emailCode" placeholder="请输入验证码" size="large" class="auth-input sms-input" maxlength="6">
        <template #prefix><KeyRound :size="18" class="input-icon" /></template>
      </el-input>
      <CountdownButton :countdown="countdown" @click="() => {}" />
    </div>
    <FormError :message="errors.emailCode" />

    <div class="input-wrapper">
      <el-input v-model="form.nickname" placeholder="请输入昵称" size="large" class="auth-input">
        <template #prefix><User :size="18" class="input-icon" /></template>
      </el-input>
      <FormError :message="errors.nickname" />
    </div>

    <div class="input-wrapper">
      <PasswordInput v-model="form.password" placeholder="请输入密码（8-32位）" />
      <FormError :message="errors.password" />
    </div>

    <div class="input-wrapper">
      <PasswordInput v-model="form.confirmPassword" placeholder="请再次输入密码" />
      <FormError :message="errors.confirmPassword" />
    </div>

    <AgreementCheckbox v-model="agreementChecked.value" />

    <el-button type="primary" size="large" class="submit-btn" @click="onSubmit">
      注册
    </el-button>
  </div>
</template>

<style scoped>
.email-register-form {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.input-wrapper {
  margin-bottom: 8px;
}

.sms-row {
  display: flex;
  gap: 12px;
}

.sms-input {
  flex: 1;
}

.auth-input :deep(.el-input__wrapper) {
  height: var(--size-input-height);
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-input);
  box-shadow: none;
  padding: 0 14px;
}

.auth-input :deep(.el-input__wrapper.is-focus) {
  border-color: var(--color-accent);
  box-shadow: 0px 0px 0px 2px rgba(59, 130, 246, 0.15);
}

.auth-input :deep(.el-input__inner) {
  color: var(--color-text-primary);
  font-size: var(--font-size-input);
}

.auth-input :deep(.el-input__inner::placeholder) {
  color: var(--color-text-muted);
}

.input-icon {
  color: var(--color-text-muted);
}

.submit-btn {
  height: var(--size-button-height);
  border-radius: var(--radius-button);
  background: var(--color-accent-gradient);
  border: none;
  font-size: var(--font-size-button);
  font-weight: var(--font-weight-bold);
  box-shadow: var(--shadow-button);
  margin-top: 8px;
}
</style>
