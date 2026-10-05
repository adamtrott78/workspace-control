#!/usr/bin/env python3

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePath


STAGES = (
    "C0_STATIC",
    "C1_IMPORT_ACCELERATOR",
    "C2A_BACKEND_TOOLCHAIN",
    "C2B_ENGINE_BOOT",
    "C3_CANARY",
    "C4_DOMAIN",
)
STAGE_ORDER = {stage: index for index, stage in enumerate(STAGES)}
RUNTIME_READY_STAGE = "C3_CANARY"

PASS = "PASS"
FAIL = "FAIL"
RUNNING = "RUNNING"
NOT_RUN = "NOT_RUN"
VALID_STAGE_STATUSES = {PASS, FAIL, RUNNING, NOT_RUN}

MISS_CERTIFICATION_ABSENT = "CERTIFICATION_ABSENT"
MISS_PACKAGE_ENVIRONMENT_CHANGED = "PACKAGE_ENVIRONMENT_CHANGED"
MISS_EXECUTION_CONTRACT_CHANGED = "EXECUTION_CONTRACT_CHANGED"
MISS_HOST_COMPATIBILITY_CHANGED = "HOST_COMPATIBILITY_CHANGED"
MISS_CERTIFICATION_INCOMPLETE = "CERTIFICATION_INCOMPLETE"

RECOVERY_COMPLETED_REUSE = "COMPLETED_REUSE"
RECOVERY_INSPECT_OWNER = "INSPECT_OWNER"
RECOVERY_RESUME_FAILED_STAGE = "RESUME_FAILED_STAGE"
RECOVERY_EXECUTE = "EXECUTE"
RECOVERY_EXECUTE_NEW_IDENTITY = "EXECUTE_NEW_IDENTITY"


class RuntimeCertificationError(ValueError):
    pass


def _require_nonempty_string(value, field):
    if not isinstance(value, str) or not value.strip():
        raise RuntimeCertificationError(f"{field}: expected non-empty string")
    return value.strip()


def _require_bool(value, field):
    if not isinstance(value, bool):
        raise RuntimeCertificationError(f"{field}: expected boolean")
    return value


def canonical_json_bytes(value):
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise RuntimeCertificationError(
            f"value is not canonical-JSON serializable: {exc}"
        ) from exc
    return text.encode("utf-8")


def stable_sha256(value):
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def build_execution_identity(identity_payload):
    if not isinstance(identity_payload, dict) or not identity_payload:
        raise RuntimeCertificationError(
            "identity_payload: expected non-empty object"
        )
    return stable_sha256(identity_payload)


def build_operation_id(
    *,
    task_id,
    git_sha,
    operation_type,
    execution_identity,
    material_inputs,
):
    task_id = _require_nonempty_string(task_id, "task_id")
    git_sha = _require_nonempty_string(git_sha, "git_sha")
    operation_type = _require_nonempty_string(
        operation_type, "operation_type"
    )
    execution_identity = _require_nonempty_string(
        execution_identity, "execution_identity"
    )
    if not isinstance(material_inputs, dict):
        raise RuntimeCertificationError(
            "material_inputs: expected object"
        )
    return stable_sha256(
        {
            "task_id": task_id,
            "git_sha": git_sha,
            "operation_type": operation_type,
            "execution_identity": execution_identity,
            "material_inputs": material_inputs,
        }
    )


def validate_stage_receipts(stage_receipts, execution_identity=None):
    if not isinstance(stage_receipts, list):
        raise RuntimeCertificationError(
            "stage_receipts: expected array"
        )

    seen = set()
    last_index = -1
    normalized = []

    for index, receipt in enumerate(stage_receipts):
        field = f"stage_receipts[{index}]"
        if not isinstance(receipt, dict):
            raise RuntimeCertificationError(f"{field}: expected object")

        stage = receipt.get("stage")
        if stage not in STAGE_ORDER:
            raise RuntimeCertificationError(
                f"{field}.stage: unknown certification stage"
            )
        if stage in seen:
            raise RuntimeCertificationError(
                f"{field}.stage: duplicate {stage}"
            )
        seen.add(stage)

        stage_index = STAGE_ORDER[stage]
        if stage_index <= last_index:
            raise RuntimeCertificationError(
                f"{field}.stage: receipts must follow certification order"
            )
        last_index = stage_index

        status = receipt.get("status")
        if status not in VALID_STAGE_STATUSES:
            raise RuntimeCertificationError(
                f"{field}.status: expected one of "
                f"{sorted(VALID_STAGE_STATUSES)}"
            )

        receipt_identity = receipt.get("execution_identity")
        if execution_identity is not None:
            if receipt_identity != execution_identity:
                raise RuntimeCertificationError(
                    f"{field}.execution_identity: identity mismatch"
                )
        elif receipt_identity is not None:
            _require_nonempty_string(
                receipt_identity, f"{field}.execution_identity"
            )

        normalized.append(receipt)

    return normalized


