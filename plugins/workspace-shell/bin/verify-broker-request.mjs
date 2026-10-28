#!/usr/bin/env node
import { execFileSync } from "node:child_process";
import { readFileSync, realpathSync, statSync } from "node:fs";
import path from "node:path";
import {
  canonicalDigest,
  fail,
  sha256Hex,
  verifyCanonical,
} from "../src/core.js";

function readJson(file) {
  return JSON.parse(readFileSync(file, "utf8"));
}

function requireProtectedFile(file) {
  const stat = statSync(file);
  if (!stat.isFile()) fail("TRUST_FILE_INVALID", `${file} is not a regular file`);
  const testUnowned = process.env.WORKSPACE_SHELL_TEST_ALLOW_UNOWNED === "1" && typeof process.getuid === "function" && process.getuid() !== 0;
  if (!testUnowned) {
    if (stat.uid !== 0) fail("TRUST_FILE_OWNER", `${file} must be root-owned`);
    if ((stat.mode & 0o022) !== 0) fail("TRUST_FILE_MODE", `${file} must not be group/world writable`);
  }
}

function assertString(obj, field) {
  if (typeof obj?.[field] !== "string" || obj[field].length === 0) {
    fail("APPROVAL_FIELD_INVALID", `${field} must be a nonempty string`);
  }
}

function assertExact(value, expected, field) {
  if (value !== expected) {
    fail("APPROVAL_BINDING_MISMATCH", `${field} does not match broker-observed authority`);
  }
}

function parseTime(value, field) {
  const ms = Date.parse(value);
  if (!Number.isFinite(ms)) fail("APPROVAL_TIME_INVALID", `${field} is not RFC3339-compatible`);
  return ms;
}

function validateJsonSchema(value, schema, field = "parameters") {
  if (!schema || typeof schema !== "object") fail("PARAMETER_SCHEMA_INVALID", "helper parameter schema missing");
  const type = schema.type;
  if (type === "object") {
    if (value === null || Array.isArray(value) || typeof value !== "object") {
      fail("PARAMETER_SCHEMA_REJECTED", `${field} must be an object`);
    }
    const props = schema.properties ?? {};
    const required = new Set(schema.required ?? []);
    for (const key of required) {
      if (!(key in value)) fail("PARAMETER_SCHEMA_REJECTED", `${field} missing required key ${key}`);
    }
    if (schema.additionalProperties === false) {
      for (const key of Object.keys(value)) {
        if (!(key in props)) fail("PARAMETER_SCHEMA_REJECTED", `${field} has unexpected key ${key}`);
      }
    }
    for (const [key, child] of Object.entries(props)) {
      if (key in value) validateJsonSchema(value[key], child, `${field}.${key}`);
    }
    return;
  }
  if (type === "array") {
    if (!Array.isArray(value)) fail("PARAMETER_SCHEMA_REJECTED", `${field} must be an array`);
    if (Number.isInteger(schema.maxItems) && value.length > schema.maxItems) fail("PARAMETER_SCHEMA_REJECTED", `${field} too long`);
    if (Number.isInteger(schema.minItems) && value.length < schema.minItems) fail("PARAMETER_SCHEMA_REJECTED", `${field} too short`);
    for (let i = 0; i < value.length; i += 1) validateJsonSchema(value[i], schema.items ?? {}, `${field}[${i}]`);
    return;
  }
  if (type === "string") {
    if (typeof value !== "string") fail("PARAMETER_SCHEMA_REJECTED", `${field} must be a string`);
    if (Number.isInteger(schema.maxLength) && value.length > schema.maxLength) fail("PARAMETER_SCHEMA_REJECTED", `${field} too long`);
    if (Array.isArray(schema.enum) && !schema.enum.includes(value)) fail("PARAMETER_SCHEMA_REJECTED", `${field} is outside enum`);
    if (schema.pattern && !(new RegExp(schema.pattern).test(value))) fail("PARAMETER_SCHEMA_REJECTED", `${field} fails pattern`);
    return;
  }
  if (type === "integer") {
    if (!Number.isInteger(value)) fail("PARAMETER_SCHEMA_REJECTED", `${field} must be integer`);
    if (Number.isFinite(schema.minimum) && value < schema.minimum) fail("PARAMETER_SCHEMA_REJECTED", `${field} below minimum`);
    if (Number.isFinite(schema.maximum) && value > schema.maximum) fail("PARAMETER_SCHEMA_REJECTED", `${field} above maximum`);
    return;
  }
  if (type === "boolean") {
    if (typeof value !== "boolean") fail("PARAMETER_SCHEMA_REJECTED", `${field} must be boolean`);
    return;
  }
  if (type === undefined) return;
  fail("PARAMETER_SCHEMA_INVALID", `unsupported schema type ${type}`);
}

