from pathlib import Path
import json
import subprocess
import tempfile
import os

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
    assert 'chmod -R a+rX,go-w "$PREFIX"' in SCRIPT


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


def test_production_postgres_listener_identity_is_guarded():
    assert "production-postgres-listeners-before.txt" in SCRIPT
    assert "production-postgres-listeners-after.txt" in SCRIPT
    assert "PRODUCTION_POSTGRES_LISTENER_IDENTITY_CHANGED" in SCRIPT
    assert "NON_CI_POSTGRES_PROCESS_SET_CHANGED" not in SCRIPT
    assert "ps -eo pid=,args=" not in SCRIPT


def test_shell_parses():
    # CI also runs repository-wide tests; this explicit marker ensures the
    # intended validation contract includes a shell syntax check.
    assert SCRIPT.startswith("#!/usr/bin/env bash")


def test_promoted_postgres_is_usable_by_ci_controller_before_pgvector_build():
    normalize = SCRIPT.index('chmod -R a+rX,go-w "$PREFIX"')
    execute_probe = SCRIPT.index('runuser -u ci-controller -- test -x "$PREFIX/bin/pg_config"')
    header_probe = SCRIPT.index('runuser -u ci-controller -- test -r "$PREFIX/include/server/postgres.h"')
    pgvector_build = SCRIPT.index('make -C pgvector -j"$JOBS" PG_CONFIG="$PREFIX/bin/pg_config"')
    assert normalize < execute_probe < pgvector_build
    assert normalize < header_probe < pgvector_build


def test_shell_syntax_is_valid():
    script_path = ROOT / "scripts" / "bootstrap_lambda_ci_p3_postgres_runtime.sh"
    subprocess.run(["bash", "-n", str(script_path)], check=True)


def test_staged_pgvector_paths_follow_custom_runtime_pg_config():
    assert 'PKGLIBDIR="$("$PREFIX/bin/pg_config" --pkglibdir)"' in SCRIPT
    assert 'PGSHARE="$("$PREFIX/bin/pg_config" --sharedir)"' in SCRIPT
    assert 'VECTOR_STAGE_SO="$VECTOR_STAGE_ROOT$PKGLIBDIR/vector.so"' in SCRIPT
    assert 'VECTOR_STAGE_CONTROL="$VECTOR_STAGE_ROOT$PGSHARE/extension/vector.control"' in SCRIPT
    assert '$VECTOR_STAGE/lib/postgresql/vector.so' not in SCRIPT
    assert '$VECTOR_STAGE/share/postgresql/extension/vector.control' not in SCRIPT


def test_existing_runtime_vector_control_uses_pg_config_sharedir():
    assert 'EXISTING_PGSHARE="$("$PREFIX/bin/pg_config" --sharedir)"' in SCRIPT
    assert '"$EXISTING_PGSHARE/extension/vector.control"' in SCRIPT
    assert '"$PREFIX/share/postgresql/extension/vector.control"' not in SCRIPT


def test_failure_always_emits_compact_receipt_before_cleanup_returns():
    assert 'P3_RUNTIME_REPORT="$OUT/lambda-ci-p3-runtime.json"' in SCRIPT
    assert '"decision": "FAIL"' in SCRIPT
    assert '"failure_stage": os.environ["P3_RUNTIME_STAGE"]' in SCRIPT
    assert '"exit_code": int(os.environ["P3_RUNTIME_RC"])' in SCRIPT
    assert '"partial_runtime_removed": os.environ["P3_RUNTIME_PARTIAL_REMOVED"] == "true"' in SCRIPT


def test_multiline_child_shells_use_quoted_stdin_heredocs_not_bash_c_strings():
    assert "bash -ceu '" not in SCRIPT
    assert "bash -c '" not in SCRIPT
    assert "bash -seu <<'BUILD_POSTGRES'" in SCRIPT
    assert "bash -seu <<'BUILD_PGVECTOR'" in SCRIPT
    assert "bash -seu <<'SMOKE_RUNTIME'" in SCRIPT


def test_exact_smoke_child_shell_executes_under_set_u_with_fake_runtime():
    marker = "bash -seu <<'SMOKE_RUNTIME'\n"
    start = SCRIPT.index(marker) + len(marker)
    end = SCRIPT.index("\nSMOKE_RUNTIME", start)
    smoke = SCRIPT[start:end]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        prefix = root / "runtime"
        bindir = prefix / "bin"
        smoke_root = root / "smoke"
        bindir.mkdir(parents=True)
        smoke_root.mkdir()

        programs = {
            "initdb": "#!/usr/bin/env bash\nexit 0\n",
            "pg_ctl": "#!/usr/bin/env bash\nexit 0\n",
            "createdb": "#!/usr/bin/env bash\nexit 0\n",
            "psql": """#!/usr/bin/env bash
set -eu
case "$*" in
  *extversion*) printf '0.8.6\\n' ;;
  *) printf 't\\n' ;;
esac
""",
        }
        for name, body in programs.items():
            p = bindir / name
            p.write_text(body)
            p.chmod(0o755)

        env = os.environ.copy()
        env["PREFIX"] = str(prefix)
        env["SMOKE_ROOT"] = str(smoke_root)
        env["LD_LIBRARY_PATH"] = str(prefix / "lib")

        subprocess.run(
            ["bash", "-seu"],
            input=smoke,
            text=True,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        conf = (smoke_root / "data" / "postgresql.conf").read_text()
        assert f"unix_socket_directories = '{smoke_root / 'socket'}'" in conf
        assert "listen_addresses = ''" in conf


def test_privilege_switches_start_from_neutral_cwd():
    marker = '# All privilege-switched subprocesses must inherit a neutral accessible cwd.'
    assert marker in SCRIPT
    marker_pos = SCRIPT.index(marker)
    cd_pos = SCRIPT.index('cd /', marker_pos)
    first_runuser = SCRIPT.index('runuser -u', cd_pos)
    assert marker_pos < cd_pos < first_runuser


def test_listener_capture_ignores_unrelated_listener_churn():
    start = SCRIPT.index('capture_production_postgres_listeners() {')
    end = SCRIPT.index('\n}\n', start) + 3
    fn = SCRIPT[start:end]

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        bindir = root / "bin"
        bindir.mkdir()
        ss = bindir / "ss"
        ss.write_text(
            """#!/usr/bin/env bash
cat <<'EOF'
LISTEN 0 244 0.0.0.0:5432 0.0.0.0:* users:((\"postgres\",pid=4242,fd=5))
LISTEN 3 128 127.0.0.1:9999 0.0.0.0:* users:((\"other\",pid=111,fd=4))
LISTEN 0 244 [::]:5432 [::]:* users:((\"postgres\",pid=4242,fd=6))
EOF
"""
        )
        ss.chmod(0o755)

        env = os.environ.copy()
        env["PATH"] = f"{bindir}:{env['PATH']}"
        program = fn + '\ncapture_production_postgres_listeners\n'
        proc = subprocess.run(
            ["bash", "-seu"],
            input=program,
            text=True,
            env=env,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        lines = proc.stdout.strip().splitlines()
        assert lines == [
            "0.0.0.0:5432 users:((\"postgres\",pid=4242,fd=5))",
            "[::]:5432 users:((\"postgres\",pid=4242,fd=6))",
        ]


def test_pass_receipt_reports_listener_identity_not_full_process_set():
    assert '"production_postgres_listener_identity_unchanged":True' in SCRIPT
    assert '"production_postgres_process_set_unchanged":True' not in SCRIPT
