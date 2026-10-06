from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "scripts" / "bootstrap_lambda_ci_p3_pgvector.sh").read_text()


def test_bootstrap_requires_root_explicit_authorization_and_exact_sha():
    assert 'WORKSPACE_CI_P3_PGVECTOR_AUTHORIZED' in SCRIPT
    assert 'WORKSPACE_CI_P3_PGVECTOR_EXPECTED_SHA' in SCRIPT
    assert 'UNEXPECTED_WORKSPACE_CONTROL_SHA' in SCRIPT


def test_exact_pgvector_version_and_official_key_are_pinned():
    assert 'VERSION="0.8.6-1.pgdg22.04+2"' in SCRIPT
    assert 'PGDG_FINGERPRINT="B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8"' in SCRIPT
    assert 'https://apt.postgresql.org/pub/repos/apt' in SCRIPT
    assert 'https://www.postgresql.org/media/keys/ACCC4CF8.asc' in SCRIPT


def test_no_package_install_or_system_apt_configuration_mutation():
    lowered = SCRIPT.lower()
    assert "apt-get install" not in lowered
    assert "dpkg -i" not in lowered
    assert "/etc/apt/sources.list.d" not in SCRIPT
    assert "apt-key" not in lowered
    assert "dpkg-deb -x" in SCRIPT
    assert "package_database_modified" in SCRIPT
    assert "apt_configuration_modified" in SCRIPT


def test_only_extension_runtime_files_are_promoted():
    assert 'TARGET_SO="$PKGLIBDIR/vector.so"' in SCRIPT
    assert 'TARGET_CONTROL="$TARGET_EXT_DIR/vector.control"' in SCRIPT
    assert "vector--*.sql" in SCRIPT
    assert "install -o root -g root -m 0644" in SCRIPT
    assert "postgresql.conf" not in SCRIPT.split("# Smoke-test only")[0]


def test_external_download_and_extraction_run_under_ci_controller():
    assert "runuser -u ci-controller" in SCRIPT
    assert "apt-get" in SCRIPT
    assert "gpg --batch --show-keys --with-colons" in SCRIPT


def test_smoke_test_is_ephemeral_unix_socket_only():
    assert "runuser -u ci-research-engine" in SCRIPT
    assert "listen_addresses = ''" in SCRIPT
    assert "unix_socket_directories" in SCRIPT
    assert "CREATE EXTENSION vector" in SCRIPT
    assert '"0.8.6"' in SCRIPT
    assert "production_database_modified" in SCRIPT


def test_production_postgres_master_must_not_change():
    assert "MASTER_BEFORE" in SCRIPT
    assert "MASTER_AFTER" in SCRIPT
    assert "PRODUCTION_POSTGRES_MASTER_CHANGED" in SCRIPT


def test_failure_rolls_back_only_manifested_files():
    assert "if [[ "$rc" -ne 0 && "$COPIED" == "1" ]]" in SCRIPT
    assert "installed_files" in SCRIPT
    assert "rm -f -- "$path"" in SCRIPT
