@echo off
chcp 65001 >nul
cd /d "%~dp0"
title MineMarket

echo ============================================
echo   MineMarket 本地啟動
echo ============================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [1/3] 找不到虛擬環境，正在建立...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo 建立失敗：請先安裝 Python 3.12，並確認安裝時有勾選 "Add to PATH"。
        pause
        exit /b 1
    )
    echo       安裝套件中，第一次會比較久...
    ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
    ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
) else (
    echo [1/3] 虛擬環境已就緒
)

if not exist ".env" (
    echo.
    echo [2/3] 找不到 .env 設定檔
    echo       請先複製 .env.example 成 .env，並填入資料庫密碼。
    echo.
    pause
    exit /b 1
) else (
    echo [2/3] 設定檔已就緒
)

echo [3/3] 啟動伺服器...
echo.
echo   網址： http://localhost:7775
echo   停止： 按 Ctrl+C，或直接關閉這個視窗
echo.
echo ============================================
echo.

start "" http://localhost:7775
".venv\Scripts\python.exe" controller.py

echo.
echo 伺服器已停止。
pause