def first_required_nonpass(stage_receipts):
    by_stage = {item["stage"]: item for item in stage_receipts}
    for stage in STAGES[: STAGE_ORDER[RUNTIME_READY_STAGE] + 1]:
        receipt = by_stage.get(stage)
        if receipt is None or receipt.get("status") != PASS:
            return stage
    return None


def is_runtime_certified(certification):
    validate_certification(certification)
    if not certification.get("runtime_certified"):
        return False
    return first_required_nonpass(
        certification.get("stage_receipts", [])
    ) is None


def validate_failure_envelope(envelope):
    if not isinstance(envelope, dict):
        raise RuntimeCertificationError(
            "failure_envelope: expected object"
        )
    if envelope.get("schema_version") != 1:
        raise RuntimeCertificationError(
            "failure_envelope.schema_version: expected 1"
        )
    stage = envelope.get("stage")
    if stage not in STAGE_ORDER:
        raise RuntimeCertificationError(
            "failure_envelope.stage: unknown certification stage"
        )

    parent = envelope.get("parent_failure")
    causal = envelope.get("causal_failure")
    for field, obj in (
        ("parent_failure", parent),
        ("causal_failure", causal),
    ):
        if not isinstance(obj, dict):
            raise RuntimeCertificationError(
                f"failure_envelope.{field}: expected object"
            )
        _require_nonempty_string(
            obj.get("class"),
            f"failure_envelope.{field}.class",
        )
        _require_nonempty_string(
            obj.get("message"),
            f"failure_envelope.{field}.message",
        )

    role = causal.get("role")
    if role is not None:
        _require_nonempty_string(
            role, "failure_envelope.causal_failure.role"
        )

    state_flags = envelope.get("state_flags")
    if not isinstance(state_flags, dict):
        raise RuntimeCertificationError(
            "failure_envelope.state_flags: expected object"
        )
    for name in (
        "scientific_state_materialized",
        "production_routing_changed",
    ):
        _require_bool(
            state_flags.get(name),
            f"failure_envelope.state_flags.{name}",
        )

    counts = envelope.get("counts")
    if not isinstance(counts, dict):
        raise RuntimeCertificationError(
            "failure_envelope.counts: expected object"
        )
    for name in (
        "engine_init_completed",
        "inference_calls_started",
        "inference_calls_completed",
    ):
        value = counts.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise RuntimeCertificationError(
                f"failure_envelope.counts.{name}: "
                "expected non-negative integer"
            )

    if counts["inference_calls_completed"] > counts["inference_calls_started"]:
        raise RuntimeCertificationError(
            "failure_envelope.counts: completed calls cannot exceed "
            "started calls"
        )

    process = envelope.get("process")
    if process is not None:
        validate_process_identity(process)

    artifacts = envelope.get("artifacts")
    if artifacts is not None and not isinstance(artifacts, dict):
        raise RuntimeCertificationError(
            "failure_envelope.artifacts: expected object"
        )
    return True


def validate_process_identity(process):
    if not isinstance(process, dict):
        raise RuntimeCertificationError("process: expected object")
    role = process.get("role")
    if role is not None:
        _require_nonempty_string(role, "process.role")
    pid = process.get("pid")
    if pid is not None:
        if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
            raise RuntimeCertificationError(
                "process.pid: expected positive integer"
            )
    executable = process.get("executable")
    if executable is not None:
        _require_nonempty_string(executable, "process.executable")
    argv = process.get("argv")
    if argv is not None:
        if not isinstance(argv, list) or not argv:
            raise RuntimeCertificationError(
                "process.argv: expected non-empty array"
            )
        for index, arg in enumerate(argv):
            _require_nonempty_string(
                arg, f"process.argv[{index}]"
            )
    if pid is None and executable is None and argv is None:
        raise RuntimeCertificationError(
            "process: expected at least pid, executable, or argv"
        )
    return True


