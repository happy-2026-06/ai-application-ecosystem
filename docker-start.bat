@echo off
chcp 65001 >nul
title AI项目集群 — Docker 一键部署
cd /d "%~dp0"

echo.
echo ================================================
echo   AI项目集群 — Docker 部署
echo ================================================
echo.
echo   [?] 首次构建需要几分钟下载镜像...
echo       之后每次启动只需 5-15 秒
echo.

echo [1/3] 构建镜像...
docker compose build
if %errorlevel% neq 0 (
    echo [X] 构建失败！请确认 Docker Desktop 已启动。
    pause
    exit /b 1
)

echo.
echo [2/3] 启动全部服务...
docker compose up -d
if %errorlevel% neq 0 (
    echo [X] 启动失败！
    pause
    exit /b 1
)

echo.
echo [3/3] 等待服务就绪...
echo     (数据库 + 3个后端 + 3个前端)
echo.

:: 检查所有端口
set OK=0
for /l %%i in (1,1,60) do (
    timeout /t 2 /nobreak >nul
    set COUNT=0

    curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8101/api/health 2>nul | find "200" >nul && set /a COUNT+=1
    curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8202/api/health 2>nul | find "200" >nul && set /a COUNT+=1
    curl -s -o nul -w "%%{http_code}" http://127.0.0.1:8000/api/health 2>nul | find "200" >nul && set /a COUNT+=1

    echo     等待中... !COUNT!/3 就绪 (%%i*2s^)

    if !COUNT! geq 3 (
        set OK=1
        goto :ready
    )
)

:ready
echo.

if %OK%==1 (
    echo ================================================
    echo   全部启动完成!
    echo ================================================
    echo.
    echo   项目① RAG客服:       http://127.0.0.1:3001
    echo   项目② 自媒体助手:     http://127.0.0.1:3002
    echo   项目③ 短视频工坊:     http://127.0.0.1:3000
    echo.

    start http://127.0.0.1:3001
    timeout /t 1 /nobreak >nul
    start http://127.0.0.1:3002
    timeout /t 1 /nobreak >nul
    start http://127.0.0.1:3000
) else (
    echo [!] 部分服务启动较慢，请稍后手动刷新浏览器。
)

echo.
echo 提示: 关闭此窗口不会停止服务。
echo       停止服务请用: docker compose down
echo.

pause
