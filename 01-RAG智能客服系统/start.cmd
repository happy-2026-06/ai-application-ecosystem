@echo off
chcp 65001 >nul
title RAG智能客服系统 - 01

cd /d "%~dp0"

echo.
echo ╔════════════════════════════════════╗
echo ║   RAG 知识库问答系统 v1.0          ║
echo ╚════════════════════════════════════╝
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
echo [1/2] 启动后端 (8101)...
start "RAG-Backend-01" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8101"

echo [2/2] 启动前端 (3001)...
start "RAG-Frontend-01" cmd /k "cd /d "%~dp0frontend" && npx vite --host 0.0.0.0 --port 3001"

echo.
echo 等待服务启动...
:waitloop
timeout /t 2 >nul
curl -s http://localhost:8101/api/health >nul 2>&1
if errorlevel 1 goto waitloop

echo.
echo ╔════════════════════════════════════╗
echo ║         启动成功！                 ║
echo ║  前端: http://localhost:3001       ║
echo ║  后端: http://localhost:8101/docs  ║
echo ║  账号: admin / 123456              ║
echo ╚════════════════════════════════════╝
echo.

start http://localhost:3001
pause >nul
