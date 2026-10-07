import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const server=readFileSync(new URL("../server.js",import.meta.url),"utf8");
const live=readFileSync(new URL("../public/heartbeat-live-card.html",import.meta.url),"utf8");
const panel=readFileSync(new URL("../public/heartbeat-panel.html",import.meta.url),"utf8");

function toolBlock(name,next){
  const start=server.indexOf('"'+name+'"');
  const end=next?server.indexOf('"'+next+'"',start):server.length;
  assert.ok(start>=0&&end>start);
  return server.slice(start,end);
}

test("v0.4.4 backend and cache-busted live resource are explicit",()=>{
  assert.ok(server.includes('version: "0.4.4"'));
  assert.ok(server.includes('const LIVE_URI = "ui://workspace-heartbeat/live-v2.html"'));
});

test("heartbeat_begin_turn is the single mounted turn boundary",()=>{
  const block=toolBlock("heartbeat_begin_turn","heartbeat_update");
  assert.ok(block.includes("resourceUri: LIVE_URI"));
  assert.ok(block.includes('visibility: ["model", "app"]'));
  assert.ok(block.includes("store.beginTurn"));
  assert.ok(block.includes("message: z.string().min(1).max(4000)"));
});

test("heartbeat_update is data-only and requires explicit turn_id",()=>{
  const block=toolBlock("heartbeat_update","heartbeat_snapshot");
  assert.ok(!block.includes("resourceUri:"));
  assert.ok(block.includes("turn_id: z.string().min(1).max(160)"));
  assert.ok(block.includes("store.updateTurn"));
});

test("heartbeat_snapshot is app-only and turn-scoped",()=>{
  const block=toolBlock("heartbeat_snapshot","heartbeat_get");
  assert.ok(block.includes('visibility: ["app"]'));
  assert.ok(block.includes("turn_id: z.string().min(1).max(160)"));
  assert.ok(block.includes("store.getTurnSnapshot"));
  assert.ok(!block.includes("resourceUri:"));
});

test("legacy heartbeat_open and heartbeat_render tools are removed",()=>{
  assert.ok(!server.includes('"heartbeat_open"'));
  assert.ok(!server.includes('"heartbeat_render"'));
});

test("live card polls immutable task_id plus turn_id",()=>{
  assert.ok(live.includes('name:"heartbeat_snapshot"'));
  assert.ok(live.includes("arguments:{task_id:taskId,turn_id:turnId}"));
  assert.ok(live.includes("item.turn_id!==turnId"));
  assert.ok(live.includes("payload.superseded"));
  assert.ok(live.includes('ui/resource-teardown'));
});

test("stale-contract and begin-turn guidance are explicit",()=>{
  assert.ok(server.includes("FIRST call heartbeat_begin_turn"));
  assert.ok(server.includes("its plugin contract is stale"));
  assert.ok(server.includes("start a new conversation"));
});

test("task-level side panel remains separate",()=>{
  assert.ok(panel.includes("snapshot.history"));
  assert.ok(server.includes("resourceUri: PANEL_URI"));
});
