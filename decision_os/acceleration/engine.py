"""Agent-agnostic Verified Save state transitions and receipts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import uuid
from typing import Any

from .model import DecisionIdentity, DecisionType, derive_decision_identity, sha256_text
from .store import AccelerationStore


ChoiceProvider = Callable[[DecisionIdentity], str | None]
MutationAuthorityPreflight = Callable[[DecisionIdentity], bool]


@dataclass(frozen=True)
class DecisionOutcome:
    """Result of one mechanically typed decision check."""

    identity: DecisionIdentity
    run_id: str
    iteration: int
    allowed: bool
    status: str
    source_interrupt_id: str | None
    default_created_run_id: str | None = None
    pending_cross_run_checkpoint: bool = False


@dataclass(frozen=True)
class CheckpointOutcome:
    """Terminal classification after a Wrapper-owned checkpoint attempt."""

    status: str
    verified: bool
    event_hash: str | None


class AccelerationEngine:
    """Fail-closed Verified Save engine over one local append-only store."""

    def __init__(
        self,
        repository: Path,
        *,
        store: AccelerationStore | None = None,
        adapter: str = "core",
        adapter_version: str = "v0.1",
        mutation_authority_preflight: MutationAuthorityPreflight | None = None,
    ) -> None:
        self.repository = Path(repository)
        self.store = store or AccelerationStore(self.repository)
        self.adapter = adapter
        self.adapter_version = adapter_version
        self.mutation_authority_preflight = mutation_authority_preflight

    @staticmethod
    def new_run_id() -> str:
        return str(uuid.uuid4())

    def evaluate(
        self,
        *,
        run_id: str,
        iteration: int,
        decision_type: DecisionType,
        requested_scope: str,
        source_interrupt_id: str | None,
        choice_provider: ChoiceProvider | None,
    ) -> DecisionOutcome:
        """Record DECISION_CHECK, reuse a valid Default, or ask the human."""

        identity = derive_decision_identity(
            self.repository,
            decision_type,
            requested_scope,
        )
        self.store.append(
            "DECISION_CHECK",
            identity,
            run_id=run_id,
            iteration=iteration,
            adapter=self.adapter,
            adapter_version=self.adapter_version,
            status="CHECKED",
            source_interrupt_id=source_interrupt_id,
        )
        if (
            identity.decision_type
            in {DecisionType.CREATE_FILE, DecisionType.MODIFY_FILE}
            and self.mutation_authority_preflight is not None
        ):
            try:
                authority_allowed = (
                    self.mutation_authority_preflight(identity) is True
                )
            except Exception:
                authority_allowed = False
            if not authority_allowed:
                return DecisionOutcome(
                    identity,
                    run_id,
                    iteration,
                    False,
                    "DENIED",
                    source_interrupt_id,
                )
        active = self.store.active_default(identity.decision_key)
        if active is not None:
            if active.rule_hash != identity.rule_hash:
                return DecisionOutcome(
                    identity,
                    run_id,
                    iteration,
                    False,
                    "RULE_HASH_MISMATCH",
                    source_interrupt_id,
                    default_created_run_id=active.created_run_id,
                )
            if active.created_run_id == run_id:
                return DecisionOutcome(
                    identity,
                    run_id,
                    iteration,
                    True,
                    "SAME_RUN_DEFAULT",
                    source_interrupt_id,
                    default_created_run_id=active.created_run_id,
                )
            self.store.append(
                "DEFAULT_MATCHED",
                identity,
                run_id=run_id,
                iteration=iteration,
                adapter=self.adapter,
                adapter_version=self.adapter_version,
                status="MATCHED_PENDING_CHECKPOINT",
                default_created_run_id=active.created_run_id,
                default_rule_hash=active.rule_hash,
                matched_rule_hash=identity.rule_hash,
                source_interrupt_id=source_interrupt_id,
            )
            self.store.append(
                "INTERRUPT_SKIPPED",
                identity,
                run_id=run_id,
                iteration=iteration,
                adapter=self.adapter,
                adapter_version=self.adapter_version,
                status="PENDING_CHECKPOINT",
                default_created_run_id=active.created_run_id,
                default_rule_hash=active.rule_hash,
                matched_rule_hash=identity.rule_hash,
                source_interrupt_id=source_interrupt_id,
                interrupt_skipped=True,
            )
            return DecisionOutcome(
                identity,
                run_id,
                iteration,
                True,
                "DEFAULT_MATCHED",
                source_interrupt_id,
                default_created_run_id=active.created_run_id,
                pending_cross_run_checkpoint=True,
            )

        choice: str | None = None
        if choice_provider is not None:
            try:
                choice = choice_provider(identity)
            except (EOFError, KeyboardInterrupt, OSError):
                choice = None
        normalized_choice = "" if choice is None else str(choice).strip()
        if normalized_choice == "1":
            return DecisionOutcome(
                identity,
                run_id,
                iteration,
                True,
                "ALLOW_ONCE",
                source_interrupt_id,
            )
        if normalized_choice == "2":
            self.store.append(
                "HUMAN_DEFAULT_CREATED",
                identity,
                run_id=run_id,
                iteration=iteration,
                adapter=self.adapter,
                adapter_version=self.adapter_version,
                status="ACTIVE",
                default_created_run_id=run_id,
                default_rule_hash=identity.rule_hash,
                source_interrupt_id=source_interrupt_id,
            )
            return DecisionOutcome(
                identity,
                run_id,
                iteration,
                True,
                "HUMAN_DEFAULT_CREATED",
                source_interrupt_id,
                default_created_run_id=run_id,
            )
        return DecisionOutcome(
            identity,
            run_id,
            iteration,
            False,
            "DENIED",
            source_interrupt_id,
        )

    def finish_checkpoint(
        self,
        outcome: DecisionOutcome,
        *,
        normal_terminal: bool,
        override_before_checkpoint: bool = False,
        checkpoint_id: str | None = None,
    ) -> CheckpointOutcome:
        """Promote only a valid cross-Run candidate after a normal checkpoint."""

        if not outcome.pending_cross_run_checkpoint:
            return CheckpointOutcome(outcome.status, False, None)
        identity = outcome.identity
        checkpoint = checkpoint_id or str(uuid.uuid4())
        common = {
            "run_id": outcome.run_id,
            "iteration": outcome.iteration,
            "adapter": self.adapter,
            "adapter_version": self.adapter_version,
            "default_created_run_id": outcome.default_created_run_id,
            "default_rule_hash": identity.rule_hash,
            "matched_rule_hash": identity.rule_hash,
            "source_interrupt_id": outcome.source_interrupt_id,
            "checkpoint_id": checkpoint,
            "interrupt_skipped": True,
        }
        if override_before_checkpoint:
            self.store.append(
                "OVERRIDE",
                identity,
                status="PRE_CHECKPOINT_OVERRIDE",
                **common,
            )
            event = self.store.append(
                "REVOKED_SAVE",
                identity,
                status="NOT_VERIFIED",
                **common,
            )
            return CheckpointOutcome(
                "REVOKED_SAVE",
                False,
                event["event_hash"],
            )
        if not normal_terminal:
            event = self.store.append(
                "CHECKPOINT_PENDING",
                identity,
                status="PENDING_ABNORMAL_TERMINAL",
                **common,
            )
            return CheckpointOutcome("PENDING", False, event["event_hash"])

        self.store.append(
            "CHECKPOINT_PASSED",
            identity,
            status="PASSED",
            **common,
        )
        first_verified_use = (
            identity.decision_key not in self.store.verified_decision_keys()
        )
        event_type = "VERIFIED_SAVE" if first_verified_use else "VERIFIED_REUSE"
        event = self.store.append(
            event_type,
            identity,
            status=event_type,
            **common,
        )
        return CheckpointOutcome(event_type, True, event["event_hash"])

    def revoke(self, *, run_id: str, decision_key: str) -> str:
        """Deactivate one Default without rewriting historical verified reuse."""

        active = self.store.active_default(decision_key)
        if active is None:
            raise ValueError("No active Repository Default matches the key.")
        events = self.store.read_events()
        source = next(
            (
                event
                for event in reversed(events)
                if event["decision_key"] == decision_key
            ),
            None,
        )
        if source is None:
            raise ValueError("Decision key is not present in the event chain.")
        identity = DecisionIdentity(
            repository_id=source["repository_id"],
            decision_type=DecisionType(source["decision_type"]),
            normalized_scope=source["normalized_scope"],
            decision_key=source["decision_key"],
            rule_hash=active.rule_hash,
        )
        verified = decision_key in self.store.verified_decision_keys()
        if verified:
            self.store.append(
                "DEFAULT_REVOKED_AFTER_USE",
                identity,
                run_id=run_id,
                iteration=1,
                adapter=self.adapter,
                adapter_version=self.adapter_version,
                status="INACTIVE_HISTORY_PRESERVED",
                default_created_run_id=active.created_run_id,
                default_rule_hash=active.rule_hash,
            )
            return "DEFAULT_REVOKED_AFTER_USE"
        self.store.append(
            "OVERRIDE",
            identity,
            run_id=run_id,
            iteration=1,
            adapter=self.adapter,
            adapter_version=self.adapter_version,
            status="DEFAULT_REVOKED_BEFORE_VERIFIED_USE",
            default_created_run_id=active.created_run_id,
            default_rule_hash=active.rule_hash,
        )
        self.store.append(
            "REVOKED_SAVE",
            identity,
            run_id=run_id,
            iteration=1,
            adapter=self.adapter,
            adapter_version=self.adapter_version,
            status="NOT_VERIFIED",
            default_created_run_id=active.created_run_id,
            default_rule_hash=active.rule_hash,
        )
        return "REVOKED_SAVE"

    def supersede(self, *, run_id: str, decision_key: str) -> str:
        """Deactivate one Default as superseded while preserving prior reuse."""

        active = self.store.active_default(decision_key)
        if active is None:
            raise ValueError("No active Repository Default matches the key.")
        source = next(
            (
                event
                for event in reversed(self.store.read_events())
                if event["decision_key"] == decision_key
            ),
            None,
        )
        if source is None:
            raise ValueError("Decision key is not present in the event chain.")
        identity = DecisionIdentity(
            repository_id=source["repository_id"],
            decision_type=DecisionType(source["decision_type"]),
            normalized_scope=source["normalized_scope"],
            decision_key=source["decision_key"],
            rule_hash=active.rule_hash,
        )
        self.store.append(
            "DEFAULT_SUPERSEDED",
            identity,
            run_id=run_id,
            iteration=1,
            adapter=self.adapter,
            adapter_version=self.adapter_version,
            status="INACTIVE_HISTORY_PRESERVED",
            default_created_run_id=active.created_run_id,
            default_rule_hash=active.rule_hash,
        )
        return "DEFAULT_SUPERSEDED"

    def receipt(self) -> dict[str, Any]:
        """Build a privacy-safe Receipt from verified events and current estimates."""

        verified_saves, verified_reuses = self.store.counters()
        settings = self.store.read_settings()
        minutes = verified_reuses * settings.minutes_per_reuse
        money = minutes / 60 * settings.hourly_value_jpy
        tokens = (
            None
            if settings.tokens_per_reuse is None
            else verified_reuses * settings.tokens_per_reuse
        )
        return {
            "claim_boundary": (
                "Verified Save is a locally recorded proof-of-use event, "
                "not third-party certification."
            ),
            "estimated": {
                "hourly_value_jpy": settings.hourly_value_jpy,
                "minutes": minutes,
                "minutes_per_reuse": settings.minutes_per_reuse,
                "money_jpy": money,
                "tokens": tokens,
                "tokens_per_reuse": settings.tokens_per_reuse,
            },
            "hard_metrics": {
                "verified_reuses": verified_reuses,
                "verified_saves": verified_saves,
            },
            "receipt_identity": (
                f"receipt:v1:{sha256_text(self.store.chain_head())}"
            ),
            "status": "VERIFIED" if verified_reuses else "NO_VERIFIED_REUSE",
        }

    def render_receipt(self) -> str:
        """Render one compact Receipt with hard metrics separated from estimates."""

        receipt = self.receipt()
        hard = receipt["hard_metrics"]
        estimated = receipt["estimated"]
        tokens = (
            "UNKNOWN"
            if estimated["tokens"] is None
            else f"{estimated['tokens']:,}"
        )
        token_formula = (
            "tokens remain UNKNOWN until tokens_per_reuse is configured"
            if estimated["tokens_per_reuse"] is None
            else (
                f"{hard['verified_reuses']} verified reuse"
                f" × {estimated['tokens_per_reuse']:,} configured tokens per reuse"
            )
        )
        return "\n".join(
            (
                receipt["status"],
                "",
                f"{hard['verified_saves']} Save",
                f"{hard['verified_reuses']} Verified Reuse",
                "",
                "ESTIMATED RECOVERED",
                "",
                f"{estimated['minutes']:.1f} minutes",
                f"¥{estimated['money_jpy']:,.0f}",
                f"{tokens} tokens",
                "",
                "Calculated from:",
                (
                    f"{hard['verified_reuses']} verified reuse"
                    f" × {estimated['minutes_per_reuse']:g} estimated minutes"
                    " per reuse"
                    f" × ¥{estimated['hourly_value_jpy']:,.0f} per hour"
                ),
                token_formula,
                "",
                receipt["claim_boundary"],
                "",
            )
        )


class DeterministicAdapter:
    """Internal no-network adapter used only to validate engine transitions."""

    name = "deterministic-test"
    version = "v0.1"

    def __init__(self, engine: AccelerationEngine) -> None:
        self.engine = engine

    def run(
        self,
        *,
        decision_type: DecisionType,
        scope: str,
        human_choice: str | None = None,
        run_id: str | None = None,
        iteration: int = 1,
        normal_terminal: bool = True,
        override_before_checkpoint: bool = False,
    ) -> tuple[DecisionOutcome, CheckpointOutcome]:
        fixed_run_id = run_id or self.engine.new_run_id()
        provider = (
            None
            if human_choice is None
            else lambda _identity: human_choice
        )
        outcome = self.engine.evaluate(
            run_id=fixed_run_id,
            iteration=iteration,
            decision_type=decision_type,
            requested_scope=scope,
            source_interrupt_id=f"fixture:{fixed_run_id}:{iteration}",
            choice_provider=provider,
        )
        checkpoint = self.engine.finish_checkpoint(
            outcome,
            normal_terminal=normal_terminal,
            override_before_checkpoint=override_before_checkpoint,
            checkpoint_id=f"fixture-checkpoint:{fixed_run_id}:{iteration}",
        )
        return outcome, checkpoint
