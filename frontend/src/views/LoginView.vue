<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import LoginCard from '@/components/auth/LoginCard.vue'
import LoginTabs from '@/components/auth/LoginTabs.vue'
import AccountLoginForm from '@/components/auth/AccountLoginForm.vue'
import PhoneLoginForm from '@/components/auth/PhoneLoginForm.vue'
import AgreementCheckbox from '@/components/auth/AgreementCheckbox.vue'
import OAuthPanel from '@/components/auth/OAuthPanel.vue'
import RegisterLink from '@/components/auth/RegisterLink.vue'
import { useAuth } from '@/composables/useAuth'

const activeTab = ref<'account' | 'phone'>('account')
const { loading, error, loginWithPassword, loginWithPhone } = useAuth()
const agreementChecked = ref(true)
const agreementShake = ref(false)

const accountFormRef = ref<InstanceType<typeof AccountLoginForm> | null>(null)
const phoneFormRef = ref<InstanceType<typeof PhoneLoginForm> | null>(null)

const submitError = ref<string | null>(null)

async function doLogin(data: {
  account?: string
  password?: string
  rememberMe?: boolean
  phone?: string
  smsCode?: string
}) {
  submitError.value = null

  if (!agreementChecked.value) {
    agreementShake.value = true
    ElMessage.warning('请先阅读并同意用户协议')
    setTimeout(() => { agreementShake.value = false }, 2000)
    return
  }

  try {
    if ('account' in data && data.account) {
      await loginWithPassword(data.account, data.password!, data.rememberMe ?? false)
    } else if ('phone' in data && data.phone) {
      await loginWithPhone(data.phone, data.smsCode!)
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '登录失败，请稍后重试'
    submitError.value = msg
    ElMessage.error(msg)
  }
}

/** 按钮点击 → 触发表单验证 → 验证通过后 emit('submit') → doLogin */
function handleSubmit() {
  const formRef = activeTab.value === 'account' ? accountFormRef.value : phoneFormRef.value
  if (!formRef) return
  formRef.submit()
}
</script>

<template>
  <div class="login-view">
    <LoginCard :loading="loading">
      <LoginTabs v-model="activeTab" />

      <div class="form-area">
        <div
          :class="{ 'form-panel': true, hidden: activeTab !== 'account' }"
        >
          <AccountLoginForm ref="accountFormRef" @submit="doLogin" />
        </div>
        <div
          :class="{ 'form-panel': true, hidden: activeTab !== 'phone' }"
        >
          <PhoneLoginForm ref="phoneFormRef" @submit="doLogin" />
        </div>
      </div>

      <div v-if="submitError" class="login-error">{{ submitError }}</div>
      <div v-else-if="error" class="login-error">{{ error }}</div>

      <el-button
        type="primary"
        size="large"
        class="login-btn"
        :loading="loading"
        @click="handleSubmit"
      >
        登录
      </el-button>

      <AgreementCheckbox v-model="agreementChecked" :class="{ shake: agreementShake }" />

      <OAuthPanel />

      <RegisterLink />
    </LoginCard>
  </div>
</template>

<style scoped>
.login-view {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.form-area {
  display: grid;
}

.form-area > * {
  grid-area: 1 / 1;
}

.form-panel {
  transition: opacity 0.2s ease, visibility 0.2s ease;
}

.form-panel.hidden {
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
}

.login-error {
  color: var(--color-text-error);
  font-size: var(--font-size-agreement);
  text-align: center;
}

.login-btn {
  height: var(--size-button-height);
  border-radius: var(--radius-button);
  background: var(--color-accent-gradient);
  border: none;
  font-size: var(--font-size-button);
  font-weight: var(--font-weight-bold);
  box-shadow: var(--shadow-button);
}

.login-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.shake {
  animation: shake-anim 0.4s ease;
}

@keyframes shake-anim {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  75% { transform: translateX(6px); }
}
</style>
