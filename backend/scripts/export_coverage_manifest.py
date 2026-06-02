#!/usr/bin/env python3
"""Export a manifest mapping each corpus sample to its original test/source
path inside the cloned library repos, and generate per-library coverage
run commands.

Usage:
    python3 scripts/export_coverage_manifest.py \
        --mui-dir ~/coverage_repos/material-ui \
        --element-plus-dir ~/coverage_repos/element-plus \
        --base-ui-dir ~/coverage_repos/base-ui \
        --ant-design-dir ~/coverage_repos/ant-design \
        --out output/coverage/manifest.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from mr_framework.samples import load_all_samples

# ── canonical test-file locations inside each repo ───────────────────────────
# These patterns are based on each library's actual repo structure.
_PATTERNS: dict[str, list[str]] = {
    "mui-material": [
        "packages/mui-material/src/{component}/{component}.test.js",
        "packages/mui-material/src/{component}/{component}.test.tsx",
        "packages/mui-material/src/{component}/index.test.js",
    ],
    "mui-base-ui": [
        "packages/react/src/{component}/{component}.test.tsx",
        "packages/react/src/{component}/index.test.tsx",
        "packages/react/src/{component}/{component}.test.js",
    ],
    "element-plus": [
        "packages/components/{component_lower}/__tests__/{component_lower}.test.ts",
        "packages/components/{component_lower}/__tests__/{component_lower}.spec.ts",
        "packages/components/{component_lower}/__tests__/index.test.ts",
    ],
    "ant-design": [
        "components/{component_lower}/__tests__/index.test.tsx",
        "components/{component_lower}/__tests__/{component_lower}.test.tsx",
        "components/{component_lower}/__tests__/index.test.ts",
    ],
}


def _find_test(repo_dir: Path, library: str, component: str) -> Path | None:
    comp_lower = component.lower().replace(" ", "-")
    comp_pascal = component.replace(" ", "")
    for pattern in _PATTERNS.get(library, []):
        candidate = repo_dir / pattern.format(
            component=comp_pascal,
            component_lower=comp_lower,
        )
        if candidate.exists():
            return candidate
    # Fuzzy: walk the repo for any test file containing the component name
    search_dirs = {
        "mui-material": repo_dir / "packages" / "mui-material" / "src",
        "mui-base-ui": repo_dir / "packages" / "react" / "src",
        "element-plus": repo_dir / "packages" / "components",
        "ant-design": repo_dir / "components",
    }.get(library)
    if search_dirs and search_dirs.exists():
        for f in search_dirs.rglob("*.test.*"):
            if comp_lower in f.name.lower() or comp_lower in str(f.parent).lower():
                return f
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mui-dir", default="")
    ap.add_argument("--element-plus-dir", default="")
    ap.add_argument("--base-ui-dir", default="")
    ap.add_argument("--ant-design-dir", default="")
    ap.add_argument("--out", default=str(PROJECT_ROOT / "output" / "coverage" / "manifest.json"))
    args = ap.parse_args()

    repo_map = {
        "mui-material":  Path(args.mui_dir) if args.mui_dir else None,
        "mui-base-ui":   Path(args.base_ui_dir) if args.base_ui_dir else None,
        "element-plus":  Path(args.element_plus_dir) if args.element_plus_dir else None,
        "ant-design":    Path(args.ant_design_dir) if args.ant_design_dir else None,
    }

    samples = load_all_samples()
    manifest = []
    not_found = []

    for s in samples:
        repo_dir = repo_map.get(s.library)
        test_path_in_repo = None
        if repo_dir and repo_dir.exists():
            found = _find_test(repo_dir, s.library, s.component_name)
            if found:
                test_path_in_repo = str(found.relative_to(repo_dir))

        entry = {
            "sample_id": s.sample_id,
            "library": s.library,
            "category": s.category,
            "component_name": s.component_name,
            "corpus_test_path": str(s.test_path),
            "corpus_source_path": str(s.source_path),
            "repo_test_path": test_path_in_repo,
            "repo_dir": str(repo_dir) if repo_dir else None,
            "found": test_path_in_repo is not None,
        }
        manifest.append(entry)
        if not test_path_in_repo:
            not_found.append(s.sample_id)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    found_n = sum(1 for e in manifest if e["found"])
    print(json.dumps({
        "total": len(manifest),
        "found_in_repo": found_n,
        "not_found": len(not_found),
        "not_found_samples": not_found[:20],
        "manifest": str(out),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
