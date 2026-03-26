#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DEFAULT_ENV_FILE="${ROOT_DIR}/.env"
FALLBACK_ENV_FILE="${ROOT_DIR}/.env.example"

if [[ -f "${DEFAULT_ENV_FILE}" ]]; then
  ENV_FILE="${DEFAULT_ENV_FILE}"
else
  ENV_FILE="${FALLBACK_ENV_FILE}"
fi

export_env() {
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
}

find_psql() {
  if command -v psql >/dev/null 2>&1; then
    command -v psql
    return 0
  fi

  if [[ -x "/opt/homebrew/opt/postgresql@16/bin/psql" ]]; then
    printf '%s\n' "/opt/homebrew/opt/postgresql@16/bin/psql"
    return 0
  fi

  echo "Error: psql not found. Install postgresql@16 first." >&2
  exit 1
}

brew_status() {
  if command -v brew >/dev/null 2>&1; then
    brew services list | awk 'NR==1 || /postgresql@16|redis|minio/'
  else
    echo "brew not found"
  fi
}

psql_cmd() {
  export_env
  local psql_bin
  psql_bin="$(find_psql)"

  local args=(
    "${psql_bin}"
    -h "${POSTGRES_HOST}"
    -p "${POSTGRES_PORT}"
    -U "${POSTGRES_USER}"
  )

  if [[ -n "${POSTGRES_PASSWORD:-}" ]]; then
    PGPASSWORD="${POSTGRES_PASSWORD}" "${args[@]}" "$@"
  else
    "${args[@]}" "$@"
  fi
}

ensure_postgres_running() {
  export_env
  if psql_cmd -d postgres -c "select 1;" >/dev/null 2>&1; then
    return 0
  fi

  echo "Error: PostgreSQL is not reachable at ${POSTGRES_HOST}:${POSTGRES_PORT} as ${POSTGRES_USER}." >&2
  echo "If you use Homebrew, run: brew services start postgresql@16" >&2
  exit 1
}

ensure_db() {
  export_env
  ensure_postgres_running

  local exists
  exists="$(psql_cmd -d postgres -tAc "select 1 from pg_database where datname = '${POSTGRES_DB}';")"
  if [[ "${exists}" == "1" ]]; then
    echo "Database ${POSTGRES_DB} already exists."
    return 0
  fi

  psql_cmd -d postgres -c "create database ${POSTGRES_DB};"
  echo "Database ${POSTGRES_DB} created."
}

up() {
  echo "Using env file: ${ENV_FILE}"
  ensure_postgres_running
  ensure_db
  echo "Local PostgreSQL is ready."
}

status() {
  export_env
  echo "Env file: ${ENV_FILE}"
  brew_status
  if psql_cmd -d postgres -c "select 1;" >/dev/null 2>&1; then
    echo "PostgreSQL connection: OK"
  else
    echo "PostgreSQL connection: FAILED"
  fi
}

conninfo() {
  export_env
  ensure_postgres_running
  psql_cmd -d "${POSTGRES_DB}" -c '\conninfo'
}

usage() {
  cat <<'EOF'
Usage: infra/scripts/local-infra.sh <command>

Commands:
  up         Validate local PostgreSQL service and create project database if missing
  ensure-db  Create project database if missing
  status     Show local service status and PostgreSQL connectivity
  conninfo   Show current PostgreSQL connection info for the project database
EOF
}

main() {
  local command="${1:-}"
  case "${command}" in
    up)
      up
      ;;
    ensure-db)
      ensure_db
      ;;
    status)
      status
      ;;
    conninfo)
      conninfo
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "${@}"
