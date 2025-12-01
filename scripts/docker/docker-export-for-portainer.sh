#!/bin/bash
# Docker镜像导出脚本 - 用于Portainer部署 (Linux/Mac)
# 生成tar镜像文件和Portainer Stack配置

set -e

echo "=================================================="
echo "Docker镜像导出 - Portainer部署"
echo "=================================================="
echo ""

BACKEND_IMAGE="proto-sap:latest"
POSTGRES_IMAGE="postgres:15"
BACKEND_TAR="proto-sap-latest.tar"
POSTGRES_TAR="postgres-15-latest.tar"
COMPOSE_FILE="portainer-stack.yml"

echo "准备导出以下镜像："
echo "  1. 后端应用: $BACKEND_IMAGE"
echo "  2. PostgreSQL: $POSTGRES_IMAGE"
echo ""

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo "✗ Docker未安装"
    exit 1
fi

echo "✓ Docker已安装"
echo ""

# 检查后端镜像
echo "步骤1: 检查镜像..."
if ! docker images | grep -q "proto-sap"; then
    echo "✗ 后端镜像不存在"
    echo "  请先运行: docker-compose build"
    exit 1
fi
echo "✓ 后端镜像存在"

# 自动检测镜像名称
BACKEND_IMAGE=$(docker images | grep "proto-sap" | grep "latest" | awk '{print $1":"$2}' | head -1)
if [ -z "$BACKEND_IMAGE" ]; then
    echo "✗ 找不到proto-sap镜像"
    exit 1
fi
echo "  使用镜像: $BACKEND_IMAGE"

if ! docker images | grep -q "postgres"; then
    echo "✗ PostgreSQL镜像不存在"
    echo "  请先运行: docker pull postgres:15"
    exit 1
fi
echo "✓ PostgreSQL镜像存在"

echo ""

# 步骤2: 导出镜像
echo "步骤2: 导出Docker镜像..."
echo "  导出后端镜像（这可能需要几分钟）..."
docker save $BACKEND_IMAGE -o $BACKEND_TAR
BACKEND_SIZE=$(du -h $BACKEND_TAR | cut -f1)
echo "    ✓ 大小: $BACKEND_SIZE"

echo "  导出PostgreSQL镜像..."
docker save $POSTGRES_IMAGE -o $POSTGRES_TAR
POSTGRES_SIZE=$(du -h $POSTGRES_TAR | cut -f1)
echo "    ✓ 大小: $POSTGRES_SIZE"

echo ""

# 步骤3: 压缩镜像（可选）
echo "步骤3: 压缩镜像（加速上传）..."
gzip -v $BACKEND_TAR
gzip -v $POSTGRES_TAR
echo "✓ 压缩完成"

echo ""

# 步骤4: 创建Portainer Stack配置
echo "步骤4: 创建Portainer Stack配置..."
cat > $COMPOSE_FILE << 'EOF'
version: '3.8'

