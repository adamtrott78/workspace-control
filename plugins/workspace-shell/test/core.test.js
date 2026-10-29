import test from "node:test";
import assert from "node:assert/strict";
import { generateKeyPairSync } from "node:crypto";
import { chmodSync, mkdtempSync, mkdirSync, writeFileSync, symlinkSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { Readable } from "node:stream";
import {
  RequestAdmissionLimiter,
  authorizeTaskExecution,
  canonicalize,
  readBoundedJsonBody,
  readReceiptNoFollow,
  resolveProfile,
  signCanonical,
  verifyCanonical,
} from "../src/core.js";

test("MCP admission limiter freezes two inflight and eight queued", async () => {
  const limiter = new RequestAdmissionLimiter({ maxInflight: 2, maxQueued: 8 });
  const release1 = await limiter.acquire();
  const release2 = await limiter.acquire();
  const queued = Array.from({ length: 8 }, () => limiter.acquire());
  assert.deepEqual(limiter.snapshot(), { inflight: 2, queued: 8 });
  await assert.rejects(limiter.acquire(), /MCP_QUEUE_FULL/);

  release1();
  const release3 = await queued[0];
  assert.deepEqual(limiter.snapshot(), { inflight: 2, queued: 7 });
  release3();
  const release4 = await queued[1];
  release4();
  release2();

  for (let i = 2; i < queued.length; i += 1) {
    const release = await queued[i];
    release();
  }
  assert.deepEqual(limiter.snapshot(), { inflight: 0, queued: 0 });
});

test("MCP body parser rejects over 64 KiB before SDK parsing", async () => {
  const valid = Buffer.from(JSON.stringify({ jsonrpc: "2.0", id: 1, method: "ping" }));
  assert.deepEqual(
    await readBoundedJsonBody(Readable.from([valid]), 65536),
    { jsonrpc: "2.0", id: 1, method: "ping" },
  );
  const oversized = Buffer.alloc(65537, 0x20);
  await assert.rejects(
    readBoundedJsonBody(Readable.from([oversized]), 65536),
    /MCP_REQUEST_TOO_LARGE/,
  );
  await assert.rejects(
    readBoundedJsonBody(Readable.from([Buffer.from("{")]), 65536),
    /MCP_REQUEST_INVALID/,
  );
});

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
  const gitRead = resolveProfile("git-read", ["rev-parse", "HEAD"]);
  assert.equal(gitRead.executable, "/usr/bin/git");
  assert.deepEqual(gitRead.argv.slice(0, 8), [
    "-c", "core.hooksPath=/dev/null",
    "-c", "core.fsmonitor=false",
    "-c", "diff.external=",
    "-c", "credential.helper=",
  ]);
  assert.deepEqual(gitRead.argv.slice(-2), ["rev-parse", "HEAD"]);
  assert.equal(gitRead.env.GIT_TERMINAL_PROMPT, "0");
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
      repositories: [{
        name: "workspace-control",
        intent: "mutate",
        remote: { checkpoint_sha: "a".repeat(40) },
      }],
    }),
  );
  const result = authorizeTaskExecution({
    authorityRoot: root,
    taskId: "task-abc",
    target: "workspace-control",
    expectedSha: "a".repeat(40),
    authorityOwnerUid: typeof process.getuid === "function" ? process.getuid() : null,
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


test("receipt reader verifies owner group and immutable mode", () => {
  const root = mkdtempSync(path.join(os.tmpdir(), "workspace-shell-receipt-mode-"));
  const receiptId = "receipt-abcdefgh";
  const file = path.join(root, receiptId + ".json");
  writeFileSync(file, JSON.stringify({ receipt_id: receiptId, task_id: "task-abc" }));
  chmodSync(file, 0o640);
  const receipt = readReceiptNoFollow(root, receiptId, {
    expectedUid: typeof process.getuid === "function" ? process.getuid() : null,
    expectedGid: typeof process.getgid === "function" ? process.getgid() : null,
  });
  assert.equal(receipt.task_id, "task-abc");

  chmodSync(file, 0o660);
  assert.throws(
    () => readReceiptNoFollow(root, receiptId, {
      expectedUid: typeof process.getuid === "function" ? process.getuid() : null,
      expectedGid: typeof process.getgid === "function" ? process.getgid() : null,
    }),
    /RECEIPT_MODE_INVALID/,
  );
});
