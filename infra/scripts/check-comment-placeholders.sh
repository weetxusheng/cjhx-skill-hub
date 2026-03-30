#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

echo "Running placeholder comment checks..."

TARGETS=(
  "${ROOT_DIR}/apps/admin-web/src"
  "${ROOT_DIR}/apps/portal-web/src"
  "${ROOT_DIR}/apps/api-server/app"
)

pattern='(TODO|TBD|WIP|FIXME)'

if command -v rg >/dev/null 2>&1; then
  if rg -n --hidden -S "${pattern}" "${TARGETS[@]}"; then
    echo "Placeholder comments found in code. Remove before committing." >&2
    exit 1
  fi
else
  if grep -R -n -E "${pattern}" "${TARGETS[@]}"; then
    echo "Placeholder comments found in code. Remove before committing." >&2
    exit 1
  fi
fi

echo "Placeholder comment checks passed."

