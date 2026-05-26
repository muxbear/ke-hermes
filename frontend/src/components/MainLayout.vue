<script setup lang="ts">
import SideMenu from './SideMenu.vue'
import TopBar from './TopBar.vue'
</script>

<template>
  <div class="main-layout">
    <SideMenu />
    <div class="right-area">
      <TopBar />
      <div class="work-area">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<style scoped>
.main-layout {
  display: flex;
  height: 100vh;
  background: var(--surface-primary);
}

.right-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.work-area {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}
</style>
