d@echo off
echo 安裝pgvector擴展...

:: 從.env文件加載PostgreSQL路徑
for /f "tokens=1,* delims==" %%a in (.env) do (
    if "%%a"=="PGBIN_PATH" set PGBIN_PATH=%%b
)

:: 如果.env中沒有設置，使用默認路徑
if "%PGBIN_PATH%"=="" set PGBIN_PATH=D:\PostgreSQL\16\bin

echo 使用PostgreSQL路徑: %PGBIN_PATH%

:: 下載pgvector
if not exist pgvector (
    echo 下載pgvector...
    git clone https://github.com/pgvector/pgvector.git
    if %ERRORLEVEL% NEQ 0 (
        echo 無法使用git下載pgvector。
        echo 請手動下載: https://github.com/pgvector/pgvector/archive/refs/heads/master.zip
        echo 並解壓到當前目錄中的pgvector文件夾
        pause
        exit /b 1
    )
)

:: 進入pgvector目錄
cd pgvector

:: 設置環境變量
set PATH=%PGBIN_PATH%;%PATH%

:: 編譯和安裝pgvector
echo 編譯和安裝pgvector...
make
make install

:: 返回原始目錄
cd ..

echo pgvector安裝完成！
pause