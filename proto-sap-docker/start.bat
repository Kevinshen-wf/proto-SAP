@echo off
setlocal enabledelayedexpansion

echo ==================================================
echo 采购订单管理系统 - 启动脚本
echo ==================================================
echo.

REM 检查Docker
if errorlevel 1 (
    echo ✗ Docker未安装
    pause
    exit /b 1
)

REM 检查.env.docker
if not exist .env.docker (
    if exist .env.docker.example (
        echo ✓ 已从示例创建.env.docker
    ) else (
        echo ✗ 找不到.env.docker配置文件
        pause
        exit /b 1
    )
)

echo 启动容器...
docker-compose up -d

if errorlevel 1 (
    echo ✗ 启动失败
    pause
    exit /b 1
)

echo ✓ 容器已启动
echo.
timeout /t 10

echo 容器状态:
docker-compose ps
echo.
echo 访问地址:
echo   - 前端: http://localhost:5000
echo   - 数据库: localhost:5432
echo.
pause
