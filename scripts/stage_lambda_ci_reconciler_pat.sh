#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

if [[ "$(id -un)" != "ci-reconciler" ]]; then
  echo "ERROR=RUN_AS_CI_RECONCILER" >&2
  exit 70
fi

TARGET=/var/lib/workspace-ci/reconcile-controller/github-token
[[ -d "$(dirname "$TARGET")" ]] || {
  echo "ERROR=RECONCILE_CONTROLLER_STATE_DIR_MISSING" >&2
  exit 70
}

TOKEN=""
printf 'Fine-grained GitHub token (workspace-control read/actions only; reconciliation controller credential): ' >/dev/tty
IFS= read -r -s TOKEN </dev/tty
printf '\n' >/dev/tty
[[ -n "$TOKEN" ]] || {
  echo "ERROR=EMPTY_RECONCILIATION_TOKEN" >&2
  exit 70
}

TMP="$(mktemp /var/lib/workspace-ci/reconcile-controller/.github-token.XXXXXX)"
cleanup() {
  TOKEN=""
  [[ -n "${TMP:-}" && -e "$TMP" ]] && rm -f -- "$TMP"
}
trap cleanup EXIT

printf '%s' "$TOKEN" > "$TMP"
chmod 0600 "$TMP"
mv -f -- "$TMP" "$TARGET"
TMP=""
TOKEN=""

[[ "$(stat -c '%U:%G' "$TARGET")" == "ci-reconciler:workspace-ci-reconciler" ]] || {
  echo "ERROR=RECONCILIATION_TOKEN_OWNER_DRIFT" >&2
  exit 70
}
[[ "$(stat -c '%a' "$TARGET")" == "600" ]] || {
  echo "ERROR=RECONCILIATION_TOKEN_MODE_DRIFT" >&2
  exit 70
}

echo "RECONCILIATION_CREDENTIAL_STAGED=PASS"
echo "NEXT=Run the exact Run-3 activation helper through sudo."
