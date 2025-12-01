@echo off
REM Docker镜像导出脚本 - 用于Portainer部署 (Windows版本)
REM 生成tar镜像文件和Portainer Stack配置

setlocal enabledelayedexpansion

echo ==================================================
echo Docker镜像导出 - Portainer部署
echo ==================================================
echo.

set BACKEND_IMAGE=proto-sap:latest
REM 注：docker-compose自动将镜像命名为 proto-sap-backend:latest
REM 如果镜像名称不同，请修改下面的变量
if exist "" set BACKEND_IMAGE_ALT=proto-sap-backend:latest
set POSTGRES_IMAGE=postgres:15
set BACKEND_TAR=proto-sap-latest.tar
set POSTGRES_TAR=postgres-15-latest.tar
set COMPOSE_FILE=portainer-stack.yml

echo 准备导出以下镜像：
echo   1. 后端应用: %BACKEND_IMAGE%
echo   2. PostgreSQL: %POSTGRES_IMAGE%
echo.

REM 检查Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Docker未安装
    pause
    exit /b 1
)

echo ✓ Docker已安装
echo.

REM 检查镜像存在
echo 步骤1: 检查镜像...
docker images | findstr /C:"proto-sap-backend" >nul 2>&1
if errorlevel 1 (
    echo ✗ 后端镜像不存在
    echo   请先运行: docker-compose build
    pause
    exit /b 1
)
echo ✓ 后端镜像存在

REM 获取镜像名称
for /f "tokens=1" %%A in ('docker images ^| findstr /C:"proto-sap-backend" ^| findstr "latest"') do set BACKEND_IMAGE=%%A:latest
if not defined BACKEND_IMAGE (
    for /f "tokens=1" %%A in ('docker images ^| findstr /C:"proto-sap" ^| findstr "latest" ^| findstr /v "backend"') do set BACKEND_IMAGE=%%A:latest
)

docker images | findstr /C:"postgres" >nul 2>&1
if errorlevel 1 (
    echo ✗ PostgreSQL镜像不存在
    echo   请先运行: docker pull postgres:15
    pause
    exit /b 1
)
echo ✓ PostgreSQL镜像存在

echo.

REM 步骤2: 导出镜像
echo 步骤2: 导出Docker镜像（这可能需要几分钟）...
echo   导出后端镜像...
docker save %BACKEND_IMAGE% -o %BACKEND_TAR%
echo     ✓ 已保存

echo   导出PostgreSQL镜像...
docker save %POSTGRES_IMAGE% -o %POSTGRES_TAR%
echo     ✓ 已保存

echo.

REM 步骤3: 压缩镜像
echo 步骤3: 压缩镜像（加速上传）...
powershell -Command "Compress-Archive -Path '%BACKEND_TAR%' -DestinationPath '%BACKEND_TAR%.gz' -Force" 2>nul
if errorlevel 1 (
    echo ⚠ PowerShell压缩失败，保留原tar文件
) else (
    echo   ✓ %BACKEND_TAR%.gz 已创建
    del %BACKEND_TAR%
)

powershell -Command "Compress-Archive -Path '%POSTGRES_TAR%' -DestinationPath '%POSTGRES_TAR%.gz' -Force" 2>nul
if errorlevel 1 (
    echo ⚠ PowerShell压缩失败，保留原tar文件
) else (
    echo   ✓ %POSTGRES_TAR%.gz 已创建
    del %POSTGRES_TAR%
)

echo.

