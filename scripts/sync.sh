#!/usr/bin/env bash
# Keep this checkout in sync with origin/main.
# Pull with rebase (local edits are autostashed) and push when the branch is ahead.
# Run once:  scripts/sync.sh
# Loop:      while true; do scripts/sync.sh; sleep 300; done
set -u

cd "$(dirname "$0")/.." || exit 1
LOG="${SYNC_LOG:-/tmp/opencode/campusclaim-sync.log}"

{
  echo "=== $(date -u +%FT%TZ) sync ==="
  if ! git pull --rebase --autostash; then
    echo "pull failed; leaving the tree untouched"
    exit 1
  fi

  ahead=$(git rev-list --count origin/main..HEAD)
  if [ "$ahead" -gt 0 ]; then
    git push origin main || { echo "push failed"; exit 1; }
    echo "pushed $ahead commit(s)"
  else
    echo "nothing to push"
  fi
} >> "$LOG" 2>&1
