# 采购订单管理系统（Proto-SAP）

基于Python Flask和PostgreSQL的采购订单管理系统。

## 快速开始

docker build -t proto-sap .
docker save proto-sap -o proto-sap.tar

### Docker部署（推荐）

```bash
# 启动应用
.\deploy.ps1 start

# 或使用docker compose
docker compose up -d
```

### 访问应用

- **前端首页**: http://localhost:5000
- **数据库管理**: http://localhost:5000/database_management.html
- **PDF导入**: http://localhost:5000/pdf_import.html

## 项目结构

```
proto-SAP/
├── backend/          # Flask后端应用
├── frontend/         # 前端HTML/CSS/JS
├── config/           # 配置文件
├── scripts/          # 脚本工具
├── tests/            # 单元测试
├── utils/            # 工具函数
├── docs/             # 文档
├── Dockerfile        # Docker镜像定义
├── docker-compose.yml # Docker编排
├── init_db.py        # 数据库初始化
├── requirements.txt   # Python依赖
├── deploy.ps1        # 部署脚本
└── README.md         # 项目说明
```

## 常用命令

### 使用部署脚本

```powershell
# 启动
.\deploy.ps1 start

# 重新构建并启动
.\deploy.ps1 start -rebuild

# 查看日志
.\deploy.ps1 logs

# 停止
.\deploy.ps1 stop

# 重启
.\deploy.ps1 restart

# 清理数据
.\deploy.ps1 clean
```

### 使用docker compose

```bash
# 启动
docker compose up -d

# 重新构建并启动
docker compose up -d --build

# 停止
docker compose down

# 查看日志
docker compose logs -f backend
```

## 功能特性

- ✅ WF/Non-WF采购订单管理
- ✅ PDF导入和数据提取
- ✅ 数据验证和编辑
- ✅ 发货管理和跟踪
- ✅ 用户认证和权限控制
- ✅ 操作日志记录
- ✅ 响应式UI设计
- ✅ Docker容器化部署

## 环境配置

修改 `.env` 文件配置环境变量：

```env
DB_HOST=postgres
DB_NAME=purchase_orders
DB_USER=postgres
DB_PASSWORD=pgsql
DB_PORT=5432
```

## 技术栈

- **后端**: Python 3.11 + Flask
- **数据库**: PostgreSQL 15
- **前端**: Bootstrap 5 + Vanilla JS
- **部署**: Docker + Docker Compose

## 许可证

MIT
