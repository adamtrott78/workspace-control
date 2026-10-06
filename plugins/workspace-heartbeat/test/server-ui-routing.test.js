import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const server = readFileSync(new URL("../server.js", import.meta.url), "utf8");
const summary = readFileSync(
  new URL("../public/heartbeat-summary-card.html", import.meta.url),
  "utf8",
);
const panel = readFileSync(
  new URL("../public/heartbeat-panel.html", import.meta.url),
  "utf8",
);

test("heartbeat_update remains data-only", () => {
  const updateStart = server.indexOf('"heartbeat_update"');
  const renderStart = server.indexOf('"heartbeat_render"');
  assert.notEqual(updateStart, -1);
  assert.notEqual(renderStart, -1);
  const updateBlock = server.slice(updateStart, renderStart);
  assert.equal(updateBlock.includes("resourceUri:"), false);
  assert.equal(updateBlock.includes("structuredContent: { heartbeat }"), true);
});

test("heartbeat_render owns one compact summary UI and is task scoped", () => {
  assert.equal(
    server.includes('const SUMMARY_URI = "ui://workspace-heartbeat/summary-v1.html";'),
    true,
  );
  const renderStart = server.indexOf('"heartbeat_render"');
  const getStart = server.indexOf('"heartbeat_get"');
  const renderBlock = server.slice(renderStart, getStart);
  assert.equal(renderBlock.includes("resourceUri: SUMMARY_URI"), true);
  assert.equal(renderBlock.includes("task_id: z.string().min(1).max(160)"), true);
  assert.equal(renderBlock.includes("snapshot.history.slice(-3)"), true);
  assert.equal(renderBlock.includes("snapshot.timeline"), false);
});

test("summary card renders at most three task-local updates", () => {
  assert.equal(summary.includes("snapshot.recent.slice(-3)"), true);
  assert.equal(summary.includes("full history in heartbeat panel"), true);
  assert.equal(summary.includes("timeline"), false);
});

test("heartbeat_get remains the full-history thread panel", () => {
  assert.equal(
    server.includes('const PANEL_URI = "ui://workspace-heartbeat/panel-v8.html";'),
    true,
  );
  const getStart = server.indexOf('"heartbeat_get"');
  const getBlock = server.slice(getStart);
  assert.equal(getBlock.includes("resourceUri: PANEL_URI"), true);
  assert.equal(getBlock.includes('entrypoints: [{ type: "thread" }]'), true);
});

test("side panel renders task history rather than cross-task timeline", () => {
  assert.equal(
    panel.includes("const source=Array.isArray(snapshot.history)?snapshot.history:[];"),
    true,
  );
  assert.equal(panel.includes("snapshot.timeline)&&snapshot.timeline.length"), false);
});

test("heartbeat prose guidance prefers natural semantic updates", () => {
  assert.equal(server.includes("normal conversational progress commentary"), true);
  assert.equal(server.includes("Prefer findings and decisions over narration of tool mechanics"), true);
  assert.equal(server.includes("Avoid headings, task IDs, sequence numbers, stage labels"), true);
});

test("heartbeat_render is end-of-turn only", () => {
  assert.equal(server.includes("call heartbeat_render exactly once"), true);
  assert.equal(server.includes("Call this at most once near the end"), true);
});
