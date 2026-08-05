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
    --exclude='media/avatars' \
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
    PID=$(pgrep -f "uvicorn main:app" | head -1)
    if [ -n "$PID" ]; then
        kill "$PID" 2>/dev/null
        sleep 1
        # 如果还没死，强制杀
        kill -9 "$PID" 2>/dev/null
        echo "旧进程已停止 (PID: $PID)"
    else
        echo "无旧进程运行"
    fi

    # 后台启动
    source ../.venv/bin/activate
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/aceresearch.log 2>&1 &
    NEW_PID=$!
    echo "服务已启动 (PID: $NEW_PID)"
    sleep 3

    # 验证
    CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000)
    if [ "$CODE" = "200" ]; then
        echo "HTTP 状态码: $CODE  部署成功"
    else
        echo "HTTP 状态码: $CODE  可能还在启动，查看日志: tail -20 /tmp/aceresearch.log"
    fi
REMOTE

echo ""
echo "=== 部署完成 ==="
