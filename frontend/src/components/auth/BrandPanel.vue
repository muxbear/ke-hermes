<script setup lang="ts">
import FeatureGrid from './FeatureGrid.vue'
</script>

<template>
  <div class="brand-panel">
    <!-- Top spacer -->
    <div class="brand-spacer" />

    <!-- Content wrapper -->
    <div class="brand-content">
      <!-- Logo -->
      <div class="brand-logo">
        <svg viewBox="0 0 96 96" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="96" height="96" rx="20" fill="url(#logo-grad)" />
          <circle cx="48" cy="48" r="28" stroke="white" stroke-width="3" fill="none" opacity="0.9" />
          <circle cx="48" cy="48" r="14" stroke="white" stroke-width="2" fill="none" opacity="0.6" />
          <circle cx="48" cy="28" r="4" fill="white" opacity="0.8" />
          <defs>
            <linearGradient id="logo-grad" x1="0" y1="0" x2="96" y2="96">
              <stop offset="0%" stop-color="#3b82f6" />
              <stop offset="100%" stop-color="#8b5cf6" />
            </linearGradient>
          </defs>
        </svg>
      </div>

      <!-- System name -->
      <h1 class="brand-name">Ke-Hermes</h1>

      <!-- Tagline -->
      <p class="brand-tagline">自我进化，越用越强</p>

      <!-- Feature grid -->
      <FeatureGrid />
    </div>

    <!-- Bottom spacer -->
    <div class="brand-spacer" />

    <!-- Copyright -->
    <footer class="brand-footer">2026 Ke-Hermes 版权所有</footer>
  </div>
</template>

<style scoped>
.brand-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  padding: var(--size-brand-padding-v) var(--size-brand-padding-h);
}

.brand-spacer {
  flex: 1;
  min-height: 20px;
}

.brand-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--size-brand-block-gap);
}

.brand-logo {
  width: var(--size-logo);
  height: var(--size-logo);
  border-radius: var(--radius-logo);
  filter: drop-shadow(var(--shadow-logo));
}

.brand-name {
  margin: 0;
  font-size: var(--font-size-system-name);
  font-weight: var(--font-weight-bold);
  color: #ffffff;
  letter-spacing: 0.02em;
}

.brand-tagline {
  margin: 0;
  font-size: var(--font-size-tagline);
  color: var(--color-text-label);
  letter-spacing: 0.04em;
}

.brand-footer {
  font-size: var(--font-size-copyright);
  color: var(--color-text-muted);
  opacity: 0.5;
}
</style>
