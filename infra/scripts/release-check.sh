#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_DIR="${ROOT_DIR}/apps/api-server"
REQUIRED_DOCS=(
  "${ROOT_DIR}/AGENTS.md"
  "${ROOT_DIR}/CONTRIBUTING.md"
  "${ROOT_DIR}/docs/10-architecture/system-architecture.md"
  "${ROOT_DIR}/docs/10-architecture/data-and-permissions.md"
  "${ROOT_DIR}/docs/20-engineering/doc-update-matrix.md"
  "${ROOT_DIR}/docs/20-engineering/feature-test-playbook.md"
  "${ROOT_DIR}/docs/20-engineering/spec-lifecycle.md"
  "${ROOT_DIR}/docs/30-product-flows/upload-review-release.md"
  "${ROOT_DIR}/docs/30-product-flows/skill-authorization-and-metrics.md"
)
FORBIDDEN_PATTERNS=(
  ".DS_Store"
)

cleanup_generated_artifacts() {
  rm -rf \
    "${ROOT_DIR}/test-results" \
    "${ROOT_DIR}/playwright-report" \
    "${ROOT_DIR}/apps/admin-web/dist" \
    "${ROOT_DIR}/apps/portal-web/dist" \
    "${ROOT_DIR}/apps/admin-web/vite.config.js" \
    "${ROOT_DIR}/apps/admin-web/vite.config.d.ts" \
    "${ROOT_DIR}/apps/portal-web/vite.config.js" \
    "${ROOT_DIR}/apps/portal-web/vite.config.d.ts" \
    "${ROOT_DIR}/apps/admin-web/tsconfig.node.tsbuildinfo" \
    "${ROOT_DIR}/apps/admin-web/tsconfig.tsbuildinfo" \
    "${ROOT_DIR}/apps/portal-web/tsconfig.node.tsbuildinfo" \
    "${ROOT_DIR}/apps/portal-web/tsconfig.tsbuildinfo"
}

trap cleanup_generated_artifacts EXIT

check_doc_sync_against_changes() {
  if ! git -C "${ROOT_DIR}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "No git repository detected, skipping change-to-doc sync check."
    return 0
  fi

  if ! git -C "${ROOT_DIR}" rev-parse --verify HEAD >/dev/null 2>&1; then
    echo "No git HEAD detected, skipping change-to-doc sync check."
    return 0
  fi

  local changed_files
  changed_files="$(git -C "${ROOT_DIR}" diff --name-only HEAD)"

  if [ -z "${changed_files}" ]; then
    echo "No changed files detected, skipping change-to-doc sync check."
    return 0
  fi

  local changed_docs
  changed_docs="$(printf '%s\n' "${changed_files}" | grep '^docs/' || true)"

  if printf '%s\n' "${changed_files}" | grep -Eq 'apps/api-server/alembic/versions/|apps/api-server/app/models/'; then
    printf '%s\n' "${changed_docs}" | grep -Eq '^docs/20-engineering/database-guide.md|^docs/10-architecture/' || {
      echo "Schema or model changes require database or architecture docs to be updated." >&2
      exit 1
    }
  fi

  if printf '%s\n' "${changed_files}" | grep -Eq 'apps/api-server/app/api/routes/|apps/.*/src/lib/api.ts|apps/api-server/app/schemas/'; then
    printf '%s\n' "${changed_docs}" | grep -Eq '^docs/20-engineering/api-and-testing.md' || {
      echo "API changes require docs/20-engineering/api-and-testing.md to be updated." >&2
      exit 1
    }
  fi

  if printf '%s\n' "${changed_files}" | grep -Eq 'app/api/deps.py|app/services/skill_access.py|app/models/(role|permission|skill_role_grant|skill_user_grant|user_role|role_permission)\.py|admin_roles.py|admin_users.py'; then
    printf '%s\n' "${changed_docs}" | grep -Eq '^docs/10-architecture/data-and-permissions.md|^docs/30-product-flows/skill-authorization-and-metrics.md' || {
      echo "Permission changes require permission and authorization docs to be updated." >&2
      exit 1
    }
  fi

  if printf '%s\n' "${changed_files}" | grep -Eq 'admin_reviews.py|admin_releases.py|admin_versions.py|app/services/skill_lifecycle.py|ReviewsPage.tsx|ReleasesPage.tsx|ReviewHistoryPage.tsx'; then
    printf '%s\n' "${changed_docs}" | grep -Eq '^docs/30-product-flows/upload-review-release.md|^docs/30-product-flows/admin-workbench.md' || {
      echo "Review or release flow changes require workflow docs to be updated." >&2
      exit 1
    }
  fi
}

