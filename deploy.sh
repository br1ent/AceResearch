#!/bin/bash
#
# AceResearch 一键部署脚本
# 用法: ./deploy.sh [--frontend]
#   --frontend  也构建前端并部署（不改前端代码时可以跳过）

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVER="brent@114.55.0.227"
REMOTE_DIR="/home/brent/AceResearch"

echo "=== 1. 构建前端 ==="
if [ "$1" = "--frontend" ]; then
    cd "$SCRIPT_DIR/frontend"
    npm run build
    cd ..
else
    echo "跳过（使用已有 dist，加 --frontend 可强制重新构建）"
fi

echo ""
echo "=== 2. 同步后端代码 ==="
cd "$SCRIPT_DIR/backend"
tar czf - \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='.env' \
    --exclude='chroma_data' \
    --exclude='.git' \
    . | ssh "$SERVER" "cd $REMOTE_DIR/backend && tar xzf -"
echo "后端同步完成"

echo ""
echo "=== 3. 同步前端 dist ==="
cd "$SCRIPT_DIR/frontend"
tar czf - dist/ | ssh "$SERVER" "cd $REMOTE_DIR/frontend && tar xzf -"
echo "前端同步完成"

echo ""
echo "=== 4. 重启服务 ==="
ssh "$SERVER" "bash -s" << 'REMOTE'
    cd ~/AceResearch/backend

    # 停掉旧进程
    pkill -f "uvicorn main:app" 2>/dev/null && echo "旧进程已停止" || echo "无旧进程运行"
    sleep 1

    # 后台启动
    source ../.venv/bin/activate
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
    echo "服务已启动 (PID: $!)"
    sleep 2

    # 验证
    curl -s -o /dev/null -w "HTTP 状态码: %{http_code}" http://localhost:8000 && echo "" || echo "启动失败，请检查日志"
REMOTE

echo ""
echo "=== 部署完成 ==="
