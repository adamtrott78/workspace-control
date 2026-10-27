import {
  constants as fsConstants,
  closeSync,
  fstatSync,
  lstatSync,
  openSync,
  readFileSync,
  readSync,
} from "node:fs";
import { createHash, createPrivateKey, createPublicKey, sign, verify } from "node:crypto";
import net from "node:net";
import path from "node:path";

export class ShellPolicyError extends Error {
  constructor(code, message) {
    super(`${code}: ${message}`);
    this.code = code;
  }
}

export function fail(code, message) {
  throw new ShellPolicyError(code, message);
}

export function canonicalize(value) {
  if (value === null) return "null";
  if (value === true) return "true";
  if (value === false) return "false";
  if (typeof value === "string") return JSON.stringify(value);
  if (typeof value === "number") {
    if (!Number.isFinite(value)) fail("INVALID_JSON_NUMBER", "non-finite numbers are forbidden");
    return JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return "[" + value.map((item) => canonicalize(item)).join(",") + "]";
  }
  if (typeof value === "object") {
    const entries = Object.keys(value)
      .sort()
      .map((key) => JSON.stringify(key) + ":" + canonicalize(value[key]));
    return "{" + entries.join(",") + "}";
  }
  fail("INVALID_CANONICAL_VALUE", `unsupported JSON type ${typeof value}`);
}

export function sha256Hex(value) {
  const input = Buffer.isBuffer(value) ? value : Buffer.from(String(value), "utf8");
  return createHash("sha256").update(input).digest("hex");
}

export function canonicalDigest(value) {
  return sha256Hex(canonicalize(value));
}

export function signCanonical(payload, privateKeyPem) {
  const key = createPrivateKey(privateKeyPem);
  const signature = sign(null, Buffer.from(canonicalize(payload), "utf8"), key);
  return signature.toString("base64url");
}

export function verifyCanonical(payload, signature, publicKeyPem) {
  try {
    const key = createPublicKey(publicKeyPem);
    return verify(
      null,
      Buffer.from(canonicalize(payload), "utf8"),
      key,
      Buffer.from(signature, "base64url"),
    );
  } catch {
    return false;
  }
}

export function assertSha(value, field = "sha") {
  if (typeof value !== "string" || !/^[0-9a-f]{40}$/.test(value)) {
    fail("INVALID_SHA", `${field} must be a full lowercase 40-character Git SHA`);
  }
  return value;
}

export function assertTaskId(value) {
  if (typeof value !== "string" || !/^[a-z0-9][a-z0-9-]{2,100}$/.test(value)) {
    fail("INVALID_TASK_ID", "task_id does not match the frozen v1 grammar");
  }
  return value;
}

export function assertTarget(value) {
  if (value !== "workspace-control") {
    fail("TARGET_NOT_AUTHORIZED", "v1 unprivileged execution target is workspace-control only");
  }
  return value;
}

