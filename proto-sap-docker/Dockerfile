# 使用官方Python镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制项目文件
COPY . .

# 创建上传目录
RUN mkdir -p uploads

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/')" || exit 1

# 创建初始化脚本
RUN echo '#!/bin/bash\n\
set -e\n\
echo "等待数据库就绪..."\n\
sleep 10\n\
echo "初始化数据库..."\n\
python init_db.py || true\n\
echo "启动Flask应用..."\n\
python backend/app.py' > /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# 启动应用
ENTRYPOINT ["/app/docker-entrypoint.sh"]
