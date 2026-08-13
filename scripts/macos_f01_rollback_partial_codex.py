#!/usr/bin/env python3
"""Identity-bounded rollback for the accepted F-01 Slice 4A partial state.

This file is deliberately standalone so an independent reviewer can hash one
file and authorize exactly one rollback-only execution.  It never invokes an
authorization mechanism itself and contains no provisioning operation.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
import time
from typing import Callable, Mapping, Sequence


ROLLBACK_SCHEMA = "decision-os-f01-slice4a-partial-rollback-v0.1"
PRIVILEGED_INTERACTION_BUDGET = 1
CONFIRMATION = "rollback-only-observed-partial-codex-uid-gid-510"

DSCL = "/usr/bin/dscl"
STATE_ROOT = Path(
    "/Library/Application Support/DecisionOS/F01PrincipalSeparation/v1"
)
HOST_STATE_PATHS = (
    Path("/Library/Application Support/DecisionOS"),
    Path("/Library/Application Support/DecisionOS/F01PrincipalSeparation"),
    STATE_ROOT,
)
RECORD_NOT_FOUND_EXIT = (-(-14136)) % 256  # eDSRecordNotFound -> 56

EXPECTED_USER = {
    "RecordName": ("_decisionos_codex",),
    "UniqueID": ("510",),
    "GeneratedUID": ("D6515614-B56A-4943-AA41-18D17DE9F899",),
    "PrimaryGroupID": ("510",),
    "RealName": ("Decision", "OS", "Codex", "execution", "principal"),
}
EXPECTED_GROUP = {
    "RecordName": ("_decisionos_codex",),
    "PrimaryGroupID": ("510",),
    "GeneratedUID": ("1F200679-B0A2-4D13-A86F-6492F9C4B66F",),
    "RealName": ("Decision", "OS", "Codex", "execution", "principal"),
}
USER_PATH = "/Users/_decisionos_codex"
GROUP_PATH = "/Groups/_decisionos_codex"
HELD_USER_PATHS = (
    "/Users/_decisionos_guardian",
    "/Users/_decisionos_broker",
)
HELD_GROUP_PATHS = (
    "/Groups/_decisionos_guardian",
    "/Groups/_decisionos_broker",
)
USER_READ_KEYS = tuple(EXPECTED_USER) + (
    "NFSHomeDirectory",
    "UserShell",
    "IsHidden",
    "AuthenticationAuthority",
)
GROUP_READ_KEYS = tuple(EXPECTED_GROUP) + (
    "GroupMembership",
    "GroupMembers",
)
ROLLBACK_MUTATION_COMMANDS = (
    (DSCL, ".", "-delete", USER_PATH),
    (DSCL, ".", "-delete", GROUP_PATH),
)


def _identity_sha256() -> str:
    payload = {
        "user": {key: list(value) for key, value in EXPECTED_USER.items()},
        "group": {key: list(value) for key, value in EXPECTED_GROUP.items()},
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


EXPECTED_IDENTITY_SHA256 = _identity_sha256()


@dataclass(frozen=True)
class CommandResult:
    returncode: int
    stdout: bytes = b""
    stderr: bytes = b""


Runner = Callable[[Sequence[str]], CommandResult]


class RollbackError(RuntimeError):
    """The exact rollback could not be proved or completed."""

    def __init__(
        self,
        message: str,
        *,
        completed_mutations: Sequence[str] = (),
    ) -> None:
        super().__init__(message)
        self.completed_mutations = tuple(completed_mutations)


def _default_runner(arguments: Sequence[str]) -> CommandResult:
    if not arguments or any(type(value) is not str for value in arguments):
        raise RollbackError("Host command arguments are invalid.")
    try:
        completed = subprocess.run(
            list(arguments),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            shell=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RollbackError(
            f"Required host command {Path(arguments[0]).name} could not run."
        ) from exc
    return CommandResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _decode(value: bytes, label: str) -> str:
    try:
        return value.decode("utf-8")
    except UnicodeError as exc:
        raise RollbackError(f"{label} is not valid UTF-8.") from exc


def _parse_record(output: bytes) -> dict[str, tuple[str, ...]]:
    values: dict[str, list[str]] = {}
    current: str | None = None
    for raw_line in _decode(output, "Directory Service record output").splitlines():
        if not raw_line or raw_line.startswith("No such key:"):
            current = None
            continue
        if not raw_line[0].isspace() and ":" in raw_line:
            native_hidden_prefix = "dsAttrTypeNative:IsHidden:"
            if raw_line.startswith(native_hidden_prefix):
                key = "IsHidden"
                raw_value = raw_line[len(native_hidden_prefix) :]
            else:
                key, raw_value = raw_line.split(":", 1)
            if key in values:
                raise RollbackError("Directory Service record contains duplicate keys.")
            current = key
            values[key] = raw_value.strip().split()
        elif current is not None:
            values[current].extend(raw_line.strip().split())
        else:
            raise RollbackError("Directory Service record output is ambiguous.")
    return {key: tuple(value) for key, value in values.items()}


def _read_record(
    runner: Runner,
    record_path: str,
    keys: Sequence[str],
) -> dict[str, tuple[str, ...]]:
    result = runner((DSCL, ".", "-read", record_path, *keys))
    if result.returncode != 0:
        raise RollbackError(
            f"Required record {record_path} is unavailable "
            f"(exit {result.returncode})."
        )
    return _parse_record(result.stdout)


def _require_absent(runner: Runner, record_path: str) -> None:
    result = runner((DSCL, ".", "-read", record_path, "RecordName"))
    if result.returncode == 0:
        raise RollbackError(f"Held record unexpectedly exists: {record_path}")
    diagnostic = _decode(result.stderr + result.stdout, "Directory Service error")
    if (
        result.returncode != RECORD_NOT_FOUND_EXIT
        or "eDSRecordNotFound" not in diagnostic
    ):
        raise RollbackError(
            f"Absence of {record_path} cannot be proved "
            f"(exit {result.returncode})."
        )


def _search_names(
    runner: Runner,
    record_root: str,
    attribute: str,
    numeric_id: int,
) -> tuple[str, ...]:
    result = runner(
        (DSCL, ".", "-search", record_root, attribute, str(numeric_id))
    )
    if result.returncode != 0:
        raise RollbackError(
            f"Numeric identity search for {attribute}={numeric_id} failed "
            f"(exit {result.returncode})."
        )
    names: list[str] = []
    for raw_line in _decode(result.stdout, "Directory Service search output").splitlines():
        if (
            not raw_line.strip()
            or raw_line[0].isspace()
            or raw_line.strip() in {"(", ")"}
        ):
            continue
        parts = raw_line.split()
        if len(parts) < 3 or parts[1] != attribute or parts[2] != "=":
            raise RollbackError("Directory Service search output is ambiguous.")
        names.append(parts[0])
    return tuple(names)


def _require_mapping(
    observed: Mapping[str, tuple[str, ...]],
    expected: Mapping[str, tuple[str, ...]],
    label: str,
) -> None:
    for key, expected_value in expected.items():
        if observed.get(key) != expected_value:
            raise RollbackError(
                f"{label} identity mismatch at {key}; deletion refused."
            )


def _require_optional_shape(
    user: Mapping[str, tuple[str, ...]],
    group: Mapping[str, tuple[str, ...]],
) -> None:
    allowed_user_values = {
        "NFSHomeDirectory": ("/var/empty",),
        "UserShell": ("/usr/bin/false",),
        "IsHidden": ("1",),
    }
    for key, allowed in allowed_user_values.items():
        value = user.get(key)
        if value is not None and value != allowed:
            raise RollbackError(
                f"User attribute {key} differs from the Slice 4A shape."
            )
    authentication = user.get("AuthenticationAuthority")
    if authentication is not None and not any(
        "DisabledUser" in value for value in authentication
    ):
        raise RollbackError(
            "Unexpected authentication authority is attached to the target user."
        )
    allowed_names = ("_decisionos_codex",)
    allowed_guids = (EXPECTED_USER["GeneratedUID"][0],)
    if group.get("GroupMembership") not in {None, allowed_names}:
        raise RollbackError("Private group has an unrelated named member.")
    if group.get("GroupMembers") not in {None, allowed_guids}:
        raise RollbackError("Private group has an unrelated GUID member.")


def _require_held_surfaces_absent(
    runner: Runner,
    lexists: Callable[[str], bool],
) -> None:
    if any(lexists(str(path)) for path in HOST_STATE_PATHS):
        raise RollbackError(
            "DecisionOS host state exists; partial-state rollback is no longer valid."
        )
    for path in (*HELD_USER_PATHS, *HELD_GROUP_PATHS):
        _require_absent(runner, path)


def _require_exact_partial_state(
    runner: Runner,
    lexists: Callable[[str], bool],
) -> None:
    _require_held_surfaces_absent(runner, lexists)
    user = _read_record(runner, USER_PATH, USER_READ_KEYS)
    group = _read_record(runner, GROUP_PATH, GROUP_READ_KEYS)
    _require_mapping(user, EXPECTED_USER, "User")
    _require_mapping(group, EXPECTED_GROUP, "Group")
    _require_optional_shape(user, group)
    if _search_names(runner, "/Users", "UniqueID", 510) != (
        "_decisionos_codex",
    ):
        raise RollbackError("UID 510 is not uniquely bound to the target user.")
    if _search_names(runner, "/Groups", "PrimaryGroupID", 510) != (
        "_decisionos_codex",
    ):
        raise RollbackError("GID 510 is not uniquely bound to the target group.")


def _require_user_still_bound(runner: Runner) -> None:
    """Rebind the user immediately before the name-addressed deletion."""

    user = _read_record(runner, USER_PATH, USER_READ_KEYS)
    _require_mapping(user, EXPECTED_USER, "User")
    _require_optional_shape(user, {})
    if _search_names(runner, "/Users", "UniqueID", 510) != (
        "_decisionos_codex",
    ):
        raise RollbackError("UID 510 changed before user deletion.")


def _wait_absent(
    runner: Runner,
    record_path: str,
    *,
    sleep: Callable[[float], None],
) -> None:
    for attempt in range(20):
        result = runner((DSCL, ".", "-read", record_path, "RecordName"))
        diagnostic = _decode(
            result.stderr + result.stdout, "Directory Service deletion readback"
        )
        if (
            result.returncode == RECORD_NOT_FOUND_EXIT
            and "eDSRecordNotFound" in diagnostic
        ):
            return
        if result.returncode not in {0, RECORD_NOT_FOUND_EXIT}:
            raise RollbackError(
                f"Deletion readback for {record_path} failed "
                f"(exit {result.returncode})."
            )
        if attempt != 19:
            sleep(0.1)
    raise RollbackError(f"Deletion of {record_path} did not become observable.")


def _wait_numeric_free(
    runner: Runner,
    record_root: str,
    attribute: str,
    numeric_id: int,
    *,
    label: str,
    sleep: Callable[[float], None],
) -> None:
    for attempt in range(20):
        if not _search_names(runner, record_root, attribute, numeric_id):
            return
        if attempt != 19:
            sleep(0.1)
    raise RollbackError(f"{label} {numeric_id} remains allocated after deletion.")


def _mutate(
    runner: Runner,
    arguments: Sequence[str],
    completed: list[str],
    label: str,
) -> None:
    if tuple(arguments) not in ROLLBACK_MUTATION_COMMANDS:
        raise RollbackError("Rollback attempted an unapproved mutation command.")
    result = runner(tuple(arguments))
    if result.returncode != 0:
        raise RollbackError(
            f"{label} failed (exit {result.returncode}); HOLD without retry.",
            completed_mutations=completed,
        )
    completed.append(label)


def _require_tool(path: str) -> None:
    status = os.lstat(path)
    if (
        not stat.S_ISREG(status.st_mode)
        or status.st_uid != 0
        or stat.S_IMODE(status.st_mode) & 0o022
        or not os.access(path, os.X_OK)
    ):
        raise RollbackError(f"Rollback tool identity is unsafe: {path}")


def rollback_partial_codex(
    *,
    runner: Runner = _default_runner,
    lexists: Callable[[str], bool] = os.path.lexists,
    sleep: Callable[[float], None] = time.sleep,
    system: Callable[[], str] = platform.system,
    geteuid: Callable[[], int] = os.geteuid,
    require_tool: Callable[[str], None] = _require_tool,
) -> dict[str, object]:
    """Remove only the two exact observed partial records, or fail closed."""

    completed: list[str] = []
    if system() != "Darwin":
        raise RollbackError("Rollback requires macOS.")
    if geteuid() != 0:
        raise RollbackError("Rollback requires one explicit root authorization.")
    require_tool(DSCL)
    _require_exact_partial_state(runner, lexists)
    _require_user_still_bound(runner)
    _require_held_surfaces_absent(runner, lexists)

    _mutate(runner, ROLLBACK_MUTATION_COMMANDS[0], completed, "user_deleted")
    try:
        _wait_absent(runner, USER_PATH, sleep=sleep)
        _wait_numeric_free(
            runner,
            "/Users",
            "UniqueID",
            510,
            label="UID",
            sleep=sleep,
        )

        # Rebind the surviving group immediately before its own deletion.  A
        # name/GID/GUID swap between the two mutations must stop at HOLD.
        group = _read_record(runner, GROUP_PATH, GROUP_READ_KEYS)
        _require_mapping(group, EXPECTED_GROUP, "Group")
        _require_optional_shape({}, group)
        if _search_names(runner, "/Groups", "PrimaryGroupID", 510) != (
            "_decisionos_codex",
        ):
            raise RollbackError("GID 510 changed before group deletion.")
        _require_absent(runner, USER_PATH)
        _require_held_surfaces_absent(runner, lexists)

        _mutate(runner, ROLLBACK_MUTATION_COMMANDS[1], completed, "group_deleted")
        _wait_absent(runner, GROUP_PATH, sleep=sleep)
        _wait_numeric_free(
            runner,
            "/Groups",
            "PrimaryGroupID",
            510,
            label="GID",
            sleep=sleep,
        )
        _require_absent(runner, USER_PATH)
        _require_held_surfaces_absent(runner, lexists)
    except RollbackError as exc:
        if not exc.completed_mutations:
            exc.completed_mutations = tuple(completed)
        raise

    return {
        "schema": ROLLBACK_SCHEMA,
        "passed": True,
        "gate": "HOLD",
        "disposition": "ROLLBACK_COMPLETE_AWAITING_INDEPENDENT_REVIEW",
        "privileged_interaction_budget": PRIVILEGED_INTERACTION_BUDGET,
        "expected_identity_sha256": EXPECTED_IDENTITY_SHA256,
        "completed_mutations": list(completed),
        "removed_records": [USER_PATH, GROUP_PATH],
        "uid_510_free": True,
        "gid_510_free": True,
        "decisionos_host_state_absent": True,
        "protected_repository_acl_changed": False,
        "provisioning_performed": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rollback only the accepted F-01 Slice 4A partial identity."
    )
    parser.add_argument("operation", choices=("rollback",))
    parser.add_argument("--confirm", required=True, choices=(CONFIRMATION,))
    arguments = parser.parse_args(list(argv) if argv is not None else None)
    assert arguments.operation == "rollback"
    try:
        report = rollback_partial_codex()
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
        return 0
    except (OSError, RollbackError) as exc:
        completed = (
            list(exc.completed_mutations)
            if isinstance(exc, RollbackError)
            else []
        )
        print(
            json.dumps(
                {
                    "schema": ROLLBACK_SCHEMA,
                    "passed": False,
                    "gate": "HOLD",
                    "error": str(exc),
                    "completed_mutations": completed,
                    "privileged_interaction_budget": (
                        PRIVILEGED_INTERACTION_BUDGET
                    ),
                    "authorization_retry_allowed": False,
                    "protected_repository_acl_changed": False,
                    "provisioning_performed": False,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
