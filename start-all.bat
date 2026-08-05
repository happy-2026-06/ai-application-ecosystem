@echo off
chcp 65001 >nul
title AI项目一键启动 — 双击即用
cd /d "%~dp0"

echo.
echo ╔══════════════════════════════════════╗
echo ║   AI项目一键启动  v2.0               ║
echo ║   自带故障自动恢复，持续在线          ║
echo ╚══════════════════════════════════════╝

:: ── 环境检查 ──────────────────────────────────
where python >nul 2>&1 || (echo [X] 未找到 Python & pause & exit /b 1)
where node >nul 2>&1   || (echo [X] 未找到 Node.js & pause & exit /b 1)

:: ── 清理残留 ──────────────────────────────────
echo.
echo [?] 清理上次关机残留...
for %%P in (8000 3000 8101 3001 8202 3002) do (
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%%P " ^| findstr "LISTENING"') do (
        taskkill /f /pid %%a >nul 2>&1
    )
)
for %%d in ("01-RAG智能客服系统" "02-AI自媒体内容助手" "03-AI短视频脚本工坊") do (
    if exist "%~dp0%%~d\backend\scripts\db_cleanup.py" python "%~dp0%%~d\backend\scripts\db_cleanup.py" >nul 2>&1
)
for /d /r "%~dp0" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo [OK] 残留已清理

:: ── 启动所有服务 ──────────────────────────────
echo.
echo [?] 启动6个服务...

start "P1-Backend"  /min cmd /c "cd /d "%~dp001-RAG智能客服系统\backend"  && python -m uvicorn app.main:app --host 0.0.0.0 --port 8101"
start "P1-Frontend" /min cmd /c "cd /d "%~dp001-RAG智能客服系统\frontend" && npx vite --host 0.0.0.0 --port 3001"
start "P2-Backend"  /min cmd /c "cd /d "%~dp002-AI自媒体内容助手\backend"  && python -m uvicorn app.main:app --host 0.0.0.0 --port 8202"
start "P2-Frontend" /min cmd /c "cd /d "%~dp002-AI自媒体内容助手\frontend" && npx vite --host 0.0.0.0 --port 3002"
start "P3-Backend"  /min cmd /c "cd /d "%~dp003-AI短视频脚本工坊\backend"  && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
start "P3-Frontend" /min cmd /c "cd /d "%~dp003-AI短视频脚本工坊\frontend" && npx vite --host 0.0.0.0 --port 3000"

:: ── 等待就绪 ──────────────────────────────────
echo.
echo [?] 等待后端启动...
set tries=0
:waitloop
timeout /t 3 >nul
set /a tries+=1
set /a ok=0
curl -s http://127.0.0.1:8101/api/health >nul 2>&1 && set /a ok+=1
curl -s http://127.0.0.1:8202/api/health >nul 2>&1 && set /a ok+=1
curl -s http://127.0.0.1:8000/api/health >nul 2>&1 && set /a ok+=1
if %ok% equ 3 goto ready
if %tries% lss 30 goto waitloop

echo [WARN] 部分服务启动较慢 (%ok%/3)，守护进程会在后台自动修复
goto show

:ready
echo [OK] 全部就绪！

:show
echo.
echo ╔══════════════════════════════════════╗
echo ║          启动完成！                  ║
echo ║  P1 http://127.0.0.1:3001            ║
echo ║  P2 http://127.0.0.1:3002            ║
echo ║  P3 http://127.0.0.1:3000            ║
echo ╚══════════════════════════════════════╝
echo.
echo [?] 按任意键关闭此窗口（服务不会停）
pause >nul

start http://127.0.0.1:3001
start http://127.0.0.1:3002
start http://127.0.0.1:3000

:: ═══════════════════════════════════════════════
:: 守护循环 — 每30秒巡检，挂了自动拉起
:: ═══════════════════════════════════════════════
:guard
timeout /t 30 >nul

set chg=0

netstat -ano | find ":8101 " | find "LISTENING" >nul 2>&1 || (
    echo [%time%] P1后端挂了→重启
    python "%~dp001-RAG智能客服系统\backend\scripts\db_cleanup.py" >nul 2>&1
    start "P1-Backend" /min cmd /c "cd /d "%~dp001-RAG智能客服系统\backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8101"
    set chg=1
)
netstat -ano | find ":3001 " | find "LISTENING" >nul 2>&1 || (
    echo [%time%] P1前端挂了→重启
    start "P1-Frontend" /min cmd /c "cd /d "%~dp001-RAG智能客服系统\frontend" && npx vite --host 0.0.0.0 --port 3001"
    set chg=1
)
netstat -ano | find ":8202 " | find "LISTENING" >nul 2>&1 || (
    echo [%time%] P2后端挂了→重启
    python "%~dp002-AI自媒体内容助手\backend\scripts\db_cleanup.py" >nul 2>&1
    start "P2-Backend" /min cmd /c "cd /d "%~dp002-AI自媒体内容助手\backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8202"
    set chg=1
)
netstat -ano | find ":3002 " | find "LISTENING" >nul 2>&1 || (
    echo [%time%] P2前端挂了→重启
    start "P2-Frontend" /min cmd /c "cd /d "%~dp002-AI自媒体内容助手\frontend" && npx vite --host 0.0.0.0 --port 3002"
    set chg=1
)
netstat -ano | find ":8000 " | find "LISTENING" >nul 2>&1 || (
    echo [%time%] P3后端挂了→重启
    python "%~dp003-AI短视频脚本工坊\backend\scripts\db_cleanup.py" >nul 2>&1
    start "P3-Backend" /min cmd /c "cd /d "%~dp003-AI短视频脚本工坊\backend" && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    set chg=1
)
netstat -ano | find ":3000 " | find "LISTENING" >nul 2>&1 || (
    echo [%time%] P3前端挂了→重启
    start "P3-Frontend" /min cmd /c "cd /d "%~dp003-AI短视频脚本工坊\frontend" && npx vite --host 0.0.0.0 --port 3000"
    set chg=1
)
if %chg% equ 1 echo [%time%] 已自动修复

goto guard
