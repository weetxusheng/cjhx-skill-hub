#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "${ROOT_DIR}/.env"
  set +a
fi

# shellcheck source=/dev/null
source "${SCRIPT_DIR}/dev-stack-env.sh"

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

check_service "api" "${API_HEALTH_URL}" || all_healthy=false
check_service "admin-web" "${ADMIN_DEV_BASE}" || all_healthy=false
check_service "portal-web" "${PORTAL_DEV_BASE}" || all_healthy=false

if [[ "${all_healthy}" == true ]]; then
  echo "Local stack is already healthy."
  exit 0
fi

echo "Detected unavailable local services, starting missing parts..."
bash "${ROOT_DIR}/infra/scripts/start-local-stack.sh"

check_service "api" "${API_HEALTH_URL}"
check_service "admin-web" "${ADMIN_DEV_BASE}"
check_service "portal-web" "${PORTAL_DEV_BASE}"

echo "Local stack is healthy."
