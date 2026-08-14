#!/usr/bin/python3
"""One-shot GitHub-hosted macOS qualification/deployment capsule for F-01.

The capsule accepts no runtime input.  It qualifies a fixed GitHub Actions
environment without privilege, enters the accepted Slice 4A provisioner only
after qualification and focused tests pass, and always emits hash-bound
evidence.  It never accepts a protected-repository path and never changes a
repository ACL.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any, Sequence

from decision_os.companion.principal_separation import (
    PRINCIPAL_SPECS,
    RECEIPT_PATH,
    STATE_ROOT,
    principal_separation_plan,
)


SCHEMA = "decision-os-f01-slice4a-clean-macos-capsule-v0.1"
EXPECTED_REPOSITORY = "shin4141/decision-os-v13-loopkit"
EXPECTED_REF = "refs/heads/codex/13-154-f01-slice4a-clean-macos-capsule"
EVIDENCE_DIRECTORY = Path(
    "validation/f01_slice4a_clean_macos_capsule_run_evidence"
)
HOST_STATE_PATHS = (
    Path("/Library/Application Support/DecisionOS"),
    Path("/Library/Application Support/DecisionOS/F01PrincipalSeparation"),
    STATE_ROOT,
)
FIXED_ENVIRONMENT = {
    "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
    "LC_ALL": "C",
    "LANG": "C",
}
FOCUSED_TESTS = (
    "tests.test_companion_principal_separation",
    "tests.test_companion_broker_control",
    "tests.test_companion_broker_authority",
    "tests.test_companion_broker_apply",
)


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(_canonical_bytes(value))


def _run(
    arguments: Sequence[str],
    *,
    cwd: Path | None = None,
    maximum_output: int = 2_000_000,
) -> dict[str, Any]:
    completed = subprocess.run(
        list(arguments),
        cwd=cwd,
        env=FIXED_ENVIRONMENT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = completed.stdout[: maximum_output + 1]
    stderr = completed.stderr[: maximum_output + 1]
    truncated = len(stdout) > maximum_output or len(stderr) > maximum_output
    return {
        "arguments": list(arguments),
        "returncode": completed.returncode,
        "stdout": stdout[:maximum_output].decode("utf-8", "backslashreplace"),
        "stderr": stderr[:maximum_output].decode("utf-8", "backslashreplace"),
        "output_truncated": truncated,
    }


def _search_names(record_root: str, attribute: str, value: str) -> dict[str, Any]:
    result = _run(
        (
            "/usr/bin/dscl",
            ".",
            "-search",
            record_root,
            attribute,
            value,
        )
    )
    names: list[str] = []
    if result["returncode"] == 0:
        for line in result["stdout"].splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith((attribute, "(", ")")):
                name = stripped.split()[0]
                if name not in names:
                    names.append(name)
    return {
        "record_root": record_root,
        "attribute": attribute,
        "value": value,
        "returncode": result["returncode"],
        "record_names": sorted(names),
        "stderr": result["stderr"],
        "output_truncated": result["output_truncated"],
    }


def _workspace_acl(workspace: Path) -> dict[str, Any]:
    result = _run(("/bin/ls", "-ledn", str(workspace)))
    lines = result["stdout"].splitlines()
    entries = [
        line.strip()
        for line in lines[1:]
        if re.match(r"^\s*\d+:\s", line)
    ]
    return {
        "path": str(workspace),
        "returncode": result["returncode"],
        "acl_entries": entries,
        "listing": result["stdout"],
        "stderr": result["stderr"],
        "output_truncated": result["output_truncated"],
    }


def _runner_identity() -> tuple[dict[str, Any], list[str]]:
    issues: list[str] = []
    sw_version = _run(("/usr/bin/sw_vers", "-productVersion"))
    sw_build = _run(("/usr/bin/sw_vers", "-buildVersion"))
    boot_session = _run(("/usr/sbin/sysctl", "-n", "kern.bootsessionuuid"))
    platform_record = _run(
        ("/usr/sbin/ioreg", "-rd1", "-c", "IOPlatformExpertDevice")
    )
    host_name = _run(("/bin/hostname",))
    for label, result in (
        ("product version", sw_version),
        ("build version", sw_build),
        ("boot session", boot_session),
        ("platform record", platform_record),
        ("host name", host_name),
    ):
        if result["returncode"] != 0 or not result["stdout"].strip():
            issues.append(f"Runner {label} could not be read exactly.")
    private_components = (
        boot_session["stdout"].strip(),
        platform_record["stdout"],
        host_name["stdout"].strip(),
        os.environ.get("GITHUB_RUN_ID", ""),
        os.environ.get("GITHUB_RUN_ATTEMPT", ""),
    )
    fingerprint = hashlib.sha256(
        "\0".join(private_components).encode("utf-8")
    ).hexdigest()
    identity = {
        "provider": "github-hosted-macos",
        "product_version": sw_version["stdout"].strip(),
        "build_version": sw_build["stdout"].strip(),
        "architecture": platform.machine(),
        "runner_name": os.environ.get("RUNNER_NAME"),
        "runner_os": os.environ.get("RUNNER_OS"),
        "runner_arch": os.environ.get("RUNNER_ARCH"),
        "github_repository": os.environ.get("GITHUB_REPOSITORY"),
        "github_ref": os.environ.get("GITHUB_REF"),
        "github_sha": os.environ.get("GITHUB_SHA"),
        "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        "github_run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "ephemeral_identity_sha256": fingerprint,
        "raw_platform_identifiers_persisted": False,
    }
    return identity, issues


def _clean_host_qualification(workspace: Path) -> dict[str, Any]:
    identity, issues = _runner_identity()
    if platform.system() != "Darwin":
        issues.append("The candidate is not macOS.")
    if os.geteuid() == 0:
        issues.append("Clean-host qualification must run unprivileged.")
    if os.environ.get("GITHUB_ACTIONS") != "true":
        issues.append("The candidate is not a GitHub-hosted Actions job.")
    if os.environ.get("GITHUB_REPOSITORY") != EXPECTED_REPOSITORY:
        issues.append("The GitHub repository identity is outside the capsule.")
    if os.environ.get("GITHUB_REF") != EXPECTED_REF:
        issues.append("The GitHub ref identity is outside the capsule.")

    repository_head = _run(("/usr/bin/git", "rev-parse", "HEAD"), cwd=workspace)
    if (
        repository_head["returncode"] != 0
        or repository_head["stdout"].strip() != os.environ.get("GITHUB_SHA")
    ):
        issues.append("Checked-out repository identity does not equal GITHUB_SHA.")

    principal_names: dict[str, Any] = {}
    numeric_identities: dict[str, Any] = {}
    for spec in PRINCIPAL_SPECS:
        user = _search_names("/Users", "RecordName", spec.account_name)
        group = _search_names("/Groups", "RecordName", spec.private_group_name)
        principal_names[spec.role] = {"user": user, "group": group}
        if user["returncode"] != 0 or user["record_names"]:
            issues.append(f"The fixed {spec.role} user name is not free.")
        if group["returncode"] != 0 or group["record_names"]:
            issues.append(f"The fixed {spec.role} group name is not free.")

        uid = _search_names("/Users", "UniqueID", str(spec.unique_id))
        gid = _search_names(
            "/Groups", "PrimaryGroupID", str(spec.private_group_id)
        )
        numeric_identities[spec.role] = {"uid": uid, "gid": gid}
        if uid["returncode"] != 0 or uid["record_names"]:
            issues.append(f"The fixed {spec.role} UID is not free.")
        if gid["returncode"] != 0 or gid["record_names"]:
            issues.append(f"The fixed {spec.role} GID is not free.")

    host_state = {str(path): path.exists() or path.is_symlink() for path in HOST_STATE_PATHS}
    if any(host_state.values()):
        issues.append("Prior DecisionOS Slice 4A host state is present.")

    acl = _workspace_acl(workspace)
    if acl["returncode"] != 0 or acl["acl_entries"]:
        issues.append("The candidate checkout has inherited ACL authority.")

    plan = principal_separation_plan()
    if plan["protected_repository_acl_installed"] is not False:
        issues.append("The accepted Slice 4A plan unexpectedly installs an ACL.")
    if plan["sole_writer_claimed"] is not False:
        issues.append("The accepted Slice 4A plan unexpectedly claims sole writer.")

    return {
        "schema": SCHEMA,
        "phase": "clean_host_qualification",
        "passed": not issues,
        "gate": "GO" if not issues else "HOLD",
        "status": "PASS_CLEAN_HOST" if not issues else "HOLD_CANDIDATE_NOT_CLEAN",
        "issues": issues,
        "runner_identity": identity,
        "effective_uid": os.geteuid(),
        "principal_names": principal_names,
        "numeric_identities": numeric_identities,
        "host_state_paths_present": host_state,
        "workspace_acl": acl,
        "protected_repository_acl_installed": False,
        "sole_writer_claimed": False,
        "host_attempt_1_inherited": False,
        "mutation_attempted": False,
        "privileged_execution_attempted": False,
    }


def _post_deployment_observation(workspace: Path) -> dict[str, Any]:
    issues: list[str] = []
    principals: dict[str, Any] = {}
    numeric_identities: dict[str, Any] = {}
    for spec in PRINCIPAL_SPECS:
        user = _search_names("/Users", "RecordName", spec.account_name)
        group = _search_names("/Groups", "RecordName", spec.private_group_name)
        principals[spec.role] = {"user": user, "group": group}
        if user["returncode"] != 0 or user["record_names"] != [spec.account_name]:
            issues.append(f"The deployed {spec.role} user is not exact.")
        if group["returncode"] != 0 or group["record_names"] != [spec.private_group_name]:
            issues.append(f"The deployed {spec.role} group is not exact.")

        uid = _search_names("/Users", "UniqueID", str(spec.unique_id))
        gid = _search_names(
            "/Groups", "PrimaryGroupID", str(spec.private_group_id)
        )
        numeric_identities[spec.role] = {"uid": uid, "gid": gid}
        if uid["returncode"] != 0 or uid["record_names"] != [spec.account_name]:
            issues.append(f"The deployed {spec.role} UID binding is not exact.")
        if gid["returncode"] != 0 or gid["record_names"] != [spec.private_group_name]:
            issues.append(f"The deployed {spec.role} GID binding is not exact.")

    host_state = {str(path): path.exists() or path.is_symlink() for path in HOST_STATE_PATHS}
    if not all(host_state.values()):
        issues.append("The deployed DecisionOS Slice 4A host-state tree is incomplete.")
    if not RECEIPT_PATH.is_file() or RECEIPT_PATH.is_symlink():
        issues.append("The deployed identity receipt is not one regular non-symlink file.")

    acl = _workspace_acl(workspace)
    if acl["returncode"] != 0 or acl["acl_entries"]:
        issues.append("The deployment changed or inherited checkout ACL authority.")

    return {
        "schema": SCHEMA,
        "phase": "post_deployment_observation",
        "passed": not issues,
        "gate": "PASS" if not issues else "HOLD",
        "issues": issues,
        "effective_uid": os.geteuid(),
        "principals": principals,
        "numeric_identities": numeric_identities,
        "host_state_paths_present": host_state,
        "receipt_present": RECEIPT_PATH.is_file() and not RECEIPT_PATH.is_symlink(),
        "workspace_acl": acl,
        "protected_repository_acl_installed": False,
        "sole_writer_claimed": False,
        "mutation_attempted_by_observer": False,
    }


def _finalize_manifest(evidence_directory: Path) -> None:
    manifest_path = evidence_directory / "SHA256SUMS.txt"
    entries: list[str] = []
    for path in sorted(evidence_directory.iterdir(), key=lambda item: item.name):
        if path == manifest_path or not path.is_file():
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(f"{digest}  {path.name}")
    manifest_path.write_text("\n".join(entries) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 1:
        print("This capsule accepts no runtime arguments.", file=sys.stderr)
        return 64
    workspace_value = os.environ.get("GITHUB_WORKSPACE")
    workspace = Path(workspace_value).resolve() if workspace_value else Path.cwd().resolve()
    evidence_directory = workspace / EVIDENCE_DIRECTORY
    evidence_directory.mkdir(parents=True, exist_ok=False)
    status: dict[str, Any] = {
        "schema": SCHEMA,
        "phase_1_entered": True,
        "phase_1_passed": False,
        "phase_2_entered": False,
        "deployment_passed": False,
        "post_deployment_passed": False,
        "tests_passed": False,
        "final_gate": "HOLD",
    }
    exit_code = 1
    try:
        qualification = _clean_host_qualification(workspace)
        _write_json(evidence_directory / "01_clean_host_qualification.json", qualification)
        status["phase_1_passed"] = qualification["passed"]
        if not qualification["passed"]:
            status["failure_boundary"] = "clean_host_qualification"
            exit_code = 3
            return exit_code

        plan = principal_separation_plan()
        _write_json(evidence_directory / "02_exact_deployment_plan.json", plan)

        test_command = (
            sys.executable,
            "-m",
            "unittest",
            "-v",
            *FOCUSED_TESTS,
        )
        test_result = _run(test_command, cwd=workspace)
        (evidence_directory / "03_focused_tests_stdout.txt").write_text(
            test_result["stdout"], encoding="utf-8"
        )
        (evidence_directory / "03_focused_tests_stderr.txt").write_text(
            test_result["stderr"], encoding="utf-8"
        )
        _write_json(
            evidence_directory / "03_focused_tests_result.json",
            {
                "arguments": test_result["arguments"],
                "returncode": test_result["returncode"],
                "output_truncated": test_result["output_truncated"],
                "test_modules": list(FOCUSED_TESTS),
            },
        )
        status["tests_passed"] = (
            test_result["returncode"] == 0 and not test_result["output_truncated"]
        )
        if not status["tests_passed"]:
            status["failure_boundary"] = "focused_tests"
            exit_code = 4
            return exit_code

        status["phase_2_entered"] = True
        deploy_command = (
            "/usr/bin/sudo",
            "-n",
            "/usr/bin/python3",
            "-I",
            "-S",
            str(workspace / "decision_os/companion/principal_separation.py"),
            "provision",
        )
        deploy_result = _run(deploy_command, cwd=workspace)
        (evidence_directory / "04_deployment_stdout.json").write_text(
            deploy_result["stdout"], encoding="utf-8"
        )
        (evidence_directory / "04_deployment_stderr.txt").write_text(
            deploy_result["stderr"], encoding="utf-8"
        )
        _write_json(
            evidence_directory / "04_deployment_result.json",
            {
                "arguments": deploy_result["arguments"],
                "returncode": deploy_result["returncode"],
                "output_truncated": deploy_result["output_truncated"],
                "privileged_prompt_allowed": False,
                "privileged_retry_performed": False,
            },
        )
        status["deployment_passed"] = (
            deploy_result["returncode"] == 0
            and not deploy_result["output_truncated"]
        )

        post_observation = _post_deployment_observation(workspace)
        _write_json(
            evidence_directory / "05_post_deployment_observation.json",
            post_observation,
        )
        status["post_deployment_passed"] = post_observation["passed"]
        if not status["deployment_passed"]:
            status["failure_boundary"] = "slice4a_deployment"
            exit_code = 5
            return exit_code
        if not status["post_deployment_passed"]:
            status["failure_boundary"] = "post_deployment_observation"
            exit_code = 6
            return exit_code

        try:
            deployment_report = json.loads(deploy_result["stdout"])
        except json.JSONDecodeError:
            status["failure_boundary"] = "deployment_report_json"
            exit_code = 7
            return exit_code
        if (
            type(deployment_report) is not dict
            or deployment_report.get("passed") is not True
            or deployment_report.get("protected_repository_acl_installed") is not False
            or deployment_report.get("sole_writer_claimed") is not False
        ):
            status["failure_boundary"] = "deployment_report_contract"
            exit_code = 8
            return exit_code

        status["final_gate"] = "PASS_SLICE4A_CLEAN_HOST_DEPLOYMENT_QUALIFIED"
        exit_code = 0
        return exit_code
    except Exception as exc:
        exit_code = 9
        status["failure_boundary"] = "capsule_exception"
        _write_json(
            evidence_directory / "99_capsule_exception.json",
            {"exception_type": type(exc).__name__, "message": str(exc)},
        )
        return exit_code
    finally:
        status["capsule_exit_code"] = exit_code
        _write_json(evidence_directory / "00_capsule_status.json", status)
        _finalize_manifest(evidence_directory)


if __name__ == "__main__":
    raise SystemExit(main())
