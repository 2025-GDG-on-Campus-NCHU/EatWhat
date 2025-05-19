<template>
  <div class="app-container">
    <!-- 頂部標題 -->
    <div class="header">
      <h1>台灣餐廳智能推薦系統</h1>
    </div>

    <!-- 主要內容區 -->
    <div class="main-content">
      <!-- 聊天框 -->
      <div class="chat-container" ref="chatContainer">
        <!-- 歡迎訊息 -->
        <div class="message system">
          <div class="avatar system-avatar">🍽️</div>
          <div class="message-content">
            <p>您好！我是您的餐廳推薦助手。請告訴我您想找什麼類型的餐廳？</p>
            <p>例如：「台中市的日式料理」、「台北市有停車場的家庭餐廳」、「適合約會的義式餐廳」等。</p>
          </div>
        </div>

        <!-- 顯示歷史消息 -->
        <div v-for="(message, index) in messages" :key="index" :class="`message ${message.type}`">
          <div :class="`avatar ${message.type}-avatar`">
            {{ message.type === 'user' ? '👤' : '🍽️' }}
          </div>
          <div class="message-content">
            <p v-if="message.type === 'user'">{{ message.text }}</p>
            <div v-else>
              <p v-if="message.loading" class="loading">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
              </p>
              <template v-else>
                <p v-html="message.text"></p>
                
                <!-- 餐廳推薦結果 -->
                <div v-if="message.restaurants && message.restaurants.length > 0" class="restaurant-results">
                  <!-- 餐廳列表 -->
                  <div class="restaurant-list">
                    <div 
                      v-for="(restaurant, rIndex) in message.restaurants" 
                      :key="rIndex"
                      :class="['restaurant-card', selectedRestaurant === restaurant ? 'selected' : '']"
                      @click="selectRestaurant(restaurant)"
                    >
                      <div class="restaurant-img">
                        <img :src="getRestaurantImage(restaurant)" :alt="restaurant.restaurant_name">
                      </div>
                      <div class="restaurant-info">
                        <h3>{{ restaurant.restaurant_name }}</h3>
                        <p v-if="restaurant.restaurant_address"><strong>地址：</strong>{{ restaurant.restaurant_address }}</p>
                        <p v-if="restaurant.restaurant_tel"><strong>電話：</strong>{{ restaurant.restaurant_tel }}</p>
                        <p v-if="restaurant.service_time"><strong>營業時間：</strong>{{ restaurant.service_time }}</p>
                        <p v-if="restaurant.description" class="description">{{ restaurant.description }}</p>
                        <div class="actions">
                          <button @click.stop="openMapLink(restaurant)" class="btn-map">在 Google 地圖開啟</button>
                          <div class="similarity">相似度: {{ (restaurant.similarity * 100).toFixed(1) }}%</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- 輸入框 -->
      <div class="input-container">
        <textarea 
          v-model="query" 
          class="query-input" 
          placeholder="請輸入您的餐廳需求..."
          @keydown.enter.prevent="submitQuery"
          :disabled="isLoading"
          ref="inputBox"
          rows="1"
        ></textarea>
        <button 
          class="send-btn" 
          @click="submitQuery" 
          :disabled="isLoading || !query.trim()"
        >
          <span v-if="isLoading">搜尋中...</span>
          <span v-else>送出</span>
        </button>
      </div>
    </div>
    
    <!-- 餐廳詳情彈窗 -->
    <div class="restaurant-modal" v-if="showModal" @click="closeModal">
      <div class="modal-content" @click.stop>
        <button class="close-btn" @click="closeModal">×</button>
        <div v-if="selectedRestaurant">
          <div class="modal-header">
            <h2>{{ selectedRestaurant.restaurant_name }}</h2>
          </div>
          <div class="modal-body">
            <div class="modal-img">
              <img :src="getRestaurantImage(selectedRestaurant)" :alt="selectedRestaurant.restaurant_name">
            </div>
            <div class="modal-info">
              <p v-if="selectedRestaurant.restaurant_address"><strong>地址：</strong>{{ selectedRestaurant.restaurant_address }}</p>
              <p v-if="selectedRestaurant.restaurant_tel"><strong>電話：</strong>{{ selectedRestaurant.restaurant_tel }}</p>
              <p v-if="selectedRestaurant.service_time"><strong>營業時間：</strong>{{ selectedRestaurant.service_time }}</p>
              <p v-if="selectedRestaurant.description" class="description">
                <strong>介紹：</strong>{{ selectedRestaurant.description }}
              </p>
            </div>
            <div class="modal-map">
              <div id="detail-map" ref="detailMap"></div>
            </div>
            <div class="modal-actions">
              <button @click="openMapLink(selectedRestaurant)" class="btn-action">在 Google 地圖開啟</button>
              <button @click="shareRestaurant(selectedRestaurant)" class="btn-action">分享餐廳</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/* eslint-disable */
