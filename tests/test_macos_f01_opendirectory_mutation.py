from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "macos_f01_opendirectory_mutation.m"
READ_ONLY_SOURCE = ROOT / "scripts" / "macos_f01_opendirectory_readonly.m"
READ_ONLY_SOURCE_SHA256 = (
    "0b12fdebf944b01645733c9b7aaf1cbfa97397e82b6ebfbe80a6d823120adaa6"
)
PRIVILEGED_ACCOUNT_POLICY_DATA_BASE64 = (
    "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCFET0NUWVBFIHBsaXN0"
    "IFBVQkxJQyAiLS8vQXBwbGUvL0RURCBQTElTVCAxLjAvL0VOIiAiaHR0cDovL3d3dy5hcHBs"
    "ZS5jb20vRFREcy9Qcm9wZXJ0eUxpc3QtMS4wLmR0ZCI+CjxwbGlzdCB2ZXJzaW9uPSIxLjAi"
    "Pgo8ZGljdD4KCTxrZXk+Y3JlYXRpb25UaW1lPC9rZXk+Cgk8cmVhbD4xNzg2NjIxNDI1Ljc4"
    "NTU5OTk8L3JlYWw+CjwvZGljdD4KPC9wbGlzdD4K"
)
PRIVILEGED_ACCOUNT_POLICY_DATA_BYTES = (
    b'<?xml version="1.0" encoding="UTF-8"?>\n'
    b'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
    b'"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
    b'<plist version="1.0">\n'
    b"<dict>\n"
    b"\t<key>creationTime</key>\n"
    b"\t<real>1786621425.7855999</real>\n"
    b"</dict>\n"
    b"</plist>\n"
)


