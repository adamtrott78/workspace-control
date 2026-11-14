import json
import re
import sys
from pathlib import Path

EXPECTED_CHECKS = {
    "hotkey_recognition_p95_ms",
    "clipboard_write_p95_ms",
    "existing_tab_activate_p95_ms",
    "reuse_ready_p50_composed_upper_bound_ms",
    "reuse_ready_p95_composed_upper_bound_ms",
    "reuse_ready_observed_max_composed_upper_bound_ms",
    "restore_ready_p95_composed_upper_bound_ms",
    "create_ready_p95_composed_upper_bound_ms",
    "cold_start_p95_composed_upper_bound_ms",
    "no_work_p95_composed_upper_bound_ms",
    "native_helper_working_set_mib_p95",
    "native_helper_plus_extension_incremental_mib_p95",
    "helper_idle_cpu_percent_one_logical_cpu_mean",
    "firefox_two_live_worker_tabs_working_set_mib_p95",
    "firefox_four_live_worker_tabs_working_set_mib_p95",
    "firefox_two_live_idle_tabs_cpu_percent_one_logical_cpu_mean",
    "discard_three_of_four_tabs_working_set_reduction_percent",
}

FORBIDDEN_KEY_PARTS = {
    "packet_text",
    "clipboard_content",
    "page_content",
    "response_text",
    "password",
    "cookie",
}


def fail(message: str) -> None:
    raise SystemExit(f"STAGE09_TARGET_EVIDENCE_INVALID: {message}")


def walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk_keys(item)


def main() -> None:
    if len(sys.argv) != 2:
        fail("expected one evidence path")

    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 1:
        fail("schema_version")
    if data.get("stage") != "impl_09_performance_benchmark_execution":
        fail("stage")
    if data.get("evidence_class") != "TARGET_WINDOWS_OPERATOR_WORKSTATION":
        fail("evidence_class")
    if data.get("target_contract_complete") is not True:
        fail("target_contract_complete")
    if not re.fullmatch(r"[0-9a-f]{40}", str(data.get("source_sha", ""))):
        fail("source_sha")

    env = data.get("environment", {})
    for key in (
        "machine_fingerprint",
        "os_build",
        "power_mode",
        "firefox_version",
        "chrome_version",
    ):
        if not env.get(key):
            fail(f"environment.{key}")
    for key in (
        "chrome_memory_saver_disabled",
        "same_name_process_isolation_valid",
        "background_noise_valid",
    ):
        if env.get(key) is not True:
            fail(f"environment.{key}")

    measurement = data.get("measurement", {})
    expected_measurement = {
        "warmup_seconds": 60,
        "steady_state_seconds": 120,
        "sample_rate_hz": 1,
        "browser_order_alternated": True,
    }
    for key, expected in expected_measurement.items():
        if measurement.get(key) != expected:
            fail(f"measurement.{key}")

    repetitions = data.get("repetitions", {})
    expected_repetitions = {
        "browser_resource": 3,
        "discard_restore": 5,
        "reuse": 50,
        "restore": 30,
        "create": 30,
        "cold_start": 10,
        "local_primitives": 100,
    }
    for key, expected in expected_repetitions.items():
        if repetitions.get(key) != expected:
            fail(f"repetitions.{key}")

    results = data.get("results", {})
    if len(results.get("firefox", {}).get("resource_replicates", [])) != 3:
        fail("firefox resource replicate count")
    if len(results.get("firefox", {}).get("no_extension_baselines", [])) != 3:
        fail("firefox no-extension baseline count")
    if len(results.get("firefox", {}).get("discard_restore_replicates", [])) != 5:
        fail("discard/restore replicate count")
    if len(results.get("chrome", {}).get("resource_replicates", [])) != 3:
        fail("chrome resource replicate count")

    checks = results.get("budget_evaluation", {}).get("checks", [])
    ids = {item.get("id") for item in checks}
    if ids != EXPECTED_CHECKS:
        fail("frozen budget check set")
    for item in checks:
        if item.get("pass_fail") not in {"PASS", "FAIL"}:
            fail("budget pass_fail")

    security = data.get("security", {})
    for key in (
        "dom_or_page_content_collected",
        "raw_urls_collected",
        "screenshots_collected",
        "credentials_or_tokens_collected",
        "synthetic_paste_enter_send_or_mouse",
    ):
        if security.get(key) is not False:
            fail(f"security.{key}")

    if data.get("blockers") != []:
        fail("blockers must be empty for a completed target execution")

    for key in walk_keys(data):
        lowered = key.lower()
        if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
            fail(f"forbidden persisted key {key}")

    print("STAGE09_TARGET_EVIDENCE_VALID=PASS")


if __name__ == "__main__":
    main()
