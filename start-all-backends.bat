@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title AI项目8后端一键启动
cd /d "%~dp0"

echo ================================================
echo   AI应用项目 - 8个后端一键启动
echo ================================================
echo.

start "P1-Backend" cmd /c "cd /d %~dp001-RAG智能客服系统\backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8101"
start "P2-Backend" cmd /c "cd /d %~dp002-AI自媒体内容助手\backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8202"
start "P3-Backend" cmd /c "cd /d %~dp003-AI短视频脚本工坊\backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
start "P4-Backend" cmd /c "cd /d %~dp004-AI素材管理平台\backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8400"
start "P5-Backend" cmd /c "cd /d %~dp005-AI销售培训系统\backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8505"
start "P6-Backend" cmd /c "cd /d %~dp006-AI数据中心平台\backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8606"
start "P7-Backend" cmd /c "cd /d %~dp007-MCP多智能体协作平台\backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8707"
start "P8-Backend" cmd /c "cd /d %~dp008-AI模型微调训练平台\backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8808"

echo.
echo   8个后端窗口已启动，等待就绪中...
timeout /t 15 /nobreak >nul

echo.
echo 检查健康状态:
curl -s http://127.0.0.1:8101/api/health | findstr /C:"healthy" >nul && echo   [OK] ① 客服 8101  || echo   [X] ① 客服 8101
curl -s http://127.0.0.1:8202/api/health | findstr /C:"healthy" >nul && echo   [OK] ② 自媒体 8202 || echo   [X] ② 自媒体 8202
curl -s http://127.0.0.1:8000/api/health | findstr /C:"healthy" >nul && echo   [OK] ③ 脚本 8000  || echo   [X] ③ 脚本 8000
curl -s http://127.0.0.1:8400/api/health | findstr /C:"healthy" >nul && echo   [OK] ④ 素材 8400  || echo   [X] ④ 素材 8400
curl -s http://127.0.0.1:8505/api/health | findstr /C:"healthy" >nul && echo   [OK] ⑤ 培训 8505  || echo   [X] ⑤ 培训 8505
curl -s http://127.0.0.1:8606/api/health | findstr /C:"healthy" >nul && echo   [OK] ⑥ 数据中心 8606 || echo   [X] ⑥ 数据中心 8606
curl -s http://127.0.0.1:8707/api/health | findstr /C:"healthy" >nul && echo   [OK] ⑦ 多智能体 8707 || echo   [X] ⑦ 多智能体 8707
curl -s http://127.0.0.1:8808/api/health | findstr /C:"healthy" >nul && echo   [OK] ⑧ 微调 8808  || echo   [X] ⑧ 微调 8808

echo.
pause
