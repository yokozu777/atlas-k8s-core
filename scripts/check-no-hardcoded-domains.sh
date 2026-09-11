#!/usr/bin/env bash
# Fail if product sources contain org lab hostnames (mxhash.com).
# SECURITY.md / this script may mention the fingerprint for documentation / detection.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PATTERN='mxhash\.com|k8s\.mxhash'

hits="$(
  grep -rEIn "$PATTERN" "$ROOT" \
    --include='*.yaml' --include='*.yml' --include='*.j2' --include='*.json' --include='*.tf' --include='*.md' --include='*.sh' \
    --exclude-dir=.git \
    --exclude-dir=workspace \
    --exclude-dir=.ansible \
    --exclude-dir=scripts \
    --exclude='SECURITY.md' \
    --exclude='push-gitea.sh' \
    --exclude='push-github.sh' \
    --exclude='git-publish-lib.sh' \
    || true
)"

# Drop comment-only YAML/Jinja noise lines (leading # after optional spaces)
hits="$(printf '%s\n' "$hits" | grep -vE ':[0-9]+:[[:space:]]*#' || true)"

if [[ -n "${hits}" ]]; then
  echo "$hits" >&2
  echo "ERROR: org hostname fingerprint found in atlas-k8s-core product sources" >&2
  exit 1
fi

echo "OK: no org hostname hardcodes in atlas-k8s-core product sources"
