"""Canonical Field Notes Lite v0.1 model and one-shot proposal gate."""

from __future__ import annotations

import base64
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
import secrets
from typing import Any, Mapping


FIELD_NOTE_TOOL_NAME = "propose_field_note_candidate"
FIELD_NOTE_SCHEMA_VERSION = "decision-os.field-note-lite.v0.1"
FIELD_NOTE_ROOT = ".decision-os/field-notes"
MAX_MARKDOWN_BYTES = 64 * 1024
MAX_METADATA_BYTES = 8 * 1024
BODY_KEYS = (
    "trigger",
    "reusable_structure",
    "scope",
    "do_not_apply_when",
    "procedure",
    "acceptance",
    "evidence",
    "remaining_unknowns",
)
BODY_HEADINGS = (
    ("trigger", "Trigger"),
    ("reusable_structure", "Reusable Structure"),
    ("scope", "Scope"),
    ("do_not_apply_when", "Do Not Apply When"),
    ("procedure", "Procedure"),
    ("acceptance", "Acceptance"),
    ("evidence", "Evidence"),
    ("remaining_unknowns", "Remaining UNKNOWNs"),
)
MODEL_CLASSES = frozenset({"stronger", "lower-cost", "UNKNOWN"})
METADATA_START_MARKER = "<!-- decision-os-field-note-metadata:v0.1"
_LINE_BREAKS = frozenset("\r\n\v\f\x1c\x1d\x1e\x85\u2028\u2029")
_MARKDOWN_HEADING_RE = re.compile(
    r"^[ \t]*(?:(?:>[ \t]*)+)?"
    r"(?:(?:[-+*]|[0-9]+[.)])[ \t]+)?#{1,6}(?:[ \t]+|$)"
)
_MARKDOWN_FENCE_RE = re.compile(
    r"^[ \t]*(?:(?:>[ \t]*)+)?"
    r"(?:(?:[-+*]|[0-9]+[.)])[ \t]+)?(?:`{3,}|~{3,})"
)
_MARKDOWN_RULE_RE = re.compile(
    r"^[ \t]*(?:(?:>[ \t]*)+)?"
    r"(?:(?:\*[ \t]*){3,}|(?:_[ \t]*){3,}|(?:-[ \t]*){3,}|=+[ \t]*)$"
)
_MARKDOWN_HTML_BLOCK_RE = re.compile(
    r"^[ \t]*(?:(?:>[ \t]*)+)?"
    r"(?:(?:[-+*]|[0-9]+[.)])[ \t]+)?"
    r"<(?:/?[A-Za-z][A-Za-z0-9-]*(?:[ \t/>]|$)|[!?])"
)

FIELD_NOTE_TOOL_SPEC = {
    "type": "function",
    "name": FIELD_NOTE_TOOL_NAME,
    "description": (
        "Optionally propose at most one reusable Field Note candidate for this "
        "same active Run. The call is side-effect-free and does not write a file, "
        "grant authority, or trigger another model call."
    ),
    "inputSchema": {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "title",
            "value_level",
            "source_model_class",
            "target_model_class",
            "trigger_terms",
            "scope",
            "body",
        ],
        "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 120},
            "value_level": {"type": "integer", "enum": [1, 2, 3]},
            "source_model_class": {
                "type": "string",
                "enum": ["stronger", "lower-cost", "UNKNOWN"],
            },
            "target_model_class": {
                "type": "string",
                "enum": ["stronger", "lower-cost", "UNKNOWN"],
            },
            "trigger_terms": {
                "type": "array",
                "minItems": 1,
                "maxItems": 12,
                "uniqueItems": True,
                "items": {"type": "string", "minLength": 1, "maxLength": 64},
            },
            "scope": {
                "type": "object",
                "additionalProperties": False,
                "required": ["task_family", "path_prefixes", "exclude_terms"],
                "properties": {
                    "task_family": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 128,
                    },
                    "path_prefixes": {
                        "type": "array",
                        "maxItems": 16,
                        "uniqueItems": True,
                        "items": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 256,
                        },
                    },
                    "exclude_terms": {
                        "type": "array",
                        "maxItems": 16,
                        "uniqueItems": True,
                        "items": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 64,
                        },
                    },
                },
            },
            "body": {
                "type": "object",
                "additionalProperties": False,
                "required": list(BODY_KEYS),
                "properties": {
                    key: {"type": "string", "minLength": 1}
                    for key in BODY_KEYS
                },
            },
        },
    },
}


