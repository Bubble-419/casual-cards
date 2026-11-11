#!/bin/zsh
set -eu

project_root="${0:A:h:h}"
backend_pid=""
frontend_pid=""

cleanup() {
  [[ -n "$backend_pid" ]] && kill "$backend_pid" 2>/dev/null || true
  [[ -n "$frontend_pid" ]] && kill "$frontend_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

(
  cd "$project_root/backend"
  uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
) &
backend_pid=$!

(
  cd "$project_root/frontend"
  pnpm dev
) &
frontend_pid=$!

echo "Casual Cards 已启动：http://localhost:5173"
echo "按 Ctrl+C 停止前端与本地服务。"

wait
