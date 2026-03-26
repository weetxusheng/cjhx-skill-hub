#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PID_DIR="${ROOT_DIR}/.runtime/local-dev/pids"

stop_process() {
  local name="$1"
  local pid_file="${PID_DIR}/${name}.pid"

  if [[ ! -f "${pid_file}" ]]; then
    echo "${name}: no pid file, skipping."
    return 0
  fi

  local pid
  pid="$(<"${pid_file}")"

  if ! kill -0 "${pid}" >/dev/null 2>&1; then
    echo "${name}: stale pid ${pid}, cleaning up."
    rm -f "${pid_file}"
    return 0
  fi

  kill "${pid}" >/dev/null 2>&1 || true
  for _ in $(seq 1 20); do
    if ! kill -0 "${pid}" >/dev/null 2>&1; then
      rm -f "${pid_file}"
      echo "${name}: stopped."
      return 0
    fi
    sleep 1
  done

  kill -9 "${pid}" >/dev/null 2>&1 || true
  rm -f "${pid_file}"
  echo "${name}: force stopped."
}

stop_process "portal-web"
stop_process "admin-web"
stop_process "api"
