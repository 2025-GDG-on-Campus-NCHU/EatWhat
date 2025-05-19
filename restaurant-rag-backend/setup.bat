@echo off
echo Taiwan Restaurant Recommendation RAG System Installation Script
echo ===========================

echo Creating directory structure...
mkdir raw_data
mkdir processed_data
mkdir models

echo Creating Python virtual environment...
python -m venv rag_env
call rag_env\Scripts\activate

echo Installing Python dependencies...
pip install fastapi uvicorn sentence-transformers transformers torch pandas numpy python-dotenv huggingface_hub fastapi accelerate
pip install --only-binary :all: psycopg2-binary

echo Setting up_db...
python setup_db.py

echo Processing restaurant data...
python process_data.py

echo Downloading embedding model and generating vectors...
python generate_embeddings.py

echo Downloading Gemma 2b model...
python download_gemma.py

echo Installation complete!
echo.
echo Please ensure PostgreSQL is installed and configured with pgvector extension.
echo To start the backend service, run: python app.py
echo To start the frontend service, open another command prompt, navigate to restaurant-rag-frontend directory and run: npm run serve
echo.
pause