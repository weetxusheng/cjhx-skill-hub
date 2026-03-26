#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RUNTIME_DIR="${ROOT_DIR}/.runtime/local-dev"
PID_DIR="${RUNTIME_DIR}/pids"
LOG_DIR="${RUNTIME_DIR}/logs"

mkdir -p "${PID_DIR}" "${LOG_DIR}"

ensure_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: required command '$1' not found." >&2
    exit 1
  fi
}

ensure_command pnpm
ensure_command curl

is_pid_running() {
  local pid="$1"
  kill -0 "${pid}" >/dev/null 2>&1
}

is_service_healthy() {
  local health_url="$1"
  curl -fsS "${health_url}" >/dev/null 2>&1
}

is_port_busy() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"${port}" -sTCP:LISTEN -t >/dev/null 2>&1
    return $?
  fi
  return 1
}

start_process() {
  local name="$1"
  local port="$2"
  local health_url="$3"
  local command="$4"
  local pid_file="${PID_DIR}/${name}.pid"
  local log_file="${LOG_DIR}/${name}.log"

  if [[ -f "${pid_file}" ]]; then
    local existing_pid
    existing_pid="$(<"${pid_file}")"
    if is_pid_running "${existing_pid}" && is_service_healthy "${health_url}"; then
      echo "${name} is already running (pid ${existing_pid})."
      return 0
    fi
    rm -f "${pid_file}"
  fi

  if is_port_busy "${port}"; then
    if is_service_healthy "${health_url}"; then
      echo "${name} is already running on ${health_url}."
      return 0
    fi
    echo "Error: port ${port} is already in use. Stop the existing process before starting ${name}." >&2
    exit 1
  fi

  nohup bash -lc "cd '${ROOT_DIR}' && ${command}" </dev/null >"${log_file}" 2>&1 &
  local pid=$!
  echo "${pid}" >"${pid_file}"

  for _ in $(seq 1 60); do
    if is_service_healthy "${health_url}"; then
      echo "${name} started on ${health_url} (pid ${pid})."
      return 0
    fi
    if ! is_pid_running "${pid}"; then
      echo "Error: ${name} exited unexpectedly. See ${log_file}" >&2
      exit 1
    fi
    sleep 1
  done

  echo "Error: ${name} did not become ready in time. See ${log_file}" >&2
  exit 1
}

echo "Preparing local infrastructure..."
bash "${ROOT_DIR}/infra/scripts/local-infra.sh" up

echo "Running database migrations..."
(cd "${ROOT_DIR}/apps/api-server" && .venv/bin/alembic upgrade head)

start_process "api" "8000" "http://127.0.0.1:8000/health/live" \
  "cd apps/api-server && .venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
start_process "admin-web" "5174" "http://127.0.0.1:5174" \
  "pnpm --filter admin-web dev -- --host 127.0.0.1 --port 5174"
start_process "portal-web" "5173" "http://127.0.0.1:5173" \
  "pnpm --filter portal-web dev -- --host 127.0.0.1 --port 5173"

cat <<EOF

Local stack is ready:
- API: http://127.0.0.1:8000
- Admin: http://127.0.0.1:5174
- Portal: http://127.0.0.1:5173

Runtime files:
- PID dir: ${PID_DIR}
- Log dir: ${LOG_DIR}
EOF
