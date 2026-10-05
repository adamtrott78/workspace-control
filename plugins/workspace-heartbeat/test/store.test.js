import test from "node:test";
import assert from "node:assert/strict";
import { HeartbeatStore } from "../src/store.js";

test("sequence is monotonic per task across ChatGPT sessions", () => {
  const store = new HeartbeatStore();
  const first = store.update({
    sessionId: "s1",
    taskId: "task-a",
    message: "First",
    state: "working",
    now: new Date("2026-10-05T04:00:00Z"),
  });
  const second = store.update({
    sessionId: "s2",
    taskId: "task-a",
    message: "Second",
    state: "waiting",
    now: new Date("2026-10-05T04:00:01Z"),
  });

  assert.equal(first.sequence, 1);
  assert.equal(second.sequence, 2);
  assert.equal(store.get({ sessionId: "s1", taskId: "task-a" }).message, "Second");
});

test("explicit task lookup works across session identity changes", () => {
  const store = new HeartbeatStore();
  store.update({
    sessionId: "model-session",
    taskId: "task-a",
    message: "Visible to the task",
    state: "working",
  });

  assert.equal(
    store.get({ sessionId: "app-session", taskId: "task-a" }).message,
    "Visible to the task",
  );
});

test("omitted task id still resolves the latest task for that session", () => {
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

test("snapshot returns ordered bounded history", () => {
  const store = new HeartbeatStore({ historyLimit: 2 });
  store.update({
    sessionId: "s1",
    taskId: "task-a",
    message: "One",
    state: "working",
    now: new Date("2026-10-05T04:00:00Z"),
  });
  store.update({
    sessionId: "s1",
    taskId: "task-a",
    message: "Two",
    state: "working",
    now: new Date("2026-10-05T04:00:01Z"),
  });
  store.update({
    sessionId: "s2",
    taskId: "task-a",
    message: "Three",
    state: "done",
    now: new Date("2026-10-05T04:00:02Z"),
  });

  const snapshot = store.getSnapshot({ sessionId: "s9", taskId: "task-a" });
  assert.deepEqual(
    snapshot.history.map((item) => item.message),
    ["Two", "Three"],
  );
  assert.equal(snapshot.heartbeat.message, "Three");
  assert.equal(snapshot.heartbeat.sequence, 3);
});

test("missing heartbeat returns an empty snapshot", () => {
  const store = new HeartbeatStore();
  assert.deepEqual(store.getSnapshot({ sessionId: "s1" }), {
    heartbeat: null,
    history: [],
  });
});
