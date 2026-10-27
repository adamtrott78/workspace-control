import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync } from "node:crypto";
import { mkdtempSync, mkdirSync, writeFileSync, symlinkSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  authorizeTaskExecution,
  canonicalize,
  readReceiptNoFollow,
  resolveProfile,
  signCanonical,
  verifyCanonical,
} from "../src/core.js";

test("canonical JSON and Ed25519 signatures are deterministic", () => {
  assert.equal(canonicalize({ b: 2, a: [true, "x"] }), '{"a":[true,"x"],"b":2}');
  const { privateKey, publicKey } = generateKeyPairSync("ed25519");
  const priv = privateKey.export({ type: "pkcs8", format: "pem" });
  const pub = publicKey.export({ type: "spki", format: "pem" });
  const payload = { z: "last", a: 1, nested: { y: false, x: "ok" } };
  const sig = signCanonical(payload, priv);
  assert.equal(verifyCanonical(payload, sig, pub), true);
  assert.equal(verifyCanonical({ ...payload, a: 2 }, sig, pub), false);
});

test("profile grammars reject shell/interpreter/config escape shapes", () => {
  assert.equal(resolveProfile("git-read", ["rev-parse", "HEAD"]).executable, "/usr/bin/git");
  assert.throws(
    () => resolveProfile("git-read", ["-c", "alias.x=!sh", "x"]),
    /PROFILE_ARGV_DENIED/,
  );
  assert.throws(
    () => resolveProfile("git-read", ["status;rm", "-rf", "/"]),
    /PROFILE_ARGV_DENIED/,
  );
  assert.throws(
    () => resolveProfile("pytest-bounded", ["-p", "malicious_plugin"]),
    /PROFILE_ARGV_DENIED|PATH_ESCAPE/,
  );
  assert.throws(
    () => resolveProfile("pytest-bounded", ["../../etc/passwd"]),
    /PATH_ESCAPE/,
  );
  assert.throws(
    () => resolveProfile("validation-bounded", ["preflight", "--repo", "workspace-control"]),
    /PROFILE_ARGV_DENIED/,
  );
});

test("task authority is read from the trusted authority root and target-bound", () => {
  const root = mkdtempSync(path.join(os.tmpdir(), "workspace-shell-task-"));
  mkdirSync(path.join(root, "tasks", "active"), { recursive: true });
  writeFileSync(
    path.join(root, "tasks", "active", "task-abc.json"),
    JSON.stringify({
      schema_version: 2,
      task_id: "task-abc",
      status: "IN_PROGRESS",
      repositories: [{ name: "workspace-control", intent: "mutate" }],
    }),
  );
  const result = authorizeTaskExecution({
    authorityRoot: root,
    taskId: "task-abc",
    target: "workspace-control",
    expectedSha: "a".repeat(40),
  });
  assert.equal(result.repository.name, "workspace-control");
  assert.throws(
    () =>
      authorizeTaskExecution({
        authorityRoot: root,
        taskId: "task-abc",
        target: "research-engine",
        expectedSha: "a".repeat(40),
      }),
    /TARGET_NOT_AUTHORIZED/,
  );
});

test("receipt reader refuses symlink traversal", () => {
  const root = mkdtempSync(path.join(os.tmpdir(), "workspace-shell-receipt-"));
  const outside = path.join(root, "..", path.basename(root) + "-outside.json");
  writeFileSync(outside, JSON.stringify({ task_id: "task-abc" }));
  symlinkSync(outside, path.join(root, "receipt-12345678.json"));
  assert.throws(
    () => readReceiptNoFollow(root, "receipt-12345678"),
    /ELOOP|symbolic link|too many levels/i,
  );
});
