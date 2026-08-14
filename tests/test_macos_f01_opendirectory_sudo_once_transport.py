from __future__ import annotations

import ast
import base64
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import shlex
import stat
import subprocess
import sys
import unittest
import warnings
import zlib


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "macos_f01_opendirectory_sudo_once_feeder.py"
COMMAND = ROOT / "scripts" / "macos_f01_opendirectory_sudo_once_command.txt"
S1_COMMAND = ROOT / "scripts" / "macos_f01_opendirectory_sudo_one_shot_command.txt"
LOADER = ROOT / "scripts" / "macos_f01_opendirectory_one_shot_loader.py"
WRAPPER = ROOT / "scripts" / "macos_f01_opendirectory_one_shot_wrapper.py"
MUTATION_SOURCE = ROOT / "scripts" / "macos_f01_opendirectory_mutation.m"
STAGE = Path("/private/tmp/decision-os-f01-slice4a-one-shot-0450739ae668")
STAGED_WRAPPER = STAGE / "macos_f01_opendirectory_one_shot_wrapper.py"
STAGED_MUTATOR = STAGE / "macos_f01_opendirectory_mutation"
SUDO = Path("/usr/bin/sudo")
PYTHON = (
    "/Library/Developer/CommandLineTools/Library/Frameworks/"
    "Python3.framework/Versions/3.9/bin/python3.9"
)