def validate_certification(certification):
    if not isinstance(certification, dict):
        raise RuntimeCertificationError(
            "certification: expected object"
        )
    if certification.get("schema_version") != 1:
        raise RuntimeCertificationError(
            "certification.schema_version: expected 1"
        )
    execution_identity = _require_nonempty_string(
        certification.get("execution_identity"),
        "certification.execution_identity",
    )
    _require_nonempty_string(
        certification.get("package_identity"),
        "certification.package_identity",
    )
    compatibility = certification.get("compatibility_predicates")
    if not isinstance(compatibility, dict):
        raise RuntimeCertificationError(
            "certification.compatibility_predicates: expected object"
        )

    receipts = validate_stage_receipts(
        certification.get("stage_receipts", []),
        execution_identity=execution_identity,
    )

    runtime_certified = certification.get("runtime_certified")
    _require_bool(
        runtime_certified,
        "certification.runtime_certified",
    )
    all_required_pass = first_required_nonpass(receipts) is None
    if runtime_certified != all_required_pass:
        raise RuntimeCertificationError(
            "certification.runtime_certified must equal "
            "C0-C3 PASS state"
        )

    failure = certification.get("failure_envelope")
    if failure is not None:
        validate_failure_envelope(failure)

    reuse = certification.get("reuse_layers")
    if reuse is not None:
        validate_reuse_layers(reuse)

    return True


def validate_reuse_layers(reuse):
    if not isinstance(reuse, dict):
        raise RuntimeCertificationError(
            "reuse_layers: expected object"
        )
    expected = {
        "R0_ENVIRONMENT",
        "R1_CERTIFICATION",
        "R2_COMPILED_CACHE",
        "R3_LIVE_SESSION",
    }
    if set(reuse) - expected:
        raise RuntimeCertificationError(
            "reuse_layers: unknown reuse layer"
        )
    valid_states = {
        "NOT_APPLICABLE",
        "MISS",
        "PRESENT_UNVERIFIED",
        "VERIFIED_REUSE",
        "VERIFIED_HIT",
        "HEALTHY_REUSE",
    }
    for name, value in reuse.items():
        if value not in valid_states:
            raise RuntimeCertificationError(
                f"reuse_layers.{name}: unknown state"
            )
    return True


def evaluate_certification_reuse(
    cached,
    *,
    requested_package_identity,
    requested_execution_identity,
    requested_compatibility_predicates,
):
    requested_package_identity = _require_nonempty_string(
        requested_package_identity,
        "requested_package_identity",
    )
    requested_execution_identity = _require_nonempty_string(
        requested_execution_identity,
        "requested_execution_identity",
    )
    if not isinstance(requested_compatibility_predicates, dict):
        raise RuntimeCertificationError(
            "requested_compatibility_predicates: expected object"
        )

    if cached is None:
        return {
            "decision": "MISS",
            "reason": MISS_CERTIFICATION_ABSENT,
            "package_environment_compatible": None,
            "install_or_rebuild_required": None,
            "revalidate_from_stage": "C0_STATIC",
        }

    validate_certification(cached)

    cached_package = cached["package_identity"]
    if cached_package != requested_package_identity:
        return {
            "decision": "MISS",
            "reason": MISS_PACKAGE_ENVIRONMENT_CHANGED,
            "package_environment_compatible": False,
            "install_or_rebuild_required": True,
            "revalidate_from_stage": "C0_STATIC",
        }

    if (
        cached["compatibility_predicates"]
        != requested_compatibility_predicates
    ):
        return {
            "decision": "MISS",
            "reason": MISS_HOST_COMPATIBILITY_CHANGED,
            "package_environment_compatible": True,
            "install_or_rebuild_required": False,
            "revalidate_from_stage": "C0_STATIC",
        }

    if cached["execution_identity"] != requested_execution_identity:
        return {
            "decision": "MISS",
            "reason": MISS_EXECUTION_CONTRACT_CHANGED,
            "package_environment_compatible": True,
            "install_or_rebuild_required": False,
            "revalidate_from_stage": "C1_IMPORT_ACCELERATOR",
        }

    incomplete = first_required_nonpass(cached["stage_receipts"])
    if incomplete is not None:
        return {
            "decision": "MISS",
            "reason": MISS_CERTIFICATION_INCOMPLETE,
            "package_environment_compatible": True,
            "install_or_rebuild_required": False,
            "revalidate_from_stage": incomplete,
        }

    return {
        "decision": "REUSE",
        "reason": "CERTIFICATION_VALID",
        "package_environment_compatible": True,
        "install_or_rebuild_required": False,
        "revalidate_from_stage": None,
    }


