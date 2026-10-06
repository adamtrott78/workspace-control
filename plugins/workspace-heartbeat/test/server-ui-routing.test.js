import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const server = readFileSync(new URL("../server.js", import.meta.url), "utf8");

test("heartbeat_update is data-only while heartbeat_get owns the history UI", () => {
  assert.equal(server.includes('const PANEL_URI = "ui://workspace-heartbeat/panel-v7.html";'), true);
  assert.equal(server.includes("UPDATE_CARD_URI"), false);

  const updateStart = server.indexOf('"heartbeat_update"');
  const getStart = server.indexOf('"heartbeat_get"');

  assert.notEqual(updateStart, -1);
  assert.notEqual(getStart, -1);

  const updateBlock = server.slice(updateStart, getStart);
  const getBlock = server.slice(getStart);

  assert.equal(updateBlock.includes("resourceUri:"), false);
  assert.equal(updateBlock.includes("heartbeat.message"), true);
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

test("heartbeat_update returns only the newest heartbeat", () => {
  assert.equal(server.includes("const heartbeatUpdateOutputSchema"), true);
  assert.equal(server.includes("structuredContent: { heartbeat }"), true);

  const updateSchemaStart = server.indexOf("const heartbeatUpdateOutputSchema");
  const historySchemaStart = server.indexOf("const heartbeatOutputSchema");
  const updateSchema = server.slice(updateSchemaStart, historySchemaStart);

  assert.equal(updateSchema.includes("history:"), false);
  assert.equal(updateSchema.includes("timeline:"), false);
});

test("heartbeat_get retains task history and operator timeline", () => {
  assert.equal(server.includes("history: z.array(heartbeatSchema)"), true);
  assert.equal(server.includes("timeline: z.array(heartbeatSchema)"), true);
});


test("tool descriptions enforce native commentary mirror and explicit-only history", () => {
  assert.equal(
    server.includes("immediately repeat the exact heartbeat message as native assistant commentary"),
    true,
  );
  assert.equal(
    server.includes("Explicit history inspection only."),
    true,
  );
  assert.equal(
    server.includes("Do not call this during routine progress delivery"),
    true,
  );
});
