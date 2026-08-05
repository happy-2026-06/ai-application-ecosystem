@echo off
chcp 65001 >nul
title AI短视频脚本工坊
cd /d "%~dp0"

echo.
echo ╔════════════════════════════════════╗
echo ║   AI短视频脚本工坊 v1.0            ║
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
echo [1/2] 启动后端 (8000)...
start "VideoFactory-Backend" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [2/2] 启动前端 (3000)...
start "VideoFactory-Frontend" cmd /k "cd /d "%~dp0frontend" && npx vite --host 0.0.0.0 --port 3000"

echo.
echo 等待服务启动...
:waitloop
timeout /t 2 >nul
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 goto waitloop

echo.
echo ╔════════════════════════════════════╗
echo ║         启动成功！                 ║
echo ║  前端: http://localhost:3000       ║
echo ║  后端: http://localhost:8000/docs  ║
echo ║  账号: admin / admin123            ║
echo ╚════════════════════════════════════╝
echo.

start http://localhost:3000
pause >nul
