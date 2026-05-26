<script setup lang="ts">
import { reactive } from 'vue'
import { Phone, KeyRound } from 'lucide-vue-next'
import CountdownButton from '@/components/common/CountdownButton.vue'
import FormError from '@/components/common/FormError.vue'
import { useCountdown } from '@/composables/useCountdown'
import { useCaptcha } from '@/composables/useCaptcha'
import { useCaptchaStore } from '@/stores/captcha'
import CaptchaModal from '@/components/captcha/CaptchaModal.vue'
import { captchaApi } from '@/services/captchaApi'

const emit = defineEmits<{
  submit: [payload: { phone: string; smsCode: string }]
}>()

const form = reactive({
  phone: '',
  smsCode: '',
})

const errors = reactive({
  phone: '',
  smsCode: '',
})

const { countdown, start: startCountdown } = useCountdown()
const { modalVisible, requestCaptcha, onCaptchaVerified, closeCaptcha } = useCaptcha()
const captchaStore = useCaptchaStore()

function validatePhone(): boolean {
  errors.phone = ''
  if (!form.phone.trim()) {
    errors.phone = '请输入手机号'
    return false
  }
  if (!/^1[3-9]\d{9}$/.test(form.phone.trim())) {
    errors.phone = '请输入正确的手机号'
    return false
  }
  return true
}

async function handleSendSms() {
  if (!validatePhone()) return

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
    captchaStore.startSmsCountdown(60)
  } catch {
    errors.phone = '短信发送失败，请重试'
  }
}

function validate(): boolean {
  errors.phone = ''
  errors.smsCode = ''

  if (!validatePhone()) return false
  if (!form.smsCode || !/^\d{6}$/.test(form.smsCode)) {
    errors.smsCode = '验证码为 6 位数字'
    return false
  }
  return true
}

function onSubmit() {
  if (!validate()) return false
  emit('submit', {
    phone: form.phone.trim(),
    smsCode: form.smsCode,
  })
  return true
}

defineExpose({
  validate,
  getFormData: () => ({
    phone: form.phone.trim(),
    smsCode: form.smsCode,
  }),
  submit: onSubmit,
})
</script>

<template>
  <div class="phone-login-form">
    <!-- Phone -->
    <div class="input-wrapper">
      <el-input
        v-model="form.phone"
        placeholder="请输入手机号"
        size="large"
        class="auth-input"
        maxlength="11"
      >
        <template #prefix>
          <Phone :size="20" class="input-icon" />
        </template>
      </el-input>
      <FormError :message="errors.phone" />
    </div>

    <!-- SMS Code -->
    <div class="sms-row">
      <el-input
        v-model="form.smsCode"
        placeholder="请输入验证码"
        size="large"
        class="auth-input sms-input"
        maxlength="6"
      >
        <template #prefix>
          <KeyRound :size="20" class="input-icon" />
        </template>
      </el-input>
      <CountdownButton
        :countdown="countdown"
        :disabled="!form.phone.trim() || countdown > 0"
        @click="handleSendSms"
      />
    </div>
    <FormError :message="errors.smsCode" />

    <!-- Captcha Modal -->
    <CaptchaModal
      v-model="modalVisible"
      type="slide"
      @success="onCaptchaSuccess"
      @fail="closeCaptcha"
    />
  </div>
</template>

<style scoped>
.phone-login-form {
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
</style>