@unittest.skipUnless(platform.system() == "Darwin", "requires macOS OpenDirectory")
class OpenDirectoryMutationArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary = tempfile.TemporaryDirectory(
            prefix="decision-os-f01-od-mutation-tests-"
        )
        cls.temp = Path(cls._temporary.name)
        cls.module_cache = cls.temp / "module-cache"
        cls.module_cache.mkdir(mode=0o700)
        cls.production_dir = cls.temp / "production"
        cls.reproduction_dir = cls.temp / "reproduction"
        cls.production_dir.mkdir(mode=0o700)
        cls.reproduction_dir.mkdir(mode=0o700)
        cls.production_binary = cls.production_dir / "f01-od-mutation"
        cls.reproduction_binary = cls.reproduction_dir / "f01-od-mutation"
        cls.fixture_binary = cls.temp / "f01-od-mutation-tests"
        cls._compile(cls.production_binary)
        cls._compile(cls.reproduction_binary)
        cls._compile(cls.fixture_binary, "-DF01_TESTING")

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary.cleanup()

    @classmethod
    def _compile(
        cls,
        output: Path,
        *extra: str,
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
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )

    def test_modeled_transaction_and_adversarial_suite_passes(self) -> None:
        completed = subprocess.run(
            [str(self.fixture_binary)],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
        report = json.loads(completed.stdout)

        self.assertEqual(report["total"], 41)
        self.assertEqual(report["passed"], 41)
        self.assertEqual(report["failed"], 0)
        names = {item["name"] for item in report["tests"]}
        self.assertTrue(
            {
                "unprivileged_shaped_user_password_marker_validates",
                "privileged_shaped_user_password_absence_validates",
                "wrong_user_password_marker_zero_deletes",
                "multi_value_user_password_marker_zero_deletes",
                "credential_like_user_password_marker_zero_deletes",
                "non_string_user_password_marker_zero_deletes",
                "malformed_user_password_marker_zero_deletes",
                "exact_privileged_snapshot_account_policy_bytes_embedded",
                "exact_privileged_snapshot_current_state_validates",
                "exact_privileged_snapshot_orders_validation_before_fixture_delete",
                "wrong_user_guid_zero_deletes",
                "wrong_group_guid_zero_deletes",
                "wrong_uid_zero_deletes",
                "wrong_group_gid_zero_deletes",
                "missing_nfs_home_zero_deletes",
                "changed_nfs_home_zero_deletes",
                "user_shell_appears_zero_deletes",
                "is_hidden_appears_zero_deletes",
                "authentication_authority_appears_zero_deletes",
                "group_membership_appears_zero_deletes",
                "group_members_appears_zero_deletes",
                "guardian_appears_zero_deletes",
                "broker_appears_zero_deletes",
                "host_state_path_appears_zero_deletes",
                "duplicate_user_zero_deletes",
                "ambiguous_uid_zero_deletes",
                "immediate_rebind_drift_zero_deletes",
                "accepted_state_reaches_user_delete_and_retains_nserror",
                "uid_not_free_blocks_group_delete",
                "group_change_after_user_delete_blocks_group_delete",
                "group_delete_error_has_no_retry",
                "framework_read_error_retained_zero_deletes",
                "unprivileged_exact_state_has_zero_mutation_calls",
                "successful_transaction_two_deletes_in_order",
            }.issubset(names)
        )
        source = SOURCE.read_text(encoding="utf-8")
        self.assertEqual(source.count(PRIVILEGED_ACCOUNT_POLICY_DATA_BASE64), 1)
        stale_policy_data = PRIVILEGED_ACCOUNT_POLICY_DATA_BYTES.replace(
            b"1786621425.7855999",
            b"1786621421.5785599",
        )
        self.assertNotIn(
            base64.b64encode(stale_policy_data).decode("ascii"),
            source,
        )
        self.assertEqual(
            base64.b64decode(
                PRIVILEGED_ACCOUNT_POLICY_DATA_BASE64,
                validate=True,
            ),
            PRIVILEGED_ACCOUNT_POLICY_DATA_BYTES,
        )

    def test_production_binary_rejects_all_runtime_arguments_before_host_access(
        self,
    ) -> None:
        completed = subprocess.run(
            [str(self.production_binary), "--delete"],
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
        self.assertEqual(report["completed_mutations"], [])

    def test_production_surface_contains_only_direct_opendirectory_mutation(
        self,
    ) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        strings = subprocess.run(
            ["/usr/bin/strings", str(self.production_binary)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        ).stdout
        undefined = subprocess.run(
            ["/usr/bin/nm", "-u", str(self.production_binary)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        ).stdout

        self.assertEqual(source.count("deleteRecordAndReturnError:error"), 2)
        self.assertIn("deleteRecordAndReturnError:", strings)
        self.assertIn("_OBJC_CLASS_$_ODRecord", undefined)
        self.assertNotIn("successful_transaction_two_deletes_in_order", strings)
        for forbidden in (
            "AuthorizationCreate",
            "osascript",
            "/usr/bin/dscl",
            "/usr/bin/sudo",
            "sysadminctl",
            "dseditgroup",
            "pwpolicy",
            "NSTask",
            "NSURLSession",
            "getenv(",
            "NSUserDefaults",
            "system(",
            "popen(",
            "fgets(",
            "scanf(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_authority_and_identity_are_compile_time_fixed(self) -> None:
        source = SOURCE.read_text(encoding="utf-8")
        for required in (
            'F01NodeName = @"/Local/Default"',
            'F01PrincipalName = @"_decisionos_codex"',
            'F01UserGUID = @"D6515614-B56A-4943-AA41-18D17DE9F899"',
            'F01GroupGUID = @"1F200679-B0A2-4D13-A86F-6492F9C4B66F"',
            'F01NumericID = @"510"',
            'F01Home = @"/var/empty"',
            "F01RequiredMutationEUID = 0",
            "F01PrivilegedInteractionBudget = 1",
            "geteuid()",
        ):
            with self.subTest(required=required):
                self.assertIn(required, source)
        for forbidden in ("setuid(", "seteuid(", "setreuid(", "argv[1]", "stdin"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_password_marker_is_only_validation_contract_change(
        self,
    ) -> None:
        source = SOURCE.read_text(encoding="utf-8")

        self.assertIn("if (observation == nil)", source)
        self.assertIn(
            '![[(NSArray *)observation firstObject] isEqual:@"********"]',
            source,
        )
        self.assertEqual(
            source.count("F01RequireObserverSafeUserPasswordMarker(issues, user);"),
            1,
        )
        self.assertNotIn(
            "F01RequireValues(issues, user, kODAttributeTypePassword",
            source,
        )
        self.assertIn(
            "F01RequireValues(issues, group, kODAttributeTypePassword",
            source,
        )

    def test_binary_is_reproducible_native_and_has_bounded_dependencies(self) -> None:
        self.assertEqual(
            hashlib.sha256(self.production_binary.read_bytes()).hexdigest(),
            hashlib.sha256(self.reproduction_binary.read_bytes()).hexdigest(),
        )
        file_output = subprocess.run(
            ["/usr/bin/file", str(self.production_binary)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        ).stdout
        links = subprocess.run(
            ["/usr/bin/otool", "-L", str(self.production_binary)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        ).stdout

        self.assertIn("Mach-O 64-bit executable arm64", file_output)
        dependency_lines = [
            line.strip().split(" ", 1)[0]
            for line in links.splitlines()[1:]
            if line.strip()
        ]
        self.assertEqual(
            set(dependency_lines),
            {
                "/System/Library/Frameworks/Foundation.framework/Versions/C/Foundation",
                "/System/Library/Frameworks/OpenDirectory.framework/Versions/A/OpenDirectory",
                "/System/Library/Frameworks/CoreFoundation.framework/Versions/A/CoreFoundation",
                "/usr/lib/libSystem.B.dylib",
                "/usr/lib/libobjc.A.dylib",
            },
        )

    def test_accepted_read_only_helper_remains_byte_identical(self) -> None:
        self.assertEqual(
            hashlib.sha256(READ_ONLY_SOURCE.read_bytes()).hexdigest(),
            READ_ONLY_SOURCE_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
