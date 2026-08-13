from __future__ import annotations

from pathlib import Path
import unittest

from scripts.macos_f01_rollback_partial_codex import (
    CONFIRMATION,
    DSCL,
    EXPECTED_GROUP,
    EXPECTED_IDENTITY_SHA256,
    EXPECTED_USER,
    GROUP_PATH,
    PRIVILEGED_INTERACTION_BUDGET,
    ROLLBACK_MUTATION_COMMANDS,
    RollbackError,
    CommandResult,
    USER_PATH,
    _parse_record,
    rollback_partial_codex,
)


class FakeDirectoryService:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, tuple[str, ...]]] = {
            USER_PATH: dict(EXPECTED_USER)
            | {
                "NFSHomeDirectory": ("/var/empty",),
                "UserShell": ("/usr/bin/false",),
            },
            GROUP_PATH: dict(EXPECTED_GROUP),
        }
        self.calls: list[tuple[str, ...]] = []
        self.mutations: list[tuple[str, ...]] = []
        self.fail_delete_path: str | None = None
        self.swap_group_after_user_delete = False
        self.uid_collision_after_user_delete = False
        self.gid_collision_after_group_delete = False
        self.swap_user_before_rebind = False
        self.user_reads = 0

    @staticmethod
    def _record_output(
        record: dict[str, tuple[str, ...]],
        keys: tuple[str, ...],
    ) -> bytes:
        lines: list[str] = []
        selected = keys or tuple(sorted(record))
        for key in selected:
            value = record.get(key)
            if value is None:
                lines.append(f"No such key: {key}")
            elif len(value) == 1:
                lines.append(f"{key}: {value[0]}")
            else:
                lines.append(f"{key}:")
                lines.extend(f" {item}" for item in value)
        return ("\n".join(lines) + "\n").encode()

    def __call__(self, arguments: tuple[str, ...] | list[str]) -> CommandResult:
        command = tuple(arguments)
        self.calls.append(command)
        if command[:3] == (DSCL, ".", "-read"):
            path = command[3]
            record = self.records.get(path)
            if record is None:
                return CommandResult(
                    56,
                    stderr=b"<dscl_cmd> DS Error: -14136 (eDSRecordNotFound)\n",
                )
            if path == USER_PATH:
                self.user_reads += 1
                if self.swap_user_before_rebind and self.user_reads == 2:
                    record["GeneratedUID"] = (
                        "AAAAAAAA-BBBB-4CCC-8DDD-EEEEEEEEEEEE",
                    )
            return CommandResult(0, self._record_output(record, command[4:]))
        if command[:3] == (DSCL, ".", "-search"):
            root, attribute, expected = command[3:6]
            prefix = "/Users/" if root == "/Users" else "/Groups/"
            matches = []
            for path, record in self.records.items():
                if path.startswith(prefix) and record.get(attribute) == (expected,):
                    matches.append(path.rsplit("/", 1)[1])
            output = "".join(
                f"{name}\t\t{attribute} = (\n    {expected}\n)\n"
                for name in matches
            ).encode()
            return CommandResult(0, output)
        if command[:3] == (DSCL, ".", "-delete"):
            self.mutations.append(command)
            path = command[3]
            if path == self.fail_delete_path:
                return CommandResult(
                    40,
                    stderr=b"DS Error: -14120 (eDSPermissionError)\n",
                )
            if path not in self.records:
                return CommandResult(
                    56,
                    stderr=b"DS Error: -14136 (eDSRecordNotFound)\n",
                )
            del self.records[path]
            if path == USER_PATH:
                if self.swap_group_after_user_delete:
                    self.records[GROUP_PATH]["GeneratedUID"] = (
                        "AAAAAAAA-BBBB-4CCC-8DDD-EEEEEEEEEEEE",
                    )
                if self.uid_collision_after_user_delete:
                    self.records["/Users/unrelated"] = {
                        "RecordName": ("unrelated",),
                        "UniqueID": ("510",),
                    }
            if path == GROUP_PATH and self.gid_collision_after_group_delete:
                self.records["/Groups/unrelated"] = {
                    "RecordName": ("unrelated",),
                    "PrimaryGroupID": ("510",),
                }
            return CommandResult(0)
        raise AssertionError(f"Unexpected command: {command!r}")


def run(fake: FakeDirectoryService, *, state_exists: bool = False) -> dict[str, object]:
    return rollback_partial_codex(
        runner=fake,
        lexists=lambda path: state_exists,
        sleep=lambda _seconds: None,
        system=lambda: "Darwin",
        geteuid=lambda: 0,
        require_tool=lambda _path: None,
    )


