@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   项目⑤ — 话术对战教练
echo   后端: http://localhost:8505
echo   前端: http://localhost:3005
echo ========================================
echo.

REM Start backend
echo [1/2] 启动后端 (端口 8505)...
start "P5Backend" cmd /c "cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8505 --reload"

REM Wait a moment for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo [2/2] 启动前端 (端口 3005)...
start "P5Frontend" cmd /c "cd frontend && npm run dev"

echo.
echo [OK] 项目⑤启动完成！
echo   后端 API 文档: http://localhost:8505/api/docs
echo   前端页面:      http://localhost:3005
echo.
echo 按任意键退出...
pause >nul
