"""Authenticated production entrypoint for the fixed Creator-Live Cycle 005."""

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
from typing import Any, Callable, Mapping, Protocol

from decision_os.acceleration.codex_adapter import CodexRuntimeIdentity
from decision_os.acceleration.model import git_output, repository_id
from decision_os.companion.field_notes_creator_live import (
    CREATOR_LIVE_ANCHOR_FILENAME,
    CREATOR_LIVE_ANCHOR_FILENAME_V2,
    CREATOR_LIVE_ANCHOR_FILENAME_V3,
    CREATOR_LIVE_JOURNAL_FILENAME,
    CREATOR_LIVE_JOURNAL_FILENAME_V2,
    CREATOR_LIVE_JOURNAL_FILENAME_V3,
    FieldNoteCreatorLiveA3CompilerAudit,
    FieldNoteCreatorLiveA3RejectionCounts,
    FieldNoteCreatorLiveAttemptExistsError,
    FieldNoteCreatorLiveContractIdentity,
    FieldNoteCreatorLiveHistoricalBoundary,
    FieldNoteCreatorLiveProofRuntime,
    FieldNoteCreatorLiveRun2OutputIdentity,
    FieldNoteCreatorLiveTaskIdentity,
    FieldNoteCreatorLiveTerminalProjectionBinding,
    FieldNoteCreatorLiveTraceReadbackV2,
    FieldNoteCreatorLiveTraceReadbackV3,
)
from decision_os.companion.field_notes_creator_live_capture import (
    FieldNoteCreatorLiveA1CaptureBridge,
)
from decision_os.companion.field_notes_creator_live_reconnect import (
    FieldNoteCreatorLiveA2ReconnectBridge,
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
from decision_os.companion.guided_intake import _quoted_payload_boundary
from decision_os.companion.field_notes_reuse import (
    FieldNoteIdentity,
    FieldNoteOutcomeEvaluation,
    FieldNoteReuseClaim,
    FieldNoteReuseDisposition,
    FieldNoteUseEvidence,
    assess_field_note_reuse,
    bind_field_note_structure,
)
from decision_os.companion.field_notes_whole_flow import (
    FieldNoteCreatorLiveAttempt,
    FieldNoteSourceRepositoryIdentity,
    FieldNoteWholeFlowEvidenceBundle,
    FieldNoteWholeFlowRunIdentity,
    build_portable_candidate_warehouse_manifest,
    verify_field_note_whole_flow,
)


CYCLE_KEY = "cycle-005"
CYCLE_AUTHORIZATION_OBSERVED_AT = "2026-08-05T06:22:00Z"
IMPLEMENTATION_AUTHORIZATION_OBSERVED_AT = "2026-08-05T12:28:00Z"
EXPECTED_REPOSITORY = Path(
    "/Users/sn/Documents/v13/decision-os-v13-loopkit"
)
EXPECTED_REMOTE = "https://github.com/shin4141/decision-os-v13-loopkit.git"
EXPECTED_CONTRACT_PROFILE = "ORDINARY_USER_PATH_CONTRACT_APPROVED_CANDIDATE_V0_1"
EXPECTED_CONTRACT_TITLE = "Ordinary User Path Contract v0.1 — APPROVED CANDIDATE"
EXPECTED_CONTRACT_BYTES = 11_039
EXPECTED_CONTRACT_SHA256 = (
    "519bd39305af1a3a7cc35e61e1b9cfc742c5723d0cc64d0d970b070d0e65068e"
)
EXPECTED_WRAPPER_SHA256 = (
    "c3de6236a450666d8a8ef59a8f8db303bf4654cc9cb20d6ab816f3066177b11e"
)
EXPECTED_INTERPRETATION_SHA256 = (
    "7503f4b01c7c05c9ec3aed8855c9fd538c66b9b3b38840f423ec41c2101f4dd7"
)
EXPECTED_EXECUTION_AUTHORITY = "INTERPRETATION_ONLY"
EXPECTED_FREEZE_AUTHORITY = "IMMUTABLE_INTERPRETATION_ONLY"
EXPECTED_GATE = "CLEAR ENOUGH TO FREEZE"

EXPECTED_RUNTIME = CodexRuntimeIdentity(
    model="gpt-5.6-sol",
    reasoning_effort="ultra",
    service_tier="priority",
    codex_cli_version="0.146.0-alpha.3.1",
    account_type="chatgpt",
)

RUN_1_TASK = """Read only
validation/a7_creator_live_whole_flow_reentry_charter_v0_1.md.

Identify one reusable execution-identity rule that distinguishes:

- an implementation or product-code baseline; and
- the repository HEAD containing a merged execution Charter.

Propose exactly one new Field Note through the authorized Field Note proposal
path.

The proposed Note must preserve these bounded points:

- implementation baseline and execution repository HEAD are separate identities;
- documentation-only Charter bytes need not be packaged into the runtime build;
- execution must bind both identities explicitly;
- a later repository commit requires bounded requalification or a Charter delta.

Do not write or modify repository files.
Do not request direct write.
Do not make more than one Field Note proposal.
After the one proposal, stop."""

RUN_2_TASK = """Use the exact reconnected Field Note from Run 1 to evaluate this proposed
execution decision:

“A documentation-only execution Charter was merged after product code baseline
X. The installed runtime matches code baseline X. Repository main later moved
to commit Y after the Charter merge. Because the runtime code did not change,
execution may proceed without recording Y or requalifying the repository.”

Return a bounded verdict.

Demonstrate use of one exact structure from the reconnected Note through
RULE_TRACE or OUTPUT_ARTIFACT.

The evidence must identify the exact Note, exact bounded structure, exact Run 2,
and how that structure affected the verdict.

Generic similarity, correct task output, or an unsupported statement that the
Note was useful is insufficient.

Do not propose another Field Note.
Do not write or modify repository files."""

RUN_1_TASK_SHA256 = (
    "e377fb2f9e003f3f04e8d1b10d2aef96347416d86f78305102d4671519ed3417"
)
RUN_2_TASK_SHA256 = (
    "688203fd91c880cb4c9e32619219e9e660160b31fded0ae630ae2a401ea6cdcf"
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_PROOF_FILENAMES = (
    CREATOR_LIVE_JOURNAL_FILENAME,
    CREATOR_LIVE_ANCHOR_FILENAME,
    CREATOR_LIVE_JOURNAL_FILENAME_V2,
    CREATOR_LIVE_ANCHOR_FILENAME_V2,
    CREATOR_LIVE_JOURNAL_FILENAME_V3,
    CREATOR_LIVE_ANCHOR_FILENAME_V3,
)
NOT_DURABLY_PERSISTED = "NOT_DURABLY_PERSISTED"

PROTECTED_HISTORY: tuple[tuple[str, str], ...] = (
    (
        ".decision-os/field-notes/2026-08-03-topmost-canonical-state-restart-guard-lcmwhjvkpf.md",
        "3c2e45460f21a2346a8d100ebfefc6ed079994e687a70911e5f4a8954cf2d05d",
    ),
    (
        ".decision-os/field-notes/2026-08-04-bind-product-code-baseline-and-ws4unkvwfe.md",
        "dab6f42bd2c8e6a1e3f31f6f2fb8f260c380a11151bea92cfab868f8e85d2446",
    ),
    (
        ".decision-os/field-notes/2026-08-05-bind-governed-execution-to-both-nnyn57esbq.md",
        "e3f49d578dd525c0a8c8ffdf90374c50ab00167e684fbdae991d7d2d24ff9cdd",
    ),
    (
        ".decision-os/field-notes/proofs/proof_a7_creator_live_002_1d4c714b11c3f614/creator-live-proof-v0.1.jsonl",
        "8d346c5f57f28c105ec84c640e21649c1d6b31274614bc8d2fc56737f8aec99c",
    ),
    (
        ".decision-os/field-notes/proofs/proof_a7_creator_live_002_1d4c714b11c3f614/creator-live-proof-v0.1.anchor.jsonl",
        "3ccbd87e9ff4b8871f7009bf925e5acfe9111378509bd38d8764d23a9fc5344c",
    ),
    (
        ".decision-os/field-notes/proofs/proof_a7_creator_live_003_94a0d625f4d155f5/creator-live-proof-v0.1.jsonl",
        "d310a5a7131f78dab8a999e97a941748b7713f102adb44c54cb9e5be8dd0efd1",
    ),
    (
        ".decision-os/field-notes/proofs/proof_a7_creator_live_003_94a0d625f4d155f5/creator-live-proof-v0.1.anchor.jsonl",
        "0ba29aadef6267e902182a918bb0e9bc9b73eef3dd2fb60ec9c429c9fbaa44dc",
    ),
    (
        ".decision-os/field-notes/proofs/proof_a7_creator_live_004_862c2f5cfdf7b134/creator-live-proof-v0.1.jsonl",
        "af0906977646897fa6bb279f512372998404974a5b581070fe5e1e94f9fd4c4a",
    ),
    (
        ".decision-os/field-notes/proofs/proof_a7_creator_live_004_862c2f5cfdf7b134/creator-live-proof-v0.1.anchor.jsonl",
        "349b3298379f88cd2ea62f454c486ac857bc71e16614b7e8de4906e802b80331",
    ),
    (
        ".decision-os/field-notes/proofs/proof_a7_creator_live_005_1f0c0263566af0a8/creator-live-proof-v0.1.jsonl",
        "5e329626cc9b23fa800ddf53fc2a5ff637a38da58442d1e1c01d7eee00a27f6b",
    ),
    (
        ".decision-os/field-notes/proofs/proof_a7_creator_live_005_1f0c0263566af0a8/creator-live-proof-v0.1.anchor.jsonl",
        "c434ff5e4e38b45bd8f8d497fb51d11bcc5ad050d8e29ed2025b514e0bb9a4d0",
    ),
)


class _Controller(Protocol):
    def creator_live_a1_completed_draft(self, *, expected_run_id: str) -> Any: ...
    def creator_live_a2_run_completion(self, *, expected_run_id: str) -> Any: ...
    def release_creator_live_a2_run_completion(
        self,
        *,
        expected_run_id: str,
    ) -> None: ...


class CreatorLiveEntrypointError(RuntimeError):
    """One bounded public start request failed closed."""

    def __init__(self, code: str, *, http_status: int = 409) -> None:
        super().__init__(code)
        self.code = code
        self.http_status = http_status


@dataclass(frozen=True)
class CreatorLiveCycle005Spec:
    repository: Path = EXPECTED_REPOSITORY
    remote: str = EXPECTED_REMOTE
    cycle_key: str = CYCLE_KEY
    cycle_authorization_observed_at: str = CYCLE_AUTHORIZATION_OBSERVED_AT
    implementation_authorization_observed_at: str = (
        IMPLEMENTATION_AUTHORIZATION_OBSERVED_AT
    )
    runtime: CodexRuntimeIdentity = EXPECTED_RUNTIME
    run_1_task: str = RUN_1_TASK
    run_2_task: str = RUN_2_TASK
    protected_history: tuple[tuple[str, str], ...] = PROTECTED_HISTORY

    @property
    def storage_root(self) -> Path:
        return self.repository / ".decision-os/field-notes/proofs/cycle-005"


@dataclass(frozen=True)
class CreatorLiveP0Result:
    ready: bool
    failure_code: str | None
    binding: dict[str, Any] | None
    launch_binding_sha256: str | None


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _strict_object(raw: bytes, label: str) -> dict[str, Any]:
    def pairs(value: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in value:
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
    rows = []
    for path in sorted(
        files,
        key=lambda item: item.relative_to(runtime_root).as_posix().encode("utf-8"),
    ):
        relative = path.relative_to(runtime_root).as_posix()
        rows.append(f"{_sha256_bytes(path.read_bytes())}  {relative}\n")
    return _sha256_bytes("".join(rows).encode("utf-8"))


def _runtime_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _task_identities(spec: CreatorLiveCycle005Spec) -> dict[str, Any]:
    run_1 = spec.run_1_task.encode("utf-8")
    run_2 = spec.run_2_task.encode("utf-8")
    if (
        len(run_1) != 832
        or _sha256_bytes(run_1) != RUN_1_TASK_SHA256
        or len(run_2) != 856
        or _sha256_bytes(run_2) != RUN_2_TASK_SHA256
        or spec.run_1_task != spec.run_1_task.strip()
        or spec.run_2_task != spec.run_2_task.strip()
    ):
        raise ValueError("P0_TASK_IDENTITY_MISMATCH")
    return {
        "run_1": {
            "byte_count": len(run_1),
            "sha256": RUN_1_TASK_SHA256,
            "lane": "A1_ONLY",
        },
        "run_2": {
            "byte_count": len(run_2),
            "sha256": RUN_2_TASK_SHA256,
            "lane": "EXACT_A2_ONLY",
        },
    }


def _proof_artifacts_exist(root: Path) -> bool:
    return any(os.path.lexists(root / filename) for filename in _PROOF_FILENAMES)


def _proof_storage_occupied(root: Path) -> bool:
    if _proof_artifacts_exist(root):
        return True
    if not os.path.lexists(root):
        return False
    if root.is_symlink() or not root.is_dir():
        return True
    try:
        return next(root.iterdir(), None) is not None
    except OSError:
        return True


@dataclass(frozen=True)
class _A3CompilerScan:
    candidates: tuple[tuple[int, int, bytes, int], ...]
    longest_candidate_byte_count: int
    winners: tuple[tuple[int, int, bytes, int], ...]
    rejection_counts: FieldNoteCreatorLiveA3RejectionCounts


def _validate_run_2_output_artifact_inputs(
    *,
    note: FieldNoteIdentity,
    note_bytes: bytes,
    final_output_bytes: bytes,
    final_output_sha256: str,
) -> None:
    if (
        not isinstance(note_bytes, bytes)
        or _sha256_bytes(note_bytes) != note.note_sha256
        or not isinstance(final_output_bytes, bytes)
        or not final_output_bytes
        or _sha256_bytes(final_output_bytes) != final_output_sha256
        or note_bytes in final_output_bytes
    ):
        raise ValueError("A3_OUTPUT_ARTIFACT_IDENTITY_INVALID")
    try:
        note_bytes.decode("utf-8")
        final_output_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("A3_OUTPUT_ARTIFACT_UTF8_INVALID") from exc
    for identity in (
        note.note_path,
        note.field_note_id,
        note.note_sha256,
    ):
        if identity.encode("utf-8") not in final_output_bytes:
            raise ValueError("A3_OUTPUT_ARTIFACT_LINEAGE_MISSING")


def _scan_run_2_output_artifact(
    *,
    note_bytes: bytes,
    final_output_bytes: bytes,
) -> _A3CompilerScan:
    candidates: list[tuple[int, int, bytes, int]] = []
    rejection_counts = {
        "below_minimum_byte_length": 0,
        "whole_note_range": 0,
        "non_unique_source_occurrence": 0,
        "absent_output_occurrence": 0,
        "multiple_output_occurrences": 0,
    }
    for match in re.finditer(rb"[^\r\n]+", note_bytes):
        structure = match.group(0)
        below_minimum = len(structure.strip()) < 32
        whole_note = match.start() == 0 and match.end() == len(note_bytes)
        source_occurrences = note_bytes.count(structure)
        output_occurrences = final_output_bytes.count(structure)
        if below_minimum:
            rejection_counts["below_minimum_byte_length"] += 1
        if whole_note:
            rejection_counts["whole_note_range"] += 1
        if source_occurrences != 1:
            rejection_counts["non_unique_source_occurrence"] += 1
        if output_occurrences == 0:
            rejection_counts["absent_output_occurrence"] += 1
        elif output_occurrences > 1:
            rejection_counts["multiple_output_occurrences"] += 1
        if (
            below_minimum
            or whole_note
            or source_occurrences != 1
            or output_occurrences != 1
        ):
            continue
        candidates.append(
            (
                match.start(),
                match.end(),
                structure,
                final_output_bytes.index(structure),
            )
        )
    longest = max((len(item[2]) for item in candidates), default=0)
    winners = tuple(item for item in candidates if len(item[2]) == longest)
    return _A3CompilerScan(
        candidates=tuple(candidates),
        longest_candidate_byte_count=longest,
        winners=winners,
        rejection_counts=FieldNoteCreatorLiveA3RejectionCounts(
            **rejection_counts
        ),
    )


def _claim_from_a3_winner(
    *,
    note: FieldNoteIdentity,
    note_bytes: bytes,
    run_2_id: str,
    final_output_sha256: str,
    observed_at: str,
    winner: tuple[int, int, bytes, int],
) -> FieldNoteReuseClaim:
    start, end, structure, output_start = winner
    binding = bind_field_note_structure(
        note,
        note_bytes,
        structure_id=f"exact-utf8-line:{start}:{end}",
        start_byte=start,
        end_byte=end,
    )
    evidence = FieldNoteUseEvidence(
        evidence_class="OUTPUT_ARTIFACT",
        evidence_origin="IMMEDIATE_COMPLETION_RECORD",
        reusing_run_id=run_2_id,
        structure_binding=binding,
        evidence_ref=(
            f"run:{run_2_id}:final-output:bytes:"
            f"{output_start}:{output_start + len(structure)}"
        ),
        evidence_sha256=final_output_sha256,
        observer_id=run_2_id,
        observer_relation="REUSING_RUN_SELF",
        as_of=observed_at,
    )
    return FieldNoteReuseClaim(
        claimed_note=note,
        reusing_run_id=run_2_id,
        use_evidence=evidence,
        outcome_evaluation=FieldNoteOutcomeEvaluation(
            outcome="UNKNOWN",
            scope="Cycle 005 Run 2 bounded verdict output.",
            observer_id=run_2_id,
            observer_relation="REUSING_RUN_SELF",
            as_of=observed_at,
            causal_evidence_ref=f"run:{run_2_id}:final-output",
            causal_evidence_sha256=final_output_sha256,
            contribution_separated=False,
        ),
        human_intervention="NONE",
        disposition=FieldNoteReuseDisposition(
            action="HOLD",
            reevaluation_condition=(
                "Independent evidence may later confirm the exact structure's "
                "bounded contribution."
            ),
        ),
    )


def compile_run_2_output_artifact(
    *,
    note: FieldNoteIdentity,
    note_bytes: bytes,
    run_2_id: str,
    final_output_bytes: bytes,
    final_output_sha256: str,
    observed_at: str,
) -> FieldNoteReuseClaim:
    """Compile only a unique, exact, non-whole UTF-8 output-artifact claim."""

    _validate_run_2_output_artifact_inputs(
        note=note,
        note_bytes=note_bytes,
        final_output_bytes=final_output_bytes,
        final_output_sha256=final_output_sha256,
    )
    scan = _scan_run_2_output_artifact(
        note_bytes=note_bytes,
        final_output_bytes=final_output_bytes,
    )
    if not scan.candidates:
        raise ValueError("A3_EXACT_STRUCTURE_MISSING")
    if len(scan.winners) != 1:
        raise ValueError("A3_EXACT_STRUCTURE_AMBIGUOUS")
    return _claim_from_a3_winner(
        note=note,
        note_bytes=note_bytes,
        run_2_id=run_2_id,
        final_output_sha256=final_output_sha256,
        observed_at=observed_at,
        winner=scan.winners[0],
    )


def compile_run_2_output_artifact_audited(
    *,
    note: FieldNoteIdentity,
    note_bytes: bytes,
    run_2_id: str,
    final_output_bytes: bytes,
    output_identity: FieldNoteCreatorLiveRun2OutputIdentity,
) -> tuple[
    tuple[int, int, bytes, int] | None,
    FieldNoteCreatorLiveA3CompilerAudit,
]:
    """Return transient winner facts plus their content-free typed audit."""

    if (
        not isinstance(output_identity, FieldNoteCreatorLiveRun2OutputIdentity)
        or output_identity.run_id != run_2_id
        or output_identity.final_output_byte_count != len(final_output_bytes)
        or output_identity.final_output_sha256
        != _sha256_bytes(final_output_bytes)
    ):
        raise ValueError("A3_OUTPUT_ARTIFACT_IDENTITY_INVALID")
    _validate_run_2_output_artifact_inputs(
        note=note,
        note_bytes=note_bytes,
        final_output_bytes=final_output_bytes,
        final_output_sha256=output_identity.final_output_sha256,
    )
    scan = _scan_run_2_output_artifact(
        note_bytes=note_bytes,
        final_output_bytes=final_output_bytes,
    )
    winner = scan.winners[0] if len(scan.winners) == 1 else None
    terminal_a3_code = (
        None
        if winner is not None
        else "A3_EXACT_STRUCTURE_MISSING"
        if not scan.candidates
        else "A3_EXACT_STRUCTURE_AMBIGUOUS"
    )
    audit = FieldNoteCreatorLiveA3CompilerAudit.issue(
        proof_attempt_id=output_identity.proof_attempt_id,
        run_id=run_2_id,
        output_artifact_id=output_identity.output_artifact.artifact_id,
        source_note_byte_count=len(note_bytes),
        source_note_sha256=note.note_sha256,
        output_byte_count=len(final_output_bytes),
        output_sha256=output_identity.final_output_sha256,
        eligible_candidate_count=len(scan.candidates),
        rejection_counts=scan.rejection_counts,
        longest_candidate_byte_count=scan.longest_candidate_byte_count,
        winning_candidate_count=len(scan.winners),
        selected_source_start_byte=(winner[0] if winner is not None else None),
        selected_source_end_byte=(winner[1] if winner is not None else None),
        selected_output_start_byte=(winner[3] if winner is not None else None),
        selected_output_end_byte=(
            winner[3] + len(winner[2]) if winner is not None else None
        ),
        terminal_a3_code=terminal_a3_code,
    )
    return winner, audit


def _claim_from_verified_a3_audit(
    *,
    note: FieldNoteIdentity,
    note_bytes: bytes,
    run_2_id: str,
    output_identity: FieldNoteCreatorLiveRun2OutputIdentity,
    observed_at: str,
    winner: tuple[int, int, bytes, int],
    audit: FieldNoteCreatorLiveA3CompilerAudit,
) -> FieldNoteReuseClaim:
    start, end, structure, output_start = winner
    if (
        audit.proof_attempt_id != output_identity.proof_attempt_id
        or audit.run_id != run_2_id
        or audit.output_artifact_id
        != output_identity.output_artifact.artifact_id
        or audit.source_note_byte_count != len(note_bytes)
        or audit.source_note_sha256 != note.note_sha256
        or audit.output_byte_count != output_identity.final_output_byte_count
        or audit.output_sha256 != output_identity.final_output_sha256
        or audit.winning_candidate_count != 1
        or audit.terminal_a3_code is not None
        or audit.selected_source_start_byte != start
        or audit.selected_source_end_byte != end
        or audit.selected_output_start_byte != output_start
        or audit.selected_output_end_byte != output_start + len(structure)
        or note_bytes[start:end] != structure
    ):
        raise ValueError("A3_COMPILER_AUDIT_READBACK_MISMATCH")
    return _claim_from_a3_winner(
        note=note,
        note_bytes=note_bytes,
        run_2_id=run_2_id,
        final_output_sha256=output_identity.final_output_sha256,
        observed_at=observed_at,
        winner=winner,
    )


def _terminal_projection_binding_from_p0(
    p0: CreatorLiveP0Result,
) -> FieldNoteCreatorLiveTerminalProjectionBinding:
    binding = p0.binding
    if p0.launch_binding_sha256 is None or not isinstance(binding, Mapping):
        raise ValueError("P0_TERMINAL_PROJECTION_BINDING_UNAVAILABLE")
    contract = binding.get("contract")
    tasks = binding.get("tasks")
    authorizations = binding.get("authorizations")
    historical = binding.get("historical_boundary")
    if (
        not isinstance(contract, Mapping)
        or not isinstance(tasks, Mapping)
        or not isinstance(authorizations, Mapping)
        or not isinstance(historical, Mapping)
        or not isinstance(tasks.get("run_1"), Mapping)
        or not isinstance(tasks.get("run_2"), Mapping)
    ):
        raise ValueError("P0_TERMINAL_PROJECTION_BINDING_UNAVAILABLE")
    run_1_task = tasks["run_1"]
    run_2_task = tasks["run_2"]
    return FieldNoteCreatorLiveTerminalProjectionBinding.create(
        launch_binding_sha256=p0.launch_binding_sha256,
        contract_identity=FieldNoteCreatorLiveContractIdentity(
            profile=contract.get("profile"),
            title=contract.get("title"),
            source_byte_count=contract.get("source_byte_count"),
            source_sha256=contract.get("source_sha256"),
            wrapper_sha256=contract.get("wrapper_sha256"),
            interpretation_sha256=contract.get("interpretation_sha256"),
        ),
        ordinary_contract_execution_authority=contract.get(
            "ordinary_contract_execution_authority"
        ),
        guided_intake_freeze_authority=contract.get(
            "guided_intake_freeze_authority_state"
        ),
        implementation_authorization_observed_at=authorizations.get(
            "implementation_observed_at"
        ),
        run_1_task=FieldNoteCreatorLiveTaskIdentity(
            byte_count=run_1_task.get("byte_count"),
            sha256=run_1_task.get("sha256"),
        ),
        run_2_task=FieldNoteCreatorLiveTaskIdentity(
            byte_count=run_2_task.get("byte_count"),
            sha256=run_2_task.get("sha256"),
        ),
        historical_boundary=FieldNoteCreatorLiveHistoricalBoundary(
            cycle_key=historical.get("cycle_key"),
            state=historical.get("state"),
            failure_boundary=historical.get("failure_boundary"),
            failure_code=historical.get("failure_code"),
        ),
    )


class CreatorLiveCycle005Entrypoint:
    """Own P0, one durable attempt, and the content-free Cycle projection."""

    def __init__(
        self,
        controller: _Controller,
        *,
        spec: CreatorLiveCycle005Spec | None = None,
        now: Callable[[], str] = _utc_now,
        runtime_opener: Callable[..., FieldNoteCreatorLiveProofRuntime] = (
            FieldNoteCreatorLiveProofRuntime.open_attempt
        ),
        worker_factory: Callable[..., Any] = threading.Thread,
    ) -> None:
        self.controller = controller
        self.spec = spec or CreatorLiveCycle005Spec()
        self.now = now
        self.runtime_opener = runtime_opener
        self.worker_factory = worker_factory
        self._lock = threading.RLock()
        self._runtime: FieldNoteCreatorLiveProofRuntime | None = None
        self._worker: threading.Thread | None = None
        self._starting = False
        self._active = False
        self._stage = "P0"
        self._terminal_state: str | None = None
        self._terminal_failure_code: str | None = None
        self._receipt_sha256: str | None = None
        self._manifest_sha256: str | None = None

    @property
    def mutation_blocked(self) -> bool:
        with self._lock:
            return self._starting or self._active

    def _git_common_dir(self, repository: Path) -> Path:
        value = _run_git(repository, "rev-parse", "--git-common-dir")
        path = Path(value)
        return (repository / path).resolve() if not path.is_absolute() else path

    def _p0(self, base_snapshot: Mapping[str, Any]) -> CreatorLiveP0Result:
        try:
            repository = self.spec.repository.resolve(strict=True)
            selected = base_snapshot.get("repository")
            if not isinstance(selected, Mapping) or Path(
                str(selected.get("path", ""))
            ).resolve(strict=True) != repository:
                raise ValueError("P0_REPOSITORY_PATH_MISMATCH")
            head = _run_git(repository, "rev-parse", "HEAD")
            local_main = _run_git(repository, "rev-parse", "main")
            origin_main = _run_git(repository, "rev-parse", "origin/main")
            branch = _run_git(repository, "branch", "--show-current")
            remote = _run_git(repository, "remote", "get-url", "origin")
            if remote != self.spec.remote:
                raise ValueError("P0_REMOTE_MISMATCH")
            if branch != "main":
                raise ValueError("P0_BRANCH_MISMATCH")
            if head != local_main or head != origin_main:
                raise ValueError("P0_REVISION_MISMATCH")
            if (
                _run_git(
                    repository,
                    "status",
                    "--porcelain",
                    "--untracked-files=no",
                )
                or not _git_diff_clean(repository, cached=False)
            ):
                raise ValueError("P0_TRACKED_WORKTREE_DIRTY")
            if not _git_diff_clean(repository, cached=True):
                raise ValueError("P0_INDEX_DIRTY")
            common = self._git_common_dir(repository)
            operation_paths = (
                common / "MERGE_HEAD",
                common / "CHERRY_PICK_HEAD",
                common / "REVERT_HEAD",
                common / "REBASE_HEAD",
                common / "rebase-apply",
                common / "rebase-merge",
            )
            if any(path.exists() for path in operation_paths):
                raise ValueError("P0_GIT_OPERATION_ACTIVE")
            observed_repository_id = repository_id(repository)

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
            preparation_receipt_sha = technical.get("preparation_receipt_sha256")
            if not isinstance(freeze_receipt_sha, str) or not _SHA256.fullmatch(
                freeze_receipt_sha
            ):
                raise ValueError("P0_FREEZE_RECEIPT_IDENTITY_INVALID")
            if not isinstance(preparation_receipt_sha, str) or not _SHA256.fullmatch(
                preparation_receipt_sha
            ):
                raise ValueError("P0_PREPARATION_RECEIPT_IDENTITY_INVALID")

            guided_root = common / "decision-os/guided-intake-v0.1"
            guided_state = _strict_object(
                (guided_root / "state.json").read_bytes(),
                "Guided Intake state",
            )
            guided_record = guided_state.get("record")
            if not isinstance(guided_record, Mapping):
                raise ValueError("P0_GUIDED_STATE_INVALID")
            current_chain_head = guided_record.get("event_chain_head")
            if not isinstance(current_chain_head, str) or not _SHA256.fullmatch(
                current_chain_head
            ):
                raise ValueError("P0_CURRENT_CHAIN_HEAD_INVALID")
            events = (guided_root / "events.ndjson").read_bytes().splitlines()
            if len(events) < 2:
                raise ValueError("P0_EVENT_CHAIN_INCOMPLETE")
            previous_event = _strict_object(events[-2], "Previous Guided event")
            current_event = _strict_object(events[-1], "Current Guided event")
            predecessor_head = freeze_receipt.get("event_chain_head")
            if (
                current_event.get("event_hash") != current_chain_head
                or current_event.get("kind") != "INTAKE_FROZEN"
                or current_event.get("previous_event_hash") != predecessor_head
                or previous_event.get("event_hash") != predecessor_head
            ):
                raise ValueError("P0_EVENT_CHAIN_RELATIONSHIP_INVALID")
            freeze_receipt_path = guided_root / "receipts" / f"{freeze_receipt_sha}.json"
            freeze_receipt_bytes = freeze_receipt_path.read_bytes()
            if (
                _sha256_bytes(freeze_receipt_bytes) != freeze_receipt_sha
                or _strict_object(freeze_receipt_bytes, "Freeze receipt")
                != dict(freeze_receipt)
            ):
                raise ValueError("P0_FREEZE_RECEIPT_MISMATCH")
            ordinary_root = common / "decision-os/ordinary-user-path-v0.1"
            preparation_path = (
                ordinary_root
                / "preparation-receipts"
                / f"{preparation_receipt_sha}.json"
            )
            preparation_bytes = preparation_path.read_bytes()
            preparation = _strict_object(preparation_bytes, "Preparation receipt")
            if (
                _sha256_bytes(preparation_bytes) != preparation_receipt_sha
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
                or wrapper_identity.get("byte_size") != 11_946
                or source_identity.get("sha256") != EXPECTED_CONTRACT_SHA256
                or source_identity.get("byte_size") != EXPECTED_CONTRACT_BYTES
            ):
                raise ValueError("P0_CONTRACT_BYTE_IDENTITY_MISMATCH")
            wrapper_path = (
                guided_root
                / "original-requests"
                / f"{EXPECTED_WRAPPER_SHA256}.utf8"
            )
            wrapper_bytes = wrapper_path.read_bytes()
            if (
                len(wrapper_bytes) != 11_946
                or _sha256_bytes(wrapper_bytes) != EXPECTED_WRAPPER_SHA256
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
                or _sha256_bytes(source_bytes) != EXPECTED_CONTRACT_SHA256
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
            draft_bytes = (guided_root / "drafts" / f"{draft_sha}.json").read_bytes()
            if _sha256_bytes(draft_bytes) != draft_sha:
                raise ValueError("P0_CONTRACT_DRAFT_MISMATCH")
            frozen_sha = freeze.get("frozen_intake_sha256")
            if not isinstance(frozen_sha, str) or not _SHA256.fullmatch(frozen_sha):
                raise ValueError("P0_FROZEN_INTAKE_IDENTITY_INVALID")
            frozen_bytes = (guided_root / "freezes" / f"{frozen_sha}.json").read_bytes()
            if _sha256_bytes(frozen_bytes) != frozen_sha:
                raise ValueError("P0_FROZEN_INTAKE_MISMATCH")

            protected: list[dict[str, str]] = []
            for relative, expected_sha in self.spec.protected_history:
                target = repository / relative
                if (
                    not target.is_file()
                    or target.is_symlink()
                    or _sha256_bytes(target.read_bytes()) != expected_sha
                ):
                    raise ValueError("P0_PROTECTED_HISTORY_MISMATCH")
                protected.append({"path": relative, "sha256": expected_sha})

            source_product_tree = product_tree_sha256(repository)
            installed_product_tree = product_tree_sha256(_runtime_root())
            if source_product_tree != installed_product_tree:
                raise ValueError("P0_SOURCE_INSTALLED_PRODUCT_TREE_MISMATCH")
            tasks = _task_identities(self.spec)
            charter: list[dict[str, str]] = []
            for target in sorted(
                (repository / "validation").glob(
                    "a7_creator_live_whole_flow_reentry_charter*.md"
                ),
                key=lambda item: item.name.encode("utf-8"),
            ):
                charter.append(
                    {
                        "path": target.relative_to(repository).as_posix(),
                        "sha256": _sha256_bytes(target.read_bytes()),
                    }
                )
            if not charter:
                raise ValueError("P0_CHARTER_LINEAGE_MISSING")
            binding = {
                "schema": "decision-os.creator-live-cycle-005-launch-binding.v0.1",
                "cycle_key": self.spec.cycle_key,
                "repository": {
                    "path": str(repository),
                    "repository_id": observed_repository_id,
                    "head": head,
                    "local_main": local_main,
                    "origin_main": origin_main,
                    "branch": branch,
                    "remote": remote,
                    "tracked_worktree_clean": True,
                    "index_clean": True,
                    "git_operation_active": False,
                },
                "contract": {
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
                    "frozen_intake_sha256": freeze.get("frozen_intake_sha256"),
                    "freeze_receipt_sha256": freeze_receipt_sha,
                    "guided_intake_current_event_chain_head": current_chain_head,
                    "contract_preparation_receipt_event_chain_head": preparation.get(
                        "event_chain_head"
                    ),
                    "contract_freeze_receipt_event_chain_head": predecessor_head,
                    "ordinary_contract_execution_authority": (
                        EXPECTED_EXECUTION_AUTHORITY
                    ),
                    "guided_intake_freeze_authority_state": (
                        EXPECTED_FREEZE_AUTHORITY
                    ),
                    "gate": EXPECTED_GATE,
                },
                "authorizations": {
                    "cycle_observed_at": self.spec.cycle_authorization_observed_at,
                    "implementation_observed_at": (
                        self.spec.implementation_authorization_observed_at
                    ),
                },
                "runtime": {
                    "provider": "openai",
                    "account_type": self.spec.runtime.account_type,
                    "model": self.spec.runtime.model,
                    "reasoning_effort": self.spec.runtime.reasoning_effort,
                    "service_tier": self.spec.runtime.service_tier,
                    "codex_cli_version": self.spec.runtime.codex_cli_version,
                    "fresh_ephemeral_thread_per_run": True,
                    "provider_transport_required": True,
                    "model_sandbox_network_access": False,
                    "model_capabilities": {
                        "web": False,
                        "browser": False,
                        "general_url_access": False,
                        "mcp": False,
                        "plugins": False,
                        "apps": False,
                        "hooks": False,
                        "remote_plugins": False,
                        "multi_agent": False,
                        "shell_or_command_execution": False,
                        "dependency_installation": False,
                        "arbitrary_file_mutation": False,
                    },
                },
                "tasks": tasks,
                "attempt_policy": {
                    "one_attempt_no_retry": True,
                    "replacement_permitted": False,
                },
                "charter_lineage": charter,
                "protected_history": protected,
                "product": {
                    "source_tree_sha256": source_product_tree,
                    "installed_tree_sha256": installed_product_tree,
                },
                "historical_boundary": {
                    "cycle_key": "cycle-004",
                    "state": "FAILED",
                    "failure_boundary": "A1_CAPTURE",
                    "failure_code": "A1_CAPTURE_CHRONOLOGY_INVALID",
                },
            }
            digest = _sha256_bytes(canonical_json(binding).encode("utf-8"))
            return CreatorLiveP0Result(True, None, binding, digest)
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
            return CreatorLiveP0Result(False, code[:128], None, None)

    def _public_readback(
        self,
        runtime: FieldNoteCreatorLiveProofRuntime,
    ) -> dict[str, Any]:
        readback = runtime.read_back()
        if not readback.durable_readback_verified:
            raise ValueError("PROOF_STORAGE_INTEGRITY_FAILURE")
        prefix = "proof_a7_creator_live_cycle_005_"
        launch_binding_sha256 = readback.proof_attempt_id.removeprefix(prefix)
        if (
            not _SHA256.fullmatch(launch_binding_sha256)
            or readback.proof_attempt_id != prefix + launch_binding_sha256
        ):
            raise ValueError("PROOF_ATTEMPT_IDENTITY_INVALID")
        terminal_state = readback.state
        terminal_stage = (
            readback.failure_boundary
            if readback.state == "FAILED"
            else "A7"
            if readback.state == "TRACE_COMPLETE"
            else readback.current_stage
        )
        contract_identity: dict[str, Any] | str = NOT_DURABLY_PERSISTED
        ordinary_authority: str = NOT_DURABLY_PERSISTED
        freeze_authority: str = NOT_DURABLY_PERSISTED
        run_1_task: dict[str, Any] = {
            "byte_count": NOT_DURABLY_PERSISTED,
            "sha256": (
                readback.a1_capture_commit.task_sha256
                if readback.a1_capture_commit is not None
                else NOT_DURABLY_PERSISTED
            ),
        }
        run_2_task: dict[str, Any] = {
            "byte_count": NOT_DURABLY_PERSISTED,
            "sha256": NOT_DURABLY_PERSISTED,
        }
        implementation_authorization: str = NOT_DURABLY_PERSISTED
        historical_boundary: dict[str, Any] | str = NOT_DURABLY_PERSISTED
        retry_count: int | str = NOT_DURABLY_PERSISTED
        replacement_count: int | str = NOT_DURABLY_PERSISTED
        output_artifact: dict[str, Any] | str = NOT_DURABLY_PERSISTED
        compiler: dict[str, Any] | str = NOT_DURABLY_PERSISTED
        if isinstance(readback, FieldNoteCreatorLiveTraceReadbackV3):
            binding = readback.terminal_projection_binding
            contract = binding.contract_identity
            contract_identity = {
                "profile": contract.profile,
                "title": contract.title,
                "source_byte_count": contract.source_byte_count,
                "source_sha256": contract.source_sha256,
                "wrapper_sha256": contract.wrapper_sha256,
                "interpretation_sha256": contract.interpretation_sha256,
            }
            ordinary_authority = binding.ordinary_contract_execution_authority
            freeze_authority = binding.guided_intake_freeze_authority
            run_1_task = {
                "byte_count": binding.run_1_task.byte_count,
                "sha256": binding.run_1_task.sha256,
            }
            run_2_task = {
                "byte_count": binding.run_2_task.byte_count,
                "sha256": binding.run_2_task.sha256,
            }
            implementation_authorization = (
                binding.implementation_authorization_observed_at
            )
            historical = binding.historical_boundary
            historical_boundary = {
                "cycle_key": historical.cycle_key,
                "state": historical.state,
                "failure_boundary": historical.failure_boundary,
                "failure_code": historical.failure_code,
            }
            retry_count = binding.retry_count
            replacement_count = binding.replacement_count
            output = readback.run_2_output_identity
            if output is not None:
                artifact = output.output_artifact
                output_artifact = {
                    "schema": artifact.schema,
                    "artifact_id": artifact.artifact_id,
                    "proof_attempt_id": artifact.proof_attempt_id,
                    "run_id": artifact.run_id,
                    "transmission_ordinal": artifact.transmission_ordinal,
                    "media_type": artifact.media_type,
                    "byte_count": artifact.byte_count,
                    "sha256": artifact.sha256,
                }
            audit = readback.a3_compiler_audit
            if audit is not None:
                counts = audit.rejection_counts
                compiler = {
                    "compiler_version": audit.compiler_version,
                    "compiler_branch": audit.compiler_branch,
                    "source_note_byte_count": audit.source_note_byte_count,
                    "source_note_sha256": audit.source_note_sha256,
                    "output_artifact_id": audit.output_artifact_id,
                    "output_byte_count": audit.output_byte_count,
                    "output_sha256": audit.output_sha256,
                    "eligible_candidate_count": audit.eligible_candidate_count,
                    "rejection_counts": {
                        "below_minimum_byte_length": (
                            counts.below_minimum_byte_length
                        ),
                        "whole_note_range": counts.whole_note_range,
                        "non_unique_source_occurrence": (
                            counts.non_unique_source_occurrence
                        ),
                        "absent_output_occurrence": (
                            counts.absent_output_occurrence
                        ),
                        "multiple_output_occurrences": (
                            counts.multiple_output_occurrences
                        ),
                    },
                    "longest_candidate_byte_count": (
                        audit.longest_candidate_byte_count
                    ),
                    "winning_candidate_count": audit.winning_candidate_count,
                    "selected_source_start_byte": (
                        audit.selected_source_start_byte
                    ),
                    "selected_source_end_byte": audit.selected_source_end_byte,
                    "selected_output_start_byte": (
                        audit.selected_output_start_byte
                    ),
                    "selected_output_end_byte": audit.selected_output_end_byte,
                    "terminal_a3_code": audit.terminal_a3_code,
                    "audit_sha256": audit.audit_sha256,
                }
        elif not isinstance(readback, FieldNoteCreatorLiveTraceReadbackV2):
            raise ValueError("PROOF_READBACK_VERSION_UNSUPPORTED")
        return {
            "revision": readback.source_repository.source_commit,
            "contract_identity": contract_identity,
            "ordinary_contract_execution_authority": ordinary_authority,
            "guided_intake_freeze_authority": freeze_authority,
            "runtime": {
                "account_type": readback.runtime.account_type,
                "model": readback.runtime.model,
                "reasoning_effort": readback.runtime.reasoning_effort,
                "service_tier": readback.runtime.service_tier,
                "codex_cli_version": readback.runtime.codex_cli_version,
            },
            "run_1_task": run_1_task,
            "run_2_task": run_2_task,
            "cycle_authorization_observed_at": readback.authorization_observed_at,
            "implementation_authorization_observed_at": (
                implementation_authorization
            ),
            "historical_boundary": historical_boundary,
            "launch_binding_sha256": launch_binding_sha256,
            "proof_attempt_id": readback.proof_attempt_id,
            "proof_as_of": readback.terminal_proof_as_of,
            "journal_sha256": readback.journal_sha256,
            "anchor_sha256": readback.anchor_sha256,
            "readback_sha256": readback.readback_sha256,
            "terminal_state": terminal_state,
            "terminal_stage": terminal_stage,
            "failure_code": readback.failure_reason,
            "retry_count": retry_count,
            "replacement_count": replacement_count,
            "output_artifact": output_artifact,
            "compiler": compiler,
        }

    def snapshot(self, base_snapshot: Mapping[str, Any]) -> dict[str, Any]:
        with self._lock:
            root = self.spec.storage_root
            if self._runtime is not None:
                try:
                    identities = self._public_readback(self._runtime)
                    durable_state = identities["terminal_state"]
                    state = (
                        "RUNNING"
                        if self._active
                        else durable_state
                        if durable_state in {"FAILED", "TRACE_COMPLETE"}
                        else "OPEN_UNRESUMABLE"
                    )
                    stage = identities["terminal_stage"] or "proof-open"
                    return {
                        "cycle_key": self.spec.cycle_key,
                        "state": state,
                        "stage": stage,
                        "p0": {
                            "ready": False,
                            "failure_code": "CYCLE_005_ATTEMPT_EXISTS",
                        },
                        "launch_binding_sha256": identities[
                            "launch_binding_sha256"
                        ],
                        "binding": None,
                        "identities": identities,
                        "receipt_sha256": None,
                        "manifest_sha256": None,
                        "failure_code": identities["failure_code"],
                        "one_attempt_no_retry": True,
                        "replacement_permitted": False,
                        "storage_occupied": True,
                        "start_allowed": False,
                    }
                except Exception:
                    self._runtime = None
                    self._terminal_state = "INTEGRITY_FAILURE"
            if _proof_storage_occupied(root):
                try:
                    runtime = FieldNoteCreatorLiveProofRuntime.load_attempt(root)
                    readback = runtime.read_back()
                    if not readback.durable_readback_verified:
                        raise ValueError("PROOF_STORAGE_INTEGRITY_FAILURE")
                    self._runtime = runtime
                    state = (
                        readback.state
                        if readback.state in {"FAILED", "TRACE_COMPLETE"}
                        else "OPEN_UNRESUMABLE"
                    )
                    self._terminal_state = state
                    self._stage = (
                        readback.failure_boundary
                        if readback.state == "FAILED"
                        else "A7"
                        if readback.state == "TRACE_COMPLETE"
                        else readback.current_stage or "proof-open"
                    )
                    return self.snapshot(base_snapshot)
                except Exception:
                    return {
                        "cycle_key": self.spec.cycle_key,
                        "state": "INTEGRITY_FAILURE",
                        "stage": "proof-open",
                        "p0": {"ready": False, "failure_code": "PROOF_STORAGE_INTEGRITY_FAILURE"},
                        "launch_binding_sha256": None,
                        "binding": None,
                        "identities": None,
                        "receipt_sha256": None,
                        "manifest_sha256": None,
                        "failure_code": "PROOF_STORAGE_INTEGRITY_FAILURE",
                        "one_attempt_no_retry": True,
                        "replacement_permitted": False,
                        "storage_occupied": True,
                        "start_allowed": False,
                    }
            p0 = self._p0(base_snapshot)
            return {
                "cycle_key": self.spec.cycle_key,
                "state": "READY" if p0.ready else "NOT_READY",
                "stage": "P0",
                "p0": {"ready": p0.ready, "failure_code": p0.failure_code},
                "launch_binding_sha256": p0.launch_binding_sha256,
                "binding": p0.binding,
                "identities": None,
                "receipt_sha256": None,
                "manifest_sha256": None,
                "failure_code": p0.failure_code,
                "one_attempt_no_retry": True,
                "replacement_permitted": False,
                "storage_occupied": False,
                "start_allowed": p0.ready,
            }

    def start(self, launch_binding_sha256: str) -> dict[str, Any]:
        if not isinstance(launch_binding_sha256, str) or not _SHA256.fullmatch(
            launch_binding_sha256
        ):
            raise CreatorLiveEntrypointError(
                "LAUNCH_BINDING_INVALID",
                http_status=400,
            )
        with self._lock:
            if (
                self._starting
                or self._active
                or _proof_storage_occupied(self.spec.storage_root)
            ):
                raise CreatorLiveEntrypointError("CYCLE_005_ATTEMPT_EXISTS")
            self._starting = True
        try:
            base_snapshot = self.controller.snapshot()
        except Exception as exc:
            with self._lock:
                self._starting = False
            raise CreatorLiveEntrypointError("P0_STATE_UNAVAILABLE") from exc
        with self._lock:
            p0 = self._p0(base_snapshot)
            if not p0.ready or p0.launch_binding_sha256 is None:
                self._starting = False
                raise CreatorLiveEntrypointError(p0.failure_code or "P0_NOT_READY")
            if launch_binding_sha256 != p0.launch_binding_sha256:
                self._starting = False
                raise CreatorLiveEntrypointError("LAUNCH_BINDING_STALE")
            proof_attempt_id = (
                "proof_a7_creator_live_cycle_005_" + launch_binding_sha256
            )
            run_1_id = "run_a7_creator_live_cycle_005_1_" + launch_binding_sha256
            try:
                terminal_projection_binding = (
                    _terminal_projection_binding_from_p0(p0)
                )
                attempt = FieldNoteCreatorLiveAttempt(
                    proof_attempt_id=proof_attempt_id,
                    proof_mode="CREATOR_LIVE",
                    creator_id="Shin",
                    authorization_observed_at=(
                        self.spec.cycle_authorization_observed_at
                    ),
                )
                repository = self.spec.repository.resolve(strict=True)
                source = FieldNoteSourceRepositoryIdentity(
                    repository_id=repository_id(repository),
                    source_commit=git_output(repository, "rev-parse", "HEAD"),
                )
            except Exception as exc:
                self._starting = False
                raise CreatorLiveEntrypointError(
                    "P0_TERMINAL_PROJECTION_BINDING_UNAVAILABLE"
                    if str(exc).startswith("P0_TERMINAL_PROJECTION")
                    else "P0_REPOSITORY_IDENTITY_CHANGED"
                ) from exc
            try:
                runtime = self.runtime_opener(
                    self.spec.storage_root,
                    attempt=attempt,
                    source_repository=source,
                    run_1_id=run_1_id,
                    runtime=self.spec.runtime,
                    terminal_projection_binding=terminal_projection_binding,
                )
            except FieldNoteCreatorLiveAttemptExistsError as exc:
                self._starting = False
                raise CreatorLiveEntrypointError(
                    "CYCLE_005_ATTEMPT_EXISTS"
                ) from exc
            except Exception as exc:
                self._starting = False
                code = (
                    "PROOF_STORAGE_INTEGRITY_FAILURE"
                    if _proof_artifacts_exist(self.spec.storage_root)
                    else "PROOF_OPEN_FAILED"
                )
                raise CreatorLiveEntrypointError(code) from exc
            self._runtime = runtime
            self._starting = False
            self._active = True
            self._stage = "proof-open"
            try:
                self._worker = self.worker_factory(
                    target=self._run_sequence,
                    args=(runtime, source, launch_binding_sha256),
                    name="decision-os-creator-live-cycle-005",
                    daemon=True,
                )
                self._worker.start()
            except Exception as exc:
                self._starting = False
                self._active = False
                try:
                    runtime.record_stage_failure(
                        "A1_CAPTURE",
                        "CYCLE_005_COORDINATOR_START_FAILED",
                    )
                except Exception:
                    pass
                raise CreatorLiveEntrypointError(
                    "CYCLE_005_COORDINATOR_START_FAILED"
                ) from exc
            return self.snapshot(base_snapshot)

    def _fail_open_runtime(
        self,
        runtime: FieldNoteCreatorLiveProofRuntime,
        code: str,
    ) -> None:
        try:
            readback = runtime.read_back()
            if readback.state != "OPEN":
                return
            stage = readback.current_stage
            boundary = {
                "A1_CAPTURE": "A1_CAPTURE",
                "A2_RECONNECT": "A2_RECONNECT",
                "A3_REUSE": "A3_REUSE",
                "A4_DURABILITY": "A4_DURABILITY",
                "A5_CONFIRMATION": "A5_CONFIRMATION",
                "A6_REVIEW": "A6_REVIEW",
            }.get(stage, "RUNTIME_ENFORCEMENT")
            runtime.record_stage_failure(boundary, code[:256])
        except Exception:
            pass

    def _run_sequence(
        self,
        runtime: FieldNoteCreatorLiveProofRuntime,
        source: FieldNoteSourceRepositoryIdentity,
        launch_binding_sha256: str,
    ) -> None:
        try:
            repository = self.spec.repository.resolve(strict=True)
            self._stage = "A1"
            a1_bridge = FieldNoteCreatorLiveA1CaptureBridge(
                runtime=runtime,
                controller=self.controller,  # type: ignore[arg-type]
                repository=repository,
                source_repository=source,
            )
            a1_bridge.capture(self.spec.run_1_task)
            after_a1 = runtime.read_back()
            draft = self.controller.creator_live_a1_completed_draft(
                expected_run_id=after_a1.run_1.run_id
            )
            note = after_a1.captured_note
            if note is None:
                raise ValueError("A1_NOTE_IDENTITY_MISSING")
            self._stage = "A2"
            run_2_id = "run_a7_creator_live_cycle_005_2_" + launch_binding_sha256
            runtime.open_run_2(
                FieldNoteWholeFlowRunIdentity(
                    proof_attempt_id=after_a1.proof_attempt_id,
                    run_id=run_2_id,
                    started_at=self.now(),
                    repository=source,
                    runtime=self.spec.runtime,
                )
            )
            pre_a2 = runtime.read_back()
            exact = prepare_creator_live_a2_reconnect(
                repository,
                creator_live_a2_target_from_readback(pre_a2),
            )
            a2_bridge = FieldNoteCreatorLiveA2ReconnectBridge(
                runtime=runtime,
                controller=self.controller,
                repository=repository,
                source_repository=source,
            )
            a2_bridge.reconnect(self.spec.run_2_task)
            completion = self.controller.creator_live_a2_run_completion(
                expected_run_id=run_2_id
            )
            try:
                after_a2 = runtime.read_back()
                target = after_a2.captured_note
                if target is None:
                    raise ValueError("A2_TARGET_MISSING")
                note_bytes = exact.note_bytes
                reconnect_receipt = completion.reconnect_receipt
                final_output_bytes = completion.final_output_bytes
                output_identity = FieldNoteCreatorLiveRun2OutputIdentity.create(
                    proof_attempt_id=after_a2.proof_attempt_id,
                    run_id=completion.run_id,
                    task_byte_count=completion.task_byte_count,
                    task_sha256=completion.task_sha256,
                    final_output_byte_count=len(final_output_bytes),
                    final_output_sha256=completion.final_output_sha256,
                )
                if (
                    completion.transmission_ordinal != 2
                    or completion.normal_terminal is not True
                    or completion.turn_status != "completed"
                    or completion.runtime_status != "NORMAL_TERMINAL"
                    or completion.failure_diagnostic_absent is not True
                ):
                    raise ValueError("A2_OUTPUT_IDENTITY_INVALID")
                durable_output = runtime.record_run_2_output_identity(
                    output_identity
                )
                if durable_output.run_2_output_identity != output_identity:
                    raise ValueError("A2_OUTPUT_IDENTITY_READBACK_MISMATCH")
                self._stage = "A3"
                evidence_as_of = self.now()
                winner, audit = compile_run_2_output_artifact_audited(
                    note=target,
                    note_bytes=note_bytes,
                    run_2_id=run_2_id,
                    final_output_bytes=final_output_bytes,
                    output_identity=output_identity,
                )
                durable_audit = runtime.record_a3_compiler_audit(audit)
                if durable_audit.a3_compiler_audit != audit:
                    raise ValueError("A3_COMPILER_AUDIT_READBACK_MISMATCH")
            finally:
                self.controller.release_creator_live_a2_run_completion(
                    expected_run_id=run_2_id
                )
                del completion
            if audit.terminal_a3_code is not None:
                runtime.record_stage_failure(
                    "A3_REUSE",
                    audit.terminal_a3_code,
                )
            if winner is None or durable_audit.a3_compiler_audit is None:
                raise ValueError("A3_COMPILER_RESULT_INVALID")
            claim = _claim_from_verified_a3_audit(
                note=target,
                note_bytes=note_bytes,
                run_2_id=run_2_id,
                output_identity=output_identity,
                observed_at=evidence_as_of,
                winner=winner,
                audit=durable_audit.a3_compiler_audit,
            )
            assessment = assess_field_note_reuse(
                target,
                claim,
                note_bytes=note_bytes,
            )
            if assessment.state != "REUSED":
                raise ValueError("A3_NOT_DEMONSTRABLY_REUSED")
            runtime.record_a3_reuse(
                assessment,
                note=target,
                note_bytes=note_bytes,
            )

            ledger = FieldNoteMaturityLedger(
                repository / ".decision-os/field-notes/maturity-ledger-v0.1",
                target,
            )
            self._stage = "A4"
            commit = commit_field_note_maturity(
                ledger,
                FieldNoteMaturityCommitRequest(
                    note=target,
                    note_bytes=note_bytes,
                    reuse_claim=claim,
                    recorded_at=self.now(),
                    delivery_context=reconnect_receipt,
                ),
            )
            if commit.assessment != assessment or commit.durable_snapshot is None:
                raise ValueError("A4_ASSESSMENT_READBACK_MISMATCH")
            runtime.record_a4_durability(commit.durable_snapshot)
            self._stage = "A5"
            runtime.record_a5_confirmation(commit)
            self._stage = "A6"
            review = review_field_note_maturity(
                ledger,
                target,
                note_bytes=note_bytes,
                review_as_of=self.now(),
            )
            runtime.record_a6_review(review)
            self._stage = "A7"
            terminal = runtime.read_back()
            if terminal.run_2 is None:
                raise ValueError("A7_RUN_2_MISSING")
            bundle = FieldNoteWholeFlowEvidenceBundle(
                attempt=terminal.attempt,
                source_repository=source,
                run_1=terminal.run_1,
                run_2=terminal.run_2,
                note=target,
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
                self._stage = "A7"
        except Exception as exc:
            code = str(exc).strip() or "CREATOR_LIVE_SEQUENCE_FAILED"
            self._fail_open_runtime(runtime, code)
            with self._lock:
                self._terminal_state = "FAILED"
                self._terminal_failure_code = code[:256]
        finally:
            with self._lock:
                self._active = False


__all__ = [
    "CYCLE_KEY",
    "CreatorLiveCycle005Entrypoint",
    "CreatorLiveCycle005Spec",
    "CreatorLiveEntrypointError",
    "CreatorLiveP0Result",
    "RUN_1_TASK",
    "RUN_1_TASK_SHA256",
    "RUN_2_TASK",
    "RUN_2_TASK_SHA256",
    "compile_run_2_output_artifact",
    "compile_run_2_output_artifact_audited",
    "product_tree_sha256",
]
