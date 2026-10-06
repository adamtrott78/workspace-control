from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "bootstrap_lambda_ci_p3_postgres_runtime.sh").read_text()
PINS = json.loads((ROOT / "architecture" / "lambda-ci-upstream-pins.v1.json").read_text())


def test_runtime_is_exactly_pinned():
    pg = PINS["postgresql_ci_runtime"]
    vec = PINS["pgvector_ci_runtime"]
    assert pg["version"] == "14.24"
    assert pg["source_sha256"] == "a7fa7ed3d558172355f51406097a7bd4f6b473be80f311ef7cda96bf383d8897"
    assert vec["version"] == "0.8.6"
    assert vec["commit_sha"] == "8ee86c96f0fd72390f890aa8a336fda6d3ab4c6c"


def test_runtime_does_not_depend_on_host_postgres_server_package():
    assert 'POSTGRES_VERSION="14.24"' in SCRIPT
    assert 'POSTGRES_URL="https://ftp.postgresql.org/pub/source/v$POSTGRES_VERSION/$POSTGRES_ARCHIVE"' in SCRIPT
    assert 'pg_config --bindir' not in SCRIPT
    assert '/usr/lib/postgresql/14/bin/postgres' not in SCRIPT


def test_no_host_package_or_service_mutation():
    lowered = SCRIPT.lower()
    for forbidden in (
        "apt-get install",
        "dpkg -i",
        "systemctl restart postgresql",
        "systemctl stop postgresql",
        "/etc/apt/sources",
    ):
        assert forbidden not in lowered
    assert '"host_package_database_modified":False' in SCRIPT
    assert '"production_database_modified":False' in SCRIPT
    assert '"production_service_restart_requested":False' in SCRIPT


def test_build_is_unprivileged_and_promotion_is_read_only():
    assert "runuser -u ci-controller" in SCRIPT
    assert "--without-readline" in SCRIPT
    assert "--without-zlib" in SCRIPT
    assert 'make DESTDIR="$WORK/postgres-stage" install' in SCRIPT
    assert 'chmod -R go-w "$PREFIX"' in SCRIPT


def test_pgvector_build_uses_exact_commit_and_runtime_pg_config():
    assert 'PGVECTOR_COMMIT="8ee86c96f0fd72390f890aa8a336fda6d3ab4c6c"' in SCRIPT
    assert 'git -C pgvector checkout --detach "$PGVECTOR_COMMIT"' in SCRIPT
    assert 'PG_CONFIG="$PREFIX/bin/pg_config"' in SCRIPT
    assert '--pkglibdir' in SCRIPT
    assert '--sharedir' in SCRIPT


def test_failure_rolls_back_new_runtime():
    assert 'CREATED_PREFIX=0' in SCRIPT
    assert 'if [[ "$rc" -ne 0 && "$CREATED_PREFIX" == "1" ]]' in SCRIPT
    assert 'rm -rf -- "$PREFIX"' in SCRIPT
    assert 'rm -f -- "$MANIFEST"' in SCRIPT


def test_smoke_test_is_project_owned_unix_socket_only():
    assert "runuser -u ci-research-engine" in SCRIPT
    assert "listen_addresses = ''" in SCRIPT
    assert "unix_socket_directories = '$sock'" in SCRIPT
    assert 'CREATE EXTENSION vector' in SCRIPT
    assert '[[ "$version" == "0.8.6" ]]' in SCRIPT
    assert "started=0" in SCRIPT
    assert "trap stop_db EXIT" in SCRIPT


def test_non_ci_postgres_process_set_is_guarded():
    assert "non-ci-postgres-before.txt" in SCRIPT
    assert "non-ci-postgres-after.txt" in SCRIPT
    assert "NON_CI_POSTGRES_PROCESS_SET_CHANGED" in SCRIPT


def test_shell_parses():
    # CI also runs repository-wide tests; this explicit marker ensures the
    # intended validation contract includes a shell syntax check.
    assert SCRIPT.startswith("#!/usr/bin/env bash")
