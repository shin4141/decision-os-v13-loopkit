from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
import platform
import shlex
import stat
import subprocess
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "scripts" / "macos_f01_opendirectory_sudo_one_shot_command.txt"
HISTORICAL_COMMAND = ROOT / "scripts" / "macos_f01_opendirectory_one_shot_command.txt"
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

COMMAND_SHA256 = "de3e767904080373237f2d0372f058add7d0b5db0270f8e0795d7280c72f4af4"
HISTORICAL_COMMAND_SHA256 = (
    "75d433390e58e08bbd4ba97c80addbc85814416794f76b51fb57d4d87add4575"
)
LOADER_SHA256 = "5ae6ab13c9068f2c63afef58c4749a7c55244f4cec1edf4381c92c20d2e86ab1"
WRAPPER_SHA256 = "faaa4ad63585ddc552a645d656976355c111351e5e36820ac745e31595f87ad9"
MUTATION_SOURCE_SHA256 = (
    "28f6728199e09a2e459eb1d0237e8d16ddb688e57b70c08050a45bcfabde32bf"
)
MUTATOR_SHA256 = "0450739ae6680b148d4c38af6cc047502be6b1d32b37cc53fc0b153a6ffed802"
SUDO_CONTENT_SHA256 = "NOT_USER_READABLE / NOT REQUIRED UNDER SSV TRUST CONTRACT"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decoded_loader() -> tuple[str, str, bytes]:
    command = COMMAND.read_text(encoding="utf-8")
    tokens = shlex.split(command)
    bootstrap = tokens[-1]
    encoded = bootstrap.split('b64decode("', 1)[1].split('")', 1)[0]
    return command, bootstrap, zlib.decompress(
        base64.b64decode(encoded, validate=True)
    )


@unittest.skipUnless(platform.system() == "Darwin", "requires macOS host identity")
class SSVSudoTransportTests(unittest.TestCase):
    def test_candidate_is_one_fixed_sudo_transport(self) -> None:
        command, bootstrap, _loader = decoded_loader()
        tokens = shlex.split(command)

        self.assertTrue(command.endswith("\n"))
        self.assertEqual(command.count("\n"), 1)
        self.assertEqual(sha256(COMMAND), COMMAND_SHA256)
        self.assertEqual(
            tokens[:6],
            ["/usr/bin/sudo", "--", PYTHON, "-I", "-S", "-c"],
        )
        self.assertEqual(len(tokens), 7)
        self.assertEqual(command.count("/usr/bin/sudo"), 1)
        self.assertEqual(command.count("osascript"), 0)
        self.assertEqual(command.count("administrator privileges"), 0)
        self.assertEqual(command.count("do shell script"), 0)
        self.assertNotIn("retry", command.lower())
        self.assertNotIn("fallback", command.lower())
        compile(bootstrap, "<decision-os-f01-sudo-bootstrap>", "exec")

    def test_exact_reviewed_loader_payload_is_embedded(self) -> None:
        _command, _bootstrap, loader = decoded_loader()

        self.assertEqual(loader, LOADER.read_bytes())
        self.assertEqual(hashlib.sha256(loader).hexdigest(), LOADER_SHA256)
        compile(loader, "<decision-os-f01-one-shot-loader>", "exec")
        decoded = loader.decode("utf-8")
        self.assertEqual(decoded.count("exec(compile(wrapper"), 1)
        for forbidden in (
            "osascript",
            "/usr/bin/sudo",
            "/usr/bin/dscl",
            "sysadminctl",
            "dseditgroup",
            "pwpolicy",
            "deleteRecord",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, decoded)

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
    def test_sudo_is_exact_ssv_managed_execute_only_anchor(self) -> None:
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
                self.assertEqual(metadata.st_uid, 0)
                self.assertEqual(metadata.st_gid, 0)
                self.assertEqual(stat.S_IMODE(metadata.st_mode) & 0o022, 0)

        mounted = subprocess.run(
            ["/sbin/mount"],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        ).stdout
        root_mount = next(
            line for line in mounted.splitlines() if " on / (" in line
        )
        for required in ("apfs", "sealed", "read-only"):
            with self.subTest(required=required):
                self.assertIn(required, root_mount)

    def test_existing_chain_and_historical_command_are_unchanged(self) -> None:
        self.assertEqual(sha256(HISTORICAL_COMMAND), HISTORICAL_COMMAND_SHA256)
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
