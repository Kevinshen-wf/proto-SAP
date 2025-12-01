@echo off
REM Docker快速启动脚本 (Windows版本)

setlocal enabledelayedexpansion

echo ==================================================
echo 采购订单管理系统 - Docker启动脚本 (Windows)
echo ==================================================
echo.

REM 检查Docker是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Docker未安装，请先安装Docker Desktop
    pause
    exit /b 1
)

echo ✓ Docker已安装
echo.

REM 检查.env.docker文件
if not exist .env.docker (
    echo ⚠ .env.docker文件不存在，正在从示例文件创建...
    if exist .env.docker.example (
        copy .env.docker.example .env.docker
        echo ✓ 已创建.env.docker文件，请根据需要修改
    ) else (
        echo ✗ 找不到.env.docker.example文件
        pause
        exit /b 1
    )
)

echo ✓ 环境配置文件已就绪
echo.

REM 启动服务
echo 启动Docker容器...
docker-compose up -d

if errorlevel 1 (
    echo ✗ 启动失败，请检查Docker和docker-compose
    pause
    exit /b 1
)

echo.
echo ✓ 容器已启动
echo.

REM 等待数据库就绪
echo 等待数据库就绪...
timeout /t 5

REM 检查容器状态
echo.
echo ==================================================
echo 容器状态：
echo ==================================================
docker-compose ps
echo.

REM 数据库会在容器启动脚本中自动初始化
echo 数据库正在创建中，请等待...
timeout /t 10

echo.
echo ==================================================
echo ✓ 系统启动完成！
echo ==================================================
echo.
echo 访问地址：
echo   - 前端: http://localhost:5000
echo   - 数据库: localhost:5432
echo.
echo 常用命令：
echo   - 查看日志: docker-compose logs -f
echo   - 进入容器: docker-compose exec backend bash
echo   - 停止服务: docker-compose down
echo.
echo 注：数据库初始化需要 30-60 秒，请等待系统完全就绪
echo.
pause
