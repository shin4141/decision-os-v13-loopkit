from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import unittest
from unittest import mock

import decision_os.companion.principal_separation as principal_module
from scripts.macos_f01_rollback_partial_codex import CommandResult

from decision_os.companion.principal_separation import (
    ADMIN_GID,
    AUTHENTICATION_KEY_BYTES,
    BROKER_KEY_DIRECTORY,
    BROKER_KEY_PATH,
    BROKER_RUNTIME_DIRECTORY,
    CONTROLLER_KEY_DIRECTORY,
    CONTROLLER_KEY_PATH,
    HostObservation,
    KEYS_DIRECTORY,
    PRINCIPAL_SEPARATION_SCHEMA,
    PRINCIPAL_SPECS,
    PRIVILEGED_INTERACTION_BUDGET,
    AdversarialObservation,
    PrincipalObservation,
    PrincipalReceipt,
    PrincipalSeparationError,
    RECEIPT_PATH,
    ResourceObservation,
    RoleReceipt,
    STATE_ROOT,
    canonical_receipt_bytes,
    evaluate_principal_separation,
    principal_separation_plan,
    provision_principal_separation,
)


USER_GUIDS = {
    "codex": "10000000-0000-4000-8000-000000000001",
    "controller": "20000000-0000-4000-8000-000000000002",
    "broker": "30000000-0000-4000-8000-000000000003",
}
GROUP_GUIDS = {
    "codex": "40000000-0000-4000-8000-000000000004",
    "controller": "50000000-0000-4000-8000-000000000005",
    "broker": "60000000-0000-4000-8000-000000000006",
}
INSTALLATION_ID = "70000000-0000-4000-8000-000000000007"
KEY_HASH = hashlib.sha256(b"k" * AUTHENTICATION_KEY_BYTES).hexdigest()


def valid_receipt() -> PrincipalReceipt:
    return PrincipalReceipt(
        installation_id=INSTALLATION_ID,
        created_at_unix=1_786_585_200,
        roles={
            spec.role: RoleReceipt(
                account_name=spec.account_name,
                unique_id=spec.unique_id,
                generated_uid=USER_GUIDS[spec.role],
                private_group_name=spec.private_group_name,
                private_group_id=spec.private_group_id,
                private_group_generated_uid=GROUP_GUIDS[spec.role],
            )
            for spec in PRINCIPAL_SPECS
        },
        authentication_key_id=(
            f"decision-os-f01-envelope-hmac:{INSTALLATION_ID}"
        ),
        authentication_key_sha256=KEY_HASH,
    )


def principal(role: str) -> PrincipalObservation:
    spec = next(value for value in PRINCIPAL_SPECS if value.role == role)
    # macOS may add universal/non-authority groups. Only private-group sharing,
    # admin/wheel, sudo, and protected resource ownership carry authority here.
    effective = (spec.private_group_id, 12, 61, 100, 701, 702)
    return PrincipalObservation(
        account_name=spec.account_name,
        unique_id=spec.unique_id,
        generated_uid=USER_GUIDS[role],
        primary_group_id=spec.private_group_id,
        private_group_name=spec.private_group_name,
        private_group_generated_uid=GROUP_GUIDS[role],
        private_group_members=(spec.account_name,),
        private_group_member_guids=(USER_GUIDS[role],),
        home="/var/empty",
        shell="/usr/bin/false",
        is_hidden="1",
        authentication_allowed=False,
        effective_group_ids=effective,
        sudo_root_allowed=False,
        sudo_broker_allowed=role == "broker",
    )


def resource(
    path: object,
    kind: str,
    uid: int,
    gid: int,
    mode: int,
    inode: int,
    *,
    links: int = 1,
) -> ResourceObservation:
    return ResourceObservation(
        path=str(path),
        kind=kind,
        owner_uid=uid,
        group_gid=gid,
        mode=mode,
        device=17,
        inode=inode,
        link_count=links,
    )


