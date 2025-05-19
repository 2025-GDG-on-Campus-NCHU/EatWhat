@echo off
echo start backend server...
cd restaurant-rag-backend
call rag_env\Scripts\activate
python app.py