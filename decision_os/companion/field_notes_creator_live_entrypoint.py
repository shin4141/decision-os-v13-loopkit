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
    CREATOR_LIVE_JOURNAL_FILENAME,
    CREATOR_LIVE_JOURNAL_FILENAME_V2,
    FieldNoteCreatorLiveAttemptExistsError,
    FieldNoteCreatorLiveProofRuntime,
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
IMPLEMENTATION_AUTHORIZATION_OBSERVED_AT = "2026-08-05T08:47:00Z"
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
)

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
    candidates: list[tuple[int, int, bytes, int]] = []
    for match in re.finditer(rb"[^\r\n]+", note_bytes):
        structure = match.group(0)
        if (
            len(structure.strip()) < 32
            or (match.start() == 0 and match.end() == len(note_bytes))
            or note_bytes.count(structure) != 1
            or final_output_bytes.count(structure) != 1
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
    if not candidates:
        raise ValueError("A3_EXACT_STRUCTURE_MISSING")
    longest = max(len(item[2]) for item in candidates)
    winners = tuple(item for item in candidates if len(item[2]) == longest)
    if len(winners) != 1:
        raise ValueError("A3_EXACT_STRUCTURE_AMBIGUOUS")
    start, end, structure, output_start = winners[0]
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
                "historical_boundary": (
                    "Cycle 004 remains FAILED/A1_CAPTURE/"
                    "A1_CAPTURE_CHRONOLOGY_INVALID; earlier proofs remain terminal."
                ),
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

    def _public_readback(self, runtime: FieldNoteCreatorLiveProofRuntime) -> dict[str, Any]:
        readback = runtime.read_back()
        return {
            "proof_attempt_id": readback.proof_attempt_id,
            "run_1_id": readback.run_1.run_id,
            "run_2_id": readback.run_2.run_id if readback.run_2 else None,
            "note_id": (
                readback.captured_note.field_note_id
                if readback.captured_note is not None
                else None
            ),
            "note_path": (
                readback.captured_note.note_path
                if readback.captured_note is not None
                else None
            ),
            "note_sha256": (
                readback.captured_note.note_sha256
                if readback.captured_note is not None
                else None
            ),
            "proof_as_of": readback.terminal_proof_as_of,
            "journal_sha256": _sha256_bytes(runtime.journal_path.read_bytes()),
            "anchor_sha256": _sha256_bytes(runtime.anchor_path.read_bytes()),
        }

    def snapshot(self, base_snapshot: Mapping[str, Any]) -> dict[str, Any]:
        with self._lock:
            root = self.spec.storage_root
            if self._runtime is not None:
                readback = self._runtime.read_back()
                state = self._terminal_state or (
                    "RUNNING" if self._active else readback.state
                )
                digest = readback.proof_attempt_id.removeprefix(
                    "proof_a7_creator_live_cycle_005_"
                )
                return {
                    "cycle_key": self.spec.cycle_key,
                    "state": state,
                    "stage": self._stage,
                    "p0": {"ready": True, "failure_code": None},
                    "launch_binding_sha256": digest if _SHA256.fullmatch(digest) else None,
                    "binding": None,
                    "identities": self._public_readback(self._runtime),
                    "receipt_sha256": self._receipt_sha256,
                    "manifest_sha256": self._manifest_sha256,
                    "failure_code": self._terminal_failure_code,
                    "one_attempt_no_retry": True,
                    "replacement_permitted": False,
                }
            if _proof_storage_occupied(root):
                try:
                    runtime = FieldNoteCreatorLiveProofRuntime.load_attempt(root)
                    readback = runtime.read_back()
                    self._runtime = runtime
                    state = (
                        readback.state
                        if readback.state in {"FAILED", "TRACE_COMPLETE"}
                        else "OPEN_UNRESUMABLE"
                    )
                    self._terminal_state = state
                    self._stage = readback.current_stage or "A7"
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
                    "P0_REPOSITORY_IDENTITY_CHANGED"
                ) from exc
            try:
                runtime = self.runtime_opener(
                    self.spec.storage_root,
                    attempt=attempt,
                    source_repository=source,
                    run_1_id=run_1_id,
                    runtime=self.spec.runtime,
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
            after_a2 = runtime.read_back()
            target = after_a2.captured_note
            if target is None:
                raise ValueError("A2_TARGET_MISSING")
            note_bytes = exact.note_bytes
            self._stage = "A3"
            evidence_as_of = self.now()
            claim = compile_run_2_output_artifact(
                note=target,
                note_bytes=note_bytes,
                run_2_id=run_2_id,
                final_output_bytes=completion.final_output_bytes,
                final_output_sha256=completion.final_output_sha256,
                observed_at=evidence_as_of,
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
                    delivery_context=completion.reconnect_receipt,
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
                a2_reconnect=completion.reconnect_receipt,
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
    "product_tree_sha256",
]
