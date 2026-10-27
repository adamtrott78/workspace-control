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

test("live card is turn-scoped, delta-polled, and self-refreshing",()=>{
  assert.ok(live.includes("payload.turn_history"));
  assert.ok(live.includes("payload.recent.slice(-3)"));
  assert.ok(live.includes("item.task_id!==taskId||item.turn_id!==turnId"));
  assert.ok(live.includes('name:"heartbeat_poll"'));
  assert.ok(live.includes("after_sequence:afterSequence"));
  assert.ok(live.includes("payload.turn_status"));
  assert.ok(live.includes("payload.resync"));
  assert.ok(live.includes("Turn complete · no longer live"));
  assert.ok(live.includes(".history.capped"));
  assert.ok(live.includes("turnHistory.length>5"));
  assert.ok(live.includes('ui/notifications/size-changed'));
  assert.ok(live.includes("--five-update-height"));
  assert.ok(live.includes("overflow-y:auto"));
  assert.ok(live.includes("shouldFollowLatest"));
  assert.equal(live.includes("setInterval("),false);
});
