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
  assert.equal(store.get({ sessionId: "s9", taskId: "task-a" }).message, "Second");
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

test("omitted task id resolves the latest task for that session", () => {
  const store = new HeartbeatStore();
  store.update({ sessionId: "s1", taskId: "task-a", message: "A", state: "working" });
  store.update({ sessionId: "s1", taskId: "task-b", message: "B", state: "blocked" });

  assert.equal(store.get({ sessionId: "s1" }).task_id, "task-b");
});

test("snapshot keeps task history separate from cross-task timeline", () => {
  const store = new HeartbeatStore();
  store.update({
    sessionId: "s1",
    taskId: "parent",
    message: "Parent one",
    state: "working",
    now: new Date("2026-10-05T04:00:00Z"),
  });
  store.update({
    sessionId: "s1",
    taskId: "parent",
    message: "Parent two",
    state: "working",
    now: new Date("2026-10-05T04:00:01Z"),
  });
  store.update({
    sessionId: "s1",
    taskId: "child",
    message: "Child one",
    state: "working",
    now: new Date("2026-10-05T04:00:02Z"),
  });

  const snapshot = store.getSnapshot({ sessionId: "different-app-session", taskId: "child" });

  assert.deepEqual(snapshot.history.map((x) => x.message), ["Child one"]);
  assert.deepEqual(
    snapshot.timeline.map((x) => [x.task_id, x.message]),
    [
      ["parent", "Parent one"],
      ["parent", "Parent two"],
      ["child", "Child one"],
    ],
  );
});

test("same task recovers its timeline after session identity changes", () => {
  const store = new HeartbeatStore();
  store.update({
    sessionId: "s1",
    taskId: "task-a",
    message: "One",
    state: "working",
    now: new Date("2026-10-05T04:00:00Z"),
  });
  store.update({
    sessionId: "s2",
    taskId: "task-a",
    message: "Two",
    state: "working",
    now: new Date("2026-10-05T04:00:01Z"),
  });

  const snapshot = store.getSnapshot({ sessionId: "s3", taskId: "task-a" });
  assert.deepEqual(snapshot.timeline.map((x) => x.message), ["One", "Two"]);
});

test("timeline is bounded independently from task history", () => {
  const store = new HeartbeatStore({ historyLimit: 3, timelineLimit: 2 });
  store.update({ sessionId: "s1", taskId: "a", message: "One", state: "working" });
  store.update({ sessionId: "s1", taskId: "b", message: "Two", state: "working" });
  store.update({ sessionId: "s1", taskId: "c", message: "Three", state: "done" });

  const snapshot = store.getSnapshot({ sessionId: "s1", taskId: "c" });
  assert.deepEqual(snapshot.timeline.map((x) => x.message), ["Two", "Three"]);
});

test("missing heartbeat returns an empty snapshot", () => {
  const store = new HeartbeatStore();
  assert.deepEqual(store.getSnapshot({ sessionId: "s1" }), {
    heartbeat: null,
    history: [],
    timeline: [],
  });
});