services:
  # PostgreSQL数据库服务
  postgres:
    image: postgres:15
    container_name: proto-sap-db
    environment:
      POSTGRES_DB: ${DB_NAME:-purchase_orders}
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-pgsql}
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "${DB_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - proto-sap-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

  # Flask后端服务
  backend:
    image: proto-sap:latest
    container_name: proto-sap-backend
    environment:
      DB_HOST: postgres
      DB_NAME: ${DB_NAME:-purchase_orders}
      DB_USER: ${DB_USER:-postgres}
      DB_PASSWORD: ${DB_PASSWORD:-pgsql}
      DB_PORT: 5432
      APP_HOST: 0.0.0.0
      APP_PORT: ${APP_PORT:-5000}
      APP_DEBUG: ${APP_DEBUG:-False}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-wefabricate-secret-key-2025}
      SMTP_SERVER: ${SMTP_SERVER:-smtp.qq.com}
      SMTP_PORT: ${SMTP_PORT:-587}
      SENDER_EMAIL: ${SENDER_EMAIL:-your_email@qq.com}
      SENDER_PASSWORD: ${SENDER_PASSWORD:-}
      APP_BASE_URL: ${APP_BASE_URL:-http://localhost:5000}
      EMAIL_ENABLED: ${EMAIL_ENABLED:-true}
    ports:
      - "${APP_PORT:-5000}:5000"
    volumes:
      - ./uploads:/app/uploads
      - ./pdf_samples:/app/pdf_samples
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - proto-sap-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '1'
          memory: 512M

volumes:
  postgres_data:
    driver: local

networks:
  proto-sap-network:
    driver: bridge
EOF

echo "✓ Stack配置已创建"

echo ""

# 步骤5: 创建说明文档
echo "步骤5: 创建说明文档..."
cat > PORTAINER_IMPORT.md << 'EOF'
# Portainer 导入镜像指南

## 生成的文件

- `proto-sap-latest.tar.gz` - 后端镜像（约800MB-1.5GB压缩后）
- `postgres-15-latest.tar.gz` - PostgreSQL镜像（约300MB-400MB压缩后）
- `portainer-stack.yml` - Stack部署配置

## 上传到Portainer

### 方法1: Web UI上传镜像

1. 进入Portainer → 选择远程环境
2. 左侧菜单 → Images
3. 点击 "Load image"
4. 选择 `proto-sap-latest.tar.gz` 上传
5. 重复上传 `postgres-15-latest.tar.gz`

### 方法2: 通过SSH上传

```bash
# 复制文件到远程主机
scp *.tar.gz user@docker-host:/tmp/

# 在远程主机加载镜像
ssh user@docker-host
docker load -i /tmp/proto-sap-latest.tar.gz
docker load -i /tmp/postgres-15-latest.tar.gz
rm /tmp/*.tar.gz
```

## 创建Stack部署

1. Portainer → Stacks → Add Stack
2. 选择 "Upload docker-compose file"
3. 上传 `portainer-stack.yml`
4. Stack name: `proto-sap`
5. 编辑环境变量（可选）
6. 点击 "Deploy"

## 验证部署

- 进入 Containers
- 应该看到两个运行中的容器：
  - `proto-sap-db`
  - `proto-sap-backend`

## 访问应用

- 前端: http://docker-host:5000
- 数据库: docker-host:5432

## 故障排查

### 镜像加载失败
```bash
# SSH进入主机，手动加载
docker load -i /tmp/proto-sap-latest.tar.gz
```

### 容器无法启动
```bash
# 查看日志
docker logs proto-sap-backend
docker logs proto-sap-db
```

### 数据库连接失败
```bash
# 检查网络
docker network inspect proto-sap-network

# 测试连接
docker exec proto-sap-backend nc -zv postgres 5432
```
EOF

echo "✓ 说明文档已创建"

echo ""

# 步骤6: 显示总结
echo "=================================================="
echo "✓ 导出完成！"
echo "=================================================="
echo ""
echo "生成的文件："
ls -lh proto-sap-latest.tar.gz postgres-15-latest.tar.gz portainer-stack.yml 2>/dev/null || echo "正在压缩..."
echo ""
echo "后续步骤："
echo ""
echo "1. 将以下文件上传到Portainer主机或本地Portainer:"
echo "   - proto-sap-latest.tar.gz"
echo "   - postgres-15-latest.tar.gz"
echo "   - portainer-stack.yml"
echo ""
echo "2. 在Portainer中导入镜像:"
echo "   Images → Load image → 选择上述tar.gz文件"
echo ""
echo "3. 创建Stack部署:"
echo "   Stacks → Add stack → Upload docker-compose file"
echo "   上传 portainer-stack.yml"
echo ""
echo "4. 访问应用:"
echo "   http://docker-host:5000"
echo ""
echo "详细说明见: PORTAINER_IMPORT.md"
echo ""
