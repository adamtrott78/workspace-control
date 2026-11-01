import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { generateKeyPairSync } from "node:crypto";
import {
  chmodSync,
  mkdtempSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  buildFrontendRequest,
  canonicalDigest,
  sha256Hex,
  signCanonical,
  signFrontendRequest,
} from "../src/core.js";

const verifier = fileURLToPath(new URL("../bin/verify-broker-request.mjs", import.meta.url));

function git(cwd, args) {
  return execFileSync("/usr/bin/git", ["-C", cwd, ...args], {
    encoding: "utf8",
    env: {
      PATH: "/usr/bin:/bin",
      LANG: "C.UTF-8",
      LC_ALL: "C.UTF-8",
      GIT_CONFIG_NOSYSTEM: "1",
      GIT_CONFIG_GLOBAL: "/dev/null",
    },
  }).trim();
}

function fixture() {
  const root = mkdtempSync(path.join(os.tmpdir(), "workspace-shell-broker-"));
  const source = path.join(root, "source");
  mkdirSync(source);
  git(source, ["init"]);
  git(source, ["config", "user.email", "test@example.invalid"]);
  git(source, ["config", "user.name", "Workspace Shell Test"]);
  const helperPath = path.join(source, "helper.sh");
  writeFileSync(helperPath, "#!/bin/sh\ncat >/dev/null\nprintf 'ok\\n'\n");
  chmodSync(helperPath, 0o755);
  git(source, ["add", "helper.sh"]);
  git(source, ["commit", "-m", "helper"]);
  const commit = git(source, ["rev-parse", "HEAD"]);
  const tree = git(source, ["rev-parse", "HEAD^{tree}"]);
  const helperSha = sha256Hex(readFileSync(helperPath));

  const frontendKeys = generateKeyPairSync("ed25519");
  const issuerKeys = generateKeyPairSync("ed25519");
  const frontendPriv = frontendKeys.privateKey.export({ type: "pkcs8", format: "pem" });
  const frontendPub = frontendKeys.publicKey.export({ type: "spki", format: "pem" });
  const issuerPriv = issuerKeys.privateKey.export({ type: "pkcs8", format: "pem" });
  const issuerPub = issuerKeys.publicKey.export({ type: "spki", format: "pem" });

  const frontendPubPath = path.join(root, "frontend-public.pem");
  const trustPath = path.join(root, "trusted-issuers.json");
  const revocationsPath = path.join(root, "revocations.json");
  const registryPath = path.join(root, "helpers.json");
  const policyArtifactPath = path.join(root, "authority.json");
  const configPath = path.join(root, "verifier.json");
  writeFileSync(frontendPubPath, frontendPub);
  writeFileSync(policyArtifactPath, JSON.stringify({ authority: "test-policy-v1" }));

  const now = Date.now();
  writeFileSync(
    trustPath,
    JSON.stringify({
      schema_version: 1,
      issuers: {
        "operator-test": {
          status: "active",
          public_key_pem: issuerPub,
          not_before: new Date(now - 60_000).toISOString(),
          not_after: new Date(now + 86_400_000).toISOString(),
        },
      },
    }),
  );
  writeFileSync(revocationsPath, JSON.stringify({ approval_ids: [], issuer_key_ids: [] }));

  const parameterSchema = {
    type: "object",
    additionalProperties: false,
    required: ["mode"],
    properties: { mode: { type: "string", enum: ["safe"] } },
  };
  const helperEntry = {
    relative_path: "helper.sh",
    sha256: helperSha,
    target: "workspace-control",
    task_ids: ["task-abc"],
    operation: "noop",
    parameter_schema: parameterSchema,
    source_repository: "workspace-control",
    enabled: true,
    timeout_ms: 5000,
  };
  const registry = {
    schema_version: 1,
    version: "test-registry-v1",
    helpers: { "test-helper": helperEntry },
  };
  writeFileSync(registryPath, JSON.stringify(registry));

  const cfg = {
    frontend_public_key: frontendPubPath,
    trusted_issuers: trustPath,
    revocations: revocationsPath,
    helper_registry: registryPath,
    design_authority_sha: "a".repeat(40),
    policy_artifact_path: policyArtifactPath,
    policy_artifact_sha256: sha256Hex(readFileSync(policyArtifactPath)),
    source_roots: { "workspace-control": source },
  };
  writeFileSync(configPath, JSON.stringify(cfg));

  function build({
    approvalMutator = null,
    requestMutator = null,
    signer = issuerPriv,
    issuedAt = new Date(now - 1000),
    expiresAt = new Date(now + 5 * 60_000),
    taskId = "task-abc",
  } = {}) {
    const parameters = { mode: "safe" };
    let approvalPayload = {
      schema: "workspace-shell-approval.v2",
      approval_id: "approval-12345678",
      issuer_key_id: "operator-test",
      issued_at: issuedAt.toISOString(),
      expires_at: expiresAt.toISOString(),
      task_id: taskId,
      target: "workspace-control",
      design_authority_sha: cfg.design_authority_sha,
      policy_artifact_sha256: cfg.policy_artifact_sha256,
      helper_registry_version: registry.version,
      helper_registry_sha256: canonicalDigest(registry),
      helper_entry_sha256: canonicalDigest(helperEntry),
      helper_id: "test-helper",
      helper_sha256: helperSha,
      expected_source_repository: "workspace-control",
      expected_source_commit: commit,
      expected_source_tree: tree,
      operation: "noop",
      parameter_schema_sha256: canonicalDigest(parameterSchema),
      parameter_digest_sha256: canonicalDigest(parameters),
      nonce: "nonce-12345678",
      idempotency_key: "idem-12345678",
      max_uses: 1,
    };
    if (approvalMutator) approvalPayload = approvalMutator({ ...approvalPayload });
    const approval = {
      payload: approvalPayload,
      signature: signCanonical(approvalPayload, signer),
    };
    let frontendPayload = buildFrontendRequest({
      requestId: "request-12345678",
      taskId,
      target: "workspace-control",
      expectedSha: commit,
      helperId: "test-helper",
      helperSha256: helperSha,
      nonce: approvalPayload.nonce,
      parameters,
      approvalId: approvalPayload.approval_id,
    });
    if (requestMutator) frontendPayload = requestMutator({ ...frontendPayload });
    return {
      schema: "workspace-shell-broker-request.v1",
      frontend_request: signFrontendRequest(frontendPayload, frontendPriv),
      approval,
      parameters,
    };
  }

  function verifyRequest(request) {
    const proc = spawnSync(process.execPath, [verifier, configPath], {
      input: JSON.stringify(request),
      encoding: "utf8",
      env: { ...process.env, WORKSPACE_SHELL_TEST_ALLOW_UNOWNED: "1" },
    });
    assert.ok(proc.stdout, proc.stderr);
    return JSON.parse(proc.stdout);
  }

  return {
    root,
    source,
    trustPath,
    revocationsPath,
    registryPath,
    policyArtifactPath,
    configPath,
    issuerPriv,
    build,
    verifyRequest,
  };
}

