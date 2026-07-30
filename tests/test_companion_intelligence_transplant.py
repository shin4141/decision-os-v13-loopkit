from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import select
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from decision_os.intelligence_transplant import (
    E4_IMPLEMENTATION_BINDING,
    LOWER_RUN_TRIAL_MANIFEST,
    RUN_CHARTER,
    SEAT_ASSIGNMENT_RECEIPT,
    canonical_json,
    exact_ref,
    object_with_content_hash,
)
from decision_os.companion.guided_intake import (
    GuidedIntakeConflictError,
    GuidedIntakeController,
)
from decision_os.companion.intelligence_transplant import (
    IntelligenceTransplantBusyError,
    IntelligenceTransplantConflictError,
    IntelligenceTransplantController,
    IntelligenceTransplantIntegrityError,
    IntelligenceTransplantValidationError,
)
from decision_os.companion.manual_bridge import (
    BridgeSessionController,
    ManualBridgeValidationError,
    build_intelligence_transplant_transport,
)
from tests.test_companion_guided_intake import (
    AMBIGUOUS_REQUEST,
    clear_draft,
)
from tests.test_companion_manual_bridge import (
    complete_boundary,
    fixture_bytes,
)
from tests.test_decision_os_intelligence_transplant import (
    control,
    valid_graph,
)


FIXED_TIME = "2026-07-30T00:30:00Z"


class DeterministicIds:
    def __init__(self, prefix: str = "stage5-event") -> None:
        self.prefix = prefix
        self.index = 0

    def __call__(self) -> str:
        self.index += 1
        return f"{self.prefix}-{self.index:04d}"


def git(repository: Path, *arguments: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ("git", "-C", str(repository), *arguments),
        check=True,
        capture_output=True,
        text=text,
    )
    return completed.stdout


def create_repository(parent: Path, name: str = "repo") -> Path:
    repository = parent / name
    repository.mkdir()
    subprocess.run(
        ("git", "init", "-q", str(repository)),
        check=True,
        capture_output=True,
    )
    git(repository, "config", "user.name", "Stage 5 Test")
    git(repository, "config", "user.email", "stage5@example.invalid")
    (repository / "seed.txt").write_text("seed\n", encoding="utf-8")
    git(repository, "add", "seed.txt")
    git(repository, "commit", "-qm", "seed")
    return repository


def current_head(repository: Path) -> str:
    value = git(repository, "rev-parse", "HEAD")
    assert isinstance(value, str)
    return value.strip()


def charter_for(repository: Path) -> tuple[dict[str, object], dict[str, object]]:
    record = json.loads(
        Path(
            "tests/fixtures/intelligence_transplant_v0_1/valid_charter.json"
        ).read_text(encoding="utf-8")
    )
    head = current_head(repository)
    record.update(
        {
            "completion_line": "Stage 5 private state is restartable.",
            "repository_head": head,
            "source_freeze_id": "GI-FREEZE-STAGE5-001",
            "source_freeze_sha256": "a" * 64,
        }
    )
    record = object_with_content_hash(record)
    source = {
        "completion_line": record["completion_line"],
        "freeze_id": record["source_freeze_id"],
        "frozen_intake_sha256": record["source_freeze_sha256"],
        "repository_head": head,
    }
    return record, source


def transport_for(
    record: dict[str, object],
    *,
    context_ref: dict[str, str] | None,
) -> dict[str, object]:
    payload = canonical_json(record)
    return build_intelligence_transplant_transport(
        payload=payload,
        source_path_or_label=f"{record['object_id']}.json",
        mode="BYTE_EXACT_FILE_IMPORT",
        declared_sha256=hashlib.sha256(payload).hexdigest(),
        context_evidence_ref=context_ref,
        as_of=str(record["as_of"]),
    )


def _replace_refs(
    value: object,
    refs: dict[str, dict[str, str]],
) -> object:
    if isinstance(value, dict):
        if set(value) == {"content_hash", "object_id"}:
            object_id = value.get("object_id")
            if isinstance(object_id, str) and object_id in refs:
                return dict(refs[object_id])
        return {key: _replace_refs(item, refs) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_refs(item, refs) for item in value]
    return value


def graph_through_real_e4(
    repository: Path,
    *,
    include_unbound_change: bool = False,
) -> list[dict[str, object]]:
    base = current_head(repository)
    asset_path = repository / "decision_os" / "context_guard.py"
    asset_path.parent.mkdir()
    asset_path.write_text("def guard() -> bool:\n    return True\n", encoding="utf-8")
    git(repository, "add", "decision_os/context_guard.py")
    if include_unbound_change:
        (repository / "unbound.txt").write_text(
            "must be declared\n",
            encoding="utf-8",
        )
        git(repository, "add", "unbound.txt")
    git(repository, "commit", "-qm", "add context guard")
    head = current_head(repository)
    blob = git(repository, "rev-parse", f"{head}:decision_os/context_guard.py")
    assert isinstance(blob, str)
    asset_bytes = asset_path.read_bytes()

    source = valid_graph()[:10]
    refs: dict[str, dict[str, str]] = {}
    rebound: list[dict[str, object]] = []
    for original in source:
        record = _replace_refs(deepcopy(original), refs)
        assert isinstance(record, dict)
        if record["object_type"] == RUN_CHARTER:
            record.update(
                {
                    "repository_head": head,
                    "source_freeze_id": "GI-FREEZE-STAGE5-001",
                    "source_freeze_sha256": "a" * 64,
                    "completion_line": "Stage 5 E4 is Git-bound.",
                }
            )
        if record["object_type"] == E4_IMPLEMENTATION_BINDING:
            artifact = record["changed_artifacts"][0]
            artifact.update(
                {
                    "git_blob": blob.strip(),
                    "sha256": hashlib.sha256(asset_bytes).hexdigest(),
                }
            )
            record["claim_bindings"][0]["asset_hash"] = artifact["sha256"]
            record.update(
                {
                    "repository_base": base,
                    "repository_head": head,
                    "repository_opening_head": head,
                    "repository_closing_head": head,
                    "repository_base_is_ancestor": True,
                }
            )
        record = object_with_content_hash(record)
        refs[str(record["object_id"])] = exact_ref(record)
        rebound.append(record)
    return rebound


class CompanionIntelligenceTransplantTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repository = create_repository(self.root)
        self.ids = DeterministicIds()
        self.controller = IntelligenceTransplantController(
            self.repository,
            clock=lambda: FIXED_TIME,
            id_factory=self.ids,
        )

    def freeze_charter(self) -> dict[str, object]:
        charter, source = charter_for(self.repository)
        return self.controller.freeze_charter(
            charter,
            charter_source=source,
            repository_head=str(source["repository_head"]),
        )

    def test_store_is_lazy_private_git_common_dir_and_charter_is_not_active(
        self,
    ) -> None:
        before = git(self.repository, "status", "--porcelain=v1")
        expected_root = (
            (self.repository / ".git").resolve()
            / "decision-os"
            / "intelligence-transplant"
            / "v0.1"
        )
        self.assertEqual(expected_root, self.controller.store.root)
        empty = self.controller.snapshot()
        self.assertEqual("EMPTY", empty["store_state"])
        self.assertFalse(expected_root.exists())

        projection = self.freeze_charter()

        self.assertEqual("NOT_ESTABLISHED", projection["execution_status"])
        self.assertEqual("READY", projection["store_state"])
        self.assertEqual(before, git(self.repository, "status", "--porcelain=v1"))
        for directory in self.controller.store._directories():
            self.assertEqual(0o700, os.stat(directory).st_mode & 0o777)
        for target in (
            self.controller.store.events_path,
            self.controller.store.event_head_path,
            self.controller.store.root / ".transaction.lock",
        ):
            self.assertEqual(0o600, os.stat(target).st_mode & 0o777)

    def test_integrity_anchor_detects_event_truncation_and_blob_replacement(
        self,
    ) -> None:
        self.freeze_charter()
        events = self.controller.store.events_path
        events.write_bytes(b"")
        with self.assertRaises(IntelligenceTransplantIntegrityError):
            self.controller.snapshot()

        other_repository = create_repository(self.root, "blob-corrupt")
        other = IntelligenceTransplantController(
            other_repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("blob"),
        )
        charter, source = charter_for(other_repository)
        other.freeze_charter(charter, charter_source=source)
        blob = (
            other.store.root
            / "charters"
            / "sha256"
            / f"{charter['content_hash']}.json"
        )
        blob.write_bytes(blob.read_bytes() + b" ")
        with self.assertRaises(IntelligenceTransplantIntegrityError):
            other.snapshot()

        reset_repository = create_repository(self.root, "anchor-delete")
        reset = IntelligenceTransplantController(
            reset_repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("anchor"),
        )
        charter, source = charter_for(reset_repository)
        reset.freeze_charter(charter, charter_source=source)
        reset.store.events_path.unlink()
        reset.store.event_head_path.unlink()
        with self.assertRaises(IntelligenceTransplantIntegrityError):
            reset.snapshot()

    def test_event_wrapper_rewrite_and_coordinated_invalid_rehash_fail_closed(
        self,
    ) -> None:
        self.freeze_charter()
        events_path = self.controller.store.events_path
        original = events_path.read_bytes()
        events_path.write_bytes(original.rstrip(b"\n") + b" \n")
        with self.assertRaises(IntelligenceTransplantIntegrityError):
            self.controller.snapshot()

        other_repository = create_repository(self.root, "wrapper-rehash")
        other = IntelligenceTransplantController(
            other_repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("wrapper"),
        )
        charter, source = charter_for(other_repository)
        other.freeze_charter(charter, charter_source=source)
        event = json.loads(other.store.events_path.read_text(encoding="utf-8"))
        event["event_id"] = "event-coordinated-wrapper-rewrite"
        body = {
            key: value
            for key, value in event.items()
            if key != "event_hash"
        }
        event["event_hash"] = hashlib.sha256(canonical_json(body)).hexdigest()
        other.store.events_path.write_bytes(canonical_json(event) + b"\n")
        head_body = {
            "event_chain_head": event["event_hash"],
            "event_count": 1,
            "schema_version": (
                "decision-os-intelligence-transplant-store-v0.1"
            ),
        }
        head = {
            **head_body,
            "head_sha256": hashlib.sha256(
                canonical_json(head_body)
            ).hexdigest(),
        }
        other.store.event_head_path.write_bytes(canonical_json(head))
        with self.assertRaises(IntelligenceTransplantIntegrityError):
            other.snapshot()

        receipt_repository = create_repository(self.root, "receipt-rehash")
        receipt_controller = IntelligenceTransplantController(
            receipt_repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("receipt"),
        )
        receipt_charter, receipt_source = charter_for(receipt_repository)
        receipt_controller.freeze_charter(
            receipt_charter,
            charter_source=receipt_source,
        )
        seat = deepcopy(valid_graph()[1])
        seat["charter_ref"] = exact_ref(receipt_charter)
        seat = object_with_content_hash(seat)
        receipt_controller.attach_object(
            seat,
            transport=transport_for(seat, context_ref=None),
        )
        rewritten = [
            json.loads(line)
            for line in receipt_controller.store.events_path.read_text(
                encoding="utf-8"
            ).splitlines()
        ]
        changed_receipt = rewritten[-1]["payload"]["transport_receipt"]
        changed_receipt["source_path_or_label"] = "rewritten-source.json"
        receipt_body = {
            key: value
            for key, value in changed_receipt.items()
            if key != "receipt_sha256"
        }
        changed_receipt["receipt_sha256"] = hashlib.sha256(
            canonical_json(receipt_body)
        ).hexdigest()
        rewritten_body = {
            key: value
            for key, value in rewritten[-1].items()
            if key != "event_hash"
        }
        rewritten[-1]["event_hash"] = hashlib.sha256(
            canonical_json(rewritten_body)
        ).hexdigest()
        receipt_controller.store.events_path.write_bytes(
            b"".join(canonical_json(item) + b"\n" for item in rewritten)
        )
        receipt_head_body = {
            "event_chain_head": rewritten[-1]["event_hash"],
            "event_count": len(rewritten),
            "schema_version": (
                "decision-os-intelligence-transplant-store-v0.1"
            ),
        }
        receipt_head = {
            **receipt_head_body,
            "head_sha256": hashlib.sha256(
                canonical_json(receipt_head_body)
            ).hexdigest(),
        }
        receipt_controller.store.event_head_path.write_bytes(
            canonical_json(receipt_head)
        )
        with self.assertRaises(IntelligenceTransplantIntegrityError):
            receipt_controller.snapshot()

    def test_symlink_replacement_fails_closed(self) -> None:
        self.freeze_charter()
        evidence = self.controller.store.root / "evidence"
        displaced = self.controller.store.root / "evidence-displaced"
        evidence.rename(displaced)
        evidence.symlink_to(displaced, target_is_directory=True)
        with self.assertRaises(IntelligenceTransplantIntegrityError):
            self.controller.snapshot()

        race_repository = create_repository(self.root, "symlink-race")
        race = IntelligenceTransplantController(
            race_repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("race"),
        )
        charter, source = charter_for(race_repository)
        race.freeze_charter(charter, charter_source=source)
        seat = deepcopy(valid_graph()[1])
        seat["charter_ref"] = exact_ref(charter)
        seat = object_with_content_hash(seat)
        outside = self.root / "outside-evidence"
        (outside / "sha256").mkdir(parents=True)
        os.chmod(outside, 0o700)
        os.chmod(outside / "sha256", 0o700)
        race_evidence = race.store.root / "evidence"
        race_displaced = race.store.root / "evidence-before-race"
        original_assert = race.store._assert_safe_path
        swapped = False

        def swap_after_check(target: Path) -> None:
            nonlocal swapped
            original_assert(target)
            if (
                not swapped
                and target.suffix == ".json"
                and target.parent.name == "sha256"
                and target.parent.parent.name == "evidence"
            ):
                swapped = True
                race_evidence.rename(race_displaced)
                race_evidence.symlink_to(outside, target_is_directory=True)

        race.store._assert_safe_path = swap_after_check  # type: ignore[method-assign]
        try:
            with self.assertRaises(IntelligenceTransplantIntegrityError):
                race.attach_object(
                    seat,
                    transport=transport_for(seat, context_ref=None),
                )
        finally:
            race.store._assert_safe_path = original_assert  # type: ignore[method-assign]
        self.assertTrue(swapped)
        self.assertEqual([], list((outside / "sha256").iterdir()))

    def test_cross_process_lock_contention_is_busy(self) -> None:
        self.freeze_charter()
        lock_path = self.controller.store.root / ".transaction.lock"
        script = (
            "import fcntl,sys,time\n"
            "stream=open(sys.argv[1],'rb')\n"
            "fcntl.flock(stream.fileno(),fcntl.LOCK_EX)\n"
            "print('locked',flush=True)\n"
            "time.sleep(2)\n"
        )
        child = subprocess.Popen(
            (sys.executable, "-c", script, str(lock_path)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            assert child.stdout is not None
            self.assertEqual("locked", child.stdout.readline().strip())
            with self.assertRaises(IntelligenceTransplantBusyError):
                self.controller.snapshot()
        finally:
            child.terminate()
            child.communicate(timeout=5)

    def test_charter_source_head_cannot_be_bypassed_by_omitting_precondition(
        self,
    ) -> None:
        charter, source = charter_for(self.repository)
        (self.repository / "later.txt").write_text("later\n", encoding="utf-8")
        git(self.repository, "add", "later.txt")
        git(self.repository, "commit", "-qm", "later")

        with self.assertRaisesRegex(
            IntelligenceTransplantConflictError,
            "RUN CHARTER REPOSITORY AS-OF STALE",
        ):
            self.controller.freeze_charter(
                charter,
                charter_source=source,
            )
        self.assertEqual([], self.controller.store.read_events())

    def test_transport_is_exact_session_independent_and_declared_hash_required(
        self,
    ) -> None:
        bridge = BridgeSessionController(self.repository)
        self.assertFalse(bridge.store.root.exists())
        payload = b'{"alpha":"beta"}\r\n'
        digest = hashlib.sha256(payload).hexdigest()
        transport = build_intelligence_transplant_transport(
            payload=payload,
            source_path_or_label="manual.json",
            mode="BYTE_EXACT_FILE_IMPORT",
            declared_sha256=digest,
            context_evidence_ref=None,
            as_of=FIXED_TIME,
        )
        self.assertEqual(payload, transport["payload"])
        self.assertEqual(
            digest,
            transport["transport_receipt"]["exact_payload_sha256"],
        )
        self.assertFalse(bridge.store.root.exists())
        with self.assertRaises(ManualBridgeValidationError):
            build_intelligence_transplant_transport(
                payload=payload,
                source_path_or_label="manual.json",
                mode="BYTE_EXACT_FILE_IMPORT",
                declared_sha256=None,
                context_evidence_ref=None,
                as_of=FIXED_TIME,
            )

        self.freeze_charter()
        charter = self.controller.store.read_records()[0]
        seat = deepcopy(valid_graph()[1])
        seat["charter_ref"] = exact_ref(charter)
        seat = object_with_content_hash(seat)
        noncanonical = transport_for(seat, context_ref=None)
        receipt = noncanonical["transport_receipt"]
        receipt["as_of"] = "2026-07-30T00:30:00+00:00"
        receipt_body = {
            key: value
            for key, value in receipt.items()
            if key != "receipt_sha256"
        }
        receipt["receipt_sha256"] = hashlib.sha256(
            canonical_json(receipt_body)
        ).hexdigest()
        with self.assertRaises(IntelligenceTransplantValidationError):
            self.controller.attach_object(seat, transport=noncanonical)

        future = transport_for(seat, context_ref=None)
        future_receipt = future["transport_receipt"]
        future_receipt["as_of"] = "2026-07-31T00:30:00Z"
        future_body = {
            key: value
            for key, value in future_receipt.items()
            if key != "receipt_sha256"
        }
        future_receipt["receipt_sha256"] = hashlib.sha256(
            canonical_json(future_body)
        ).hexdigest()
        with self.assertRaisesRegex(
            IntelligenceTransplantValidationError,
            "outside the record/event window",
        ):
            self.controller.attach_object(seat, transport=future)

    def test_stage5_transport_preserves_legacy_session_and_golden_bytes(
        self,
    ) -> None:
        bridge = BridgeSessionController(
            self.repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("legacy"),
        )
        bridge.create_session(complete_boundary())
        for filename, role in (
            ("pro_design_valid.md", "PRO_DESIGN"),
            ("build_receipt_valid.md", "BUILD_RECEIPT"),
            ("pro_audit_valid.md", "PRO_AUDIT"),
            ("reusable_delta_valid.md", "REUSABLE_DELTA_RECORD"),
        ):
            if role == "BUILD_RECEIPT":
                bridge.generate_execution_handoff()
                bridge.freeze_output("EXECUTION_HANDOFF")
            bridge.import_artifact(
                selected_role=role,
                payload=fixture_bytes(filename),
                source_path_or_label=filename,
                import_mode="BYTE_EXACT_FILE_IMPORT",
            )
        bridge.generate_golden_manifest()
        bridge.freeze_output("GOLDEN_MANIFEST")
        before = {
            path.relative_to(bridge.store.root).as_posix(): path.read_bytes()
            for path in bridge.store.root.rglob("*")
            if path.is_file()
        }

        payload = b'{"stage5":"transport-only"}\n'
        build_intelligence_transplant_transport(
            payload=payload,
            source_path_or_label="stage5.json",
            mode="BYTE_EXACT_FILE_IMPORT",
            declared_sha256=hashlib.sha256(payload).hexdigest(),
            context_evidence_ref=None,
            as_of=FIXED_TIME,
        )
        stage5 = IntelligenceTransplantController(
            self.repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("stage5-with-legacy"),
        )
        charter, charter_source = charter_for(self.repository)
        stage5.freeze_charter(
            charter,
            charter_source=charter_source,
            repository_head=str(charter_source["repository_head"]),
        )
        seat = deepcopy(valid_graph()[1])
        seat["charter_ref"] = exact_ref(charter)
        seat = object_with_content_hash(seat)
        stage5.attach_object(
            seat,
            transport=transport_for(seat, context_ref=None),
        )

        after = {
            path.relative_to(bridge.store.root).as_posix(): path.read_bytes()
            for path in bridge.store.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)
        self.assertEqual(
            [
                "EVIDENCE_PACKET",
                "PRO_DESIGN",
                "EXECUTION_HANDOFF",
                "BUILD_RECEIPT",
                "PRO_AUDIT",
                "REUSABLE_DELTA_RECORD",
            ],
            bridge.snapshot()["golden_manifest"]["artifact_order"],
        )

    def test_guided_intake_charter_source_is_narrow_current_and_read_only(
        self,
    ) -> None:
        guided = GuidedIntakeController(
            self.repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("guided"),
        )
        guided.capture(AMBIGUOUS_REQUEST)
        guided.import_draft(
            json.dumps(clear_draft(), ensure_ascii=False, separators=(",", ":")),
            "MANUAL_PRO_DRAFT",
        )
        frozen = guided.freeze()
        before_source = {
            path.relative_to(guided.store.root).as_posix(): path.read_bytes()
            for path in guided.store.root.rglob("*")
            if path.is_file()
        }

        source = guided.charter_source()
        after_source = {
            path.relative_to(guided.store.root).as_posix(): path.read_bytes()
            for path in guided.store.root.rglob("*")
            if path.is_file()
        }

        self.assertEqual(before_source, after_source)
        self.assertEqual(
            frozen["interpretation"]["completion_line"]["text"],
            source["completion_line"],
        )
        self.assertEqual(
            frozen["freeze"]["sha256"],
            source["frozen_intake_sha256"],
        )
        self.assertEqual(
            {
                "completion_line",
                "freeze_id",
                "frozen_intake_sha256",
                "repository_head",
            },
            set(source),
        )
        (self.repository / "later.txt").write_text("later\n", encoding="utf-8")
        git(self.repository, "add", "later.txt")
        git(self.repository, "commit", "-qm", "later")
        before_stale_source = {
            path.relative_to(guided.store.root).as_posix(): path.read_bytes()
            for path in guided.store.root.rglob("*")
            if path.is_file()
        }
        with self.assertRaises(GuidedIntakeConflictError):
            guided.charter_source()
        after_stale_source = {
            path.relative_to(guided.store.root).as_posix(): path.read_bytes()
            for path in guided.store.root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before_stale_source, after_stale_source)

    def test_concurrent_duplicate_append_has_one_effective_event(self) -> None:
        self.freeze_charter()
        charter = self.controller.store.read_records()[0]
        seat = valid_graph()[1]
        seat["charter_ref"] = exact_ref(charter)
        seat = object_with_content_hash(seat)
        transport = transport_for(seat, context_ref=None)
        first = IntelligenceTransplantController(
            self.repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("first"),
        )
        second = IntelligenceTransplantController(
            self.repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("second"),
        )
        barrier = threading.Barrier(2)
        outcomes: list[str] = []

        def attach(controller: IntelligenceTransplantController) -> None:
            barrier.wait()
            try:
                controller.attach_object(seat, transport=transport)
                outcomes.append("accepted")
            except IntelligenceTransplantValidationError:
                outcomes.append("rejected")

        threads = [
            threading.Thread(target=attach, args=(first,)),
            threading.Thread(target=attach, args=(second,)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
        self.assertEqual(["accepted", "rejected"], sorted(outcomes))
        self.assertEqual(2, len(self.controller.store.read_events()))

    def test_duplicate_event_id_and_repository_toctou_never_append(
        self,
    ) -> None:
        self.freeze_charter()
        charter = self.controller.store.read_records()[0]
        seat = deepcopy(valid_graph()[1])
        seat["charter_ref"] = exact_ref(charter)
        seat = object_with_content_hash(seat)
        transport = transport_for(seat, context_ref=None)

        duplicate_id = IntelligenceTransplantController(
            self.repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("ignored"),
        )
        existing_event_id = self.controller.store.read_events()[0][
            "event_id"
        ]
        duplicate_id._new_event_id = (  # type: ignore[method-assign]
            lambda _record: existing_event_id
        )
        with self.assertRaisesRegex(
            IntelligenceTransplantConflictError,
            "EVENT ID ALREADY EXISTS",
        ):
            duplicate_id.attach_object(seat, transport=transport)
        self.assertEqual(1, len(self.controller.store.read_events()))
        self.assertEqual("READY", self.controller.snapshot()["store_state"])

        original_append = self.controller.store.append_event

        def drift_then_append(**kwargs: object) -> dict[str, object]:
            (self.repository / "drift.txt").write_text(
                "drift\n",
                encoding="utf-8",
            )
            git(self.repository, "add", "drift.txt")
            git(self.repository, "commit", "-qm", "drift before append")
            return original_append(**kwargs)

        self.controller.store.append_event = drift_then_append  # type: ignore[method-assign]
        try:
            with self.assertRaisesRegex(
                IntelligenceTransplantConflictError,
                "APPEND INPUT CHANGED",
            ):
                self.controller.attach_object(seat, transport=transport)
        finally:
            self.controller.store.append_event = original_append  # type: ignore[method-assign]
        self.assertEqual(1, len(self.controller.store.read_events()))

    def test_real_git_e4_binding_and_tampered_blob_fail_closed(self) -> None:
        graph = graph_through_real_e4(self.repository)
        charter = graph[0]
        source = {
            "completion_line": charter["completion_line"],
            "freeze_id": charter["source_freeze_id"],
            "frozen_intake_sha256": charter["source_freeze_sha256"],
            "repository_head": charter["repository_head"],
        }
        self.controller.freeze_charter(charter, charter_source=source)
        for index, record in enumerate(graph[1:], start=1):
            context = (
                None
                if record["object_type"] == SEAT_ASSIGNMENT_RECEIPT
                else exact_ref(graph[index - 1])
            )
            transport = transport_for(record, context_ref=context)
            if record["object_type"] == "AUDIT_INPUT_MANIFEST":
                self.controller.freeze_manifest(record, transport=transport)
            else:
                self.controller.attach_object(record, transport=transport)
        self.assertEqual(
            "IMPLEMENTED",
            self.controller.snapshot()["delta_state"],
        )

        e4 = graph[-1]
        (self.repository / "decision_os" / "context_guard.py").unlink()
        git(self.repository, "add", "-u", "decision_os/context_guard.py")
        git(self.repository, "commit", "-qm", "rollback context guard")
        rollback = control(
            graph,
            action="ROLLBACK",
            target=e4,
            minute=14,
            object_id="CONTROL-ROLLBACK-STORE-001",
        )
        rollback["post_rollback_repository_head"] = current_head(
            self.repository
        )
        rollback["rollback_changed_artifacts"] = [
            {
                "path": "decision_os/context_guard.py",
                "post_rollback_state": "DELETED",
                "git_blob": None,
                "sha256": None,
            }
        ]
        rollback = object_with_content_hash(rollback)
        rolled_back = self.controller.record_control(
            rollback,
            transport=transport_for(
                rollback,
                context_ref=exact_ref(e4),
            ),
        )
        self.assertEqual("REVOKED", rolled_back["delta_state"])

        invalid_repository = create_repository(self.root, "invalid-e4")
        invalid_graph = graph_through_real_e4(invalid_repository)
        invalid = invalid_graph[-1]
        invalid["changed_artifacts"][0]["git_blob"] = "f" * 40
        invalid = object_with_content_hash(invalid)
        invalid_controller = IntelligenceTransplantController(
            invalid_repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("invalid"),
        )
        source_charter = invalid_graph[0]
        invalid_controller.freeze_charter(
            source_charter,
            charter_source={
                "completion_line": source_charter["completion_line"],
                "freeze_id": source_charter["source_freeze_id"],
                "frozen_intake_sha256": source_charter[
                    "source_freeze_sha256"
                ],
                "repository_head": source_charter["repository_head"],
            },
        )
        for index, record in enumerate(invalid_graph[1:-1], start=1):
            transport = transport_for(
                record,
                context_ref=(
                    None
                    if record["object_type"] == SEAT_ASSIGNMENT_RECEIPT
                    else exact_ref(invalid_graph[index - 1])
                ),
            )
            if record["object_type"] == "AUDIT_INPUT_MANIFEST":
                invalid_controller.freeze_manifest(record, transport=transport)
            else:
                invalid_controller.attach_object(record, transport=transport)
        with self.assertRaises(IntelligenceTransplantValidationError):
            invalid_controller.attach_object(
                invalid,
                transport=transport_for(
                    invalid,
                    context_ref=exact_ref(invalid_graph[-2]),
                ),
            )

        unbound_repository = create_repository(self.root, "unbound-e4")
        unbound_graph = graph_through_real_e4(
            unbound_repository,
            include_unbound_change=True,
        )
        unbound_controller = IntelligenceTransplantController(
            unbound_repository,
            clock=lambda: FIXED_TIME,
            id_factory=DeterministicIds("unbound"),
        )
        unbound_charter = unbound_graph[0]
        unbound_controller.freeze_charter(
            unbound_charter,
            charter_source={
                "completion_line": unbound_charter["completion_line"],
                "freeze_id": unbound_charter["source_freeze_id"],
                "frozen_intake_sha256": unbound_charter[
                    "source_freeze_sha256"
                ],
                "repository_head": unbound_charter["repository_head"],
            },
        )
        for index, record in enumerate(unbound_graph[1:-1], start=1):
            transported = transport_for(
                record,
                context_ref=(
                    None
                    if record["object_type"] == SEAT_ASSIGNMENT_RECEIPT
                    else exact_ref(unbound_graph[index - 1])
                ),
            )
            if record["object_type"] == "AUDIT_INPUT_MANIFEST":
                unbound_controller.freeze_manifest(
                    record,
                    transport=transported,
                )
            else:
                unbound_controller.attach_object(
                    record,
                    transport=transported,
                )
        with self.assertRaisesRegex(
            IntelligenceTransplantValidationError,
            "not completely bound",
        ):
            unbound_controller.attach_object(
                unbound_graph[-1],
                transport=transport_for(
                    unbound_graph[-1],
                    context_ref=exact_ref(unbound_graph[-2]),
                ),
            )

    def test_replace_and_graft_cannot_promote_e4_to_implemented(
        self,
    ) -> None:
        graph = graph_through_real_e4(self.repository)
        charter = graph[0]
        self.controller.freeze_charter(
            charter,
            charter_source={
                "completion_line": charter["completion_line"],
                "freeze_id": charter["source_freeze_id"],
                "frozen_intake_sha256": charter[
                    "source_freeze_sha256"
                ],
                "repository_head": charter["repository_head"],
            },
        )
        for index, record in enumerate(graph[1:-1], start=1):
            transported = transport_for(
                record,
                context_ref=(
                    None
                    if record["object_type"] == SEAT_ASSIGNMENT_RECEIPT
                    else exact_ref(graph[index - 1])
                ),
            )
            if record["object_type"] == "AUDIT_INPUT_MANIFEST":
                self.controller.freeze_manifest(
                    record,
                    transport=transported,
                )
            else:
                self.controller.attach_object(
                    record,
                    transport=transported,
                )
        event_count = len(self.controller.store.read_events())
        e4_transport = transport_for(
            graph[-1],
            context_ref=exact_ref(graph[-2]),
        )
        head = current_head(self.repository)
        base = str(graph[-1]["repository_base"])

        git(self.repository, "replace", head, base)
        with self.assertRaisesRegex(
            IntelligenceTransplantConflictError,
            "GIT INTERPRETATION UNSAFE",
        ):
            self.controller.attach_object(
                graph[-1],
                transport=e4_transport,
            )
        git(self.repository, "replace", "-d", head)
        self.assertEqual(
            event_count,
            len(self.controller.store.read_events()),
        )
        self.assertNotEqual(
            "IMPLEMENTED",
            self.controller.snapshot()["delta_state"],
        )

        grafts_path = self.repository / ".git" / "info" / "grafts"
        grafts_path.write_text(f"{head} {base}\n", encoding="ascii")
        with self.assertRaisesRegex(
            IntelligenceTransplantConflictError,
            "GIT INTERPRETATION UNSAFE",
        ):
            self.controller.attach_object(
                graph[-1],
                transport=e4_transport,
            )
        grafts_path.unlink()
        self.assertEqual(
            event_count,
            len(self.controller.store.read_events()),
        )
        self.assertNotEqual(
            "IMPLEMENTED",
            self.controller.snapshot()["delta_state"],
        )

    def test_snapshot_rejects_replace_grafts_config_and_missing_e4_blob(
        self,
    ) -> None:
        graph = graph_through_real_e4(self.repository)
        charter = graph[0]
        self.controller.freeze_charter(
            charter,
            charter_source={
                "completion_line": charter["completion_line"],
                "freeze_id": charter["source_freeze_id"],
                "frozen_intake_sha256": charter[
                    "source_freeze_sha256"
                ],
                "repository_head": charter["repository_head"],
            },
        )
        for index, record in enumerate(graph[1:], start=1):
            transported = transport_for(
                record,
                context_ref=(
                    None
                    if record["object_type"] == SEAT_ASSIGNMENT_RECEIPT
                    else exact_ref(graph[index - 1])
                ),
            )
            if record["object_type"] == "AUDIT_INPUT_MANIFEST":
                self.controller.freeze_manifest(
                    record,
                    transport=transported,
                )
            else:
                self.controller.attach_object(
                    record,
                    transport=transported,
                )
        self.assertEqual(
            "IMPLEMENTED",
            self.controller.snapshot()["delta_state"],
        )
        head = current_head(self.repository)
        base = str(graph[-1]["repository_base"])
        git(self.repository, "replace", head, base)
        with self.assertRaisesRegex(
            IntelligenceTransplantIntegrityError,
            "GIT INTERPRETATION UNSAFE",
        ):
            self.controller.snapshot()
        git(self.repository, "replace", "-d", head)

        grafts_path = self.repository / ".git" / "info" / "grafts"
        grafts_path.write_text(f"{head} {base}\n", encoding="ascii")
        with self.assertRaisesRegex(
            IntelligenceTransplantIntegrityError,
            "GIT INTERPRETATION UNSAFE",
        ):
            self.controller.snapshot()
        grafts_path.unlink()

        git(self.repository, "config", "core.useReplaceRefs", "true")
        with self.assertRaisesRegex(
            IntelligenceTransplantIntegrityError,
            "GIT INTERPRETATION UNSAFE",
        ):
            self.controller.snapshot()
        git(self.repository, "config", "--unset", "core.useReplaceRefs")
        self.assertEqual(
            "IMPLEMENTED",
            self.controller.snapshot()["delta_state"],
        )
        blob_id = str(graph[-1]["changed_artifacts"][0]["git_blob"])
        blob_path = (
            self.repository
            / ".git"
            / "objects"
            / blob_id[:2]
            / blob_id[2:]
        )
        self.assertTrue(blob_path.is_file())
        blob_path.unlink()
        with self.assertRaisesRegex(
            IntelligenceTransplantIntegrityError,
            "GIT EVIDENCE INVALID",
        ):
            self.controller.snapshot()

    def test_repository_drift_during_event_head_write_invalidates_publication(
        self,
    ) -> None:
        self.freeze_charter()
        charter = self.controller.store.read_records()[0]
        seat = deepcopy(valid_graph()[1])
        seat["charter_ref"] = exact_ref(charter)
        seat = object_with_content_hash(seat)
        transport = transport_for(seat, context_ref=None)
        original_write_event_head = self.controller.store._write_event_head

        def drift_during_head_write(
            *,
            event_count: int,
            event_chain_head: str,
        ) -> None:
            (self.repository / "publication-drift.txt").write_text(
                "drift during publication\n",
                encoding="utf-8",
            )
            git(self.repository, "add", "publication-drift.txt")
            git(self.repository, "commit", "-qm", "drift during publication")
            original_write_event_head(
                event_count=event_count,
                event_chain_head=event_chain_head,
            )

        self.controller.store._write_event_head = (  # type: ignore[method-assign]
            drift_during_head_write
        )
        try:
            with self.assertRaisesRegex(
                IntelligenceTransplantIntegrityError,
                "PUBLICATION INVALID",
            ):
                self.controller.attach_object(
                    seat,
                    transport=transport,
                )
        finally:
            self.controller.store._write_event_head = (  # type: ignore[method-assign]
                original_write_event_head
            )

        publication_state = json.loads(
            self.controller.store.publication_state_path.read_text(
                encoding="utf-8"
            )
        )
        invalid_head = json.loads(
            self.controller.store.event_head_path.read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("INVALID", publication_state["publication_status"])
        self.assertEqual(publication_state, invalid_head)
        self.assertNotEqual(
            publication_state["expected_repository_head"],
            publication_state["observed_repository_head"],
        )
        self.assertEqual(
            2,
            len(self.controller.store.events_path.read_bytes().splitlines()),
        )
        with self.assertRaisesRegex(
            IntelligenceTransplantIntegrityError,
            "PUBLICATION INVALID",
        ):
            self.controller.snapshot()
        self.controller.store.publication_state_path.unlink()
        with self.assertRaisesRegex(
            IntelligenceTransplantIntegrityError,
            "PUBLICATION INVALID",
        ):
            self.controller.snapshot()

    def test_atomic_publication_and_marker_removal_fsync_parent_directory(
        self,
    ) -> None:
        operations: list[tuple[str, str]] = []
        original_fsync = os.fsync
        original_replace = os.replace
        original_unlink = os.unlink

        def observed_fsync(descriptor: int) -> None:
            original_fsync(descriptor)
            mode = os.fstat(descriptor).st_mode
            operations.append(
                (
                    "directory-fsync"
                    if stat.S_ISDIR(mode)
                    else "file-fsync",
                    "",
                )
            )

        def observed_replace(
            source: str,
            target: str,
            *,
            src_dir_fd: int | None = None,
            dst_dir_fd: int | None = None,
        ) -> None:
            original_replace(
                source,
                target,
                src_dir_fd=src_dir_fd,
                dst_dir_fd=dst_dir_fd,
            )
            operations.append(("replace", target))

        def observed_unlink(
            target: str,
            *,
            dir_fd: int | None = None,
        ) -> None:
            original_unlink(target, dir_fd=dir_fd)
            operations.append(("unlink", target))

        with (
            patch(
                "decision_os.companion.intelligence_transplant.os.fsync",
                side_effect=observed_fsync,
            ),
            patch(
                "decision_os.companion.intelligence_transplant.os.replace",
                side_effect=observed_replace,
            ),
            patch(
                "decision_os.companion.intelligence_transplant.os.unlink",
                side_effect=observed_unlink,
            ),
        ):
            self.freeze_charter()
            charter = self.controller.store.read_records()[0]
            seat = deepcopy(valid_graph()[1])
            seat["charter_ref"] = exact_ref(charter)
            seat = object_with_content_hash(seat)
            transport = transport_for(seat, context_ref=None)
            self.controller.attach_object(seat, transport=transport)
            events = self.controller.store.read_events()
            self.controller.store._invalidate_publication(
                event_count=len(events),
                event_chain_head=events[-1]["event_hash"],
                expected_repository_head=current_head(self.repository),
                observed_repository_head=None,
            )

        replaced = [
            target
            for operation, target in operations
            if operation == "replace"
        ]
        self.assertGreaterEqual(replaced.count("publication-state.json"), 3)
        self.assertGreaterEqual(replaced.count("event-head.json"), 3)
        self.assertIn(f"{charter['content_hash']}.json", replaced)
        self.assertIn(f"{seat['content_hash']}.json", replaced)
        self.assertIn(
            f"{transport['transport_receipt']['receipt_sha256']}"
            ".receipt.json",
            replaced,
        )
        self.assertIn(
            f"{transport['transport_receipt']['exact_payload_sha256']}.bin",
            replaced,
        )

        marker_unlinks = 0
        for index, (operation, target) in enumerate(operations):
            if operation == "replace":
                self.assertEqual(
                    ("directory-fsync", ""),
                    operations[index + 1],
                    msg=f"{target} was not followed by a directory fsync",
                )
            elif operation == "unlink" and target == "publication-state.json":
                marker_unlinks += 1
                self.assertEqual(
                    ("directory-fsync", ""),
                    operations[index + 1],
                )
        self.assertEqual(2, marker_unlinks)

    def test_force_killed_publication_reopens_fail_closed(self) -> None:
        script = """
from copy import deepcopy
import sys
import time

from decision_os.intelligence_transplant import exact_ref, object_with_content_hash
from decision_os.companion.intelligence_transplant import IntelligenceTransplantController
from tests.test_companion_intelligence_transplant import (
    DeterministicIds,
    FIXED_TIME,
    transport_for,
)
from tests.test_decision_os_intelligence_transplant import valid_graph

repository, phase = sys.argv[1:]
controller = IntelligenceTransplantController(
    repository,
    clock=lambda: FIXED_TIME,
    id_factory=DeterministicIds("crash"),
)
charter = controller.store.read_records()[0]
seat = deepcopy(valid_graph()[1])
seat["charter_ref"] = exact_ref(charter)
seat = object_with_content_hash(seat)
transport = transport_for(seat, context_ref=None)

if phase == "after-in-progress":
    original = controller.store._write_publication_state
    def stop_after_in_progress(**kwargs):
        original(**kwargs)
        if kwargs["status"] == "IN_PROGRESS":
            print(phase, flush=True)
            time.sleep(60)
    controller.store._write_publication_state = stop_after_in_progress
elif phase == "before-event-head":
    def stop_before_event_head(**kwargs):
        print(phase, flush=True)
        time.sleep(60)
    controller.store._write_event_head = stop_before_event_head
elif phase == "before-marker-clear":
    def stop_before_marker_clear():
        print(phase, flush=True)
        time.sleep(60)
    controller.store._clear_publication_state = stop_before_marker_clear
else:
    raise AssertionError(phase)

controller.attach_object(seat, transport=transport)
"""
        expected_counts = {
            "after-in-progress": (1, 1),
            "before-event-head": (2, 1),
            "before-marker-clear": (2, 2),
        }
        for phase, (event_count, head_count) in expected_counts.items():
            with self.subTest(phase=phase):
                repository = create_repository(
                    self.root,
                    f"publication-crash-{phase}",
                )
                controller = IntelligenceTransplantController(
                    repository,
                    clock=lambda: FIXED_TIME,
                    id_factory=DeterministicIds(f"parent-{phase}"),
                )
                charter, source = charter_for(repository)
                controller.freeze_charter(
                    charter,
                    charter_source=source,
                )
                child = subprocess.Popen(
                    (
                        sys.executable,
                        "-B",
                        "-c",
                        script,
                        str(repository),
                        phase,
                    ),
                    cwd=Path(__file__).resolve().parents[1],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                try:
                    assert child.stdout is not None
                    ready, _, _ = select.select(
                        [child.stdout],
                        [],
                        [],
                        10,
                    )
                    self.assertTrue(
                        ready,
                        msg=f"{phase} child did not reach the crash point.",
                    )
                    self.assertEqual(phase, child.stdout.readline().strip())
                finally:
                    child.kill()
                    _, stderr = child.communicate(timeout=5)
                self.assertNotEqual(
                    0,
                    child.returncode,
                    msg=stderr,
                )

                publication_state = json.loads(
                    controller.store.publication_state_path.read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(
                    "IN_PROGRESS",
                    publication_state["publication_status"],
                )
                self.assertEqual(
                    event_count,
                    len(
                        controller.store.events_path.read_bytes().splitlines()
                    ),
                )
                event_head = json.loads(
                    controller.store.event_head_path.read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(head_count, event_head["event_count"])

                reopened = IntelligenceTransplantController(
                    repository,
                    clock=lambda: FIXED_TIME,
                    id_factory=DeterministicIds(f"reopen-{phase}"),
                )
                with self.assertRaisesRegex(
                    IntelligenceTransplantIntegrityError,
                    "PUBLICATION INVALID",
                ):
                    reopened.snapshot()

    def test_lower_manifest_head_drift_is_rejected_before_append(self) -> None:
        self.freeze_charter()
        record = deepcopy(
            next(
                item
                for item in valid_graph()
                if item["object_type"] == LOWER_RUN_TRIAL_MANIFEST
            )
        )
        self.assertEqual(LOWER_RUN_TRIAL_MANIFEST, record["object_type"])
        record["repository_head"] = "f" * 40
        record = object_with_content_hash(record)
        before = len(self.controller.store.read_events())
        with self.assertRaises(IntelligenceTransplantValidationError):
            self.controller.freeze_manifest(
                record,
                transport=transport_for(
                    record,
                    context_ref=exact_ref(
                        self.controller.store.read_records()[0]
                    ),
                ),
            )
        self.assertEqual(before, len(self.controller.store.read_events()))


if __name__ == "__main__":
    unittest.main()
