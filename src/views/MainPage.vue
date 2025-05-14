<template>
  <div class="w-full max-w-screen-xl mx-auto px-4 py-8">
    <ChatBox class="mb-6" />

    <Carousel
      :items-to-show="3"
      :wrap-around="true"
      :transition="500"
      :center-mode="true"
      class="overflow-visible"
    >
      <Slide
        v-for="(restaurant, index) in restaurants"
        :key="index"
        class="flex justify-center"
      >
        <div
          class="transition-transform duration-500 ease-in-out"
          :class="{
            'scale-110 z-20': currentIndex === index,
            'scale-90 opacity-70 z-10 -mx-4': currentIndex !== index,
          }"
        >
          <RestaurantCard
            :name="restaurant.name"
            :description="restaurant.description"
            :imageUrl="restaurant.imageUrl"
            :address="restaurant.address"
            :rating="restaurant.rating"
            :isActive="currentIndex === index"
          />
        </div>
      </Slide>
    </Carousel>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Carousel, Slide } from 'vue3-carousel'
import 'vue3-carousel/dist/carousel.css'
import RestaurantCard from '@/components/RestaurantCard.vue'
import ChatBox from '@/components/ChatBox.vue'

const currentIndex = ref(0)

const restaurants = [
  {
    name: '鼎泰豐',
    description: '世界知名的小籠包餐廳',
    imageUrl: 'https://picsum.photos/400/200?random=1',
    address: '台北市信義區',
    rating: '4.8 / 5',
  },
  {
    name: '永康牛肉麵',
    description: '紅燒與清燉牛肉麵皆受歡迎',
    imageUrl: 'https://picsum.photos/400/200?random=2',
    address: '台北市大安區',
    rating: '4.6 / 5',
  },
  {
    name: '阿宗麵線',
    description: '香濃大腸麵線、快速美味',
    imageUrl: 'https://picsum.photos/400/200?random=3',
    address: '台北市西門町',
    rating: '4.3 / 5',
  },
  {
    name: '阜杭豆漿',
    description: '人氣早餐，豆漿燒餅油條',
    imageUrl: 'https://picsum.photos/400/200?random=4',
    address: '台北市中正區',
    rating: '4.7 / 5',
  },
]
</script>