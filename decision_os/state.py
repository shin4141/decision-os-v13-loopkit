"""Deterministic parsing for the current V13 Markdown state surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable


FIELD_LINE = re.compile(r"^(?P<name>[^:\n]+):\s*$")
NON_FIELD_PREFIXES = ("-", "*", ">", "#", "|")


def normalize_field(name: str) -> str:
    """Normalize a visible state-field label without interpreting its value."""

    normalized = re.sub(r"[^a-z0-9]+", "_", name.casefold()).strip("_")
    return normalized


def first_fenced_block(text: str) -> str | None:
    """Return only the first fenced block.

    Current V13 state is intentionally read from the first current receipt
    block. Later fences are historical As-of evidence and must not backfill a
    missing current field.
    """

    lines = text.splitlines()
    opening_index: int | None = None
    opening_marker = ""

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            opening_index = index
            opening_marker = stripped[:3]
            break

    if opening_index is None:
        return None

    block: list[str] = []
    for line in lines[opening_index + 1 :]:
        if line.strip().startswith(opening_marker):
            return "\n".join(block)
        block.append(line)

    return None


def parse_fields(block: str) -> dict[str, tuple[str, ...]]:
    """Parse ``Field:`` followed by one non-empty value line."""

    lines = block.splitlines()
    parsed: dict[str, list[str]] = {}

    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith(NON_FIELD_PREFIXES):
            continue

        match = FIELD_LINE.match(stripped)
        if match is None:
            continue

        value = ""
        for candidate in lines[index + 1 :]:
            candidate = candidate.strip()
            if candidate:
                if FIELD_LINE.match(candidate):
                    break
                value = candidate
                break

        key = normalize_field(match.group("name"))
        if key:
            parsed.setdefault(key, []).append(value)

    return {key: tuple(values) for key, values in parsed.items()}


@dataclass(frozen=True)
class StateSurface:
    """One current V13 state surface."""

    relative_path: str
    exists: bool
    block_found: bool
    fields: dict[str, tuple[str, ...]]

    @property
    def conflicting_fields(self) -> tuple[str, ...]:
        conflicts = []
        for key, values in self.fields.items():
            if len(set(values)) > 1:
                conflicts.append(key)
        return tuple(sorted(conflicts))


def load_surface(repo_root: Path, relative_path: str) -> StateSurface:
    path = repo_root / relative_path
    if not path.exists():
        return StateSurface(relative_path, False, False, {})

    resolved_root = repo_root.resolve()
    if path.is_symlink():
        raise OSError(f"{relative_path}: symbolic links are not accepted")

    resolved_path = path.resolve(strict=True)
    if not resolved_path.is_relative_to(resolved_root) or not resolved_path.is_file():
        raise OSError(f"{relative_path}: state surface escapes the repository")

    text = resolved_path.read_text(encoding="utf-8", errors="strict")
    block = first_fenced_block(text)
    if block is None:
        return StateSurface(relative_path, True, False, {})

    return StateSurface(relative_path, True, True, parse_fields(block))


def values_for(
    surfaces: Iterable[StateSurface], aliases: Iterable[str]
) -> tuple[tuple[str, str], ...]:
    """Return ``(source, value)`` pairs for normalized aliases."""

    normalized_aliases = tuple(
        dict.fromkeys(normalize_field(alias) for alias in aliases)
    )
    found: list[tuple[str, str]] = []
    for surface in surfaces:
        for alias in normalized_aliases:
            for value in surface.fields.get(alias, ()):
                found.append((surface.relative_path, value))
    return tuple(found)


def first_value(
    surfaces: Iterable[StateSurface], aliases: Iterable[str]
) -> str | None:
    values = values_for(surfaces, aliases)
    return values[0][1] if values else None
