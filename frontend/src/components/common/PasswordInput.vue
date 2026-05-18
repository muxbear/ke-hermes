<script setup lang="ts">
import { ref, computed } from 'vue'
import { Eye, EyeOff } from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    modelValue: string
    placeholder?: string
    disabled?: boolean
  }>(),
  {
    placeholder: '请输入密码',
    disabled: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const showPassword = ref(false)
const inputType = computed(() => (showPassword.value ? 'text' : 'password'))
const allowPaste = import.meta.env.VITE_ALLOW_PASTE_PASSWORD !== 'false'

function onInput(e: Event) {
  const target = e.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <div class="password-input">
    <input
      :type="inputType"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :autocomplete="allowPaste ? 'current-password' : 'off'"
      class="input-field"
      @input="onInput"
      @paste="allowPaste ? undefined : (e: ClipboardEvent) => e.preventDefault()"
    />
    <button
      type="button"
      class="toggle-btn"
      :disabled="disabled"
      @click="showPassword = !showPassword"
    >
      <EyeOff v-if="showPassword" :size="18" />
      <Eye v-else :size="18" />
    </button>
  </div>
</template>

<style scoped>
.password-input {
  display: flex;
  align-items: center;
  height: var(--size-input-height);
  padding: 0 14px;
  border-radius: var(--radius-input);
  background: var(--color-bg-input);
  border: 1px solid var(--color-border-input);
  transition: border-color var(--transition-fast);
}

.password-input:focus-within {
  border-color: var(--color-accent);
  box-shadow: 0px 0px 0px 2px rgba(59, 130, 246, 0.15);
}

.input-field {
  flex: 1;
  border: none;
  outline: none;
  background: none;
  color: var(--color-text-primary);
  font-size: var(--font-size-input);
  font-family: var(--font-family-base);
}

.input-field::placeholder {
  color: var(--color-text-muted);
}

.input-field:disabled {
  opacity: 0.5;
}

.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-full);
  background: none;
  color: var(--color-text-muted);
  cursor: pointer;
  flex-shrink: 0;
}

.toggle-btn:hover {
  color: var(--color-text-secondary);
}
</style>