class PartialCodexRollbackTests(unittest.TestCase):
    def test_exact_partial_identity_is_removed_and_verified(self) -> None:
        fake = FakeDirectoryService()

        report = run(fake)

        self.assertTrue(report["passed"])
        self.assertEqual(report["gate"], "HOLD")
        self.assertEqual(fake.mutations, list(ROLLBACK_MUTATION_COMMANDS))
        self.assertNotIn(USER_PATH, fake.records)
        self.assertNotIn(GROUP_PATH, fake.records)
        self.assertTrue(report["uid_510_free"])
        self.assertTrue(report["gid_510_free"])
        self.assertFalse(report["provisioning_performed"])
        self.assertFalse(report["protected_repository_acl_changed"])

    def test_expected_identity_is_bound_to_name_uid_gid_and_both_guids(self) -> None:
        self.assertEqual(EXPECTED_USER["RecordName"], ("_decisionos_codex",))
        self.assertEqual(EXPECTED_USER["UniqueID"], ("510",))
        self.assertEqual(EXPECTED_USER["PrimaryGroupID"], ("510",))
        self.assertEqual(
            EXPECTED_USER["GeneratedUID"],
            ("D6515614-B56A-4943-AA41-18D17DE9F899",),
        )
        self.assertEqual(EXPECTED_GROUP["PrimaryGroupID"], ("510",))
        self.assertEqual(
            EXPECTED_GROUP["GeneratedUID"],
            ("1F200679-B0A2-4D13-A86F-6492F9C4B66F",),
        )
        self.assertEqual(len(EXPECTED_IDENTITY_SHA256), 64)

    def test_each_user_identity_mismatch_refuses_all_deletion(self) -> None:
        mutations = {
            "RecordName": ("_decisionos_codex_old",),
            "UniqueID": ("999",),
            "GeneratedUID": ("AAAAAAAA-BBBB-4CCC-8DDD-EEEEEEEEEEEE",),
            "PrimaryGroupID": ("999",),
            "RealName": ("Unrelated", "principal"),
        }
        for key, value in mutations.items():
            with self.subTest(key=key):
                fake = FakeDirectoryService()
                fake.records[USER_PATH][key] = value
                with self.assertRaisesRegex(RollbackError, "mismatch"):
                    run(fake)
                self.assertEqual(fake.mutations, [])

    def test_each_group_identity_mismatch_refuses_all_deletion(self) -> None:
        mutations = {
            "RecordName": ("_decisionos_codex_old",),
            "PrimaryGroupID": ("999",),
            "GeneratedUID": ("AAAAAAAA-BBBB-4CCC-8DDD-EEEEEEEEEEEE",),
            "RealName": ("Unrelated", "group"),
        }
        for key, value in mutations.items():
            with self.subTest(key=key):
                fake = FakeDirectoryService()
                fake.records[GROUP_PATH][key] = value
                with self.assertRaisesRegex(RollbackError, "mismatch"):
                    run(fake)
                self.assertEqual(fake.mutations, [])

    def test_unexpected_authentication_or_group_membership_refuses_deletion(self) -> None:
        cases = (
            (USER_PATH, "AuthenticationAuthority", (";ShadowHash;",)),
            (GROUP_PATH, "GroupMembership", ("unrelated",)),
            (
                GROUP_PATH,
                "GroupMembers",
                ("AAAAAAAA-BBBB-4CCC-8DDD-EEEEEEEEEEEE",),
            ),
        )
        for path, key, value in cases:
            with self.subTest(path=path, key=key):
                fake = FakeDirectoryService()
                fake.records[path][key] = value
                with self.assertRaises(RollbackError):
                    run(fake)
                self.assertEqual(fake.mutations, [])

    def test_duplicate_uid_or_gid_refuses_deletion(self) -> None:
        for kind in ("uid", "gid"):
            with self.subTest(kind=kind):
                fake = FakeDirectoryService()
                if kind == "uid":
                    fake.records["/Users/unrelated"] = {
                        "RecordName": ("unrelated",),
                        "UniqueID": ("510",),
                    }
                else:
                    fake.records["/Groups/unrelated"] = {
                        "RecordName": ("unrelated",),
                        "PrimaryGroupID": ("510",),
                    }
                with self.assertRaisesRegex(RollbackError, "uniquely bound"):
                    run(fake)
                self.assertEqual(fake.mutations, [])

    def test_guardian_broker_or_state_tree_presence_refuses_deletion(self) -> None:
        for path in (
            "/Users/_decisionos_guardian",
            "/Users/_decisionos_broker",
            "/Groups/_decisionos_guardian",
            "/Groups/_decisionos_broker",
        ):
            with self.subTest(path=path):
                fake = FakeDirectoryService()
                fake.records[path] = {"RecordName": (path.rsplit("/", 1)[1],)}
                with self.assertRaisesRegex(RollbackError, "unexpectedly exists"):
                    run(fake)
                self.assertEqual(fake.mutations, [])
        fake = FakeDirectoryService()
        with self.assertRaisesRegex(RollbackError, "host state exists"):
            run(fake, state_exists=True)
        self.assertEqual(fake.mutations, [])

    def test_first_delete_failure_stops_without_group_delete_or_retry(self) -> None:
        fake = FakeDirectoryService()
        fake.fail_delete_path = USER_PATH

        with self.assertRaisesRegex(RollbackError, "HOLD without retry") as raised:
            run(fake)

        self.assertEqual(fake.mutations, [ROLLBACK_MUTATION_COMMANDS[0]])
        self.assertEqual(raised.exception.completed_mutations, ())

    def test_group_is_rebound_after_user_deletion_before_group_delete(self) -> None:
        fake = FakeDirectoryService()
        fake.swap_group_after_user_delete = True

        with self.assertRaisesRegex(RollbackError, "Group identity mismatch") as raised:
            run(fake)

        self.assertEqual(fake.mutations, [ROLLBACK_MUTATION_COMMANDS[0]])
        self.assertEqual(raised.exception.completed_mutations, ("user_deleted",))
        self.assertIn(GROUP_PATH, fake.records)

    def test_user_is_rebound_immediately_before_user_delete(self) -> None:
        fake = FakeDirectoryService()
        fake.swap_user_before_rebind = True

        with self.assertRaisesRegex(RollbackError, "User identity mismatch"):
            run(fake)

        self.assertEqual(fake.mutations, [])

    def test_native_hidden_attribute_is_normalized(self) -> None:
        self.assertEqual(
            _parse_record(b"dsAttrTypeNative:IsHidden: 1\n"),
            {"IsHidden": ("1",)},
        )

    def test_uid_collision_after_user_delete_stops_before_group_delete(self) -> None:
        fake = FakeDirectoryService()
        fake.uid_collision_after_user_delete = True

        with self.assertRaisesRegex(RollbackError, "UID 510 remains") as raised:
            run(fake)

        self.assertEqual(fake.mutations, [ROLLBACK_MUTATION_COMMANDS[0]])
        self.assertEqual(raised.exception.completed_mutations, ("user_deleted",))
        self.assertIn("/Users/unrelated", fake.records)

    def test_host_state_emerging_after_user_delete_stops_before_group_delete(
        self,
    ) -> None:
        fake = FakeDirectoryService()

        with self.assertRaisesRegex(RollbackError, "host state exists") as raised:
            rollback_partial_codex(
                runner=fake,
                lexists=lambda _path: USER_PATH not in fake.records,
                sleep=lambda _seconds: None,
                system=lambda: "Darwin",
                geteuid=lambda: 0,
                require_tool=lambda _path: None,
            )

        self.assertEqual(fake.mutations, [ROLLBACK_MUTATION_COMMANDS[0]])
        self.assertEqual(raised.exception.completed_mutations, ("user_deleted",))
        self.assertIn(GROUP_PATH, fake.records)

    def test_group_delete_failure_stops_without_retry(self) -> None:
        fake = FakeDirectoryService()
        fake.fail_delete_path = GROUP_PATH

        with self.assertRaisesRegex(RollbackError, "HOLD without retry") as raised:
            run(fake)

        self.assertEqual(fake.mutations, list(ROLLBACK_MUTATION_COMMANDS))
        self.assertEqual(raised.exception.completed_mutations, ("user_deleted",))

    def test_gid_collision_after_group_delete_is_detected(self) -> None:
        fake = FakeDirectoryService()
        fake.gid_collision_after_group_delete = True

        with self.assertRaisesRegex(RollbackError, "GID 510 remains") as raised:
            run(fake)

        self.assertEqual(fake.mutations, list(ROLLBACK_MUTATION_COMMANDS))
        self.assertEqual(
            raised.exception.completed_mutations,
            ("user_deleted", "group_deleted"),
        )
        self.assertIn("/Groups/unrelated", fake.records)

    def test_non_root_or_non_darwin_never_reaches_directory_service(self) -> None:
        for system, euid in (("Linux", 0), ("Darwin", 501)):
            with self.subTest(system=system, euid=euid):
                fake = FakeDirectoryService()
                with self.assertRaises(RollbackError):
                    rollback_partial_codex(
                        runner=fake,
                        lexists=lambda _path: False,
                        sleep=lambda _seconds: None,
                        system=lambda: system,
                        geteuid=lambda: euid,
                        require_tool=lambda _path: None,
                    )
                self.assertEqual(fake.calls, [])

    def test_only_two_mutation_commands_exist_and_target_slice_records(self) -> None:
        self.assertEqual(
            ROLLBACK_MUTATION_COMMANDS,
            (
                (DSCL, ".", "-delete", USER_PATH),
                (DSCL, ".", "-delete", GROUP_PATH),
            ),
        )
        source = Path(
            "scripts/macos_f01_rollback_partial_codex.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("osascript", source)
        self.assertNotIn("/usr/bin/sudo", source)
        self.assertNotIn("/usr/bin/pwpolicy", source)
        self.assertNotIn('"-create"', source)

    def test_single_interaction_budget_and_exact_confirmation_are_fixed(self) -> None:
        self.assertEqual(PRIVILEGED_INTERACTION_BUDGET, 1)
        self.assertEqual(
            CONFIRMATION,
            "rollback-only-observed-partial-codex-uid-gid-510",
        )


if __name__ == "__main__":
    unittest.main()