HELPER_SHA256 = "5659eb30493fa36ff6be61047549471b2d5c7faa4b456a9f954bdaf5a3c0938e"
COMMAND_SHA256 = "1877dfe9dd088a5d84fafd7febb0719e1f3bf96df4b0f4d3b2b5e1a6ec8cb8c8"
S1_COMMAND_SHA256 = "de3e767904080373237f2d0372f058add7d0b5db0270f8e0795d7280c72f4af4"
LOADER_SHA256 = "5ae6ab13c9068f2c63afef58c4749a7c55244f4cec1edf4381c92c20d2e86ab1"
WRAPPER_SHA256 = "faaa4ad63585ddc552a645d656976355c111351e5e36820ac745e31595f87ad9"
MUTATION_SOURCE_SHA256 = (
    "28f6728199e09a2e459eb1d0237e8d16ddb688e57b70c08050a45bcfabde32bf"
)
MUTATOR_SHA256 = "0450739ae6680b148d4c38af6cc047502be6b1d32b37cc53fc0b153a6ffed802"
SUDO_CONTENT_SHA256 = "NOT_USER_READABLE / NOT REQUIRED UNDER SSV TRUST CONTRACT"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_helper():
    spec = importlib.util.spec_from_file_location("f01_sudo_once_feeder", HELPER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FEEDER = load_helper()


def canonical_report(status: str, completed: list[str]) -> bytes:
    return (
        json.dumps(
            {"completed_mutations": completed, "status": status},
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


class OneReadPassword:
    def __init__(self, value: str) -> None:
        self.value = value
        self.calls = 0
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.calls += 1
        self.prompts.append(prompt)
        if self.calls != 1:
            raise AssertionError("a second human credential read was attempted")
        return self.value


class FakeSudoProcess:
    def __init__(self, returncode: int, stdout: bytes, stderr: bytes) -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.communicate_calls = 0
        self.input: bytes | None = None
        self.first_read: bytes | None = None
        self.second_read: bytes | None = None

    def communicate(self, *, input: bytes):
        self.communicate_calls += 1
        if self.communicate_calls != 1:
            raise AssertionError("a second stdin feed was attempted")
        self.input = input
        pipe = io.BytesIO(input)
        self.first_read = pipe.readline()
        self.second_read = pipe.readline()
        return self.stdout, self.stderr


class FakeProcessFactory:
    def __init__(self, process: FakeSudoProcess) -> None:
        self.process = process
        self.calls = 0
        self.argv: list[str] | None = None
        self.kwargs: dict[str, object] | None = None

    def __call__(self, argv: list[str], **kwargs: object) -> FakeSudoProcess:
        self.calls += 1
        if self.calls != 1:
            raise AssertionError("a second sudo process was attempted")
        self.argv = list(argv)
        self.kwargs = dict(kwargs)
        return self.process


class PipeProbeFactory:
    def __init__(self) -> None:
        self.calls = 0
        self.argv: list[str] | None = None

    def __call__(self, argv: list[str], **kwargs: object):
        self.calls += 1
        if self.calls != 1:
            raise AssertionError("a second child process was attempted")
        self.argv = list(argv)
        probe = (
            "import json,sys;"
            "first=sys.stdin.buffer.readline();"
            "second=sys.stdin.buffer.readline();"
            "report={'first_ends_newline':first.endswith(b'\\n'),"
            "'first_length':len(first),'second_length':len(second)};"
            "sys.stdout.write(json.dumps(report,separators=(',',':'),"
            "sort_keys=True)+'\\n')"
        )
        return subprocess.Popen(
            [sys.executable, "-I", "-S", "-c", probe],
            **kwargs,
        )


@unittest.skipUnless(platform.system() == "Darwin", "requires macOS host identity")
class SingleInputSudoTransportTests(unittest.TestCase):
    def run_fixture(
        self,
        *,
        secret: str,
        returncode: int,
        child_stdout: bytes,
        child_stderr: bytes,
    ):
        reader = OneReadPassword(secret)
        process = FakeSudoProcess(returncode, child_stdout, child_stderr)
        factory = FakeProcessFactory(process)
        output = io.BytesIO()
        errors = io.BytesIO()
        result = FEEDER.run_once(
            password_reader=reader,
            process_factory=factory,
            stdout=output,
            stderr=errors,
        )
        return result, reader, process, factory, output.getvalue(), errors.getvalue()

    def test_command_embeds_exact_helper_and_reviewed_loader(self) -> None:
        command = COMMAND.read_text(encoding="utf-8")
        tokens = shlex.split(command)
        bootstrap = tokens[-1]
        encoded_helper = bootstrap.split('b64decode("', 1)[1].split('")', 1)[0]
        embedded_helper = zlib.decompress(
            base64.b64decode(encoded_helper, validate=True)
        )
        embedded_loader = zlib.decompress(
            base64.b64decode(FEEDER.LOADER_PAYLOAD_B64, validate=True)
        )

        self.assertTrue(command.endswith("\n"))
        self.assertEqual(command.count("\n"), 1)
        self.assertEqual(tokens[:4], [PYTHON, "-I", "-S", "-c"])
        self.assertEqual(len(tokens), 5)
        self.assertEqual(sha256(COMMAND), COMMAND_SHA256)
        self.assertEqual(sha256(HELPER), HELPER_SHA256)
        self.assertEqual(embedded_helper, HELPER.read_bytes())
        self.assertEqual(embedded_loader, LOADER.read_bytes())
        self.assertEqual(hashlib.sha256(embedded_loader).hexdigest(), LOADER_SHA256)
        self.assertEqual(
            FEEDER.LOADER_BOOTSTRAP,
            shlex.split(S1_COMMAND.read_text(encoding="utf-8"))[-1],
        )
        compile(bootstrap, "<decision-os-f01-sudo-once-bootstrap>", "exec")
        compile(embedded_helper, "<decision-os-f01-sudo-once-feeder>", "exec")
        compile(FEEDER.LOADER_BOOTSTRAP, "<decision-os-f01-loader>", "exec")

    def test_single_password_line_single_sudo_and_exact_success(self) -> None:
        secret = "fixture-secret-never-serialize"
        success = canonical_report(
            "ROLLBACK_COMPLETE_AWAITING_INDEPENDENT_REVIEW",
            ["user_deleted", "group_deleted"],
        )
        result, reader, process, factory, output, errors = self.run_fixture(
            secret=secret,
            returncode=0,
            child_stdout=success,
            child_stderr=b"",
        )

        self.assertEqual(result, 0)
        self.assertEqual(reader.calls, 1)
        self.assertEqual(reader.prompts, [FEEDER.PASSWORD_PROMPT])
        self.assertEqual(factory.calls, 1)
        self.assertEqual(process.communicate_calls, 1)
        self.assertEqual(process.input, secret.encode("utf-8") + b"\n")
        self.assertEqual(process.first_read, secret.encode("utf-8") + b"\n")
        self.assertEqual(process.second_read, b"")
        self.assertEqual(factory.argv, list(FEEDER.SUDO_ARGV))
        assert factory.kwargs is not None
        self.assertIs(factory.kwargs["stdin"], subprocess.PIPE)
        self.assertIs(factory.kwargs["stdout"], subprocess.PIPE)
        self.assertIs(factory.kwargs["stderr"], subprocess.PIPE)
        self.assertEqual(factory.kwargs["env"], FEEDER.SUDO_ENV)
        self.assertEqual(output, success)
        self.assertEqual(errors, b"")

        durable_fixture = repr(
            (factory.argv, factory.kwargs["env"], output, errors)
        ).encode("utf-8")
        self.assertNotIn(secret.encode("utf-8"), durable_fixture)

    def test_wrong_password_second_sudo_read_gets_eof_without_human_retry(self) -> None:
        secret = "wrong-fixture-secret"
        diagnostic = b"sudo: no password was provided\n"
        result, reader, process, factory, output, errors = self.run_fixture(
            secret=secret,
            returncode=1,
            child_stdout=b"",
            child_stderr=diagnostic,
        )

        self.assertEqual(result, FEEDER.HOLD_EXIT_CODE)
        self.assertEqual(reader.calls, 1)
        self.assertEqual(factory.calls, 1)
        self.assertEqual(process.communicate_calls, 1)
        self.assertEqual(process.first_read, secret.encode("utf-8") + b"\n")
        self.assertEqual(process.second_read, b"")
        self.assertEqual(output, b"")
        self.assertEqual(errors, diagnostic)
        self.assertNotIn(secret.encode("utf-8"), output + errors)

    def test_real_pipe_fake_child_observes_one_line_then_eof(self) -> None:
        secret = "pipe-probe-secret"
        reader = OneReadPassword(secret)
        factory = PipeProbeFactory()
        output = io.BytesIO()
        errors = io.BytesIO()

        result = FEEDER.run_once(
            password_reader=reader,
            process_factory=factory,
            stdout=output,
            stderr=errors,
        )
        report = json.loads(output.getvalue())

        self.assertEqual(result, FEEDER.HOLD_EXIT_CODE)
        self.assertEqual(reader.calls, 1)
        self.assertEqual(factory.calls, 1)
        self.assertEqual(factory.argv, list(FEEDER.SUDO_ARGV))
        self.assertEqual(
            report,
            {
                "first_ends_newline": True,
                "first_length": len(secret.encode("utf-8")) + 1,
                "second_length": 0,
            },
        )
        self.assertEqual(errors.getvalue(), b"")
        self.assertNotIn(secret.encode("utf-8"), output.getvalue())

    def test_non_success_results_are_preserved_and_remain_hold(self) -> None:
        fixtures = (
            (0, canonical_report("HOLD_CHILD_RESULT", []), b"", "handled_hold"),
            (0, b"not-json\n", b"", "malformed"),
            (
                0,
                canonical_report(
                    "ROLLBACK_COMPLETE_AWAITING_INDEPENDENT_REVIEW",
                    ["user_deleted"],
                ),
                b"",
                "partial_completion",
            ),
            (
                1,
                canonical_report(
                    "ROLLBACK_COMPLETE_AWAITING_INDEPENDENT_REVIEW",
                    ["user_deleted", "group_deleted"],
                ),
                b"sudo-auth-failure\n",
                "nonzero_sudo",
            ),
        )
        for returncode, child_stdout, child_stderr, label in fixtures:
            with self.subTest(label=label):
                result, reader, process, factory, output, errors = self.run_fixture(
                    secret="fixture-only",
                    returncode=returncode,
                    child_stdout=child_stdout,
                    child_stderr=child_stderr,
                )
                self.assertEqual(result, FEEDER.HOLD_EXIT_CODE)
                self.assertEqual(reader.calls, 1)
                self.assertEqual(factory.calls, 1)
                self.assertEqual(process.communicate_calls, 1)
                self.assertEqual(output, child_stdout)
                self.assertEqual(errors, child_stderr)

    def test_cancelled_or_non_line_credential_fails_before_sudo(self) -> None:
        class CancelledPassword:
            def __init__(self) -> None:
                self.calls = 0

            def __call__(self, _prompt: str) -> str:
                self.calls += 1
                raise EOFError

        class EchoFallbackPassword:
            def __init__(self) -> None:
                self.calls = 0

            def __call__(self, _prompt: str) -> str:
                self.calls += 1
                warnings.warn(
                    "echo-safe input unavailable",
                    FEEDER.getpass.GetPassWarning,
                )
                return "must-not-be-returned"

        for reader in (
            CancelledPassword(),
            EchoFallbackPassword(),
            OneReadPassword("two\nlines"),
        ):
            with self.subTest(reader=type(reader).__name__):
                factory = FakeProcessFactory(FakeSudoProcess(0, b"", b""))
                result = FEEDER.run_once(
                    password_reader=reader,
                    process_factory=factory,
                    stdout=io.BytesIO(),
                    stderr=io.BytesIO(),
                )
                self.assertEqual(result, FEEDER.HOLD_EXIT_CODE)
                self.assertEqual(reader.calls, 1)
                self.assertEqual(factory.calls, 0)

    def test_static_surface_has_no_retry_recursion_fallback_or_secret_sink(self) -> None:
        source = HELPER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        named_calls = [
            node.func.id for node in calls if isinstance(node.func, ast.Name)
        ]
        attribute_calls = [
            node.func.attr for node in calls if isinstance(node.func, ast.Attribute)
        ]

        self.assertEqual(source.count("/usr/bin/sudo"), 1)
        self.assertEqual(named_calls.count("reader"), 1)
        self.assertEqual(named_calls.count("factory"), 1)
        self.assertEqual(attribute_calls.count("communicate"), 1)
        self.assertEqual(named_calls.count("run_once"), 1)
        self.assertFalse(
            any(
                isinstance(node, (ast.For, ast.While, ast.AsyncFor))
                for node in ast.walk(tree)
            )
        )
        self.assertNotIn("open(", source)
        self.assertNotIn("os.environ", source)
        self.assertNotIn("logging", source)
        for forbidden in (
            "osascript",
            "/usr/bin/dscl",
            "sysadminctl",
            "dseditgroup",
            "pwpolicy",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

        expected_argv = (
            "/usr/bin/sudo",
            "-S",
            "-p",
            "",
            "--",
            PYTHON,
            "-I",
            "-S",
            "-c",
            FEEDER.LOADER_BOOTSTRAP,
        )
        self.assertEqual(FEEDER.SUDO_ARGV, expected_argv)
        self.assertEqual(FEEDER.PRIVILEGED_HUMAN_INTERACTION_BUDGET, 1)
        self.assertEqual(FEEDER.SUDO_INVOCATION_BUDGET, 1)
        self.assertIs(FEEDER.AUTHORIZATION_RETRY_ALLOWED, False)
        self.assertEqual(FEEDER.main(["unexpected"]), FEEDER.HOLD_EXIT_CODE)

    def test_command_syntax_parses_without_execution(self) -> None:
        for shell in ("/bin/zsh", "/bin/sh"):
            with self.subTest(shell=shell):
                completed = subprocess.run(
                    [shell, "-n", str(COMMAND)],
                    check=False,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=15,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)

    @unittest.skipIf(os.geteuid() == 0, "qualification must remain unprivileged")
    def test_ssv_anchor_and_existing_chain_remain_exact(self) -> None:
        observed = os.lstat(SUDO)
        self.assertTrue(stat.S_ISREG(observed.st_mode))
        self.assertEqual(
            (
                observed.st_dev,
                observed.st_ino,
                observed.st_uid,
                observed.st_gid,
                stat.S_IMODE(observed.st_mode),
                observed.st_nlink,
                observed.st_size,
            ),
            (16777234, 1152921500312572853, 0, 0, 0o4511, 1, 1575952),
        )
        self.assertFalse(os.access(SUDO, os.R_OK))
        self.assertEqual(
            SUDO_CONTENT_SHA256,
            "NOT_USER_READABLE / NOT REQUIRED UNDER SSV TRUST CONTRACT",
        )
        for component in (Path("/"), Path("/usr"), Path("/usr/bin"), SUDO):
            with self.subTest(component=component):
                metadata = os.lstat(component)
                self.assertFalse(stat.S_ISLNK(metadata.st_mode))
                self.assertEqual((metadata.st_uid, metadata.st_gid), (0, 0))
                self.assertEqual(stat.S_IMODE(metadata.st_mode) & 0o022, 0)

        root_mount = next(
            line
            for line in subprocess.run(
                ["/sbin/mount"],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=15,
            ).stdout.splitlines()
            if " on / (" in line
        )
        for required in ("apfs", "sealed", "read-only"):
            self.assertIn(required, root_mount)

        self.assertEqual(sha256(S1_COMMAND), S1_COMMAND_SHA256)
        self.assertEqual(sha256(LOADER), LOADER_SHA256)
        self.assertEqual(sha256(WRAPPER), WRAPPER_SHA256)
        self.assertEqual(sha256(MUTATION_SOURCE), MUTATION_SOURCE_SHA256)
        self.assertEqual(sha256(STAGED_WRAPPER), WRAPPER_SHA256)
        self.assertEqual(sha256(STAGED_MUTATOR), MUTATOR_SHA256)

        stage = os.lstat(STAGE)
        wrapper = os.lstat(STAGED_WRAPPER)
        mutator = os.lstat(STAGED_MUTATOR)
        self.assertEqual(
            (
                stage.st_dev,
                stage.st_ino,
                stage.st_uid,
                stage.st_gid,
                stat.S_IMODE(stage.st_mode),
                stage.st_nlink,
                stage.st_size,
            ),
            (16777234, 123725406, 501, 0, 0o500, 4, 128),
        )
        self.assertEqual(
            (
                wrapper.st_dev,
                wrapper.st_ino,
                wrapper.st_uid,
                wrapper.st_gid,
                stat.S_IMODE(wrapper.st_mode),
                wrapper.st_nlink,
                wrapper.st_size,
            ),
            (16777234, 123725636, 501, 0, 0o444, 1, 21377),
        )
        self.assertEqual(
            (
                mutator.st_dev,
                mutator.st_ino,
                mutator.st_uid,
                mutator.st_gid,
                stat.S_IMODE(mutator.st_mode),
                mutator.st_nlink,
                mutator.st_size,
            ),
            (16777234, 123725407, 501, 0, 0o555, 1, 94704),
        )


if __name__ == "__main__":
    unittest.main()
