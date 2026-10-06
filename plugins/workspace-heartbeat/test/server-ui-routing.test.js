import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const server = readFileSync(new URL("../server.js", import.meta.url), "utf8");
const live = readFileSync(new URL("../public/heartbeat-live-card.html", import.meta.url), "utf8");
const panel = readFileSync(new URL("../public/heartbeat-panel.html", import.meta.url), "utf8");

function toolBlock(name,next){
  const start=server.indexOf('"'+name+'"');
  const end=next?server.indexOf('"'+next+'"',start):server.length;
  assert.ok(start>=0&&end>start);
  return server.slice(start,end);
}

test("v0.4.3 backend passes server syntax gate",()=>{
  assert.ok(server.includes('version: "0.4.3"'));
  assert.ok(server.includes('const LIVE_URI = "ui://workspace-heartbeat/live-v1.html"'));
});
test("heartbeat_update is data-only and fail-closed on writer conflicts",()=>{
  const block=toolBlock("heartbeat_update","heartbeat_writer");
  assert.ok(!block.includes("resourceUri:"));
  assert.ok(block.includes("structuredContent: { heartbeat }"));
  assert.ok(block.includes("leaseErrorResult(error)"));
});
test("heartbeat_writer exposes explicit handoff claim and recovery without UI",()=>{
  const block=toolBlock("heartbeat_writer","heartbeat_open");
  assert.ok(!block.includes("resourceUri:"));
  assert.ok(block.includes('z.enum(["handoff", "claim", "recover"])'));
  assert.ok(block.includes("expected_sequence: z.number().int().nonnegative()"));
  assert.ok(block.includes("store.handoff(args)"));
  assert.ok(block.includes("store.claim(args)"));
  assert.ok(block.includes("store.recover(args)"));
  assert.ok(!block.includes("${sessionId}"));
});
test("heartbeat_open mounts only the live resource, requires task_id, and is read-only",()=>{
  const block=toolBlock("heartbeat_open","heartbeat_snapshot");
  assert.ok(block.includes("resourceUri: LIVE_URI"));
  assert.ok(block.includes('visibility: ["model", "app"]'));
  assert.ok(block.includes("task_id: z.string().min(1).max(160)"));
  assert.ok(block.includes("snapshot.history.slice(-3)"));
  assert.ok(block.includes("readOnlyHint: true"));
  assert.ok(!block.includes("store.handoff("));
  assert.ok(!block.includes("store.claim("));
  assert.ok(!block.includes("store.recover("));
});
test("heartbeat_snapshot is app-only read-only, with no attached UI",()=>{
  const block=toolBlock("heartbeat_snapshot","heartbeat_get");
  assert.ok(block.includes('visibility: ["app"]'));
  assert.ok(block.includes('"openai/widgetAccessible": true'));
  assert.ok(!block.includes("resourceUri:"));
  assert.ok(block.includes("snapshot.history.slice(-3)"));
  assert.ok(block.includes("readOnlyHint: true"));
  assert.ok(!block.includes("store.handoff("));
  assert.ok(!block.includes("store.claim("));
  assert.ok(!block.includes("store.recover("));
});
test("heartbeat_get remains read-only and never transfers writer ownership",()=>{
  const block=toolBlock("heartbeat_get",null);
  assert.ok(block.includes("readOnlyHint: true"));
  assert.ok(!block.includes("store.handoff("));
  assert.ok(!block.includes("store.claim("));
  assert.ok(!block.includes("store.recover("));
});
test("old repeated render path is removed",()=>{
  assert.ok(!server.includes('"heartbeat_render"'));
  assert.ok(!server.includes("summary-v1.html"));
});
test("live card fetches via MCP Apps bridge without remounting",()=>{
  assert.ok(live.includes('request("tools/call",{'));
  assert.ok(live.includes('name:"heartbeat_snapshot"'));
  assert.ok(live.includes("ui/initialize"));
  assert.ok(live.includes("ui/notifications/initialized"));
  assert.ok(live.includes("if(document.hidden)"));
  assert.ok(live.includes('latestState==="done"'));
  assert.ok(!live.includes("fetch("));
  assert.ok(!live.includes("window.openai.callTool"));
});
test("task-only side-panel history is preserved",()=>{
  assert.ok(panel.includes("const source=Array.isArray(snapshot.history)?snapshot.history:[];"));
  assert.ok(!panel.includes("snapshot.timeline)&&snapshot.timeline.length"));
  assert.ok(server.includes("resourceUri: PANEL_URI"));
  assert.ok(server.includes('entrypoints: [{ type: "thread" }]'));
});
test("natural prose guidance, early open, and explicit writer recovery are explicit",()=>{
  assert.ok(server.includes("findings and decisions over tool mechanics"));
  assert.ok(server.includes("action=handoff"));
  assert.ok(server.includes("action=claim"));
  assert.ok(server.includes("action=recover"));
  assert.ok(server.includes("stale evidence is rejected"));
});
