from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import psycopg2.extras
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import os
import time
from typing import List, Optional
from dotenv import load_dotenv
import traceback

# 載入環境變數
load_dotenv()

app = FastAPI()

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應限制為前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加簡單緩存
query_cache = {}

# 初始化計時器
start_time = time.time()
print(f"[{time.time() - start_time:.2f}s] 啟動服務...")

# 載入模型
print(f"[{time.time() - start_time:.2f}s] 載入Sentence Transformer模型...")
embedding_model = SentenceTransformer("models/sentence-transformer")
print(f"[{time.time() - start_time:.2f}s] Sentence Transformer模型載入完成")

# 載入Gemma 2b模型
print(f"[{time.time() - start_time:.2f}s] 載入Gemma 2b模型...")
tokenizer = AutoTokenizer.from_pretrained("models/gemma-2b")
model = AutoModelForCausalLM.from_pretrained(
    "models/gemma-2b",
    device_map="cuda:0",
    torch_dtype=torch.float16,
    use_cache=True,  # 啟用KV緩存加速推理
    low_cpu_mem_usage=True  # 降低CPU內存使用
)
print(f"[{time.time() - start_time:.2f}s] Gemma 2b模型載入完成")

# 創建資料庫連接池
from psycopg2 import pool

# 初始化連接池
connection_pool = None

def init_connection_pool():
    global connection_pool
    try:
        connection_pool = pool.SimpleConnectionPool(
            1, 10,  # 最小和最大連接數
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "restaurant_rag"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "a00010002")
        )
        print(f"[{time.time() - start_time:.2f}s] 資料庫連接池初始化成功")
    except Exception as e:
        print(f"[{time.time() - start_time:.2f}s] 初始化連接池出錯: {e}")
        connection_pool = None

# 初始化連接池
init_connection_pool()

# 獲取連接的新函數，使用連接池
def get_db_connection():
    if connection_pool:
        conn = connection_pool.getconn()
        print(f"[{time.time() - start_time:.2f}s] 從連接池獲取連接")
        return conn
    else:
        # 使用原來的直接連接作為備選
        try:
            print(f"[{time.time() - start_time:.2f}s] 創建新資料庫連接")
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                database=os.getenv("DB_NAME", "restaurant_rag"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "a00010002")
            )
            return conn
        except Exception as e:
            print(f"[{time.time() - start_time:.2f}s] 資料庫連接錯誤: {e}")
            return None

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class Restaurant(BaseModel):
    id: int
    restaurant_name: str
    restaurant_address: Optional[str] = None
    restaurant_tel: Optional[str] = None
    restaurant_px: Optional[float] = None
    restaurant_py: Optional[float] = None
    service_time: Optional[str] = None
    description: Optional[str] = None
    similarity: float

