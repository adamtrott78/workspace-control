import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const panel = readFileSync(
  new URL("../public/heartbeat-panel.html", import.meta.url),
  "utf8",
);
const summary = readFileSync(
  new URL("../public/heartbeat-summary-card.html", import.meta.url),
  "utf8",
);

test("history panel is event-driven without background polling", () => {
  assert.equal(panel.includes("ui/notifications/tool-result"), true);
  assert.equal(panel.includes("ui/initialize"), true);
  assert.equal(panel.includes("tools/call"), false);
  assert.equal(panel.includes("reconcile"), false);
  assert.equal(panel.includes("setInterval("), false);
  assert.equal(panel.includes("setTimeout("), false);
  assert.equal(panel.includes("setWidgetState"), true);
});

test("history panel renders full task-local history instead of cross-task timeline", () => {
  assert.equal(
    panel.includes(
      "const source=Array.isArray(snapshot.history)?snapshot.history:[];",
    ),
    true,
  );
  assert.equal(panel.includes("snapshot.timeline)&&snapshot.timeline.length"), false);
  assert.equal(panel.includes("taskCount=new Set"), false);
  assert.equal(panel.includes("for "+latest.task_id), true);
});

test("compact summary renders only the rolling task-local window", () => {
  assert.equal(summary.includes("snapshot.recent.slice(-3)"), true);
  assert.equal(summary.includes("latest.task_id"), true);
  assert.equal(summary.includes("full history in heartbeat panel"), true);
  assert.equal(summary.includes("timeline"), false);
  assert.equal(summary.includes("setWidgetState"), false);
  assert.equal(summary.includes("setInterval("), false);
  assert.equal(summary.includes("setTimeout("), false);
});
