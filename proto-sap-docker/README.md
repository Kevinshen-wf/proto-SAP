# 采购订单管理系统 - Docker Compose 完整包

此包包含应用程序所需的所有Docker镜像和配置文件。

## 包含内容

- `images/` - Docker镜像文件
  - `proto-sap-backend-latest.tar` - Flask后端应用镜像
  - `postgres-15-latest.tar` - PostgreSQL 15数据库镜像
- `docker-compose.yml` - Docker Compose配置
- `.env.docker` - 环境变量配置
- `load-images.bat` - 镜像加载脚本 (Windows)
- `start.bat` - 启动脚本 (Windows)

## 快速开始

### 1. 加载镜像

双击运行 `load-images.bat`

或手动运行：

```bash
load-images.bat
```

### 2. 配置环境变量（可选)

编辑 `.env.docker` 文件，修改数据库密码、邮件配置等。

### 3. 启动系统

双击运行 `start.bat` 或运行：

```bash
docker-compose up -d
```

### 4. 访问应用

- 前端: http://localhost:5000
- 数据库: localhost:5432

## 停止系统

```bash
docker-compose down
```

## 查看日志

```bash
docker-compose logs -f backend
docker-compose logs -f postgres
```
