"""Append-only, hash-chained local storage for Verified Save."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import uuid
from typing import Any

from .model import (
    EVENT_FIELDS,
    EVENT_TYPES,
    GENESIS_EVENT_HASH,
    PROTOCOL_VERSION,
    DecisionIdentity,
    canonical_json,
    git_output,
    git_root,
    hash_payload,
    repository_id,
)


class StateIntegrityError(RuntimeError):
    """The local event chain or configuration is unverifiable."""


@dataclass(frozen=True)
class DefaultRecord:
    """One active repository default reconstructed from the event chain."""

    decision_key: str
    created_run_id: str
    rule_hash: str


@dataclass(frozen=True)
class ActiveDefaultRecord:
    """Presentation fields for one active exact Repository Default."""

    decision_key: str
    created_run_id: str
    rule_hash: str
    decision_type: str
    normalized_scope: str
    created_at: str


@dataclass(frozen=True)
class ReceiptSettings:
    """User-configurable estimate inputs, separate from verified events."""

    minutes_per_reuse: float = 7.5
    hourly_value_jpy: float = 5000.0
    tokens_per_reuse: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "hourly_value_jpy": self.hourly_value_jpy,
            "minutes_per_reuse": self.minutes_per_reuse,
            "protocol_version": PROTOCOL_VERSION,
            "tokens_per_reuse": self.tokens_per_reuse,
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _new_event_id() -> str:
    return str(uuid.uuid4())


class AccelerationStore:
    """Single-writer local state under the target repository Git common dir."""

    def __init__(
        self,
        repository: Path,
        *,
        clock: Callable[[], str] = _utc_now,
        event_id_factory: Callable[[], str] = _new_event_id,
    ) -> None:
        self.repository = git_root(repository)
        self.repository_id = repository_id(self.repository)
        common_raw = git_output(self.repository, "rev-parse", "--git-common-dir")
        common = Path(common_raw)
        if not common.is_absolute():
            common = self.repository / common
        self.git_common_dir = common.resolve(strict=True)
        self.state_dir = (
            self.git_common_dir / "decision-os" / "acceleration" / "v0.1"
        )
        self.events_path = self.state_dir / "events.jsonl"
        self.config_path = self.state_dir / "config.json"
        self._clock = clock
        self._event_id_factory = event_id_factory

    def read_events(self) -> list[dict[str, Any]]:
        """Read and verify the complete append-only chain."""

        if not self.events_path.exists():
            return []
        try:
            raw_lines = self.events_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            raise StateIntegrityError("Event chain is unreadable.") from exc

        events: list[dict[str, Any]] = []
        previous = GENESIS_EVENT_HASH
        seen_ids: set[str] = set()
        for index, line in enumerate(raw_lines, start=1):
            if not line.strip():
                raise StateIntegrityError(
                    f"Event chain contains an empty line at {index}."
                )
            try:
                event = json.loads(line)
            except (json.JSONDecodeError, UnicodeError) as exc:
                raise StateIntegrityError(
                    f"Event chain JSON is invalid at line {index}."
                ) from exc
            if not isinstance(event, dict):
                raise StateIntegrityError(
                    f"Event chain value is not an object at line {index}."
                )
            missing = EVENT_FIELDS.difference(event)
            if missing:
                raise StateIntegrityError(
                    f"Event chain fields are missing at line {index}: "
                    f"{sorted(missing)}"
                )
            if event["event_type"] not in EVENT_TYPES:
                raise StateIntegrityError(
                    f"Unsupported event type at line {index}."
                )
            if event["protocol_version"] != PROTOCOL_VERSION:
                raise StateIntegrityError(
                    f"Protocol version mismatch at line {index}."
                )
            if event["repository_id"] != self.repository_id:
                raise StateIntegrityError(
                    f"Repository identity mismatch at line {index}."
                )
            if event["prev_event_hash"] != previous:
                raise StateIntegrityError(
                    f"Previous hash mismatch at line {index}."
                )
            event_id = event["event_id"]
            if not isinstance(event_id, str) or not event_id or event_id in seen_ids:
                raise StateIntegrityError(
                    f"Event ID is invalid or duplicated at line {index}."
                )
            expected = hash_payload(
                {key: value for key, value in event.items() if key != "event_hash"}
            )
            if event["event_hash"] != expected:
                raise StateIntegrityError(
                    f"Event hash mismatch at line {index}."
                )
            seen_ids.add(event_id)
            previous = expected
            events.append(event)
        return events

    def append(
        self,
        event_type: str,
        identity: DecisionIdentity,
        *,
        run_id: str,
        iteration: int,
        adapter: str,
        adapter_version: str,
        status: str,
        default_created_run_id: str | None = None,
        default_rule_hash: str | None = None,
        matched_rule_hash: str | None = None,
        source_interrupt_id: str | None = None,
        checkpoint_id: str | None = None,
        interrupt_skipped: bool = False,
    ) -> dict[str, Any]:
        """Verify the chain, then append one canonical event."""

        if event_type not in EVENT_TYPES:
            raise ValueError(f"Unsupported event type: {event_type}")
        if not run_id or iteration < 1:
            raise ValueError("run_id and positive iteration are required.")
        events = self.read_events()
        previous = (
            events[-1]["event_hash"] if events else GENESIS_EVENT_HASH
        )
        event: dict[str, Any] = {
            "adapter": adapter,
            "adapter_version": adapter_version,
            "checkpoint_id": checkpoint_id,
            "decision_key": identity.decision_key,
            "decision_type": identity.decision_type.value,
            "default_created_run_id": default_created_run_id,
            "default_rule_hash": default_rule_hash,
            "event_id": self._event_id_factory(),
            "event_type": event_type,
            "interrupt_skipped": bool(interrupt_skipped),
            "iteration": iteration,
            "matched_rule_hash": matched_rule_hash,
            "normalized_scope": identity.normalized_scope,
            "prev_event_hash": previous,
            "protocol_version": PROTOCOL_VERSION,
            "repository_id": identity.repository_id,
            "run_id": run_id,
            "source_interrupt_id": source_interrupt_id,
            "status": status,
            "timestamp": self._clock(),
        }
        event["event_hash"] = hash_payload(event)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        try:
            with self.events_path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(canonical_json(event))
                stream.write("\n")
        except OSError as exc:
            raise StateIntegrityError("Event append failed.") from exc
        return event

    def read_settings(self) -> ReceiptSettings:
        """Read estimate settings without changing verified state."""

        if not self.config_path.exists():
            return ReceiptSettings()
        try:
            value = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise StateIntegrityError("Acceleration config is invalid.") from exc
        if not isinstance(value, dict):
            raise StateIntegrityError("Acceleration config is not an object.")
        try:
            settings = ReceiptSettings(
                minutes_per_reuse=float(value["minutes_per_reuse"]),
                hourly_value_jpy=float(value["hourly_value_jpy"]),
                tokens_per_reuse=(
                    None
                    if value.get("tokens_per_reuse") is None
                    else int(value["tokens_per_reuse"])
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise StateIntegrityError(
                "Acceleration config fields are invalid."
            ) from exc
        self._validate_settings(settings)
        return settings

    def update_settings(
        self,
        *,
        minutes_per_reuse: float | None = None,
        hourly_value_jpy: float | None = None,
        tokens_per_reuse: int | None = None,
        set_tokens: bool = False,
    ) -> ReceiptSettings:
        """Atomically update estimate inputs without adding protocol events."""

        current = self.read_settings()
        updated = ReceiptSettings(
            minutes_per_reuse=(
                current.minutes_per_reuse
                if minutes_per_reuse is None
                else float(minutes_per_reuse)
            ),
            hourly_value_jpy=(
                current.hourly_value_jpy
                if hourly_value_jpy is None
                else float(hourly_value_jpy)
            ),
            tokens_per_reuse=(
                tokens_per_reuse if set_tokens else current.tokens_per_reuse
            ),
        )
        self._validate_settings(updated)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.config_path.with_suffix(".json.tmp")
        try:
            temporary.write_text(
                f"{canonical_json(updated.as_dict())}\n",
                encoding="utf-8",
            )
            temporary.replace(self.config_path)
        except OSError as exc:
            raise StateIntegrityError("Acceleration config update failed.") from exc
        return updated

    @staticmethod
    def _validate_settings(settings: ReceiptSettings) -> None:
        if (
            not math.isfinite(settings.minutes_per_reuse)
            or settings.minutes_per_reuse <= 0
            or not math.isfinite(settings.hourly_value_jpy)
            or settings.hourly_value_jpy <= 0
        ):
            raise StateIntegrityError("Estimate settings must be positive.")
        if (
            settings.tokens_per_reuse is not None
            and settings.tokens_per_reuse <= 0
        ):
            raise StateIntegrityError("tokens_per_reuse must be positive.")

    def active_default(self, decision_key: str) -> DefaultRecord | None:
        """Reconstruct the current active Default for one decision key."""

        active: DefaultRecord | None = None
        for event in self.read_events():
            if event["decision_key"] != decision_key:
                continue
            if event["event_type"] == "HUMAN_DEFAULT_CREATED":
                created_run_id = event["default_created_run_id"]
                rule = event["default_rule_hash"]
                if not isinstance(created_run_id, str) or not isinstance(rule, str):
                    raise StateIntegrityError("Default identity is incomplete.")
                active = DefaultRecord(decision_key, created_run_id, rule)
            elif event["event_type"] in {
                "OVERRIDE",
                "DEFAULT_REVOKED_AFTER_USE",
                "DEFAULT_SUPERSEDED",
            }:
                active = None
        return active

    def active_defaults(self) -> tuple[ActiveDefaultRecord, ...]:
        """Enumerate active exact defaults without changing protocol state."""

        active: dict[str, ActiveDefaultRecord] = {}
        for event in self.read_events():
            key = event["decision_key"]
            if event["event_type"] == "HUMAN_DEFAULT_CREATED":
                created_run_id = event["default_created_run_id"]
                rule = event["default_rule_hash"]
                decision_type = event["decision_type"]
                scope = event["normalized_scope"]
                created_at = event["timestamp"]
                if not all(
                    isinstance(value, str) and value
                    for value in (
                        key,
                        created_run_id,
                        rule,
                        decision_type,
                        scope,
                        created_at,
                    )
                ):
                    raise StateIntegrityError("Default identity is incomplete.")
                active[key] = ActiveDefaultRecord(
                    decision_key=key,
                    created_run_id=created_run_id,
                    rule_hash=rule,
                    decision_type=decision_type,
                    normalized_scope=scope,
                    created_at=created_at,
                )
            elif event["event_type"] in {
                "OVERRIDE",
                "DEFAULT_REVOKED_AFTER_USE",
                "DEFAULT_SUPERSEDED",
            }:
                active.pop(key, None)
        return tuple(
            sorted(
                active.values(),
                key=lambda item: (
                    item.normalized_scope,
                    item.decision_type,
                    item.created_at,
                ),
            )
        )

    def verified_decision_keys(self) -> set[str]:
        """Return unique repository decision pairs that became Verified Saves."""

        return {
            event["decision_key"]
            for event in self.read_events()
            if event["event_type"] == "VERIFIED_SAVE"
        }

    def counters(self) -> tuple[int, int]:
        """Return unique Saves and total verified cross-Run reuses."""

        events = self.read_events()
        saves = len(
            {
                event["decision_key"]
                for event in events
                if event["event_type"] == "VERIFIED_SAVE"
            }
        )
        reuses = sum(
            event["event_type"] in {"VERIFIED_SAVE", "VERIFIED_REUSE"}
            for event in events
        )
        return saves, reuses

    def chain_head(self) -> str:
        """Return the verified event-chain head hash."""

        events = self.read_events()
        return events[-1]["event_hash"] if events else GENESIS_EVENT_HASH
