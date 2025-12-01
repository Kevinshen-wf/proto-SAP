@echo off
REM Portainer部署诊断脚本 (Windows版本)

setlocal enabledelayedexpansion

echo ==================================================
echo Portainer Proto-SAP 诊断脚本
echo ==================================================
echo.

REM 步骤1: 检查容器状态
echo 步骤1: 检查容器状态...
echo.
docker ps | findstr proto-sap
echo.

docker ps | findstr proto-sap-backend >nul 2>&1
if errorlevel 1 (
    echo ✗ 后端容器未运行
    echo.
    echo 请检查:
    echo   1. 在Portainer中查看 proto-sap Stack状态
    echo   2. 查看容器日志: docker logs proto-sap-backend
    pause
    exit /b 1
)

echo ✓ 容器正在运行
echo.

REM 步骤2: 检查端口映射
echo 步骤2: 检查端口映射...
echo.
for /f "tokens=*" %%A in ('docker inspect proto-sap-backend --format="table {{.ID}}"') do set CONTAINER_ID=%%A

docker inspect proto-sap-backend | findstr /C:"5000" >nul 2>&1
if errorlevel 1 (
    echo ✗ 警告: 端口5000映射不正确
    echo.
    echo 可能的原因:
    echo   1. Stack部署时端口映射失败
    echo   2. 环境变量 APP_PORT 配置错误
    echo.
    echo 解决方案:
    echo   1. 删除现有Stack: docker-compose down
    echo   2. 确认portainer-stack.yml中的端口是硬编码: ports: ["5000:5000"]
    echo   3. 重新部署Stack
    pause
    exit /b 1
)

echo ✓ 端口映射正确
echo.

REM 步骤3: 测试容器内连接
echo 步骤3: 测试容器内连接...
echo.
docker exec proto-sap-backend curl -s http://localhost:5000/ >nul 2>&1
if errorlevel 1 (
    echo ✗ 容器内部无法访问应用
    echo.
    echo 查看日志:
    docker logs proto-sap-backend | powershell -Command "Select-Object -Last 20"
    pause
    exit /b 1
)

echo ✓ 容器内部可以访问 http://localhost:5000/
echo.

REM 步骤4: 测试本机连接
echo 步骤4: 测试本机连接...
echo.
powershell -Command "try { Invoke-WebRequest http://localhost:5000/ -ErrorAction SilentlyContinue | Out-Null; $true } catch { $false }" >nul 2>&1
if errorlevel 1 (
    echo ✗ 无法访问 http://localhost:5000/
    echo.
    echo 可能的原因:
    echo   1. 防火墙阻止了5000端口
    echo   2. 应用未正确启动
    echo   3. 端口被其他应用占用
    echo.
    echo 检查端口占用:
    netstat -ano | findstr :5000
    pause
    exit /b 1
)

echo ✓ 可以访问 http://localhost:5000/
echo.

REM 最终状态
echo ==================================================
echo ✓ 诊断完成
echo ==================================================
echo.
echo 访问应用:
echo   http://localhost:5000
echo   http://127.0.0.1:5000
echo.
echo 如果仍然无法访问,请:
echo   1. 查看容器日志: docker logs -f proto-sap-backend
echo   2. 进入容器调试: docker exec -it proto-sap-backend bash
echo   3. 查看容器详细信息: docker inspect proto-sap-backend
echo.
pause
