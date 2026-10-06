import test from "node:test";
import assert from "node:assert/strict";
import { HeartbeatLeaseError, HeartbeatStore } from "../src/store.js";

function update(store, sessionId, taskId, message, state = "working", second = 0) {
  return store.update({
    sessionId,
    taskId,
    message,
    state,
    now: new Date(`2026-10-05T04:00:${String(second).padStart(2, "0")}Z`),
  });
}

test("first writer claims task and a different session is rejected without mutation", () => {
  const store = new HeartbeatStore();
  const first = update(store, "s1", "task-a", "First", "working", 0);

  assert.equal(first.sequence, 1);
  assert.throws(
    () => update(store, "s2", "task-a", "Rejected", "waiting", 1),
    (error) => {
      assert.ok(error instanceof HeartbeatLeaseError);
      assert.equal(error.code, "WRITER_OWNERSHIP_CONFLICT");
      assert.deepEqual(error.toPublic(), {
        code: "WRITER_OWNERSHIP_CONFLICT",
        task_id: "task-a",
        sequence: 1,
      });
      return true;
    },
  );

  const snapshot = store.getSnapshot({ sessionId: "s2", taskId: "task-a" });
  assert.equal(snapshot.heartbeat.sequence, 1);
  assert.deepEqual(snapshot.history.map((x) => x.message), ["First"]);
  assert.deepEqual(snapshot.timeline.map((x) => x.message), ["First"]);
  assert.equal(store.get({ sessionId: "s2" }), null);
});

test("different sessions can write different tasks concurrently", () => {
  const store = new HeartbeatStore();
  const a = update(store, "s1", "task-a", "A");
  const b = update(store, "s2", "task-b", "B");

  assert.equal(a.sequence, 1);
  assert.equal(b.sequence, 1);
  assert.equal(store.get({ sessionId: "s1", taskId: "task-a" }).message, "A");
  assert.equal(store.get({ sessionId: "s2", taskId: "task-b" }).message, "B");
});

test("owning session continues with monotonic sequence", () => {
  const store = new HeartbeatStore();
  update(store, "s1", "task-a", "One", "working", 0);
  const second = update(store, "s1", "task-a", "Two", "waiting", 1);

  assert.equal(second.sequence, 2);
});

test("read-only explicit task lookup works across session identity changes without stealing", () => {
  const store = new HeartbeatStore();
  update(store, "s1", "task-a", "Visible to the task");

  assert.equal(
    store.get({ sessionId: "s2", taskId: "task-a" }).message,
    "Visible to the task",
  );
  assert.equal(
    store.getSnapshot({ sessionId: "s2", taskId: "task-a" }).heartbeat.sequence,
    1,
  );

  const second = update(store, "s1", "task-a", "Owner still writes");
  assert.equal(second.sequence, 2);
});

test("omitted task id resolves the latest task for that writing session", () => {
  const store = new HeartbeatStore();
  update(store, "s1", "task-a", "A");
  update(store, "s1", "task-b", "B", "blocked");

  assert.equal(store.get({ sessionId: "s1" }).task_id, "task-b");
});

test("snapshot keeps task history separate from cross-task timeline", () => {
  const store = new HeartbeatStore();
  update(store, "s1", "parent", "Parent one", "working", 0);
  update(store, "s1", "parent", "Parent two", "working", 1);
  update(store, "s1", "child", "Child one", "working", 2);

  const snapshot = store.getSnapshot({
    sessionId: "different-app-session",
    taskId: "child",
  });

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

test("explicit normal handoff preserves history, sequence, and timeline", () => {
  const store = new HeartbeatStore();
  update(store, "s1", "task-a", "One", "working", 0);

  assert.deepEqual(
    store.handoff({ sessionId: "s1", taskId: "task-a", expectedSequence: 1 }),
    { task_id: "task-a", sequence: 1, status: "handoff_ready" },
  );

  assert.throws(
    () => update(store, "s2", "task-a", "Must claim first", "working", 1),
    (error) => error.code === "WRITER_HANDOFF_PENDING",
  );

  assert.deepEqual(
    store.claim({ sessionId: "s2", taskId: "task-a", expectedSequence: 1 }),
    { task_id: "task-a", sequence: 1, status: "owned" },
  );

  const second = update(store, "s2", "task-a", "Two", "working", 2);
  assert.equal(second.sequence, 2);

  const snapshot = store.getSnapshot({ sessionId: "s9", taskId: "task-a" });
  assert.deepEqual(snapshot.history.map((x) => x.message), ["One", "Two"]);
  assert.deepEqual(snapshot.timeline.map((x) => x.message), ["One", "Two"]);
});

test("only the current writer may release a normal handoff", () => {
  const store = new HeartbeatStore();
  update(store, "s1", "task-a", "One");

  assert.throws(
    () =>
      store.handoff({
        sessionId: "s2",
        taskId: "task-a",
        expectedSequence: 1,
      }),
    (error) => error.code === "WRITER_NOT_OWNER",
  );

  assert.equal(update(store, "s1", "task-a", "Two").sequence, 2);
});

test("recovery takeover is explicit, sequence-bound, and revokes the old writer", () => {
  const store = new HeartbeatStore();
  update(store, "s1", "task-a", "One");

  assert.deepEqual(
    store.recover({ sessionId: "s2", taskId: "task-a", expectedSequence: 1 }),
    { task_id: "task-a", sequence: 1, status: "recovered" },
  );

  const second = update(store, "s2", "task-a", "Recovered writer");
  assert.equal(second.sequence, 2);

  assert.throws(
    () => update(store, "s1", "task-a", "Stale writer"),
    (error) => error.code === "WRITER_OWNERSHIP_CONFLICT",
  );
});

test("stale recovery evidence is rejected without stealing a newer stream", () => {
  const store = new HeartbeatStore();
  update(store, "s1", "task-a", "One");
  update(store, "s1", "task-a", "Two");

  assert.throws(
    () =>
      store.recover({
        sessionId: "s2",
        taskId: "task-a",
        expectedSequence: 1,
      }),
    (error) => {
      assert.equal(error.code, "SEQUENCE_MISMATCH");
      assert.deepEqual(error.toPublic(), {
        code: "SEQUENCE_MISMATCH",
        task_id: "task-a",
        sequence: 2,
        expected_sequence: 1,
      });
      return true;
    },
  );

  assert.equal(update(store, "s1", "task-a", "Three").sequence, 3);
});

test("public lease results never expose raw hidden session identifiers", () => {
  const store = new HeartbeatStore();
  update(store, "raw-session-s1", "task-a", "One");

  let publicError;
  try {
    update(store, "raw-session-s2", "task-a", "Rejected");
  } catch (error) {
    publicError = error.toPublic();
  }

  const serialized = JSON.stringify(publicError);
  assert.equal(serialized.includes("raw-session-s1"), false);
  assert.equal(serialized.includes("raw-session-s2"), false);

  const handoff = store.handoff({
    sessionId: "raw-session-s1",
    taskId: "task-a",
    expectedSequence: 1,
  });
  const claim = store.claim({
    sessionId: "raw-session-s2",
    taskId: "task-a",
    expectedSequence: 1,
  });
  assert.equal(JSON.stringify(handoff).includes("raw-session"), false);
  assert.equal(JSON.stringify(claim).includes("raw-session"), false);
});

test("timeline is bounded independently from task history", () => {
  const store = new HeartbeatStore({ historyLimit: 3, timelineLimit: 2 });
  update(store, "s1", "a", "One");
  update(store, "s1", "b", "Two");
  update(store, "s1", "c", "Three", "done");

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