@app.post("/search", response_model=List[Restaurant])
async def search_restaurants(request: QueryRequest):
    request_start_time = time.time()
    print(f"[{request_start_time - start_time:.2f}s] 收到搜索請求: {request.query}")
    
    try:
        # 將查詢轉換為嵌入向量
        encode_start = time.time()
        print(f"[{encode_start - start_time:.2f}s] 開始生成查詢向量...")
        query_embedding = embedding_model.encode(request.query)
        print(f"[{time.time() - start_time:.2f}s] 向量生成完成，耗時: {time.time() - encode_start:.2f}s")
        
        # 在資料庫中搜尋相似餐廳
        db_start = time.time()
        print(f"[{db_start - start_time:.2f}s] 連接資料庫...")
        conn = get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="無法連接到資料庫，請檢查日誌獲取更多信息")
            
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # 使用向量相似度搜尋
        # 注意pgvector要求向量格式為 [1,2,3]
        vector_str = f"[{','.join(str(x) for x in query_embedding.tolist())}]"
        
        query_start = time.time()
        print(f"[{query_start - start_time:.2f}s] 執行向量搜索查詢...")
        cur.execute("""
            SELECT id, restaurant_name, restaurant_address, restaurant_tel, 
                   restaurant_px, restaurant_py, service_time, description,
                   1 - (embedding <=> %s::vector) as similarity
            FROM restaurants
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (vector_str, vector_str, request.top_k))
        
        results = cur.fetchall()
        print(f"[{time.time() - start_time:.2f}s] 查詢完成，找到 {len(results)} 條結果，查詢耗時: {time.time() - query_start:.2f}s")
        
        # 釋放資源
        cur.close()
        if connection_pool:
            connection_pool.putconn(conn)
        else:
            conn.close()
        
        # 轉換結果為API響應格式
        restaurants = [
            Restaurant(
                id=row['id'],
                restaurant_name=row['restaurant_name'],
                restaurant_address=row['restaurant_address'],
                restaurant_tel=row['restaurant_tel'],
                restaurant_px=row['restaurant_px'],
                restaurant_py=row['restaurant_py'],
                service_time=row['service_time'],
                description=row.get('description', ''),
                similarity=float(row['similarity'])
            )
            for row in results
        ]
        
        print(f"[{time.time() - start_time:.2f}s] 搜索請求處理完成，總耗時: {time.time() - request_start_time:.2f}s")
        return restaurants
    except Exception as e:
        print(f"[{time.time() - start_time:.2f}s] 處理搜索請求時出錯: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"處理請求時出錯: {str(e)}")

@app.post("/recommend")
async def recommend_restaurants(request: QueryRequest):
    request_start_time = time.time()
    print(f"[{request_start_time - start_time:.2f}s] 收到推薦請求: {request.query}")
    
    # 檢查緩存
    cache_key = request.query.strip().lower()
    if cache_key in query_cache:
        print(f"[{time.time() - start_time:.2f}s] 使用緩存結果: {cache_key}")
        return query_cache[cache_key]
    
    try:
        # 首先獲取相似的餐廳
        db_start = time.time()
        print(f"[{db_start - start_time:.2f}s] 連接資料庫...")
        conn = get_db_connection()
        if conn is None:
            raise HTTPException(status_code=500, detail="無法連接到資料庫，請檢查日誌獲取更多信息")
        
        # 檢查資料庫中是否有餐廳數據
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT COUNT(*) FROM restaurants")
        count = cur.fetchone()[0]
        print(f"[{time.time() - start_time:.2f}s] 資料庫中有 {count} 家餐廳")
        
        if count == 0:
            print(f"[{time.time() - start_time:.2f}s] 資料庫中沒有餐廳數據，請先導入數據")
            if connection_pool:
                connection_pool.putconn(conn)
            else:
                conn.close()
            raise HTTPException(status_code=404, detail="資料庫中沒有餐廳數據，請先導入數據")
        
        # 將查詢轉換為嵌入向量
        encode_start = time.time()
        print(f"[{encode_start - start_time:.2f}s] 開始生成查詢向量...")
        query_embedding = embedding_model.encode(request.query)
        print(f"[{time.time() - start_time:.2f}s] 向量生成完成，耗時: {time.time() - encode_start:.2f}s")
        
        # 創建正確格式的向量字符串
        vector_str = f"[{','.join(str(x) for x in query_embedding.tolist())}]"
        
        # 搜尋最相似的餐廳
        query_start = time.time()
        print(f"[{query_start - start_time:.2f}s] 執行向量搜索查詢，查找最相似的 {request.top_k} 家餐廳...")
        cur.execute("""
            SELECT id, restaurant_name, restaurant_address, restaurant_tel, 
                   restaurant_px, restaurant_py, service_time, description,
                   1 - (embedding <=> %s::vector) as similarity
            FROM restaurants
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """, (vector_str, vector_str, request.top_k))
        
        results = cur.fetchall()
        print(f"[{time.time() - start_time:.2f}s] 查詢完成，找到 {len(results)} 條結果，查詢耗時: {time.time() - query_start:.2f}s")
        
        # 釋放資料庫連接
        cur.close()
        if connection_pool:
            connection_pool.putconn(conn)
        else:
            conn.close()
        
        if not results:
            print(f"[{time.time() - start_time:.2f}s] 未找到相關餐廳")
            raise HTTPException(status_code=404, detail="No restaurants found")
        
        # 記錄結果詳情
        print(f"[{time.time() - start_time:.2f}s] 搜索結果:")
        for idx, row in enumerate(results):
            print(f"  結果 {idx+1}: {row['restaurant_name']}, 相似度: {row['similarity']:.4f}")
        
        # 準備提示給Gemma 2b
        prompt_start = time.time()
        print(f"[{prompt_start - start_time:.2f}s] 準備模型推理提示...")
        restaurant_info = ""
        for idx, row in enumerate(results, 1):
            restaurant_info += f"{idx}. {row['restaurant_name']}"
            if row['restaurant_address']:
                restaurant_info += f", 地址: {row['restaurant_address']}"
            if row['restaurant_tel']:
                restaurant_info += f", 電話: {row['restaurant_tel']}"
            if row['service_time']:
                restaurant_info += f", 營業時間: {row['service_time']}"
            if row.get('description'):
                restaurant_info += f"\n   描述: {row['description']}"
            restaurant_info += "\n"
        
        prompt = f"""以下是用戶的需求: "{request.query}"
        
根據用戶需求，以下是幾個可能符合的台灣餐廳:

{restaurant_info}

請根據用戶需求簡要分析哪些餐廳最適合，並提供1-2句推薦理由。僅使用繁體中文回答。"""
        
        # 生成Gemma 2b的回應
        model_start = time.time()
        print(f"[{model_start - start_time:.2f}s] 開始Gemma 2b模型推理...")
        print(f"[{model_start - start_time:.2f}s] 提示長度: {len(prompt)} 字符")
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # 修正警告問題：添加do_sample=True參數
        print(f"[{time.time() - start_time:.2f}s] 執行模型生成...")
        outputs = model.generate(
            **inputs, 
            max_new_tokens=256,  # 減少生成的token數量
            do_sample=True,  # 添加此參數消除警告
            temperature=0.7,
            top_p=0.9,
        )
        
        print(f"[{time.time() - start_time:.2f}s] 模型生成完成，解碼輸出...")
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        model_time = time.time() - model_start
        print(f"[{time.time() - start_time:.2f}s] 模型推理完成，耗時: {model_time:.2f}s")
        
        # 如果回應包含原始提示，則去除
        if response.startswith(prompt):
            response = response[len(prompt):]
        
        # 構建完整回應
        restaurants = [
            {
                "id": row['id'],
                "restaurant_name": row['restaurant_name'],
                "restaurant_address": row['restaurant_address'],
                "restaurant_tel": row['restaurant_tel'],
                "restaurant_px": row['restaurant_px'],
                "restaurant_py": row['restaurant_py'],
                "service_time": row['service_time'],
                "description": row.get('description', ''),
                "similarity": float(row['similarity'])
            }
            for row in results
        ]
        
        total_time = time.time() - request_start_time
        print(f"[{time.time() - start_time:.2f}s] 推薦請求處理完成，總耗時: {total_time:.2f}s")
        
        result = {
            "query": request.query,
            "restaurants": restaurants,
            "recommendation": response.strip(),
            "processing_time": total_time
        }
        
        # 緩存結果
        query_cache[cache_key] = result
        return result
    except Exception as e:
        print(f"[{time.time() - start_time:.2f}s] 處理推薦請求時出錯: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"處理請求時出錯: {str(e)}")

# 添加健康檢查端點
@app.get("/health")
async def health_check():
    return {"status": "ok", "uptime": time.time() - start_time}

# 添加緩存管理端點
@app.get("/cache/stats")
async def cache_stats():
    return {
        "size": len(query_cache),
        "keys": list(query_cache.keys())
    }

@app.post("/cache/clear")
async def clear_cache():
    query_cache.clear()
    return {"status": "cache cleared", "size": 0}

if __name__ == "__main__":
    print(f"[{time.time() - start_time:.2f}s] 服務初始化完成，即將啟動HTTP服務器...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)