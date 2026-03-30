#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

python3 - <<'PY'
from __future__ import annotations

import ast
import sys
from pathlib import Path

root = Path("/Users/xusheng/Documents/project/cjhx-skill-hub")
failures: list[str] = []


def check_page_interaction_contracts() -> None:
    for src_root in [root / "apps/admin-web/src", root / "apps/portal-web/src"]:
        for path in src_root.rglob("*"):
            if path.suffix not in {".ts", ".tsx"}:
                continue
            if path.name in {"main.tsx", "vite-env.d.ts"}:
                continue

            rel_path = path.relative_to(root)
            text = path.read_text(encoding="utf-8")

            if path.name == "App.tsx" or ("pages" in path.parts and path.suffix == ".tsx" and "_components" not in path.parts):
                if "交互约定" not in text:
                    failures.append(f"{rel_path}: missing page interaction contract comment")
                continue

            if ("components" in path.parts or "_components" in path.parts) and path.suffix == ".tsx":
                if "组件约定" not in text:
                    failures.append(f"{rel_path}: missing component contract comment")
                continue

            if "store" in path.parts:
                if "状态约定" not in text:
                    failures.append(f"{rel_path}: missing store contract comment")
                continue

            if "模块约定" not in text:
                failures.append(f"{rel_path}: missing module contract comment")


def check_python_docstrings() -> None:
    docstring_targets = [
        root / "apps/api-server/app/api/routes",
        root / "apps/api-server/app/services",
        root / "apps/api-server/app/repositories",
        root / "apps/api-server/app/core",
        root / "apps/api-server/app/db",
        root / "apps/api-server/scripts",
    ]
    for folder in docstring_targets:
        for path in folder.rglob("*.py"):
            rel_path = path.relative_to(root)
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                    if ast.get_docstring(node) is None:
                        failures.append(f"{rel_path}:{node.lineno} missing docstring on public function `{node.name}`")

    module_targets = [
        root / "apps/api-server/app/core",
        root / "apps/api-server/app/db",
        root / "apps/api-server/app/models",
        root / "apps/api-server/app/schemas",
        root / "apps/api-server/scripts",
    ]
    for folder in module_targets:
        for path in folder.rglob("*.py"):
            rel_path = path.relative_to(root)
            tree = ast.parse(path.read_text(encoding="utf-8"))
            if ast.get_docstring(tree) is None:
                failures.append(f"{rel_path}: missing module contract docstring")


check_page_interaction_contracts()
check_python_docstrings()

if failures:
    print("Comment contract violations found:", file=sys.stderr)
    for item in failures:
        print(f"- {item}", file=sys.stderr)
    sys.exit(1)

print("Comment contract checks passed.")
PY
