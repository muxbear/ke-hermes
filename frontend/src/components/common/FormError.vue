<script setup lang="ts">
defineProps<{
  message?: string | null
}>()
</script>

<template>
  <Transition name="fade">
    <p v-if="message" class="form-error">{{ message }}</p>
  </Transition>
</template>

<style scoped>
.form-error {
  margin: 0;
  font-size: var(--font-size-agreement);
  color: var(--color-text-error);
  line-height: 1.4;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-fast);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
