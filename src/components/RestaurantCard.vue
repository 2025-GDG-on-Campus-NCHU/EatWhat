<template>
  <div class="rounded-xl bg-white shadow-xl p-4 w-[280px] lg:w-[360px] transition-all duration-500">
    <img
      :src="imageUrl"
      alt="restaurant"
      class="w-full h-48 object-cover rounded-lg"
    />
    <h2 class="text-xl font-bold mt-3">{{ name }}</h2>
    <p class="text-gray-600 mt-1">{{ description }}</p>
    <p class="text-gray-500 text-sm mt-1">📍 {{ address }}</p>
    <p class="text-yellow-500 font-semibold mt-1">⭐ {{ rating }}</p>

    <transition name="fade">
      <div v-if="isActive" class="mt-4">
        <iframe
          width="100%" height="200"
          :src="'https://www.google.com/maps?q=' + encodeURIComponent(address) + '&output=embed'"
          frameborder="0" allowfullscreen
          class="rounded-md"
        ></iframe>
        <button class="mt-2 text-blue-600 hover:text-white hover:bg-blue-600 border border-blue-600 px-4 py-1 rounded-full transition-all">
          查看菜單
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup>
const props = defineProps({
  name: String,
  description: String,
  imageUrl: String,
  address: String,
  rating: String,
  isActive: Boolean
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>