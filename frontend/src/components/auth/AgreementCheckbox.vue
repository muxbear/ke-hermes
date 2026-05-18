<script setup lang="ts">
import { ElMessageBox } from 'element-plus'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

function openAgreement(type: 'user' | 'privacy') {
  const title = type === 'user' ? '用户服务协议' : '隐私政策'
  ElMessageBox.alert(
    `《${title}》全文内容将在后端获取后展示。本文档为协议占位内容，实际使用中需替换为完整的协议文本。`,
    title,
    {
      confirmButtonText: '同意',
      cancelButtonText: '不同意',
      showCancelButton: true,
      distinguishCancelAndClose: true,
    },
  )
    .then(() => {
      emit('update:modelValue', true)
    })
    .catch(() => {
      // 不同意，不做操作
    })
}
</script>

<template>
  <div class="agreement-checkbox">
    <el-checkbox
      :model-value="modelValue"
      size="small"
      @update:model-value="emit('update:modelValue', $event)"
    />
    <span class="agreement-text">
      我已阅读并同意
      <a class="agreement-link" @click.prevent="openAgreement('user')">《用户服务协议》</a>
      和
      <a class="agreement-link" @click.prevent="openAgreement('privacy')">《隐私政策》</a>
    </span>
  </div>
</template>

<style scoped>
.agreement-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 6px;
}

.agreement-text {
  font-size: var(--font-size-agreement);
  color: var(--color-text-secondary);
  line-height: 1.5;
}

.agreement-link {
  color: var(--color-accent);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  text-decoration: none;
}

.agreement-link:hover {
  text-decoration: underline;
}
</style>
