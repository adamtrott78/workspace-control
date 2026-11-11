#!/usr/bin/env bash
set -euo pipefail

if [[ "$#" -ne 2 ]]; then
  echo "usage: $0 <live-pr-number> <review-request-comment-id>" >&2
  exit 2
fi

LIVE_PR_NUMBER="$1"
REVIEW_REQUEST_COMMENT_ID="$2"
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
SOURCE_HEAD="$(git -C "$ROOT" rev-parse HEAD)"
TMP="$(mktemp -d /tmp/workspace-ci-v3-wc-terminal-revival.XXXXXX)"
umask 077

cleanup() {
  rm -rf "$TMP" >/dev/null 2>&1 || sudo -n rm -rf "$TMP" >/dev/null 2>&1 || true
}
trap cleanup EXIT

test -z "$(git -C "$ROOT" status --porcelain --untracked-files=all)"
if git -C "$ROOT" symbolic-ref -q HEAD >/dev/null 2>&1; then
  echo "STOP_ATTACHED_HEAD"
  exit 20
fi

command -v gh >/dev/null
command -v curl >/dev/null
command -v sha256sum >/dev/null
sudo -v

TOKEN_FILE="$TMP/github-token"
gh auth token > "$TOKEN_FILE"
test -s "$TOKEN_FILE"
chmod 0600 "$TOKEN_FILE"

GO_ARCHIVE="$TMP/go1.26.3.linux-amd64.tar.gz"
GO_SHA256="2b2cfc7148493da5e73981bffbf3353af381d5f93e789c82c79aff64962eb556"
curl -fsSL --retry 3 -o "$GO_ARCHIVE" "https://go.dev/dl/go1.26.3.linux-amd64.tar.gz"
printf '%s  %s\n' "$GO_SHA256" "$GO_ARCHIVE" | sha256sum -c -
tar -C "$TMP" -xzf "$GO_ARCHIVE"
GO_BIN="$TMP/go/bin/go"
test "$("$GO_BIN" env GOVERSION)" = "go1.26.3"

echo "=== V3 WORKSPACE-CONTROL TERMINAL REVIVAL PREFLIGHT ==="
echo "SOURCE_HEAD=$SOURCE_HEAD"
sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
  "$ROOT/scripts/lambda_ci_v3_workspace_control_terminal_revival_live.py" \
  --repo-root "$ROOT" \
  --github-token-file "$TOKEN_FILE" \
  --live-pr-number "$LIVE_PR_NUMBER" \
  --review-request-comment-id "$REVIEW_REQUEST_COMMENT_ID" \
  --go-bin "$GO_BIN" \
  --verify-preflight

echo "=== V3 WORKSPACE-CONTROL TERMINAL REVIVAL APPLY ==="
sudo env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
  "$ROOT/scripts/lambda_ci_v3_workspace_control_terminal_revival_live.py" \
  --repo-root "$ROOT" \
  --github-token-file "$TOKEN_FILE" \
  --live-pr-number "$LIVE_PR_NUMBER" \
  --review-request-comment-id "$REVIEW_REQUEST_COMMENT_ID" \
  --go-bin "$GO_BIN" \
  --apply
