<script setup lang="ts">
import BrandPanel from './BrandPanel.vue'
</script>

<template>
  <div class="auth-layout">
    <aside class="auth-layout__brand">
      <BrandPanel />
    </aside>
    <main class="auth-layout__form">
      <RouterView />
    </main>
  </div>
</template>

<style scoped lang="scss">
@use '@/assets/styles/mixins.scss' as *;

.auth-layout {
  display: flex;
  height: 100vh;
  background: var(--color-bg-form-area);
}

.auth-layout__brand {
  width: 40%;
  min-width: 0;
  background: var(--brand-gradient);
  overflow: hidden;
}

.auth-layout__form {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-form-area);
  overflow-y: auto;
}

@include respond-md {
  .auth-layout__brand {
    width: 32%;
  }
}

@include respond-sm {
  .auth-layout__brand {
    display: none;
  }
}
</style>
