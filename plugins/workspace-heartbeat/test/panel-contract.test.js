import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const panel = readFileSync(
  new URL("../public/heartbeat-panel.html", import.meta.url),
  "utf8",
);
const live = readFileSync(
  new URL("../public/heartbeat-live-card.html", import.meta.url),
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
  assert.equal(panel.includes("latest.task_id"), true);
  assert.equal(panel.includes("x?.task_id===activeTaskId"), true);
  assert.equal(panel.includes("knownHistory=[];"), true);
  assert.equal(panel.includes('message.method==="ui/notifications/tool-input"'), true);
});

test("live card is scoped, rolling-three, and event-driven after a timed refresh", () => {
  assert.equal(live.includes("payload.recent.slice(-3)"), true);
  assert.equal(live.includes("item.task_id!==taskId"), true);
  assert.equal(live.includes('name:"heartbeat_snapshot"'), true);
  assert.equal(live.includes('footerEl.textContent="Showing last known progress'), true);
  assert.equal(live.includes("setInterval("), false);
});