def valid_observation(receipt: PrincipalReceipt) -> HostObservation:
    return HostObservation(
        platform="Darwin",
        verifier_euid=0,
        receipt_sha256=hashlib.sha256(canonical_receipt_bytes(receipt)).hexdigest(),
        principals={role: principal(role) for role in USER_GUIDS},
        resources={
            "state_root": resource(STATE_ROOT, "directory", 0, 0, 0o755, 1),
            "receipt": resource(RECEIPT_PATH, "regular", 0, 0, 0o444, 2),
            "keys": resource(KEYS_DIRECTORY, "directory", 0, 0, 0o711, 3),
            "controller_key_directory": resource(
                CONTROLLER_KEY_DIRECTORY, "directory", 0, 511, 0o750, 4
            ),
            "broker_key_directory": resource(
                BROKER_KEY_DIRECTORY, "directory", 0, 512, 0o750, 5
            ),
            "controller_key": resource(
                CONTROLLER_KEY_PATH, "regular", 0, 511, 0o440, 6
            ),
            "broker_key": resource(
                BROKER_KEY_PATH, "regular", 0, 512, 0o440, 7
            ),
            "broker_runtime": resource(
                BROKER_RUNTIME_DIRECTORY, "directory", 0, 512, 0o770, 8
            ),
        },
        controller_key_sha256=KEY_HASH,
        broker_key_sha256=KEY_HASH,
        adversarial=AdversarialObservation(
            codex_reads_controller_key=False,
            codex_reads_broker_key=False,
            controller_reads_controller_key=True,
            controller_reads_broker_key=False,
            broker_reads_controller_key=False,
            broker_reads_broker_key=True,
            codex_writes_broker_runtime=False,
            controller_writes_broker_runtime=False,
            broker_writes_broker_runtime=True,
            codex_impersonates_broker=False,
            controller_impersonates_broker=False,
        ),
    )


def check_map(observation: HostObservation) -> dict[str, bool]:
    report = evaluate_principal_separation(valid_receipt(), observation)
    return {check.code: check.passed for check in report.checks}


class PrincipalReceiptTests(unittest.TestCase):
    def test_strict_receipt_round_trip_is_canonical(self) -> None:
        receipt = valid_receipt()
        parsed = PrincipalReceipt.from_dict(
            json.loads(canonical_receipt_bytes(receipt))
        )

        self.assertEqual(parsed, receipt)
        self.assertEqual(canonical_receipt_bytes(parsed), canonical_receipt_bytes(receipt))

    def test_receipt_rejects_unknown_field(self) -> None:
        value = valid_receipt().as_dict()
        value["protected_repository"] = "/tmp/repository"

        with self.assertRaisesRegex(PrincipalSeparationError, "fields"):
            PrincipalReceipt.from_dict(value)

    def test_receipt_rejects_role_or_fixed_id_substitution(self) -> None:
        value = valid_receipt().as_dict()
        value["roles"]["broker"]["unique_id"] = 510

        with self.assertRaisesRegex(PrincipalSeparationError, "fixed"):
            PrincipalReceipt.from_dict(value)

    def test_receipt_rejects_duplicate_user_or_group_identity(self) -> None:
        value = valid_receipt().as_dict()
        value["roles"]["broker"]["generated_uid"] = USER_GUIDS["codex"]

        with self.assertRaisesRegex(PrincipalSeparationError, "distinct"):
            PrincipalReceipt.from_dict(value)

    def test_receipt_rejects_relocated_key_or_runtime_path(self) -> None:
        for field in (
            "controller_key_path",
            "broker_key_path",
            "broker_runtime_directory",
        ):
            with self.subTest(field=field):
                value = valid_receipt().as_dict()
                value[field] = "/tmp/attacker-controlled"
                with self.assertRaisesRegex(
                    PrincipalSeparationError, "resource bindings"
                ):
                    PrincipalReceipt.from_dict(value)

    def test_receipt_rejects_wrong_authentication_key_id(self) -> None:
        value = valid_receipt().as_dict()
        value["authentication_key_id"] = "old-installation-key"

        with self.assertRaisesRegex(PrincipalSeparationError, "key identity"):
            PrincipalReceipt.from_dict(value)


class PrincipalEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.receipt = valid_receipt()
        self.observation = valid_observation(self.receipt)

    def test_complete_separation_evidence_passes(self) -> None:
        report = evaluate_principal_separation(self.receipt, self.observation)

        self.assertTrue(report.passed)
        self.assertGreaterEqual(len(report.checks), 40)
        self.assertFalse(report.as_dict()["protected_repository_acl_installed"])
        self.assertFalse(report.as_dict()["sole_writer_claimed"])
        self.assertNotIn(USER_GUIDS["broker"], json.dumps(report.as_dict()))
        self.assertNotIn(KEY_HASH, json.dumps(report.as_dict()))

    def test_stale_broker_name_with_new_guid_fails_closed(self) -> None:
        principals = dict(self.observation.principals)
        principals["broker"] = replace(
            principals["broker"],
            generated_uid="80000000-0000-4000-8000-000000000008",
            private_group_member_guids=(
                "80000000-0000-4000-8000-000000000008",
            ),
        )
        observed = replace(self.observation, principals=principals)

        checks = check_map(observed)

        self.assertFalse(checks["broker_identity_pinned"])
        self.assertFalse(evaluate_principal_separation(self.receipt, observed).passed)

    def test_codex_key_readability_fails_closed(self) -> None:
        adversarial = replace(
            self.observation.adversarial,
            codex_reads_broker_key=True,
        )
        observed = replace(self.observation, adversarial=adversarial)

        self.assertFalse(check_map(observed)["codex_cannot_read_trust_material"])

    def test_controller_approval_plus_broker_write_fails_closed(self) -> None:
        adversarial = replace(
            self.observation.adversarial,
            controller_writes_broker_runtime=True,
        )
        observed = replace(self.observation, adversarial=adversarial)

        self.assertFalse(
            check_map(observed)[
                "controller_approval_does_not_imply_broker_write"
            ]
        )

    def test_controller_without_approval_key_access_fails_closed(self) -> None:
        adversarial = replace(
            self.observation.adversarial,
            controller_reads_controller_key=False,
        )

        self.assertFalse(
            check_map(replace(self.observation, adversarial=adversarial))[
                "controller_has_approval_not_broker_trust_access"
            ]
        )

    def test_broker_without_own_trust_access_fails_closed(self) -> None:
        adversarial = replace(
            self.observation.adversarial,
            broker_reads_broker_key=False,
        )

        self.assertFalse(
            check_map(replace(self.observation, adversarial=adversarial))[
                "broker_has_broker_trust_not_controller_copy"
            ]
        )

    def test_codex_or_controller_impersonation_fails_closed(self) -> None:
        for field, code in (
            ("codex_impersonates_broker", "codex_cannot_impersonate_broker"),
            (
                "controller_impersonates_broker",
                "controller_cannot_impersonate_broker",
            ),
        ):
            with self.subTest(field=field):
                adversarial = replace(
                    self.observation.adversarial,
                    **{field: True},
                )
                self.assertFalse(
                    check_map(replace(self.observation, adversarial=adversarial))[
                        code
                    ]
                )

    def test_admin_or_sudo_membership_fails_closed(self) -> None:
        principals = dict(self.observation.principals)
        principals["codex"] = replace(
            principals["codex"],
            effective_group_ids=principals["codex"].effective_group_ids
            + (ADMIN_GID,),
            sudo_root_allowed=True,
        )
        checks = check_map(replace(self.observation, principals=principals))

        self.assertFalse(checks["codex_not_admin_or_wheel"])
        self.assertFalse(checks["codex_cannot_sudo_root"])

    def test_shared_private_group_fails_even_when_common_groups_are_allowed(self) -> None:
        principals = dict(self.observation.principals)
        principals["controller"] = replace(
            principals["controller"],
            effective_group_ids=principals["controller"].effective_group_ids
            + (512,),
        )

        checks = check_map(replace(self.observation, principals=principals))

        self.assertFalse(checks["no_shared_private_authority_group"])

    def test_login_or_authentication_enablement_fails_closed(self) -> None:
        principals = dict(self.observation.principals)
        principals["broker"] = replace(
            principals["broker"],
            shell="/bin/zsh",
            authentication_allowed=True,
        )

        self.assertFalse(
            check_map(replace(self.observation, principals=principals))[
                "broker_login_disabled"
            ]
        )

    def test_wrong_resource_owner_group_or_mode_fails_closed(self) -> None:
        mutations = (
            ("owner_uid", 501),
            ("group_gid", 511),
            ("mode", 0o777),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                resources = dict(self.observation.resources)
                resources["broker_runtime"] = replace(
                    resources["broker_runtime"], **{field: value}
                )
                self.assertFalse(
                    check_map(replace(self.observation, resources=resources))[
                        "broker_runtime_ownership_and_mode"
                    ]
                )

    def test_linked_or_mismatched_key_copies_fail_closed(self) -> None:
        resources = dict(self.observation.resources)
        resources["broker_key"] = replace(
            resources["broker_key"],
            inode=resources["controller_key"].inode,
            link_count=2,
        )
        observed = replace(
            self.observation,
            resources=resources,
            broker_key_sha256=hashlib.sha256(b"other").hexdigest(),
        )
        checks = check_map(observed)

        self.assertFalse(checks["trust_key_copies_not_linked"])
        self.assertFalse(checks["trust_key_commitment_matches"])

    def test_missing_role_or_resource_observation_fails_closed(self) -> None:
        principals = dict(self.observation.principals)
        resources = dict(self.observation.resources)
        del principals["controller"]
        del resources["broker_key"]
        checks = check_map(
            replace(self.observation, principals=principals, resources=resources)
        )

        self.assertFalse(checks["complete_role_observation"])
        self.assertFalse(checks["controller_identity_present"])
        self.assertFalse(checks["complete_resource_observation"])
        self.assertFalse(checks["broker_key_ownership_and_mode"])

    def test_non_root_or_non_darwin_observation_fails_closed(self) -> None:
        observed = replace(self.observation, platform="Linux", verifier_euid=501)
        checks = check_map(observed)

        self.assertFalse(checks["darwin_host"])
        self.assertFalse(checks["root_verifier"])


class PrincipalSurfaceTests(unittest.TestCase):
    def test_plan_is_fixed_and_has_no_repository_or_acl_input(self) -> None:
        plan = principal_separation_plan()

        self.assertEqual(plan["schema"], PRINCIPAL_SEPARATION_SCHEMA)
        self.assertFalse(plan["protected_repository_path_parameter"])
        self.assertFalse(plan["protected_repository_acl_installed"])
        self.assertFalse(plan["sole_writer_claimed"])
        self.assertNotIn("repository", plan["resources"])
        self.assertEqual(plan["privileged_interaction_budget"], 1)
        self.assertFalse(plan["authorization_retry_allowed"])
        self.assertFalse(plan["mutation_retry_allowed"])

    @mock.patch(
        "decision_os.companion.principal_separation.platform.system",
        return_value="Darwin",
    )
    @mock.patch(
        "decision_os.companion.principal_separation.os.geteuid",
        return_value=501,
    )
    def test_provision_requires_explicit_root_gate(
        self,
        _geteuid: mock.Mock,
        _system: mock.Mock,
    ) -> None:
        with self.assertRaisesRegex(PrincipalSeparationError, "root execution"):
            provision_principal_separation()


class FakeProvisionDirectoryService:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, tuple[str, ...]]] = {}
        self.authentication_allowed: dict[str, bool] = {}
        self.calls: list[tuple[str, ...]] = []
        self.mutations: list[tuple[str, ...]] = []
        self.fail_command: tuple[str, ...] | None = None
        self.delayed_attribute: tuple[str, str] | None = None
        self.delayed_reads_remaining = 0
        self.authentication_reads_before_disabled = 0

    def _record_output(
        self,
        path: str,
        keys: tuple[str, ...],
    ) -> bytes:
        record = self.records[path]
        lines: list[str] = []
        for key in keys or tuple(sorted(record)):
            value = record.get(key)
            if (
                self.delayed_attribute == (path, key)
                and self.delayed_reads_remaining > 0
            ):
                self.delayed_reads_remaining -= 1
                value = None
            if value is None:
                lines.append(f"No such key: {key}")
                continue
            output_key = "dsAttrTypeNative:IsHidden" if key == "IsHidden" else key
            if len(value) == 1:
                lines.append(f"{output_key}: {value[0]}")
            else:
                lines.append(f"{output_key}:")
                lines.extend(f" {item}" for item in value)
        return ("\n".join(lines) + "\n").encode()

    def __call__(self, arguments: tuple[str, ...] | list[str]) -> CommandResult:
        command = tuple(arguments)
        self.calls.append(command)
        if command[:3] == (principal_module.DSCL, ".", "-read"):
            path = command[3]
            if path not in self.records:
                return CommandResult(
                    56,
                    stderr=b"DS Error: -14136 (eDSRecordNotFound)\n",
                )
            return CommandResult(0, self._record_output(path, command[4:]))
        if command[:3] == (principal_module.DSCL, ".", "-search"):
            root, attribute, expected = command[3:6]
            prefix = f"{root}/"
            matches = [
                path.rsplit("/", 1)[1]
                for path, record in self.records.items()
                if path.startswith(prefix) and record.get(attribute) == (expected,)
            ]
            output = "".join(
                f"{name}\t\t{attribute} = (\n    {expected}\n)\n"
                for name in matches
            ).encode()
            return CommandResult(0, output)
        if command[:3] == (principal_module.DSCL, ".", "-create"):
            self.mutations.append(command)
            if command == self.fail_command:
                return CommandResult(
                    40,
                    stderr=b"DS Error: -14120 (eDSPermissionError)\n",
                )
            path = command[3]
            name = path.rsplit("/", 1)[1]
            record = self.records.setdefault(path, {"RecordName": (name,)})
            if path.startswith("/Users/"):
                record.setdefault("Password", ("********",))
                self.authentication_allowed.setdefault(name, True)
            if len(command) == 6:
                attribute, value = command[4:6]
                record[attribute] = tuple(value.split())
            return CommandResult(0)
        if command[0] == principal_module.PWPOLICY:
            account = command[2]
            operation = command[3]
            if operation == "disableuser":
                self.mutations.append(command)
                if command == self.fail_command:
                    return CommandResult(
                        40,
                        stderr=b"password policy mutation failed\n",
                    )
                self.authentication_allowed[account] = False
                return CommandResult(0)
            if operation == "authentication-allowed":
                allowed = self.authentication_allowed[account]
                if not allowed and self.authentication_reads_before_disabled > 0:
                    self.authentication_reads_before_disabled -= 1
                    allowed = True
                message = (
                    f"Policy allows user <{account}> to authenticate\n"
                    if allowed
                    else f"User <{account}> is not allowed to authenticate: disabled\n"
                )
                return CommandResult(0, message.encode())
        raise AssertionError(f"Unexpected command: {command!r}")


class CorrectedProvisionTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fake = FakeProvisionDirectoryService()

    def _run_full(
        self,
    ) -> tuple[object, list[tuple[object, ...]], list[tuple[object, ...]]]:
        directories: list[tuple[object, ...]] = []
        files: list[tuple[object, ...]] = []
        guids = iter(
            (
                "10000000-0000-4000-8000-000000000001",
                "20000000-0000-4000-8000-000000000002",
                "30000000-0000-4000-8000-000000000003",
                "40000000-0000-4000-8000-000000000004",
                "50000000-0000-4000-8000-000000000005",
                "60000000-0000-4000-8000-000000000006",
                "70000000-0000-4000-8000-000000000007",
            )
        )
        with (
            mock.patch.object(principal_module, "_run", side_effect=self.fake),
            mock.patch.object(principal_module, "_require_darwin_root"),
            mock.patch.object(principal_module, "_ensure_root_parent"),
            mock.patch.object(
                principal_module,
                "_create_directory",
                side_effect=lambda *args: directories.append(args),
            ),
            mock.patch.object(
                principal_module,
                "_write_new_file",
                side_effect=lambda *args: files.append(args),
            ),
            mock.patch.object(principal_module, "_fsync_directory"),
            mock.patch.object(
                principal_module, "_new_guid", side_effect=lambda: next(guids)
            ),
            mock.patch.object(
                principal_module.secrets,
                "token_bytes",
                return_value=b"k" * AUTHENTICATION_KEY_BYTES,
            ),
            mock.patch.object(
                principal_module,
                "verify_installed_principal_separation",
                return_value=mock.sentinel.report,
            ),
            mock.patch.object(principal_module.time, "sleep"),
            mock.patch.object(
                principal_module.time, "time", return_value=1_786_585_200
            ),
            mock.patch.object(Path, "exists", return_value=False),
            mock.patch.object(Path, "is_file", return_value=False),
            mock.patch.object(Path, "is_symlink", return_value=False),
        ):
            result = principal_module.provision_principal_separation()
        return result, directories, files

    def test_complete_future_transaction_succeeds_in_fixture(self) -> None:
        result, directories, files = self._run_full()

        self.assertIs(result, mock.sentinel.report)
        self.assertEqual(
            set(self.fake.records),
            {
                "/Groups/_decisionos_codex",
                "/Users/_decisionos_codex",
                "/Groups/_decisionos_guardian",
                "/Users/_decisionos_guardian",
                "/Groups/_decisionos_broker",
                "/Users/_decisionos_broker",
            },
        )
        self.assertTrue(
            all(not allowed for allowed in self.fake.authentication_allowed.values())
        )
        self.assertEqual(
            directories,
            [
                (STATE_ROOT, 0o755, 0),
                (KEYS_DIRECTORY, 0o711, 0),
                (CONTROLLER_KEY_DIRECTORY, 0o750, 511),
                (BROKER_KEY_DIRECTORY, 0o750, 512),
                (BROKER_RUNTIME_DIRECTORY, 0o770, 512),
            ],
        )
        self.assertEqual(
            [value[0] for value in files],
            [CONTROLLER_KEY_PATH, BROKER_KEY_PATH, RECEIPT_PATH],
        )
        self.assertEqual(files[0][1], files[1][1])
        self.assertEqual(len(files[0][1]), AUTHENTICATION_KEY_BYTES)
        self.assertEqual(files[0][2:], (0o440, 511))
        self.assertEqual(files[1][2:], (0o440, 512))
        self.assertEqual(files[2][2:], (0o444, 0))
        receipt = PrincipalReceipt.from_dict(json.loads(files[2][1]))
        self.assertEqual(receipt.authentication_key_sha256, KEY_HASH)

    def test_every_dscl_mutation_has_readback_before_next_mutation(self) -> None:
        self._run_full()
        calls = self.fake.calls
        mutation_indexes = [
            index
            for index, call in enumerate(calls)
            if call[:3] == (principal_module.DSCL, ".", "-create")
        ]
        for position, index in enumerate(mutation_indexes):
            next_index = (
                mutation_indexes[position + 1]
                if position + 1 < len(mutation_indexes)
                else len(calls)
            )
            self.assertTrue(
                any(
                    call[:3] == (principal_module.DSCL, ".", "-read")
                    and call[3] == calls[index][3]
                    for call in calls[index + 1 : next_index]
                ),
                calls[index],
            )

    def test_native_is_hidden_readback_is_normalized(self) -> None:
        parsed = principal_module._parse_dscl_record(
            b"dsAttrTypeNative:IsHidden: 1\nRecordName: _decisionos_codex\n"
        )

        self.assertEqual(parsed["IsHidden"], ("1",))

    def test_visibility_poll_does_not_retry_mutation(self) -> None:
        self.fake.delayed_attribute = (
            "/Users/_decisionos_codex",
            "NFSHomeDirectory",
        )
        self.fake.delayed_reads_remaining = 2

        self._run_full()

        command = (
            principal_module.DSCL,
            ".",
            "-create",
            "/Users/_decisionos_codex",
            "NFSHomeDirectory",
            "/var/empty",
        )
        self.assertEqual(self.fake.mutations.count(command), 1)

    def test_exact_prior_failure_point_stops_without_retry(self) -> None:
        self.fake.fail_command = (
            principal_module.DSCL,
            ".",
            "-create",
            "/Users/_decisionos_guardian",
            "NFSHomeDirectory",
            "/var/empty",
        )

        with self.assertRaisesRegex(
            PrincipalSeparationError, "eDSPermissionError"
        ) as raised:
            self._run_full()

        self.assertEqual(self.fake.mutations.count(self.fake.fail_command), 1)
        self.assertIn(
            '["/usr/bin/dscl",".","-create","/Users/_decisionos_guardian",'
            '"NFSHomeDirectory","/var/empty"]',
            str(raised.exception),
        )
        self.assertNotIn("/Users/_decisionos_broker", self.fake.records)

    def test_pwpolicy_disable_failure_is_not_retried(self) -> None:
        self.fake.fail_command = (
            principal_module.PWPOLICY,
            "-u",
            "_decisionos_guardian",
            "disableuser",
        )

        with self.assertRaisesRegex(
            PrincipalSeparationError, "password policy mutation failed"
        ):
            self._run_full()

        self.assertEqual(self.fake.mutations.count(self.fake.fail_command), 1)
        self.assertNotIn("/Users/_decisionos_broker", self.fake.records)

    def test_authentication_readback_can_settle_without_mutation_retry(self) -> None:
        self.fake.authentication_reads_before_disabled = 3

        self._run_full()

        for spec in PRINCIPAL_SPECS:
            command = (
                principal_module.PWPOLICY,
                "-u",
                spec.account_name,
                "disableuser",
            )
            self.assertEqual(self.fake.mutations.count(command), 1)

    def test_nonzero_authentication_readback_fails_even_if_text_says_denied(
        self,
    ) -> None:
        result = CommandResult(
            1,
            stdout=(
                b"User <_decisionos_codex> is not allowed to authenticate: "
                b"disabled\n"
            ),
        )
        with mock.patch.object(principal_module, "_run", return_value=result):
            with self.assertRaisesRegex(
                PrincipalSeparationError, "cannot be proved"
            ):
                principal_module._authentication_allowed("_decisionos_codex")

    def test_exact_pwpolicy_syntax_and_no_password_or_dseditgroup_mutation(self) -> None:
        self._run_full()

        for spec in PRINCIPAL_SPECS:
            self.assertIn(
                (
                    "/usr/bin/pwpolicy",
                    "-u",
                    spec.account_name,
                    "disableuser",
                ),
                self.fake.mutations,
            )
        self.assertFalse(
            any(
                call[0] == principal_module.DSCL
                and len(call) >= 5
                and call[4] == "Password"
                for call in self.fake.mutations
            )
        )
        self.assertFalse(
            any(call[0] == "/usr/sbin/dseditgroup" for call in self.fake.calls)
        )

    def test_every_directory_service_mutation_failure_stops_at_that_command(self) -> None:
        self._run_full()
        successful_mutations = tuple(self.fake.mutations)

        for failed_command in successful_mutations:
            with self.subTest(command=failed_command):
                self.fake = FakeProvisionDirectoryService()
                self.fake.fail_command = failed_command
                with self.assertRaises(PrincipalSeparationError):
                    self._run_full()
                self.assertEqual(self.fake.mutations[-1], failed_command)
                self.assertEqual(self.fake.mutations.count(failed_command), 1)

    def test_unexpected_presence_error_is_not_treated_as_absence(self) -> None:
        def unavailable(_arguments: tuple[str, ...]) -> CommandResult:
            return CommandResult(40, stderr=b"eDSPermissionError\n")

        with mock.patch.object(principal_module, "_run", side_effect=unavailable):
            with self.assertRaisesRegex(
                PrincipalSeparationError, "presence cannot be proved"
            ):
                principal_module._record_exists("/Users/example")

    def test_future_transaction_has_one_interaction_budget_and_no_auth_wrapper(self) -> None:
        self.assertEqual(PRIVILEGED_INTERACTION_BUDGET, 1)
        source = Path("decision_os/companion/principal_separation.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("osascript", source)
        self.assertNotIn("administrator privileges", source)

    def test_plan_pins_all_future_executables_and_syntax(self) -> None:
        plan = principal_separation_plan()

        self.assertEqual(
            plan["executable_paths"],
            [
                "/usr/bin/dscl",
                "/usr/bin/id",
                "/usr/bin/pwpolicy",
                "/usr/bin/python3",
                "/usr/bin/sudo",
                "/bin/test",
                "/usr/bin/touch",
                "/usr/bin/false",
            ],
        )
        self.assertEqual(
            plan["entrypoint_interpreter"],
            ["/usr/bin/python3", "-I", "-S"],
        )
        contract = plan["directory_service_contract"]
        self.assertEqual(contract["datasource"], ".")
        self.assertEqual(contract["mutation_retry"], "forbidden")
        self.assertEqual(
            contract["authentication_disable"],
            ["/usr/bin/pwpolicy", "-u", "<account>", "disableuser"],
        )


if __name__ == "__main__":
    unittest.main()
