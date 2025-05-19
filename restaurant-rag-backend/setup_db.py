import psycopg2
import os
from dotenv import load_dotenv
import sys

# 載入環境變數
load_dotenv()

# 獲取資料庫連接信息
host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

try:
    # 連接到默認資料庫
    print(f"連接到PostgreSQL，用戶: {user}, 主機: {host}...")
    conn = psycopg2.connect(
        host=host,
        database="postgres",  # 連接到默認資料庫
        user=user,
        password=password
    )
    conn.autocommit = True  # 開啟自動提交
    cursor = conn.cursor()

    # 檢查restaurant_rag資料庫是否存在
    cursor.execute("SELECT 1 FROM pg_database WHERE datname='restaurant_rag'")
    exists = cursor.fetchone()
    
    if not exists:
        print("創建restaurant_rag資料庫...")
        cursor.execute("CREATE DATABASE restaurant_rag")
        print("資料庫創建成功！")
    else:
        print("restaurant_rag資料庫已存在")
    
    # 關閉到默認資料庫的連接
    cursor.close()
    conn.close()
    
    # 連接到restaurant_rag資料庫
    print("連接到restaurant_rag資料庫...")
    conn = psycopg2.connect(
        host=host,
        database="restaurant_rag",
        user=user,
        password=password
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # 檢查pgvector擴展是否已安裝
    try:
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname='vector'")
        vector_exists = cursor.fetchone()
        
        if not vector_exists:
            print("安裝pgvector擴展...")
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            print("pgvector擴展安裝成功！")
        else:
            print("pgvector擴展已安裝")
    except Exception as e:
        print(f"安裝pgvector擴展時出錯: {e}")
        print("請確保您已經正確安裝了pgvector擴展。您可能需要手動安裝它。")
    
    # 檢查restaurants表是否存在
    cursor.execute("SELECT 1 FROM information_schema.tables WHERE table_name='restaurants'")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("創建restaurants表...")
        cursor.execute("""
        CREATE TABLE restaurants (
            id SERIAL PRIMARY KEY,
            restaurant_name TEXT NOT NULL,
            restaurant_address TEXT,
            restaurant_tel TEXT,
            restaurant_px NUMERIC,
            restaurant_py NUMERIC,
            service_time TEXT,
            description TEXT,
            embedding vector(384)
        )
        """)
        print("restaurants表創建成功！")
    else:
        # 檢查description列是否存在
        cursor.execute("SELECT 1 FROM information_schema.columns WHERE table_name='restaurants' AND column_name='description'")
        description_exists = cursor.fetchone()
        
        if not description_exists:
            print("添加description列...")
            cursor.execute("ALTER TABLE restaurants ADD COLUMN description TEXT")
            print("description列添加成功！")
        else:
            print("description列已存在")
    
    # 報告結果
    cursor.execute("SELECT COUNT(*) FROM restaurants")
    row_count = cursor.fetchone()[0]
    print(f"restaurants表中有 {row_count} 行數據")
    
    print("資料庫設置完成！")

except Exception as e:
    print(f"設置資料庫時出錯: {e}")
    print(f"確保PostgreSQL服務正在運行，且連接信息正確: 主機={host}, 用戶={user}")
    print("如果您無法連接，請檢查PostgreSQL是否正在運行，密碼是否正確。")
    sys.exit(1)
finally:
    if 'cursor' in locals() and cursor:
        cursor.close()
    if 'conn' in locals() and conn:
        conn.close()