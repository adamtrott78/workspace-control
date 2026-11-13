#!/usr/bin/env bash
set -euo pipefail

fail() { echo "ERROR: $*" >&2; exit 1; }

EXPECTED_AUTHORITY_SHA="${1:-}"
EXPECTED_PAD_SHA="${2:-}"
AUTHORITY_ROOT="/etc/workspace-shell/authority"
PAD_ROOT="/srv/workspace-shell/PADataset"
EVIDENCE_ROOT="/srv/workspace-shell/PADataset-evidence"
MOUNTPOINT="$PAD_ROOT/local_artifacts/evidence"

[[ "$EXPECTED_AUTHORITY_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "expected authority SHA must be full lowercase SHA"
[[ "$EXPECTED_PAD_SHA" =~ ^[0-9a-f]{40}$ ]] || fail "expected PADataset SHA must be full lowercase SHA"

LIVE_AUTH="$(sudo git -c safe.directory="$AUTHORITY_ROOT" -C "$AUTHORITY_ROOT" rev-parse HEAD)"
[[ "$LIVE_AUTH" == "$EXPECTED_AUTHORITY_SHA" ]] || fail "live authority SHA mismatch"
[[ -z "$(sudo git -c safe.directory="$AUTHORITY_ROOT" -C "$AUTHORITY_ROOT" status --porcelain=v1 --untracked-files=normal)" ]] || fail "live authority snapshot is dirty"

LIVE_PAD="$(sudo git -c safe.directory="$PAD_ROOT" -C "$PAD_ROOT" rev-parse HEAD)"
[[ "$LIVE_PAD" == "$EXPECTED_PAD_SHA" ]] || fail "live PADataset SHA mismatch"
[[ -z "$(sudo git -c safe.directory="$PAD_ROOT" -C "$PAD_ROOT" status --porcelain=v1 --untracked-files=normal)" ]] || fail "live PADataset snapshot is dirty"

sudo test -d "$EVIDENCE_ROOT" || fail "evidence root missing"
sudo mountpoint -q "$EVIDENCE_ROOT" || fail "evidence root is not a mountpoint"
OPTIONS="$(sudo findmnt -n -o OPTIONS --target "$EVIDENCE_ROOT")"
case ",$OPTIONS," in *,ro,*) ;; *) fail "evidence root is not read-only: $OPTIONS" ;; esac
for required in nosuid nodev noexec; do
  case ",$OPTIONS," in *,"$required",*) ;; *) fail "evidence root missing $required: $OPTIONS" ;; esac
done

if sudo test -e "$MOUNTPOINT"; then
  sudo test -d "$MOUNTPOINT" || fail "expected mountpoint path is not a directory"
  echo "EVIDENCE_MOUNTPOINT_ALREADY_PRESENT=1"
else
  sudo mkdir -p "$MOUNTPOINT"
  sudo chown root:root "$PAD_ROOT/local_artifacts" "$MOUNTPOINT"
  sudo chmod 0755 "$PAD_ROOT/local_artifacts" "$MOUNTPOINT"
  echo "EVIDENCE_MOUNTPOINT_CREATED=1"
fi

[[ -z "$(sudo git -c safe.directory="$PAD_ROOT" -C "$PAD_ROOT" status --porcelain=v1 --untracked-files=normal)" ]] || fail "mountpoint repair dirtied PADataset source"

echo "AUTHORITY_SHA=$EXPECTED_AUTHORITY_SHA"
echo "PADATASET_SHA=$EXPECTED_PAD_SHA"
echo "EVIDENCE_OPTIONS=$OPTIONS"
echo "PADATASET_EVIDENCE_MOUNTPOINT_REPAIR=PASS"
