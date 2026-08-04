@echo off
chcp 65001 >nul
title RAG智能客服系统 - 01
cd /d "%~dp0"

echo.
echo ========================================
echo     RAG智能客服系统 v1.0
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
echo [1/2] Starting backend on port 8101...
start "P1-Backend" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8101"

echo [2/2] Starting frontend on port 3001...
start "P1-Frontend" cmd /k "cd /d "%~dp0frontend" && npx vite --host 0.0.0.0 --port 3001"

echo.
echo Waiting for backend...
:waitloop1
timeout /t 2 >nul
curl -s http://localhost:8101/api/health >nul 2>&1
if errorlevel 1 goto waitloop1

echo.
echo ========================================
echo   Backend:  http://localhost:8101/docs
echo   Frontend: http://localhost:3001
echo   Login:    admin / 123456
echo ========================================
echo.

start http://localhost:3001
pause >nul