def validate_operation_receipt(receipt):
    if not isinstance(receipt, dict):
        raise RuntimeCertificationError(
            "operation_receipt: expected object"
        )
    if receipt.get("schema_version") != 1:
        raise RuntimeCertificationError(
            "operation_receipt.schema_version: expected 1"
        )
    for field in (
        "operation_id",
        "task_id",
        "git_sha",
        "operation_type",
        "execution_identity",
    ):
        _require_nonempty_string(
            receipt.get(field),
            f"operation_receipt.{field}",
        )
    status = receipt.get("status")
    if status not in {RUNNING, PASS, FAIL}:
        raise RuntimeCertificationError(
            "operation_receipt.status: expected RUNNING, PASS, or FAIL"
        )
    stage = receipt.get("terminal_stage")
    if stage is not None and stage not in STAGE_ORDER:
        raise RuntimeCertificationError(
            "operation_receipt.terminal_stage: unknown stage"
        )
    process = receipt.get("owner_process")
    if process is not None:
        validate_process_identity(process)
    failure = receipt.get("failure_envelope")
    if failure is not None:
        validate_failure_envelope(failure)
    return True


def recovery_decision(receipt, *, expected_operation_id):
    expected_operation_id = _require_nonempty_string(
        expected_operation_id,
        "expected_operation_id",
    )

    if receipt is None:
        return {
            "decision": RECOVERY_EXECUTE,
            "repeat_expensive_stage": False,
            "resume_stage": None,
        }

    validate_operation_receipt(receipt)

    if receipt["operation_id"] != expected_operation_id:
        return {
            "decision": RECOVERY_EXECUTE_NEW_IDENTITY,
            "repeat_expensive_stage": False,
            "resume_stage": None,
        }

    status = receipt["status"]
    if status == PASS:
        return {
            "decision": RECOVERY_COMPLETED_REUSE,
            "repeat_expensive_stage": False,
            "resume_stage": None,
        }
    if status == RUNNING:
        return {
            "decision": RECOVERY_INSPECT_OWNER,
            "repeat_expensive_stage": False,
            "resume_stage": receipt.get("terminal_stage"),
        }
    return {
        "decision": RECOVERY_RESUME_FAILED_STAGE,
        "repeat_expensive_stage": False,
        "resume_stage": receipt.get("terminal_stage"),
    }


def process_matches_signature(argv, signature):
    if not isinstance(argv, list) or not argv:
        return False
    if not isinstance(signature, dict):
        raise RuntimeCertificationError(
            "signature: expected object"
        )

    executable_basenames = signature.get("executable_basenames", [])
    if not isinstance(executable_basenames, list) or not executable_basenames:
        raise RuntimeCertificationError(
            "signature.executable_basenames: expected non-empty array"
        )
    executable_basenames = {
        _require_nonempty_string(
            item, "signature.executable_basenames[]"
        )
        for item in executable_basenames
    }

    if PurePath(argv[0]).name not in executable_basenames:
        return False

    exact_argv = signature.get("exact_argv")
    if exact_argv is not None:
        if not isinstance(exact_argv, list) or not exact_argv:
            raise RuntimeCertificationError(
                "signature.exact_argv: expected non-empty array"
            )
        return argv == exact_argv

    script_arg_index = signature.get("script_arg_index")
    script_basenames = signature.get("script_basenames")
    if script_arg_index is None or script_basenames is None:
        raise RuntimeCertificationError(
            "signature: expected exact_argv or script_arg_index + "
            "script_basenames"
        )
    if (
        not isinstance(script_arg_index, int)
        or isinstance(script_arg_index, bool)
        or script_arg_index < 1
    ):
        raise RuntimeCertificationError(
            "signature.script_arg_index: expected positive integer"
        )
    if not isinstance(script_basenames, list) or not script_basenames:
        raise RuntimeCertificationError(
            "signature.script_basenames: expected non-empty array"
        )
    if len(argv) <= script_arg_index:
        return False
    names = {
        _require_nonempty_string(
            item, "signature.script_basenames[]"
        )
        for item in script_basenames
    }
    return PurePath(argv[script_arg_index]).name in names


