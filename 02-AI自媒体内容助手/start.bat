@echo off
chcp 65001 >nul
title AI自媒体内容助手 - 02
cd /d "%~dp0"

echo.
echo ========================================
echo     AI自媒体内容助手 v1.0
echo ========================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python
    pause & exit /b 1
)
echo [OK] Python

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Node.js
    pause & exit /b 1
)
echo [OK] Node.js

echo.
echo [1/2] Starting backend on port 8202...
start "P2-Backend" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8202 --reload"

echo [2/2] Starting frontend on port 3002...
start "P2-Frontend" cmd /k "cd /d "%~dp0frontend" && npx vite --host 0.0.0.0 --port 3002"

echo.
echo Waiting for backend...
:waitloop2
timeout /t 2 >nul
curl -s http://localhost:8202/api/health >nul 2>&1
if errorlevel 1 goto waitloop2

echo.
echo ========================================
echo   Backend:  http://localhost:8202/docs
echo   Frontend: http://localhost:3002
echo   Login:    admin / 123456
echo ========================================
echo.

start http://localhost:3002
pause >nul