export function assertRelativePath(value, field = "path") {
  if (typeof value !== "string" || value.length === 0 || value.length > 512) {
    fail("INVALID_PATH", `${field} must be a non-empty bounded relative path`);
  }
  if (value.includes("\0") || path.posix.isAbsolute(value) || path.win32.isAbsolute(value)) {
    fail("PATH_ESCAPE", `${field} must be relative`);
  }
  const normalized = path.posix.normalize(value.replaceAll("\\", "/"));
  if (normalized === ".." || normalized.startsWith("../")) {
    fail("PATH_ESCAPE", `${field} escapes the workspace`);
  }
  if (normalized.split("/").includes(".git") && field !== "cwd") {
    fail("GIT_INTERNAL_PATH_DENIED", `${field} cannot address .git internals`);
  }
  return normalized === "." ? "." : normalized.replace(/^\.\//, "");
}

function assertArgvShape(argv) {
  if (!Array.isArray(argv) || argv.length < 1 || argv.length > 32) {
    fail("INVALID_ARGV", "argv must contain 1..32 entries");
  }
  let bytes = 0;
  for (const arg of argv) {
    if (typeof arg !== "string" || arg.length > 512 || arg.includes("\0") || arg.includes("\n") || arg.includes("\r")) {
      fail("INVALID_ARGV", "argv entries must be bounded single-line strings without NUL");
    }
    bytes += Buffer.byteLength(arg);
  }
  if (bytes > 16384) fail("INVALID_ARGV", "argv exceeds the v1 byte budget");
}

function validateGitRead(argv) {
  const exact = new Set([
    JSON.stringify(["rev-parse", "HEAD"]),
    JSON.stringify(["rev-parse", "HEAD^{tree}"]),
    JSON.stringify(["status", "--porcelain=v1", "--untracked-files=normal"]),
    JSON.stringify(["diff", "--name-status", "--no-ext-diff"]),
    JSON.stringify(["diff", "--stat", "--no-ext-diff"]),
  ]);
  if (exact.has(JSON.stringify(argv))) return;

  if (
    argv.length >= 4 &&
    argv[0] === "diff" &&
    argv[1] === "--name-status" &&
    argv[2] === "--no-ext-diff" &&
    argv[3] === "--"
  ) {
    for (const p of argv.slice(4)) assertRelativePath(p, "git path");
    return;
  }

  fail("PROFILE_ARGV_DENIED", "git-read argv is outside the fixed v1 grammar");
}

function validatePytest(argv) {
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (["-q", "-x", "--disable-warnings"].includes(arg)) continue;
    if (/^--maxfail=[1-9][0-9]?$/.test(arg)) continue;
    if (arg === "-k") {
      i += 1;
      if (i >= argv.length || argv[i].length === 0 || argv[i].length > 160) {
        fail("PROFILE_ARGV_DENIED", "-k requires a bounded expression");
      }
      continue;
    }
    const p = assertRelativePath(arg, "pytest path");
    if (!(p === "tests" || p.startsWith("tests/") || p === "plugins/workspace-shell/test" || p.startsWith("plugins/workspace-shell/test/"))) {
      fail("PROFILE_ARGV_DENIED", "pytest-bounded may address only repository test paths");
    }
  }
}

function validateWorkspaceControl(argv) {
  const cmd = argv[0];
  if (!["task-validate", "workflow-validate"].includes(cmd)) {
    fail("PROFILE_ARGV_DENIED", "validation-bounded exposes only task-validate/workflow-validate");
  }
  const allowedFlags = new Set(["--file", "--profile", "--json"]);
  for (let i = 1; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!allowedFlags.has(arg)) fail("PROFILE_ARGV_DENIED", `unsupported validation flag ${arg}`);
    if (arg === "--json") continue;
    i += 1;
    if (i >= argv.length) fail("PROFILE_ARGV_DENIED", `${arg} requires a value`);
    assertRelativePath(argv[i], arg);
  }
}

export function resolveProfile(profile, argv) {
  assertArgvShape(argv);
  switch (profile) {
    case "git-read":
      validateGitRead(argv);
      return {
        executable: "/usr/bin/git",
        argv,
        writeScratch: false,
        env: {
          GIT_CONFIG_NOSYSTEM: "1",
          GIT_CONFIG_GLOBAL: "/dev/null",
          GIT_OPTIONAL_LOCKS: "0",
        },
      };
    case "pytest-bounded":
      validatePytest(argv);
      return {
        executable: "/usr/bin/python3",
        argv: ["-m", "pytest", ...argv],
        writeScratch: true,
        env: {
          PYTEST_DISABLE_PLUGIN_AUTOLOAD: "1",
          PYTHONDONTWRITEBYTECODE: "1",
        },
      };
    case "validation-bounded":
      validateWorkspaceControl(argv);
      return {
        executable: "/usr/bin/python3",
        argv: ["scripts/workspace_control.py", ...argv],
        writeScratch: true,
        env: { PYTHONDONTWRITEBYTECODE: "1" },
      };
    default:
      fail("PROFILE_NOT_AUTHORIZED", "unknown Workspace Shell v1 profile");
  }
}

