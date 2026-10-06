import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const panel=readFileSync(new URL("../public/heartbeat-panel.html",import.meta.url),"utf8");
const live=readFileSync(new URL("../public/heartbeat-live-card.html",import.meta.url),"utf8");

test("history panel remains explicit and non-polling",()=>{
  assert.ok(panel.includes("ui/notifications/tool-result"));
  assert.ok(panel.includes("snapshot.history"));
  assert.equal(panel.includes('tools/call'),false);
  assert.equal(panel.includes("setInterval("),false);
});

test("live card is turn-scoped rolling-three and self-refreshing",()=>{
  assert.ok(live.includes("payload.recent)?payload.recent.slice(-3)"));
  assert.ok(live.includes("item.task_id!==taskId||item.turn_id!==turnId"));
  assert.ok(live.includes('name:"heartbeat_snapshot"'));
  assert.ok(live.includes("payload.superseded"));
  assert.ok(live.includes("Turn complete · no longer live"));
  assert.equal(live.includes("setInterval("),false);
});
