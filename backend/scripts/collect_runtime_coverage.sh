#!/usr/bin/env bash
# collect_runtime_coverage.sh
# Run per-component tests with coverage in each original repo, then
# collect statement/branch coverage into output/coverage/runtime_coverage.json
#
# Prerequisites:
#   - Each repo cloned and dependencies installed (pnpm install / npm install)
#   - c8 installed globally: npm i -g c8
#   - Manifest generated: python3 backend/scripts/export_coverage_manifest.py ...
#
# Usage:
#   bash backend/scripts/collect_runtime_coverage.sh \
#     --manifest output/coverage/manifest.json \
#     --out output/coverage/runtime_coverage.json
#
# Per-library runner notes:
#   mui-material : pnpm jest --coverage --coverageProvider=v8 <test_pattern>
#   mui-base-ui  : pnpm vitest run --coverage <test_pattern>
#   element-plus : pnpm vitest run --coverage <test_pattern>
#   ant-design   : npx jest --coverage --coverageProvider=v8 <test_pattern>

set -euo pipefail

MANIFEST="${1:-output/coverage/manifest.json}"
OUT="${2:-output/coverage/runtime_coverage.json}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

mkdir -p "$(dirname "$OUT")"

python3 - "$MANIFEST" "$OUT" <<'PYEOF'
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

manifest_path = sys.argv[1]
out_path = sys.argv[2]
manifest = json.loads(Path(manifest_path).read_text())

# ── coverage extraction helpers ─────────────────────────────────────────────

def run_vitest_coverage(repo_dir: str, test_file: str) -> dict | None:
    """Run vitest with c8 coverage on a single test file."""
    cmd = [
        "pnpm", "vitest", "run",
        "--coverage",
        "--coverage.provider=v8",
        "--coverage.reporter=json-summary",
        "--coverage.reportOnFailure=true",
        test_file,
    ]
    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env["COVERAGE_OUTPUT_DIR"] = tmp
        result = subprocess.run(
            cmd, cwd=repo_dir, capture_output=True, text=True, timeout=120, env=env
        )
        # Try to parse coverage-summary.json written by v8 reporter
        for summary_file in Path(tmp).rglob("coverage-summary.json"):
            data = json.loads(summary_file.read_text())
            total = data.get("total", {})
            return {
                "statement_coverage_rate": total.get("statements", {}).get("pct", 0.0) / 100,
                "branch_coverage_rate": total.get("branches", {}).get("pct", 0.0) / 100,
                "line_coverage_rate": total.get("lines", {}).get("pct", 0.0) / 100,
                "function_coverage_rate": total.get("functions", {}).get("pct", 0.0) / 100,
            }
        # Fallback: parse stdout for Istanbul summary line
        pct_re = re.compile(r"Stmts\s*\|\s*([\d.]+).*?Branches\s*\|\s*([\d.]+)", re.S)
        m = pct_re.search(result.stdout + result.stderr)
        if m:
            return {
                "statement_coverage_rate": float(m.group(1)) / 100,
                "branch_coverage_rate": float(m.group(2)) / 100,
            }
    return None


def run_jest_coverage(repo_dir: str, test_file: str) -> dict | None:
    """Run jest with --coverage on a single test file."""
    cmd = [
        "npx", "jest",
        "--coverage",
        "--coverageProvider=v8",
        "--coverageReporters=json-summary",
        "--testPathPattern", re.escape(test_file),
        "--no-cache",
    ]
    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env["JEST_COVERAGE_OUTPUT"] = tmp
        result = subprocess.run(
            cmd, cwd=repo_dir, capture_output=True, text=True, timeout=120, env=env
        )
        for summary_file in Path(tmp).rglob("coverage-summary.json"):
            data = json.loads(summary_file.read_text())
            total = data.get("total", {})
            return {
                "statement_coverage_rate": total.get("statements", {}).get("pct", 0.0) / 100,
                "branch_coverage_rate": total.get("branches", {}).get("pct", 0.0) / 100,
                "line_coverage_rate": total.get("lines", {}).get("pct", 0.0) / 100,
                "function_coverage_rate": total.get("functions", {}).get("pct", 0.0) / 100,
            }
    return None

# ── per-library runner dispatch ──────────────────────────────────────────────
VITEST_LIBS  = {"element-plus", "mui-base-ui"}
JEST_LIBS    = {"ant-design"}
MUI_LIBS     = {"mui-material"}   # custom mocha/chai → use jest compat layer

results = []
for entry in manifest:
    if not entry.get("found") or not entry.get("repo_test_path"):
        results.append({**entry, "runtime_coverage": None, "error": "not_found"})
        continue

    repo_dir = entry["repo_dir"]
    test_rel = entry["repo_test_path"]
    lib = entry["library"]

    print(f"[{lib}] {entry['component_name']} ...", flush=True)
    try:
        if lib in VITEST_LIBS:
            cov = run_vitest_coverage(repo_dir, test_rel)
        elif lib in JEST_LIBS or lib in MUI_LIBS:
            cov = run_jest_coverage(repo_dir, test_rel)
        else:
            cov = None
        results.append({**entry, "runtime_coverage": cov, "error": None})
    except subprocess.TimeoutExpired:
        results.append({**entry, "runtime_coverage": None, "error": "timeout"})
    except Exception as e:
        results.append({**entry, "runtime_coverage": None, "error": str(e)})

Path(out_path).write_text(json.dumps(results, indent=2, ensure_ascii=False))
found   = sum(1 for r in results if r.get("runtime_coverage"))
print(f"\nDone: {found}/{len(results)} components have runtime coverage data.")
PYEOF
