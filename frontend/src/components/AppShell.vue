<script setup>
import SideMenu from './SideMenu.vue'
import TopBar from './TopBar.vue'
import ChatMain from './ChatMain.vue'
import RightPanel from './RightPanel.vue'
</script>

<template>
  <div class="app-shell">
    <SideMenu />
    <div class="main-column">
      <TopBar />
      <ChatMain />
    </div>
    <RightPanel />
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  height: 100vh;
  background: var(--surface-primary);
}

.main-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}
</style>