cd "${ROOT_DIR}"

echo "[1/10] Verify required documentation"
for doc in "${REQUIRED_DOCS[@]}"; do
  test -f "${doc}"
done

echo "[2/10] Check repository cleanliness"
cleanup_generated_artifacts

for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
  if find "${ROOT_DIR}" -path "${ROOT_DIR}/node_modules" -prune -o -path "${ROOT_DIR}/apps/api-server/.venv" -prune -o -path "${ROOT_DIR}/apps/api-server/storage" -prune -o -path "${ROOT_DIR}/apps/api-server/.pytest_cache" -prune -o -path "${ROOT_DIR}/apps/api-server/skill_hub_api.egg-info" -prune -o -name "$(basename "${pattern}")" -print | grep -q .; then
    case "${pattern}" in
      ".DS_Store")
        echo "Found forbidden OS file: ${pattern}" >&2
        exit 1
        ;;
    esac
  fi
done

for path in \
  "${ROOT_DIR}/apps/admin-web/tsconfig.node.tsbuildinfo" \
  "${ROOT_DIR}/apps/admin-web/tsconfig.tsbuildinfo" \
  "${ROOT_DIR}/apps/portal-web/tsconfig.node.tsbuildinfo" \
  "${ROOT_DIR}/apps/portal-web/tsconfig.tsbuildinfo" \
  "${ROOT_DIR}/apps/admin-web/vite.config.js" \
  "${ROOT_DIR}/apps/admin-web/vite.config.d.ts" \
  "${ROOT_DIR}/apps/portal-web/vite.config.js" \
  "${ROOT_DIR}/apps/portal-web/vite.config.d.ts"; do
  if [ -e "${path}" ]; then
    echo "Found forbidden generated artifact: ${path}" >&2
    exit 1
  fi
done

if ! grep -q "spec-lifecycle.md" "${ROOT_DIR}/AGENTS.md"; then
  echo "AGENTS.md must reference spec-lifecycle.md" >&2
  exit 1
fi

if ! grep -q "release-check.sh" "${ROOT_DIR}/docs/20-engineering/doc-update-matrix.md"; then
  echo "doc-update-matrix.md must mention release-check.sh" >&2
  exit 1
fi

echo "[3/10] Check doc sync against code changes"
check_doc_sync_against_changes

echo "[4/10] Validate local infrastructure"
bash "${ROOT_DIR}/infra/scripts/local-infra.sh" up

echo "[5/10] Check API virtualenv"
test -x "${API_DIR}/.venv/bin/python"

echo "[6/10] Run database migrations"
(
  cd "${API_DIR}"
  .venv/bin/alembic upgrade head
)

echo "[7/10] Run backend test suite"
(
  cd "${API_DIR}"
  .venv/bin/pytest -q
)

echo "[8/10] Build frontend applications"
pnpm --filter admin-web build
pnpm --filter portal-web build

echo "[9/10] Run E2E smoke tests"
pnpm test:e2e

echo "[10/10] Verify build artifacts are not left in repository"
cleanup_generated_artifacts
for path in \
  "${ROOT_DIR}/test-results" \
  "${ROOT_DIR}/apps/admin-web/dist" \
  "${ROOT_DIR}/apps/portal-web/dist"; do
  if [ -e "${path}" ]; then
    echo "Build artifact should not remain after checks: ${path}" >&2
    exit 1
  fi
done

echo "Release check passed."
