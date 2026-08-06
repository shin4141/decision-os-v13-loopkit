"""Production fixation and future-authorized one-shot Creator-Live Cycle 006."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
from typing import Any, Callable, Mapping, Protocol

from decision_os.acceleration.codex_adapter import (
    CYCLE_006_CODEX_CLI_VERSION,
    CYCLE_006_CODEX_PATH,
    CYCLE_006_CODEX_RECOVERY_RECEIPT,
    CYCLE_006_CODEX_SHA256,
    CodexRuntimeIdentity,
    verify_cycle_006_codex_runtime_artifact,
)
from decision_os.acceleration.model import git_output
from decision_os.acceleration.model import repository_id
from decision_os.companion.field_notes_creator_live import (
    FieldNoteCreatorLiveA1CaptureCommitReceipt,
    FieldNoteCreatorLiveAttemptExistsError,
    FieldNoteCreatorLiveContractIdentity,
    FieldNoteCreatorLiveHistoricalBoundary,
    FieldNoteCreatorLiveProofRuntime,
    FieldNoteCreatorLiveRun2OutputIdentity,
    FieldNoteCreatorLiveTaskIdentity,
    FieldNoteCreatorLiveTerminalProjectionBinding,
    _A1_CAPTURE_COMMIT_AUTHORITY,
)
from decision_os.companion.field_notes_creator_live_candidate_v0_2 import (
    A3_WITNESS_SCHEMA,
    BOUNDARY_SCHEMA,
    CANDIDATE_DEVELOPER_INSTRUCTIONS,
    CANDIDATE_ID,
    COMPARISON_SCHEMA,
    COMPRESSION_SCHEMA,
    DEVELOPER_INSTRUCTIONS_SHA256,
    DIFF_SCHEMA,
    FIXED_SOURCE_IDENTITY,
    FIXED_TASK_IDENTITIES,
    INDEPENDENCE_SCHEMA,
    POST_A1_READBACK_FILENAME,
    POST_A1_SCHEMA,
    PROJECTION_SCHEMA,
    PUBLIC_BUNDLE_ASSEMBLER,
    PUBLIC_BUNDLE_SCHEMA,
    REDUCTION_CORE_STATEMENT,
    REDUCTION_MAP_SCHEMA,
    SOURCE_ISOLATION_SCHEMA,
    SOURCE_TOOL_NAME,
    WitnessBindingV02,
    bind_generated_witness_v0_2,
    WITNESS_SCHEMA,
    candidate_dynamic_tools,
    check_boundaries_v0_2,
    compression_receipt,
    dynamic_tool_manifest_sha256,
    issue_post_a1_gate_v0_2,
    load_fixed_source,
    persist_post_a1_readback_v0_2,
    project_public_after,
    public_safety,
    qualify_independence,
    read_post_a1_readback_v0_2,
    require_post_a1_gate_for_a2,
    verify_a3_winner_witness_v0_2,
    verify_fixed_tasks,
    verify_packaged_source_against_git,
)
from decision_os.companion.field_notes_creator_live_candidate import (
    verify_fixed_before as verify_candidate_v0_1_fixed_before,
)
from decision_os.companion.field_notes_creator_live_entrypoint import (
    _claim_from_verified_a3_audit,
    compile_run_2_output_artifact_audited,
)
from decision_os.companion.field_notes_creator_live_capture import (
    FieldNoteCreatorLiveA1CaptureBridge,
)
from decision_os.companion.field_notes_creator_live_reconnect import (
    creator_live_a2_target_from_readback,
    prepare_creator_live_a2_reconnect,
)
from decision_os.companion.field_notes_maturity_commit import (
    FieldNoteMaturityCommitRequest,
    commit_field_note_maturity,
)
from decision_os.companion.field_notes_maturity_ledger import (
    FieldNoteMaturityLedger,
)
from decision_os.companion.field_notes_maturity_review import (
    review_field_note_maturity,
)
from decision_os.companion.field_notes_model import canonical_json
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    assess_field_note_reuse,
)
from decision_os.companion.field_notes_whole_flow import (
    FieldNoteCreatorLiveAttempt,
    FieldNoteSourceRepositoryIdentity,
    FieldNoteWholeFlowEvidenceBundle,
    FieldNoteWholeFlowRunIdentity,
    _a1_evidence_sha256,
    build_portable_candidate_warehouse_manifest,
    verify_field_note_whole_flow,
)
from decision_os.companion.guided_intake import (
    GuidedIntakeStore,
    _quoted_payload_boundary,
    canonical_json as guided_canonical_json,
)


CYCLE_NUMBER = "006"
CYCLE_KEY = "cycle-006"
IMPLEMENTATION_AUTHORIZATION_OBSERVED_AT = "2026-08-06T00:50:00Z"
LIVE_START_AUTHORIZATION_OBSERVED_AT: None = None

EXPECTED_REPOSITORY = Path("/Users/sn/Documents/v13/decision-os-v13-loopkit")
EXPECTED_REMOTE = "https://github.com/shin4141/decision-os-v13-loopkit.git"

CONTRACT_FILENAME = (
    "Decision_OS_Ordinary_User_Path_Contract_v0.1_APPROVED_CANDIDATE.md"
)
EXPECTED_CONTRACT_PROFILE = "ORDINARY_USER_PATH_CONTRACT_APPROVED_CANDIDATE_V0_1"
EXPECTED_CONTRACT_TITLE = "Ordinary User Path Contract v0.1 — APPROVED CANDIDATE"
EXPECTED_CONTRACT_BYTES = 11_039
EXPECTED_CONTRACT_SHA256 = (
    "519bd39305af1a3a7cc35e61e1b9cfc742c5723d0cc64d0d970b070d0e65068e"
)
EXPECTED_WRAPPER_BYTES = 11_946
EXPECTED_WRAPPER_SHA256 = (
    "c3de6236a450666d8a8ef59a8f8db303bf4654cc9cb20d6ab816f3066177b11e"
)
EXPECTED_INTERPRETATION_SHA256 = (
    "7503f4b01c7c05c9ec3aed8855c9fd538c66b9b3b38840f423ec41c2101f4dd7"
)
EXPECTED_EXECUTION_AUTHORITY = "INTERPRETATION_ONLY"
EXPECTED_FREEZE_AUTHORITY = "IMMUTABLE_INTERPRETATION_ONLY"
EXPECTED_GATE = "CLEAR ENOUGH TO FREEZE"
RUNTIME_MIGRATION_AS_OF = "2026-08-07"
FORWARD_RUNTIME_CHARTER_PATH = (
    "validation/a7_creator_live_whole_flow_reentry_charter_delta_v1_1.md"
)
FORWARD_RUNTIME_CHARTER_SHA256 = (
    "dade3a6994e0814ae50cba7b412726e9d4a65f94c5c214b1d62bc32c3a89203d"
)

EXPECTED_RUNTIME = {
    "provider": "openai",
    "account": "ChatGPT",
    "model": "gpt-5.6-sol",
    "reasoning_effort": "ultra",
    "service_tier": "priority",
    "codex_cli_version": CYCLE_006_CODEX_CLI_VERSION,
    "codex_binary_sha256": CYCLE_006_CODEX_SHA256,
    "runtime_as_of": RUNTIME_MIGRATION_AS_OF,
    "artifact_custody": "PRESERVED_CONTENT_ADDRESSED",
    "sandbox": "read-only",
    "model_sandbox_network": False,
    "provider_transport_required": True,
    "fresh_ephemeral_thread_per_run": True,
    "repository_cwd": "canonical-selected-repository",
}

EXPECTED_CODEX_RUNTIME = CodexRuntimeIdentity(
    model=EXPECTED_RUNTIME["model"],
    reasoning_effort=EXPECTED_RUNTIME["reasoning_effort"],
    service_tier=EXPECTED_RUNTIME["service_tier"],
    codex_cli_version=EXPECTED_RUNTIME["codex_cli_version"],
    account_type="chatgpt",
)

_A3_OVERLAY_FILENAME = "candidate-v0.2-a3-witness-verification.json"
_TURN_START_INTENT_SCHEMA = (
    "decision-os.creator-live-cycle-006-turn-start-intent.v0.1"
)
_TURN_START_SCHEMA = "decision-os.creator-live-cycle-006-turn-start.v0.1"
_TURN_START_INTENT_FILENAMES = (
    "candidate-v0.2-run-1-turn-start-intent.json",
    "candidate-v0.2-run-2-turn-start-intent.json",
)
_TURN_START_FILENAMES = (
    "candidate-v0.2-run-1-turn-start.json",
    "candidate-v0.2-run-2-turn-start.json",
)

CYCLE_005_JOURNAL_SHA256 = (
    "1de2e998804f5fb694707846b7deb0dc9d8b5f9cfc6027ad0210ddc270029322"
)
CYCLE_005_ANCHOR_SHA256 = (
    "e246757a7ba98849a6b4a694ababf473dc1a98baf1fc1ce0ea7daa3a6e7e8610"
)
CYCLE_005_READBACK_SHA256 = (
    "481be90dc8751bda3d7b00714f5a0c650230dffa8974a1332881ce42c127710f"
)
CYCLE_005_TERMINAL = (
    "FAILED",
    "A3_REUSE",
    "A3_EXACT_STRUCTURE_MISSING",
)

BEHAVIOR_SUITE_SHA256 = (
    "655fab6e1de937cc0057af2e5236ce38f07bb19deeb97143655082b2d45522b6"
)
BEHAVIOR_RUBRIC_SHA256 = (
    "553b372340570a211969588fd0114a497846c493171fa9e75494ce8965c705a1"
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PROOF_ID_PREFIX = "proof_a7_creator_live_cycle_006_"

_SCHEMA_FILES: tuple[tuple[str, str, str], ...] = (
    (
        "schema/creator_live_agents_source_isolation_v0_1.schema.json",
        SOURCE_ISOLATION_SCHEMA,
        "882c1a9b15a86bb12e278239495821175935a9d05e306a7132674ff33f31b94a",
    ),
    (
        "schema/creator_live_agents_independence_v0_1.schema.json",
        INDEPENDENCE_SCHEMA,
        "0da8b08aa061e18bd3247c1e54f3eac89dfb40caea8b65bb01bee8d4eb0550f8",
    ),
    (
        "schema/creator_live_agents_post_a1_gate_v0_2.schema.json",
        POST_A1_SCHEMA,
        "efda4d2c4ec1eb75d0d1ed9626c79ceb73e376f57699f902c3527a95361470eb",
    ),
    (
        "schema/creator_live_agents_before_after_public_bundle_v0_2.schema.json",
        PUBLIC_BUNDLE_SCHEMA,
        "4f46c0f64218cd0ed17ad556de9bdad04902252f5bb368debe2259f3566203d2",
    ),
    (
        "schema/creator_live_agents_common_before_comparison_v0_1.schema.json",
        COMPARISON_SCHEMA,
        "6debd4876efed92266bda4614b9e5c49ef5f31462d79d4d743e74446689b5d6d",
    ),
    (
        "schema/creator_live_agents_reduction_boundary_map_v0_1.schema.json",
        REDUCTION_MAP_SCHEMA,
        "8ca542055dfa663302d22ca31f19e4a68fa44077e4f73b2cc2b636f71bf4893e",
    ),
)

_CANDIDATE_V01_FILES: tuple[tuple[str, str], ...] = (
    ("decision_os/companion/field_notes_creator_live_candidate.py", "dcbfa65c97db298b7813190b0cde0a357eb9e2f8ce1e8eaff83ea767176ab0c7"),
    ("prompts/creator_live_agents_before_after_v0_1_run_1.txt", "b5109c7c8b3eff094542f494e8835a1e2b1819e7007bd55575bb51a94f63844a"),
    ("prompts/creator_live_agents_before_after_v0_1_run_2.txt", "7bf74ab01cd1e8f28bee3e54f2810801814fb675c665e3f54ccc5cc0a673b2da"),
    ("schema/creator_live_agents_before_after_public_bundle_v0_1.schema.json", "0f610bf829c82d776d624e4be2c526d08a504529b989e0ba85386a0bd3794aec"),
    ("tests/test_field_notes_creator_live_candidate.py", "2dc413eef7171f7d7b547a56429fb0a2c240836a0b77ef64179d7965d05abfd8"),
    ("validation/a7_creator_live_whole_flow_reentry_charter_delta_v0_8.md", "cf4055fc099cb2bb1eefbf59c9be9fc454abbca92e6e233147a7a5fb7d28a979"),
    ("validation/fixtures/creator_live_agents_before_after_v0_1/behavior/01-human-seat-retention.json", "88caa148aac74ffb2e10265d92ef0faf172831b5efc9274d8a27e4b9f67e2783"),
    ("validation/fixtures/creator_live_agents_before_after_v0_1/behavior/02-unauthorized-authority.json", "6930be3443b30471c302e27a2d2932349aba8572ee3421f3ea88f0eafa8ba535"),
    ("validation/fixtures/creator_live_agents_before_after_v0_1/behavior/03-missing-prerequisite-stop-hold.json", "cf70f9fd6b870c841885b604e432d9a516093ae634cf50c89e260b1611eb4c7e"),
    ("validation/fixtures/creator_live_agents_before_after_v0_1/behavior/04-evidence-provenance.json", "281074ecd2fd14da0fee416c4cbe55ad6c20a856cf2f4b40c952f1f13fe6a2f9"),
    ("validation/fixtures/creator_live_agents_before_after_v0_1/behavior/05-handoff-ownership.json", "f82f4811abaaf721dacc4458692e0f3e27d8ade7f89265ea7d20ec410b65f6fd"),
    ("validation/fixtures/creator_live_agents_before_after_v0_1/behavior/06-routine-cleanup.json", "bfd46d541fddeaab9995717584427caeec688bcb4829009e4402a9eaefe2215f"),
    ("validation/fixtures/creator_live_agents_before_after_v0_1/behavior/07-execution-agent-routing.json", "8bee987a202d53f5a88811d7b3fc43e12b21563f8697796c18b212a4e49c5701"),
    ("validation/fixtures/creator_live_agents_before_after_v0_1/behavior/08-forward-only-change.json", "f63a220641c6891013b7057d41c169454e08b6cec9fdb58da792068354586f9f"),
    ("validation/fixtures/creator_live_agents_before_after_v0_1/behavior/09-rollback-preservation.json", "3790bdc35f14b0d66dc2bfbc8f3cd96b3a6fdd221e609515fe20313b35712e5c"),
    ("validation/fixtures/creator_live_agents_before_after_v0_1/behavior/10-conflicting-instructions.json", "aaa32b693aa181748657545d238dcc6addce639cdfa184253eb3b60e3522c619"),
    ("validation/fixtures/creator_live_agents_before_after_v0_1/behavior/manifest.json", BEHAVIOR_SUITE_SHA256),
    ("validation/fixtures/creator_live_agents_before_after_v0_1/behavior/rubric.json", BEHAVIOR_RUBRIC_SHA256),
)

_CANDIDATE_V02_FILES: tuple[tuple[str, str], ...] = (
    ("decision_os/companion/candidate_inputs/creator_live_agents_before_after_v0_2/AGENTS.md", "e856160413a9d47622779dede6a2eeca9fd027284d815b155ab6e323a74863db"),
    ("decision_os/companion/field_notes_creator_live_candidate_v0_2.py", "4d11eb89b4d0e0de8bfbd7330923612db883d61a0b7477119758fb539ed5917a"),
    ("prompts/creator_live_agents_before_after_v0_2_run_1.txt", "2ed80098fb169313b13c36dddfd69a3ab487a4fe31d8474889cff7ba441b09e2"),
    ("prompts/creator_live_agents_before_after_v0_2_run_2.txt", "1a67c3677ce8c73b4259317130e689dfefa1827fffe3abe377af861da8ec4bdb"),
    ("schema/creator_live_agents_before_after_public_bundle_v0_2.schema.json", "4f46c0f64218cd0ed17ad556de9bdad04902252f5bb368debe2259f3566203d2"),
    ("schema/creator_live_agents_common_before_comparison_v0_1.schema.json", "6debd4876efed92266bda4614b9e5c49ef5f31462d79d4d743e74446689b5d6d"),
    ("schema/creator_live_agents_independence_v0_1.schema.json", "0da8b08aa061e18bd3247c1e54f3eac89dfb40caea8b65bb01bee8d4eb0550f8"),
    ("schema/creator_live_agents_post_a1_gate_v0_2.schema.json", "efda4d2c4ec1eb75d0d1ed9626c79ceb73e376f57699f902c3527a95361470eb"),
    ("schema/creator_live_agents_reduction_boundary_map_v0_1.schema.json", "8ca542055dfa663302d22ca31f19e4a68fa44077e4f73b2cc2b636f71bf4893e"),
    ("schema/creator_live_agents_source_isolation_v0_1.schema.json", "882c1a9b15a86bb12e278239495821175935a9d05e306a7132674ff33f31b94a"),
    ("tests/test_field_notes_creator_live_candidate_v0_2.py", "ee2a049fdf6cd6778de57bd4b29161ceb16e8dbcd5688ea68b5c3785958171d7"),
    ("validation/a7_creator_live_whole_flow_reentry_charter_delta_v0_9.md", "ce9b60a1c54b7aff7a6083687ed4ffe8b52a7011d7eac64c339d525265c670b6"),
    ("validation/fixtures/creator_live_agents_before_after_v0_2/comparison_manifest_expected.json", "b35f3c218400ba5814407ea3756829e878154d8443aae52c680a8641e3e8b6a3"),
    ("validation/fixtures/creator_live_agents_before_after_v0_2/reduction_boundary_map_expected.json", "2f1c43d02df766e7a67002e1df56358856acad58974e2a13bd380b17cf04a3b1"),
    ("validation/fixtures/creator_live_agents_before_after_v0_2/source_isolation_transcripts.json", "cfa36dd1d51e697ec282711537937419c5475d922d4ba38818e17ca87a0255fa"),
)


class _Controller(Protocol):
    def snapshot(self) -> dict[str, Any]: ...


class CreatorLiveCycle006Error(RuntimeError):
    """One Cycle 006 start request failed before any live activity."""

    def __init__(self, code: str, *, http_status: int = 409) -> None:
        super().__init__(code)
        self.code = code
        self.http_status = http_status


@dataclass(frozen=True)
class CreatorLiveCycle006Spec:
    repository: Path = EXPECTED_REPOSITORY
    remote: str = EXPECTED_REMOTE
    runtime_root: Path | None = None
    codex_executable: Path = CYCLE_006_CODEX_PATH
    live_start_authorization_observed_at: str | None = (
        LIVE_START_AUTHORIZATION_OBSERVED_AT
    )
    runtime: CodexRuntimeIdentity = EXPECTED_CODEX_RUNTIME

    @property
    def storage_root(self) -> Path:
        return self.repository / ".decision-os/field-notes/proofs/cycle-006"


@dataclass(frozen=True)
class CreatorLiveCycle006P0Result:
    ready: bool
    failure_code: str | None
    binding: dict[str, Any] | None
    launch_binding_sha256: str | None


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _cycle_006_codex_cli_version(executable: Path) -> str:
    """Verify the fixed artifact without starting app-server or a model."""

    return verify_cycle_006_codex_runtime_artifact(executable)


def _strict_object(raw: bytes, label: str) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in items:
            if key in result:
                raise ValueError(f"{label} contains a duplicate field.")
            result[key] = item
        return result

    try:
        value = json.loads(raw, object_pairs_hook=pairs)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not strict JSON.") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} is not an object.")
    return value


def _read_regular_bytes(target: Path, code: str) -> bytes:
    if not target.is_file() or target.is_symlink():
        raise ValueError(code)
    try:
        return target.read_bytes()
    except OSError as exc:
        raise ValueError(code) from exc


def _require_exact_lineage(
    groups: Mapping[str, tuple[Any, ...]],
) -> None:
    """Reject any projected identity group that is not exactly one value."""

    for values in groups.values():
        if len(values) < 2 or any(value != values[0] for value in values[1:]):
            raise ValueError("P0_CONTRACT_LINEAGE_MISMATCH")


def _run_git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=repository,
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    if completed.returncode != 0:
        raise ValueError("P0_GIT_IDENTITY_UNAVAILABLE")
    return completed.stdout.strip()


def _git_diff_clean(repository: Path, *, cached: bool) -> bool:
    arguments = ["git", "diff", "--quiet"]
    if cached:
        arguments.append("--cached")
    completed = subprocess.run(
        arguments,
        cwd=repository,
        capture_output=True,
        check=False,
        timeout=10,
    )
    if completed.returncode not in {0, 1}:
        raise ValueError("P0_GIT_IDENTITY_UNAVAILABLE")
    return completed.returncode == 0


def product_tree_sha256(runtime_root: Path) -> str:
    """Hash one exact Decision OS product tree without following symlinks."""

    package = runtime_root / "decision_os"
    if not package.is_dir() or package.is_symlink():
        raise ValueError("P0_PRODUCT_TREE_UNAVAILABLE")
    files: list[Path] = []
    for path in package.rglob("*"):
        relative = path.relative_to(runtime_root)
        if "__pycache__" in relative.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError("P0_PRODUCT_TREE_SYMLINK")
        if path.is_file():
            files.append(path)
    rows = [
        f"{_sha256(path.read_bytes())}  {path.relative_to(runtime_root).as_posix()}\n"
        for path in sorted(
            files,
            key=lambda item: item.relative_to(runtime_root).as_posix().encode("utf-8"),
        )
    ]
    return _sha256("".join(rows).encode("utf-8"))


def _runtime_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _manifest_identity(
    repository: Path,
    files: tuple[tuple[str, str], ...],
    mismatch_code: str,
) -> str:
    rows: list[str] = []
    for relative, expected in files:
        target = repository / relative
        if (
            not target.is_file()
            or target.is_symlink()
            or _sha256(target.read_bytes()) != expected
        ):
            raise ValueError(mismatch_code)
        rows.append(f"{expected}  {relative}\n")
    return _sha256("".join(rows).encode("utf-8"))


def future_proof_identity(launch_binding_sha256: str) -> str:
    """Derive the sole future proof identity without allocating storage."""

    if not isinstance(launch_binding_sha256, str) or not _SHA256.fullmatch(
        launch_binding_sha256
    ):
        raise ValueError("LAUNCH_BINDING_INVALID")
    return _PROOF_ID_PREFIX + launch_binding_sha256


def _terminal_projection_binding(
    p0: CreatorLiveCycle006P0Result,
) -> FieldNoteCreatorLiveTerminalProjectionBinding:
    if p0.binding is None or p0.launch_binding_sha256 is None:
        raise ValueError("P0_TERMINAL_PROJECTION_BINDING_UNAVAILABLE")
    binding = p0.binding
    contract = binding["contract"]
    historical = binding["historical_boundary"]["cycle_005"]
    run_1 = binding["tasks"]["run_1"]
    run_2 = binding["tasks"]["run_2"]
    return FieldNoteCreatorLiveTerminalProjectionBinding.create(
        launch_binding_sha256=p0.launch_binding_sha256,
        contract_identity=FieldNoteCreatorLiveContractIdentity(
            profile=contract["profile"],
            title=contract["title"],
            source_byte_count=contract["source_byte_count"],
            source_sha256=contract["source_sha256"],
            wrapper_sha256=contract["wrapper_sha256"],
            interpretation_sha256=contract["interpretation_sha256"],
        ),
        ordinary_contract_execution_authority=contract[
            "ordinary_contract_execution_authority"
        ],
        guided_intake_freeze_authority=contract[
            "guided_intake_freeze_authority"
        ],
        implementation_authorization_observed_at=(
            IMPLEMENTATION_AUTHORIZATION_OBSERVED_AT
        ),
        run_1_task=FieldNoteCreatorLiveTaskIdentity(
            byte_count=run_1["utf8_byte_count"],
            sha256=run_1["sha256"],
        ),
        run_2_task=FieldNoteCreatorLiveTaskIdentity(
            byte_count=run_2["utf8_byte_count"],
            sha256=run_2["sha256"],
        ),
        historical_boundary=FieldNoteCreatorLiveHistoricalBoundary(
            cycle_key=historical["cycle_key"],
            state=historical["state"],
            failure_boundary=historical["failure_boundary"],
            failure_code=historical["failure_code"],
        ),
    )


def _persist_a3_overlay(
    root: Path,
    *,
    launch_binding_sha256: str,
    post_a1_readback_sha256: str,
    verification: Any,
) -> str:
    value = {
        "schema": "decision-os.creator-live-cycle-006-a3-overlay-receipt.v0.1",
        "candidate_id": CANDIDATE_ID,
        "launch_binding_sha256": launch_binding_sha256,
        "post_a1_readback_sha256": post_a1_readback_sha256,
        "verification": verification.as_dict(),
    }
    raw = canonical_json(value).encode("utf-8")
    target = root / _A3_OVERLAY_FILENAME
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        remaining = memoryview(raw)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("A3_OVERLAY_WRITE_INCOMPLETE")
            remaining = remaining[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    parent = os.open(root, os.O_RDONLY)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)
    observed = target.read_bytes()
    if observed != raw:
        raise ValueError("A3_OVERLAY_READBACK_MISMATCH")
    return _sha256(raw)


def _turn_start_binding(
    root: Path,
    *,
    proof_attempt_id: str,
    launch_binding_sha256: str,
    run_index: int,
    run_id: str,
) -> dict[str, Any]:
    if (
        not root.is_dir()
        or root.is_symlink()
        or not _SHA256.fullmatch(launch_binding_sha256)
        or proof_attempt_id != _PROOF_ID_PREFIX + launch_binding_sha256
        or run_index not in {1, 2}
        or not isinstance(run_id, str)
        or not run_id
        or len(run_id) > 256
        or "\x00" in run_id
    ):
        raise ValueError("CYCLE_006_TURN_START_IDENTITY_INVALID")
    return {
        "candidate_id": CANDIDATE_ID,
        "proof_attempt_id": proof_attempt_id,
        "launch_binding_sha256": launch_binding_sha256,
        "run_index": run_index,
        "run_id": run_id,
    }


def _persist_content_free_record(
    root: Path,
    filename: str,
    value: Mapping[str, Any],
    *,
    failure_code: str,
) -> None:
    raw = canonical_json(value).encode("utf-8")
    target = root / filename
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        remaining = memoryview(raw)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError(failure_code)
            remaining = remaining[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    parent = os.open(root, os.O_RDONLY)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)
    if target.is_symlink() or target.read_bytes() != raw:
        raise ValueError(failure_code)


def _require_exact_content_free_record(
    target: Path,
    expected: Mapping[str, Any],
) -> None:
    if not target.is_file() or target.is_symlink():
        raise ValueError("CYCLE_006_TURN_START_INTEGRITY_FAILURE")
    raw = target.read_bytes()
    value = _strict_object(raw, "Cycle 006 turn-start milestone")
    if value != expected or raw != canonical_json(expected).encode("utf-8"):
        raise ValueError("CYCLE_006_TURN_START_INTEGRITY_FAILURE")


def _persist_turn_start_intent(
    root: Path,
    *,
    proof_attempt_id: str,
    launch_binding_sha256: str,
    run_index: int,
    run_id: str,
) -> None:
    """Write ahead before the fixed task can reach provider transport."""

    binding = _turn_start_binding(
        root,
        proof_attempt_id=proof_attempt_id,
        launch_binding_sha256=launch_binding_sha256,
        run_index=run_index,
        run_id=run_id,
    )
    value = {
        "schema": _TURN_START_INTENT_SCHEMA,
        **binding,
        "milestone": "TASK_TRANSMISSION_INTENT",
    }
    _persist_content_free_record(
        root,
        _TURN_START_INTENT_FILENAMES[run_index - 1],
        value,
        failure_code="CYCLE_006_TURN_START_INTENT_PERSIST_FAILED",
    )


def _persist_turn_start(
    root: Path,
    *,
    proof_attempt_id: str,
    launch_binding_sha256: str,
    run_index: int,
    run_id: str,
) -> None:
    """Persist accepted activity only after its exact write-ahead intent."""

    binding = _turn_start_binding(
        root,
        proof_attempt_id=proof_attempt_id,
        launch_binding_sha256=launch_binding_sha256,
        run_index=run_index,
        run_id=run_id,
    )
    intent = {
        "schema": _TURN_START_INTENT_SCHEMA,
        **binding,
        "milestone": "TASK_TRANSMISSION_INTENT",
    }
    _require_exact_content_free_record(
        root / _TURN_START_INTENT_FILENAMES[run_index - 1],
        intent,
    )
    accepted = {
        "schema": _TURN_START_SCHEMA,
        **binding,
        "milestone": "TURN_START_ACCEPTED",
    }
    _persist_content_free_record(
        root,
        _TURN_START_FILENAMES[run_index - 1],
        accepted,
        failure_code="CYCLE_006_TURN_START_PERSIST_FAILED",
    )


def _turn_start_count(root: Path, readback: Any) -> int:
    """Read exact durable activity without inferring it from run allocation."""

    launch = readback.proof_attempt_id.removeprefix(_PROOF_ID_PREFIX)
    expected_runs = (readback.run_1, readback.run_2)
    accepted_present: list[bool] = []
    for run_index, (intent_filename, accepted_filename, run) in enumerate(
        zip(
            _TURN_START_INTENT_FILENAMES,
            _TURN_START_FILENAMES,
            expected_runs,
            strict=True,
        ),
        start=1,
    ):
        intent_target = root / intent_filename
        accepted_target = root / accepted_filename
        intent_exists = os.path.lexists(intent_target)
        accepted_exists = os.path.lexists(accepted_target)
        accepted_present.append(accepted_exists)
        if not intent_exists and not accepted_exists:
            continue
        if run is None or accepted_exists and not intent_exists:
            raise ValueError("CYCLE_006_TURN_START_INTEGRITY_FAILURE")
        binding = {
            "candidate_id": CANDIDATE_ID,
            "proof_attempt_id": readback.proof_attempt_id,
            "launch_binding_sha256": launch,
            "run_index": run_index,
            "run_id": run.run_id,
        }
        expected_intent = {
            "schema": _TURN_START_INTENT_SCHEMA,
            **binding,
            "milestone": "TASK_TRANSMISSION_INTENT",
        }
        _require_exact_content_free_record(intent_target, expected_intent)
        if not accepted_exists:
            raise ValueError("CYCLE_006_TURN_START_ACTIVITY_UNCERTAIN")
        expected_accepted = {
            "schema": _TURN_START_SCHEMA,
            **binding,
            "milestone": "TURN_START_ACCEPTED",
        }
        _require_exact_content_free_record(accepted_target, expected_accepted)
    if accepted_present[1] and not accepted_present[0]:
        raise ValueError("CYCLE_006_TURN_START_INTEGRITY_FAILURE")
    return sum(accepted_present)


class CreatorLiveCycle006Entrypoint:
    """Compute exact P0 and own the sole future-authorized attempt."""

    def __init__(
        self,
        controller: _Controller,
        *,
        spec: CreatorLiveCycle006Spec | None = None,
        now: Callable[[], str] | None = None,
        runtime_opener: Callable[..., FieldNoteCreatorLiveProofRuntime] = (
            FieldNoteCreatorLiveProofRuntime.open_attempt
        ),
        worker_factory: Callable[..., Any] = threading.Thread,
        runtime_version_probe: Callable[[Path], str] = (
            _cycle_006_codex_cli_version
        ),
        timeout_seconds: float = 900.0,
    ) -> None:
        self.controller = controller
        self.spec = spec or CreatorLiveCycle006Spec()
        self.now = now or (
            lambda: datetime.now(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z")
        )
        self.runtime_opener = runtime_opener
        self.worker_factory = worker_factory
        self.runtime_version_probe = runtime_version_probe
        self.timeout_seconds = float(timeout_seconds)
        self._lock = threading.RLock()
        self._runtime: FieldNoteCreatorLiveProofRuntime | None = None
        self._worker: Any = None
        self._starting = False
        self._active = False
        self._stage = "P0"
        self._terminal_state: str | None = None
        self._terminal_failure_code: str | None = None
        self._receipt_sha256: str | None = None
        self._manifest_sha256: str | None = None
        self._post_a1_readback_sha256: str | None = None
        self._a3_overlay_sha256: str | None = None
        self._runtime_verification_cache: tuple[
            tuple[Any, ...], str | None
        ] | None = None

    @property
    def mutation_blocked(self) -> bool:
        with self._lock:
            return self._starting or self._active

    def _require_runtime_binary_identity(self) -> None:
        # Status polling may reuse evidence while the complete stat identity is
        # unchanged.  Proof opening never does: re-read and re-probe here.
        failure_code = self._runtime_binary_failure_code(force=True)
        if failure_code is not None:
            raise CreatorLiveCycle006Error(failure_code)

    def _runtime_binary_cache_key(self) -> tuple[Any, ...]:
        try:
            observed = self.spec.codex_executable.lstat()
        except OSError:
            return (str(self.spec.codex_executable), "UNAVAILABLE")
        return (
            str(self.spec.codex_executable),
            observed.st_dev,
            observed.st_ino,
            observed.st_mode,
            observed.st_nlink,
            observed.st_size,
            observed.st_mtime_ns,
            observed.st_ctime_ns,
        )

    def _runtime_binary_failure_code(self, *, force: bool = False) -> str | None:
        before_key = self._runtime_binary_cache_key()
        with self._lock:
            if (
                not force
                and self._runtime_verification_cache is not None
                and self._runtime_verification_cache[0] == before_key
            ):
                return self._runtime_verification_cache[1]
        try:
            observed = self.runtime_version_probe(self.spec.codex_executable)
        except ValueError as exc:
            code = str(exc)
            failure_code = (
                code if code.startswith("P0_") else "P0_CODEX_CLI_UNAVAILABLE"
            )
        except Exception:
            failure_code = "P0_CODEX_CLI_UNAVAILABLE"
        else:
            failure_code = (
                "P0_CODEX_CLI_VERSION_MISMATCH"
                if observed != self.spec.runtime.codex_cli_version
                else None
            )
        after_key = self._runtime_binary_cache_key()
        if after_key != before_key:
            return "P0_CODEX_CLI_IDENTITY_CHANGED"
        with self._lock:
            self._runtime_verification_cache = (after_key, failure_code)
        return failure_code

    def _outer_gate_failure_code(self) -> str | None:
        """Validate non-proof outer gates in their required fail-closed order."""

        runtime_failure = self._runtime_binary_failure_code()
        if runtime_failure is not None:
            return runtime_failure
        if self.spec.live_start_authorization_observed_at is None:
            return "LIVE_START_AUTHORIZATION_ABSENT"
        return None

    @staticmethod
    def _git_common_dir(repository: Path) -> Path:
        value = _run_git(repository, "rev-parse", "--git-common-dir")
        path = Path(value)
        return (repository / path).resolve() if not path.is_absolute() else path

    def _contract_binding(
        self,
        *,
        repository: Path,
        common: Path,
        head: str,
        base_snapshot: Mapping[str, Any],
    ) -> dict[str, Any]:
        ordinary = base_snapshot.get("ordinary_contract")
        if not isinstance(ordinary, Mapping) or ordinary.get("state") != "FIXED":
            raise ValueError("P0_CONTRACT_NOT_FIXED")
        if ordinary.get("repository_identity") != head:
            raise ValueError("P0_CONTRACT_REPOSITORY_MISMATCH")
        if ordinary.get("execution_authority") != EXPECTED_EXECUTION_AUTHORITY:
            raise ValueError("P0_EXECUTION_AUTHORITY_MISMATCH")
        source = ordinary.get("source_identity")
        if not isinstance(source, Mapping) or (
            source.get("byte_size") != EXPECTED_CONTRACT_BYTES
            or source.get("sha256") != EXPECTED_CONTRACT_SHA256
            or source.get("profile") != EXPECTED_CONTRACT_PROFILE
            or source.get("title") != EXPECTED_CONTRACT_TITLE
        ):
            raise ValueError("P0_CONTRACT_SOURCE_MISMATCH")
        technical = ordinary.get("technical_details")
        if not isinstance(technical, Mapping) or (
            technical.get("wrapper_sha256") != EXPECTED_WRAPPER_SHA256
            or technical.get("interpretation_sha256")
            != EXPECTED_INTERPRETATION_SHA256
            or technical.get("gate") != EXPECTED_GATE
        ):
            raise ValueError("P0_CONTRACT_LINEAGE_MISMATCH")
        freeze = technical.get("freeze")
        if not isinstance(freeze, Mapping) or freeze.get("current") is not True:
            raise ValueError("P0_FREEZE_NOT_CURRENT")
        freeze_receipt = freeze.get("receipt")
        if not isinstance(freeze_receipt, Mapping) or (
            freeze_receipt.get("authority_state") != EXPECTED_FREEZE_AUTHORITY
            or freeze_receipt.get("product_commit") != head
            or freeze_receipt.get("current_gate") != EXPECTED_GATE
        ):
            raise ValueError("P0_FREEZE_AUTHORITY_MISMATCH")
        freeze_receipt_sha = freeze.get("receipt_sha256")
        frozen_sha = freeze.get("frozen_intake_sha256")
        preparation_receipt_sha = technical.get("preparation_receipt_sha256")
        if not isinstance(freeze_receipt_sha, str) or not _SHA256.fullmatch(
            freeze_receipt_sha
        ):
            raise ValueError("P0_FREEZE_RECEIPT_IDENTITY_INVALID")
        if not isinstance(preparation_receipt_sha, str) or not _SHA256.fullmatch(
            preparation_receipt_sha
        ):
            raise ValueError("P0_PREPARATION_RECEIPT_IDENTITY_INVALID")
        if not isinstance(frozen_sha, str) or not _SHA256.fullmatch(frozen_sha):
            raise ValueError("P0_FROZEN_INTAKE_IDENTITY_INVALID")

        guided_root = common / "decision-os/guided-intake-v0.1"
        guided_state = _strict_object(
            _read_regular_bytes(
                guided_root / "state.json",
                "P0_GUIDED_STATE_INVALID",
            ),
            "Guided Intake state",
        )
        guided_record = guided_state.get("record")
        if not isinstance(guided_record, Mapping):
            raise ValueError("P0_GUIDED_STATE_INVALID")
        if (
            guided_state.get("schema")
            != "decision-os-guided-intake-store-v0.1"
            or guided_record.get("schema")
            != "decision-os-guided-intake-state-v0.1"
            or guided_state.get("record_sha256")
            != _sha256(guided_canonical_json(dict(guided_record)))
        ):
            raise ValueError("P0_GUIDED_STATE_INVALID")
        requests = guided_record.get("requests")
        drafts = guided_record.get("drafts")
        freezes = guided_record.get("freezes")
        active_request_id = guided_record.get("active_request_id")
        active_draft_id = guided_record.get("active_draft_id")
        latest_freeze_id = guided_record.get("latest_freeze_id")
        if not all(isinstance(value, Mapping) for value in (requests, drafts, freezes)):
            raise ValueError("P0_GUIDED_STATE_INVALID")
        assert isinstance(requests, Mapping)
        assert isinstance(drafts, Mapping)
        assert isinstance(freezes, Mapping)
        guided_request = requests.get(active_request_id)
        guided_draft = drafts.get(active_draft_id)
        guided_freeze = freezes.get(latest_freeze_id)
        current_interpretation = guided_record.get("current_interpretation")
        if not all(
            isinstance(value, Mapping)
            for value in (
                guided_request,
                guided_draft,
                guided_freeze,
                current_interpretation,
            )
        ):
            raise ValueError("P0_GUIDED_STATE_INVALID")
        assert isinstance(guided_request, Mapping)
        assert isinstance(guided_draft, Mapping)
        assert isinstance(guided_freeze, Mapping)
        assert isinstance(current_interpretation, Mapping)
        current_chain_head = guided_record.get("event_chain_head")
        if not isinstance(current_chain_head, str) or not _SHA256.fullmatch(
            current_chain_head
        ):
            raise ValueError("P0_CURRENT_CHAIN_HEAD_INVALID")
        guided_store = GuidedIntakeStore(repository)
        with guided_store.transaction(write=False):
            strict_guided_record = guided_store.load_state()
            events = guided_store.read_events()
        if strict_guided_record != dict(guided_record):
            raise ValueError("P0_GUIDED_STATE_INVALID")
        if len(events) < 3:
            raise ValueError("P0_EVENT_CHAIN_INCOMPLETE")
        original_event = events[-3]
        previous_event = events[-2]
        current_event = events[-1]
        original_payload = original_event.get("payload")
        previous_payload = previous_event.get("payload")
        current_payload = current_event.get("payload")
        if not all(
            isinstance(value, Mapping)
            for value in (original_payload, previous_payload, current_payload)
        ):
            raise ValueError("P0_EVENT_CHAIN_RELATIONSHIP_INVALID")
        assert isinstance(original_payload, Mapping)
        assert isinstance(previous_payload, Mapping)
        assert isinstance(current_payload, Mapping)
        predecessor_head = freeze_receipt.get("event_chain_head")
        if (
            original_event.get("kind") != "ORIGINAL_REQUEST_CAPTURED"
            or previous_event.get("kind") != "PRO_DRAFT_IMPORTED"
            or current_event.get("event_hash") != current_chain_head
            or current_event.get("kind") != "INTAKE_FROZEN"
            or current_event.get("previous_event_hash") != predecessor_head
            or previous_event.get("event_hash") != predecessor_head
            or previous_event.get("previous_event_hash")
            != original_event.get("event_hash")
            or any(
                event.get("event_hash")
                != _sha256(
                    guided_canonical_json(
                        {
                            key: value
                            for key, value in event.items()
                            if key != "event_hash"
                        }
                    )
                )
                for event in (original_event, previous_event, current_event)
            )
        ):
            raise ValueError("P0_EVENT_CHAIN_RELATIONSHIP_INVALID")
        if (
            latest_freeze_id != freeze.get("freeze_id")
            or guided_freeze.get("freeze_id") != latest_freeze_id
            or current_payload.get("freeze_id") != latest_freeze_id
            or guided_freeze.get("receipt_sha256") != freeze_receipt_sha
            or current_payload.get("freeze_receipt_sha256")
            != freeze_receipt_sha
            or guided_freeze.get("sha256") != frozen_sha
            or current_payload.get("frozen_intake_sha256") != frozen_sha
        ):
            raise ValueError("P0_CONTRACT_LINEAGE_MISMATCH")
        freeze_receipt_bytes = _read_regular_bytes(
            guided_root / "receipts" / f"{freeze_receipt_sha}.json",
            "P0_FREEZE_RECEIPT_MISMATCH",
        )
        if (
            _sha256(freeze_receipt_bytes) != freeze_receipt_sha
            or _strict_object(freeze_receipt_bytes, "Freeze receipt")
            != dict(freeze_receipt)
        ):
            raise ValueError("P0_FREEZE_RECEIPT_MISMATCH")

        preparation_bytes = _read_regular_bytes(
            common
            / "decision-os/ordinary-user-path-v0.1/preparation-receipts"
            / f"{preparation_receipt_sha}.json",
            "P0_PREPARATION_RECEIPT_MISMATCH",
        )
        preparation = _strict_object(preparation_bytes, "Preparation receipt")
        if (
            _sha256(preparation_bytes) != preparation_receipt_sha
            or preparation.get("event_chain_head") != predecessor_head
            or preparation.get("implementation_authority_state") != "NONE"
            or preparation.get("repository_identity") != head
        ):
            raise ValueError("P0_PREPARATION_RECEIPT_MISMATCH")
        wrapper_identity = preparation.get("wrapper_identity")
        source_identity = preparation.get("source_identity")
        if (
            not isinstance(wrapper_identity, Mapping)
            or not isinstance(source_identity, Mapping)
            or wrapper_identity.get("sha256") != EXPECTED_WRAPPER_SHA256
            or wrapper_identity.get("byte_size") != EXPECTED_WRAPPER_BYTES
            or source_identity.get("sha256") != EXPECTED_CONTRACT_SHA256
            or source_identity.get("byte_size") != EXPECTED_CONTRACT_BYTES
        ):
            raise ValueError("P0_CONTRACT_BYTE_IDENTITY_MISMATCH")
        wrapper_bytes = _read_regular_bytes(
            guided_root
            / "original-requests"
            / f"{EXPECTED_WRAPPER_SHA256}.utf8",
            "P0_CONTRACT_WRAPPER_MISMATCH",
        )
        if (
            len(wrapper_bytes) != EXPECTED_WRAPPER_BYTES
            or _sha256(wrapper_bytes) != EXPECTED_WRAPPER_SHA256
        ):
            raise ValueError("P0_CONTRACT_WRAPPER_MISMATCH")
        boundary = _quoted_payload_boundary(wrapper_bytes.decode("utf-8"))
        if boundary is None:
            raise ValueError("P0_CONTRACT_SOURCE_BOUNDARY_MISSING")
        source_bytes = wrapper_bytes[
            boundary.payload_byte_start : boundary.payload_byte_end
        ]
        if (
            len(source_bytes) != EXPECTED_CONTRACT_BYTES
            or _sha256(source_bytes) != EXPECTED_CONTRACT_SHA256
            or boundary.byte_size != EXPECTED_CONTRACT_BYTES
            or boundary.sha256 != EXPECTED_CONTRACT_SHA256
        ):
            raise ValueError("P0_CONTRACT_SOURCE_BYTES_MISMATCH")
        draft_identity = preparation.get("draft_identity")
        if not isinstance(draft_identity, Mapping):
            raise ValueError("P0_CONTRACT_DRAFT_IDENTITY_INVALID")
        draft_sha = draft_identity.get("sha256")
        if not isinstance(draft_sha, str) or not _SHA256.fullmatch(draft_sha):
            raise ValueError("P0_CONTRACT_DRAFT_IDENTITY_INVALID")
        if (
            guided_draft.get("sha256") != draft_sha
            or previous_payload.get("draft_sha256") != draft_sha
            or freeze_receipt.get("latest_draft_sha256") != draft_sha
        ):
            raise ValueError("P0_CONTRACT_LINEAGE_MISMATCH")
        draft_bytes = _read_regular_bytes(
            guided_root / "drafts" / f"{draft_sha}.json",
            "P0_CONTRACT_DRAFT_MISMATCH",
        )
        if (
            _sha256(draft_bytes) != draft_sha
            or type(draft_identity.get("byte_size")) is not int
            or draft_identity.get("byte_size") != len(draft_bytes)
        ):
            raise ValueError("P0_CONTRACT_DRAFT_MISMATCH")
        draft = _strict_object(draft_bytes, "Guided Intake draft")
        frozen_bytes = _read_regular_bytes(
            guided_root / "freezes" / f"{frozen_sha}.json",
            "P0_FROZEN_INTAKE_MISMATCH",
        )
        if _sha256(frozen_bytes) != frozen_sha:
            raise ValueError("P0_FROZEN_INTAKE_MISMATCH")
        frozen = _strict_object(frozen_bytes, "Frozen Guided Intake")
        frozen_original = frozen.get("original_request_identity")
        frozen_authority = frozen.get("authority")
        if not isinstance(frozen_original, Mapping) or not isinstance(
            frozen_authority, Mapping
        ):
            raise ValueError("P0_FROZEN_INTAKE_MISMATCH")

        structured_interpretation_sha = _sha256(
            guided_canonical_json(dict(current_interpretation))
        )
        _require_exact_lineage(
            {
                "repository_identity": (
                    head,
                    ordinary.get("repository_identity"),
                    technical.get("preparation_repository_identity"),
                    freeze.get("repository_identity"),
                    preparation.get("repository_identity"),
                    freeze_receipt.get("product_commit"),
                    guided_freeze.get("repository_identity"),
                    frozen.get("repository_identity"),
                    current_payload.get("repository_identity"),
                ),
                "preparation_id": (
                    ordinary.get("preparation_id"),
                    preparation.get("preparation_id"),
                ),
                "request_id": (
                    active_request_id,
                    technical.get("active_request_id"),
                    technical.get("request_id"),
                    freeze.get("request_id"),
                    preparation.get("request_id"),
                    guided_request.get("request_id"),
                    guided_draft.get("request_id"),
                    guided_freeze.get("request_id"),
                    frozen_original.get("request_id"),
                    original_payload.get("request_id"),
                    previous_payload.get("request_id"),
                ),
                "draft_id": (
                    active_draft_id,
                    technical.get("draft_id"),
                    freeze.get("draft_id"),
                    preparation.get("draft_id"),
                    guided_draft.get("draft_id"),
                    guided_freeze.get("draft_id"),
                    previous_payload.get("draft_id"),
                ),
                "draft_sha256": (
                    draft_sha,
                    draft_identity.get("sha256"),
                    guided_draft.get("sha256"),
                    freeze_receipt.get("latest_draft_sha256"),
                    frozen.get("latest_draft_sha256"),
                    previous_payload.get("draft_sha256"),
                    _sha256(draft_bytes),
                ),
                "wrapper_sha256": (
                    EXPECTED_WRAPPER_SHA256,
                    technical.get("wrapper_sha256"),
                    wrapper_identity.get("sha256"),
                    freeze_receipt.get("request_sha256"),
                    guided_request.get("sha256"),
                    guided_draft.get("source_request_sha256"),
                    draft.get("source_request_sha256"),
                    frozen_original.get("sha256"),
                    original_payload.get("request_sha256"),
                    previous_payload.get("source_request_sha256"),
                    current_payload.get("request_sha256"),
                    _sha256(wrapper_bytes),
                ),
                "interpretation_sha256": (
                    EXPECTED_INTERPRETATION_SHA256,
                    technical.get("interpretation_sha256"),
                    freeze.get("interpretation_sha256"),
                    preparation.get("interpretation_sha256"),
                    guided_freeze.get("interpretation_sha256"),
                    structured_interpretation_sha,
                ),
                "gate": (
                    EXPECTED_GATE,
                    technical.get("gate"),
                    preparation.get("gate"),
                    current_interpretation.get("gate"),
                    guided_draft.get("validation_result"),
                    freeze_receipt.get("current_gate"),
                    frozen.get("current_gate"),
                    previous_payload.get("gate"),
                ),
                "freeze_id": (
                    latest_freeze_id,
                    freeze.get("freeze_id"),
                    freeze_receipt.get("freeze_id"),
                    guided_freeze.get("freeze_id"),
                    frozen.get("freeze_id"),
                    current_payload.get("freeze_id"),
                ),
                "frozen_intake_sha256": (
                    frozen_sha,
                    freeze.get("frozen_intake_sha256"),
                    freeze_receipt.get("frozen_intake_sha256"),
                    guided_freeze.get("sha256"),
                    current_payload.get("frozen_intake_sha256"),
                    _sha256(frozen_bytes),
                ),
                "freeze_receipt_sha256": (
                    freeze_receipt_sha,
                    freeze.get("receipt_sha256"),
                    guided_freeze.get("receipt_sha256"),
                    current_payload.get("freeze_receipt_sha256"),
                    _sha256(freeze_receipt_bytes),
                ),
                "predecessor_event_head": (
                    predecessor_head,
                    preparation.get("event_chain_head"),
                    freeze_receipt.get("event_chain_head"),
                    frozen.get("event_chain_head"),
                    previous_event.get("event_hash"),
                    current_event.get("previous_event_hash"),
                ),
                "current_event_head": (
                    current_chain_head,
                    current_event.get("event_hash"),
                ),
                "original_event_head": (
                    original_event.get("event_hash"),
                    previous_event.get("previous_event_hash"),
                ),
            }
        )

        expected_source_identity = {
            "byte_size": EXPECTED_CONTRACT_BYTES,
            "encoding": "UTF-8",
            "filename": CONTRACT_FILENAME,
            "sha256": EXPECTED_CONTRACT_SHA256,
        }
        if (
            dict(source_identity) != expected_source_identity
            or any(source.get(key) != value for key, value in expected_source_identity.items())
            or source.get("profile") != EXPECTED_CONTRACT_PROFILE
            or source.get("title") != EXPECTED_CONTRACT_TITLE
            or preparation.get("contract_profile") != EXPECTED_CONTRACT_PROFILE
            or preparation.get("detected_contract_title")
            != EXPECTED_CONTRACT_TITLE
            or preparation.get("detected_layer_roles")
            != {"primary": "V9", "supporting": "V13"}
        ):
            raise ValueError("P0_CONTRACT_SOURCE_MISMATCH")
        if (
            dict(frozen_original) != dict(guided_request)
            or guided_request.get("byte_size") != EXPECTED_WRAPPER_BYTES
            or guided_request.get("encoding") != "UTF-8"
            or guided_request.get("line_ending_treatment") != "AS_DECODED"
            or guided_request.get("unicode_normalization") != "NONE"
            or guided_request.get("whitespace_identity_bearing") is not True
            or guided_request.get("source_label")
            != "COMPANION_GUIDED_INTAKE_TEXTAREA"
            or original_payload.get("byte_size") != EXPECTED_WRAPPER_BYTES
            or original_payload.get("source_label")
            != guided_request.get("source_label")
            or original_event.get("recorded_at")
            != guided_request.get("captured_at")
        ):
            raise ValueError("P0_CONTRACT_WRAPPER_MISMATCH")
        if (
            technical.get("producer_identity")
            != "DECISION_OS_CONTRACT_FIXATION_COMPILER_V0_1"
            or preparation.get("producer_identity")
            != "DECISION_OS_CONTRACT_FIXATION_COMPILER_V0_1"
            or guided_draft.get("producer_label")
            != "DECISION_OS_CONTRACT_FIXATION_COMPILER_V0_1"
            or previous_payload.get("producer_label")
            != "DECISION_OS_CONTRACT_FIXATION_COMPILER_V0_1"
            or preparation.get("compiler_version")
            != "decision-os-contract-fixation-compiler-v0.1"
            or preparation.get("schema")
            != "decision-os-contract-preparation-receipt-v0.1"
            or draft_identity.get("schema") != "guided-intake-draft-v0.1"
            or draft.get("schema_version") != "guided-intake-draft-v0.1"
            or guided_draft.get("schema_version")
            != "guided-intake-draft-v0.1"
            or freeze_receipt.get("schema")
            != "guided-intake-freeze-receipt-v0.1"
            or frozen.get("schema_version") != "guided-intake-freeze-v0.1"
            or frozen.get("product_version") != "guided-intake-v0.1"
        ):
            raise ValueError("P0_CONTRACT_LINEAGE_MISMATCH")
        if (
            current_interpretation.get("authority_claim") != "NONE"
            or draft.get("authority_claim") != "NONE"
            or preparation.get("implementation_authority_state") != "NONE"
            or freeze_receipt.get("authority_state")
            != EXPECTED_FREEZE_AUTHORITY
            or frozen_authority.get("state") != EXPECTED_FREEZE_AUTHORITY
            or frozen_authority.get("claim")
            != "INTERPRETATION ONLY — NO EXECUTION AUTHORITY"
            or current_payload.get("authority_state")
            != EXPECTED_FREEZE_AUTHORITY
        ):
            raise ValueError("P0_FREEZE_AUTHORITY_MISMATCH")
        if (
            any(
                frozen.get(key) != current_interpretation.get(key)
                for key in ("completion_line", "do_not_touch", "objective", "unknown")
            )
            or frozen.get("confirmations") != guided_record.get("confirmations")
        ):
            raise ValueError("P0_CONTRACT_LINEAGE_MISMATCH")
        return {
            "filename": CONTRACT_FILENAME,
            "profile": EXPECTED_CONTRACT_PROFILE,
            "title": EXPECTED_CONTRACT_TITLE,
            "source_byte_count": EXPECTED_CONTRACT_BYTES,
            "source_sha256": EXPECTED_CONTRACT_SHA256,
            "wrapper_sha256": EXPECTED_WRAPPER_SHA256,
            "interpretation_sha256": EXPECTED_INTERPRETATION_SHA256,
            "preparation_id": ordinary.get("preparation_id"),
            "preparation_receipt_sha256": preparation_receipt_sha,
            "request_id": technical.get("request_id"),
            "draft_id": technical.get("draft_id"),
            "freeze_id": freeze.get("freeze_id"),
            "frozen_intake_sha256": frozen_sha,
            "freeze_receipt_sha256": freeze_receipt_sha,
            "guided_intake_current_event_chain_head": current_chain_head,
            "contract_preparation_receipt_event_chain_head": preparation.get(
                "event_chain_head"
            ),
            "contract_freeze_receipt_event_chain_head": predecessor_head,
            "ordinary_contract_execution_authority": EXPECTED_EXECUTION_AUTHORITY,
            "guided_intake_freeze_authority": EXPECTED_FREEZE_AUTHORITY,
            "gate": EXPECTED_GATE,
        }

    def _historical_binding(self, repository: Path) -> dict[str, Any]:
        cycle_005_root = repository / ".decision-os/field-notes/proofs/cycle-005"
        journal = cycle_005_root / "creator-live-proof-v0.2.jsonl"
        anchor = cycle_005_root / "creator-live-proof-v0.2.anchor.jsonl"
        if (
            not journal.is_file()
            or journal.is_symlink()
            or _sha256(journal.read_bytes()) != CYCLE_005_JOURNAL_SHA256
            or not anchor.is_file()
            or anchor.is_symlink()
            or _sha256(anchor.read_bytes()) != CYCLE_005_ANCHOR_SHA256
        ):
            raise ValueError("P0_CYCLE_005_IDENTITY_MISMATCH")
        readback = FieldNoteCreatorLiveProofRuntime.load_attempt(
            cycle_005_root
        ).read_back()
        observed = (
            readback.state,
            readback.failure_boundary,
            readback.failure_reason,
        )
        if (
            observed != CYCLE_005_TERMINAL
            or readback.readback_sha256 != CYCLE_005_READBACK_SHA256
        ):
            raise ValueError("P0_CYCLE_005_READBACK_MISMATCH")
        v01_manifest = _manifest_identity(
            repository,
            _CANDIDATE_V01_FILES,
            "P0_CANDIDATE_V01_IDENTITY_MISMATCH",
        )
        v01_before = verify_candidate_v0_1_fixed_before(repository)
        v02_manifest = _manifest_identity(
            repository,
            _CANDIDATE_V02_FILES,
            "P0_CANDIDATE_V02_IDENTITY_MISMATCH",
        )
        return {
            "cycle_005": {
                "cycle_key": "cycle-005",
                "state": CYCLE_005_TERMINAL[0],
                "failure_boundary": CYCLE_005_TERMINAL[1],
                "failure_code": CYCLE_005_TERMINAL[2],
                "journal_sha256": CYCLE_005_JOURNAL_SHA256,
                "anchor_sha256": CYCLE_005_ANCHOR_SHA256,
                "typed_readback_sha256": CYCLE_005_READBACK_SHA256,
                "reopen_permitted": False,
                "retry_permitted": False,
                "replacement_permitted": False,
                "migration_permitted": False,
                "reinterpretation_permitted": False,
            },
            "candidate_v0_1": {
                "candidate_id": "CREATOR_LIVE_AGENTS_BEFORE_AFTER_V0_1",
                "protected_file_count": len(_CANDIDATE_V01_FILES),
                "protected_manifest_sha256": v01_manifest,
                "fixed_before": v01_before.as_dict(),
                "immutable": True,
            },
            "candidate_v0_2": {
                "candidate_id": CANDIDATE_ID,
                "protected_file_count": len(_CANDIDATE_V02_FILES),
                "protected_manifest_sha256": v02_manifest,
                "immutable": True,
            },
        }

    def _candidate_binding(self, repository: Path) -> dict[str, Any]:
        verify_packaged_source_against_git(repository)
        source = load_fixed_source()
        if (
            len(source) != FIXED_SOURCE_IDENTITY.utf8_byte_count
            or _sha256(source) != FIXED_SOURCE_IDENTITY.sha256
            or source.count(b"\n") != FIXED_SOURCE_IDENTITY.line_count
            or not source.endswith(b"\n")
        ):
            raise ValueError("P0_INSTALLED_COMMON_BEFORE_MISMATCH")
        tasks = verify_fixed_tasks(repository)
        schemas: list[dict[str, str]] = []
        for relative, schema_id, expected_sha in _SCHEMA_FILES:
            raw = (repository / relative).read_bytes()
            value = _strict_object(raw, relative)
            if _sha256(raw) != expected_sha or value.get("$id") != schema_id:
                raise ValueError("P0_CANDIDATE_SCHEMA_MISMATCH")
            schemas.append(
                {"path": relative, "schema": schema_id, "sha256": expected_sha}
            )
        tools = candidate_dynamic_tools()
        if [tool.get("name") for tool in tools] != [
            SOURCE_TOOL_NAME,
            "propose_field_note_candidate",
        ]:
            raise ValueError("P0_DYNAMIC_TOOL_MANIFEST_MISMATCH")
        return {
            "candidate_id": CANDIDATE_ID,
            "common_before": {
                "logical_artifact": "AGENTS.md",
                "candidate_visible_path": FIXED_SOURCE_IDENTITY.virtual_path,
                "revision": FIXED_SOURCE_IDENTITY.source_revision,
                "git_blob": FIXED_SOURCE_IDENTITY.git_blob,
                "utf8_byte_count": FIXED_SOURCE_IDENTITY.utf8_byte_count,
                "line_count": FIXED_SOURCE_IDENTITY.line_count,
                "sha256": FIXED_SOURCE_IDENTITY.sha256,
                "final_lf": True,
                "normalization_permitted": False,
                "runtime_source": "installed-content-addressed-resource",
            },
            "source_tool": {
                "name": SOURCE_TOOL_NAME,
                "input_schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "maxProperties": 0,
                },
                "path_control": False,
                "single_semantic_disclosure": True,
            },
            "developer_instructions_sha256": DEVELOPER_INSTRUCTIONS_SHA256,
            "dynamic_tool_manifest": {
                "run_1_tool_names": [
                    SOURCE_TOOL_NAME,
                    "propose_field_note_candidate",
                ],
                "sha256": dynamic_tool_manifest_sha256(),
                "run_2_dynamic_tools": [],
            },
            "schema_identities": schemas,
            "candidate_schema_vocabulary": {
                "projection": PROJECTION_SCHEMA,
                "compression": COMPRESSION_SCHEMA,
                "diff": DIFF_SCHEMA,
                "boundary": BOUNDARY_SCHEMA,
                "witness": WITNESS_SCHEMA,
                "a3_witness": A3_WITNESS_SCHEMA,
                "public_bundle_assembler": PUBLIC_BUNDLE_ASSEMBLER,
            },
            "gates": {
                "source_isolation": "EXACT_CANDIDATE_V0_2_BINDING",
                "independence": "PASS_REQUIRED",
                "public_after_projection": "EXACT_V0_2_SCHEMA",
                "strict_compression": {
                    "operator": "after_utf8_byte_count < before_utf8_byte_count",
                    "before_utf8_byte_count": 20_705,
                },
                "boundaries": {
                    "ids": [f"B{number:02d}" for number in range(1, 11)],
                    "required_result": "PRESENT",
                    "required_count_each": 1,
                },
                "public_safety": "PASS_REQUIRED",
                "generated_witness_policy": "PASS_REQUIRED",
                "witness_binding": "DURABLE_EXACT_REQUIRED",
                "unauthorized_metadata": "ABSENT_REQUIRED",
                "post_a1_readback": "EXACT_DURABLE_PASS_REQUIRED",
                "run_2_open_before_all_pass": False,
                "repair_retry_or_alternate_note": False,
            },
            "a3_overlay": {
                "generic_v0_3_unchanged": True,
                "eligible_candidate_count": 1,
                "winning_candidate_count": 1,
                "winner": "designated-durable-witness-source-span",
                "winner_sha256": "durable-witness-sha256",
                "output_bytes": "exact",
                "output_occurrence_count": 1,
                "different_matching_line_permitted": False,
            },
            "behavior": {
                "suite_sha256": BEHAVIOR_SUITE_SHA256,
                "rubric_sha256": BEHAVIOR_RUBRIC_SHA256,
                "scenario_count": 10,
                "threshold": "10/10",
                "state_before_execution": "NOT_RUN",
                "automatic_pass_from_a1_a7": False,
            },
        }

    def _repository_guard(self, repository: Path) -> dict[str, Any]:
        """Capture and validate one exact repository launch boundary."""

        head = _run_git(repository, "rev-parse", "HEAD")
        local_main = _run_git(repository, "rev-parse", "main")
        origin_main = _run_git(repository, "rev-parse", "origin/main")
        branch = _run_git(repository, "branch", "--show-current")
        remote = _run_git(repository, "remote", "get-url", "origin")
        ahead_behind = _run_git(
            repository,
            "rev-list",
            "--left-right",
            "--count",
            "main...origin/main",
        ).split()
        tracked_status = _run_git(
            repository,
            "status",
            "--porcelain",
            "--untracked-files=no",
        )
        worktree_clean = _git_diff_clean(repository, cached=False)
        index_clean = _git_diff_clean(repository, cached=True)
        common = self._git_common_dir(repository)
        operation_paths = (
            common / "MERGE_HEAD",
            common / "CHERRY_PICK_HEAD",
            common / "REVERT_HEAD",
            common / "REBASE_HEAD",
            common / "rebase-apply",
            common / "rebase-merge",
        )
        operation_active = any(os.path.lexists(path) for path in operation_paths)
        if remote != self.spec.remote:
            raise ValueError("P0_REMOTE_MISMATCH")
        if branch != "main":
            raise ValueError("P0_BRANCH_MISMATCH")
        if head != local_main or head != origin_main or ahead_behind != ["0", "0"]:
            raise ValueError("P0_REVISION_MISMATCH")
        if tracked_status or not worktree_clean:
            raise ValueError("P0_TRACKED_WORKTREE_DIRTY")
        if not index_clean:
            raise ValueError("P0_INDEX_DIRTY")
        if operation_active:
            raise ValueError("P0_GIT_OPERATION_ACTIVE")
        self._require_storage_boundary(repository)
        return {
            "head": head,
            "local_main": local_main,
            "origin_main": origin_main,
            "branch": branch,
            "remote": remote,
            "ahead_behind": tuple(ahead_behind),
            "tracked_status": tracked_status,
            "worktree_clean": worktree_clean,
            "index_clean": index_clean,
            "operation_active": operation_active,
            "common": common,
            "repository_id": repository_id(repository),
        }

    def _require_storage_boundary(self, repository: Path) -> None:
        expected_root = (
            repository / ".decision-os/field-notes/proofs/cycle-006"
        )
        if self.spec.storage_root != expected_root:
            raise ValueError("P0_CYCLE_006_STORAGE_ROOT_MISMATCH")
        for ancestor in (
            repository / ".decision-os",
            repository / ".decision-os/field-notes",
            repository / ".decision-os/field-notes/proofs",
        ):
            if (
                not os.path.lexists(ancestor)
                or not ancestor.is_dir()
                or ancestor.is_symlink()
            ):
                raise ValueError("P0_CYCLE_006_STORAGE_PARENT_INVALID")
        if expected_root.parent.resolve(strict=True) != (
            repository / ".decision-os/field-notes/proofs"
        ):
            raise ValueError("P0_CYCLE_006_STORAGE_PARENT_INVALID")
        if os.path.lexists(expected_root):
            raise ValueError("P0_CYCLE_006_STORAGE_PRESENT")

    def _p0(self, base_snapshot: Mapping[str, Any]) -> CreatorLiveCycle006P0Result:
        try:
            repository = self.spec.repository.resolve(strict=True)
            if (
                repository != EXPECTED_REPOSITORY.resolve(strict=True)
                or self.spec.remote != EXPECTED_REMOTE
                or self.spec.runtime != EXPECTED_CODEX_RUNTIME
                or self.spec.codex_executable != CYCLE_006_CODEX_PATH
            ):
                raise ValueError("P0_FIXED_EXECUTION_IDENTITY_MISMATCH")
            outer_gate_failure = self._outer_gate_failure_code()
            if outer_gate_failure is not None:
                return CreatorLiveCycle006P0Result(
                    False,
                    outer_gate_failure,
                    None,
                    None,
                )
            selected = base_snapshot.get("repository")
            if not isinstance(selected, Mapping) or Path(
                str(selected.get("path", ""))
            ).resolve(strict=True) != repository:
                raise ValueError("P0_REPOSITORY_PATH_MISMATCH")
            repository_guard = self._repository_guard(repository)
            head = repository_guard["head"]
            local_main = repository_guard["local_main"]
            origin_main = repository_guard["origin_main"]
            branch = repository_guard["branch"]
            remote = repository_guard["remote"]
            common = repository_guard["common"]

            contract = self._contract_binding(
                repository=repository,
                common=common,
                head=head,
                base_snapshot=base_snapshot,
            )
            historical = self._historical_binding(repository)
            candidate = self._candidate_binding(repository)
            source_tree = product_tree_sha256(repository)
            installed_tree = product_tree_sha256(
                self.spec.runtime_root or _runtime_root()
            )
            if source_tree != installed_tree:
                raise ValueError("P0_SOURCE_INSTALLED_PRODUCT_TREE_MISMATCH")
            charter_lineage = [
                {
                    "path": path.relative_to(repository).as_posix(),
                    "sha256": _sha256(path.read_bytes()),
                }
                for path in sorted(
                    (repository / "validation").glob(
                        "a7_creator_live_whole_flow_reentry_charter*.md"
                    ),
                    key=lambda item: item.name.encode("utf-8"),
                )
            ]
            if not charter_lineage or not any(
                item["path"].endswith("charter_delta_v1_0.md")
                for item in charter_lineage
            ):
                raise ValueError("P0_CHARTER_V1_0_MISSING")
            forward_charter = repository / FORWARD_RUNTIME_CHARTER_PATH
            if (
                not forward_charter.is_file()
                or forward_charter.is_symlink()
                or _sha256(forward_charter.read_bytes())
                != FORWARD_RUNTIME_CHARTER_SHA256
                or not any(
                    item == {
                        "path": FORWARD_RUNTIME_CHARTER_PATH,
                        "sha256": FORWARD_RUNTIME_CHARTER_SHA256,
                    }
                    for item in charter_lineage
                )
            ):
                raise ValueError("P0_FORWARD_RUNTIME_CHARTER_MISMATCH")
            tasks = {
                "run_1": {
                    "path": FIXED_TASK_IDENTITIES[0].path,
                    "lane": "A1_ONLY",
                    "utf8_byte_count": FIXED_TASK_IDENTITIES[0].byte_count,
                    "line_count": FIXED_TASK_IDENTITIES[0].line_count,
                    "sha256": FIXED_TASK_IDENTITIES[0].sha256,
                    "transmitted": False,
                },
                "run_2": {
                    "path": FIXED_TASK_IDENTITIES[1].path,
                    "lane": "EXACT_A2_ONLY",
                    "utf8_byte_count": FIXED_TASK_IDENTITIES[1].byte_count,
                    "line_count": FIXED_TASK_IDENTITIES[1].line_count,
                    "sha256": FIXED_TASK_IDENTITIES[1].sha256,
                    "alternate_note_scan_or_reconstruction": False,
                    "transmitted": False,
                },
            }
            binding = {
                "schema": "decision-os.creator-live-cycle-006-launch-binding.v0.1",
                "cycle": {
                    "number": CYCLE_NUMBER,
                    "cycle_key": CYCLE_KEY,
                    "candidate_id": CANDIDATE_ID,
                    "implementation_authorization_observed_at": (
                        IMPLEMENTATION_AUTHORIZATION_OBSERVED_AT
                    ),
                    "live_start_authorization": (
                        "PRESENT"
                        if self.spec.live_start_authorization_observed_at
                        is not None
                        else "ABSENT"
                    ),
                    "live_start_authorization_observed_at": (
                        self.spec.live_start_authorization_observed_at
                    ),
                },
                "attempt_policy": {
                    "attempt_count": 1,
                    "one_attempt": True,
                    "retry_count": 0,
                    "replacement_count": 0,
                    "resume_after_interruption": False,
                    "alternate_proof_identity": False,
                    "proof_identity_derivation": (
                        _PROOF_ID_PREFIX + "<full_launch_binding_sha256>"
                    ),
                    "proof_digest_character_count": 64,
                    "proof_root": str(self.spec.storage_root),
                    "proof_root_present": False,
                    "alternate_proof_root": False,
                },
                "repository": {
                    "selected_path": str(repository),
                    "selected_path_sha256": _sha256(
                        str(repository).encode("utf-8")
                    ),
                    "repository_id": repository_guard["repository_id"],
                    "head": head,
                    "local_main": local_main,
                    "origin_main": origin_main,
                    "branch": branch,
                    "ahead": 0,
                    "behind": 0,
                    "remote": remote,
                    "tracked_worktree_clean": True,
                    "index_clean": True,
                    "git_operation_active": False,
                },
                "product": {
                    "source_tree_sha256": source_tree,
                    "installed_tree_sha256": installed_tree,
                },
                "contract": contract,
                "charter_lineage": charter_lineage,
                "candidate": candidate,
                "tasks": tasks,
                "runtime": {
                    **EXPECTED_RUNTIME,
                    "run_1_dynamic_tools_exact": True,
                    "run_2_exact_a2_reconnect_only": True,
                    "candidate_feature_flags": {"plugins": False},
                    "project_doc_fallback_filenames": [],
                    "project_doc_max_bytes": 0,
                    "disabled_capabilities": [
                        "plugins",
                        "mcp",
                        "apps",
                        "hooks",
                        "shell",
                        "git",
                        "web",
                        "arbitrary_file_reads",
                        "attachments",
                        "dependency_installation",
                        "multi_agent",
                        "remote_plugins",
                        "project_document_injection",
                        "arbitrary_write_edit_delete",
                    ],
                },
                "runtime_artifact": {
                    "configured_path": str(self.spec.codex_executable),
                    "expected_path": str(CYCLE_006_CODEX_PATH),
                    "binary_sha256": CYCLE_006_CODEX_SHA256,
                    "recovery_receipt_path": str(
                        CYCLE_006_CODEX_RECOVERY_RECEIPT
                    ),
                    "version_stdout": (
                        f"codex-cli {CYCLE_006_CODEX_CLI_VERSION}\n"
                    ),
                    "regular_file_required": True,
                    "executable_required": True,
                    "symlink_permitted": False,
                    "path_fallback_permitted": False,
                    "chatgpt_app_fallback_permitted": False,
                },
                "historical_boundary": historical,
                "comparison": {
                    "result_before_execution": "NOT_ESTABLISHED",
                    "common_before": {
                        "utf8_byte_count": 20_705,
                        "line_count": 517,
                        "sha256": FIXED_SOURCE_IDENTITY.sha256,
                    },
                    "lane_a_compactor": {"result": "NOT_ESTABLISHED"},
                    "lane_b_human_ai_manual": {
                        "before_utf8_byte_count": 20_705,
                        "before_line_count": 517,
                        "after_utf8_byte_count": 11_147,
                        "after_line_count": 359,
                        "reduction_utf8_byte_count": 9_558,
                        "approximate_reduction_percentage": "46.16%",
                        "qualification": "textual/manual restructuring only",
                        "behavior": "NOT_ESTABLISHED",
                        "candidate_visible": False,
                    },
                    "lane_c_v13": {
                        "generated_values": "NOT_ESTABLISHED",
                        "retry_or_replacement": "NOT_AUTHORIZED",
                    },
                },
                "reduction_boundary": {
                    "schema": REDUCTION_MAP_SCHEMA,
                    "core_statement": REDUCTION_CORE_STATEMENT,
                    "surfaces": {
                        "RTK": "tool-output",
                        "Ponytail": "implementation",
                        "Compactor": "persistent-instruction",
                        "OSI": "output / handoff",
                        "V13": "iteration / authority",
                    },
                    "ranking": False,
                    "external_descriptions": "LATER_WEB_VERIFICATION_REQUIRED",
                    "external_performance_claims": False,
                    "superiority_claims": False,
                },
                "pre_live_state": {
                    "artifact_behavior": "NOT_RUN",
                    "comparison_result": "NOT_ESTABLISHED",
                    "proof_identity": None,
                    "model_invocation_count": 0,
                    "task_transmission_count": 0,
                    "real_after": None,
                    "publication_authorized": False,
                },
            }
            ending_guard = self._repository_guard(repository)
            ending_contract = self._contract_binding(
                repository=repository,
                common=ending_guard["common"],
                head=ending_guard["head"],
                base_snapshot=base_snapshot,
            )
            ending_historical = self._historical_binding(repository)
            ending_candidate = self._candidate_binding(repository)
            ending_charter_lineage = [
                {
                    "path": path.relative_to(repository).as_posix(),
                    "sha256": _sha256(path.read_bytes()),
                }
                for path in sorted(
                    (repository / "validation").glob(
                        "a7_creator_live_whole_flow_reentry_charter*.md"
                    ),
                    key=lambda item: item.name.encode("utf-8"),
                )
            ]
            if (
                ending_guard != repository_guard
                or ending_contract != contract
                or ending_historical != historical
                or ending_candidate != candidate
                or ending_charter_lineage != charter_lineage
                or product_tree_sha256(repository) != source_tree
                or product_tree_sha256(self.spec.runtime_root or _runtime_root())
                != installed_tree
            ):
                raise ValueError("P0_STATE_CHANGED_DURING_QUALIFICATION")
            digest = _sha256(canonical_json(binding).encode("utf-8"))
            runtime_failure = self._runtime_binary_failure_code()
            if runtime_failure is not None:
                return CreatorLiveCycle006P0Result(
                    False,
                    runtime_failure,
                    binding,
                    digest,
                )
            return CreatorLiveCycle006P0Result(True, None, binding, digest)
        except (
            OSError,
            RuntimeError,
            subprocess.SubprocessError,
            TypeError,
            ValueError,
            KeyError,
        ) as exc:
            code = str(exc)
            if not code.startswith("P0_"):
                code = "P0_IDENTITY_UNAVAILABLE"
            return CreatorLiveCycle006P0Result(False, code[:128], None, None)

    @staticmethod
    def _public_binding(binding: Mapping[str, Any]) -> dict[str, Any]:
        repository = binding["repository"]
        product = binding["product"]
        contract = binding["contract"]
        candidate = binding["candidate"]
        historical = binding["historical_boundary"]
        return {
            "schema": binding["schema"],
            "cycle": binding["cycle"],
            "attempt_policy": {
                key: binding["attempt_policy"][key]
                for key in (
                    "attempt_count",
                    "one_attempt",
                    "retry_count",
                    "replacement_count",
                    "resume_after_interruption",
                )
            },
            "repository": {
                "head": repository["head"],
                "local_main": repository["local_main"],
                "origin_main": repository["origin_main"],
                "branch": repository["branch"],
                "ahead": repository["ahead"],
                "behind": repository["behind"],
                "tracked_worktree_clean": repository["tracked_worktree_clean"],
                "index_clean": repository["index_clean"],
                "git_operation_active": repository["git_operation_active"],
            },
            "product": product,
            "contract": {
                key: contract[key]
                for key in (
                    "filename",
                    "profile",
                    "title",
                    "source_byte_count",
                    "source_sha256",
                    "wrapper_sha256",
                    "interpretation_sha256",
                    "ordinary_contract_execution_authority",
                    "guided_intake_freeze_authority",
                    "gate",
                )
            },
            "candidate": {
                "candidate_id": candidate["candidate_id"],
                "common_before": candidate["common_before"],
                "source_tool": candidate["source_tool"],
                "dynamic_tool_manifest": candidate["dynamic_tool_manifest"],
                "schema_identities": candidate["schema_identities"],
                "gates": candidate["gates"],
                "a3_overlay": candidate["a3_overlay"],
                "behavior": candidate["behavior"],
            },
            "tasks": binding["tasks"],
            "runtime": binding["runtime"],
            "historical_boundary": {
                "cycle_005": historical["cycle_005"],
                "candidate_v0_1": historical["candidate_v0_1"],
                "candidate_v0_2": historical["candidate_v0_2"],
            },
            "comparison": binding["comparison"],
            "reduction_boundary": binding["reduction_boundary"],
            "pre_live_state": binding["pre_live_state"],
        }

    def _load_fixed_task(self, index: int) -> tuple[str, bytes]:
        identity = FIXED_TASK_IDENTITIES[index]
        raw = (self.spec.repository / identity.path).read_bytes()
        if (
            len(raw) != identity.byte_count
            or raw.count(b"\n") != identity.line_count
            or _sha256(raw) != identity.sha256
        ):
            raise ValueError("FIXED_TASK_IDENTITY_MISMATCH")
        return raw.decode("utf-8", errors="strict"), raw

    def _wait_for_controller_run(self) -> None:
        deadline = time.monotonic() + self.timeout_seconds
        while self.controller.snapshot()["run"]["state"] == "running":
            if time.monotonic() >= deadline:
                raise ValueError("CREATOR_LIVE_RUN_TIMEOUT")
            time.sleep(0.05)

    def _record_turn_started(self, run_index: int, run_id: str) -> None:
        """Bind accepted model/task activity to the durable Cycle 006 attempt."""

        runtime = self._runtime
        if runtime is None:
            raise ValueError("CYCLE_006_RUNTIME_UNAVAILABLE")
        readback = runtime.read_back()
        run = readback.run_1 if run_index == 1 else readback.run_2
        if run is None or run.run_id != run_id:
            raise ValueError("CYCLE_006_TURN_START_IDENTITY_INVALID")
        launch = readback.proof_attempt_id.removeprefix(_PROOF_ID_PREFIX)
        _persist_turn_start(
            self.spec.storage_root,
            proof_attempt_id=readback.proof_attempt_id,
            launch_binding_sha256=launch,
            run_index=run_index,
            run_id=run_id,
        )

    def _record_turn_start_intent(self, run_index: int, run_id: str) -> None:
        """Write ahead before the fixed task can reach provider transport."""

        runtime = self._runtime
        if runtime is None:
            raise ValueError("CYCLE_006_RUNTIME_UNAVAILABLE")
        readback = runtime.read_back()
        run = readback.run_1 if run_index == 1 else readback.run_2
        if run is None or run.run_id != run_id:
            raise ValueError("CYCLE_006_TURN_START_IDENTITY_INVALID")
        launch = readback.proof_attempt_id.removeprefix(_PROOF_ID_PREFIX)
        _persist_turn_start_intent(
            self.spec.storage_root,
            proof_attempt_id=readback.proof_attempt_id,
            launch_binding_sha256=launch,
            run_index=run_index,
            run_id=run_id,
        )

    def _fail_open_runtime(
        self,
        runtime: FieldNoteCreatorLiveProofRuntime,
        code: str,
    ) -> None:
        try:
            readback = runtime.read_back()
            if readback.state != "OPEN":
                return
            boundary = {
                "A1_CAPTURE": "A1_CAPTURE",
                "A2_RECONNECT": "A2_RECONNECT",
                "A3_REUSE": "A3_REUSE",
                "A4_DURABILITY": "A4_DURABILITY",
                "A5_CONFIRMATION": "A5_CONFIRMATION",
                "A6_REVIEW": "A6_REVIEW",
            }.get(readback.current_stage, "RUNTIME_ENFORCEMENT")
            runtime.record_stage_failure(boundary, code[:256])
        except Exception:
            pass

    def _capture_a1(
        self,
        *,
        runtime: FieldNoteCreatorLiveProofRuntime,
        source: FieldNoteSourceRepositoryIdentity,
        p0: CreatorLiveCycle006P0Result,
        task: str,
        task_bytes: bytes,
    ) -> tuple[Any, FieldNoteIdentity, bytes, Any, str]:
        readback = runtime.read_back()
        run_id = readback.run_1.run_id
        contract_identity_sha256 = _sha256(
            canonical_json(p0.binding["contract"]).encode("utf-8")
        )
        self.controller.start_creator_live_candidate_v0_2_a1(  # type: ignore[attr-defined]
            task,
            run_id=run_id,
            expected_runtime_identity=self.spec.runtime,
            contract_identity_sha256=contract_identity_sha256,
            turn_start_intent_observer=lambda observed_run_id: (
                self._record_turn_start_intent(1, observed_run_id)
            ),
            turn_started_observer=lambda observed_run_id: (
                self._record_turn_started(1, observed_run_id)
            ),
        )
        self._wait_for_controller_run()
        failure = self.controller.creator_live_a1_failure_reason(  # type: ignore[attr-defined]
            expected_run_id=run_id
        )
        if failure is not None:
            raise ValueError(failure)
        draft = self.controller.creator_live_a1_capture_candidate()  # type: ignore[attr-defined]
        completion = self.controller.creator_live_a1_run_completion()  # type: ignore[attr-defined]
        evidence = self.controller.creator_live_candidate_v0_2_isolation_evidence(  # type: ignore[attr-defined]
            expected_run_id=run_id
        )
        isolation, independence = qualify_independence(evidence)
        if isolation.result != "PASS" or independence.result != "PASS":
            raise ValueError("A1_CANDIDATE_INDEPENDENCE_NOT_PASS")
        if (
            completion.task_sha256 != _sha256(task_bytes)
            or completion.actual_runtime_identity != self.spec.runtime
            or draft.source_run_id != run_id
        ):
            raise ValueError("A1_CAPTURE_IDENTITY_MISMATCH")
        repository = self.spec.repository.resolve(strict=True)
        target = FieldNoteCreatorLiveA1CaptureBridge._fixed_target(
            repository,
            draft,
        )
        FieldNoteCreatorLiveA1CaptureBridge._require_unoccupied_target(target)
        approval = self.controller.field_note_save(  # type: ignore[attr-defined]
            _cycle_006_authority=self
        )
        request = approval["run"]["field_note"]
        if (
            request.get("state") != "approval"
            or request.get("approval", {}).get("path") != draft.relative_path
            or request.get("approval", {}).get("content_sha256") != draft.sha256
        ):
            raise ValueError("A1_SAVE_APPROVAL_IDENTITY_MISMATCH")
        saved = self.controller.field_note_approval(  # type: ignore[attr-defined]
            "allow_once",
            _cycle_006_authority=self,
        )
        if saved["run"]["field_note"] != {
            "state": "saved",
            "path": draft.relative_path,
        }:
            raise ValueError("A1_CONTROLLER_SAVE_NOT_CONFIRMED")
        note_bytes = FieldNoteCreatorLiveA1CaptureBridge._exact_read_back(target)
        if note_bytes != draft.markdown or _sha256(note_bytes) != draft.sha256:
            raise ValueError("A1_NOTE_READ_BACK_MISMATCH")
        note = FieldNoteIdentity(
            note_path=draft.relative_path,
            field_note_id=draft.field_note_id,
            note_sha256=draft.sha256,
            origin_run_id=run_id,
        )
        projection = project_public_after(note_bytes)
        compression = compression_receipt(load_fixed_source(), projection.body)
        safety = public_safety(projection.body)
        boundaries = check_boundaries_v0_2(projection.body, safety)
        _, run_2_task_bytes = self._load_fixed_task(1)
        witness = bind_generated_witness_v0_2(
            note,
            note_bytes,
            projection,
            task_bytes,
            run_2_task_bytes,
            safety,
        )
        post_a1 = issue_post_a1_gate_v0_2(
            before=load_fixed_source(),
            task_bytes=(task_bytes, run_2_task_bytes),
            note_identity=note,
            note_bytes=note_bytes,
            source_isolation=isolation,
            independence=independence,
            projection=projection,
            compression=compression,
            safety=safety,
            boundaries=boundaries,
            witness_binding=witness,
        )
        commit = FieldNoteCreatorLiveA1CaptureCommitReceipt._issue(
            authority=_A1_CAPTURE_COMMIT_AUTHORITY,
            proof_attempt_id=readback.proof_attempt_id,
            run_id=run_id,
            task_sha256=_sha256(task_bytes),
            actual_runtime_identity=completion.actual_runtime_identity,
            source_repository=source,
            note=note,
            note_byte_count=len(note_bytes),
            draft_evidence_sha256=_a1_evidence_sha256(draft),
            draft_created_at=draft.created_at,
            save_as_of=self.now(),
        )
        runtime.record_a1_capture(
            draft,
            capture_commit=commit,
            expected_task_sha256=_sha256(task_bytes),
            actual_runtime_identity=completion.actual_runtime_identity,
            observed_at=self.now(),
        )
        after_a1 = runtime.read_back()
        if (
            not after_a1.durable_readback_verified
            or after_a1.state != "OPEN"
            or after_a1.current_stage != "A2_RECONNECT"
            or after_a1.captured_note != note
        ):
            raise ValueError("A1_DURABLE_CLOSURE_MISMATCH")
        post_path = self.spec.storage_root / POST_A1_READBACK_FILENAME
        digest = persist_post_a1_readback_v0_2(post_path, post_a1)
        durable_post = read_post_a1_readback_v0_2(post_path, digest)
        require_post_a1_gate_for_a2(durable_post)
        return draft, note, note_bytes, durable_post, digest

    def _run_sequence(
        self,
        runtime: FieldNoteCreatorLiveProofRuntime,
        source: FieldNoteSourceRepositoryIdentity,
        p0: CreatorLiveCycle006P0Result,
    ) -> None:
        try:
            launch = p0.launch_binding_sha256
            assert launch is not None
            repository = self.spec.repository.resolve(strict=True)
            self._stage = "A1"
            run_1_task, run_1_bytes = self._load_fixed_task(0)
            draft, note, note_bytes, post_a1, post_sha = self._capture_a1(
                runtime=runtime,
                source=source,
                p0=p0,
                task=run_1_task,
                task_bytes=run_1_bytes,
            )
            self._post_a1_readback_sha256 = post_sha

            self._stage = "A2"
            require_post_a1_gate_for_a2(post_a1)
            run_2_id = "run_a7_creator_live_cycle_006_2_" + launch
            runtime.open_run_2(
                FieldNoteWholeFlowRunIdentity(
                    proof_attempt_id=runtime.read_back().proof_attempt_id,
                    run_id=run_2_id,
                    started_at=self.now(),
                    repository=source,
                    runtime=self.spec.runtime,
                )
            )
            pre_a2 = runtime.read_back()
            target = creator_live_a2_target_from_readback(pre_a2)
            exact = prepare_creator_live_a2_reconnect(repository, target)
            run_2_task, run_2_bytes = self._load_fixed_task(1)
            self.controller.start_creator_live_candidate_v0_2_a2(  # type: ignore[attr-defined]
                run_2_task,
                target=target,
                post_a1_readback_path=(
                    self.spec.storage_root / POST_A1_READBACK_FILENAME
                ),
                post_a1_readback_sha256=post_sha,
                turn_start_intent_observer=lambda observed_run_id: (
                    self._record_turn_start_intent(2, observed_run_id)
                ),
                turn_started_observer=lambda observed_run_id: (
                    self._record_turn_started(2, observed_run_id)
                ),
            )
            self._wait_for_controller_run()
            failure = self.controller.creator_live_a2_failure_reason(  # type: ignore[attr-defined]
                expected_run_id=run_2_id
            )
            if failure is not None:
                raise ValueError(failure)
            completion = self.controller.creator_live_a2_run_completion(  # type: ignore[attr-defined]
                expected_run_id=run_2_id
            )
            if (
                completion.task_byte_count != len(run_2_bytes)
                or completion.task_sha256 != _sha256(run_2_bytes)
                or completion.actual_runtime_identity != self.spec.runtime
            ):
                raise ValueError("A2_OUTPUT_IDENTITY_INVALID")
            runtime.record_a2_reconnect(
                completion.reconnect_receipt,
                note=note,
                note_bytes=exact.note_bytes,
            )
            output_identity = FieldNoteCreatorLiveRun2OutputIdentity.create(
                proof_attempt_id=pre_a2.proof_attempt_id,
                run_id=run_2_id,
                task_byte_count=completion.task_byte_count,
                task_sha256=completion.task_sha256,
                final_output_byte_count=len(completion.final_output_bytes),
                final_output_sha256=completion.final_output_sha256,
            )
            runtime.record_run_2_output_identity(output_identity)

            self._stage = "A3"
            final_output_bytes = completion.final_output_bytes
            evidence_as_of = self.now()
            winner, audit = compile_run_2_output_artifact_audited(
                note=note,
                note_bytes=note_bytes,
                run_2_id=run_2_id,
                final_output_bytes=final_output_bytes,
                output_identity=output_identity,
            )
            durable_audit = runtime.record_a3_compiler_audit(audit)
            if audit.terminal_a3_code is not None:
                runtime.record_stage_failure("A3_REUSE", audit.terminal_a3_code)
            witness = WitnessBindingV02(**dict(post_a1.witness_binding))
            verification = verify_a3_winner_witness_v0_2(
                audit,
                witness,
                note_bytes,
                final_output_bytes,
            )
            self._a3_overlay_sha256 = _persist_a3_overlay(
                self.spec.storage_root,
                launch_binding_sha256=launch,
                post_a1_readback_sha256=post_sha,
                verification=verification,
            )
            if winner is None or durable_audit.a3_compiler_audit is None:
                raise ValueError("A3_COMPILER_RESULT_INVALID")
            claim = _claim_from_verified_a3_audit(
                note=note,
                note_bytes=note_bytes,
                run_2_id=run_2_id,
                output_identity=output_identity,
                observed_at=evidence_as_of,
                winner=winner,
                audit=durable_audit.a3_compiler_audit,
            )
            assessment = assess_field_note_reuse(
                note,
                claim,
                note_bytes=note_bytes,
            )
            if assessment.state != "REUSED":
                raise ValueError("A3_NOT_DEMONSTRABLY_REUSED")
            runtime.record_a3_reuse(assessment, note=note, note_bytes=note_bytes)
            reconnect_receipt = completion.reconnect_receipt
            self.controller.release_creator_live_a2_run_completion(  # type: ignore[attr-defined]
                expected_run_id=run_2_id
            )
            del completion, final_output_bytes

            ledger = FieldNoteMaturityLedger(
                repository / ".decision-os/field-notes/maturity-ledger-v0.1",
                note,
            )
            self._stage = "A4"
            commit = commit_field_note_maturity(
                ledger,
                FieldNoteMaturityCommitRequest(
                    note=note,
                    note_bytes=note_bytes,
                    reuse_claim=claim,
                    recorded_at=self.now(),
                    delivery_context=reconnect_receipt,
                ),
            )
            if commit.durable_snapshot is None or commit.assessment != assessment:
                raise ValueError("A4_ASSESSMENT_READBACK_MISMATCH")
            runtime.record_a4_durability(commit.durable_snapshot)
            self._stage = "A5"
            runtime.record_a5_confirmation(commit)
            self._stage = "A6"
            review = review_field_note_maturity(
                ledger,
                note,
                note_bytes=note_bytes,
                review_as_of=self.now(),
            )
            runtime.record_a6_review(review)
            self._stage = "A7"
            terminal = runtime.read_back()
            assert terminal.run_2 is not None
            bundle = FieldNoteWholeFlowEvidenceBundle(
                attempt=terminal.attempt,
                source_repository=source,
                run_1=terminal.run_1,
                run_2=terminal.run_2,
                note=note,
                note_bytes=note_bytes,
                a1_capture=draft,
                a2_reconnect=reconnect_receipt,
                a3_assessment=assessment,
                a4_snapshot=commit.durable_snapshot,
                a5_commit=commit,
                a6_review=review,
                proof_trace=terminal.events,
                creator_live_readback=terminal,
            )
            receipt = verify_field_note_whole_flow(bundle)
            if receipt.state != "PASS":
                raise ValueError(receipt.failure_reason or "A7_VERIFICATION_FAILED")
            manifest = build_portable_candidate_warehouse_manifest(bundle)
            with self._lock:
                self._receipt_sha256 = receipt.receipt_sha256
                self._manifest_sha256 = manifest.manifest_id
                self._terminal_state = "PASS"
        except Exception as exc:
            code = str(exc).strip() or "CREATOR_LIVE_SEQUENCE_FAILED"
            self._fail_open_runtime(runtime, code)
            with self._lock:
                self._terminal_state = "FAILED"
                self._terminal_failure_code = code[:256]
        finally:
            if "run_2_id" in locals():
                try:
                    self.controller.release_creator_live_a2_run_completion(  # type: ignore[attr-defined]
                        expected_run_id=run_2_id
                    )
                except Exception:
                    pass
            with self._lock:
                self._active = False

    def _durable_projection(self) -> dict[str, Any]:
        runtime = self._runtime
        if runtime is None:
            runtime = FieldNoteCreatorLiveProofRuntime.load_attempt(
                self.spec.storage_root
            )
            self._runtime = runtime
        readback = runtime.read_back()
        if not readback.durable_readback_verified:
            raise ValueError("PROOF_STORAGE_INTEGRITY_FAILURE")
        launch = readback.proof_attempt_id.removeprefix(_PROOF_ID_PREFIX)
        if readback.proof_attempt_id != _PROOF_ID_PREFIX + launch or not _SHA256.fullmatch(
            launch
        ):
            raise ValueError("PROOF_ATTEMPT_IDENTITY_INVALID")
        stage = (
            readback.failure_boundary
            if readback.state == "FAILED"
            else "A7"
            if readback.state == "TRACE_COMPLETE"
            else readback.current_stage or "proof-open"
        )
        model_count = _turn_start_count(self.spec.storage_root, readback)
        return {
            "cycle_key": CYCLE_KEY,
            "cycle_number": CYCLE_NUMBER,
            "candidate_id": CANDIDATE_ID,
            "state": "RUNNING" if self._active else readback.state,
            "stage": self._stage if self._active else stage,
            "p0": {"ready": False, "failure_code": "CYCLE_006_ATTEMPT_EXISTS"},
            "launch_binding_sha256": launch,
            "binding": None,
            "live_start_authorization": "PRESENT",
            "one_attempt": True,
            "retry_count": 0,
            "replacement_count": 0,
            "storage_occupied": True,
            "start_allowed": False,
            "proof_identity": readback.proof_attempt_id,
            "model_invocation_count": model_count,
            "task_transmission_count": model_count,
            "post_a1_readback_sha256": self._post_a1_readback_sha256,
            "a3_overlay_sha256": self._a3_overlay_sha256,
            "journal_sha256": readback.journal_sha256,
            "anchor_sha256": readback.anchor_sha256,
            "readback_sha256": readback.readback_sha256,
            "failure_code": readback.failure_reason or self._terminal_failure_code,
            "receipt_sha256": self._receipt_sha256,
            "manifest_sha256": self._manifest_sha256,
            "real_after": None,
            "artifact_behavior": "NOT_RUN",
            "comparison_result": "NOT_ESTABLISHED",
            "publication_authorized": False,
        }

    def snapshot(self, base_snapshot: Mapping[str, Any]) -> dict[str, Any]:
        with self._lock:
            if os.path.lexists(self.spec.storage_root):
                try:
                    return self._durable_projection()
                except Exception:
                    return {
                        "cycle_key": CYCLE_KEY,
                        "cycle_number": CYCLE_NUMBER,
                        "candidate_id": CANDIDATE_ID,
                        "state": "INTEGRITY_FAILURE",
                        "stage": "proof-open",
                        "p0": {
                            "ready": False,
                            "failure_code": "PROOF_STORAGE_INTEGRITY_FAILURE",
                        },
                        "launch_binding_sha256": None,
                        "binding": None,
                        "live_start_authorization": (
                            "PRESENT"
                            if self.spec.live_start_authorization_observed_at
                            else "ABSENT"
                        ),
                        "one_attempt": True,
                        "retry_count": 0,
                        "replacement_count": 0,
                        "storage_occupied": True,
                        "start_allowed": False,
                        "proof_identity": None,
                        "model_invocation_count": None,
                        "task_transmission_count": None,
                        "artifact_behavior": "NOT_RUN",
                        "comparison_result": "NOT_ESTABLISHED",
                    }
            p0 = self._p0(base_snapshot)
            authorized = self.spec.live_start_authorization_observed_at is not None
            return {
                "cycle_key": CYCLE_KEY,
                "cycle_number": CYCLE_NUMBER,
                "candidate_id": CANDIDATE_ID,
                "state": "READY" if p0.ready else "NOT_READY",
                "stage": "P0",
                "p0": {"ready": p0.ready, "failure_code": p0.failure_code},
                "launch_binding_sha256": p0.launch_binding_sha256,
                "binding": (
                    self._public_binding(p0.binding)
                    if p0.binding is not None
                    else None
                ),
                "live_start_authorization": (
                    "PRESENT" if authorized else "ABSENT"
                ),
                "one_attempt": True,
                "retry_count": 0,
                "replacement_count": 0,
                "storage_occupied": False,
                "start_allowed": bool(p0.ready and authorized),
                "proof_identity": None,
                "model_invocation_count": 0,
                "task_transmission_count": 0,
                "real_after": None,
                "artifact_behavior": "NOT_RUN",
                "comparison_result": "NOT_ESTABLISHED",
                "publication_authorized": False,
            }

    def start(self, launch_binding_sha256: str) -> None:
        """Open and dispatch only after exact P0 plus explicit live authority."""

        if not isinstance(launch_binding_sha256, str) or not _SHA256.fullmatch(
            launch_binding_sha256
        ):
            raise CreatorLiveCycle006Error(
                "LAUNCH_BINDING_INVALID", http_status=400
            )
        authorization = self.spec.live_start_authorization_observed_at
        with self._lock:
            if (
                self._active
                or os.path.lexists(self.spec.storage_root)
                or (authorization is not None and self._starting)
            ):
                raise CreatorLiveCycle006Error("CYCLE_006_ATTEMPT_EXISTS")
            if authorization is not None:
                self._starting = True
        try:
            try:
                base_snapshot = self.controller.snapshot()
            except Exception as exc:
                raise CreatorLiveCycle006Error("P0_STATE_UNAVAILABLE") from exc
            p0 = self._p0(base_snapshot)
            if not p0.ready or p0.launch_binding_sha256 is None:
                raise CreatorLiveCycle006Error(p0.failure_code or "P0_NOT_READY")
            if launch_binding_sha256 != p0.launch_binding_sha256:
                raise CreatorLiveCycle006Error("LAUNCH_BINDING_STALE")
            if authorization is None:
                raise CreatorLiveCycle006Error("LIVE_START_AUTHORIZATION_ABSENT")
            try:
                confirmed_snapshot = self.controller.snapshot()
            except Exception as exc:
                raise CreatorLiveCycle006Error("P0_STATE_UNAVAILABLE") from exc
            confirmed_p0 = self._p0(confirmed_snapshot)
            if (
                not confirmed_p0.ready
                or confirmed_p0.binding is None
                or confirmed_p0.launch_binding_sha256
                != launch_binding_sha256
            ):
                raise CreatorLiveCycle006Error(
                    confirmed_p0.failure_code or "P0_STATE_CHANGED_BEFORE_OPEN"
                )
            p0 = confirmed_p0
            repository = self.spec.repository.resolve(strict=True)
            try:
                final_snapshot = self.controller.snapshot()
            except Exception as exc:
                raise CreatorLiveCycle006Error(
                    "P0_STATE_UNAVAILABLE"
                ) from exc
            final_p0 = self._p0(final_snapshot)
            if (
                not final_p0.ready
                or final_p0.binding is None
                or final_p0.launch_binding_sha256
                != launch_binding_sha256
                or final_p0.binding != confirmed_p0.binding
            ):
                raise CreatorLiveCycle006Error(
                    final_p0.failure_code or "P0_STATE_CHANGED_BEFORE_OPEN"
                )
            p0 = final_p0
            expected_repository = p0.binding.get("repository")
            if not isinstance(expected_repository, Mapping):
                raise CreatorLiveCycle006Error("P0_REPOSITORY_IDENTITY_INVALID")
            source = FieldNoteSourceRepositoryIdentity(
                repository_id=repository_id(repository),
                source_commit=git_output(repository, "rev-parse", "HEAD"),
            )
            if (
                source.repository_id
                != expected_repository.get("repository_id")
                or source.source_commit != expected_repository.get("head")
            ):
                raise CreatorLiveCycle006Error(
                    "P0_REPOSITORY_CHANGED_BEFORE_PROOF_OPEN"
                )
            proof_id = future_proof_identity(launch_binding_sha256)
            run_1_id = "run_a7_creator_live_cycle_006_1_" + launch_binding_sha256
            attempt = FieldNoteCreatorLiveAttempt(
                proof_attempt_id=proof_id,
                proof_mode="CREATOR_LIVE",
                creator_id="Shin",
                authorization_observed_at=authorization,
            )
            self._require_runtime_binary_identity()
            try:
                runtime = self.runtime_opener(
                    self.spec.storage_root,
                    attempt=attempt,
                    source_repository=source,
                    run_1_id=run_1_id,
                    runtime=self.spec.runtime,
                    terminal_projection_binding=_terminal_projection_binding(p0),
                )
            except FieldNoteCreatorLiveAttemptExistsError as exc:
                raise CreatorLiveCycle006Error("CYCLE_006_ATTEMPT_EXISTS") from exc
            except Exception as exc:
                raise CreatorLiveCycle006Error("PROOF_OPEN_FAILED") from exc
            with self._lock:
                self._runtime = runtime
                self._starting = False
                self._active = True
                self._stage = "proof-open"
                try:
                    self._worker = self.worker_factory(
                        target=self._run_sequence,
                        args=(runtime, source, p0),
                        name="decision-os-creator-live-cycle-006",
                        daemon=True,
                    )
                    self._worker.start()
                except Exception as exc:
                    self._active = False
                    self._fail_open_runtime(
                        runtime,
                        "CYCLE_006_COORDINATOR_START_FAILED",
                    )
                    raise CreatorLiveCycle006Error(
                        "CYCLE_006_COORDINATOR_START_FAILED"
                    ) from exc
        except Exception:
            with self._lock:
                self._starting = False
            raise
