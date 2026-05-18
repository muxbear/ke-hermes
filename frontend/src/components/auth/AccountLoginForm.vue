<script setup lang="ts">
import { reactive, ref } from 'vue'
import { User, Lock, KeyRound } from 'lucide-vue-next'
import PasswordInput from '@/components/common/PasswordInput.vue'
import FormError from '@/components/common/FormError.vue'

const emit = defineEmits<{
  submit: [payload: { account: string; password: string; rememberMe: boolean }]
  'forgot-password': []
}>()

const form = reactive({
  account: '',
  password: '',
  rememberMe: false,
})

const errors = reactive({
  account: '',
  password: '',
})

function validate(): boolean {
  errors.account = ''
  errors.password = ''

  if (!form.account.trim()) {
    errors.account = '请输入账号'
    return false
  }
  if (form.account.trim().length < 2 || form.account.trim().length > 64) {
    errors.account = '账号长度 2-64 个字符'
    return false
  }
  if (!form.password) {
    errors.password = '请输入密码'
    return false
  }
  if (form.password.length < 6 || form.password.length > 12) {
    errors.password = '密码 6-12 个字符，至少包含字母和数字'
    return false
  }

  return true
}

function onSubmit() {
  if (!validate()) return false
  emit('submit', {
    account: form.account.trim(),
    password: form.password,
    rememberMe: form.rememberMe,
  })
  return true
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter') {
    onSubmit()
  }
}

defineExpose({
  validate,
  getFormData: () => ({
    account: form.account.trim(),
    password: form.password,
    rememberMe: form.rememberMe,
  }),
  submit: onSubmit,
})
</script>

<template>
  <div class="account-login-form" @keydown="handleKeydown">
    <!-- Account -->
    <div class="input-wrapper">
      <el-input
        v-model="form.account"
        placeholder="请输入账号"
        size="large"
        class="auth-input"
      >
        <template #prefix>
          <User :size="18" class="input-icon" />
        </template>
      </el-input>
      <FormError :message="errors.account" />
    </div>

    <!-- Password -->
    <div class="input-wrapper">
      <PasswordInput
        v-model="form.password"
        placeholder="请输入密码"
      />
      <FormError :message="errors.password" />
    </div>

    <!-- Remember me + Forgot -->
    <div class="form-extra">
      <label class="remember-me">
        <el-checkbox v-model="form.rememberMe" size="small" />
        <span>记住我</span>
      </label>
      <a class="forgot-link" @click.prevent="emit('forgot-password')">忘记密码</a>
    </div>
  </div>
</template>

<style scoped>
.account-login-form {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.input-wrapper {
  margin-bottom: 8px;
}

.auth-input :deep(.el-input__wrapper) {
  height: var(--size-input-height);
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-input);
  border-radius: var(--radius-input);
  box-shadow: none;
  padding: 0 14px;
}

.auth-input :deep(.el-input__wrapper:hover) {
  border-color: var(--color-text-muted);
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

.form-extra {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: var(--font-size-remember-forgot);
  color: var(--color-text-secondary);
  cursor: pointer;
}

.forgot-link {
  font-size: var(--font-size-remember-forgot);
  color: var(--color-text-secondary);
  text-decoration: underline;
  cursor: pointer;
}

.forgot-link:hover {
  color: var(--color-accent);
}
</style>
