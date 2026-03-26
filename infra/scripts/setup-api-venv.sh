#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
API_DIR="${ROOT_DIR}/apps/api-server"
VENV_DIR="${API_DIR}/.venv"

find_python() {
  if command -v python3.14 >/dev/null 2>&1; then
    command -v python3.14
    return 0
  fi

  if [[ -x "/opt/homebrew/bin/python3.14" ]]; then
    printf '%s\n' "/opt/homebrew/bin/python3.14"
    return 0
  fi

  echo "Error: python3.14 not found. Install Python 3.14 first." >&2
  exit 1
}

PYTHON_BIN="$(find_python)"

echo "Using Python: ${PYTHON_BIN}"
echo "API dir: ${API_DIR}"

if [[ ! -d "${VENV_DIR}" ]]; then
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
fi

"${VENV_DIR}/bin/python" -m pip install --upgrade pip setuptools wheel
"${VENV_DIR}/bin/pip" install -e "${API_DIR}[dev]"

cat <<EOF
Virtual environment ready.

Activate with:
  source ${VENV_DIR}/bin/activate

Run backend with:
  cd ${API_DIR}
  alembic upgrade head
  uvicorn app.main:app --reload
EOF