import { ref, onMounted, nextTick, watch } from 'vue'
import axios from 'axios'

export default {
  name: 'App',
  setup() {
    // 狀態
    const query = ref('')
    const isLoading = ref(false)
    const messages = ref([])
    const chatContainer = ref(null)
    const inputBox = ref(null)
    const selectedRestaurant = ref(null)
    const showModal = ref(false)
    const leafletMap = ref(null)
    const detailMap = ref(null)
    const map = ref(null)
    const modalMap = ref(null)
    const markers = ref([])

    // 餐廳圖片庫 - 使用固定的食物相關圖片
    const foodImages = [
      "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=400&h=300&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1540189549336-e6e99c3679fe?q=80&w=400&h=300&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?q=80&w=400&h=300&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?q=80&w=400&h=300&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1512621776951-a57141f2eefd?q=80&w=400&h=300&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1606787366850-de6330128bfc?q=80&w=400&h=300&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1505253758473-96b7015fcd40?q=80&w=400&h=300&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1482049016688-2d3e1b311543?q=80&w=400&h=300&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1601314002592-b8734bca6604?q=80&w=400&h=300&auto=format&fit=crop",
      "https://images.unsplash.com/photo-1476224203421-9ac39bcb3327?q=80&w=400&h=300&auto=format&fit=crop"
    ];

    // 提交查詢
    const submitQuery = async () => {
      if (!query.value.trim() || isLoading.value) return
      
      // 添加用戶消息
      messages.value.push({ type: 'user', text: query.value })
      
      // 添加系統消息（初始為加載狀態）
      const messageIndex = messages.value.push({ type: 'system', text: '', loading: true }) - 1
      
      // 滾動到底部
      await nextTick()
      scrollToBottom()
      
      isLoading.value = true
      
      try {
        // 調用API
        const response = await axios.post('http://localhost:8000/recommend', {
          query: query.value,
          top_k: 5
        })
        
        // 更新系統消息
        messages.value[messageIndex] = {
          type: 'system',
          text: formatRecommendation(response.data.recommendation),
          restaurants: response.data.restaurants,
          loading: false
        }
        
        // 清空輸入
        query.value = ''
        
        // 滾動到底部
        await nextTick()
        scrollToBottom()
      } catch (error) {
        console.error('推薦請求錯誤:', error)
        // 更新為錯誤消息
        messages.value[messageIndex] = {
          type: 'system',
          text: '抱歉，查詢時發生錯誤，請稍後再試。',
          loading: false
        }
      } finally {
        isLoading.value = false
        // 自動聚焦到輸入框
        inputBox.value.focus()
      }
    }

    // 初始化詳情地圖
    const initDetailMap = async (restaurant) => {
      await nextTick()
      
      if (!detailMap.value) {
        console.error('Detail map container not found')
        return
      }
      
      // 如果地圖已存在，清除它
      if (modalMap.value) {
        modalMap.value.remove()
        modalMap.value = null
      }
      
      try {
        // 獲取座標
        let lat = parseFloat(restaurant.restaurant_py || 0)
        let lng = parseFloat(restaurant.restaurant_px || 0)
        
        // 確認座標是否有效 (台灣區域)
        const isValidLat = lat >= 21 && lat <= 26
        const isValidLng = lng >= 119 && lng <= 123
        
        // 如果座標可能顛倒，嘗試交換調整
        if (!isValidLat && !isValidLng && parseFloat(restaurant.restaurant_px) >= 21 && parseFloat(restaurant.restaurant_px) <= 26) {
          lat = parseFloat(restaurant.restaurant_px)
          lng = parseFloat(restaurant.restaurant_py)
        }
        
        // 再次檢查座標是否有效
        if (lat >= 21 && lat <= 26 && lng >= 119 && lng <= 123) {
          createDetailMap(lat, lng, restaurant.restaurant_name)
        } 
        // 如果座標無效但有地址，使用地址進行地理編碼
        else if (restaurant.restaurant_address) {
          geocodeAddress(restaurant.restaurant_address, (lat, lng) => {
            createDetailMap(lat, lng, restaurant.restaurant_name)
          })
        } else {
          // 使用台灣中心點
          createDetailMap(23.7, 121.0, restaurant.restaurant_name)
        }
      } catch (error) {
        console.error('詳情地圖初始化錯誤:', error)
      }
    }

    // 創建詳情地圖
    const createDetailMap = (lat, lng, title) => {
      try {
        if (!detailMap.value) return
        
        modalMap.value = window.L.map(detailMap.value, { fadeAnimation: false }).setView([lat, lng], 16)
        
        window.L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(modalMap.value)
        
        window.L.marker([lat, lng]).addTo(modalMap.value)
          .bindPopup(`<b>${title}</b>`)
          .openPopup()
          
        // 強制重新計算地圖大小以修復可能的渲染問題
        setTimeout(() => {
          if (modalMap.value) {
            modalMap.value.invalidateSize(true)
          }
        }, 300)
      } catch (error) {
        console.error('創建詳情地圖錯誤:', error)
      }
    }
    
    // 地理編碼（將地址轉換為座標）
    const geocodeAddress = (address, callback) => {
      // 使用Nominatim服務（OpenStreetMap的免費地理編碼服務）
      const nominatimUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address + ',台灣')}&limit=1`
      
      console.log(`地理編碼請求: ${nominatimUrl}`)
      
      fetch(nominatimUrl)
        .then(response => response.json())
        .then(data => {
          console.log("地理編碼結果:", data)
          if (data.length > 0) {
            const lat = parseFloat(data[0].lat)
            const lng = parseFloat(data[0].lon)
            console.log(`地理編碼成功: (${lat}, ${lng})`)
            callback(lat, lng)
          } else {
            console.log("地理編碼無結果，使用預設座標")
            // 如果找不到地址，使用台灣中心點
            callback(23.7, 121.0)
          }
        })
        .catch(error => {
          console.error('地理編碼錯誤:', error)
          // 如果找不到地址，使用台灣中心點
          callback(23.7, 121.0)
        })
    }

    // 格式化推薦文本
    const formatRecommendation = (text) => {
      // 將純文本轉換為HTML
      const formattedText = text
        .replace(/\n/g, '<br>')
        .replace(/「([^」]+)」/g, '<span class="highlight">"$1"</span>')
        .replace(/(\d+\. .+)：/g, '<strong>$1</strong>：')
      
      return formattedText
    }

    // 滾動到聊天底部
    const scrollToBottom = () => {
      if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
      }
    }

    // 獲取餐廳圖片
    const getRestaurantImage = (restaurant) => {
      // 基於餐廳名稱生成隨機但一致的種子
      const seed = restaurant.restaurant_name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
      
      // 使用種子選擇一個固定的圖片
      return foodImages[seed % foodImages.length]
    }

    // 選擇餐廳
    const selectRestaurant = (restaurant) => {
      console.log("選擇餐廳:", restaurant)
      selectedRestaurant.value = restaurant
      showModal.value = true
      
      // 初始化詳情地圖
      nextTick(() => {
        initDetailMap(restaurant)
      })
    }

    // 關閉詳情視窗
    const closeModal = () => {
      showModal.value = false
    }

    // 打開地圖連結 (改用 Google Maps)
    const openMapLink = (restaurant) => {
      // 直接使用餐廳名稱和地址搜尋 Google Maps
      const query = restaurant.restaurant_address 
        ? `${restaurant.restaurant_name}, ${restaurant.restaurant_address}` 
        : restaurant.restaurant_name
        
      const url = `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query + ', 台灣')}`
      window.open(url, '_blank')
    }

    // 分享餐廳
    const shareRestaurant = (restaurant) => {
      if (navigator.share) {
        navigator.share({
          title: restaurant.restaurant_name,
          text: `我發現了一個很棒的餐廳：${restaurant.restaurant_name}${restaurant.restaurant_address ? `，地址：${restaurant.restaurant_address}` : ''}`,
          url: `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(`${restaurant.restaurant_address || restaurant.restaurant_name}, 台灣`)}`
        })
      } else {
        alert('您的瀏覽器不支持分享功能')
      }
    }

    // 自適應輸入框高度
    watch(query, () => {
      if (inputBox.value) {
        inputBox.value.style.height = 'auto'
        inputBox.value.style.height = `${Math.min(inputBox.value.scrollHeight, 120)}px`
      }
    })

    // 初始化
    onMounted(() => {
      console.log("App 已載入")
      
      // 自動聚焦到輸入框
      if (inputBox.value) {
        inputBox.value.focus()
      }
      
      // 調整輸入框高度
      if (inputBox.value) {
        inputBox.value.style.height = 'auto'
        inputBox.value.style.height = `${Math.min(inputBox.value.scrollHeight, 120)}px`
      }
    })

    return {
      query,
      isLoading,
      messages,
      chatContainer,
      inputBox,
      selectedRestaurant,
      showModal,
      leafletMap,
      detailMap,
      submitQuery,
      getRestaurantImage,
      selectRestaurant,
      closeModal,
      openMapLink,
      shareRestaurant
    }
  }
}
</script>

<style>
/* 整體應用樣式 */
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 1280px;
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  color: #333;
  background-color: #f5f5f5;
}

/* 標題欄 */
.header {
  padding: 15px 20px;
  background-color: #ff5722;
  color: white;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.header h1 {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 600;
}

/* 主內容區 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 聊天容器 */
.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  background-color: #f5f5f5;
}

/* 消息樣式 */
.message {
  display: flex;
  margin-bottom: 20px;
  animation: fadeIn 0.3s ease-out;
}

.user {
  justify-content: flex-end;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-right: 12px;
  flex-shrink: 0;
}

.user-avatar {
  background-color: #4caf50;
  margin-left: 12px;
  margin-right: 0;
  order: 2;
}

.system-avatar {
  background-color: #ff5722;
}

.message-content {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 18px;
  background: white;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  overflow-wrap: break-word;
}

.user .message-content {
  background-color: #e3f2fd;
  border-top-right-radius: 4px;
}

.system .message-content {
  background-color: white;
  border-top-left-radius: 4px;
}

.message-content p {
  margin: 0 0 10px 0;
  line-height: 1.5;
}

.message-content p:last-child {
  margin-bottom: 0;
}

.highlight {
  color: #ff5722;
  font-weight: 500;
}

/* 加載動畫 */
.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 24px;
}

.dot {
  width: 8px;
  height: 8px;
  background-color: #ff5722;
  border-radius: 50%;
  margin: 0 4px;
  animation: bounce 1.5s infinite ease-in-out;
}

.dot:nth-child(1) {
  animation-delay: 0s;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

/* 餐廳結果區 */
.restaurant-results {
  margin-top: 16px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  background: white;
}

/* 地圖容器 */
.map-container {
  width: 100%;
  height: 300px;
  background-color: #f0f0f0;
}

#leaflet-map, #detail-map {
  width: 100%;
  height: 100%;
}

/* 自定義地圖標記 */
.custom-marker-container {
  background: none;
  border: none;
}

.custom-marker {
  width: 30px;
  height: 30px;
  background-color: #ff5722;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  box-shadow: 0 2px 5px rgba(0,0,0,0.3);
}

/* 餐廳列表 */
.restaurant-list {
  max-height: 600px;
  overflow-y: auto;
  padding: 16px;
}

.restaurant-card {
  display: flex;
  margin-bottom: 16px;
  padding: 16px;
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
  cursor: pointer;
}

.restaurant-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.restaurant-card.selected {
  border: 2px solid #ff5722;
  background-color: #fff9f5;
}

.restaurant-img {
  width: 120px;
  height: 120px;
  flex-shrink: 0;
  margin-right: 16px;
  border-radius: 8px;
  overflow: hidden;
}

.restaurant-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.restaurant-info {
  flex: 1;
}

.restaurant-info h3 {
  margin: 0 0 8px 0;
  font-size: 1.2rem;
  color: #333;
}

.restaurant-info p {
  margin: 4px 0;
  font-size: 0.9rem;
  color: #666;
}

.description {
  max-height: none;
  margin-bottom: 15px;
  white-space: pre-line;
  line-height: 1.5;
  font-size: 0.9rem;
  color: #666;
}

.actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.btn-map {
  padding: 6px 12px;
  background-color: #4285f4;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
}

.similarity {
  font-size: 0.85rem;
  color: #777;
}

/* 輸入區域 */
.input-container {
  padding: 16px;
  background-color: white;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: flex-end;
}

.query-input {
  flex: 1;
  padding: 12px 16px;
  border-radius: 24px;
  border: 1px solid #ddd;
  font-size: 16px;
  resize: none;
  min-height: 24px;
  max-height: 120px;
  background-color: #f9f9f9;
  transition: all 0.2s;
}

.query-input:focus {
  outline: none;
  border-color: #ff5722;
  background-color: white;
  box-shadow: 0 0 0 2px rgba(255, 87, 34, 0.1);
}

.send-btn {
  margin-left: 12px;
  padding: 10px 20px;
  background-color: #ff5722;
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.send-btn:hover {
  background-color: #f4511e;
}

.send-btn:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

/* 餐廳詳情彈窗 */
.restaurant-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  animation: fadeIn 0.3s;
}

.modal-content {
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  background-color: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  position: relative;
  animation: slideUp 0.3s;
}

.close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 30px;
  height: 30px;
  background-color: rgba(0, 0, 0, 0.2);
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.modal-header {
  padding: 20px;
  background-color: #ff5722;
  color: white;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.8rem;
}

.modal-body {
  padding: 20px;
  max-height: calc(90vh - 70px);
  overflow-y: auto;
}

.modal-img {
  width: 100%;
  height: 250px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 20px;
}

.modal-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.modal-info p {
  margin: 10px 0;
  font-size: 1rem;
  line-height: 1.6;
}

.modal-map {
  margin: 20px 0;
  border-radius: 8px;
  overflow: hidden;
  height: 300px;
}

.modal-actions {
  display: flex;
  margin-top: 20px;
}

.btn-action {
  padding: 10px 16px;
  margin-right: 12px;
  background-color: #4285f4;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.95rem;
  cursor: pointer;
}

.btn-action:hover {
  background-color: #3367d6;
}

.btn-action:last-child {
  background-color: #34a853;
}

.btn-action:last-child:hover {
  background-color: #2d9144;
}

/* 動畫 */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(30px); }
  to { transform: translateY(0); }
}

@keyframes bounce {
  0%, 80%, 100% { 
    transform: scale(0);
  }
  40% { 
    transform: scale(1);
  }
}

/* 響應式設計 */
@media (max-width: 768px) {
  .restaurant-card {
    flex-direction: column;
  }
  
  .restaurant-img {
    width: 100%;
    height: 180px;
    margin-right: 0;
    margin-bottom: 16px;
  }
  
  .query-input {
    font-size: 14px;
  }
  
  .send-btn {
    padding: 8px 16px;
    font-size: 14px;
  }
  
  .modal-content {
    width: 95%;
  }
}
</style>