#!/usr/bin/env python3
"""Fail-closed qualification for the canonical local Companion process."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
from typing import Mapping, Protocol


RESULT_SCHEMA = "decision-os.companion-process-qualification.v0.1"
CANONICAL_MODULE = "decision_os.companion"
CANONICAL_LISTENER_HOST = "127.0.0.1"
LAUNCHER_RELATIVE_PATH = Path("macos/DecisionOSCompanion.applescript")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MODULE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*$")

PASS = "PASS"
RUNTIME_LISTENER_MISSING = "RUNTIME_LISTENER_MISSING"
RUNTIME_LISTENER_MULTIPLE_OWNERS = "RUNTIME_LISTENER_MULTIPLE_OWNERS"
RUNTIME_PROCESS_MISSING = "RUNTIME_PROCESS_MISSING"
RUNTIME_PROCESS_EXECUTABLE_MISMATCH = "RUNTIME_PROCESS_EXECUTABLE_MISMATCH"
RUNTIME_PROCESS_COMMAND_MISMATCH = "RUNTIME_PROCESS_COMMAND_MISMATCH"
RUNTIME_PROCESS_MODULE_MISMATCH = "RUNTIME_PROCESS_MODULE_MISMATCH"
RUNTIME_PROCESS_PARENT_AMBIGUOUS = "RUNTIME_PROCESS_PARENT_AMBIGUOUS"
RUNTIME_PROCESS_EVIDENCE_UNAVAILABLE = "RUNTIME_PROCESS_EVIDENCE_UNAVAILABLE"
RUNTIME_ROOT_MISSING = "RUNTIME_ROOT_MISSING"
RUNTIME_PRODUCT_TREE_MISMATCH = "RUNTIME_PRODUCT_TREE_MISMATCH"
RUNTIME_LAUNCHER_SOURCE_MISMATCH = "RUNTIME_LAUNCHER_SOURCE_MISMATCH"
RUNTIME_LAUNCHER_MODULE_MISMATCH = "RUNTIME_LAUNCHER_MODULE_MISMATCH"


class ProcessEvidenceUnavailable(RuntimeError):
    """The bounded operating-system evidence could not be collected safely."""


@dataclass(frozen=True)
class ProcessEvidence:
    pid: int
    parent_pid: int
    executable: str
    argv: tuple[str, ...]


@dataclass(frozen=True)
class ListenerEvidence:
    exists: bool
    owner_pids: tuple[int, ...]


@dataclass(frozen=True)
class QualificationConfig:
    runtime_root: Path
    repository_root: Path
    expected_product_tree: str
    expected_python: Path
    listener_host: str
    listener_port: int
    expected_module: str
    expected_applet: Path | None = None


@dataclass(frozen=True)
class QualificationResult:
    code: str
    details: Mapping[str, object]

    @property
    def passed(self) -> bool:
        return self.code == PASS

    def as_dict(self) -> dict[str, object]:
        return {
            "schema": RESULT_SCHEMA,
            "result": self.code,
            "passed": self.passed,
            "details": dict(self.details),
        }


class ProcessCollector(Protocol):
    def listener(self, host: str, port: int) -> ListenerEvidence:
        """Return the bounded listener and owner-PID evidence."""

    def process(self, pid: int) -> ProcessEvidence | None:
        """Return one process identity or None when that PID no longer exists."""

    def expected_process_executable(self, expected_python: Path) -> str:
        """Resolve the OS process executable used by the expected Python."""


class DarwinProcessCollector:
    """Collect only the listener owner and the exact processes it binds."""

    @staticmethod
    def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                command,
                capture_output=True,
                check=False,
                text=True,
            )
        except OSError as exc:
            raise ProcessEvidenceUnavailable(
                "Operating-system process evidence is unavailable."
            ) from exc

    def listener(self, host: str, port: int) -> ListenerEvidence:
        completed = self._run(
            [
                "lsof",
                "-nP",
                "-a",
                f"-iTCP@{host}:{port}",
                "-sTCP:LISTEN",
                "-Fpn",
            ]
        )
        if completed.returncode not in {0, 1}:
            raise ProcessEvidenceUnavailable(
                "Listener ownership evidence is unavailable."
            )
        owners: set[int] = set()
        listener_seen = False
        for line in completed.stdout.splitlines():
            if line.startswith("p") and line[1:].isdigit():
                owners.add(int(line[1:]))
            elif line.startswith("n"):
                listener_seen = True
        if completed.returncode == 1 and not completed.stdout.strip():
            return ListenerEvidence(False, ())
        return ListenerEvidence(listener_seen or bool(owners), tuple(sorted(owners)))

    def _ps_field(self, pid: int, field: str) -> str | None:
        completed = self._run(
            ["ps", "-ww", "-p", str(pid), "-o", f"{field}="]
        )
        if completed.returncode == 1:
            return None
        if completed.returncode != 0:
            raise ProcessEvidenceUnavailable(
                "Process identity evidence is unavailable."
            )
        value = completed.stdout.strip()
        return value or None

    def process(self, pid: int) -> ProcessEvidence | None:
        executable = self._ps_field(pid, "comm")
        if executable is None:
            return None
        parent = self._ps_field(pid, "ppid")
        command = self._ps_field(pid, "command")
        if parent is None or not parent.isdigit() or command is None:
            raise ProcessEvidenceUnavailable(
                "Process identity evidence is incomplete."
            )
        try:
            argv = tuple(shlex.split(command, posix=True))
        except ValueError as exc:
            raise ProcessEvidenceUnavailable(
                "Process argv evidence is malformed."
            ) from exc
        if not argv:
            raise ProcessEvidenceUnavailable("Process argv evidence is empty.")
        return ProcessEvidence(pid, int(parent), executable, argv)

    def expected_process_executable(self, expected_python: Path) -> str:
        probe = (
            "import os, subprocess; "
            "print(subprocess.check_output("
            "['ps','-ww','-p',str(os.getpid()),'-o','comm='],"
            "text=True).strip())"
        )
        completed = self._run([str(expected_python), "-c", probe])
        value = completed.stdout.strip()
        if completed.returncode != 0 or not value:
            raise ProcessEvidenceUnavailable(
                "Expected Python executable identity is unavailable."
            )
        return value


def _result(code: str, **details: object) -> QualificationResult:
    return QualificationResult(code, details)


def _path_matches(observed: str | Path, expected: str | Path) -> bool:
    observed_path = Path(observed)
    expected_path = Path(expected)
    try:
        return os.path.samefile(observed_path, expected_path)
    except OSError:
        return (
            observed_path.expanduser().resolve(strict=False)
            == expected_path.expanduser().resolve(strict=False)
        )


def product_tree_sha256(runtime_root: Path) -> str:
    """Reproduce the authorized sorted 51-file product manifest identity."""

    package = runtime_root / "decision_os"
    if not package.is_dir() or package.is_symlink():
        raise ProcessEvidenceUnavailable(
            "Installed Decision OS product tree is unavailable."
        )
    files: list[Path] = []
    for path in package.rglob("*"):
        relative = path.relative_to(runtime_root)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ProcessEvidenceUnavailable(
                "Installed Decision OS product tree contains a symlink."
            )
        if path.is_file():
            files.append(path)
    rows = []
    for path in sorted(
        files,
        key=lambda item: item.relative_to(runtime_root).as_posix().encode("utf-8"),
    ):
        relative = path.relative_to(runtime_root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{digest}  {relative}\n")
    return hashlib.sha256("".join(rows).encode("utf-8")).hexdigest()


def _launcher_binding(
    config: QualificationConfig,
) -> tuple[QualificationResult | None, str | None]:
    installed = config.runtime_root / LAUNCHER_RELATIVE_PATH
    authorized = config.repository_root / LAUNCHER_RELATIVE_PATH
    if (
        not installed.is_file()
        or installed.is_symlink()
        or not authorized.is_file()
        or authorized.is_symlink()
    ):
        return _result(RUNTIME_LAUNCHER_SOURCE_MISMATCH), None
    try:
        installed_bytes = installed.read_bytes()
        authorized_bytes = authorized.read_bytes()
    except OSError:
        return _result(RUNTIME_PROCESS_EVIDENCE_UNAVAILABLE), None
    if installed_bytes != authorized_bytes:
        return _result(RUNTIME_LAUNCHER_SOURCE_MISMATCH), None
    try:
        source = authorized_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return _result(RUNTIME_LAUNCHER_SOURCE_MISMATCH), None
    if f" -m {config.expected_module}" not in source:
        return _result(RUNTIME_LAUNCHER_MODULE_MISMATCH), None
    return None, hashlib.sha256(installed_bytes).hexdigest()


def qualify_process_evidence(
    *,
    listener: ListenerEvidence,
    processes: Mapping[int, ProcessEvidence],
    expected_process_executable: str,
    expected_module: str,
    expected_applet: Path | None = None,
) -> QualificationResult:
    """Classify already-collected process evidence without OS access."""

    if not isinstance(listener, ListenerEvidence):
        return _result(RUNTIME_PROCESS_EVIDENCE_UNAVAILABLE)
    if not listener.exists:
        return _result(RUNTIME_LISTENER_MISSING)
    owners = tuple(sorted(set(listener.owner_pids)))
    if len(owners) > 1:
        return _result(
            RUNTIME_LISTENER_MULTIPLE_OWNERS,
            listener_owner_count=len(owners),
        )
    if len(owners) != 1:
        return _result(RUNTIME_PROCESS_MISSING)
    owner_pid = owners[0]
    process = processes.get(owner_pid)
    if not isinstance(process, ProcessEvidence) or process.pid != owner_pid:
        return _result(RUNTIME_PROCESS_MISSING, listener_owner_pid=owner_pid)
    if (
        type(process.parent_pid) is not int
        or process.parent_pid < 0
        or not isinstance(process.executable, str)
        or not process.executable
        or not isinstance(process.argv, tuple)
        or not all(isinstance(value, str) and value for value in process.argv)
        or not isinstance(expected_process_executable, str)
        or not expected_process_executable
    ):
        return _result(RUNTIME_PROCESS_EVIDENCE_UNAVAILABLE)
    if not _path_matches(process.executable, expected_process_executable):
        return _result(
            RUNTIME_PROCESS_EXECUTABLE_MISMATCH,
            listener_owner_pid=owner_pid,
        )
    argv = process.argv
    if len(argv) != 3 or argv[1] != "-m":
        return _result(
            RUNTIME_PROCESS_COMMAND_MISMATCH,
            listener_owner_pid=owner_pid,
        )
    if argv[2] != expected_module:
        return _result(
            RUNTIME_PROCESS_MODULE_MISMATCH,
            listener_owner_pid=owner_pid,
        )
    if not _path_matches(argv[0], process.executable):
        return _result(
            RUNTIME_PROCESS_COMMAND_MISMATCH,
            listener_owner_pid=owner_pid,
        )
    applet_verified = False
    if expected_applet is not None:
        parent = processes.get(process.parent_pid)
        if (
            process.parent_pid <= 1
            or not isinstance(parent, ProcessEvidence)
            or parent.pid != process.parent_pid
            or not isinstance(parent.executable, str)
            or not _path_matches(parent.executable, expected_applet)
        ):
            return _result(
                RUNTIME_PROCESS_PARENT_AMBIGUOUS,
                listener_owner_pid=owner_pid,
            )
        applet_verified = True
    return _result(
        PASS,
        listener_owner_pid=owner_pid,
        module=expected_module,
        applet_parent_verified=applet_verified,
    )


def qualify_companion_process(
    config: QualificationConfig,
    *,
    collector: ProcessCollector | None = None,
) -> QualificationResult:
    """Bind the installed tree and launcher to the listener-owning process."""

    if (
        not isinstance(config, QualificationConfig)
        or config.listener_host != CANONICAL_LISTENER_HOST
        or type(config.listener_port) is not int
        or not 1 <= config.listener_port <= 65535
        or config.expected_module != CANONICAL_MODULE
        or _MODULE_RE.fullmatch(config.expected_module) is None
        or _SHA256_RE.fullmatch(config.expected_product_tree) is None
        or not config.runtime_root.is_absolute()
        or not config.repository_root.is_absolute()
        or not config.expected_python.is_absolute()
        or (
            config.expected_applet is not None
            and not config.expected_applet.is_absolute()
        )
    ):
        return _result(RUNTIME_PROCESS_EVIDENCE_UNAVAILABLE)
    if (
        not config.runtime_root.is_dir()
        or config.runtime_root.is_symlink()
    ):
        return _result(RUNTIME_ROOT_MISSING)
    try:
        installed_tree = product_tree_sha256(config.runtime_root)
    except (OSError, ProcessEvidenceUnavailable):
        return _result(RUNTIME_PROCESS_EVIDENCE_UNAVAILABLE)
    if installed_tree != config.expected_product_tree:
        return _result(
            RUNTIME_PRODUCT_TREE_MISMATCH,
            installed_product_tree=installed_tree,
        )
    launcher_failure, launcher_sha256 = _launcher_binding(config)
    if launcher_failure is not None:
        return launcher_failure
    active_collector = collector or DarwinProcessCollector()
    try:
        listener = active_collector.listener(
            config.listener_host,
            config.listener_port,
        )
        owner_processes: dict[int, ProcessEvidence] = {}
        for pid in listener.owner_pids:
            process = active_collector.process(pid)
            if process is not None:
                owner_processes[pid] = process
                if config.expected_applet is not None and process.parent_pid > 1:
                    parent = active_collector.process(process.parent_pid)
                    if parent is not None:
                        owner_processes[parent.pid] = parent
        expected_executable = active_collector.expected_process_executable(
            config.expected_python
        )
    except ProcessEvidenceUnavailable:
        return _result(RUNTIME_PROCESS_EVIDENCE_UNAVAILABLE)
    process_result = qualify_process_evidence(
        listener=listener,
        processes=owner_processes,
        expected_process_executable=expected_executable,
        expected_module=config.expected_module,
        expected_applet=config.expected_applet,
    )
    if not process_result.passed:
        return process_result
    return _result(
        PASS,
        **process_result.details,
        listener_host=config.listener_host,
        listener_port=config.listener_port,
        installed_product_tree=installed_tree,
        installed_launcher_sha256=launcher_sha256,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Qualify the canonical listener-owning Companion process."
    )
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--expected-product-tree", required=True)
    parser.add_argument("--expected-python", type=Path, required=True)
    parser.add_argument("--listener-host", required=True)
    parser.add_argument("--listener-port", type=int, required=True)
    parser.add_argument("--expected-module", required=True)
    parser.add_argument("--expected-applet", type=Path)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    result = qualify_companion_process(
        QualificationConfig(
            runtime_root=arguments.runtime_root,
            repository_root=arguments.repository_root,
            expected_product_tree=arguments.expected_product_tree,
            expected_python=arguments.expected_python,
            listener_host=arguments.listener_host,
            listener_port=arguments.listener_port,
            expected_module=arguments.expected_module,
            expected_applet=arguments.expected_applet,
        )
    )
    print(json.dumps(result.as_dict(), sort_keys=True, separators=(",", ":")))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
