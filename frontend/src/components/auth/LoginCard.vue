<script setup lang="ts">
withDefaults(
  defineProps<{
    loading?: boolean
  }>(),
  {
    loading: false,
  },
)
</script>

<template>
  <div class="login-card">
    <slot />
  </div>
</template>

<style scoped lang="scss">
@use '@/assets/styles/mixins.scss' as *;

.login-card {
  width: 100%;
  max-width: var(--size-card-max-width);
  padding: var(--size-card-padding);
  display: flex;
  flex-direction: column;
  gap: var(--size-card-gap);

  @include glass-card;
}
</style>