@dataclass(frozen=True)
class FieldNoteDraft:
    title: str
    value_level: int
    source_model_class: str
    target_model_class: str
    trigger_terms: tuple[str, ...]
    task_family: str
    path_prefixes: tuple[str, ...]
    exclude_terms: tuple[str, ...]
    body: tuple[tuple[str, str], ...]
    source_run_id: str
    created_at: str
    field_note_id: str
    relative_path: str
    markdown: bytes
    sha256: str

    def body_value(self, key: str) -> str:
        return dict(self.body)[key]

    def public_candidate(self) -> dict[str, Any]:
        return {
            "state": "candidate",
            "title": self.title,
            "value_level": self.value_level,
            "reusable_structure": self.body_value("reusable_structure"),
            "actions": ["save", "skip"],
        }


def _bounded_string(value: Any, minimum: int, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not minimum <= len(value) <= maximum
        or not value.strip()
    ):
        raise ValueError("String is outside the bounded schema.")
    if "\x00" in value:
        raise ValueError("NUL is not allowed.")
    return value


def configured_model_class(value: Any) -> str:
    if not isinstance(value, str) or value not in MODEL_CLASSES:
        raise ValueError("Trusted model class is invalid.")
    return value


def level_three_available(
    trusted_source_model_class: str,
    trusted_target_model_class: str,
) -> bool:
    """Return whether the active trusted pair admits Level 3 proposals."""

    source_class = configured_model_class(trusted_source_model_class)
    target_class = configured_model_class(trusted_target_model_class)
    return source_class == "stronger" and target_class == "lower-cost"


def field_note_tool_spec_for_trust(
    trusted_source_model_class: str,
    trusted_target_model_class: str,
) -> dict[str, Any]:
    """Return one fresh shipped Option A model-facing proposal contract."""

    configured_model_class(trusted_source_model_class)
    configured_model_class(trusted_target_model_class)
    tool_spec = copy.deepcopy(FIELD_NOTE_TOOL_SPEC)
    input_schema = tool_spec["inputSchema"]
    properties = input_schema["properties"]
    properties["value_level"]["enum"] = [1, 2]
    return tool_spec


def _structured_text(value: Any, maximum: int, *, title: bool) -> str:
    text = _bounded_string(value, 1, maximum)
    if title and any(character in _LINE_BREAKS for character in text):
        raise ValueError("Field Note title must be one line.")
    if METADATA_START_MARKER in text or "<!--" in text or "-->" in text:
        raise ValueError("Field Note text contains a structural marker.")
    for line in text.splitlines() or [text]:
        if (
            _MARKDOWN_HEADING_RE.match(line)
            or _MARKDOWN_FENCE_RE.match(line)
            or _MARKDOWN_RULE_RE.match(line)
            or _MARKDOWN_HTML_BLOCK_RE.match(line)
        ):
            raise ValueError("Field Note text contains Markdown structure.")
    return text


def validate_compiled_markdown(markdown: bytes) -> None:
    if not isinstance(markdown, bytes):
        raise ValueError("Compiled Field Note must be UTF-8 bytes.")
    try:
        text = markdown.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Compiled Field Note is not valid UTF-8.") from exc
    if len(markdown) > MAX_MARKDOWN_BYTES:
        raise ValueError("Compiled Field Note exceeds 64 KiB.")
    if text.count(METADATA_START_MARKER) != 1:
        raise ValueError("Compiled Field Note metadata marker is not unique.")
    lines = text.splitlines()
    if (
        len(lines) < 5
        or lines[0] != METADATA_START_MARKER
        or lines[2] != "-->"
        or text.count("-->") != 1
    ):
        raise ValueError("Compiled Field Note metadata block is invalid.")
    h1_positions = [
        index
        for index, line in enumerate(lines)
        if re.match(r"^#[ \t]+\S", line)
    ]
    if len(h1_positions) != 1:
        raise ValueError("Compiled Field Note H1 is not unique.")
    if h1_positions[0] != 4:
        raise ValueError("Compiled Field Note H1 position is invalid.")
    heading_positions: list[int] = []
    allowed_headings = {f"## {heading}" for _, heading in BODY_HEADINGS}
    for _, heading in BODY_HEADINGS:
        expected = f"## {heading}"
        positions = [
            index for index, line in enumerate(lines) if line == expected
        ]
        if len(positions) != 1:
            raise ValueError(
                "Compiled Field Note fixed heading is not unique."
            )
        heading_positions.append(positions[0])
    if heading_positions != sorted(heading_positions) or (
        heading_positions and h1_positions[0] >= heading_positions[0]
    ):
        raise ValueError("Compiled Field Note heading order is invalid.")
    for line in lines:
        if _MARKDOWN_HEADING_RE.match(line) and not (
            re.match(r"^#[ \t]+\S", line) or line in allowed_headings
        ):
            raise ValueError("Compiled Field Note has an extra heading.")