REM 步骤4: 创建Portainer Stack配置
echo 步骤4: 创建Portainer Stack配置...
(
    echo version: '3.8'
    echo.
    echo services:
    echo   # PostgreSQL数据库服务
    echo   postgres:
    echo     image: postgres:15
    echo     container_name: proto-sap-db
    echo     environment:
    echo       POSTGRES_DB: ${DB_NAME:-purchase_orders}
    echo       POSTGRES_USER: ${DB_USER:-postgres}
    echo       POSTGRES_PASSWORD: ${DB_PASSWORD:-pgsql}
    echo       PGDATA: /var/lib/postgresql/data/pgdata
    echo     ports:
    echo       - "${DB_PORT:-5432}:5432"
    echo     volumes:
    echo       - postgres_data:/var/lib/postgresql/data
    echo     networks:
    echo       - proto-sap-network
    echo     restart: unless-stopped
    echo     healthcheck:
    echo       test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
    echo       interval: 10s
    echo       timeout: 5s
    echo       retries: 5
    echo     deploy:
    echo       resources:
    echo         limits:
    echo           cpus: '1'
    echo           memory: 512M
    echo         reservations:
    echo           cpus: '0.5'
    echo           memory: 256M
    echo.
    echo   # Flask后端服务
    echo   backend:
    echo     image: proto-sap:latest
    echo     container_name: proto-sap-backend
    echo     environment:
    echo       DB_HOST: postgres
    echo       DB_NAME: ${DB_NAME:-purchase_orders}
    echo       DB_USER: ${DB_USER:-postgres}
    echo       DB_PASSWORD: ${DB_PASSWORD:-pgsql}
    echo       DB_PORT: 5432
    echo       APP_HOST: 0.0.0.0
    echo       APP_PORT: ${APP_PORT:-5000}
    echo       APP_DEBUG: ${APP_DEBUG:-False}
    echo       JWT_SECRET_KEY: ${JWT_SECRET_KEY:-wefabricate-secret-key-2025}
    echo       SMTP_SERVER: ${SMTP_SERVER:-smtp.qq.com}
    echo       SMTP_PORT: ${SMTP_PORT:-587}
    echo       SENDER_EMAIL: ${SENDER_EMAIL:-your_email@qq.com}
    echo       SENDER_PASSWORD: ${SENDER_PASSWORD:-}
    echo       APP_BASE_URL: ${APP_BASE_URL:-http://localhost:5000}
    echo       EMAIL_ENABLED: ${EMAIL_ENABLED:-true}
    echo     ports:
    echo       - "${APP_PORT:-5000}:5000"
    echo     volumes:
    echo       - ./uploads:/app/uploads
    echo       - ./pdf_samples:/app/pdf_samples
    echo     depends_on:
    echo       postgres:
    echo         condition: service_healthy
    echo     networks:
    echo       - proto-sap-network
    echo     restart: unless-stopped
    echo     healthcheck:
    echo       test: ["CMD", "curl", "-f", "http://localhost:5000/"]
    echo       interval: 30s
    echo       timeout: 10s
    echo       retries: 3
    echo       start_period: 60s
    echo     deploy:
    echo       resources:
    echo         limits:
    echo           cpus: '2'
    echo           memory: 1G
    echo         reservations:
    echo           cpus: '1'
    echo           memory: 512M
    echo.
    echo volumes:
    echo   postgres_data:
    echo     driver: local
    echo.
    echo networks:
    echo   proto-sap-network:
    echo     driver: bridge
) > %COMPOSE_FILE%

echo ✓ Stack配置已创建

echo.

REM 步骤5: 创建说明文档
echo 步骤5: 创建说明文档...
(
    echo # Portainer 导入镜像指南
    echo.
    echo ## 生成的文件
    echo.
    echo - proto-sap-latest.tar.gz - 后端镜像
    echo - postgres-15-latest.tar.gz - PostgreSQL镜像
    echo - portainer-stack.yml - Stack部署配置
    echo.
    echo ## 上传到Portainer
    echo.
    echo ### 方法1: Web UI上传镜像
    echo.
    echo 1. 进入Portainer ^-> 选择远程环境
    echo 2. 左侧菜单 ^-> Images
    echo 3. 点击 "Load image"
    echo 4. 选择 proto-sap-latest.tar.gz 上传
    echo 5. 重复上传 postgres-15-latest.tar.gz
    echo.
    echo ### 方法2: 通过SSH上传
    echo.
    echo ^`^`^`bash
    echo # 复制文件到远程主机
    echo scp *.tar.gz user@docker-host:/tmp/
    echo.
    echo # 在远程主机加载镜像
    echo ssh user@docker-host
    echo docker load -i /tmp/proto-sap-latest.tar.gz
    echo docker load -i /tmp/postgres-15-latest.tar.gz
    echo rm /tmp/*.tar.gz
    echo ^`^`^`
    echo.
    echo ## 创建Stack部署
    echo.
    echo 1. Portainer ^-> Stacks ^-> Add Stack
    echo 2. 选择 "Upload docker-compose file"
    echo 3. 上传 portainer-stack.yml
    echo 4. Stack name: proto-sap
    echo 5. 点击 "Deploy"
    echo.
    echo ## 验证部署
    echo.
    echo - 进入 Containers
    echo - 应该看到两个容器: proto-sap-db 和 proto-sap-backend
    echo.
    echo ## 访问应用
    echo.
    echo - 前端: http://docker-host:5000
    echo - 数据库: docker-host:5432
) > PORTAINER_IMPORT.md

echo ✓ 说明文档已创建

echo.

REM 步骤6: 显示总结
echo ==================================================
echo ✓ 导出完成！
echo ==================================================
echo.
echo 生成的文件：
dir /h proto-sap-latest.tar* postgres-15-latest.tar* %COMPOSE_FILE% 2>nul
echo.
echo 后续步骤：
echo.
echo 1. 将以下文件上传到Portainer主机：
echo    - proto-sap-latest.tar.gz
echo    - postgres-15-latest.tar.gz
echo    - portainer-stack.yml
echo.
echo 2. 在Portainer中导入镜像：
echo    Images ^-> Load image ^-> 选择上述tar.gz文件
echo.
echo 3. 创建Stack部署：
echo    Stacks ^-> Add stack ^-> Upload docker-compose file
echo    上传 portainer-stack.yml
echo.
echo 4. 访问应用：
echo    http://docker-host:5000
echo.
echo 详细说明见: PORTAINER_IMPORT.md
echo.
pause
