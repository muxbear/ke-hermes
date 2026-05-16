<script setup>
import ChatHeader from './ChatHeader.vue'
import MessageList from './MessageList.vue'
import InputBar from './InputBar.vue'
</script>

<template>
  <div class="chat-main">
    <ChatHeader />
    <MessageList />
    <InputBar />
  </div>
</template>

<style scoped>
.chat-main {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--surface-primary);
}
</style>