import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const panel = readFileSync(new URL("../public/heartbeat-panel.html", import.meta.url), "utf8");
const card = readFileSync(new URL("../public/heartbeat-update-card.html", import.meta.url), "utf8");

test("history panel is event-driven without background polling", () => {
  assert.equal(panel.includes("ui/notifications/tool-result"), true);
  assert.equal(panel.includes("ui/initialize"), true);
  assert.equal(panel.includes("tools/call"), false);
  assert.equal(panel.includes("reconcile"), false);
  assert.equal(panel.includes("setInterval("), false);
  assert.equal(panel.includes("setTimeout("), false);
  assert.equal(panel.includes("setWidgetState"), true);
});

test("history panel renders cross-task operator timeline", () => {
  assert.equal(panel.includes("snapshot.timeline"), true);
  assert.equal(panel.includes("task-boundary"), true);
  assert.equal(panel.includes("taskCount=new Set"), true);
});

test("update card renders only the invoking heartbeat", () => {
  assert.equal(card.includes("structured?.heartbeat"), true);
  assert.equal(card.includes("heartbeat.message"), true);
  assert.equal(card.includes("heartbeat.task_id"), true);
  assert.equal(card.includes("history"), false);
  assert.equal(card.includes("timeline"), false);
  assert.equal(card.includes("setWidgetState"), false);
  assert.equal(card.includes("setInterval("), false);
  assert.equal(card.includes("setTimeout("), false);
});
