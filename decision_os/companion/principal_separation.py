"""Fail-closed macOS OS-principal separation for F-01 Slice 4A.

This module establishes and verifies identities and private host resources only.
It deliberately accepts no protected-repository path and installs no ACL.  The
Broker account is therefore only the future protected-write principal; Slice 4A
does not make it the sole writer of any repository.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import stat
import subprocess
import sys
import time
from typing import Any, Iterable, Mapping, Sequence
import uuid


PRINCIPAL_SEPARATION_SCHEMA = "decision-os-f01-principal-separation-v0.1"
PRINCIPAL_VERIFICATION_SCHEMA = (
    "decision-os-f01-principal-separation-verification-v0.1"
)
PRIVILEGED_INTERACTION_BUDGET = 1

STATE_ROOT = Path(
    "/Library/Application Support/DecisionOS/F01PrincipalSeparation/v1"
)
RECEIPT_PATH = STATE_ROOT / "identity-receipt.json"
KEYS_DIRECTORY = STATE_ROOT / "keys"
CONTROLLER_KEY_DIRECTORY = KEYS_DIRECTORY / "controller"
BROKER_KEY_DIRECTORY = KEYS_DIRECTORY / "broker"
CONTROLLER_KEY_PATH = CONTROLLER_KEY_DIRECTORY / "envelope-authentication.key"
BROKER_KEY_PATH = BROKER_KEY_DIRECTORY / "envelope-authentication.key"
BROKER_RUNTIME_DIRECTORY = STATE_ROOT / "broker-runtime"

AUTHENTICATION_KEY_BYTES = 32
AUTHENTICATION_KEY_VERSION = 1
DISABLED_SHELL = "/usr/bin/false"
EMPTY_HOME = "/var/empty"
ADMIN_GID = 80
WHEEL_GID = 0

DSCL = "/usr/bin/dscl"
ID = "/usr/bin/id"
PWPOLICY = "/usr/bin/pwpolicy"
PYTHON = "/usr/bin/python3"
SUDO = "/usr/bin/sudo"
TEST = "/bin/test"
TOUCH = "/usr/bin/touch"


class PrincipalSeparationError(RuntimeError):
    """The intended OS authority separation could not be proven."""


@dataclass(frozen=True)
class PrincipalSpec:
    role: str
    account_name: str
    unique_id: int
    private_group_name: str
    private_group_id: int
    real_name: str


PRINCIPAL_SPECS = (
    PrincipalSpec(
        role="codex",
        account_name="_decisionos_codex",
        unique_id=510,
        private_group_name="_decisionos_codex",
        private_group_id=510,
        real_name="Decision OS Codex execution principal",
    ),
    PrincipalSpec(
        role="controller",
        account_name="_decisionos_guardian",
        unique_id=511,
        private_group_name="_decisionos_guardian",
        private_group_id=511,
        real_name="Decision OS Controller Guardian principal",
    ),
    PrincipalSpec(
        role="broker",
        account_name="_decisionos_broker",
        unique_id=512,
        private_group_name="_decisionos_broker",
        private_group_id=512,
        real_name="Decision OS Broker write principal",
    ),
)
SPEC_BY_ROLE = {spec.role: spec for spec in PRINCIPAL_SPECS}


_ROLE_RECEIPT_FIELDS = frozenset(
    {
        "account_name",
        "unique_id",
        "generated_uid",
        "private_group_name",
        "private_group_id",
        "private_group_generated_uid",
    }
)
_RECEIPT_FIELDS = frozenset(
    {
        "schema",
        "installation_id",
        "created_at_unix",
        "state_root",
        "roles",
        "authentication_key_id",
        "authentication_key_version",
        "authentication_key_bytes",
        "authentication_key_sha256",
        "controller_key_path",
        "broker_key_path",
        "broker_runtime_directory",
    }
)


def _plain_uuid(value: Any, label: str) -> str:
    if type(value) is not str:
        raise PrincipalSeparationError(f"{label} is invalid.")
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as exc:
        raise PrincipalSeparationError(f"{label} is invalid.") from exc
    canonical = str(parsed).upper()
    if value.upper() != canonical:
        raise PrincipalSeparationError(f"{label} is not canonical.")
    return canonical


def _sha256_hex(value: Any, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise PrincipalSeparationError(f"{label} is invalid.")
    return value


@dataclass(frozen=True)
class RoleReceipt:
    account_name: str
    unique_id: int
    generated_uid: str
    private_group_name: str
    private_group_id: int
    private_group_generated_uid: str

    @classmethod
    def from_dict(cls, role: str, value: Any) -> "RoleReceipt":
        spec = SPEC_BY_ROLE.get(role)
        if spec is None or type(value) is not dict or set(value) != _ROLE_RECEIPT_FIELDS:
            raise PrincipalSeparationError("Principal receipt role fields are invalid.")
        if (
            value["account_name"] != spec.account_name
            or value["unique_id"] != spec.unique_id
            or value["private_group_name"] != spec.private_group_name
            or value["private_group_id"] != spec.private_group_id
        ):
            raise PrincipalSeparationError(
                f"The {role} receipt does not name the fixed Slice 4A identity."
            )
        return cls(
            account_name=spec.account_name,
            unique_id=spec.unique_id,
            generated_uid=_plain_uuid(
                value["generated_uid"], f"{role} GeneratedUID"
            ),
            private_group_name=spec.private_group_name,
            private_group_id=spec.private_group_id,
            private_group_generated_uid=_plain_uuid(
                value["private_group_generated_uid"],
                f"{role} private-group GeneratedUID",
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "account_name": self.account_name,
            "unique_id": self.unique_id,
            "generated_uid": self.generated_uid,
            "private_group_name": self.private_group_name,
            "private_group_id": self.private_group_id,
            "private_group_generated_uid": self.private_group_generated_uid,
        }


@dataclass(frozen=True)
class PrincipalReceipt:
    installation_id: str
    created_at_unix: int
    roles: Mapping[str, RoleReceipt]
    authentication_key_id: str
    authentication_key_sha256: str

    @classmethod
    def from_dict(cls, value: Any) -> "PrincipalReceipt":
        if type(value) is not dict or set(value) != _RECEIPT_FIELDS:
            raise PrincipalSeparationError("Principal receipt fields are invalid.")
        if value["schema"] != PRINCIPAL_SEPARATION_SCHEMA:
            raise PrincipalSeparationError("Principal receipt schema is invalid.")
        if (
            type(value["created_at_unix"]) is not int
            or value["created_at_unix"] < 0
        ):
            raise PrincipalSeparationError("Principal receipt time is invalid.")
        if value["state_root"] != str(STATE_ROOT):
            raise PrincipalSeparationError("Principal receipt state root is invalid.")
        if type(value["roles"]) is not dict or set(value["roles"]) != set(
            SPEC_BY_ROLE
        ):
            raise PrincipalSeparationError("Principal receipt roles are invalid.")
        if (
            value["authentication_key_version"] != AUTHENTICATION_KEY_VERSION
            or value["authentication_key_bytes"] != AUTHENTICATION_KEY_BYTES
            or value["controller_key_path"] != str(CONTROLLER_KEY_PATH)
            or value["broker_key_path"] != str(BROKER_KEY_PATH)
            or value["broker_runtime_directory"]
            != str(BROKER_RUNTIME_DIRECTORY)
        ):
            raise PrincipalSeparationError(
                "Principal receipt resource bindings are invalid."
            )
        installation_id = _plain_uuid(
            value["installation_id"], "Installation identity"
        )
        expected_key_id = f"decision-os-f01-envelope-hmac:{installation_id}"
        if value["authentication_key_id"] != expected_key_id:
            raise PrincipalSeparationError(
                "Principal receipt authentication-key identity is invalid."
            )
        roles = {
            role: RoleReceipt.from_dict(role, role_value)
            for role, role_value in value["roles"].items()
        }
        user_guids = {record.generated_uid for record in roles.values()}
        group_guids = {
            record.private_group_generated_uid for record in roles.values()
        }
        if (
            len(user_guids) != len(roles)
            or len(group_guids) != len(roles)
            or user_guids & group_guids
        ):
            raise PrincipalSeparationError(
                "Principal and private-group identities must all be distinct."
            )
        return cls(
            installation_id=installation_id,
            created_at_unix=value["created_at_unix"],
            roles=roles,
            authentication_key_id=expected_key_id,
            authentication_key_sha256=_sha256_hex(
                value["authentication_key_sha256"],
                "Authentication-key hash",
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": PRINCIPAL_SEPARATION_SCHEMA,
            "installation_id": self.installation_id,
            "created_at_unix": self.created_at_unix,
            "state_root": str(STATE_ROOT),
            "roles": {
                role: self.roles[role].as_dict() for role in sorted(self.roles)
            },
            "authentication_key_id": self.authentication_key_id,
            "authentication_key_version": AUTHENTICATION_KEY_VERSION,
            "authentication_key_bytes": AUTHENTICATION_KEY_BYTES,
            "authentication_key_sha256": self.authentication_key_sha256,
            "controller_key_path": str(CONTROLLER_KEY_PATH),
            "broker_key_path": str(BROKER_KEY_PATH),
            "broker_runtime_directory": str(BROKER_RUNTIME_DIRECTORY),
        }


def canonical_receipt_bytes(receipt: PrincipalReceipt) -> bytes:
    if type(receipt) is not PrincipalReceipt:
        raise PrincipalSeparationError("An exact principal receipt is required.")
    return (
        json.dumps(receipt.as_dict(), sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


@dataclass(frozen=True)
class PrincipalObservation:
    account_name: str
    unique_id: int
    generated_uid: str
    primary_group_id: int
    private_group_name: str
    private_group_generated_uid: str
    private_group_members: tuple[str, ...]
    private_group_member_guids: tuple[str, ...]
    home: str
    shell: str
    is_hidden: str
    authentication_allowed: bool
    effective_group_ids: tuple[int, ...]
    sudo_root_allowed: bool
    sudo_broker_allowed: bool


@dataclass(frozen=True)
class ResourceObservation:
    path: str
    kind: str
    owner_uid: int
    group_gid: int
    mode: int
    device: int
    inode: int
    link_count: int


@dataclass(frozen=True)
class AdversarialObservation:
    codex_reads_controller_key: bool
    codex_reads_broker_key: bool
    controller_reads_controller_key: bool
    controller_reads_broker_key: bool
    broker_reads_controller_key: bool
    broker_reads_broker_key: bool
    codex_writes_broker_runtime: bool
    controller_writes_broker_runtime: bool
    broker_writes_broker_runtime: bool
    codex_impersonates_broker: bool
    controller_impersonates_broker: bool


@dataclass(frozen=True)
class HostObservation:
    platform: str
    verifier_euid: int
    receipt_sha256: str
    principals: Mapping[str, PrincipalObservation]
    resources: Mapping[str, ResourceObservation]
    controller_key_sha256: str
    broker_key_sha256: str
    adversarial: AdversarialObservation


@dataclass(frozen=True)
class VerificationCheck:
    code: str
    passed: bool

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "passed": self.passed}


@dataclass(frozen=True)
class PrincipalVerificationReport:
    checks: tuple[VerificationCheck, ...]
    receipt_sha256: str
    principal_identity_sha256: Mapping[str, str]
    effective_group_ids: Mapping[str, tuple[int, ...]]

    @property
    def passed(self) -> bool:
        return bool(self.checks) and all(check.passed for check in self.checks)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": PRINCIPAL_VERIFICATION_SCHEMA,
            "passed": self.passed,
            "checks": [check.as_dict() for check in self.checks],
            "receipt_sha256": self.receipt_sha256,
            "principal_identity_sha256": dict(
                sorted(self.principal_identity_sha256.items())
            ),
            "effective_group_ids": {
                role: list(groups)
                for role, groups in sorted(self.effective_group_ids.items())
            },
            "protected_repository_acl_installed": False,
            "sole_writer_claimed": False,
            "privileged_interaction_budget": PRIVILEGED_INTERACTION_BUDGET,
        }


def _identity_hash(observed: PrincipalObservation) -> str:
    payload = {
        "account_name": observed.account_name,
        "unique_id": observed.unique_id,
        "generated_uid": observed.generated_uid,
        "primary_group_id": observed.primary_group_id,
        "private_group_name": observed.private_group_name,
        "private_group_generated_uid": observed.private_group_generated_uid,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def evaluate_principal_separation(
    receipt: PrincipalReceipt,
    observation: HostObservation,
) -> PrincipalVerificationReport:
    """Evaluate a complete observation; every missing proof becomes failure."""

    if type(receipt) is not PrincipalReceipt or type(observation) is not HostObservation:
        raise PrincipalSeparationError(
            "Exact receipt and host observation objects are required."
        )
    checks: list[VerificationCheck] = []

    def check(code: str, condition: bool) -> None:
        checks.append(VerificationCheck(code=code, passed=condition is True))

    check("darwin_host", observation.platform == "Darwin")
    check("root_verifier", observation.verifier_euid == 0)
    check(
        "complete_role_observation",
        set(observation.principals) == set(SPEC_BY_ROLE),
    )

    role_identity_hashes: dict[str, str] = {}
    effective_groups: dict[str, tuple[int, ...]] = {}
    for role, spec in SPEC_BY_ROLE.items():
        observed = observation.principals.get(role)
        expected = receipt.roles.get(role)
        present = observed is not None and expected is not None
        check(f"{role}_identity_present", present)
        if not present:
            continue
        assert observed is not None and expected is not None
        role_identity_hashes[role] = _identity_hash(observed)
        effective_groups[role] = tuple(observed.effective_group_ids)
        check(
            f"{role}_identity_pinned",
            observed.account_name == expected.account_name
            and observed.unique_id == expected.unique_id
            and observed.generated_uid == expected.generated_uid
            and observed.primary_group_id == expected.private_group_id
            and observed.private_group_name == expected.private_group_name
            and observed.private_group_generated_uid
            == expected.private_group_generated_uid,
        )
        check(
            f"{role}_login_disabled",
            observed.home == EMPTY_HOME
            and observed.shell == DISABLED_SHELL
            and observed.is_hidden in {"1", "YES"}
            and not observed.authentication_allowed,
        )
        check(
            f"{role}_private_group_exclusive",
            observed.private_group_members in {(), (spec.account_name,)}
            and observed.private_group_member_guids
            in {(), (expected.generated_uid,)}
            and spec.private_group_id in observed.effective_group_ids,
        )
        check(
            f"{role}_not_admin_or_wheel",
            ADMIN_GID not in observed.effective_group_ids
            and WHEEL_GID not in observed.effective_group_ids,
        )
        check(f"{role}_cannot_sudo_root", not observed.sudo_root_allowed)
        if role != "broker":
            check(
                f"{role}_cannot_sudo_broker",
                not observed.sudo_broker_allowed,
            )

    observed_principals = list(observation.principals.values())
    check(
        "principal_names_distinct",
        len({value.account_name for value in observed_principals})
        == len(PRINCIPAL_SPECS),
    )
    check(
        "principal_uids_distinct",
        len({value.unique_id for value in observed_principals})
        == len(PRINCIPAL_SPECS),
    )
    check(
        "principal_guids_distinct",
        len({value.generated_uid for value in observed_principals})
        == len(PRINCIPAL_SPECS),
    )

    private_gids = {spec.private_group_id for spec in PRINCIPAL_SPECS}
    shared_private_gid = False
    for left_index, left in enumerate(observed_principals):
        for right in observed_principals[left_index + 1 :]:
            if set(left.effective_group_ids) & set(right.effective_group_ids) & private_gids:
                shared_private_gid = True
    check("no_shared_private_authority_group", not shared_private_gid)

    expected_resources = {
        "state_root": (STATE_ROOT, "directory", 0, 0, 0o755),
        "receipt": (RECEIPT_PATH, "regular", 0, 0, 0o444),
        "keys": (KEYS_DIRECTORY, "directory", 0, 0, 0o711),
        "controller_key_directory": (
            CONTROLLER_KEY_DIRECTORY,
            "directory",
            0,
            SPEC_BY_ROLE["controller"].private_group_id,
            0o750,
        ),
        "broker_key_directory": (
            BROKER_KEY_DIRECTORY,
            "directory",
            0,
            SPEC_BY_ROLE["broker"].private_group_id,
            0o750,
        ),
        "controller_key": (
            CONTROLLER_KEY_PATH,
            "regular",
            0,
            SPEC_BY_ROLE["controller"].private_group_id,
            0o440,
        ),
        "broker_key": (
            BROKER_KEY_PATH,
            "regular",
            0,
            SPEC_BY_ROLE["broker"].private_group_id,
            0o440,
        ),
        "broker_runtime": (
            BROKER_RUNTIME_DIRECTORY,
            "directory",
            0,
            SPEC_BY_ROLE["broker"].private_group_id,
            0o770,
        ),
    }
    check(
        "complete_resource_observation",
        set(observation.resources) == set(expected_resources),
    )
    for name, (path, kind, uid, gid, mode) in expected_resources.items():
        resource = observation.resources.get(name)
        check(
            f"{name}_ownership_and_mode",
            resource is not None
            and resource.path == str(path)
            and resource.kind == kind
            and resource.owner_uid == uid
            and resource.group_gid == gid
            and resource.mode == mode
            and (
                (kind == "regular" and resource.link_count == 1)
                or (kind == "directory" and resource.link_count >= 1)
            ),
        )

    receipt_resource = observation.resources.get("receipt")
    check(
        "stale_identity_receipt_root_pinned",
        receipt_resource is not None
        and receipt_resource.owner_uid == 0
        and receipt_resource.group_gid == 0
        and receipt_resource.mode == 0o444
        and observation.receipt_sha256
        == hashlib.sha256(canonical_receipt_bytes(receipt)).hexdigest(),
    )
    controller_key = observation.resources.get("controller_key")
    broker_key = observation.resources.get("broker_key")
    check(
        "trust_key_copies_not_linked",
        controller_key is not None
        and broker_key is not None
        and controller_key.link_count == 1
        and broker_key.link_count == 1
        and (controller_key.device, controller_key.inode)
        != (broker_key.device, broker_key.inode),
    )
    check(
        "trust_key_commitment_matches",
        observation.controller_key_sha256
        == receipt.authentication_key_sha256
        == observation.broker_key_sha256,
    )

    adversarial = observation.adversarial
    check(
        "codex_cannot_read_trust_material",
        not adversarial.codex_reads_controller_key
        and not adversarial.codex_reads_broker_key,
    )
    check(
        "controller_has_approval_not_broker_trust_access",
        adversarial.controller_reads_controller_key
        and not adversarial.controller_reads_broker_key,
    )
    check(
        "broker_has_broker_trust_not_controller_copy",
        adversarial.broker_reads_broker_key
        and not adversarial.broker_reads_controller_key,
    )
    check(
        "controller_approval_does_not_imply_broker_write",
        not adversarial.controller_writes_broker_runtime,
    )
    check(
        "codex_has_no_broker_write",
        not adversarial.codex_writes_broker_runtime,
    )
    check(
        "broker_runtime_write_identity_works",
        adversarial.broker_writes_broker_runtime,
    )
    check(
        "codex_cannot_impersonate_broker",
        not adversarial.codex_impersonates_broker,
    )
    check(
        "controller_cannot_impersonate_broker",
        not adversarial.controller_impersonates_broker,
    )

    return PrincipalVerificationReport(
        checks=tuple(checks),
        receipt_sha256=observation.receipt_sha256,
        principal_identity_sha256=role_identity_hashes,
        effective_group_ids=effective_groups,
    )


def _run(
    arguments: Sequence[str],
    *,
    input_bytes: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    if not arguments or any(type(value) is not str for value in arguments):
        raise PrincipalSeparationError("Host command arguments are invalid.")
    try:
        return subprocess.run(
            list(arguments),
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        command = Path(arguments[0]).name
        raise PrincipalSeparationError(
            f"Required host command {command} could not be proved."
        ) from exc


def _checked(arguments: Sequence[str]) -> bytes:
    completed = _run(arguments)
    if completed.returncode != 0:
        command = Path(arguments[0]).name if arguments else "unknown"
        rendered = json.dumps(list(arguments), separators=(",", ":"))
        try:
            diagnostic = completed.stderr.decode("utf-8").strip()
        except UnicodeError:
            diagnostic = "non-UTF-8 diagnostic"
        suffix = f": {diagnostic[:512]}" if diagnostic else ""
        raise PrincipalSeparationError(
            f"Required host command {command} {rendered} failed closed "
            f"(exit {completed.returncode}){suffix}."
        )
    return completed.stdout


def _parse_dscl_record(output: bytes) -> dict[str, tuple[str, ...]]:
    try:
        text = output.decode("utf-8")
    except UnicodeError as exc:
        raise PrincipalSeparationError(
            "Directory-service output is not valid UTF-8."
        ) from exc
    values: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in text.splitlines():
        if not raw_line or raw_line.startswith("No such key:"):
            current = None
            continue
        if not raw_line[0].isspace() and ":" in raw_line:
            if raw_line.endswith(":"):
                key = raw_line[:-1]
                raw_value = ""
            elif ": " in raw_line:
                key, raw_value = raw_line.rsplit(": ", 1)
            else:
                raise PrincipalSeparationError(
                    "Directory-service record output is ambiguous."
                )
            if key.startswith("dsAttrTypeNative:"):
                key = key.removeprefix("dsAttrTypeNative:")
            if key in values:
                raise PrincipalSeparationError(
                    "Directory-service record contains duplicate attributes."
                )
            current = key
            values[current] = raw_value.strip().split()
        elif current is not None:
            values[current].extend(raw_line.strip().split())
    return {key: tuple(items) for key, items in values.items()}


def _one(record: Mapping[str, tuple[str, ...]], key: str) -> str:
    value = record.get(key)
    if value is None or len(value) != 1:
        raise PrincipalSeparationError(
            f"Directory-service attribute {key} is absent or ambiguous."
        )
    return value[0]


def _read_record(record_path: str) -> dict[str, tuple[str, ...]]:
    return _parse_dscl_record(_checked((DSCL, ".", "-read", record_path)))


def _record_exists(record_path: str) -> bool:
    completed = _run((DSCL, ".", "-read", record_path, "RecordName"))
    if completed.returncode == 0:
        return True
    try:
        diagnostic = (completed.stderr + completed.stdout).decode("utf-8")
    except UnicodeError as exc:
        raise PrincipalSeparationError(
            "Directory-service absence result is not valid UTF-8."
        ) from exc
    if completed.returncode == 56 and "eDSRecordNotFound" in diagnostic:
        return False
    raise PrincipalSeparationError(
        f"Directory-service record presence cannot be proved "
        f"(exit {completed.returncode})."
    )


def _numeric_id_in_use(record_root: str, attribute: str, value: int) -> bool:
    completed = _run(
        (DSCL, ".", "-search", record_root, attribute, str(value))
    )
    if completed.returncode != 0:
        raise PrincipalSeparationError(
            "Directory-service numeric identity search failed closed."
        )
    return bool(completed.stdout.strip())


def _require_darwin_root() -> None:
    if platform.system() != "Darwin":
        raise PrincipalSeparationError("Slice 4A host operations require macOS.")
    if os.geteuid() != 0:
        raise PrincipalSeparationError(
            "Slice 4A provision/verify requires an explicit root execution gate."
        )
    for executable in (
        DSCL,
        ID,
        PWPOLICY,
        PYTHON,
        SUDO,
        TEST,
        TOUCH,
        DISABLED_SHELL,
    ):
        try:
            status = Path(executable).lstat()
        except OSError as exc:
            raise PrincipalSeparationError(
                f"Required macOS executable is unavailable: {executable}"
            ) from exc
        if (
            not stat.S_ISREG(status.st_mode)
            or status.st_uid != 0
            or stat.S_IMODE(status.st_mode) & 0o022
            or not os.access(executable, os.X_OK)
        ):
            raise PrincipalSeparationError(
                f"Required macOS executable identity is unsafe: {executable}"
            )


def _create_directory(path: Path, mode: int, gid: int) -> None:
    path.mkdir(mode=mode)
    os.chown(path, 0, gid, follow_symlinks=False)
    os.chmod(path, mode, follow_symlinks=False)


def _write_new_file(path: Path, content: bytes, mode: int, gid: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, mode)
    try:
        os.fchown(descriptor, 0, gid)
        os.fchmod(descriptor, mode)
        view = memoryview(content)
        written = 0
        while written < len(view):
            count = os.write(descriptor, view[written:])
            if count <= 0:
                raise PrincipalSeparationError("Secure host file write stalled.")
            written += count
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _read_selected_record(
    record_path: str,
    keys: Sequence[str],
) -> dict[str, tuple[str, ...]] | None:
    completed = _run((DSCL, ".", "-read", record_path, *keys))
    if completed.returncode == 0:
        return _parse_dscl_record(completed.stdout)
    try:
        diagnostic = (completed.stderr + completed.stdout).decode("utf-8")
    except UnicodeError as exc:
        raise PrincipalSeparationError(
            "Directory-service readback is not valid UTF-8."
        ) from exc
    if completed.returncode == 56 and "eDSRecordNotFound" in diagnostic:
        return None
    raise PrincipalSeparationError(
        f"Directory-service readback failed closed "
        f"(exit {completed.returncode})."
    )


def _wait_record_values(
    record_path: str,
    expected: Mapping[str, tuple[str, ...]],
) -> None:
    keys = tuple(expected)
    for attempt in range(20):
        observed = _read_selected_record(record_path, keys)
        if observed is not None and all(
            observed.get(key) == value for key, value in expected.items()
        ):
            return
        if attempt != 19:
            time.sleep(0.1)
    raise PrincipalSeparationError(
        f"Directory-service mutation for {record_path} was not read back; "
        "HOLD without retry."
    )


def _set_record_attribute(
    record_path: str,
    attribute: str,
    value: str,
) -> None:
    # A mutation is issued exactly once. Only read-only visibility checks poll.
    _checked((DSCL, ".", "-create", record_path, attribute, value))
    _wait_record_values(record_path, {attribute: tuple(value.split())})


def _authentication_allowed(account_name: str) -> bool:
    completed = _run((PWPOLICY, "-u", account_name, "authentication-allowed"))
    try:
        diagnostic = (completed.stdout + completed.stderr).decode("utf-8").strip()
    except UnicodeError as exc:
        raise PrincipalSeparationError(
            "Password-policy result is not valid UTF-8."
        ) from exc
    if completed.returncode != 0:
        raise PrincipalSeparationError(
            f"Authentication policy for {account_name} cannot be proved "
            f"(exit {completed.returncode})."
        )
    allowed = f"Policy allows user <{account_name}> to authenticate"
    denied = f"User <{account_name}> is not allowed to authenticate"
    if allowed in diagnostic and denied not in diagnostic:
        return True
    if denied in diagnostic and allowed not in diagnostic:
        return False
    raise PrincipalSeparationError(
        f"Authentication policy for {account_name} cannot be proved "
        f"(exit {completed.returncode})."
    )


def _disable_authentication(account_name: str) -> None:
    # pwpolicy(8): `disableuser` disables authentication for one user. The
    # command is never retried; only the policy readback is polled.
    _checked((PWPOLICY, "-u", account_name, "disableuser"))
    for attempt in range(20):
        if not _authentication_allowed(account_name):
            return
        if attempt != 19:
            time.sleep(0.1)
    raise PrincipalSeparationError(
        f"Authentication disablement for {account_name} was not observed; "
        "HOLD without retry."
    )


def _create_group(spec: PrincipalSpec, generated_uid: str) -> None:
    path = f"/Groups/{spec.private_group_name}"
    _checked((DSCL, ".", "-create", path))
    _wait_record_values(path, {"RecordName": (spec.private_group_name,)})
    _set_record_attribute(path, "RealName", spec.real_name)
    _set_record_attribute(
        path,
        "PrimaryGroupID",
        str(spec.private_group_id),
    )
    _set_record_attribute(path, "GeneratedUID", generated_uid)


def _create_user(spec: PrincipalSpec, generated_uid: str) -> None:
    path = f"/Users/{spec.account_name}"
    _checked((DSCL, ".", "-create", path))
    _wait_record_values(path, {"RecordName": (spec.account_name,)})
    attributes = (
        ("RealName", spec.real_name),
        ("UniqueID", str(spec.unique_id)),
        ("PrimaryGroupID", str(spec.private_group_id)),
        ("GeneratedUID", generated_uid),
        ("NFSHomeDirectory", EMPTY_HOME),
        ("UserShell", DISABLED_SHELL),
        ("IsHidden", "1"),
    )
    for attribute, value in attributes:
        _set_record_attribute(path, attribute, value)
    _disable_authentication(spec.account_name)


def _new_guid() -> str:
    return str(uuid.uuid4()).upper()


def _preflight_new_install() -> None:
    if STATE_ROOT.exists() or STATE_ROOT.is_symlink():
        raise PrincipalSeparationError(
            "Unreceipted Slice 4A host state already exists; refusing adoption."
        )
    for spec in PRINCIPAL_SPECS:
        if _record_exists(f"/Users/{spec.account_name}"):
            raise PrincipalSeparationError(
                f"Existing {spec.role} account cannot be adopted as fresh authority."
            )
        if _record_exists(f"/Groups/{spec.private_group_name}"):
            raise PrincipalSeparationError(
                f"Existing {spec.role} group cannot be adopted as fresh authority."
            )
        if _numeric_id_in_use("/Users", "UniqueID", spec.unique_id):
            raise PrincipalSeparationError(
                f"Fixed {spec.role} UID is already in use; refusing substitution."
            )
        if _numeric_id_in_use(
            "/Groups", "PrimaryGroupID", spec.private_group_id
        ):
            raise PrincipalSeparationError(
                f"Fixed {spec.role} GID is already in use; refusing substitution."
            )


def _ensure_root_parent(path: Path) -> None:
    missing: list[Path] = []
    cursor = path
    while not cursor.exists():
        missing.append(cursor)
        cursor = cursor.parent
    status = cursor.lstat()
    if (
        not stat.S_ISDIR(status.st_mode)
        or status.st_uid != 0
        or stat.S_IMODE(status.st_mode) & 0o022
    ):
        raise PrincipalSeparationError(
            "Existing host-state ancestor is not root-owned and non-writable."
        )
    for directory in reversed(missing):
        _create_directory(directory, 0o755, 0)


def provision_principal_separation() -> PrincipalVerificationReport:
    """Create the fixed three-principal host substrate, once, as root."""

    _require_darwin_root()
    if RECEIPT_PATH.is_file() and not RECEIPT_PATH.is_symlink():
        return verify_installed_principal_separation()
    _preflight_new_install()

    user_guids = {spec.role: _new_guid() for spec in PRINCIPAL_SPECS}
    group_guids = {spec.role: _new_guid() for spec in PRINCIPAL_SPECS}
    if len(set(user_guids.values()) | set(group_guids.values())) != 6:
        raise PrincipalSeparationError("Fresh principal GUID generation collided.")

    for spec in PRINCIPAL_SPECS:
        _create_group(spec, group_guids[spec.role])
        _create_user(spec, user_guids[spec.role])

    _ensure_root_parent(STATE_ROOT.parent)
    _create_directory(STATE_ROOT, 0o755, 0)
    _create_directory(KEYS_DIRECTORY, 0o711, 0)
    _create_directory(
        CONTROLLER_KEY_DIRECTORY,
        0o750,
        SPEC_BY_ROLE["controller"].private_group_id,
    )
    _create_directory(
        BROKER_KEY_DIRECTORY,
        0o750,
        SPEC_BY_ROLE["broker"].private_group_id,
    )
    _create_directory(
        BROKER_RUNTIME_DIRECTORY,
        0o770,
        SPEC_BY_ROLE["broker"].private_group_id,
    )

    authentication_secret = secrets.token_bytes(AUTHENTICATION_KEY_BYTES)
    authentication_sha256 = hashlib.sha256(authentication_secret).hexdigest()
    _write_new_file(
        CONTROLLER_KEY_PATH,
        authentication_secret,
        0o440,
        SPEC_BY_ROLE["controller"].private_group_id,
    )
    _write_new_file(
        BROKER_KEY_PATH,
        authentication_secret,
        0o440,
        SPEC_BY_ROLE["broker"].private_group_id,
    )
    del authentication_secret

    installation_id = _new_guid()
    receipt = PrincipalReceipt(
        installation_id=installation_id,
        created_at_unix=int(time.time()),
        roles={
            spec.role: RoleReceipt(
                account_name=spec.account_name,
                unique_id=spec.unique_id,
                generated_uid=user_guids[spec.role],
                private_group_name=spec.private_group_name,
                private_group_id=spec.private_group_id,
                private_group_generated_uid=group_guids[spec.role],
            )
            for spec in PRINCIPAL_SPECS
        },
        authentication_key_id=(
            f"decision-os-f01-envelope-hmac:{installation_id}"
        ),
        authentication_key_sha256=authentication_sha256,
    )
    receipt_bytes = canonical_receipt_bytes(receipt)
    _write_new_file(RECEIPT_PATH, receipt_bytes, 0o444, 0)
    for directory in (
        CONTROLLER_KEY_DIRECTORY,
        BROKER_KEY_DIRECTORY,
        KEYS_DIRECTORY,
        BROKER_RUNTIME_DIRECTORY,
        STATE_ROOT,
    ):
        _fsync_directory(directory)
    return verify_installed_principal_separation()


def _read_regular_file(path: Path, *, maximum: int) -> tuple[bytes, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(
        os, "O_NOFOLLOW", 0
    )
    descriptor = os.open(path, flags)
    try:
        status = os.fstat(descriptor)
        if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
            raise PrincipalSeparationError(
                f"Host resource is not one unlinked regular file: {path}"
            )
        chunks: list[bytes] = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        if len(content) > maximum:
            raise PrincipalSeparationError(f"Host resource is oversized: {path}")
        after = os.fstat(descriptor)
        stable_before = (
            status.st_dev,
            status.st_ino,
            status.st_mode,
            status.st_nlink,
            status.st_uid,
            status.st_gid,
            status.st_size,
            status.st_mtime_ns,
            status.st_ctime_ns,
        )
        stable_after = (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_nlink,
            after.st_uid,
            after.st_gid,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if stable_after != stable_before:
            raise PrincipalSeparationError(f"Host resource changed while read: {path}")
        return content, status
    finally:
        os.close(descriptor)


def _load_receipt() -> tuple[PrincipalReceipt, bytes]:
    content, status = _read_regular_file(RECEIPT_PATH, maximum=64 * 1024)
    if status.st_uid != 0 or status.st_gid != 0 or stat.S_IMODE(status.st_mode) != 0o444:
        raise PrincipalSeparationError(
            "Principal receipt is not immutable to all runtime principals."
        )
    try:
        parsed = json.loads(content.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PrincipalSeparationError("Principal receipt is invalid JSON.") from exc
    receipt = PrincipalReceipt.from_dict(parsed)
    if content != canonical_receipt_bytes(receipt):
        raise PrincipalSeparationError("Principal receipt is not canonical.")
    return receipt, content


def _integer(value: str, label: str) -> int:
    try:
        parsed = int(value, 10)
    except (TypeError, ValueError) as exc:
        raise PrincipalSeparationError(f"{label} is not an integer.") from exc
    return parsed


def _nested_sudo_allowed(actor: str, target: str) -> bool:
    result = _run(
        (
            SUDO,
            "-n",
            "-u",
            actor,
            "--",
            SUDO,
            "-n",
            "-u",
            target,
            "--",
            ID,
            "-u",
        ),
        input_bytes=b"",
    )
    return result.returncode == 0


def _as_principal_test(account_name: str, flag: str, path: Path) -> bool:
    result = _run(
        (SUDO, "-n", "-u", account_name, "--", TEST, flag, str(path)),
        input_bytes=b"",
    )
    return result.returncode == 0


def _as_principal_write_probe(account_name: str, role: str) -> bool:
    name = f".{role}-{secrets.token_hex(12)}.principal-probe"
    path = BROKER_RUNTIME_DIRECTORY / name
    result = _run(
        (SUDO, "-n", "-u", account_name, "--", TOUCH, str(path)),
        input_bytes=b"",
    )
    succeeded = result.returncode == 0 and path.is_file() and not path.is_symlink()
    if path.exists() or path.is_symlink():
        status = path.lstat()
        if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
            raise PrincipalSeparationError(
                "Broker runtime probe produced an unexpected filesystem object."
            )
        path.unlink()
        _fsync_directory(BROKER_RUNTIME_DIRECTORY)
    return succeeded


def _resource(path: Path) -> ResourceObservation:
    status = path.lstat()
    if stat.S_ISREG(status.st_mode):
        kind = "regular"
    elif stat.S_ISDIR(status.st_mode):
        kind = "directory"
    else:
        kind = "other"
    return ResourceObservation(
        path=str(path),
        kind=kind,
        owner_uid=status.st_uid,
        group_gid=status.st_gid,
        mode=stat.S_IMODE(status.st_mode),
        device=status.st_dev,
        inode=status.st_ino,
        link_count=status.st_nlink,
    )


def _principal_observation(
    role: str,
    receipt: PrincipalReceipt,
) -> PrincipalObservation:
    spec = SPEC_BY_ROLE[role]
    user = _read_record(f"/Users/{spec.account_name}")
    group = _read_record(f"/Groups/{spec.private_group_name}")
    group_ids = tuple(
        _integer(value, f"{role} effective GID")
        for value in _checked((ID, "-G", spec.account_name)).decode("ascii").split()
    )
    broker_name = SPEC_BY_ROLE["broker"].account_name
    return PrincipalObservation(
        account_name=_one(user, "RecordName"),
        unique_id=_integer(_one(user, "UniqueID"), f"{role} UID"),
        generated_uid=_plain_uuid(_one(user, "GeneratedUID"), f"{role} GUID"),
        primary_group_id=_integer(
            _one(user, "PrimaryGroupID"), f"{role} primary GID"
        ),
        private_group_name=_one(group, "RecordName"),
        private_group_generated_uid=_plain_uuid(
            _one(group, "GeneratedUID"), f"{role} group GUID"
        ),
        private_group_members=tuple(group.get("GroupMembership", ())),
        private_group_member_guids=tuple(group.get("GroupMembers", ())),
        home=_one(user, "NFSHomeDirectory"),
        shell=_one(user, "UserShell"),
        is_hidden=_one(user, "IsHidden"),
        authentication_allowed=_authentication_allowed(spec.account_name),
        effective_group_ids=group_ids,
        sudo_root_allowed=_nested_sudo_allowed(spec.account_name, "root"),
        sudo_broker_allowed=(
            role == "broker"
            or _nested_sudo_allowed(spec.account_name, broker_name)
        ),
    )


def collect_host_observation(
    receipt: PrincipalReceipt,
    receipt_bytes: bytes,
) -> HostObservation:
    """Collect root-mediated negative probes without exposing key bytes."""

    _require_darwin_root()
    controller_key, _ = _read_regular_file(
        CONTROLLER_KEY_PATH, maximum=AUTHENTICATION_KEY_BYTES
    )
    broker_key, _ = _read_regular_file(
        BROKER_KEY_PATH, maximum=AUTHENTICATION_KEY_BYTES
    )
    if (
        len(controller_key) != AUTHENTICATION_KEY_BYTES
        or len(broker_key) != AUTHENTICATION_KEY_BYTES
    ):
        raise PrincipalSeparationError("Authentication-key length is invalid.")
    key_hashes = (
        hashlib.sha256(controller_key).hexdigest(),
        hashlib.sha256(broker_key).hexdigest(),
    )
    del controller_key
    del broker_key

    principals = {
        role: _principal_observation(role, receipt) for role in SPEC_BY_ROLE
    }
    resources = {
        "state_root": _resource(STATE_ROOT),
        "receipt": _resource(RECEIPT_PATH),
        "keys": _resource(KEYS_DIRECTORY),
        "controller_key_directory": _resource(CONTROLLER_KEY_DIRECTORY),
        "broker_key_directory": _resource(BROKER_KEY_DIRECTORY),
        "controller_key": _resource(CONTROLLER_KEY_PATH),
        "broker_key": _resource(BROKER_KEY_PATH),
        "broker_runtime": _resource(BROKER_RUNTIME_DIRECTORY),
    }
    codex = SPEC_BY_ROLE["codex"].account_name
    controller = SPEC_BY_ROLE["controller"].account_name
    broker = SPEC_BY_ROLE["broker"].account_name
    adversarial = AdversarialObservation(
        codex_reads_controller_key=_as_principal_test(
            codex, "-r", CONTROLLER_KEY_PATH
        ),
        codex_reads_broker_key=_as_principal_test(codex, "-r", BROKER_KEY_PATH),
        controller_reads_controller_key=_as_principal_test(
            controller, "-r", CONTROLLER_KEY_PATH
        ),
        controller_reads_broker_key=_as_principal_test(
            controller, "-r", BROKER_KEY_PATH
        ),
        broker_reads_controller_key=_as_principal_test(
            broker, "-r", CONTROLLER_KEY_PATH
        ),
        broker_reads_broker_key=_as_principal_test(
            broker, "-r", BROKER_KEY_PATH
        ),
        codex_writes_broker_runtime=_as_principal_write_probe(codex, "codex"),
        controller_writes_broker_runtime=_as_principal_write_probe(
            controller, "controller"
        ),
        broker_writes_broker_runtime=_as_principal_write_probe(broker, "broker"),
        codex_impersonates_broker=_nested_sudo_allowed(codex, broker),
        controller_impersonates_broker=_nested_sudo_allowed(controller, broker),
    )
    return HostObservation(
        platform=platform.system(),
        verifier_euid=os.geteuid(),
        receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
        principals=principals,
        resources=resources,
        controller_key_sha256=key_hashes[0],
        broker_key_sha256=key_hashes[1],
        adversarial=adversarial,
    )


def verify_installed_principal_separation() -> PrincipalVerificationReport:
    _require_darwin_root()
    receipt, receipt_bytes = _load_receipt()
    observation = collect_host_observation(receipt, receipt_bytes)
    report = evaluate_principal_separation(receipt, observation)
    if not report.passed:
        raise PrincipalSeparationError(
            "OS-principal separation verification failed closed."
        )
    return report


def principal_separation_plan() -> dict[str, Any]:
    """Return the exact bounded host mutation plan; never mutate host state."""

    return {
        "schema": PRINCIPAL_SEPARATION_SCHEMA,
        "operation": "plan-only",
        "gate": "HOLD",
        "privileged_interaction_budget": PRIVILEGED_INTERACTION_BUDGET,
        "authorization_retry_allowed": False,
        "mutation_retry_allowed": False,
        "state_root": str(STATE_ROOT),
        "executable_paths": [
            DSCL,
            ID,
            PWPOLICY,
            PYTHON,
            SUDO,
            TEST,
            TOUCH,
            DISABLED_SHELL,
        ],
        "entrypoint_interpreter": [PYTHON, "-I", "-S"],
        "directory_service_contract": {
            "datasource": ".",
            "record_write": [DSCL, ".", "-create"],
            "record_readback": [DSCL, ".", "-read"],
            "numeric_id_search": [DSCL, ".", "-search"],
            "authentication_disable": [
                PWPOLICY,
                "-u",
                "<account>",
                "disableuser",
            ],
            "authentication_readback": [
                PWPOLICY,
                "-u",
                "<account>",
                "authentication-allowed",
            ],
            "mutation_retry": "forbidden",
            "readback_visibility_poll": {
                "maximum_attempts": 20,
                "interval_seconds": 0.1,
            },
        },
        "principals": [
            {
                "role": spec.role,
                "account_name": spec.account_name,
                "unique_id": spec.unique_id,
                "private_group_name": spec.private_group_name,
                "private_group_id": spec.private_group_id,
                "login": "disabled",
            }
            for spec in PRINCIPAL_SPECS
        ],
        "resources": {
            "receipt": str(RECEIPT_PATH),
            "controller_key": str(CONTROLLER_KEY_PATH),
            "broker_key": str(BROKER_KEY_PATH),
            "broker_runtime": str(BROKER_RUNTIME_DIRECTORY),
        },
        "protected_repository_path_parameter": False,
        "protected_repository_acl_installed": False,
        "sole_writer_claimed": False,
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Provision or verify F-01 Slice 4A macOS principals."
    )
    parser.add_argument("operation", choices=("plan", "provision", "verify"))
    arguments = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if arguments.operation == "plan":
            result: dict[str, Any] = principal_separation_plan()
        else:
            report = (
                provision_principal_separation()
                if arguments.operation == "provision"
                else verify_installed_principal_separation()
            )
            result = report.as_dict()
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, PrincipalSeparationError) as exc:
        print(
            json.dumps(
                {
                    "schema": PRINCIPAL_VERIFICATION_SCHEMA,
                    "passed": False,
                    "gate": "HOLD",
                    "error": str(exc),
                    "privileged_interaction_budget": (
                        PRIVILEGED_INTERACTION_BUDGET
                    ),
                    "authorization_retry_allowed": False,
                    "protected_repository_acl_installed": False,
                    "sole_writer_claimed": False,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "AdversarialObservation",
    "BROKER_KEY_PATH",
    "BROKER_RUNTIME_DIRECTORY",
    "CONTROLLER_KEY_PATH",
    "HostObservation",
    "PRINCIPAL_SEPARATION_SCHEMA",
    "PRINCIPAL_SPECS",
    "PRINCIPAL_VERIFICATION_SCHEMA",
    "PRIVILEGED_INTERACTION_BUDGET",
    "PrincipalObservation",
    "PrincipalReceipt",
    "PrincipalSeparationError",
    "PrincipalVerificationReport",
    "RECEIPT_PATH",
    "ResourceObservation",
    "RoleReceipt",
    "STATE_ROOT",
    "canonical_receipt_bytes",
    "collect_host_observation",
    "evaluate_principal_separation",
    "main",
    "principal_separation_plan",
    "provision_principal_separation",
    "verify_installed_principal_separation",
]
