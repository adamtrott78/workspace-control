import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const server = readFileSync(new URL("../server.js", import.meta.url), "utf8");

test("both heartbeat tools bind to the same panel resource", () => {
  assert.equal(server.includes('const PANEL_URI = "ui://workspace-heartbeat/panel-v5.html";'), true);

  const updateStart = server.indexOf('"heartbeat_update"');
  const getStart = server.indexOf('"heartbeat_get"');

  assert.notEqual(updateStart, -1);
  assert.notEqual(getStart, -1);

  const updateBlock = server.slice(updateStart, getStart);
  const getBlock = server.slice(getStart);

  assert.equal(updateBlock.includes("resourceUri: PANEL_URI"), true);
  assert.equal(getBlock.includes("resourceUri: PANEL_URI"), true);
});

test("only heartbeat_get advertises the thread entrypoint", () => {
  const updateStart = server.indexOf('"heartbeat_update"');
  const getStart = server.indexOf('"heartbeat_get"');
  const updateBlock = server.slice(updateStart, getStart);
  const getBlock = server.slice(getStart);

  assert.equal(updateBlock.includes('entrypoints: [{ type: "thread" }]'), false);
  assert.equal(getBlock.includes('entrypoints: [{ type: "thread" }]'), true);
});
