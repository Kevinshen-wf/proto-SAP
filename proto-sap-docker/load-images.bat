@echo off
setlocal enabledelayedexpansion

echo ==================================================
echo 加载Docker镜像
echo ==================================================
echo.

cd images

echo 加载后端镜像...
docker load -i proto-sap-backend-latest.tar
echo ✓ 后端镜像已加载
echo.

echo 加载PostgreSQL镜像...
docker load -i postgres-15-latest.tar
echo ✓ PostgreSQL镜像已加载
echo.

cd ..

echo ==================================================
echo ✓ 所有镜像已加载！
echo ==================================================
echo.
echo 现在可以运行:
echo   docker-compose up -d
echo.
pause