def find_matching_processes(signature, proc_root="/proc"):
    root = Path(proc_root)
    matches = []
    if not root.exists():
        return matches

    for entry in root.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            raw = (entry / "cmdline").read_bytes()
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            continue
        if not raw:
            continue
        argv = [
            part.decode("utf-8", errors="replace")
            for part in raw.split(b"\0")
            if part
        ]
        if process_matches_signature(argv, signature):
            matches.append(
                {
                    "pid": int(entry.name),
                    "executable": argv[0],
                    "argv": argv,
                }
            )
    return sorted(matches, key=lambda item: item["pid"])


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeCertificationError(
            f"could not read JSON {path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeCertificationError(
            f"invalid JSON in {path}: {exc}"
        ) from exc


def _print_json(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Workspace-control runtime certification, reuse, "
            "and recovery primitives."
        )
    )
    sub = parser.add_subparsers(dest="command", required=True)

    identity = sub.add_parser("execution-id")
    identity.add_argument("--identity-json", required=True)

    operation = sub.add_parser("operation-id")
    operation.add_argument("--task-id", required=True)
    operation.add_argument("--git-sha", required=True)
    operation.add_argument("--operation-type", required=True)
    operation.add_argument("--execution-identity", required=True)
    operation.add_argument("--material-inputs-json", required=True)

    cert = sub.add_parser("validate-certification")
    cert.add_argument("--certification", required=True)

    reuse = sub.add_parser("reuse-decision")
    reuse.add_argument("--cached-certification")
    reuse.add_argument("--package-identity", required=True)
    reuse.add_argument("--execution-identity", required=True)
    reuse.add_argument("--compatibility-json", required=True)

    recover = sub.add_parser("recover")
    recover.add_argument("--receipt")
    recover.add_argument("--operation-id", required=True)

    match = sub.add_parser("process-match")
    match.add_argument("--argv-json", required=True)
    match.add_argument("--signature-json", required=True)

    scan = sub.add_parser("process-scan")
    scan.add_argument("--signature-json", required=True)
    scan.add_argument("--proc-root", default="/proc")

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        if args.command == "execution-id":
            _print_json(
                {
                    "execution_identity": build_execution_identity(
                        load_json(args.identity_json)
                    )
                }
            )
            return 0

        if args.command == "operation-id":
            _print_json(
                {
                    "operation_id": build_operation_id(
                        task_id=args.task_id,
                        git_sha=args.git_sha,
                        operation_type=args.operation_type,
                        execution_identity=args.execution_identity,
                        material_inputs=load_json(
                            args.material_inputs_json
                        ),
                    )
                }
            )
            return 0

        if args.command == "validate-certification":
            cert = load_json(args.certification)
            validate_certification(cert)
            _print_json(
                {
                    "valid": True,
                    "runtime_certified": is_runtime_certified(cert),
                }
            )
            return 0

        if args.command == "reuse-decision":
            cached = (
                load_json(args.cached_certification)
                if args.cached_certification
                else None
            )
            _print_json(
                evaluate_certification_reuse(
                    cached,
                    requested_package_identity=args.package_identity,
                    requested_execution_identity=args.execution_identity,
                    requested_compatibility_predicates=load_json(
                        args.compatibility_json
                    ),
                )
            )
            return 0

        if args.command == "recover":
            receipt = load_json(args.receipt) if args.receipt else None
            _print_json(
                recovery_decision(
                    receipt,
                    expected_operation_id=args.operation_id,
                )
            )
            return 0

        if args.command == "process-match":
            argv_value = load_json(args.argv_json)
            if not isinstance(argv_value, list):
                raise RuntimeCertificationError(
                    "argv-json: expected JSON array"
                )
            _print_json(
                {
                    "match": process_matches_signature(
                        argv_value,
                        load_json(args.signature_json),
                    )
                }
            )
            return 0

        if args.command == "process-scan":
            _print_json(
                {
                    "matches": find_matching_processes(
                        load_json(args.signature_json),
                        proc_root=args.proc_root,
                    )
                }
            )
            return 0

        raise RuntimeCertificationError("unknown command")
    except RuntimeCertificationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
