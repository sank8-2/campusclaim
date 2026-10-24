#!/usr/bin/env bash
# Keep the current branch in sync with its upstream.
# Pull with rebase (local edits are autostashed) and push when the branch is ahead.
# Run once:  scripts/sync.sh
# Loop:      while true; do scripts/sync.sh; sleep 300; done
set -u

cd "$(dirname "$0")/.." || exit 1
LOG="${SYNC_LOG:-/tmp/opencode/campusclaim-sync.log}"
branch=$(git rev-parse --abbrev-ref HEAD)

{
  echo "=== $(date -u +%FT%TZ) sync (branch=$branch) ==="
  if ! git pull --rebase --autostash origin "$branch"; then
    echo "pull failed; leaving the tree untouched"
    exit 1
  fi

  ahead=$(git rev-list --count "origin/$branch"..HEAD)
  if [ "$ahead" -gt 0 ]; then
    git push origin "$branch" || { echo "push failed"; exit 1; }
    echo "pushed $ahead commit(s) to $branch"
  else
    echo "nothing to push"
  fi
} >> "$LOG" 2>&1
