#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ALLOWLIST_FILE="${ROOT_DIR}/infra/config/code-quality-allowlist.txt"
ALLOWLIST=()

while IFS= read -r line || [[ -n "${line}" ]]; do
  ALLOWLIST+=("${line}")
done < "${ALLOWLIST_FILE}"

is_allowlisted() {
  local target="$1"
  for item in "${ALLOWLIST[@]}"; do
    if [[ "${item}" == "${target}" ]]; then
      return 0
    fi
  done
  return 1
}

failures=0

report_failure() {
  echo "CODE QUALITY: $1" >&2
  failures=1
}

check_pattern_absent() {
  local pattern="$1"
  local label="$2"
  shift 2
  local out_file="/tmp/skill-hub-code-quality-grep.txt"
  if command -v rg >/dev/null 2>&1; then
    if rg -n "${pattern}" "$@" >"${out_file}"; then
      report_failure "${label}"
      cat "${out_file}" >&2
    fi
  else
    # Fallback for environments without ripgrep.
    # Use grep recursively and include line numbers.
    if grep -R -n -E "${pattern}" "$@" >"${out_file}"; then
      report_failure "${label} (grep fallback; consider installing ripgrep for faster checks)"
      cat "${out_file}" >&2
    fi
  fi
  rm -f "${out_file}"
}

check_line_threshold() {
  local threshold="$1"
  shift
  while IFS= read -r -d '' file; do
    local rel_path="${file#${ROOT_DIR}/}"
    local line_count
    line_count="$(wc -l < "${file}" | tr -d ' ')"
    if (( line_count > threshold )) && ! is_allowlisted "${rel_path}"; then
      report_failure "${rel_path} exceeds ${threshold} lines (${line_count}) and is not in the code-quality allowlist."
    fi
  done < <(find "$@" -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.py' \) -print0)
}

for allowlisted_path in "${ALLOWLIST[@]}"; do
  full_path="${ROOT_DIR}/${allowlisted_path}"
  if [[ ! -f "${full_path}" ]]; then
    report_failure "Allowlist entry points to a missing file: ${allowlisted_path}"
    continue
  fi

  line_count="$(wc -l < "${full_path}" | tr -d ' ')"
  threshold=400
  if [[ "${allowlisted_path}" == apps/admin-web/* || "${allowlisted_path}" == apps/portal-web/* ]]; then
    threshold=250
  elif [[ "${allowlisted_path}" == apps/api-server/tests/* ]]; then
    threshold=600
  fi

  if (( line_count <= threshold )); then
    report_failure "Allowlist entry is stale and should be removed: ${allowlisted_path} (${line_count} <= ${threshold})."
  fi
done

check_pattern_absent 'console\.log' "console.log is forbidden in committed frontend code." \
  "${ROOT_DIR}/apps/admin-web/src" \
  "${ROOT_DIR}/apps/portal-web/src"

check_pattern_absent 'return null;' "Frontend components must render an explicit empty/forbidden/loading state instead of returning null." \
  "${ROOT_DIR}/apps/admin-web/src" \
  "${ROOT_DIR}/apps/portal-web/src"

check_line_threshold 250 "${ROOT_DIR}/apps/admin-web/src" "${ROOT_DIR}/apps/portal-web/src"
check_line_threshold 400 "${ROOT_DIR}/apps/api-server/app"
check_line_threshold 600 "${ROOT_DIR}/apps/api-server/tests"

if (( failures > 0 )); then
  exit 1
fi

echo "Code quality checks passed."
