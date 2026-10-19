from __future__ import annotations

from collections import Counter
from typing import Any

from timeskeleton import load_schema
from timeskeleton.manifest import _MAP_NESTED_MEMBERS, _MAP_NUMBER_MEMBERS

REFERENCE_PREFIX = "#/$defs/"


def _reference_name(value: Any) -> str | None:
    if not isinstance(value, dict):
        return None
    reference = value.get("$ref")
    if not isinstance(reference, str) or not reference.startswith(REFERENCE_PREFIX):
        return None
    return reference.removeprefix(REFERENCE_PREFIX)


def _recorded_facts(table: dict[str, dict[str, tuple[str, ...]]]) -> list[str]:
    return sorted(
        f"{map_name}.{kind}.{key}"
        for map_name, members in table.items()
        for kind, keys in members.items()
        for key in keys
    )


def _schema_facts() -> tuple[list[str], list[str]]:
    definitions = load_schema()["$defs"]
    map_names = [
        _reference_name(branch) for branch in definitions["ConversionMap"]["oneOf"]
    ]
    assert all(map_names)
    number_definitions = {"Number"} | {
        name for name in definitions if name.startswith("Fraction")
    }
    map_definitions = {"ConversionMap", *map_names}
    number: set[str] = set()
    nested: set[str] = set()

    for map_name in map_names:
        assert map_name is not None
        for key, member in definitions[map_name]["properties"].items():
            direct_reference = _reference_name(member)
            item_reference = _reference_name(member.get("items"))
            additional_reference = _reference_name(member.get("additionalProperties"))
            if direct_reference in number_definitions:
                number.add(f"{map_name}.values.{key}")
            if member.get("type") == "array" and item_reference in number_definitions:
                number.add(f"{map_name}.arrays.{key}")
            if direct_reference in map_definitions:
                nested.add(f"{map_name}.values.{key}")
            if member.get("type") == "array" and item_reference in map_definitions:
                nested.add(f"{map_name}.arrays.{key}")
            if (
                member.get("type") == "object"
                and additional_reference in map_definitions
            ):
                nested.add(f"{map_name}.records.{key}")
    return sorted(number), sorted(nested)


def _assert_exact(label: str, expected: list[str], recorded: list[str]) -> None:
    missing = sorted((Counter(expected) - Counter(recorded)).elements())
    extra = sorted((Counter(recorded) - Counter(expected)).elements())
    assert not missing and not extra, (
        f"{label}: missing {missing or 'none'}; extra {extra or 'none'}"
    )


def test_the_respelling_tables_match_the_schema() -> None:
    number, nested = _schema_facts()
    _assert_exact("number members", number, _recorded_facts(_MAP_NUMBER_MEMBERS))
    _assert_exact("nested-map members", nested, _recorded_facts(_MAP_NESTED_MEMBERS))
