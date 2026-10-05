import test from "node:test";
import assert from "node:assert/strict";
import { HeartbeatStore } from "../src/store.js";

test("update increments sequence per session and task", () => {
  const store = new HeartbeatStore();
  const first = store.update({
    sessionId: "s1",
    taskId: "task-a",
    message: "First",
    state: "working",
    now: new Date("2026-10-05T04:00:00Z"),
  });
  const second = store.update({
    sessionId: "s1",
    taskId: "task-a",
    message: "Second",
    state: "waiting",
    now: new Date("2026-10-05T04:00:01Z"),
  });

  assert.equal(first.sequence, 1);
  assert.equal(second.sequence, 2);
  assert.equal(store.get({ sessionId: "s1", taskId: "task-a" }).message, "Second");
});

test("sessions do not leak heartbeats into each other", () => {
  const store = new HeartbeatStore();
  store.update({
    sessionId: "s1",
    taskId: "task-a",
    message: "Private to s1",
    state: "working",
  });

  assert.equal(store.get({ sessionId: "s2", taskId: "task-a" }), null);
});

test("get without task id returns latest task for the session", () => {
  const store = new HeartbeatStore();
  store.update({
    sessionId: "s1",
    taskId: "task-a",
    message: "A",
    state: "working",
  });
  store.update({
    sessionId: "s1",
    taskId: "task-b",
    message: "B",
    state: "blocked",
  });

  assert.equal(store.get({ sessionId: "s1" }).task_id, "task-b");
});

test("missing heartbeat returns null", () => {
  const store = new HeartbeatStore();
  assert.equal(store.get({ sessionId: "s1" }), null);
});
