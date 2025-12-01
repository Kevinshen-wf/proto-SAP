#!/bin/bash
# Docker镜像构建并保存为tar文件脚本 (Linux/Mac)

set -e

echo "=================================================="
echo "采购订单管理系统 - Docker镜像打包"
echo "=================================================="
echo ""

# 镜像名称和版本
IMAGE_NAME="proto-sap"
IMAGE_VERSION="latest"
IMAGE_TAG="${IMAGE_NAME}:${IMAGE_VERSION}"
TAR_FILENAME="${IMAGE_NAME}-${IMAGE_VERSION}.tar"
COMPRESSED_FILENAME="${IMAGE_NAME}-${IMAGE_VERSION}.tar.gz"

echo "镜像名称: $IMAGE_TAG"
echo "输出文件: $COMPRESSED_FILENAME"
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "✗ Docker未安装，请先安装Docker"
    exit 1
fi

echo "✓ Docker已安装"
echo ""

# 步骤1: 构建镜像
echo "步骤1: 构建Docker镜像..."
docker build -t $IMAGE_TAG .

if [ $? -eq 0 ]; then
    echo "✓ 镜像构建成功"
else
    echo "✗ 镜像构建失败"
    exit 1
fi

echo ""

# 步骤2: 保存为tar文件
echo "步骤2: 保存镜像为tar文件..."
docker save $IMAGE_TAG -o $TAR_FILENAME

if [ $? -eq 0 ]; then
    echo "✓ 镜像已保存为: $TAR_FILENAME"
    
    # 获取文件大小
    TAR_SIZE=$(du -h $TAR_FILENAME | cut -f1)
    echo "  文件大小: $TAR_SIZE"
else
    echo "✗ 保存镜像失败"
    exit 1
fi

echo ""

# 步骤3: 压缩tar文件
echo "步骤3: 压缩tar文件（节省空间）..."
gzip -v $TAR_FILENAME

if [ $? -eq 0 ]; then
    echo "✓ 压缩成功"
    
    # 获取压缩后文件大小
    COMPRESSED_SIZE=$(du -h $COMPRESSED_FILENAME | cut -f1)
    echo "  压缩后文件: $COMPRESSED_FILENAME"
    echo "  压缩后大小: $COMPRESSED_SIZE"
    
    # 计算压缩率
    if [ -f "$COMPRESSED_FILENAME" ]; then
        ORIGINAL_SIZE=$(stat -f%z "$TAR_FILENAME.bak" 2>/dev/null || echo "0")
        if [ "$ORIGINAL_SIZE" != "0" ]; then
            COMPRESSION_RATE=$((100 - ($(stat -f%z "$COMPRESSED_FILENAME") * 100 / ORIGINAL_SIZE)))
            echo "  压缩率: ${COMPRESSION_RATE}%"
        fi
    fi
else
    echo "⚠ 压缩失败，但tar文件已保存"
fi

echo ""
echo "=================================================="
echo "✓ 镜像打包完成！"
echo "=================================================="
echo ""
echo "镜像信息："
docker images $IMAGE_NAME
echo ""
echo "文件信息："
ls -lh $COMPRESSED_FILENAME 2>/dev/null || ls -lh $TAR_FILENAME
echo ""
echo "恢复镜像命令："
echo "  gunzip < $COMPRESSED_FILENAME | docker load"
echo "  或"
echo "  docker load < $TAR_FILENAME"
echo ""
