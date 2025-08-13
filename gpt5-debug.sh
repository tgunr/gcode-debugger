#!/usr/bin/env bash
set -euo pipefail

OUT="debug_bundle"
rm -rf "$OUT" debug_bundle.zip
mkdir -p "$OUT"

# 1) Basic env info
python3 - <<'PY' > "$OUT/env.txt" || true
import sys, platform, subprocess, json
print("PYTHON:", sys.version)
print("PLATFORM:", platform.platform())
print("EXE:", sys.executable)
try:
    print("\nPIP FREEZE:\n")
    print(subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True))
except Exception as e:
    print("\npip freeze failed:", e)
PY

# 2) Project manifests (add/remove as needed)
cp -f main.py "$OUT/" 2>/dev/null || true
cp -f core/*.py "$OUT/" 2>/dev/null || true
cp -f gui/*.py "$OUT/" 2>/dev/null || true
cp -f requirements*.txt "$OUT/" 2>/dev/null || true
cp -f *.md "$OUT/" 2>/dev/null || true
cp -f docs/* "$OUT/" 2>/dev/null || true

# 3) Recent logs & traces if present
mkdir -p "$OUT/logs"
cp -Rf logs "$OUT/" 2>/dev/null || true
cp -f ./*.log "$OUT/logs/" 2>/dev/null || true

# 4) Lightweight tree (without heavy dirs)
{ 
  echo "PROJECT TREE (filtered):"
  command -v tree >/dev/null 2>&1 && tree -a -I '.git|node_modules|venv|.venv|build|dist|__pycache__|.mypy_cache|.pytest_cache' . \
  || tree -a -I '.git|node_modules|venv|.venv|build|dist|__pycache__|.mypy_cache|.pytest_cache' . 2>/dev/null \
  || find . -maxdepth 3 -not -path '*/.git*' -not -path '*/node_modules*' -not -path '*/venv*' -not -path '*/.venv*'
} > "$OUT/tree.txt"

# 5) Recent git info (if repo)
git rev-parse --is-inside-work-tree >/dev/null 2>&1 && {
  echo "=== GIT STATUS ===" > "$OUT/git.txt"
  git status --porcelain=v1 >> "$OUT/git.txt" 2>/dev/null || true
  echo -e "\n=== LAST 20 COMMITS ===" >> "$OUT/git.txt"
  git --no-pager log --oneline -n 20 >> "$OUT/git.txt" 2>/dev/null || true
} || true

zip -r debug_bundle.zip "$OUT" >/dev/null
echo "Wrote debug_bundle.zip"