def _unique_strings(
    value: Any,
    *,
    minimum_items: int,
    maximum_items: int,
    maximum_length: int,
) -> tuple[str, ...]:
    if not isinstance(value, list) or not minimum_items <= len(value) <= maximum_items:
        raise ValueError("String list is outside the bounded schema.")
    result = tuple(_bounded_string(item, 1, maximum_length) for item in value)
    if len(set(result)) != len(result):
        raise ValueError("String list contains duplicates.")
    return result


def canonical_json(value: Mapping[str, Any]) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return (
        serialized.replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def _slug(title: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", title.casefold())[:5]
    if len(words) == 1:
        words.append("note")
    return "-".join(words) if len(words) >= 2 else "field-note"


def _short_id(field_note_id: str) -> str:
    encoded = base64.b32encode(
        hashlib.sha256(field_note_id.encode("utf-8")).digest()
    ).decode("ascii").lower().rstrip("=")
    return encoded[:10]


def _new_identity() -> str:
    return f"fn_{secrets.token_hex(16)}"


def _utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def compile_draft(
    arguments: Mapping[str, Any],
    *,
    source_run_id: str,
    created_at: str | None = None,
    field_note_id: str | None = None,
) -> FieldNoteDraft:
    if set(arguments) != {
        "title",
        "value_level",
        "source_model_class",
        "target_model_class",
        "trigger_terms",
        "scope",
        "body",
    }:
        raise ValueError("Proposal keys are invalid.")
    title = _structured_text(arguments["title"], 120, title=True)
    value_level = arguments["value_level"]
    if type(value_level) is not int or value_level not in {1, 2, 3}:
        raise ValueError("Value level is invalid.")
    source_class = arguments["source_model_class"]
    target_class = arguments["target_model_class"]
    if source_class not in MODEL_CLASSES or target_class not in MODEL_CLASSES:
        raise ValueError("Model class is invalid.")
    if value_level == 3 and (
        source_class != "stronger" or target_class != "lower-cost"
    ):
        raise ValueError("Level 3 model classes are invalid.")
    trigger_terms = _unique_strings(
        arguments["trigger_terms"],
        minimum_items=1,
        maximum_items=12,
        maximum_length=64,
    )
    scope = arguments["scope"]
    if not isinstance(scope, dict) or set(scope) != {
        "task_family",
        "path_prefixes",
        "exclude_terms",
    }:
        raise ValueError("Scope is invalid.")
    task_family = _bounded_string(scope["task_family"], 1, 128)
    path_prefixes = _unique_strings(
        scope["path_prefixes"],
        minimum_items=0,
        maximum_items=16,
        maximum_length=256,
    )
    exclude_terms = _unique_strings(
        scope["exclude_terms"],
        minimum_items=0,
        maximum_items=16,
        maximum_length=64,
    )
    body = arguments["body"]
    if not isinstance(body, dict) or set(body) != set(BODY_KEYS):
        raise ValueError("Body is invalid.")
    body_items = tuple(
        (key, _structured_text(body[key], 60_000, title=False))
        for key in BODY_KEYS
    )
    if not source_run_id:
        raise ValueError("Source Run identity is missing.")
    timestamp = created_at or _utc_timestamp()
    try:
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("Creation time is invalid.") from exc
    if parsed.tzinfo is None:
        raise ValueError("Creation time must be timezone-aware.")
    normalized = parsed.astimezone(timezone.utc).replace(microsecond=0)
    timestamp = normalized.isoformat().replace("+00:00", "Z")
    identity = field_note_id or _new_identity()
    metadata = {
        "created_at": timestamp,
        "field_note_id": identity,
        "maturity_evidence": {
            "different_task_reuse": None,
            "first_verified_reuse": None,
        },
        "schema_version": FIELD_NOTE_SCHEMA_VERSION,
        "scope": {
            "exclude_terms": list(exclude_terms),
            "path_prefixes": list(path_prefixes),
            "repository": "current",
            "task_family": task_family,
        },
        "source_model_class": source_class,
        "source_run_id": source_run_id,
        "source_run_outcome": "SUCCESS",
        "status": "CANDIDATE",
        "target_model_class": target_class,
        "trigger_terms": list(trigger_terms),
        "value_level": value_level,
    }
    metadata_block = (
        f"{METADATA_START_MARKER}\n"
        f"{canonical_json(metadata)}\n"
        "-->\n"
    )
    if len(metadata_block.encode("utf-8")) > MAX_METADATA_BYTES:
        raise ValueError("Metadata exceeds the bounded size.")
    body_map = dict(body_items)
    sections = "".join(
        f"\n## {heading}\n{body_map[key]}\n"
        for key, heading in BODY_HEADINGS
    )
    markdown = f"{metadata_block}\n# {title}\n{sections}".encode("utf-8")
    if len(markdown) > MAX_MARKDOWN_BYTES:
        raise ValueError("Compiled Field Note exceeds 64 KiB.")
    validate_compiled_markdown(markdown)
    relative_path = (
        f"{FIELD_NOTE_ROOT}/{normalized.date().isoformat()}-"
        f"{_slug(title)}-{_short_id(identity)}.md"
    )
    return FieldNoteDraft(
        title=title,
        value_level=value_level,
        source_model_class=source_class,
        target_model_class=target_class,
        trigger_terms=trigger_terms,
        task_family=task_family,
        path_prefixes=path_prefixes,
        exclude_terms=exclude_terms,
        body=body_items,
        source_run_id=source_run_id,
        created_at=timestamp,
        field_note_id=identity,
        relative_path=relative_path,
        markdown=markdown,
        sha256=hashlib.sha256(markdown).hexdigest(),
    )


class FieldNoteProposalGate:
    """Run-local one-shot admission gate for a typed proposal."""

    def __init__(
        self,
        source_run_id: str,
        *,
        trusted_source_model_class: str = "UNKNOWN",
        trusted_target_model_class: str = "UNKNOWN",
    ) -> None:
        self.source_run_id = source_run_id
        self.trusted_source_model_class = configured_model_class(
            trusted_source_model_class
        )
        self.trusted_target_model_class = configured_model_class(
            trusted_target_model_class
        )
        self.attempted = False
        self.accepted: FieldNoteDraft | None = None

    def propose(self, arguments: Mapping[str, Any]) -> tuple[bool, str]:
        if self.attempted:
            return False, "proposal_attempt_already_consumed"
        self.attempted = True
        try:
            source_class = arguments.get("source_model_class")
            target_class = arguments.get("target_model_class")
            if source_class not in MODEL_CLASSES or target_class not in MODEL_CLASSES:
                raise ValueError("Proposal model class is invalid.")
            value_level = arguments.get("value_level")
            if value_level == 3:
                if not level_three_available(
                    self.trusted_source_model_class,
                    self.trusted_target_model_class,
                ):
                    self.accepted = None
                    return False, "level_3_trust_not_configured"
                if (
                    source_class != self.trusted_source_model_class
                    or target_class != self.trusted_target_model_class
                ):
                    self.accepted = None
                    return False, "level_3_trust_class_mismatch"
            trusted_arguments = dict(arguments)
            trusted_arguments["source_model_class"] = (
                self.trusted_source_model_class
            )
            trusted_arguments["target_model_class"] = (
                self.trusted_target_model_class
            )
            self.accepted = compile_draft(
                trusted_arguments,
                source_run_id=self.source_run_id,
            )
        except (TypeError, ValueError):
            self.accepted = None
            return False, "proposal_schema_invalid"
        return True, "proposal_accepted"
