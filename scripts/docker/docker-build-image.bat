@echo off
REM Docker镜像构建并保存为tar文件脚本 (Windows版本)

setlocal enabledelayedexpansion

set IMAGE_NAME=proto-sap
set IMAGE_VERSION=latest
set IMAGE_TAG=%IMAGE_NAME%:%IMAGE_VERSION%
set TAR_FILENAME=%IMAGE_NAME%-%IMAGE_VERSION%.tar
set COMPRESSED_FILENAME=%IMAGE_NAME%-%IMAGE_VERSION%.tar.gz

echo ==================================================
echo 采购订单管理系统 - Docker镜像打包
echo ==================================================
echo.
echo 镜像名称: %IMAGE_TAG%
echo 输出文件: %COMPRESSED_FILENAME%
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

REM 步骤1: 构建镜像
echo 步骤1: 构建Docker镜像...
docker build -t %IMAGE_TAG% .

if errorlevel 1 (
    echo ✗ 镜像构建失败
    pause
    exit /b 1
)

echo ✓ 镜像构建成功
echo.

REM 步骤2: 保存为tar文件
echo 步骤2: 保存镜像为tar文件...
docker save %IMAGE_TAG% -o %TAR_FILENAME%

if errorlevel 1 (
    echo ✗ 保存镜像失败
    pause
    exit /b 1
)

echo ✓ 镜像已保存为: %TAR_FILENAME%
if exist %TAR_FILENAME% (
    for /f "tokens=*" %%A in ('powershell -Command "((Get-Item %TAR_FILENAME%).Length / 1GB).ToString(\"0.00\") + \" GB\""') do (
        echo   文件大小: %%A
    )
)

echo.

REM 步骤3: 使用PowerShell压缩tar文件
echo 步骤3: 压缩tar文件（节省空间）...
echo 注：如果您安装了7-Zip或WinRAR，可以手动压缩以获得更好的压缩率
echo.

REM 尝试使用PowerShell压缩
powershell -Command "Compress-Archive -Path %TAR_FILENAME% -DestinationPath %COMPRESSED_FILENAME% -Force" 2>nul
if errorlevel 1 (
    echo ⚠ PowerShell压缩失败，tar文件已保存，可以手动使用7-Zip压缩
    echo.
) else (
    echo ✓ 压缩成功
    if exist %COMPRESSED_FILENAME% (
        for /f "tokens=*" %%A in ('powershell -Command "((Get-Item %COMPRESSED_FILENAME%).Length / 1GB).ToString(\"0.00\") + \" GB\""') do (
            echo   压缩后文件: %COMPRESSED_FILENAME%
            echo   压缩后大小: %%A
        )
    )
    echo.
)

echo ==================================================
echo ✓ 镜像打包完成！
echo ==================================================
echo.
echo 镜像信息：
docker images %IMAGE_NAME%
echo.
echo 文件信息：
if exist %COMPRESSED_FILENAME% (
    dir %COMPRESSED_FILENAME%
) else (
    dir %TAR_FILENAME%
)
echo.
echo 恢复镜像命令：
echo   docker load -i %TAR_FILENAME%
echo   或
echo   docker load -i %COMPRESSED_FILENAME%
echo.
pause