function readJsonFile(file, ownerUid) {
  try {
    const stat = lstatSync(file);
    if (!stat.isFile() || stat.isSymbolicLink()) {
      fail("AUTHORITY_FILE_INVALID", `${file} must be a regular non-symlink file`);
    }
    if (ownerUid !== null && stat.uid !== ownerUid) {
      fail("AUTHORITY_OWNER_MISMATCH", `${file} owner uid mismatch`);
    }
    if ((stat.mode & 0o022) !== 0) {
      fail("AUTHORITY_MODE_INVALID", `${file} must not be group/world writable`);
    }
    return JSON.parse(readFileSync(file, "utf8"));
  } catch (error) {
    if (error instanceof ShellPolicyError) throw error;
    fail("AUTHORITY_READ_FAILED", `cannot read trusted authority file ${file}: ${error.message}`);
  }
}

export function loadTaskCapsule(authorityRoot, taskId, { ownerUid = 0 } = {}) {
  assertTaskId(taskId);
  const candidates = [
    path.join(authorityRoot, "tasks", "active", taskId + ".json"),
    path.join(authorityRoot, "tasks", "completed", taskId + ".json"),
    path.join(authorityRoot, "tasks", "archive", taskId + ".json"),
  ];
  for (const candidate of candidates) {
    try {
      const capsule = readJsonFile(candidate, ownerUid);
      if (capsule.task_id !== taskId) {
        fail("TASK_ID_MISMATCH", "capsule task_id does not match requested task");
      }
      return { capsule, path: candidate };
    } catch (error) {
      if (
        error instanceof ShellPolicyError &&
        error.code === "AUTHORITY_READ_FAILED" &&
        /ENOENT/.test(error.message)
      ) {
        continue;
      }
      throw error;
    }
  }
  fail("TASK_NOT_FOUND", "durable task capsule not found in trusted authority root");
}

export function authorizeTaskExecution({
  authorityRoot,
  taskId,
  target,
  expectedSha,
  authorityOwnerUid = 0,
}) {
  assertTaskId(taskId);
  assertTarget(target);
  assertSha(expectedSha, "expected_sha");
  const { capsule, path: capsulePath } = loadTaskCapsule(
    authorityRoot,
    taskId,
    { ownerUid: authorityOwnerUid },
  );
  if (capsule.status !== "IN_PROGRESS") {
    fail(
      "TASK_STATE_DENIED",
      `task status ${capsule.status} does not permit Workspace Shell execution`,
    );
  }
  const repository = (capsule.repositories ?? []).find(
    (entry) => entry?.name === target,
  );
  if (!repository) {
    fail("TASK_TARGET_DENIED", "target repository is absent from durable task scope");
  }
  const boundSha =
    repository.remote?.checkpoint_sha ??
    repository.local?.head_sha ??
    null;
  if (!boundSha || !/^[0-9a-f]{40}$/.test(boundSha)) {
    fail("TASK_PROVENANCE_MISSING", "task repository has no exact checkpoint SHA binding");
  }
  if (expectedSha !== boundSha) {
    fail("TASK_SHA_MISMATCH", "expected_sha differs from durable task checkpoint");
  }
  return { capsule, capsulePath, repository };
}

export function buildFrontendRequest({
  requestId,
  taskId,
  target,
  expectedSha,
  helperId,
  helperSha256,
  nonce,
  parameters,
  approvalId,
  now = new Date(),
}) {
  assertTaskId(taskId);
  if (typeof target !== "string" || target.length < 2 || target.length > 100) {
    fail("INVALID_TARGET", "privileged target is invalid");
  }
  assertSha(expectedSha, "expected_sha");
  if (!/^[a-z0-9][a-z0-9._-]{2,100}$/.test(helperId)) fail("INVALID_HELPER_ID", "helper_id is invalid");
  if (!/^[0-9a-f]{64}$/.test(helperSha256)) fail("INVALID_HELPER_DIGEST", "helper_sha256 is invalid");
  if (typeof nonce !== "string" || nonce.length < 8 || nonce.length > 128) fail("INVALID_NONCE", "nonce is invalid");
  return {
    schema: "workspace-shell-frontend-request.v1",
    request_id: requestId,
    timestamp: now.toISOString(),
    task_id: taskId,
    target,
    expected_sha: expectedSha,
    helper_id: helperId,
    helper_sha256: helperSha256,
    parameter_digest_sha256: canonicalDigest(parameters),
    nonce,
    approval_id: approvalId,
  };
}

