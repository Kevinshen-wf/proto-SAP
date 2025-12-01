#!/bin/bash
set -e

echo "========================================"
echo "Proto-SAP 应用启动脚本"
echo "========================================"
echo ""

echo "第1步: 检查数据库连接..."
echo "数据库主机: ${DB_HOST:-localhost}"
echo "数据库名: ${DB_NAME:-purchase_orders}"
echo ""

echo "第2步: 等待数据库就绪（最多等待60秒）..."
for i in {1..60}; do
  if pg_isready -h ${DB_HOST:-localhost} -U ${DB_USER:-postgres} -p ${DB_PORT:-5432} >/dev/null 2>&1; then
    echo "✓ 数据库连接成功"
    break
  fi
  echo "  等待中... ($i/60)"
  sleep 1
done

echo ""
echo "第3步: 初始化数据库表..."
if python init_db.py; then
  echo "✓ 数据库初始化成功"
else
  echo "✗ 数据库初始化失败"
  exit 1
fi

echo ""
echo "第4步: 启动Flask应用..."
echo "应用地址: http://0.0.0.0:5000"
echo "========================================"
echo ""

python backend/app.py
