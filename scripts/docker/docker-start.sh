#!/bin/bash
# Docker快速启动脚本

set -e

echo "=================================================="
echo "采购订单管理系统 - Docker启动脚本"
echo "=================================================="
echo ""

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "✗ Docker未安装，请先安装Docker"
    exit 1
fi

echo "✓ Docker已安装"

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "✗ Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi

echo "✓ Docker Compose已安装"
echo ""

# 检查是否存在.env.docker文件
if [ ! -f .env.docker ]; then
    echo "⚠ .env.docker文件不存在，正在从示例文件创建..."
    if [ -f .env.docker.example ]; then
        cp .env.docker.example .env.docker
        echo "✓ 已创建.env.docker文件，请根据需要修改"
    else
        echo "✗ 找不到.env.docker.example文件"
        exit 1
    fi
fi

echo "✓ 环境配置文件已就绪"
echo ""

# 启动服务
echo "启动Docker容器..."
docker-compose up -d

echo ""
echo "✓ 容器已启动"
echo ""

# 等待数据库就绪
echo "等待数据库就绪..."
sleep 5

# 检查容器状态
echo ""
echo "=================================================="
echo "容器状态："
echo "=================================================="
docker-compose ps
echo ""

# 数据库会在容器启动脚本中自动创建
echo "数据库正在创建中，请稍例..."
sleep 10

echo ""
echo "=================================================="
echo "✓ 系统启动完成！"
echo "=================================================="
echo ""
echo "访问地址："
echo "  - 前端: http://localhost:5000"
echo "  - 数据库: localhost:5432"
echo ""
echo "常用命令："
echo "  - 查看日志: docker-compose logs -f"
echo "  - 进入容器: docker-compose exec backend bash"
echo "  - 停止服务: docker-compose down"
echo ""
echo "注：数据库初始化需要 30-60 秒，请等待系统完全就绪"
echo ""
