"""Migrations between schema versions.

A migration is a pure function from a document at one version to the same
document at the next version, declaring that version. ``migrate`` chains them
from the declared version up to ``SCHEMA_VERSION``. Each migration is
pinned by a fixture pair (the document before and after) in the test suite.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping
from fractions import Fraction
from typing import Any

from .document import canonical_order
from .validate import (
    SCHEMA_VERSION,
    SUPPORTED_VERSIONS,
    SchemaValidationError,
    UnsupportedVersionError,
    declared_version,
    json_pointer,
    validate,
)

Migration = Callable[[dict[str, Any]], dict[str, Any]]
Path = tuple[str | int, ...]


class MigrationError(ValueError):
    """Raised when a document holds a member whose shape a migration does not know.

    Attributes:
        path: The location of the offending value as a tuple of object keys and
            array indices, empty for the document root.
        message: Why the member cannot be migrated.
    """

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{json_pointer(path)}: {message}")


# -- 0.1.0 to 0.2.0 ----------------------------------------------------------

_MEASURE_CLASSES = (
    "Measure",
    "RegularMeasure",
    "IrregularMeasure",
    "MeasureConstituent",
    "CadenzaMeasure",
)
_MEASURE_KEYS = (
    "class",
    "id",
    "count",
    "qstamp",
    "number",
    "name",
    "time_signature",
    "nominal_length",
    "actual_length",
    "start_repeat",
    "end_repeat",
    "next",
    "volta",
)
_ROW_KEYS = (
    "ID",
    "count",
    "qstamp",
    "number",
    "name",
    "time_signature",
    "nominal_length",
    "actual_length",
    "start_repeat",
    "end_repeat",
    "next",
    "volta",
    "offset_within_measure",
)
_QUARTER_KEYS = ("qstamp", "nominal_length", "actual_length", "offset_within_measure")


def _integer(value: Any) -> int | None:
    """Return a JSON integer as an int, else ``None``.

    A boolean is not an integer. An integral float is, because a JavaScript
    reader cannot tell ``2.0`` from ``2``: both packages read the same text
    the same way.
    """
    if type(value) is int:
        return value
    if type(value) is float and value.is_integer():
        return int(value)
    return None


def _quarters(value: Any, path: Path) -> Fraction | None:
    """Read a 0.1.0 measure quarter value: a Fraction pair, or null."""
    if value is None:
        return None
    if isinstance(value, list) and len(value) == 2:
        numerator, denominator = (_integer(item) for item in value)
        if numerator is not None and denominator is not None and denominator > 0:
            return Fraction(numerator, denominator)
    raise MigrationError(path, f"expected a Fraction pair or null, got {value!r}")


def _pair(value: Fraction) -> list[int]:
    return [value.numerator, value.denominator]


def _measure_class(measure: Mapping[str, Any]) -> str:
    """Return the class a 0.2.0 reader derives from a measure's values."""
    signature = measure["time_signature"]
    if measure["nominal_length"] is None:
        return "Measure"
    if isinstance(signature, str) and signature.lower() == "cadenza":
        return "CadenzaMeasure"
    if measure["offset_within_measure"]:
        return "MeasureConstituent"
    if measure["actual_length"] == measure["nominal_length"]:
        return "RegularMeasure"
    return "IrregularMeasure"


def _read_measures(value: Any, path: Path) -> list[dict[str, Any]]:
    """Read the tagged-measure measure map timetoalign wrote at 0.1.0."""
    if not isinstance(value, Mapping) or set(value) != {"measures"}:
        raise MigrationError(path, "expected an object whose only member is 'measures'")
    items = value["measures"]
    if not isinstance(items, list) or not items:
        raise MigrationError((*path, "measures"), "expected a non-empty array")
    measures: list[dict[str, Any]] = []
    ids: dict[str, str] = {}
    for position, item in enumerate(items, start=1):
        item_path: Path = (*path, "measures", position - 1)
        if not isinstance(item, Mapping):
            raise MigrationError(item_path, "expected a tagged measure object")
        tag = item.get("class")
        if tag not in _MEASURE_CLASSES:
            raise MigrationError(
                (*item_path, "class"), f"no row form for class {tag!r}"
            )
        expected = set(_MEASURE_KEYS) | (
            {"offset_within_measure"} if tag == "MeasureConstituent" else set()
        )
        if set(item) != expected:
            unknown = sorted(set(item) ^ expected)[0]
            raise MigrationError((*item_path, unknown), "not a 0.1.0 measure member")
        if _integer(item["count"]) != position:
            raise MigrationError((*item_path, "count"), f"expected count {position}")
        identifier = item["id"]
        if not isinstance(identifier, str):
            raise MigrationError((*item_path, "id"), "expected a string")
        # timetoalign spelled the default identity "m<count>"; the row ID's
        # default is str(count).
        ids[identifier] = str(position) if identifier == f"m{position}" else identifier
        measure = {key: item[key] for key in _MEASURE_KEYS}
        measure["ID"] = ids[identifier]
        for key in _QUARTER_KEYS:
            measure[key] = _quarters(item.get(key), (*item_path, key))
        measure["offset_within_measure"] = measure["offset_within_measure"] or Fraction(
            0
        )
        if _measure_class(measure) != tag:
            raise MigrationError(
                (*item_path, "class"),
                f"a row with these values reads as {_measure_class(measure)}, "
                f"not {tag}",
            )
        measures.append(measure)
    for index, measure in enumerate(measures):
        successors = measure["next"]
        next_path: Path = (*path, "measures", index, "next")
        if successors is None:
            measure["next"] = (
                [measures[index + 1]["ID"]] if index + 1 < len(measures) else []
            )
        elif isinstance(successors, list) and all(
            isinstance(entry, str) and entry in ids for entry in successors
        ):
            measure["next"] = [ids[entry] for entry in successors]
        else:
            raise MigrationError(next_path, "expected null or measure ids of this map")
    return measures


