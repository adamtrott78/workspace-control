"""Control-owned sealed storage for hidden evaluator material.

This module does not confer execution authority. It provides a narrow
filesystem primitive for keeping evaluator-only oracle/seed/nonce state out of
worker-visible repositories and context packets.

Production use MUST configure a control-owned root (normally uid 0, mode 0700)
that is outside the worker namespace. Repository tests validate the storage
contract; live worker-read denial remains a separate runtime acceptance gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
from typing import Any, Mapping


_FIXTURE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class SealedStoreError(RuntimeError):
    """Fail-closed evaluator sealed-store error."""


@dataclass(frozen=True)
class SealedFixtureRecord:
    fixture_id: str
    record_sha256: str


@dataclass(frozen=True)
class SealedEvaluatorMaterial:
    fixture_id: str
    evaluator_oracle: Mapping[str, Any]
    seed_hex: str
    seal_nonce_hex: str


@dataclass(frozen=True)
class StagedEvaluatorFixture:
    record: SealedFixtureRecord
    worker_material: Mapping[str, Any]


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _secret_hex(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise SealedStoreError(f"{field}:required_hex_string")
    try:
        raw = bytes.fromhex(value)
    except ValueError as exc:
        raise SealedStoreError(f"{field}:invalid_hex") from exc
    if len(raw) < 16:
        raise SealedStoreError(f"{field}:minimum_16_secret_bytes")
    return value


def _fixture_id(value: object) -> str:
    if not isinstance(value, str) or not _FIXTURE_ID.fullmatch(value):
        raise SealedStoreError("fixture_id:invalid")
    return value


class FilesystemEvaluatorSealedStore:
    """Strict filesystem store for evaluator-only material.

    The root must already exist and be owned by the configured owner uid with
    mode 0700. Each record is created once as a regular non-symlink file owned
    by the same uid with mode 0600. Existing records are never overwritten.
    """

    def __init__(self, root: str | os.PathLike[str], *, owner_uid: int = 0) -> None:
        self._root = Path(root)
        self._owner_uid = owner_uid
        self._validate_root()

    @property
    def root(self) -> Path:
        return self._root

    def _validate_root(self) -> None:
        try:
            st = os.lstat(self._root)
        except FileNotFoundError as exc:
            raise SealedStoreError("sealed_root:missing") from exc
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
            raise SealedStoreError("sealed_root:must_be_real_directory")
        if st.st_uid != self._owner_uid:
            raise SealedStoreError("sealed_root:owner_mismatch")
        if stat.S_IMODE(st.st_mode) != 0o700:
            raise SealedStoreError("sealed_root:mode_must_be_0700")

    def _record_path(self, fixture_id: str) -> Path:
        fixture_id = _fixture_id(fixture_id)
        return self._root / f"{fixture_id}.sealed.json"

    def put(self, *, fixture_id: str, evaluator_oracle: Mapping[str, Any], seed_hex: str, seal_nonce_hex: str) -> SealedFixtureRecord:
        self._validate_root()
        fixture_id = _fixture_id(fixture_id)
        seed_hex = _secret_hex(seed_hex, field="seed_hex")
        seal_nonce_hex = _secret_hex(seal_nonce_hex, field="seal_nonce_hex")
        if evaluator_oracle.get("fixture_id") != fixture_id:
            raise SealedStoreError("evaluator_oracle:fixture_id_mismatch")

        payload = {
            "schema_version": 1,
            "fixture_id": fixture_id,
            "visibility": "evaluator_only",
            "evaluator_oracle": dict(evaluator_oracle),
            "seed_hex": seed_hex,
            "seal_nonce_hex": seal_nonce_hex,
        }
        encoded = _canonical_bytes(payload) + b"\n"
        path = self._record_path(fixture_id)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(path, flags, 0o600)
        except FileExistsError as exc:
            raise SealedStoreError("sealed_record:already_exists") from exc
        try:
            view = memoryview(encoded)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise SealedStoreError("sealed_record:short_write")
                view = view[written:]
            os.fsync(fd)
        finally:
            os.close(fd)

        st = os.lstat(path)
        if (stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode) or st.st_uid != self._owner_uid or stat.S_IMODE(st.st_mode) != 0o600):
            try:
                path.unlink()
            finally:
                raise SealedStoreError("sealed_record:postwrite_integrity_failure")

        return SealedFixtureRecord(
            fixture_id=fixture_id,
            record_sha256=sha256(encoded).hexdigest(),
        )

    def load(self, fixture_id: str) -> SealedEvaluatorMaterial:
        self._validate_root()
        path = self._record_path(fixture_id)
        try:
            st = os.lstat(path)
        except FileNotFoundError as exc:
            raise SealedStoreError("sealed_record:not_found") from exc
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
            raise SealedStoreError("sealed_record:not_regular")
        if st.st_uid != self._owner_uid:
            raise SealedStoreError("sealed_record:owner_mismatch")
        if stat.S_IMODE(st.st_mode) != 0o600:
            raise SealedStoreError("sealed_record:mode_must_be_0600")

        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("fixture_id") != fixture_id:
            raise SealedStoreError("sealed_record:fixture_id_mismatch")
        if payload.get("visibility") != "evaluator_only":
            raise SealedStoreError("sealed_record:visibility_mismatch")
        oracle = payload.get("evaluator_oracle")
        if not isinstance(oracle, Mapping):
            raise SealedStoreError("sealed_record:oracle_missing")
        seed_hex = _secret_hex(payload.get("seed_hex"), field="seed_hex")
        nonce_hex = _secret_hex(payload.get("seal_nonce_hex"), field="seal_nonce_hex")
        return SealedEvaluatorMaterial(
            fixture_id=fixture_id,
            evaluator_oracle=dict(oracle),
            seed_hex=seed_hex,
            seal_nonce_hex=nonce_hex,
        )


def stage_ephemeral_bundle(*, store: FilesystemEvaluatorSealedStore, bundle: Mapping[str, Any], seed_hex: str, seal_nonce_hex: str) -> StagedEvaluatorFixture:
    """Persist evaluator-only state and return worker-safe material only."""
    public_fixture = bundle.get("public_fixture")
    public_seal = bundle.get("public_seal")
    evaluator_oracle = bundle.get("evaluator_oracle")
    if not isinstance(public_fixture, Mapping):
        raise SealedStoreError("bundle:public_fixture_missing")
    if not isinstance(public_seal, Mapping):
        raise SealedStoreError("bundle:public_seal_missing")
    if not isinstance(evaluator_oracle, Mapping):
        raise SealedStoreError("bundle:evaluator_oracle_missing")

    fixture_id = _fixture_id(public_fixture.get("fixture_id"))
    if public_seal.get("fixture_id") != fixture_id:
        raise SealedStoreError("bundle:public_seal_fixture_mismatch")
    if evaluator_oracle.get("fixture_id") != fixture_id:
        raise SealedStoreError("bundle:evaluator_oracle_fixture_mismatch")

    record = store.put(
        fixture_id=fixture_id,
        evaluator_oracle=evaluator_oracle,
        seed_hex=seed_hex,
        seal_nonce_hex=seal_nonce_hex,
    )
    worker_material = {
        "public_fixture": dict(public_fixture),
        "public_seal": dict(public_seal),
    }
    return StagedEvaluatorFixture(record=record, worker_material=worker_material)
