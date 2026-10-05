import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../public/heartbeat-panel.html", import.meta.url), "utf8");

test("panel uses MCP Apps notifications and adaptive reconciliation", () => {
  assert.equal(html.includes("ui/notifications/tool-result"), true);
  assert.equal(html.includes("ui/initialize"), true);
  assert.equal(html.includes("tools/call"), true);
  assert.equal(html.includes("setInterval(refresh, 1000)"), false);
  assert.equal(html.includes("ACTIVE_MS=5000"), true);
  assert.equal(html.includes("QUIET_MS=15000"), true);
  assert.equal(html.includes("ERROR_MS=30000"), true);
  assert.equal(html.includes("document.visibilityState"), true);
  assert.equal(html.includes("retained update"), true);
});
