from __future__ import annotations

import json
from pathlib import Path
import platform
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "macos_f01_opendirectory_readonly.m"


@unittest.skipUnless(platform.system() == "Darwin", "requires macOS OpenDirectory")
class OpenDirectoryReadOnlyHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary = tempfile.TemporaryDirectory(
            prefix="decision-os-f01-od-readonly-tests-"
        )
        cls.temp = Path(cls._temporary.name)
        cls.module_cache = cls.temp / "module-cache"
        cls.module_cache.mkdir(mode=0o700)
        cls.normal_binary = cls.temp / "f01-od-readonly"
        cls.test_binary = cls.temp / "f01-od-readonly-tests"
        cls._compile(cls.normal_binary)
        cls._compile(cls.test_binary, "-DF01_TESTING")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    @classmethod
    def _compile(
        cls,
        output: Path,
        *extra: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "/usr/bin/clang",
                "-fobjc-arc",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-O2",
                *extra,
                f"-fmodules-cache-path={cls.module_cache}",
                "-framework",
                "Foundation",
                "-framework",
                "OpenDirectory",
                str(SOURCE),
                "-o",
                str(output),
            ],
            check=check,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )

    def test_adversarial_fixture_suite_passes(self) -> None:
        completed = subprocess.run(
            [str(self.test_binary)],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
        report = json.loads(completed.stdout)

        self.assertEqual(report["total"], 32)
        self.assertEqual(report["passed"], 32)
        self.assertEqual(report["failed"], 0)
        names = {item["name"] for item in report["tests"]}
        self.assertTrue(
            {
                "wrong_user_guid",
                "wrong_group_guid",
                "wrong_uid",
                "wrong_group_gid",
                "missing_nfs_home",
                "changed_nfs_home",
                "user_shell_appears",
                "is_hidden_appears",
                "authentication_authority_appears",
                "group_membership_appears",
                "group_members_appears",
                "guardian_user_exists",
                "broker_group_exists",
                "duplicate_user_record",
                "wrong_opendirectory_node",
                "framework_read_error_retained",
                "deletion_disabled_zero_mutation_calls",
                "multivalue_attributes_are_canonicalized",
            }.issubset(names)
        )

    def test_ordinary_binary_rejects_all_runtime_arguments(self) -> None:
        completed = subprocess.run(
            [str(self.normal_binary), "--delete"],
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
        report = json.loads(completed.stdout)

        self.assertEqual(completed.returncode, 64)
        self.assertEqual(report["status"], "HOLD_RUNTIME_INPUT_REJECTED")
        self.assertFalse(report["mutation_attempted"])
        self.assertFalse(report["privileged_execution_authorized"])

    def test_ordinary_binary_has_no_delete_or_authorization_surface(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        strings = subprocess.run(
            ["/usr/bin/strings", str(self.normal_binary)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        ).stdout
        undefined = subprocess.run(
            ["/usr/bin/nm", "-u", str(self.normal_binary)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        ).stdout

        self.assertIn("PRIVILEGED_EXECUTION_AUTHORIZED = NO", source)
        self.assertNotIn("deleteRecordAndReturnError", source)
        self.assertNotIn("deleteRecordAndReturnError", strings)
        self.assertNotIn("deleteRecordAndReturnError", undefined)
        for forbidden in (
            "AuthorizationCreate",
            "osascript",
            "/usr/bin/dscl",
            "/usr/bin/sudo",
            "getenv(",
            "NSUserDefaults",
            "system(",
            "popen(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_mutation_enabled_compile_is_a_hard_error(self) -> None:
        completed = self._compile(
            self.temp / "must-not-build",
            "-DF01_MUTATION_ENABLED",
            check=False,
        )

        self.assertNotEqual(completed.returncode, 0)
        self.assertIn(
            "This read-only qualification source cannot be compiled with mutation support",
            completed.stderr,
        )

    def test_binary_is_native_macho_linked_only_to_expected_apple_surface(self) -> None:
        file_output = subprocess.run(
            ["/usr/bin/file", str(self.normal_binary)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        ).stdout
        links = subprocess.run(
            ["/usr/bin/otool", "-L", str(self.normal_binary)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        ).stdout

        self.assertIn("Mach-O 64-bit executable arm64", file_output)
        self.assertIn("OpenDirectory.framework", links)
        self.assertIn("Foundation.framework", links)


if __name__ == "__main__":
    unittest.main()