function hardenedGit(sourceRoot, args) {
  return execFileSync(
    "/usr/bin/git",
    [
      "-C",
      sourceRoot,
      "-c",
      "core.hooksPath=/dev/null",
      "-c",
      "core.fsmonitor=false",
      "-c",
      "diff.external=",
      "-c",
      "credential.helper=",
      ...args,
    ],
    {
      encoding: "utf8",
      timeout: 3000,
      maxBuffer: 65536,
      env: {
        PATH: "/usr/bin:/bin",
        LANG: "C.UTF-8",
        LC_ALL: "C.UTF-8",
        GIT_CONFIG_NOSYSTEM: "1",
        GIT_CONFIG_GLOBAL: "/dev/null",
        GIT_OPTIONAL_LOCKS: "0",
        GIT_TERMINAL_PROMPT: "0",
      },
    },
  ).trim();
}

function validateHelperConfinement(helper) {
  const confinement = helper.confinement ?? {
    capabilities: [],
    read_write_paths: [],
    network: "deny",
  };
  if (!Array.isArray(confinement.capabilities) || confinement.capabilities.length > 16) {
    fail("HELPER_CONFINEMENT_INVALID", "capabilities must be a bounded array");
  }
  for (const capability of confinement.capabilities) {
    if (typeof capability !== "string" || !/^CAP_[A-Z0-9_]+$/.test(capability)) {
      fail("HELPER_CONFINEMENT_INVALID", "invalid Linux capability name");
    }
  }

  if (!Array.isArray(confinement.read_write_paths) || confinement.read_write_paths.length > 16) {
    fail("HELPER_CONFINEMENT_INVALID", "read_write_paths must be a bounded array");
  }
  const forbidden = [
    "/",
    "/root",
    "/home/atrott/.ssh",
    "/home/atrott/.config/gh",
    "/home/atrott/.config/openai",
    "/home/atrott/.config/workspace-heartbeat",
    "/home/atrott/.config/workspace-shell",
    "/etc/workspace-shell",
    "/run/workspace-shell-control",
    "/var/lib/workspace-shell/receipts",
    "/var/lib/workspace-shell/helper-cache",
    "/var/lib/workspace-shell/replay",
  ];
  for (const item of confinement.read_write_paths) {
    if (
      typeof item !== "string" ||
      !path.isAbsolute(item) ||
      item.includes("\0") ||
      /\s/.test(item)
    ) {
      fail("HELPER_CONFINEMENT_INVALID", "read_write_paths entries must be absolute paths without whitespace");
    }
    const normalized = path.posix.normalize(item);
    if (
      forbidden.some((prefix) =>
        normalized === prefix || normalized.startsWith(prefix + "/")
      )
    ) {
      fail("HELPER_CONFINEMENT_INVALID", `helper write scope includes protected path ${normalized}`);
    }
  }
  if (!["deny", "host-reviewed"].includes(confinement.network)) {
    fail("HELPER_CONFINEMENT_INVALID", "network must be deny or host-reviewed");
  }
  return {
    capabilities: [...confinement.capabilities],
    read_write_paths: [...confinement.read_write_paths],
    network: confinement.network,
  };
}
function main() {
  if (process.argv.length !== 3) fail("USAGE", "expected broker config path");
  const configPath = process.argv[2];
  requireProtectedFile(configPath);
  const cfg = readJson(configPath);
  for (const p of [cfg.frontend_public_key, cfg.trusted_issuers, cfg.revocations, cfg.helper_registry]) {
    requireProtectedFile(p);
  }

  const input = readFileSync(0, "utf8");
  if (Buffer.byteLength(input) > 65536) fail("REQUEST_TOO_LARGE", "broker request exceeds 64 KiB");
  const request = JSON.parse(input);
  if (request.schema !== "workspace-shell-broker-request.v1") fail("BROKER_SCHEMA_INVALID", "unexpected broker request schema");

  const fr = request.frontend_request;
  if (!fr || typeof fr !== "object" || !fr.payload || typeof fr.signature !== "string") {
    fail("FRONTEND_REQUEST_INVALID", "signed frontend request missing");
  }
  const frontendPublicKey = readFileSync(cfg.frontend_public_key, "utf8");
  if (!verifyCanonical(fr.payload, fr.signature, frontendPublicKey)) {
    fail("FRONTEND_SIGNATURE_INVALID", "frontend request signature failed");
  }
  assertExact(fr.payload.schema, "workspace-shell-frontend-request.v1", "frontend schema");
  const frontendTimestamp = parseTime(fr.payload.timestamp, "frontend timestamp");
  if (Math.abs(Date.now() - frontendTimestamp) > 120000) {
    fail("FRONTEND_REQUEST_STALE", "signed frontend request is outside the 120-second freshness window");
  }

  const approval = request.approval;
  if (!approval || typeof approval !== "object" || !approval.payload || typeof approval.signature !== "string") {
    fail("APPROVAL_INVALID", "signed approval bundle missing");
  }
  const payload = approval.payload;
  if (payload.schema !== "workspace-shell-approval.v2") fail("APPROVAL_SCHEMA_INVALID", "unexpected approval schema");
  const required = [
    "approval_id","issuer_key_id","issued_at","expires_at","task_id","target",
    "design_authority_sha","policy_artifact_sha256",
    "helper_registry_version","helper_registry_sha256","helper_entry_sha256",
    "helper_id","helper_sha256",
    "expected_source_repository","expected_source_commit","expected_source_tree",
    "operation","parameter_schema_sha256","parameter_digest_sha256","nonce","idempotency_key","max_uses",
  ];
  for (const field of required) {
    if (payload[field] === undefined || payload[field] === null || payload[field] === "") {
      fail("APPROVAL_FIELD_MISSING", `approval field ${field} missing`);
    }
  }

  const trust = readJson(cfg.trusted_issuers);
  const issuer = trust.issuers?.[payload.issuer_key_id];
  if (!issuer || issuer.status !== "active" || typeof issuer.public_key_pem !== "string") {
    fail("APPROVAL_ISSUER_UNTRUSTED", "issuer key is absent or inactive");
  }
  const now = Date.now();
  if (issuer.not_before && now < parseTime(issuer.not_before, "issuer.not_before")) fail("APPROVAL_ISSUER_NOT_YET_VALID", "issuer key not yet valid");
  if (issuer.not_after && now >= parseTime(issuer.not_after, "issuer.not_after")) fail("APPROVAL_ISSUER_EXPIRED", "issuer key expired");
  if (!verifyCanonical(payload, approval.signature, issuer.public_key_pem)) {
    fail("APPROVAL_SIGNATURE_INVALID", "operator approval signature failed");
  }

  const revocations = readJson(cfg.revocations);
  if ((revocations.approval_ids ?? []).includes(payload.approval_id)) fail("APPROVAL_REVOKED", "approval ID revoked");
  if ((revocations.issuer_key_ids ?? []).includes(payload.issuer_key_id)) fail("APPROVAL_ISSUER_REVOKED", "issuer key revoked");

  const issuedAt = parseTime(payload.issued_at, "issued_at");
  const expiresAt = parseTime(payload.expires_at, "expires_at");
  if (expiresAt <= issuedAt || expiresAt - issuedAt > 15 * 60 * 1000) fail("APPROVAL_LIFETIME_INVALID", "approval lifetime exceeds 15 minutes");
  if (now < issuedAt - 30_000) fail("APPROVAL_NOT_YET_VALID", "approval issued_at is in the future");
  if (now >= expiresAt) fail("APPROVAL_EXPIRED", "approval expired");
  if (payload.max_uses !== 1) fail("APPROVAL_USE_LIMIT_INVALID", "v2 approval max_uses must equal 1");

  assertExact(payload.design_authority_sha, cfg.design_authority_sha, "design_authority_sha");
  assertExact(payload.policy_artifact_sha256, cfg.policy_artifact_sha256, "policy_artifact_sha256");

  assertExact(fr.payload.task_id, payload.task_id, "task_id");
  assertExact(fr.payload.target, payload.target, "target");
  assertExact(fr.payload.expected_sha, payload.expected_source_commit, "expected source commit");
  assertExact(fr.payload.helper_id, payload.helper_id, "helper_id");
  assertExact(fr.payload.helper_sha256, payload.helper_sha256, "helper_sha256");
  assertExact(fr.payload.parameter_digest_sha256, payload.parameter_digest_sha256, "parameter_digest_sha256");
  assertExact(fr.payload.nonce, payload.nonce, "nonce");
  assertExact(fr.payload.approval_id, payload.approval_id, "approval_id");

  const registry = readJson(cfg.helper_registry);
  assertExact(payload.helper_registry_version, registry.version, "helper_registry_version");
  assertExact(payload.helper_registry_sha256, canonicalDigest(registry), "helper_registry_sha256");
  const helper = registry.helpers?.[payload.helper_id];
  if (!helper) fail("HELPER_NOT_REGISTERED", "helper_id absent from root-owned registry");
  assertExact(payload.helper_entry_sha256, canonicalDigest(helper), "helper_entry_sha256");
  assertExact(payload.helper_sha256, helper.sha256, "registered helper sha256");
  assertExact(payload.target, helper.target, "registered helper target");
  assertExact(payload.operation, helper.operation, "registered helper operation");
  if (helper.enabled !== true) fail("HELPER_DISABLED", "registered helper is not enabled");

  const schemaDigest = canonicalDigest(helper.parameter_schema);
  assertExact(payload.parameter_schema_sha256, schemaDigest, "parameter schema digest");
  const parameterDigest = canonicalDigest(request.parameters);
  assertExact(payload.parameter_digest_sha256, parameterDigest, "exact parameter digest");
  validateJsonSchema(request.parameters, helper.parameter_schema);

  const sourceRoot = cfg.source_roots?.[payload.expected_source_repository];
  if (typeof sourceRoot !== "string" || !path.isAbsolute(sourceRoot)) fail("SOURCE_ROOT_UNTRUSTED", "source repository root is not pinned by broker config");
  assertExact(payload.expected_source_repository, helper.source_repository, "helper source repository");
  const observedCommit = hardenedGit(sourceRoot, ["rev-parse", "HEAD"]);
  const observedTree = hardenedGit(sourceRoot, ["rev-parse", "HEAD^{tree}"]);
  const dirty = hardenedGit(sourceRoot, ["status", "--porcelain=v1", "--untracked-files=normal"]);
  if (dirty) fail("SOURCE_DIRTY", "privileged source checkout is dirty");
  assertExact(payload.expected_source_commit, observedCommit, "observed source commit");
  assertExact(payload.expected_source_tree, observedTree, "observed source tree");

  const sourceReal = realpathSync(sourceRoot);
  const helperPath = realpathSync(path.resolve(sourceReal, helper.relative_path));
  const sourcePrefix = sourceReal.endsWith(path.sep) ? sourceReal : sourceReal + path.sep;
  if (!helperPath.startsWith(sourcePrefix)) {
    fail("HELPER_PATH_ESCAPE", "registered helper escaped source root through path or symlink traversal");
  }
  const helperBytes = readFileSync(helperPath);
  assertExact(sha256Hex(helperBytes), helper.sha256, "helper binary digest");

  const result = {
    ok: true,
    approval_id: payload.approval_id,
    issuer_key_id: payload.issuer_key_id,
    nonce: payload.nonce,
    idempotency_key: payload.idempotency_key,
    task_id: payload.task_id,
    target: payload.target,
    expected_source_commit: payload.expected_source_commit,
    expected_source_tree: payload.expected_source_tree,
    helper_id: payload.helper_id,
    helper_path: helperPath,
    helper_sha256: payload.helper_sha256,
    operation: payload.operation,
    parameters: request.parameters,
    timeout_ms: Math.min(Number(helper.timeout_ms ?? 90000), 90000),
    design_authority_sha: payload.design_authority_sha,
    policy_artifact_sha256: payload.policy_artifact_sha256,
    helper_registry_sha256: payload.helper_registry_sha256,
    helper_entry_sha256: payload.helper_entry_sha256,
    parameter_digest_sha256: payload.parameter_digest_sha256,
    confinement: validateHelperConfinement(helper),
  };
  process.stdout.write(JSON.stringify(result));
}

try {
  main();
} catch (error) {
  const code = error?.code ?? "BROKER_VERIFY_FAILED";
  const message = error instanceof Error ? error.message : String(error);
  process.stdout.write(JSON.stringify({ ok: false, error: { code, message } }));
  process.exitCode = 2;
}
