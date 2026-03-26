#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

ensure_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' not found." >&2
    exit 1
  fi
}

ensure_command curl

check_service() {
  local name="$1"
  local url="$2"
  if curl -fsS "${url}" >/dev/null 2>&1; then
    echo "${name}: healthy (${url})"
    return 0
  fi
  echo "${name}: unavailable (${url})"
  return 1
}

all_healthy=true

check_service "api" "http://127.0.0.1:8000/health/live" || all_healthy=false
check_service "admin-web" "http://127.0.0.1:5174" || all_healthy=false
check_service "portal-web" "http://127.0.0.1:5173" || all_healthy=false

if [[ "${all_healthy}" == true ]]; then
  echo "Local stack is already healthy."
  exit 0
fi

echo "Detected unavailable local services, starting missing parts..."
bash "${ROOT_DIR}/infra/scripts/start-local-stack.sh"

check_service "api" "http://127.0.0.1:8000/health/live"
check_service "admin-web" "http://127.0.0.1:5174"
check_service "portal-web" "http://127.0.0.1:5173"

echo "Local stack is healthy."
