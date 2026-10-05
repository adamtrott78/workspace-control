import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const html = readFileSync(new URL("../public/heartbeat-panel.html", import.meta.url), "utf8");

test("panel is event-driven without background polling", () => {
  assert.equal(html.includes("ui/notifications/tool-result"), true);
  assert.equal(html.includes("ui/initialize"), true);
  assert.equal(html.includes("tools/call"), false);
  assert.equal(html.includes("reconcile"), false);
  assert.equal(html.includes("setInterval("), false);
  assert.equal(html.includes("setTimeout("), false);
  assert.equal(html.includes("retained update"), true);
  assert.equal(html.includes("setWidgetState"), true);
});
