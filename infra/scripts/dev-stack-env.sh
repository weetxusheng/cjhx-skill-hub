#!/usr/bin/env bash
# 本地一键栈 URL：由根目录 .env 中的 DEV_HOST / 各端口驱动（供 start/ensure 脚本 source；固定 HTTP）。
# shellcheck disable=SC2034
: "${DEV_HOST:=127.0.0.1}"
: "${API_PORT:=8000}"
: "${ADMIN_DEV_PORT:=5174}"
: "${PORTAL_DEV_PORT:=5173}"

export DEV_HOST API_PORT ADMIN_DEV_PORT PORTAL_DEV_PORT

export API_DEV_BASE="http://${DEV_HOST}:${API_PORT}"
export ADMIN_DEV_BASE="http://${DEV_HOST}:${ADMIN_DEV_PORT}"
export PORTAL_DEV_BASE="http://${DEV_HOST}:${PORTAL_DEV_PORT}"
export API_HEALTH_URL="${API_DEV_BASE}/health/live"
