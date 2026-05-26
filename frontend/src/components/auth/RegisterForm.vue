<script setup lang="ts">
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { Phone, KeyRound, User, Lock } from 'lucide-vue-next'
import PasswordInput from '@/components/common/PasswordInput.vue'
import CountdownButton from '@/components/common/CountdownButton.vue'
import FormError from '@/components/common/FormError.vue'
import AgreementCheckbox from './AgreementCheckbox.vue'
import CaptchaModal from '@/components/captcha/CaptchaModal.vue'
import { useCountdown } from '@/composables/useCountdown'
import { useCaptcha } from '@/composables/useCaptcha'
import { useAuth } from '@/composables/useAuth'
import { captchaApi } from '@/services/captchaApi'

const { register } = useAuth()
const { countdown, start: startCountdown } = useCountdown()
const { modalVisible, requestCaptcha, onCaptchaVerified, closeCaptcha } = useCaptcha()

const form = reactive({
  phone: '',
  smsCode: '',
  nickname: '',
  password: '',
  confirmPassword: '',
})

const agreementChecked = reactive({ value: false })
const errors = reactive({
  phone: '',
  smsCode: '',
  nickname: '',
  password: '',
  confirmPassword: '',
})

const submitting = reactive({ value: false })

function validate(): boolean {
  errors.phone = ''
  errors.smsCode = ''
  errors.nickname = ''
  errors.password = ''
  errors.confirmPassword = ''

  if (!/^1[3-9]\d{9}$/.test(form.phone.trim())) {
    errors.phone = '请输入正确的手机号'
    return false
  }
  if (!/^\d{6}$/.test(form.smsCode)) {
    errors.smsCode = '验证码为 6 位数字'
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
    ElMessage.warning('请先阅读并同意用户协议')
    return false
  }
  return true
}

async function onSubmit() {
  if (!validate() || submitting.value) return
  submitting.value = true
  try {
    await register({
      phone: form.phone.trim(),
      smsCode: form.smsCode,
      nickname: form.nickname.trim(),
      password: form.password,
      agreedProtocolVersion: 'v1',
    })
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '注册失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}

function handleSendSms() {
  if (!/^1[3-9]\d{9}$/.test(form.phone.trim())) {
    errors.phone = '请输入正确的手机号'
    return
  }
  errors.phone = ''
  requestCaptcha({ type: 'send-sms' })
}

async function onCaptchaSuccess(result: { ticket: string; randstr: string }) {
  onCaptchaVerified(result.ticket, result.randstr)
  try {
    await captchaApi.sendSms({
      phone: form.phone.trim(),
      captchaTicket: result.ticket,
      captchaRandstr: result.randstr,
    })
    startCountdown(60)
  } catch {
    errors.phone = '短信发送失败，请重试'
  }
}
</script>

<template>
  <div class="register-form">
    <div class="input-wrapper">
      <el-input v-model="form.phone" placeholder="请输入手机号" size="large" class="auth-input" maxlength="11">
        <template #prefix><Phone :size="18" class="input-icon" /></template>
      </el-input>
      <FormError :message="errors.phone" />
    </div>

    <div class="sms-row">
      <el-input v-model="form.smsCode" placeholder="请输入验证码" size="large" class="auth-input sms-input" maxlength="6">
        <template #prefix><KeyRound :size="18" class="input-icon" /></template>
      </el-input>
      <CountdownButton :countdown="countdown" @click="handleSendSms" />
    </div>
    <FormError :message="errors.smsCode" />

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

    <el-button type="primary" size="large" class="submit-btn" :loading="submitting.value" @click="onSubmit">
      注册
    </el-button>

    <CaptchaModal
      v-model="modalVisible"
      type="slide"
      @success="onCaptchaSuccess"
    />
  </div>
</template>

<style scoped>
.register-form {
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
