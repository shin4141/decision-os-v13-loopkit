#!/usr/bin/env python3
"""Validate committed V13 Loop Record examples without third-party packages."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SUPPORTED_SCHEMA_KEYS = {
    "$schema",
    "$id",
    "$defs",
    "$ref",
    "title",
    "description",
    "type",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "enum",
    "minLength",
}

SUPPORTED_TYPES = {"object", "array", "string"}
LOOP_RECORD_EXAMPLE_PATTERNS = (
    "go.*.json",
    "hold.*.json",
    "cap.*.json",
    "block.*.json",
)


class SchemaSupportError(Exception):
    """The repository schema uses a keyword this validator cannot enforce."""


class RecordValidationError(Exception):
    """A Loop Record does not conform to the supported schema."""


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecordValidationError(f"{path}: cannot read valid JSON: {exc}") from exc


def audit_schema(schema: Any, location: str = "#") -> None:
    if not isinstance(schema, dict):
        raise SchemaSupportError(f"{location}: schema node must be an object")

    unsupported = sorted(set(schema) - SUPPORTED_SCHEMA_KEYS)
    if unsupported:
        raise SchemaSupportError(
            f"{location}: unsupported schema keyword(s): {', '.join(unsupported)}"
        )

    schema_type = schema.get("type")
    if schema_type is not None and schema_type not in SUPPORTED_TYPES:
        raise SchemaSupportError(f"{location}: unsupported type: {schema_type!r}")

    for metadata_key in ("$schema", "$id", "$ref", "title", "description"):
        value = schema.get(metadata_key)
        if value is not None and not isinstance(value, str):
            raise SchemaSupportError(f"{location}/{metadata_key}: must be a string")

    for container_key in ("properties", "$defs"):
        container = schema.get(container_key)
        if container is None:
            continue
        if not isinstance(container, dict):
            raise SchemaSupportError(f"{location}/{container_key}: must be an object")
        for name, child in container.items():
            audit_schema(child, f"{location}/{container_key}/{name}")

    required = schema.get("required")
    if required is not None and (
        not isinstance(required, list)
        or any(not isinstance(name, str) for name in required)
    ):
        raise SchemaSupportError(f"{location}/required: must be an array of strings")

    enum = schema.get("enum")
    if enum is not None and not isinstance(enum, list):
        raise SchemaSupportError(f"{location}/enum: must be an array")

    min_length = schema.get("minLength")
    if min_length is not None and (
        not isinstance(min_length, int)
        or isinstance(min_length, bool)
        or min_length < 0
    ):
        raise SchemaSupportError(
            f"{location}/minLength: must be a non-negative integer"
        )

    if "items" in schema:
        audit_schema(schema["items"], f"{location}/items")

    additional = schema.get("additionalProperties")
    if additional is not None and not isinstance(additional, (bool, dict)):
        raise SchemaSupportError(
            f"{location}/additionalProperties: must be boolean or a schema object"
        )
    if isinstance(additional, dict):
        audit_schema(additional, f"{location}/additionalProperties")


def resolve_local_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise SchemaSupportError(f"unsupported non-local $ref: {reference}")

    current: Any = root_schema
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise SchemaSupportError(f"unresolvable $ref: {reference}")
        current = current[part]

    if not isinstance(current, dict):
        raise SchemaSupportError(f"$ref does not resolve to a schema object: {reference}")
    return current


def validate_instance(
    schema: dict[str, Any],
    instance: Any,
    root_schema: dict[str, Any],
    location: str = "$",
    ref_stack: tuple[str, ...] = (),
) -> None:
    reference = schema.get("$ref")
    if reference is not None:
        if reference in ref_stack:
            raise SchemaSupportError(f"cyclic $ref is unsupported: {reference}")
        validate_instance(
            resolve_local_ref(root_schema, reference),
            instance,
            root_schema,
            location,
            ref_stack + (reference,),
        )

    if "enum" in schema and instance not in schema["enum"]:
        raise RecordValidationError(
            f"{location}: {instance!r} is not in enum {schema['enum']!r}"
        )

    schema_type = schema.get("type")

    if schema_type == "object":
        if not isinstance(instance, dict):
            raise RecordValidationError(f"{location}: expected object")

        properties = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in instance:
                raise RecordValidationError(
                    f"{location}: missing required property {name!r}"
                )

        additional = schema.get("additionalProperties", True)
        for name, value in instance.items():
            if name in properties:
                validate_instance(
                    properties[name], value, root_schema, f"{location}.{name}", ref_stack
                )
            elif additional is False:
                raise RecordValidationError(
                    f"{location}: unexpected property {name!r}"
                )
            elif isinstance(additional, dict):
                validate_instance(
                    additional, value, root_schema, f"{location}.{name}", ref_stack
                )

    elif schema_type == "array":
        if not isinstance(instance, list):
            raise RecordValidationError(f"{location}: expected array")
        item_schema = schema.get("items")
        if item_schema is not None:
            for index, value in enumerate(instance):
                validate_instance(
                    item_schema,
                    value,
                    root_schema,
                    f"{location}[{index}]",
                    ref_stack,
                )

    elif schema_type == "string":
        if not isinstance(instance, str):
            raise RecordValidationError(f"{location}: expected string")
        min_length = schema.get("minLength")
        if min_length is not None and len(instance) < min_length:
            raise RecordValidationError(
                f"{location}: string length is below {min_length}"
            )


def validate_examples(schema_path: Path, examples_dir: Path) -> int:
    schema = load_json(schema_path)
    if not isinstance(schema, dict):
        raise SchemaSupportError(f"{schema_path}: root schema must be an object")
    audit_schema(schema)

    example_paths = sorted(
        {
            path
            for pattern in LOOP_RECORD_EXAMPLE_PATTERNS
            for path in examples_dir.glob(pattern)
        }
    )
    if not example_paths:
        raise RecordValidationError(
            f"{examples_dir}: no Loop Record examples found"
        )

    failures: list[str] = []
    for example_path in example_paths:
        try:
            validate_instance(
                schema,
                load_json(example_path),
                schema,
                example_path.name,
            )
        except RecordValidationError as exc:
            failures.append(str(exc))

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print(
        f"PASS: {len(example_paths)}/{len(example_paths)} Loop Record examples "
        f"validate against {schema_path}"
    )
    return 0


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description=(
            "Validate canonical gate-prefixed Loop Record examples against "
            "the supported subset used by schema/v13_loop_record.schema.json. "
            "Unsupported schema keywords fail closed."
        )
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=repo_root / "schema" / "v13_loop_record.schema.json",
    )
    parser.add_argument(
        "--examples-dir",
        type=Path,
        default=repo_root / "examples",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return validate_examples(args.schema, args.examples_dir)
    except (SchemaSupportError, RecordValidationError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
