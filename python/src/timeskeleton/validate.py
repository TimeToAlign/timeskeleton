"""The TimeSkeleton schema and its validator.

The schema is one document, ``schema/<version>/timeskeleton.schema.json``. A
value is checked for its version marker, then against the schema, then for
the representation of its own-axis values and for the identity rules the
schema cannot express. Every object of the schema is open: a key it does not
declare is kept and reported by :func:`unknown_keys`, never refused.

The schema file, the fixtures, the font and the drawing specification live at
the repository root and are bundled into the wheel under
``timeskeleton/schema``, ``timeskeleton/fixtures``, ``timeskeleton/fonts``
and ``timeskeleton/docs``. The resource helpers below find them in either
place, so the package works from an installed wheel and from a source
checkout alike.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from fractions import Fraction
from functools import cache
from importlib.resources import files
from itertools import pairwise
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, validators
from jsonschema.exceptions import ValidationError

from .manifest import _exact, spell

SCHEMA_VERSION = "0.7.0"
"""The schema version this package reads and writes, the only one it supports."""

_Path = tuple[str | int, ...]


class UnsupportedVersionError(ValueError):
    """Raised when a manifest's version marker names another version.

    Attributes:
        version: The value of the manifest's ``timeskeleton`` member.
    """

    def __init__(self, version: object) -> None:
        self.version = version
        super().__init__(
            f"unsupported TimeSkeleton version {version!r}; this package reads "
            f"{SCHEMA_VERSION} only"
        )


class SchemaValidationError(ValueError):
    """Raised when a value violates the schema or a rule checked after it.

    Attributes:
        path: The location of the offending value as a tuple of object keys and
            array indices, empty for the value root.
        message: The validator's description of the violation.
    """

    def __init__(self, path: _Path, message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{json_pointer(path)}: {message}")


def json_pointer(path: Iterable[str | int]) -> str:
    """Render a path as a JSON pointer in URI fragment form (``#`` for the root)."""
    segments = [str(segment).replace("~", "~0").replace("/", "~1") for segment in path]
    return "#" + "".join(f"/{segment}" for segment in segments)


def _data_root() -> Path:
    """Return the directory holding ``schema/``, ``fixtures/`` and ``fonts/``."""
    package = Path(str(files("timeskeleton")))
    if (package / "schema").is_dir():
        return package
    return Path(__file__).resolve().parents[3]


def schema_path() -> Path:
    """Return the path of the schema document."""
    return _data_root() / "schema" / SCHEMA_VERSION / "timeskeleton.schema.json"


@cache
def load_schema() -> dict[str, Any]:
    """Return the parsed schema document.

    The result is cached and shared; treat it as read-only.
    """
    with schema_path().open(encoding="utf-8") as handle:
        return json.load(handle)


def fixture_paths() -> list[Path]:
    """Return every bundled manifest fixture, sorted by its path.

    The manifests lie in ``fixtures/<version>/`` and its subdirectories; the
    drawings under ``drawings/`` are no manifests and are left out.
    """
    directory = _data_root() / "fixtures" / SCHEMA_VERSION
    return sorted(
        path
        for path in directory.rglob("*.json")
        if "drawings" not in path.relative_to(directory).parts
    )


def rejection_paths() -> list[Path]:
    """Return the shared rejection cases, sorted by name."""
    directory = _data_root() / "fixtures" / "rejections" / SCHEMA_VERSION
    return sorted(directory.glob("*.json"))


def warning_paths() -> list[Path]:
    """Return the shared warning cases, sorted by name."""
    directory = _data_root() / "fixtures" / "warnings" / SCHEMA_VERSION
    return sorted(directory.glob("*.json"))


def _unknown_key(
    validator: Any, value: Any, instance: Any, schema: Any
) -> Iterator[Any]:
    """Fail on every value the schema marks as held by an undeclared key."""
    if value is True:
        yield ValidationError("unknown key")


# The schema marks every object's undeclared keys with `x-unknown-key`, a
# keyword every other validator ignores. This validator fails there, so that
# each object holding unknown keys fails its `unevaluatedProperties`.
_MarkingValidator = validators.extend(
    Draft202012Validator, {"x-unknown-key": _unknown_key}
)


@cache
def _validator() -> Draft202012Validator:
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@cache
def _marking_validator() -> Any:
    return _MarkingValidator(load_schema())


def _branch_tag(candidate: Mapping[str, Any], tag: str) -> Any:
    """Return the ``const`` a ``oneOf`` candidate requires of the tag property.

    A candidate is either inline or a local ``#/$defs/<name>`` reference.
    """
    reference = candidate.get("$ref")
    if isinstance(reference, str) and reference.startswith("#/$defs/"):
        candidate = load_schema()["$defs"][reference.removeprefix("#/$defs/")]
    return candidate.get("properties", {}).get(tag, {}).get("const")


def _candidate_leaves(error: ValidationError) -> Iterable[ValidationError]:
    """Yield the diagnostic leaves beneath one validator error, left to right.

    A failed ``oneOf``, ``anyOf`` or ``$ref`` holds its sub-errors in
    ``context``. A discriminated ``oneOf`` descends only into the candidate
    whose tag ``const`` equals the instance's tag value, and is itself the
    leaf when no candidate carries that value. Every other error descends
    into all its sub-errors.
    """
    children = list(error.context or ())
    tag = error.schema.get("discriminator", {}).get("propertyName")
    if (
        error.validator == "oneOf"
        and tag is not None
        and isinstance(error.instance, Mapping)
    ):
        value = error.instance.get(tag)
        branch = next(
            (
                index
                for index, candidate in enumerate(error.schema["oneOf"])
                if value is not None and _branch_tag(candidate, tag) == value
            ),
            None,
        )
        children = [
            child
            for child in children
            if branch is not None
            and child.schema_path
            and child.schema_path[0] == branch
        ]
    if not children:
        yield error
        return
    for child in children:
        yield from _candidate_leaves(child)


def _select(errors: Iterable[ValidationError]) -> ValidationError | None:
    """Pick the error to report under the shared path rule.

    The rule, shared with the TypeScript validator: among the diagnostic
    leaves of every violation, report the one with the deepest instance
    path; ties go to the first leaf reported. A discriminated ``oneOf``
    contributes only the candidate its tag selects.
    """
    best: ValidationError | None = None
    for error in errors:
        for leaf in _candidate_leaves(error):
            if best is None or len(leaf.absolute_path) > len(best.absolute_path):
                best = leaf
    return best


def _check(value: Any) -> None:
    """Check a value through every rule; see :func:`validate`."""
    if not isinstance(value, Mapping) or "timeskeleton" not in value:
        raise SchemaValidationError((), "not a TimeSkeleton manifest")
    if value["timeskeleton"] != SCHEMA_VERSION:
        raise UnsupportedVersionError(value["timeskeleton"])
    error = _select(_validator().iter_errors(value))
    if error is not None:
        raise SchemaValidationError(tuple(error.absolute_path), error.message)
    for problem in _representation_problems(value):
        raise problem
    problems = identity_problems(value)
    if problems:
        raise problems[0]


def validate(value: Mapping[str, Any]) -> None:
    """Check that ``value`` is a TimeSkeleton manifest.

    The version marker is read first: a value that is no object or has no
    ``timeskeleton`` member is refused at the root, and a marker other than
    :data:`SCHEMA_VERSION` raises :class:`UnsupportedVersionError`. The value
    is then checked against the schema, then for the representation of every
    own-axis value (its timeline's number type selects an int, a float or a
    fraction pair), then for the identity rules
    (:func:`identity_problems`). Unknown keys are no violation;
    :func:`unknown_keys` reports them.

    Raises:
        SchemaValidationError: On the first violation found, with the path to
            the offending value.
        UnsupportedVersionError: For a version marker other than
            :data:`SCHEMA_VERSION`.
    """
    _check(value)


def _key_failures_only(error: ValidationError) -> bool:
    """Whether an error consists of unknown-key failures alone."""
    if error.validator == "unevaluatedProperties":
        return True
    if error.validator in ("oneOf", "anyOf") and error.context:
        return any(
            all(_key_failures_only(child) for child in branch)
            for branch in _branches(error)
        )
    return False


def _branches(error: ValidationError) -> Iterable[list[ValidationError]]:
    grouped: dict[Any, list[ValidationError]] = defaultdict(list)
    for child in error.context or ():
        grouped[child.relative_schema_path[0]].append(child)
    return grouped.values()


def _keys(errors: Iterable[ValidationError]) -> Iterator[tuple[_Path, str]]:
    """Yield the object path and key of every unknown key the errors locate.

    An object holding unknown keys fails its ``unevaluatedProperties``; every
    object that carries it declares in its own ``properties`` every key the
    schema evaluates on it, so the unknown keys are the others. A ``oneOf``
    or ``anyOf`` that failed only because one of its branches met unknown keys
    holds those failures in that branch's context; a branch failing for any
    other reason is not the one the instance matches.
    """
    for error in errors:
        if error.validator == "unevaluatedProperties":
            declared = error.schema["properties"]
            path = tuple(error.absolute_path)
            for key in error.instance:
                if key not in declared:
                    yield path, key
        elif error.validator in ("oneOf", "anyOf"):
            for branch in _branches(error):
                if all(_key_failures_only(child) for child in branch):
                    yield from _keys(branch)


def unknown_keys(value: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the keys of a manifest that the schema does not declare.

    Every object of the schema is open, so an undeclared key, a misspelt
    optional one included, is kept rather than refused; this lists them, each
    as ``{"path": [...], "key": ...}``, the path of its object (keys and
    indices) and the key, sorted by path (indices by number, keys by code
    point, an object before its descendants) and then by key. The JavaScript
    package's ``unknownKeys`` gives the same list. The value of an unknown key
    is not looked into.

    Raises:
        SchemaValidationError: If the value is no valid manifest (see
            :func:`validate`).
        UnsupportedVersionError: For a version marker other than
            :data:`SCHEMA_VERSION`.
    """
    _check(value)
    found = set(_keys(_marking_validator().iter_errors(value)))
    return [
        {"path": list(path), "key": key}
        for path, key in sorted(found, key=lambda entry: (entry[0], entry[1]))
    ]


# -- the values of a manifest ---------------------------------------------------

_UNIT_NUMBER_TYPES = {
    "number": "float",
    "floating_measures": "float",
    "whole_note": "fraction",
    "quarters": "fraction",
    "ticks": "int",
    "milliseconds": "float",
    "seconds": "float",
    "minutes": "float",
    "samples": "int",
    "frames": "int",
    "pixels": "int",
    "meters": "float",
    "centimeters": "float",
    "millimeters": "float",
    "inches": "float",
    "points": "float",
}
"""The default number type of each unit."""


def number_type_of(timeline: Mapping[str, Any]) -> str:
    """Return the number type of a timeline's axis: its own, or its unit's default."""
    return timeline.get("number_type") or _UNIT_NUMBER_TYPES[timeline["unit"]]


def _entries(owner: Any, key: str) -> list[Any]:
    """Return the objects of an array member, or none where it is absent."""
    value = owner.get(key) if isinstance(owner, Mapping) else None
    return value if isinstance(value, list) else []


# -- representation ------------------------------------------------------------

_ARTICLES = {"int": "an int", "float": "a float", "fraction": "a fraction"}


def _written_as(value: Any) -> str:
    if isinstance(value, list):
        return "fraction"
    return "int" if isinstance(value, int) else "float"


def _represents(value: Any, number_type: str) -> bool:
    if number_type == "fraction":
        return isinstance(value, list)
    if isinstance(value, list):
        return False
    if number_type == "float":
        return not isinstance(value, int) or _rewritten(value, "float") is not None
    return isinstance(value, int) or value.is_integer()


def _rewritten(value: Any, number_type: str) -> str | None:
    """Return the value written as ``number_type`` with exactly its value.

    Spelled as in a manifest, or ``None`` when no such representation exists.
    """
    exact = _exact(value)
    if number_type == "fraction":
        return spell([exact.numerator, exact.denominator])
    if number_type == "int":
        return spell(exact.numerator) if exact.denominator == 1 else None
    try:
        double = exact.numerator / exact.denominator
    except OverflowError:
        return None
    return spell(double) if Fraction(double) == exact else None


def _representation_problem(
    key: str, owner: Mapping[str, Any], path: _Path, number_type: str
) -> Iterator[SchemaValidationError]:
    """Yield the problem of an own-axis value its axis does not select.

    The message names the key, the value, the id of the object holding it,
    the representation found and the one the axis selects, and ends with the
    value rewritten where an exact rewriting exists.
    """
    value = owner.get(key)
    if value is None or _represents(value, number_type):
        return
    fix = _rewritten(value, number_type) or _ARTICLES[number_type]
    yield SchemaValidationError(
        (*path, key),
        f"{key} {spell(value)} of '{owner['id']}' is {_ARTICLES[_written_as(value)]} "
        f"on {_ARTICLES[number_type]} axis: write {fix}",
    )


def _timeline_representation(
    timeline: Mapping[str, Any], path: _Path, offset_type: str | None
) -> Iterator[SchemaValidationError]:
    """Yield the representation problems of a timeline tree.

    Its offset (on its parent's axis, a root's on its own), its length, its
    regions' starts and ends, its breaks', jumps' and markers' coordinates,
    then its children's trees in array order.
    """
    own = number_type_of(timeline)
    yield from _representation_problem("offset", timeline, path, offset_type or own)
    yield from _representation_problem("length", timeline, path, own)
    for index, region in enumerate(_entries(timeline, "regions")):
        for key in ("start", "end"):
            yield from _representation_problem(
                key, region, (*path, "regions", index), own
            )
    flow = timeline.get("flow_control") or {}
    for member, keys in (
        ("breaks", ("coordinate",)),
        ("jumps", ("from_coordinate", "to_coordinate")),
        ("markers", ("coordinate",)),
    ):
        for index, entry in enumerate(_entries(flow, member)):
            for key in keys:
                yield from _representation_problem(
                    key, entry, (*path, "flow_control", member, index), own
                )
    for index, child in enumerate(_entries(timeline, "children")):
        yield from _timeline_representation(child, (*path, "children", index), own)


def _representation_problems(
    manifest: Mapping[str, Any],
) -> Iterator[SchemaValidationError]:
    for index, root in enumerate(_entries(manifest, "timelines")):
        yield from _timeline_representation(root, ("timelines", index), None)


# -- identity ------------------------------------------------------------------


def _element_ids(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[tuple[str, _Path]]:
    """Yield every id of a timeline tree with its path, in identity order.

    A timeline contributes its own id, then the ids of its conversion maps,
    regions, breaks, jumps and markers in array order, then its children's
    trees in array order.
    """
    yield timeline["id"], (*path, "id")
    for member in ("conversion_maps", "regions"):
        for index, entry in enumerate(_entries(timeline, member)):
            yield entry["id"], (*path, member, index, "id")
    flow = timeline.get("flow_control")
    for member in ("breaks", "jumps", "markers"):
        for index, entry in enumerate(_entries(flow, member)):
            yield entry["id"], (*path, "flow_control", member, index, "id")
    for index, child in enumerate(_entries(timeline, "children")):
        yield from _element_ids(child, (*path, "children", index))


def _timeline_ids(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[tuple[str, _Path]]:
    """Yield the id of every timeline of a tree with its path, in identity order."""
    yield timeline["id"], (*path, "id")
    for index, child in enumerate(_entries(timeline, "children")):
        yield from _timeline_ids(child, (*path, "children", index))


def _dangling_targets(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[SchemaValidationError]:
    """Yield a problem for each jump whose target names no marker of its timeline."""
    flow = timeline.get("flow_control")
    markers = {marker["id"] for marker in _entries(flow, "markers")}
    for index, jump in enumerate(_entries(flow, "jumps")):
        target = jump.get("target")
        if target is not None and target not in markers:
            yield SchemaValidationError(
                (*path, "flow_control", "jumps", index, "target"),
                f"{target!r} names no marker of this timeline",
            )
    for index, child in enumerate(_entries(timeline, "children")):
        yield from _dangling_targets(child, (*path, "children", index))


def _duplicate(identifier: str, path: _Path, first: _Path) -> SchemaValidationError:
    return SchemaValidationError(
        path, f"duplicate id {identifier!r}, first at {json_pointer(first)}"
    )


def _offset_order(children: list[Any]) -> list[int]:
    """Return the indices of children in offset order, ties by id by code point."""
    return sorted(
        range(len(children)),
        key=lambda index: (_exact(children[index]["offset"]), children[index]["id"]),
    )


def _child_ends(timeline: Mapping[str, Any]) -> list[Fraction | None]:
    """Return where each child of a timeline ends on its axis, ``None`` where unknown.

    A child of the timeline's unit ends at its offset plus its known length; a
    segment of unknown length ends where its successor in offset order starts.
    """
    children = _entries(timeline, "children")
    ends: list[Fraction | None] = [
        _exact(child["offset"]) + _exact(child["length"])
        if child.get("length") is not None and child["unit"] == timeline["unit"]
        else None
        for child in children
    ]
    if timeline.get("is_segment_line") is True:
        order = _offset_order(children)
        for index, successor in pairwise(order):
            if children[index].get("length") is None:
                ends[index] = _exact(children[successor]["offset"])
    return ends


def _child_problems(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[SchemaValidationError]:
    """Yield a problem for each child that does not sit on its parent's axis.

    Child by child in array order, each followed by its own children: a unit
    other than its parent's, at its ``unit``; where the parent's length is
    known, an offset beyond it, at the ``offset``, or else an end beyond it
    where the child's end is known (see ``_child_ends``), at the child's
    ``length``. A negative offset is no problem: the child starts before its
    parent's origin. The end is spelled as the parent's number type writes
    it, as a fraction pair where that type cannot write it exactly. Values
    compare exactly.
    """
    length = timeline.get("length")
    ends = _child_ends(timeline)
    for index, child in enumerate(_entries(timeline, "children")):
        at = (*path, "children", index)
        offset = _exact(child["offset"])
        if child["unit"] != timeline["unit"]:
            yield SchemaValidationError(
                (*at, "unit"),
                f"child '{child['id']}' has unit '{child['unit']}', its parent "
                f"'{timeline['id']}' has '{timeline['unit']}'",
            )
        end = ends[index]
        if length is not None and offset > _exact(length):
            yield SchemaValidationError(
                (*at, "offset"),
                f"offset {spell(child['offset'])} of '{child['id']}' is beyond the "
                f"length {spell(length)} of its parent '{timeline['id']}'",
            )
        elif length is not None and end is not None and end > _exact(length):
            pair = [end.numerator, end.denominator]
            yield SchemaValidationError(
                (*at, "length"),
                f"child '{child['id']}' ends at "
                f"{_rewritten(pair, number_type_of(timeline)) or spell(pair)}, beyond "
                f"the length {spell(length)} of its parent '{timeline['id']}'",
            )
        yield from _child_problems(child, at)


def _root_problems(root: Mapping[str, Any], path: _Path) -> list[SchemaValidationError]:
    """Return the problems of one root, its own scope.

    Duplicate ids within its tree, then jump targets, then children off their
    parent's axis or beyond its length, then segment lines.
    """
    problems: list[SchemaValidationError] = []
    first: dict[str, _Path] = {}
    for identifier, at in _element_ids(root, path):
        if identifier in first:
            problems.append(_duplicate(identifier, at, first[identifier]))
        else:
            first[identifier] = at
    problems.extend(_dangling_targets(root, path))
    problems.extend(_child_problems(root, path))
    problems.extend(_segment_problems(root, path))
    return problems


def _segment_problems(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[SchemaValidationError]:
    """Yield the problems of every segment line of a timeline tree.

    A timeline with ``is_segment_line`` true holds only its segments, visited
    in offset order (ties by id in code-point order): a segment whose
    ``is_segment_line`` differs from the first segment's, at that member (at
    the segment where it is absent); a segment that does not start where the
    one before it ends (the first at 0), at its ``offset``; then, if the last
    segment does not end at the segment line's length, one problem at
    the ``length``. A segment of unknown length ends where its successor
    starts, so the successor's offset is not checked, and the end is not
    checked where the last segment's length or the segment line's is not
    known. Values compare exactly; the tree is visited in identity order.
    """
    children = _entries(timeline, "children")
    if timeline.get("is_segment_line") is True:
        order = _offset_order(children)
        end: Fraction | None = Fraction(0)
        flag = False
        first_id = ""
        for position, index in enumerate(order):
            segment = children[index]
            at = (*path, "children", index)
            name = f"segment {segment['id']!r} of segment line {timeline['id']!r}"
            segment_flag = segment.get("is_segment_line") is True
            if position == 0:
                flag, first_id = segment_flag, segment["id"]
            elif segment_flag != flag:
                yield SchemaValidationError(
                    (*at, "is_segment_line") if "is_segment_line" in segment else at,
                    f"{name} differs from segment {first_id!r} in is_segment_line",
                )
            offset = _exact(segment["offset"])
            if end is not None and offset != end:
                yield SchemaValidationError(
                    (*at, "offset"),
                    f"{name} does not "
                    + (
                        "start at 0"
                        if position == 0
                        else "start where the one before it ends"
                    ),
                )
            length = segment.get("length")
            end = None if length is None else offset + _exact(length)
        length = timeline.get("length")
        if end is not None and length is not None and end != _exact(length):
            yield SchemaValidationError(
                (*path, "length"),
                f"the segments of segment line {timeline['id']!r} do not end at its "
                "length",
            )
    for index, child in enumerate(children):
        yield from _segment_problems(child, (*path, "children", index))


_PART_WORDS = ("start", "end", "name", "label", "card")
"""The part words, which follow an element's address as its parts and so are no id."""


def _reserved(identifier: str, path: _Path) -> SchemaValidationError:
    return SchemaValidationError(
        path, f"id {identifier!r} is reserved for the parts of an address"
    )


def _order_problems(
    group: Mapping[str, Any], order: list[str], path: _Path
) -> Iterator[SchemaValidationError]:
    """Yield the problems of a display order that is no permutation of members.

    Each entry that is not a member is one problem at the entry; then each
    member missing from the order is one problem at the order.
    """
    members = set(group["members"])
    listed = set(order)
    for index, entry in enumerate(order):
        if entry not in members:
            yield SchemaValidationError(
                (*path, index), f"{entry!r} is not a member of group {group['id']!r}"
            )
    for member in group["members"]:
        if member not in listed:
            yield SchemaValidationError(
                path, f"member {member!r} of group {group['id']!r} is missing"
            )


def _ancestors(roots: list[Mapping[str, Any]]) -> dict[str, tuple[str, ...]]:
    """Return the ancestor ids of every timeline of the roots, nearest first.

    Where a timeline id repeats (a problem reported on its own), its first
    occurrence counts.
    """
    found: dict[str, tuple[str, ...]] = {}

    def visit(timeline: Mapping[str, Any], above: tuple[str, ...]) -> None:
        found.setdefault(timeline["id"], above)
        for child in _entries(timeline, "children"):
            visit(child, (timeline["id"], *above))

    for root in roots:
        visit(root, ())
    return found


def _member_problems(
    group: Mapping[str, Any],
    path: _Path,
    ancestors: Mapping[str, tuple[str, ...]],
    first_member: dict[str, _Path],
) -> Iterator[SchemaValidationError]:
    """Yield the problems of a group's members, member by member.

    A member naming no timeline of the manifest is one problem and is not
    checked further; a member named by an earlier group is one; then a member
    nested with an earlier member of the same group (inside it or containing
    it) is one, naming the first such earlier member.
    """
    checked: list[str] = []
    for index, member in enumerate(group["members"]):
        at = (*path, index)
        if member not in ancestors:
            yield SchemaValidationError(
                at, f"{member!r} names no timeline of this manifest"
            )
            continue
        if member in first_member:
            earlier = json_pointer(first_member[member])
            yield SchemaValidationError(
                at, f"duplicate member {member!r}, first at {earlier}"
            )
        else:
            first_member[member] = at
        for other in checked:
            if other in ancestors[member]:
                relation = "lies inside"
            elif member in ancestors.get(other, ()):
                relation = "contains"
            else:
                continue
            yield SchemaValidationError(
                at, f"member {member!r} {relation} member {other!r} of the same group"
            )
            break
        checked.append(member)


def identity_problems(value: Mapping[str, Any]) -> list[SchemaValidationError]:
    """Return the violations of the identity rules in a schema-valid manifest.

    In this order, one problem per finding:

    1. root by root, in array order, each root's tree is its own scope: every
       id of a timeline, conversion map, region, break, jump and marker of the
       tree is unique within it, each repeated id one problem at its later
       occurrence in identity order (a timeline, then its maps, regions,
       breaks, jumps and markers, then its children in array order),
       ``duplicate id '<id>', first at <pointer>``; then each jump whose
       non-null ``target`` names no marker of its own timeline, at the target;
       then each child whose ``unit`` is not its parent's, ``child '<id>' has
       unit '<u>', its parent '<pid>' has '<pu>'``, whose ``offset`` is
       beyond its parent's known length, ``offset <v> of '<id>' is beyond the
       length <pl> of its parent '<pid>'``, or which ends beyond it, ``child
       '<id>' ends at <e>, beyond the length <pl> of its parent '<pid>'``
       (see ``_child_problems``); then the segment lines (see
       ``_segment_problems``);
    2. every id that is a part word (``start``, ``end``, ``name``, ``label``,
       ``card``), which follow an address as its parts: the manifest's ``id``,
       then root by root every id of the tree in identity order, then each
       group's id;
    3. a timeline id (of a root or a descendant) repeating a timeline id of an
       earlier root, at the later occurrence;
    4. a group id equal to a timeline id (first at the timeline) or to the id
       of an earlier group (first at that group), at the group's ``id``;
    5. the manifest's ``id`` equal to a timeline id or a group id, at ``id``,
       first at the timeline, else at the first such group;
    6. group by group, member by member: a member naming no timeline of the
       manifest; a member already named by an earlier group, ``duplicate
       member``; a member nested with an earlier member of the same group
       (inside it or containing it), each at the member;
    7. each key of ``graphical.order`` in code-point order: a key naming no
       group, at the key; each entry that is not a member of the group, at the
       entry; then each member missing from the order, at the order.

    A key with a default may be absent; its default applies.
    """
    problems: list[SchemaValidationError] = []
    roots = _entries(value, "timelines")
    groups = _entries(value, "groups")
    for index, root in enumerate(roots):
        problems.extend(_root_problems(root, ("timelines", index)))
    manifest_id = value.get("id")
    if manifest_id in _PART_WORDS:
        problems.append(_reserved(manifest_id, ("id",)))
    for index, root in enumerate(roots):
        for identifier, at in _element_ids(root, ("timelines", index)):
            if identifier in _PART_WORDS:
                problems.append(_reserved(identifier, at))
    for index, group in enumerate(groups):
        if group["id"] in _PART_WORDS:
            problems.append(_reserved(group["id"], ("groups", index, "id")))
    timelines: dict[str, _Path] = {}
    for index, root in enumerate(roots):
        seen: dict[str, _Path] = {}
        for identifier, path in _timeline_ids(root, ("timelines", index)):
            if identifier in seen:
                continue
            seen[identifier] = path
            if identifier in timelines:
                problems.append(_duplicate(identifier, path, timelines[identifier]))
        for identifier, path in seen.items():
            timelines.setdefault(identifier, path)
    first_group: dict[str, int] = {}
    for index, group in enumerate(groups):
        identifier = group["id"]
        path = ("groups", index, "id")
        if identifier in timelines:
            problems.append(_duplicate(identifier, path, timelines[identifier]))
        elif identifier in first_group:
            earlier = ("groups", first_group[identifier], "id")
            problems.append(_duplicate(identifier, path, earlier))
        first_group.setdefault(identifier, index)
    if manifest_id is not None:
        if manifest_id in timelines:
            problems.append(_duplicate(manifest_id, ("id",), timelines[manifest_id]))
        elif manifest_id in first_group:
            earlier = ("groups", first_group[manifest_id], "id")
            problems.append(_duplicate(manifest_id, ("id",), earlier))
    ancestors = _ancestors(roots)
    first_member: dict[str, _Path] = {}
    for index, group in enumerate(groups):
        problems.extend(
            _member_problems(
                group, ("groups", index, "members"), ancestors, first_member
            )
        )
    orders = (value.get("graphical") or {}).get("order") or {}
    for key in sorted(orders):
        path = ("graphical", "order", key)
        if key not in first_group:
            problems.append(
                SchemaValidationError(path, f"{key!r} names no group of this manifest")
            )
        else:
            problems.extend(
                _order_problems(groups[first_group[key]], orders[key], path)
            )
    return problems
