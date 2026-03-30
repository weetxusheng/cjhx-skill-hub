#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

cd "${ROOT_DIR}"

echo "Running doc quality checks..."

DOC_DIR="${ROOT_DIR}/docs"
EXCLUDE_PLANS_DIR="${DOC_DIR}/superpowers/plans"
EXCLUDE_SPECS_DIR="${DOC_DIR}/superpowers/specs"

if [[ ! -d "${DOC_DIR}" ]]; then
  echo "docs/ directory not found, skipping doc quality checks."
  exit 0
fi

tmp_out="/tmp/skill-hub-doc-quality.txt"
rm -f "${tmp_out}"

scan_placeholders() {
  local pattern="$1"
  if command -v rg >/dev/null 2>&1; then
    rg -n --hidden -S "${pattern}" "${DOC_DIR}" \
      --glob '!docs/superpowers/plans/**' \
      --glob '!docs/superpowers/specs/**' \
      >"${tmp_out}" || true
  else
    grep -R -n -E \
      --exclude-dir "${EXCLUDE_PLANS_DIR}" \
      --exclude-dir "${EXCLUDE_SPECS_DIR}" \
      "${pattern}" "${DOC_DIR}" >"${tmp_out}" || true
  fi

  if [[ -s "${tmp_out}" ]]; then
    echo "Doc quality gate failed: placeholders found." >&2
    cat "${tmp_out}" >&2
    exit 1
  fi
}

# 避免已提交文档中出现明显占位词。
# 仅匹配“行首占位”形式，避免误伤规范文档中对关键词的说明性引用。
scan_placeholders '^\s*(TBD|WIP)\b'
scan_placeholders '^\s*FIXME\b'
# 说明：文档中允许出现 `TODO` 术语（用于规范说明），
# 但代码注释中的占位词由 infra/scripts/check-comment-placeholders.sh 严格拦截。

echo "Checking relative links in markdown..."

python3 - <<'PY'
import os, re, sys

ROOT = os.getcwd()
DOCS = os.path.join(ROOT, "docs")

md_files = []
for base, _, files in os.walk(DOCS):
    for f in files:
        if f.endswith(".md"):
            md_files.append(os.path.join(base, f))

link_re = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

def is_external(target: str) -> bool:
    return (
        target.startswith("http://")
        or target.startswith("https://")
        or target.startswith("mailto:")
    )

def normalize(target: str) -> str:
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    return target

errors = []

for path in md_files:
    # 计划文档不纳入文档门禁（其中可能包含 TODO/TBD 示例）。
    if os.path.normpath(path).startswith(os.path.normpath(os.path.join(DOCS, "superpowers", "plans"))):
        continue

    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    for raw in link_re.findall(text):
        target = normalize(raw)
        if not target:
            continue

        # 忽略仅锚点链接与外部链接
        if target.startswith("#") or is_external(target):
            continue

        # 文件系统检查前去掉 query/fragment
        target_no_frag = target.split("#", 1)[0].split("?", 1)[0]
        if not target_no_frag:
            continue

        # 仅校验相对链接（./ ../ docs/...）；以 / 开头的路径保持跳过。
        if target_no_frag.startswith("/"):
            continue

        resolved = os.path.normpath(os.path.join(os.path.dirname(path), target_no_frag))

        if not os.path.exists(resolved):
            rel_src = os.path.relpath(path, ROOT)
            errors.append(f"{rel_src}: broken link -> {target}")

if errors:
    print("Doc quality gate failed: broken relative links found:", file=sys.stderr)
    for e in errors:
        print(e, file=sys.stderr)
    sys.exit(1)

print("Relative link check passed.")
PY

echo "Doc quality checks passed."

