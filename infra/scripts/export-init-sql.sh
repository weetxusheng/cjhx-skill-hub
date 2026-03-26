#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
OUTPUT_DIR="${ROOT_DIR}/infra/sql"
OUTPUT_FILE="${OUTPUT_DIR}/skill-hub-init.sql"
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

find_pg_tool() {
  local tool="$1"
  if command -v "${tool}" >/dev/null 2>&1; then
    command -v "${tool}"
    return 0
  fi

  local brew_path="/opt/homebrew/opt/postgresql@16/bin/${tool}"
  if [[ -x "${brew_path}" ]]; then
    printf '%s\n' "${brew_path}"
    return 0
  fi

  echo "Error: ${tool} not found. Install postgresql@16 first." >&2
  exit 1
}

pg_exec() {
  local tool="$1"
  shift
  local tool_path
  tool_path="$(find_pg_tool "${tool}")"
  if [[ -n "${POSTGRES_PASSWORD:-}" ]]; then
    PGPASSWORD="${POSTGRES_PASSWORD}" "${tool_path}" "$@"
  else
    "${tool_path}" "$@"
  fi
}

export_env

TEMP_DB="skill_hub_init_$(date +%Y%m%d%H%M%S)"
TEMP_DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}${POSTGRES_PASSWORD:+:${POSTGRES_PASSWORD}}@${POSTGRES_HOST}:${POSTGRES_PORT}/${TEMP_DB}"
TEMP_PGDUMP_URL="postgresql://${POSTGRES_USER}${POSTGRES_PASSWORD:+:${POSTGRES_PASSWORD}}@${POSTGRES_HOST}:${POSTGRES_PORT}/${TEMP_DB}"

cleanup() {
  pg_exec dropdb -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" --if-exists "${TEMP_DB}" >/dev/null 2>&1 || true
}

trap cleanup EXIT

mkdir -p "${OUTPUT_DIR}"

echo "Creating temporary database ${TEMP_DB}..."
pg_exec createdb -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT}" -U "${POSTGRES_USER}" "${TEMP_DB}"

echo "Applying migrations to temporary database..."
(
  cd "${ROOT_DIR}/apps/api-server"
  DATABASE_URL="${TEMP_DATABASE_URL}" .venv/bin/alembic upgrade head
)

echo "Exporting initialization SQL to ${OUTPUT_FILE}..."
pg_exec pg_dump \
  --dbname="${TEMP_PGDUMP_URL}" \
  --format=plain \
  --encoding=UTF8 \
  --no-owner \
  --no-privileges \
  --clean \
  --if-exists \
  >"${OUTPUT_FILE}"

echo "Initialization SQL exported:"
echo "- ${OUTPUT_FILE}"