test("broker verifier accepts exact operator-signed exact authority", () => {
  const fx = fixture();
  const result = fx.verifyRequest(fx.build());
  assert.equal(result.ok, true);
  assert.equal(result.helper_id, "test-helper");
  assert.equal(result.task_id, "task-abc");
});

test("model-facing self-signed approval is rejected", () => {
  const fx = fixture();
  const attacker = generateKeyPairSync("ed25519").privateKey.export({ type: "pkcs8", format: "pem" });
  const result = fx.verifyRequest(fx.build({ signer: attacker }));
  assert.equal(result.ok, false);
  assert.match(result.error.code, /APPROVAL_SIGNATURE_INVALID/);
});

test("operator signer cannot widen the pinned design authority", () => {
  const fx = fixture();
  const result = fx.verifyRequest(
    fx.build({
      approvalMutator: (p) => ({
        ...p,
        design_authority_sha: "d".repeat(40),
        design_reviewed_head_sha: "d".repeat(40),
      }),
    }),
  );
  assert.equal(result.ok, false);
  assert.match(result.error.code, /APPROVAL_BINDING_MISMATCH/);
});

test("registered helper task scope is independently enforced", () => {
  const fx = fixture();
  const result = fx.verifyRequest(fx.build({ taskId: "task-other" }));
  assert.equal(result.ok, false);
  assert.equal(result.error.code, "HELPER_TASK_SCOPE_DENIED");
});

test("installed policy artifact drift is rejected independently", () => {
  const fx = fixture();
  const request = fx.build();
  writeFileSync(fx.policyArtifactPath, JSON.stringify({ authority: "drifted" }));
  const result = fx.verifyRequest(request);
  assert.equal(result.ok, false);
  assert.match(result.error.code, /APPROVAL_BINDING_MISMATCH/);
});

test("expired approval is rejected even with valid signature", () => {
  const fx = fixture();
  const now = Date.now();
  const result = fx.verifyRequest(
    fx.build({
      issuedAt: new Date(now - 10 * 60_000),
      expiresAt: new Date(now - 60_000),
    }),
  );
  assert.equal(result.ok, false);
  assert.equal(result.error.code, "APPROVAL_EXPIRED");
});

test("revoked approval is rejected", () => {
  const fx = fixture();
  writeFileSync(fx.revocationsPath, JSON.stringify({ approval_ids: ["approval-12345678"], issuer_key_ids: [] }));
  const result = fx.verifyRequest(fx.build());
  assert.equal(result.ok, false);
  assert.equal(result.error.code, "APPROVAL_REVOKED");
});

test("parameter tampering is rejected before helper execution", () => {
  const fx = fixture();
  const request = fx.build();
  request.parameters = { mode: "unsafe" };
  const result = fx.verifyRequest(request);
  assert.equal(result.ok, false);
  assert.match(result.error.code, /APPROVAL_BINDING_MISMATCH|PARAMETER_SCHEMA_REJECTED/);
});

test("stale signed frontend request is rejected", () => {
  const fx = fixture();
  const result = fx.verifyRequest(
    fx.build({
      requestMutator: (p) => ({
        ...p,
        timestamp: new Date(Date.now() - 5 * 60_000).toISOString(),
      }),
    }),
  );
  assert.equal(result.ok, false);
  assert.equal(result.error.code, "FRONTEND_REQUEST_STALE");
});
