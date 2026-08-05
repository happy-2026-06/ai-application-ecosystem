@echo off
chcp 65001 >nul
title AI短视频脚本工坊 - 03
cd /d "%~dp0"

echo.
echo ========================================
echo     AI短视频脚本工坊 v1.0
echo ========================================
echo.

:: ── 环境检查 ──────────────────────────────────
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] 未找到 Python, 请先安装
    pause & exit /b 1
)
echo [OK] Python

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] 未找到 Node.js, 请先安装
    pause & exit /b 1
)
echo [OK] Node.js

:: ── 清理上次异常关机的残留 ──────────────────────
echo.
echo [?] 检查上次残留...

:: 杀掉占用端口的旧进程
for %%P in (8000 3000) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%P "') do (
        taskkill /f /pid %%a >nul 2>&1
    )
)

:: 删除 Python 字节码缓存
for /d /r "%~dp0backend" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul

:: 清理 SQLite 锁文件 + 切换为 DELETE 模式（避免关机后数据库锁死）
python "%~dp0backend\scripts\db_cleanup.py" 2>nul
echo [OK] 残留已清理

:: ── 安装前端依赖（如果还没装）───────────────────
if not exist "%~dp0frontend\node_modules" (
    echo [?] 安装前端依赖...
    cd /d "%~dp0frontend"
    call npm install
    cd /d "%~dp0"
)

:: ── 启动服务 ────────────────────────────────────
echo.
echo [1/2] 启动后端 (端口 8000)...
start "P3-Backend" cmd /c "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo [2/2] 启动前端 (端口 3000)...
start "P3-Frontend" cmd /c "cd /d "%~dp0frontend" && npx vite --host 0.0.0.0 --port 3000"

:: ── 等待后端就绪 ────────────────────────────────
echo.
echo [?] 等待后端启动（最多90秒）...
ipconfig /flushdns >nul 2>&1
set tries=0
:waitloop
timeout /t 2 >nul
curl -s http://127.0.0.1:8000/api/health >nul 2>&1
if %errorlevel% equ 0 goto ready
set /a tries+=1
if %tries% lss 45 goto waitloop
echo [X] 后端启动超时！
echo    1. 检查 backend 窗口有没有报错
echo    2. 手动打开 http://127.0.0.1:3000 试试
pause
exit /b 1

:ready
echo.
echo ========================================
echo   启动成功！
echo   后端: http://127.0.0.1:8000/docs
echo   前端: http://127.0.0.1:3000
echo ========================================
echo.
echo [?] 如果浏览器没自动打开，手动访问 http://127.0.0.1:3000
echo.

start http://127.0.0.1:3000
pause
