#!/usr/bin/env python3
"""One-shot identity wrapper for the reviewed F-01 OpenDirectory mutator.

The wrapper contains no rollback logic and no authorization mechanism. A
separately reviewed one-interaction launcher may execute this source as root.
It then authenticates fixed staged bytes, makes a root-private exact copy, and
directly launches that copy once without a shell or fallback.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import Callable, Mapping, Optional, Sequence


WRAPPER_SCHEMA = "decision-os-f01-slice4a-one-shot-wrapper-v0.1"
PRIVILEGED_INTERACTION_BUDGET = 1
AUTHORIZATION_RETRY_ALLOWED = False
EXPECTED_SUCCESS_STATUS = "ROLLBACK_COMPLETE_AWAITING_INDEPENDENT_REVIEW"
EXPECTED_COMPLETED_MUTATIONS = ("user_deleted", "group_deleted")
PRIVATE_EXECUTION_PARENT = "/private/tmp"
PRIVATE_EXECUTION_PREFIX = "decision-os-f01-verified-exec-"
PRIVATE_EXECUTABLE_NAME = "macos_f01_opendirectory_mutation"
MAX_CAPTURE_BYTES = 1024 * 1024
CHILD_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class ArtifactIdentity:
    directory: str
    filename: str
    directory_device: int
    directory_inode: int
    directory_uid: int
    directory_gid: int
    directory_mode: int
    binary_device: int
    binary_inode: int
    binary_uid: int
    binary_gid: int
    binary_mode: int
    binary_nlink: int
    binary_size: int
    binary_sha256: str
    required_euid: int
    required_egid: int


PRODUCTION_IDENTITY = ArtifactIdentity(
    directory=(
        "/private/tmp/decision-os-f01-slice4a-one-shot-0450739ae668"
    ),
    filename="macos_f01_opendirectory_mutation",
    directory_device=16777234,
    directory_inode=123725406,
    directory_uid=501,
    directory_gid=0,
    directory_mode=0o500,
    binary_device=16777234,
    binary_inode=123725407,
    binary_uid=501,
    binary_gid=0,
    binary_mode=0o555,
    binary_nlink=1,
    binary_size=94704,
    binary_sha256=(
        "0450739ae6680b148d4c38af6cc047502be6b1d32b37cc53fc0b153a6ffed802"
    ),
    required_euid=0,
    required_egid=0,
)


class WrapperError(RuntimeError):
    """A fail-closed wrapper condition."""

    def __init__(self, phase: str, message: str) -> None:
        super().__init__(message)
        self.phase = phase


@dataclass(frozen=True)
class ChildExecution:
    exit_code: Optional[int]
    stdout: bytes
    stderr: bytes
    launch_error: Optional[str] = None


@dataclass(frozen=True)
class TestHooks:
    after_artifact_open: Optional[Callable[[int, int], None]] = None
    before_private_exec: Optional[Callable[[str, int], None]] = None


Executor = Callable[[str], ChildExecution]


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _write_report(report: Mapping[str, object]) -> None:
    sys.stdout.buffer.write(_canonical_json_bytes(report))
    sys.stdout.buffer.flush()


def _base_report(status: str, phase: str, effective_uid: int) -> dict[str, object]:
    return {
        "authorization_invocations": 0,
        "authorization_retry_allowed": AUTHORIZATION_RETRY_ALLOWED,
        "completed_mutations": [],
        "effective_uid": effective_uid,
        "gate": "HOLD",
        "mutation_attempted_by_wrapper": False,
        "phase": phase,
        "privileged_interaction_budget": PRIVILEGED_INTERACTION_BUDGET,
        "privileged_prompt_count": 0,
        "protected_repository_acl_changed_by_wrapper": False,
        "provisioning_performed_by_wrapper": False,
        "schema": WRAPPER_SCHEMA,
        "status": status,
    }


def _hold_report(
    phase: str,
    message: str,
    effective_uid: int,
) -> dict[str, object]:
    report = _base_report("HOLD_WRAPPER_FAILURE", phase, effective_uid)
    report["error"] = message
    return report


def _mode(value: os.stat_result) -> int:
    return stat.S_IMODE(value.st_mode)


def _require_directory_metadata(
    observed: os.stat_result,
    identity: ArtifactIdentity,
) -> None:
    expected = (
        identity.directory_device,
        identity.directory_inode,
        identity.directory_uid,
        identity.directory_gid,
        identity.directory_mode,
    )
    actual = (
        observed.st_dev,
        observed.st_ino,
        observed.st_uid,
        observed.st_gid,
        _mode(observed),
    )
    if not stat.S_ISDIR(observed.st_mode) or actual != expected:
        raise WrapperError(
            "staged_directory_validation",
            "Staged directory identity or metadata mismatch.",
        )


def _require_binary_metadata(
    observed: os.stat_result,
    identity: ArtifactIdentity,
) -> None:
    expected = (
        identity.binary_device,
        identity.binary_inode,
        identity.binary_uid,
        identity.binary_gid,
        identity.binary_mode,
        identity.binary_nlink,
        identity.binary_size,
    )
    actual = (
        observed.st_dev,
        observed.st_ino,
        observed.st_uid,
        observed.st_gid,
        _mode(observed),
        observed.st_nlink,
        observed.st_size,
    )
    if not stat.S_ISREG(observed.st_mode) or actual != expected:
        raise WrapperError(
            "staged_binary_validation",
            "Staged binary identity or metadata mismatch.",
        )
    if observed.st_mode & (stat.S_IWGRP | stat.S_IWOTH):
        raise WrapperError(
            "staged_binary_validation",
            "Staged binary is writable by group or other.",
        )


def _require_same_inode(
    descriptor_status: os.stat_result,
    path_status: os.stat_result,
    phase: str,
) -> None:
    if not stat.S_ISREG(path_status.st_mode) or (
        descriptor_status.st_dev,
        descriptor_status.st_ino,
    ) != (path_status.st_dev, path_status.st_ino):
        raise WrapperError(phase, "Path no longer names the opened inode.")


def _hash_open_file(descriptor: int) -> tuple[str, int]:
    os.lseek(descriptor, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    total = 0
    while True:
        block = os.read(descriptor, 1024 * 1024)
        if not block:
            break
        digest.update(block)
        total += len(block)
    return digest.hexdigest(), total


def _open_and_authenticate(
    identity: ArtifactIdentity,
    hooks: TestHooks,
) -> tuple[int, int, os.stat_result]:
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    try:
        directory_fd = os.open(identity.directory, directory_flags)
    except OSError as exc:
        raise WrapperError(
            "staged_directory_open", f"Cannot open fixed staged directory: {exc}"
        ) from exc

    try:
        directory_status = os.fstat(directory_fd)
        _require_directory_metadata(directory_status, identity)
        directory_path_status = os.lstat(identity.directory)
        if (
            directory_status.st_dev,
            directory_status.st_ino,
        ) != (
            directory_path_status.st_dev,
            directory_path_status.st_ino,
        ):
            raise WrapperError(
                "staged_directory_validation",
                "Staged directory path no longer names the opened directory.",
            )

        binary_flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
        try:
            binary_fd = os.open(
                identity.filename,
                binary_flags,
                dir_fd=directory_fd,
            )
        except OSError as exc:
            raise WrapperError(
                "staged_binary_open", f"Cannot open fixed staged binary: {exc}"
            ) from exc

        try:
            binary_status = os.fstat(binary_fd)
            _require_binary_metadata(binary_status, identity)
            if hooks.after_artifact_open is not None:
                hooks.after_artifact_open(directory_fd, binary_fd)
            path_status = os.stat(
                identity.filename,
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
            _require_same_inode(
                binary_status,
                path_status,
                "staged_binary_post_open_binding",
            )
            digest, size = _hash_open_file(binary_fd)
            if digest != identity.binary_sha256 or size != identity.binary_size:
                raise WrapperError(
                    "staged_binary_hash",
                    "Opened staged binary size or SHA-256 mismatch.",
                )
            after_hash = os.fstat(binary_fd)
            _require_binary_metadata(after_hash, identity)
            return directory_fd, binary_fd, binary_status
        except BaseException:
            os.close(binary_fd)
            raise
    except BaseException:
        os.close(directory_fd)
        raise


def _copy_to_private_execution_path(
    source_fd: int,
    identity: ArtifactIdentity,
    effective_uid: int,
    effective_gid: int,
    private_parent: str,
) -> tuple[str, str, int, os.stat_result]:
    previous_umask = os.umask(0o077)
    try:
        execution_directory = tempfile.mkdtemp(
            prefix=PRIVATE_EXECUTION_PREFIX,
            dir=private_parent,
        )
    finally:
        os.umask(previous_umask)

    execution_path = os.path.join(
        execution_directory,
        PRIVATE_EXECUTABLE_NAME,
    )
    try:
        os.chmod(execution_directory, 0o700)
        directory_status = os.lstat(execution_directory)
        if (
            not stat.S_ISDIR(directory_status.st_mode)
            or directory_status.st_uid != effective_uid
            or directory_status.st_gid != effective_gid
            or _mode(directory_status) != 0o700
        ):
            raise WrapperError(
                "private_directory_validation",
                "Private execution directory metadata mismatch.",
            )

        destination_flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | os.O_CLOEXEC
        )
        destination_fd = os.open(execution_path, destination_flags, 0o500)
        try:
            os.lseek(source_fd, 0, os.SEEK_SET)
            digest = hashlib.sha256()
            total = 0
            while True:
                block = os.read(source_fd, 1024 * 1024)
                if not block:
                    break
                digest.update(block)
                total += len(block)
                view = memoryview(block)
                while view:
                    written = os.write(destination_fd, view)
                    if written <= 0:
                        raise WrapperError(
                            "private_copy",
                            "Private executable copy made no write progress.",
                        )
                    view = view[written:]
            os.fsync(destination_fd)
            os.fchmod(destination_fd, 0o500)
            copied_status = os.fstat(destination_fd)
            if (
                digest.hexdigest() != identity.binary_sha256
                or total != identity.binary_size
                or not stat.S_ISREG(copied_status.st_mode)
                or copied_status.st_uid != effective_uid
                or copied_status.st_gid != effective_gid
                or _mode(copied_status) != 0o500
                or copied_status.st_nlink != 1
                or copied_status.st_size != identity.binary_size
            ):
                raise WrapperError(
                    "private_copy_validation",
                    "Root-private executable copy identity mismatch.",
                )
        finally:
            os.close(destination_fd)

        execution_fd = os.open(
            execution_path,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
        )
        try:
            execution_status = os.fstat(execution_fd)
            digest, size = _hash_open_file(execution_fd)
            path_status = os.lstat(execution_path)
            _require_same_inode(
                execution_status,
                path_status,
                "private_copy_path_binding",
            )
            if (
                digest != identity.binary_sha256
                or size != identity.binary_size
                or execution_status.st_uid != effective_uid
                or execution_status.st_gid != effective_gid
                or _mode(execution_status) != 0o500
                or execution_status.st_nlink != 1
            ):
                raise WrapperError(
                    "private_copy_revalidation",
                    "Root-private executable failed final validation.",
                )
            return (
                execution_directory,
                execution_path,
                execution_fd,
                execution_status,
            )
        except BaseException:
            os.close(execution_fd)
            raise
    except BaseException:
        try:
            os.unlink(execution_path)
        except FileNotFoundError:
            pass
        try:
            os.rmdir(execution_directory)
        except FileNotFoundError:
            pass
        raise


def _execute_child(executable: str) -> ChildExecution:
    try:
        completed = subprocess.run(
            [executable],
            check=False,
            close_fds=True,
            cwd="/",
            env={},
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=CHILD_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return ChildExecution(
            exit_code=None,
            stdout=exc.stdout or b"",
            stderr=exc.stderr or b"",
            launch_error="Mutation child exceeded the fixed timeout.",
        )
    except OSError as exc:
        return ChildExecution(
            exit_code=None,
            stdout=b"",
            stderr=b"",
            launch_error=f"Mutation child could not launch: {exc}",
        )
    return ChildExecution(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _parse_exact_child_json(stdout: bytes) -> tuple[Optional[dict[str, object]], Optional[str]]:
    if len(stdout) > MAX_CAPTURE_BYTES:
        return None, "Child stdout exceeded the fixed capture bound."
    try:
        decoded = stdout.decode("utf-8")
    except UnicodeError:
        return None, "Child stdout is not valid UTF-8."
    try:
        value = json.loads(decoded)
    except (TypeError, ValueError):
        return None, "Child stdout is not one valid JSON value."
    if type(value) is not dict:
        return None, "Child JSON result is not an object."
    if _canonical_json_bytes(value) != stdout:
        return None, "Child JSON result is not exact canonical JSON."
    return value, None


def _child_report(
    child: ChildExecution,
    effective_uid: int,
) -> dict[str, object]:
    report = _base_report("HOLD_CHILD_RESULT", "child_result", effective_uid)
    report["child_exit_code"] = child.exit_code
    report["child_launch_error"] = child.launch_error
    report["child_stderr_base64"] = base64.b64encode(child.stderr).decode("ascii")
    report["child_stdout_base64"] = base64.b64encode(child.stdout).decode("ascii")

    if len(child.stderr) > MAX_CAPTURE_BYTES:
        report["error"] = "Child stderr exceeded the fixed capture bound."
        return report
    parsed, parse_error = _parse_exact_child_json(child.stdout)
    if parsed is not None:
        report["child_report"] = parsed
        completed = parsed.get("completed_mutations")
        if type(completed) is list and all(type(item) is str for item in completed):
            report["completed_mutations"] = completed
    if child.launch_error is not None:
        report["error"] = child.launch_error
        return report
    if parse_error is not None:
        report["error"] = parse_error
        return report
    assert parsed is not None
    if child.exit_code != 0:
        report["error"] = "Mutation child returned nonzero; HOLD without retry."
        return report
    if parsed.get("status") != EXPECTED_SUCCESS_STATUS:
        report["error"] = "Mutation child did not report the exact success status."
        return report
    if parsed.get("completed_mutations") != list(EXPECTED_COMPLETED_MUTATIONS):
        report["error"] = "Mutation child completion list is not exact."
        return report
    report["status"] = EXPECTED_SUCCESS_STATUS
    report["phase"] = "complete"
    return report


def _cleanup_private_copy(
    execution_fd: Optional[int],
    execution_path: Optional[str],
    execution_directory: Optional[str],
) -> Optional[str]:
    errors = []
    if execution_fd is not None:
        try:
            os.close(execution_fd)
        except OSError as exc:
            errors.append(f"close: {exc}")
    if execution_path is not None:
        try:
            os.unlink(execution_path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            errors.append(f"unlink: {exc}")
    if execution_directory is not None:
        try:
            os.rmdir(execution_directory)
        except FileNotFoundError:
            pass
        except OSError as exc:
            errors.append(f"rmdir: {exc}")
    return " | ".join(errors) if errors else None


def run_one_shot(
    *,
    identity: ArtifactIdentity = PRODUCTION_IDENTITY,
    geteuid: Callable[[], int] = os.geteuid,
    getegid: Callable[[], int] = os.getegid,
    executor: Executor = _execute_child,
    hooks: TestHooks = TestHooks(),
    private_parent: str = PRIVATE_EXECUTION_PARENT,
) -> dict[str, object]:
    """Authenticate and launch exactly once, or return a canonical HOLD."""

    effective_uid = geteuid()
    effective_gid = getegid()
    if effective_uid != identity.required_euid or effective_gid != identity.required_egid:
        report = _base_report(
            "HOLD_WRAPPER_PRIVILEGE_REQUIRED",
            "privilege_gate",
            effective_uid,
        )
        report["effective_gid"] = effective_gid
        return report

    directory_fd: Optional[int] = None
    binary_fd: Optional[int] = None
    execution_directory: Optional[str] = None
    execution_path: Optional[str] = None
    execution_fd: Optional[int] = None
    report: Optional[dict[str, object]] = None
    try:
        directory_fd, binary_fd, binary_status = _open_and_authenticate(
            identity,
            hooks,
        )
        (
            execution_directory,
            execution_path,
            execution_fd,
            execution_status,
        ) = _copy_to_private_execution_path(
            binary_fd,
            identity,
            effective_uid,
            effective_gid,
            private_parent,
        )

        source_path_status = os.stat(
            identity.filename,
            dir_fd=directory_fd,
            follow_symlinks=False,
        )
        _require_same_inode(
            binary_status,
            source_path_status,
            "staged_binary_pre_exec_binding",
        )
        if hooks.before_private_exec is not None:
            hooks.before_private_exec(execution_path, execution_fd)
        private_path_status = os.lstat(execution_path)
        _require_same_inode(
            execution_status,
            private_path_status,
            "private_binary_pre_exec_binding",
        )

        child = executor(execution_path)
        report = _child_report(child, effective_uid)
        report["artifact_sha256"] = identity.binary_sha256
        report["artifact_size"] = identity.binary_size
        report["execution_attempts"] = 1
    except (OSError, WrapperError) as exc:
        phase = exc.phase if isinstance(exc, WrapperError) else "wrapper_os_error"
        report = _hold_report(phase, str(exc), effective_uid)
        report["execution_attempts"] = 0
    finally:
        if binary_fd is not None:
            os.close(binary_fd)
        if directory_fd is not None:
            os.close(directory_fd)
        cleanup_error = _cleanup_private_copy(
            execution_fd,
            execution_path,
            execution_directory,
        )

    assert report is not None
    if cleanup_error is not None:
        report["prior_status"] = report["status"]
        report["status"] = "HOLD_WRAPPER_CLEANUP_FAILED"
        report["phase"] = "private_cleanup"
        report["cleanup_error"] = cleanup_error
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if arguments:
        report = _base_report(
            "HOLD_RUNTIME_INPUT_REJECTED",
            "runtime_input",
            os.geteuid(),
        )
        report["error"] = "This wrapper accepts no runtime arguments."
        _write_report(report)
        return 0
    report = run_one_shot()
    _write_report(report)
    # Every handled result returns its exact JSON through the one-shot
    # authorization transport. Success or HOLD is decided only by `status`.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
