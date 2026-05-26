<script setup>
import ChatMain from './ChatMain.vue'
import RightPanel from './RightPanel.vue'
</script>

<template>
  <div class="app-shell">
    <div class="chat-column">
      <ChatMain />
    </div>
    <RightPanel />
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  height: 100%;
  background: var(--surface-primary);
}

.chat-column {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}
</style>