#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

TMP="$(mktemp -d /tmp/ws-private-route-serve-inspect.XXXXXX)"
cleanup() { rm -rf -- "$TMP"; }
trap cleanup EXIT

for cmd in sudo tailscale python3; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "ERROR=MISSING_COMMAND:$cmd" >&2
    exit 70
  }
done

sudo -v
sudo tailscale serve status --json >"$TMP/serve.json"
sudo tailscale funnel status --json >"$TMP/funnel.json"

python3 - "$TMP/serve.json" "$TMP/funnel.json" <<'PY'
import json, sys

def load(path):
    value = json.load(open(path, encoding="utf-8"))
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise SystemExit(f"STATUS_JSON_NOT_OBJECT:{path}")
    return value

serve = load(sys.argv[1])
funnel = load(sys.argv[2])

def subset(data):
    return {
        "TCP": data.get("TCP") or {},
        "Web": data.get("Web") or {},
        "AllowFunnel": data.get("AllowFunnel") or {},
        "Services": data.get("Services") or {},
    }

payload = {
    "serve": subset(serve),
    "funnel": subset(funnel),
}
print(
    "PRIVATE_ROUTE_EXISTING_TAILSCALE_CONFIG="
    + json.dumps(payload, sort_keys=True, separators=(",", ":"))
)
PY

echo "PRIVATE_ROUTE_EXISTING_TAILSCALE_CONFIG_READONLY=PASS"
