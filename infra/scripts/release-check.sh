#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API_DIR="${ROOT_DIR}/apps/api-server"
REQUIRED_DOCS=(
  "${ROOT_DIR}/AGENTS.md"
  "${ROOT_DIR}/CONTRIBUTING.md"
  "${ROOT_DIR}/docs/10-architecture/system-architecture.md"
  "${ROOT_DIR}/docs/10-architecture/data-and-permissions.md"
  "${ROOT_DIR}/docs/10-architecture/domain-module-map.md"
  "${ROOT_DIR}/docs/20-engineering/README.md"
  "${ROOT_DIR}/docs/20-engineering/engineering-handbook.md"
  "${ROOT_DIR}/docs/20-engineering/frontend-guide.md"
  "${ROOT_DIR}/docs/20-engineering/data-and-db-handbook.md"
  "${ROOT_DIR}/docs/20-engineering/api-testing-and-release.md"
  "${ROOT_DIR}/docs/20-engineering/sso-portal-gateway.md"
  "${ROOT_DIR}/docs/20-engineering/docs-governance.md"
  "${ROOT_DIR}/docs/20-engineering/code-quality-debt-register.md"
  "${ROOT_DIR}/docs/20-engineering/page-spec-template.md"
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
  local diff_files
  local untracked_files
  diff_files="$(git -C "${ROOT_DIR}" diff --name-only HEAD)"
  untracked_files="$(git -C "${ROOT_DIR}" ls-files --others --exclude-standard)"
  changed_files="$(printf '%s\n%s\n' "${diff_files}" "${untracked_files}" | sed '/^$/d' | sort -u)"

  if [ -z "${changed_files}" ]; then
    echo "No changed files detected, skipping change-to-doc sync check."
    return 0
  fi

  local changed_docs
  changed_docs="$(printf '%s\n' "${changed_files}" | grep '^docs/' || true)"

  if grep -Eq 'apps/api-server/alembic/versions/|apps/api-server/app/models/' <<< "${changed_files}"; then
    grep -Eq '^docs/20-engineering/data-and-db-handbook.md|^docs/10-architecture/' <<< "${changed_docs}" || {
      echo "Schema or model changes require database or architecture docs to be updated." >&2
      exit 1
    }
  fi

  if grep -Eq 'apps/api-server/app/api/routes/|apps/.*/src/lib/api.ts|apps/.*/src/store/auth.ts|apps/api-server/app/schemas/|apps/api-server/app/main.py|apps/api-server/app/schemas/common.py|apps/api-server/app/services/sso_gateway_decode.py' <<< "${changed_files}"; then
    grep -Eq '^docs/20-engineering/api-testing-and-release.md|^docs/20-engineering/sso-portal-gateway.md' <<< "${changed_docs}" || {
      echo "API or HTTP client contract changes require docs/20-engineering/api-testing-and-release.md and/or sso-portal-gateway.md to be updated." >&2
      exit 1
    }
  fi

  if grep -Eq 'app/api/deps.py|app/services/skill_access.py|app/models/(role|permission|skill_role_grant|skill_user_grant|user_role|role_permission)\.py|admin_roles.py|admin_users.py' <<< "${changed_files}"; then
    grep -Eq '^docs/10-architecture/data-and-permissions.md|^docs/30-product-flows/skill-authorization-and-metrics.md' <<< "${changed_docs}" || {
      echo "Permission changes require permission and authorization docs to be updated." >&2
      exit 1
    }
  fi

  if grep -Eq 'admin_reviews.py|admin_releases.py|admin_versions.py|app/services/skill_lifecycle.py|ReviewsPage.tsx|ReleasesPage.tsx|ReviewHistoryPage.tsx' <<< "${changed_files}"; then
    grep -Eq '^docs/30-product-flows/upload-review-release.md|^docs/30-product-flows/admin-workbench.md' <<< "${changed_docs}" || {
      echo "Review or release flow changes require workflow docs to be updated." >&2
      exit 1
    }
  fi

  if grep -Eq 'apps/(portal-web|admin-web)/src/.*\.(ts|tsx|css)$' <<< "${changed_files}"; then
    grep -Eq '^docs/20-engineering/frontend-guide.md|^docs/30-product-flows/core-page-specs.md|^docs/20-engineering/page-spec-template.md' <<< "${changed_docs}" || {
      echo "Frontend structure or style changes require frontend-guide.md and/or related page specs to be updated." >&2
      exit 1
    }
  fi

}

cd "${ROOT_DIR}"

echo "[1/14] Verify required documentation"
for doc in "${REQUIRED_DOCS[@]}"; do
  test -f "${doc}"
done

echo "[2/14] Check repository cleanliness"
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

if ! grep -q "docs-governance.md" "${ROOT_DIR}/AGENTS.md"; then
  echo "AGENTS.md must reference docs-governance.md" >&2
  exit 1
fi

if ! grep -q "release-check.sh" "${ROOT_DIR}/docs/20-engineering/docs-governance.md"; then
  echo "docs-governance.md must mention release-check.sh" >&2
  exit 1
fi

echo "[3/14] Check doc sync against code changes"
check_doc_sync_against_changes

echo "[4/14] Run doc quality gates"
bash "${ROOT_DIR}/infra/scripts/check-doc-quality.sh"

echo "[5/14] Run placeholder comment gates"
bash "${ROOT_DIR}/infra/scripts/check-comment-placeholders.sh"

echo "[6/14] Run comment contract gates"
bash "${ROOT_DIR}/infra/scripts/check-comment-contracts.sh"

echo "[7/14] Run lint and code quality gates"
pnpm lint

echo "[8/14] Validate local infrastructure"
bash "${ROOT_DIR}/infra/scripts/local-infra.sh" up

echo "[9/14] Check API virtualenv"
test -x "${API_DIR}/.venv/bin/python"

echo "[10/14] Run database migrations"
(
  cd "${API_DIR}"
  .venv/bin/alembic upgrade head
)

echo "[11/14] Run backend test suite"
(
  cd "${API_DIR}"
  .venv/bin/pytest -q
)

echo "[12/14] Build frontend applications"
pnpm --filter admin-web build
pnpm --filter portal-web build

echo "[13/14] Run E2E smoke tests"
pnpm test:e2e
 
echo "[14/14] Verify build artifacts are not left in repository"
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
