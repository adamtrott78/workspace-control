#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

if [[ "$(id -un)" != "ci-controller" ]]; then
  echo "ERROR=RUN_AS_CI_CONTROLLER" >&2
  exit 70
fi

TARGET=/var/lib/workspace-ci/controller/github-token
[[ -d "$(dirname "$TARGET")" ]] || {
  echo "ERROR=CONTROLLER_STATE_DIR_MISSING" >&2
  exit 70
}

TOKEN=""
printf 'Fine-grained GitHub token (research-engine only; controller credential): ' >/dev/tty
IFS= read -r -s TOKEN </dev/tty
printf '\n' >/dev/tty
[[ -n "$TOKEN" ]] || {
  echo "ERROR=EMPTY_CONTROLLER_TOKEN" >&2
  exit 70
}

TMP="$(mktemp /var/lib/workspace-ci/controller/.github-token.XXXXXX)"
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

[[ "$(stat -c '%U:%G' "$TARGET")" == "ci-controller:workspace-ci-controller" ]] || {
  echo "ERROR=CONTROLLER_TOKEN_OWNER_DRIFT" >&2
  exit 70
}
[[ "$(stat -c '%a' "$TARGET")" == "600" ]] || {
  echo "ERROR=CONTROLLER_TOKEN_MODE_DRIFT" >&2
  exit 70
}

echo "CONTROLLER_CREDENTIAL_STAGED=PASS"
echo "NEXT=Run the accepted P5 bootstrap with WORKSPACE_CI_P5_ACTIVATE_CONTROLLER=YES."
