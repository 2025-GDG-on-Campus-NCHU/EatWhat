import json
import os
import numpy as np
import psycopg2
from psycopg2.extras import execute_values
from huggingface_hub import login
from sentence_transformers import SentenceTransformer

# 創建數據目錄（如果不存在）
os.makedirs('models', exist_ok=True)

# 登入Hugging Face
login(token="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")

# 載入embedding模型 (使用多語言模型以支持中文)
print("下載和載入Sentence Transformer模型...")
model_name = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
model = SentenceTransformer(model_name)
model.save('models/sentence-transformer')
print("模型下載完成並保存到本地")

# 讀取整合後的餐廳資料
print("讀取整合後的餐廳資料...")
with open('processed_data\\integrated_restaurants.json', 'r', encoding='utf-8') as f:
    restaurants = json.load(f)

# 準備嵌入的文本
print("準備餐廳描述文本...")
texts = []
for restaurant in restaurants:
    # 結合餐廳名稱和描述來創建豐富的表示
    text = f"{restaurant['restaurant_name']}"
    if restaurant.get('description'):
        text += f" {restaurant['description']}"
    if restaurant.get('restaurant_address'):
        text += f" 地址: {restaurant['restaurant_address']}"
    if restaurant.get('service_time'):
        text += f" 營業時間: {restaurant['service_time']}"
    texts.append(text)

# 生成嵌入
print(f"為{len(texts)}家餐廳生成嵌入向量...")
embeddings = model.encode(texts, show_progress_bar=True)
print("嵌入生成完成")

# 連接PostgreSQL
print("連接到PostgreSQL資料庫...")
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "restaurant_rag"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "a00010002")
)
cur = conn.cursor()

# 清空表格（如有必要）
cur.execute("TRUNCATE TABLE restaurants")

# 檢查description列是否存在
cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name='restaurants' AND column_name='description'")
description_exists = cur.fetchone()

if not description_exists:
    print("添加description列...")
    cur.execute("ALTER TABLE restaurants ADD COLUMN description TEXT")
    print("description列添加成功！")

# 將資料插入資料庫
print("將餐廳資料與嵌入向量存入資料庫...")
for i, restaurant in enumerate(restaurants):
    # 创建正确格式的向量字符串
    vector_str = f"[{','.join(str(x) for x in embeddings[i].tolist())}]"
    
    cur.execute(
        """
        INSERT INTO restaurants (
            restaurant_name, restaurant_address, restaurant_tel, 
            restaurant_px, restaurant_py, service_time, description, embedding
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
        """,
        (
            restaurant['restaurant_name'],
            restaurant.get('restaurant_address', ''),
            restaurant.get('restaurant_tel', ''),
            restaurant.get('restaurant_px', 0),
            restaurant.get('restaurant_py', 0),
            restaurant.get('service_time', ''),
            restaurant.get('description', ''),  # 添加了description字段
            vector_str  # 修改为向量字符串格式
        )
    )

conn.commit()
cur.close()
conn.close()

print(f"已將 {len(restaurants)} 家餐廳資料及其嵌入向量存入資料庫")