def _rows(measures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compress measures into rows exactly as timetoalign's MeasureMap.to_rows."""
    last = len(measures) - 1

    def encoded(values: Mapping[str, Any]) -> dict[str, Any]:
        return {
            key: _pair(values[key]) if key in _QUARTER_KEYS else values[key]
            for key in _ROW_KEYS
            if values.get(key) is not None
        }

    def row_for(index: int) -> dict[str, Any]:
        measure = measures[index]
        number = (
            measure["number"] if measure["number"] is not None else measure["count"]
        )
        successors = measure["next"]
        return encoded(
            {
                **measure,
                "ID": None if measure["ID"] == str(measure["count"]) else measure["ID"],
                "number": number,
                "name": measure["name"] if measure["name"] is not None else str(number),
                "next": successors if index < last or successors else None,
                "offset_within_measure": measure["offset_within_measure"] or None,
            }
        )

    def default_successor(index: int) -> dict[str, Any]:
        measure = measures[index]
        successor = row_for(index)
        for key in ("ID", "volta", "offset_within_measure"):
            successor.pop(key, None)
        successor["count"] = measure["count"] + 1
        if measure["qstamp"] is not None and measure["actual_length"] is not None:
            successor["qstamp"] = _pair(measure["qstamp"] + measure["actual_length"])
        if measure["actual_length"] is not None:
            successor.pop("actual_length")
            if measure["nominal_length"] is not None:
                successor["actual_length"] = _pair(measure["nominal_length"])
        if measure["number"] is not None:
            successor["number"] = measure["number"] + 1
            if measure["name"] is not None:
                successor["name"] = str(measure["number"] + 1)
        successor["start_repeat"] = False
        successor["end_repeat"] = False
        successor["next"] = [measures[index + 2]["ID"]]
        return successor

    return [
        row_for(index)
        for index in range(len(measures))
        if index in (0, last) or row_for(index) != default_successor(index - 1)
    ]


def _metrical_position_map(value: Mapping[str, Any], path: Path) -> dict[str, Any]:
    """Keep the meter map once and name the derived beat map by its id."""
    expected = {
        "type",
        "id",
        "name",
        "source_unit",
        "target_unit",
        "maps",
        "names",
        "meter_map",
    }
    if set(value) != expected:
        unknown = sorted(set(value) ^ expected)[0]
        raise MigrationError((*path, unknown), "not a 0.1.0 MetricalPositionMap member")
    maps = value["maps"]
    beat = maps.get("beat") if isinstance(maps, Mapping) else None
    derived = (
        isinstance(maps, Mapping)
        and set(maps) == {"mc", "beat"}
        and value["names"] == ["mc", "beat"]
        and maps["mc"] == value["meter_map"]
        and isinstance(beat, Mapping)
        and isinstance(beat.get("id"), str)
        and beat
        == {
            "type": "BeatInMeasureMap",
            "id": beat["id"],
            "name": "beat_in_measure",
            "source_unit": "quarters",
            "target_unit": None,
            "meter_map": value["meter_map"],
        }
    )
    if not derived:
        raise MigrationError(
            (*path, "maps"), "the maps are not the two derived from meter_map"
        )
    return {
        "type": value["type"],
        "id": value["id"],
        "name": value["name"],
        "source_unit": value["source_unit"],
        "target_unit": value["target_unit"],
        "meter_map": value["meter_map"],
        "beat_map_id": beat["id"],
    }


def _conversion_map(value: Any, path: Path) -> Any:
    """Migrate one conversion map, descending into the maps it composes."""
    if not isinstance(value, Mapping):
        return value
    kind = value.get("type")
    if kind == "MetricalPositionMap":
        return _metrical_position_map(value, path)
    result = dict(value)
    if kind in ("ChainMap", "PiecewiseMap") and isinstance(value.get("maps"), list):
        result["maps"] = [
            _conversion_map(item, (*path, "maps", index))
            for index, item in enumerate(value["maps"])
        ]
    if kind == "CombinationMap" and isinstance(value.get("maps"), Mapping):
        result["maps"] = {
            name: _conversion_map(item, (*path, "maps", name))
            for name, item in value["maps"].items()
        }
    return result


def _timeline(manifest: dict[str, Any], path: Path) -> None:
    """Migrate one timeline manifest and its children in place."""
    if isinstance(manifest.get("measure_map"), Mapping):
        manifest["measure_map"] = _rows(
            _read_measures(manifest["measure_map"], (*path, "measure_map"))
        )
    if isinstance(manifest.get("conversion_maps"), list):
        manifest["conversion_maps"] = [
            _conversion_map(item, (*path, "conversion_maps", index))
            for index, item in enumerate(manifest["conversion_maps"])
        ]
    children = manifest.get("children")
    if isinstance(children, Mapping):
        for key, child in children.items():
            if isinstance(child, Mapping) and isinstance(child.get("timeline"), dict):
                _timeline(child["timeline"], (*path, "children", key, "timeline"))


def _migrate_0_1_0_to_0_2_0(document: dict[str, Any]) -> dict[str, Any]:
    """Give the members 0.1.0 left opaque their 0.2.0 shapes.

    0.1.0 specified only the envelope, a timeline's top level and its
    coordinates. This step rewrites the shapes timetoalign wrote at 0.1.0
    that 0.2.0 specifies differently: a tagged-measure ``measure_map``
    becomes compressed Measure Map rows, and a ``MetricalPositionMap``, at
    any depth of the conversion maps, keeps its meter map once and names its
    derived beat map by ``beat_map_id``. Every other member is kept as it
    is, and the result must then satisfy 0.2.0: a member whose shape the
    step does not know is refused with its path.

    Raises:
        MigrationError: At the path of the first member that cannot be
            migrated.
    """
    timelines = document.get("manifest", {}).get("timelines")
    if isinstance(timelines, Mapping):
        for key, manifest in timelines.items():
            if isinstance(manifest, dict):
                _timeline(manifest, ("manifest", "timelines", key))
    return _stamped(document, "0.2.0")


# -- 0.2.0 to 0.2.1 ----------------------------------------------------------


def _migrate_0_2_0_to_0_2_1(document: dict[str, Any]) -> dict[str, Any]:
    """Write the document in the canonical order of 0.2.1.

    0.2.1 specifies the same shapes as 0.2.0 and fixes the order of every
    collection whose order carries no meaning (see
    :func:`~timeskeleton.canonical_order`). The document is validated against
    0.2.1 before it is reordered, since the order does not affect validity, so
    a refusal names the path of the input.

    Raises:
        MigrationError: At the path of the first member with no 0.2.1 shape.
    """
    return canonical_order(_stamped(document, "0.2.1"))


# -- 0.2.1 to 0.3.0 ----------------------------------------------------------


def _migrate_0_2_1_to_0_3_0(document: dict[str, Any]) -> dict[str, Any]:
    """Declare 0.3.0.

    0.3.0 keeps every definition of 0.2.1 and adds the optional ``graphical``
    block, which a 0.2.1 document does not carry, so the shapes are unchanged.
    The document is validated against 0.3.0 and then put in canonical order.

    Raises:
        MigrationError: At the path of the first member with no 0.3.0 shape.
    """
    return canonical_order(_stamped(document, "0.3.0"))


def _stamped(document: dict[str, Any], version: str) -> dict[str, Any]:
    """Return ``document`` declaring ``version``, refused unless valid at it."""
    stamped = {
        **document,
        "meta": {**document.get("meta", {}), "schema_version": version},
    }
    try:
        validate(stamped)
    except SchemaValidationError as error:
        raise MigrationError(
            error.path, f"no {version} shape: {error.message}"
        ) from error
    return stamped


MIGRATIONS: dict[str, tuple[str, Migration]] = {
    "0.1.0": ("0.2.0", _migrate_0_1_0_to_0_2_0),
    "0.2.0": ("0.2.1", _migrate_0_2_0_to_0_2_1),
    "0.2.1": ("0.3.0", _migrate_0_2_1_to_0_3_0),
}
"""Source version to ``(target version, migration)``.

Each migration returns the document declaring its target version.
"""


def migrate(document: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deep copy of ``document`` brought to ``SCHEMA_VERSION``.

    A document already at the latest version is copied unchanged and not
    validated; call :func:`~timeskeleton.validate` on it when the input is
    untrusted. A migrated document satisfies the latest schema.

    Raises:
        UnsupportedVersionError: If ``meta.schema_version`` is missing, not a
            string, or not one of ``SUPPORTED_VERSIONS``.
        MigrationError: If a member cannot be migrated, at its path.
    """
    version = declared_version(document)
    if version is None or version not in SUPPORTED_VERSIONS:
        raise UnsupportedVersionError(version)
    result = copy.deepcopy(dict(document))
    while version != SCHEMA_VERSION:
        version, step = MIGRATIONS[version]
        result = step(result)
    return result
