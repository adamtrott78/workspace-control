import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const server=readFileSync(new URL("../server.js",import.meta.url),"utf8");
const live=readFileSync(new URL("../public/heartbeat-live-card.html",import.meta.url),"utf8");
const panel=readFileSync(new URL("../public/heartbeat-panel.html",import.meta.url),"utf8");
const store=readFileSync(new URL("../src/store.js",import.meta.url),"utf8");

function toolBlock(name,next){
  const start=server.indexOf('"'+name+'"');
  const end=next?server.indexOf('"'+next+'"',start):server.length;
  assert.ok(start>=0&&end>start);
  return server.slice(start,end);
}

test("v0.4.8 backend and cache-busted live resource are explicit",()=>{
  assert.ok(server.includes('version: "0.4.8"'));
  assert.ok(server.includes('const LIVE_URI = "ui://workspace-heartbeat/live-v7.html"'));
});

test("heartbeat_begin_turn is the single mounted turn boundary",()=>{
  const block=toolBlock("heartbeat_begin_turn","heartbeat_update");
  assert.ok(block.includes("resourceUri: LIVE_URI"));
  assert.ok(block.includes('visibility: ["model", "app"]'));
  assert.ok(block.includes("store.beginTurn"));
  assert.ok(block.includes("message: z.string().min(1).max(4000)"));
});

test("heartbeat_update is data-only and requires explicit turn_id",()=>{
  const block=toolBlock("heartbeat_update","heartbeat_touch");
  assert.ok(!block.includes("resourceUri:"));
  assert.ok(block.includes("turn_id: z.string().min(1).max(160)"));
  assert.ok(block.includes("store.updateTurn"));
});

test("heartbeat_snapshot is app-only, turn-scoped, and exposes bounded full turn history",()=>{
  const block=toolBlock("heartbeat_snapshot","heartbeat_poll");
  assert.ok(block.includes('visibility: ["app"]'));
  assert.ok(block.includes("turn_id: z.string().min(1).max(160)"));
  assert.ok(block.includes("store.observeUi"));
  assert.ok(store.includes("observeUi({ taskId, turnId, now = new Date() })"));
  assert.ok(server.includes("last_ui_seen_at: z.string().nullable()"));
  assert.ok(server.includes("turn_history: z.array(heartbeatSchema).max(50)"));
  assert.ok(!block.includes("resourceUri:"));
});

test("legacy heartbeat_open and heartbeat_render tools are removed",()=>{
  assert.ok(!server.includes('"heartbeat_open"'));
  assert.ok(!server.includes('"heartbeat_render"'));
});

test("heartbeat_poll is app-only, turn-scoped, and delta bounded",()=>{
  const block=toolBlock("heartbeat_poll","heartbeat_get");
  assert.ok(block.includes('visibility: ["app"]'));
  assert.ok(block.includes("after_sequence: z.number().int().nonnegative().default(0)"));
  assert.ok(block.includes("store.observeUiDelta"));
  assert.ok(server.includes("turn_status: z.enum"));
  assert.ok(server.includes("updates: z.array(heartbeatSchema).max(50)"));
  assert.ok(!block.includes("resourceUri:"));
});

test("live card polls immutable task_id plus turn_id with last rendered sequence",()=>{
  assert.ok(live.includes('name:"heartbeat_poll"'));
  assert.ok(live.includes("after_sequence:afterSequence"));
  assert.ok(live.includes("item.turn_id!==turnId"));
  assert.ok(live.includes("payload.turn_status"));
  assert.ok(live.includes('ui/resource-teardown'));
});

test("semantic-delta, one-begin-turn, and 10-tool backstop guidance are explicit",()=>{
  assert.ok(server.includes("exactly once at the first natural user-facing progress point"));
  assert.ok(server.includes("never call heartbeat_begin_turn again until a later assistant response"));
  assert.ok(server.includes("more than 10 non-heartbeat tool operations"));
  assert.ok(server.includes("Commits, merges, checkpoints"));
  assert.ok(server.includes("its plugin contract is stale"));
});

test("executor touch cadence is explicit and does not mask semantic silence",()=>{
  const block=toolBlock("heartbeat_touch","heartbeat_snapshot");
  assert.ok(server.includes("at most three non-Heartbeat tool operations"));
  assert.ok(server.includes("touch before a fourth operation"));
  assert.ok(server.includes("Touches do not reset the separate 10-non-Heartbeat-tool semantic-silence backstop"));
  assert.ok(block.includes("does not reset the semantic-silence backstop"));
});

test("task-level side panel remains separate",()=>{
  assert.ok(panel.includes("snapshot.history"));
  assert.ok(server.includes("resourceUri: PANEL_URI"));
});
