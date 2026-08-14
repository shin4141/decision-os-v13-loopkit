from __future__ import annotations

import base64
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from typing import Optional
import zlib

from scripts.macos_f01_opendirectory_one_shot_wrapper import (
    AUTHORIZATION_RETRY_ALLOWED,
    EXPECTED_COMPLETED_MUTATIONS,
    EXPECTED_SUCCESS_STATUS,
    PRIVILEGED_INTERACTION_BUDGET,
    PRODUCTION_IDENTITY,
    ArtifactIdentity,
    ChildExecution,
    TestHooks,
    _canonical_json_bytes,
    run_one_shot,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "macos_f01_opendirectory_one_shot_wrapper.py"
LOADER_SOURCE = ROOT / "scripts" / "macos_f01_opendirectory_one_shot_loader.py"
COMMAND = ROOT / "scripts" / "macos_f01_opendirectory_one_shot_command.txt"
STAGED_WRAPPER = Path(
    "/private/tmp/decision-os-f01-slice4a-one-shot-0450739ae668/"
    "macos_f01_opendirectory_one_shot_wrapper.py"
)
LOADER_SHA256 = "5ae6ab13c9068f2c63afef58c4749a7c55244f4cec1edf4381c92c20d2e86ab1"


class Fixture:
    def __init__(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(
            prefix="decision-os-f01-one-shot-tests-"
        )
        self.root = Path(self._temporary.name)
        self.stage = self.root / "stage"
        self.private_parent = self.root / "private"
        self.stage.mkdir(mode=0o700)
        self.private_parent.mkdir(mode=0o700)
        self.binary = self.stage / "macos_f01_opendirectory_mutation"
        self.payload = b"fixed fake Mach-O execution target\n"
        self.binary.write_bytes(self.payload)
        self.binary.chmod(0o555)
        self.stage.chmod(0o500)
        self.identity = self._identity()

    def _identity(self) -> ArtifactIdentity:
        directory = os.lstat(self.stage)
        binary = os.lstat(self.binary)
        import hashlib

        return ArtifactIdentity(
            directory=str(self.stage),
            filename=self.binary.name,
            directory_device=directory.st_dev,
            directory_inode=directory.st_ino,
            directory_uid=directory.st_uid,
            directory_gid=directory.st_gid,
            directory_mode=0o500,
            binary_device=binary.st_dev,
            binary_inode=binary.st_ino,
            binary_uid=binary.st_uid,
            binary_gid=binary.st_gid,
            binary_mode=0o555,
            binary_nlink=1,
            binary_size=len(self.payload),
            binary_sha256=hashlib.sha256(self.payload).hexdigest(),
            required_euid=os.geteuid(),
            required_egid=os.getegid(),
        )

    def run(
        self,
        executor,
        *,
        identity: Optional[ArtifactIdentity] = None,
        hooks: TestHooks = TestHooks(),
        geteuid=os.geteuid,
        getegid=os.getegid,
    ) -> dict[str, object]:
        return run_one_shot(
            identity=identity or self.identity,
            geteuid=geteuid,
            getegid=getegid,
            executor=executor,
            hooks=hooks,
            private_parent=str(self.private_parent),
        )

    def cleanup(self) -> None:
        try:
            self.stage.chmod(0o700)
        except FileNotFoundError:
            pass
        self._temporary.cleanup()


class RecordingExecutor:
    def __init__(self, result: ChildExecution) -> None:
        self.result = result
        self.calls: list[str] = []
        self.executed_bytes: list[bytes] = []
        self.executed_modes: list[int] = []

    def __call__(self, path: str) -> ChildExecution:
        self.calls.append(path)
        self.executed_bytes.append(Path(path).read_bytes())
        self.executed_modes.append(stat.S_IMODE(os.lstat(path).st_mode))
        return self.result


def child_json(status: str, completed: list[str]) -> bytes:
    return _canonical_json_bytes(
        {
            "completed_mutations": completed,
            "status": status,
        }
    )


def decoded_loader() -> tuple[str, bytes]:
    command = COMMAND.read_text(encoding="utf-8")
    encoded = command.split('b64decode(\\"', 1)[1].split('\\")', 1)[0]
    return command, zlib.decompress(base64.b64decode(encoded, validate=True))


class OneShotWrapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Fixture()

    def tearDown(self) -> None:
        self.fixture.cleanup()

    def assert_zero_execution(
        self,
        report: dict[str, object],
        executor: RecordingExecutor,
    ) -> None:
        self.assertEqual(executor.calls, [])
        self.assertEqual(report["execution_attempts"], 0)
        self.assertEqual(report["completed_mutations"], [])
        self.assertTrue(str(report["status"]).startswith("HOLD"))

    def test_child_success_executes_exact_private_copy_once(self) -> None:
        stdout = child_json(
            EXPECTED_SUCCESS_STATUS,
            list(EXPECTED_COMPLETED_MUTATIONS),
        )
        executor = RecordingExecutor(
            ChildExecution(exit_code=0, stdout=stdout, stderr=b"fixture stderr\n")
        )

        report = self.fixture.run(executor)

        self.assertEqual(report["status"], EXPECTED_SUCCESS_STATUS)
        self.assertEqual(report["completed_mutations"], list(EXPECTED_COMPLETED_MUTATIONS))
        self.assertEqual(report["execution_attempts"], 1)
        self.assertEqual(len(executor.calls), 1)
        self.assertEqual(executor.executed_bytes, [self.fixture.payload])
        self.assertEqual(executor.executed_modes, [0o500])
        self.assertEqual(base64.b64decode(report["child_stdout_base64"]), stdout)
        self.assertEqual(
            base64.b64decode(report["child_stderr_base64"]),
            b"fixture stderr\n",
        )

    def test_wrong_hash_or_size_has_zero_execution(self) -> None:
        for identity in (
            replace(self.fixture.identity, binary_sha256="0" * 64),
            replace(self.fixture.identity, binary_size=len(self.fixture.payload) + 1),
        ):
            with self.subTest(identity=identity):
                executor = RecordingExecutor(ChildExecution(0, b"", b""))
                report = self.fixture.run(executor, identity=identity)
                self.assert_zero_execution(report, executor)

    def test_wrong_inode_or_owner_has_zero_execution(self) -> None:
        for identity in (
            replace(
                self.fixture.identity,
                binary_inode=self.fixture.identity.binary_inode + 1,
            ),
            replace(
                self.fixture.identity,
                binary_uid=self.fixture.identity.binary_uid + 1,
            ),
        ):
            with self.subTest(identity=identity):
                executor = RecordingExecutor(ChildExecution(0, b"", b""))
                report = self.fixture.run(executor, identity=identity)
                self.assert_zero_execution(report, executor)

    def test_wrong_directory_identity_or_metadata_has_zero_execution(self) -> None:
        for identity in (
            replace(
                self.fixture.identity,
                directory_inode=self.fixture.identity.directory_inode + 1,
            ),
            replace(
                self.fixture.identity,
                directory_uid=self.fixture.identity.directory_uid + 1,
            ),
            replace(
                self.fixture.identity,
                directory_gid=self.fixture.identity.directory_gid + 1,
            ),
            replace(self.fixture.identity, directory_mode=0o700),
        ):
            with self.subTest(identity=identity):
                executor = RecordingExecutor(ChildExecution(0, b"", b""))
                report = self.fixture.run(executor, identity=identity)
                self.assert_zero_execution(report, executor)

    def test_missing_artifact_has_zero_execution(self) -> None:
        self.fixture.stage.chmod(0o700)
        self.fixture.binary.unlink()
        self.fixture.stage.chmod(0o500)
        executor = RecordingExecutor(ChildExecution(0, b"", b""))

        report = self.fixture.run(executor)

        self.assert_zero_execution(report, executor)

    def test_symlink_has_zero_execution(self) -> None:
        self.fixture.stage.chmod(0o700)
        target = self.fixture.root / "target"
        target.write_bytes(self.fixture.payload)
        target.chmod(0o555)
        self.fixture.binary.unlink()
        self.fixture.binary.symlink_to(target)
        self.fixture.stage.chmod(0o500)
        executor = RecordingExecutor(ChildExecution(0, b"", b""))

        report = self.fixture.run(executor)

        self.assert_zero_execution(report, executor)

    def test_hardlink_has_zero_execution(self) -> None:
        self.fixture.stage.chmod(0o700)
        os.link(self.fixture.binary, self.fixture.stage / "second-link")
        self.fixture.stage.chmod(0o500)
        executor = RecordingExecutor(ChildExecution(0, b"", b""))

        report = self.fixture.run(executor)

        self.assert_zero_execution(report, executor)

    def test_wrong_mode_has_zero_execution(self) -> None:
        self.fixture.binary.chmod(0o775)
        executor = RecordingExecutor(ChildExecution(0, b"", b""))

        report = self.fixture.run(executor)

        self.assert_zero_execution(report, executor)

    def test_changed_pathname_after_open_has_zero_execution(self) -> None:
        def replace_after_open(_directory_fd: int, _binary_fd: int) -> None:
            self.fixture.stage.chmod(0o700)
            self.fixture.binary.unlink()
            self.fixture.binary.write_bytes(self.fixture.payload)
            self.fixture.binary.chmod(0o555)
            self.fixture.stage.chmod(0o500)

        executor = RecordingExecutor(ChildExecution(0, b"", b""))
        report = self.fixture.run(
            executor,
            hooks=TestHooks(after_artifact_open=replace_after_open),
        )

        self.assert_zero_execution(report, executor)
        self.assertEqual(report["phase"], "staged_binary_post_open_binding")

    def test_private_executable_substitution_has_zero_execution(self) -> None:
        def substitute(path: str, _descriptor: int) -> None:
            os.unlink(path)
            Path(path).write_bytes(b"substitute")
            os.chmod(path, 0o500)

        executor = RecordingExecutor(ChildExecution(0, b"", b""))
        report = self.fixture.run(
            executor,
            hooks=TestHooks(before_private_exec=substitute),
        )

        self.assert_zero_execution(report, executor)
        self.assertEqual(report["phase"], "private_binary_pre_exec_binding")

    def test_nonzero_child_exit_is_hold_without_retry(self) -> None:
        stdout = child_json(
            EXPECTED_SUCCESS_STATUS,
            list(EXPECTED_COMPLETED_MUTATIONS),
        )
        executor = RecordingExecutor(ChildExecution(9, stdout, b"native failure"))

        report = self.fixture.run(executor)

        self.assertEqual(len(executor.calls), 1)
        self.assertEqual(report["execution_attempts"], 1)
        self.assertEqual(report["child_exit_code"], 9)
        self.assertEqual(report["status"], "HOLD_CHILD_RESULT")
        self.assertEqual(
            base64.b64decode(report["child_stderr_base64"]),
            b"native failure",
        )

    def test_malformed_child_json_is_hold_without_retry(self) -> None:
        executor = RecordingExecutor(ChildExecution(0, b"not-json\n", b""))

        report = self.fixture.run(executor)

        self.assertEqual(len(executor.calls), 1)
        self.assertEqual(report["status"], "HOLD_CHILD_RESULT")
        self.assertIn("not one valid JSON", report["error"])

    def test_child_hold_and_native_error_are_preserved_without_retry(self) -> None:
        child_report = {
            "completed_mutations": ["user_deleted"],
            "error": {
                "code": 777,
                "domain": "com.apple.OpenDirectory",
                "user_info": {"detail": "retained"},
            },
            "status": "HOLD_GROUP_DELETE_FAILED",
        }
        stdout = _canonical_json_bytes(child_report)
        executor = RecordingExecutor(ChildExecution(2, stdout, b"exact stderr"))

        report = self.fixture.run(executor)

        self.assertEqual(len(executor.calls), 1)
        self.assertEqual(report["status"], "HOLD_CHILD_RESULT")
        self.assertEqual(report["completed_mutations"], ["user_deleted"])
        self.assertEqual(report["child_report"], child_report)
        self.assertEqual(
            report["child_report"]["error"]["domain"],
            "com.apple.OpenDirectory",
        )

    def test_launch_error_is_hold_without_retry(self) -> None:
        executor = RecordingExecutor(
            ChildExecution(
                exit_code=None,
                stdout=b"",
                stderr=b"",
                launch_error="fixture launch failure",
            )
        )

        report = self.fixture.run(executor)

        self.assertEqual(len(executor.calls), 1)
        self.assertEqual(report["status"], "HOLD_CHILD_RESULT")
        self.assertEqual(report["child_launch_error"], "fixture launch failure")

    def test_unprivileged_gate_performs_zero_artifact_or_execution_calls(self) -> None:
        executor = RecordingExecutor(ChildExecution(0, b"", b""))

        report = self.fixture.run(
            executor,
            geteuid=lambda: self.fixture.identity.required_euid + 1,
        )

        self.assertEqual(executor.calls, [])
        self.assertEqual(report["status"], "HOLD_WRAPPER_PRIVILEGE_REQUIRED")
        self.assertEqual(report["authorization_invocations"], 0)
        self.assertEqual(report["privileged_prompt_count"], 0)

    def test_runtime_argument_is_rejected_without_authorization(self) -> None:
        completed = subprocess.run(
            ["/usr/bin/python3", "-I", "-S", str(SOURCE), "unexpected"],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
        report = json.loads(completed.stdout)

        self.assertEqual(report["status"], "HOLD_RUNTIME_INPUT_REJECTED")
        self.assertEqual(report["authorization_invocations"], 0)

    def test_one_interaction_budget_no_authorizer_retry_or_fallback_exists(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")

        self.assertEqual(PRIVILEGED_INTERACTION_BUDGET, 1)
        self.assertFalse(AUTHORIZATION_RETRY_ALLOWED)
        self.assertEqual(source.count("subprocess.run("), 1)
        self.assertEqual(source.count("child = executor(execution_path)"), 1)
        for forbidden in (
            "osascript",
            "/usr/bin/sudo",
            "/usr/bin/dscl",
            "sysadminctl",
            "dseditgroup",
            "pwpolicy",
            "AuthorizationCreate",
            "shell=True",
            "createRecord",
            "deleteRecord",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_hash_bound_loader_and_single_authorization_command(self) -> None:
        command, loader_bytes = decoded_loader()
        loader = loader_bytes.decode("utf-8")

        compile(loader_bytes, "<decision-os-f01-one-shot-loader>", "exec")
        self.assertEqual(loader_bytes, LOADER_SOURCE.read_bytes())
        self.assertEqual(command.count("/usr/bin/osascript"), 1)
        self.assertEqual(command.count("with administrator privileges"), 1)
        self.assertEqual(command.count("do shell script"), 1)
        self.assertEqual(hashlib.sha256(loader_bytes).hexdigest(), LOADER_SHA256)
        self.assertIn(
            "faaa4ad63585ddc552a645d656976355c111351e5e36820ac745e31595f87ad9",
            loader,
        )
        self.assertIn(
            "bdea59019a38eb6600cc9e71e984a97fedadc406448431281e7657030f54987e",
            loader,
        )
        self.assertEqual(loader.count("exec(compile(wrapper"), 1)
        for forbidden in (
            "subprocess",
            "/usr/bin/dscl",
            "/usr/bin/sudo",
            "sysadminctl",
            "dseditgroup",
            "pwpolicy",
            "deleteRecord",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, loader)

    @unittest.skipIf(os.geteuid() == 0, "qualification must remain unprivileged")
    def test_exact_loader_payload_unprivileged_is_hold_without_authorization(self) -> None:
        command, _loader_bytes = decoded_loader()
        bootstrap = command.split('quoted form of "', 1)[1].rsplit(
            '") with administrator privileges',
            1,
        )[0]
        bootstrap = bootstrap.replace('\\"', '"')
        completed = subprocess.run(
            [sys.executable, "-I", "-S", "-c", bootstrap],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
        report = json.loads(completed.stdout)

        self.assertEqual(report["status"], "HOLD_LOADER_PRIVILEGE_REQUIRED")
        self.assertEqual(report["mutation_execution_attempts"], 0)
        self.assertEqual(report["authorization_requests_issued_by_loader"], 0)
        self.assertEqual(report["privileged_prompts_issued_by_loader"], 0)

    def test_current_staged_wrapper_matches_hash_bound_loader(self) -> None:
        if not STAGED_WRAPPER.exists():
            self.skipTest("review-only staged wrapper is not present")
        _command, loader_bytes = decoded_loader()
        namespace = {
            "__builtins__": __builtins__,
            "__name__": "loader_qualification",
        }
        exec(
            compile(loader_bytes, "<decision-os-f01-one-shot-loader>", "exec"),
            namespace,
            namespace,
        )

        namespace["hash_fixed_interpreter"]()
        opened_bytes = namespace["read_fixed_wrapper"]()

        self.assertEqual(opened_bytes, SOURCE.read_bytes())
        self.assertEqual(opened_bytes, STAGED_WRAPPER.read_bytes())

    def test_current_staged_mutator_matches_wrapper_identity(self) -> None:
        identity = PRODUCTION_IDENTITY
        staged = Path(identity.directory) / identity.filename
        if not staged.exists():
            self.skipTest("review-only staged mutator is not present")
        directory = os.lstat(identity.directory)
        binary = os.lstat(staged)

        self.assertTrue(stat.S_ISDIR(directory.st_mode))
        self.assertEqual(
            (
                directory.st_dev,
                directory.st_ino,
                directory.st_uid,
                directory.st_gid,
                stat.S_IMODE(directory.st_mode),
            ),
            (
                identity.directory_device,
                identity.directory_inode,
                identity.directory_uid,
                identity.directory_gid,
                identity.directory_mode,
            ),
        )
        self.assertTrue(stat.S_ISREG(binary.st_mode))
        self.assertEqual(
            (
                binary.st_dev,
                binary.st_ino,
                binary.st_uid,
                binary.st_gid,
                stat.S_IMODE(binary.st_mode),
                binary.st_nlink,
                binary.st_size,
                hashlib.sha256(staged.read_bytes()).hexdigest(),
            ),
            (
                identity.binary_device,
                identity.binary_inode,
                identity.binary_uid,
                identity.binary_gid,
                identity.binary_mode,
                identity.binary_nlink,
                identity.binary_size,
                identity.binary_sha256,
            ),
        )


if __name__ == "__main__":
    unittest.main()