export function signFrontendRequest(payload, privateKeyPem) {
  return {
    payload,
    signature: signCanonical(payload, privateKeyPem),
  };
}

export async function unixRpc(socketPath, request, {
  timeoutMs = 5000,
  maxResponseBytes = 1024 * 1024,
  signal = null,
} = {}) {
  if (typeof socketPath !== "string" || !socketPath.startsWith("/")) {
    fail("INVALID_SOCKET_PATH", "control socket path must be absolute");
  }
  if (signal?.aborted) {
    fail("CONTROL_CANCELLED", "control-plane RPC was cancelled before connect");
  }
  const body = Buffer.from(canonicalize(request) + "\n", "utf8");
  if (body.length > 65536) fail("REQUEST_TOO_LARGE", "control request exceeds 64 KiB");

  return await new Promise((resolve, reject) => {
    const socket = net.createConnection({ path: socketPath });
    let total = 0;
    const chunks = [];
    let settled = false;

    const cleanup = () => {
      clearTimeout(timer);
      if (signal) signal.removeEventListener("abort", onAbort);
    };

    const finishError = (error) => {
      if (settled) return;
      settled = true;
      cleanup();
      socket.destroy();
      reject(error);
    };

    const onAbort = () => {
      finishError(new ShellPolicyError(
        "CONTROL_CANCELLED",
        "control-plane RPC was cancelled by the MCP caller",
      ));
    };

    const timer = setTimeout(() => {
      finishError(new ShellPolicyError("CONTROL_TIMEOUT", "control-plane RPC timed out"));
    }, timeoutMs);

    if (signal) signal.addEventListener("abort", onAbort, { once: true });

    socket.on("connect", () => {
      // Keep the connection open after the newline-framed request so the
      // root service can observe a real client disconnect as cancellation.
      socket.write(body);
    });
    socket.on("data", (chunk) => {
      total += chunk.length;
      if (total > maxResponseBytes) {
        finishError(new ShellPolicyError(
          "CONTROL_RESPONSE_TOO_LARGE",
          "control-plane response exceeded bound",
        ));
        return;
      }
      chunks.push(chunk);
    });
    socket.on("error", (error) => {
      finishError(new ShellPolicyError("CONTROL_RPC_FAILED", error.message));
    });
    socket.on("end", () => {
      if (settled) return;
      settled = true;
      cleanup();
      try {
        const text = Buffer.concat(chunks).toString("utf8").trim();
        if (!text) throw new Error("empty control-plane response");
        resolve(JSON.parse(text));
      } catch (error) {
        reject(new ShellPolicyError("CONTROL_RESPONSE_INVALID", error.message));
      } finally {
        socket.destroy();
      }
    });
  });
}

export function readReceiptNoFollow(receiptRoot, receiptId, {
  expectedUid = null,
  maxBytes = 256 * 1024,
} = {}) {
  if (!/^[a-zA-Z0-9._-]{8,128}$/.test(receiptId)) fail("INVALID_RECEIPT_ID", "receipt_id is invalid");
  const root = path.resolve(receiptRoot);
  const file = path.resolve(root, receiptId + ".json");
  if (path.dirname(file) !== root) fail("RECEIPT_PATH_ESCAPE", "receipt path escaped root");

  const fd = openSync(file, fsConstants.O_RDONLY | fsConstants.O_NOFOLLOW);
  try {
    const stat = fstatSync(fd);
    if (!stat.isFile()) fail("RECEIPT_NOT_REGULAR", "receipt is not a regular file");
    if (expectedUid !== null && stat.uid !== expectedUid) fail("RECEIPT_OWNER_MISMATCH", "receipt owner mismatch");
    if (stat.size > maxBytes) fail("RECEIPT_TOO_LARGE", "receipt exceeds bound");
    const buffer = Buffer.alloc(stat.size);
    let offset = 0;
    while (offset < stat.size) {
      const n = readSync(fd, buffer, offset, stat.size - offset, offset);
      if (n <= 0) break;
      offset += n;
    }
    return JSON.parse(buffer.subarray(0, offset).toString("utf8"));
  } finally {
    closeSync(fd);
  }
}
