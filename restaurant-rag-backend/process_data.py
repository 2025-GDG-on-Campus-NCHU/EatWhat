import json
import os

# 創建數據目錄（如果不存在）
os.makedirs('processed_data', exist_ok=True)

# 讀取餐廳列表文件 - 使用 utf-8-sig 來處理 BOM
with open('raw_data\\RestaurantList.json', 'r', encoding='utf-8-sig') as f:
    restaurant_data = json.load(f)

# 讀取營業時間文件 - 使用 utf-8-sig 來處理 BOM
with open('raw_data\\RestaurantServiceTimeList.json', 'r', encoding='utf-8-sig') as f:
    service_time_data = json.load(f)

# 從字典中獲取正確的列表
restaurant_list = restaurant_data['Restaurants']
service_time_list = service_time_data['RestaurantServiceTimes']

print(f"找到 {len(restaurant_list)} 家餐廳")
print(f"找到 {len(service_time_list)} 筆營業時間資料")

# 建立餐廳ID字典以便快速查詢
restaurant_ids = {restaurant['RestaurantName']: restaurant for restaurant in restaurant_list}

# 整合資料 - 重新結構化以適合向量資料庫
integrated_data = []
for restaurant in restaurant_list:
    # 基本資料
    restaurant_info = {
        "restaurant_name": restaurant['RestaurantName'],
        "restaurant_address": restaurant.get('RestaurantAddress', ''),
        "restaurant_tel": restaurant.get('RestaurantTel', ''),
        "restaurant_px": restaurant.get('RestaurantPosX', 0),
        "restaurant_py": restaurant.get('RestaurantPosY', 0),
        "description": restaurant.get('Description', '')
    }
    
    # 查詢該餐廳是否有營業時間資料
    restaurant_name = restaurant['RestaurantName']
    
    # 尋找匹配的服務時間
    service_time = next((item for item in service_time_list 
                       if item['RestaurantName'] == restaurant_name), None)
    
    # 格式化服務時間
    if service_time and 'ServiceTimes' in service_time:
        # 格式化營業時間信息
        service_times = service_time['ServiceTimes']
        formatted_times = []
        
        for time_slot in service_times:
            days = ', '.join(time_slot.get('ServiceDays', []))
            start_time = time_slot.get('StartTime', '')
            end_time = time_slot.get('EndTime', '')
            name = time_slot.get('Name', '')
            
            if start_time == '00:00:00' and end_time == '00:00:00':
                # 可能是公休日
                formatted_times.append(f"{name}: {days}")
            else:
                formatted_times.append(f"{name}: {days} {start_time}-{end_time}")
        
        restaurant_info['service_time'] = '; '.join(formatted_times)
    else:
        restaurant_info['service_time'] = None
    
    integrated_data.append(restaurant_info)

# 儲存整合後的資料
with open('processed_data\\integrated_restaurants.json', 'w', encoding='utf-8') as f:
    json.dump(integrated_data, f, ensure_ascii=False, indent=2)

print(f"整合完成，共有 {len(integrated_data)} 家餐廳資料")