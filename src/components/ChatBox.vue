<!-- ChatBox.vue -->
<template>
  <div class="rounded-xl shadow-md p-4 bg-gradient-to-r from-indigo-100 to-white">
    <h2 class="text-lg font-bold mb-2">AI 美食推薦助理 🤖</h2>
    <input
      v-model="userInput"
      placeholder="請輸入您喜歡的口味或地區..."
      class="w-full border border-gray-300 rounded-md p-2"
    />
    <button
      @click="sendQuery"
      class="mt-2 bg-indigo-500 text-white px-4 py-2 rounded-md hover:bg-indigo-600"
    >
      發送
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const userInput = ref('')
function sendQuery() {
  alert(`假裝傳送查詢：「${userInput.value}」給 AI 模型！`)
  userInput.value = ''
}
</script>