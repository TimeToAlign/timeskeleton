"""The TimeSkeleton schemas and their validators.

Versions 0.5.0 and 0.6.0 have one schema document each,
``schema/timeskeleton-<version>.schema.json``, for the one file kind they
know, the timeline file. From 0.7.0 on a version has four documents under
``schema/<version>/``: ``core`` (the shared definitions), ``timeline``,
``group`` and ``bundle``, one per file kind, referring to each other by
relative ``$ref``. A value is checked against the document of its version and
kind, then for the identity rules the schema cannot express. The schema files,
the fixtures, the font and the drawing specification live at the repository
root and are bundled into the wheel under ``timeskeleton/schema``,
``timeskeleton/fixtures``, ``timeskeleton/fonts`` and ``timeskeleton/docs``.
The resource helpers below find them in either place, so the package works
from an installed wheel and from a source checkout alike.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from fractions import Fraction
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from referencing import Registry, Resource

from .manifest import _exact

SCHEMA_VERSION = "0.7.0"
"""The latest schema version bundled by this package."""

SUPPORTED_VERSIONS: tuple[str, ...] = ("0.5.0", "0.6.0", "0.7.0")
"""Every bundled schema version, oldest first."""

FILE_KINDS: tuple[str, ...] = ("timeline", "group", "bundle")
"""The file kinds, each named by the top-level member that holds its content.

A file of version 0.7.0 or later holds exactly one of these members beside
``meta``; versions 0.5.0 and 0.6.0 know the timeline file only.
"""

SCHEMA_DOCUMENTS: tuple[str, ...] = ("core", "timeline", "group", "bundle")
"""The schema documents of a version from 0.7.0 on: the shared ``core`` and
one document per file kind."""


class UnsupportedVersionError(ValueError):
    """Raised when a value declares a schema version this release does not know.

    Attributes:
        version: The declared version, or ``None`` when the value carries no
            string ``meta.schema_version``.
    """

    def __init__(self, version: object) -> None:
        self.version = version
        supported = ", ".join(SUPPORTED_VERSIONS)
        super().__init__(
            f"unsupported schema_version {version!r}; this package supports {supported}"
        )


class SchemaValidationError(ValueError):
    """Raised when a value violates its schema.

    Attributes:
        path: The location of the offending value as a tuple of object keys and
            array indices, empty for the value root.
        message: The validator's description of the violation.
    """

    def __init__(self, path: tuple[str | int, ...], message: str) -> None:
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


def _require_supported(version: str) -> None:
    if version not in SUPPORTED_VERSIONS:
        raise UnsupportedVersionError(version)


def _single_document(version: str) -> Path:
    """Return the path a version with one schema document keeps it at."""
    return _data_root() / "schema" / f"timeskeleton-{version}.schema.json"


def schema_documents(version: str = SCHEMA_VERSION) -> tuple[str, ...]:
    """Return the names of the schema documents of ``version``.

    A version with one document (0.5.0, 0.6.0) has ``("timeline",)``; a later
    version has :data:`SCHEMA_DOCUMENTS`.

    Raises:
        UnsupportedVersionError: If no schema of that version is bundled.
    """
    _require_supported(version)
    return ("timeline",) if _single_document(version).is_file() else SCHEMA_DOCUMENTS


def schema_path(version: str = SCHEMA_VERSION, document: str = "timeline") -> Path:
    """Return the path of one schema document of ``version``.

    Args:
        version: A supported schema version.
        document: One of :func:`schema_documents` of that version; the
            timeline document by default, which for 0.5.0 and 0.6.0 is the
            version's one schema file.

    Raises:
        UnsupportedVersionError: If no schema of that version is bundled.
        ValueError: If the version has no document of that name.
    """
    if document not in schema_documents(version):
        raise ValueError(f"schema {version} has no {document!r} document")
    if _single_document(version).is_file():
        return _single_document(version)
    return _data_root() / "schema" / version / f"{document}.schema.json"


@cache
def load_schema(
    version: str = SCHEMA_VERSION, document: str = "timeline"
) -> dict[str, Any]:
    """Return one parsed schema document of ``version``.

    The result is cached and shared; treat it as read-only.

    Raises:
        UnsupportedVersionError: If no schema of that version is bundled.
        ValueError: If the version has no document of that name.
    """
    with schema_path(version, document).open(encoding="utf-8") as handle:
        return json.load(handle)


def fixture_paths(version: str = SCHEMA_VERSION, kind: str = "timeline") -> list[Path]:
    """Return the bundled fixtures of one file kind for ``version``, sorted by name.

    Timeline files lie directly in ``fixtures/<version>/``, group files in its
    ``groups/`` and bundle files in its ``bundles/`` directory. A version
    before 0.7.0 has timeline files only.

    Raises:
        UnsupportedVersionError: If no fixtures of that version are bundled.
        ValueError: If ``kind`` is not one of :data:`FILE_KINDS`.
    """
    _require_supported(version)
    if kind not in FILE_KINDS:
        raise ValueError(f"unknown file kind {kind!r}; the kinds are {FILE_KINDS}")
    directory = _data_root() / "fixtures" / version
    if kind != "timeline":
        directory = directory / f"{kind}s"
    return sorted(directory.glob("*.json"))


def rejection_paths(version: str = SCHEMA_VERSION) -> list[Path]:
    """Return the shared rejection cases for ``version``, sorted by name."""
    _require_supported(version)
    return sorted((_data_root() / "fixtures" / "rejections" / version).glob("*.json"))


@cache
def _registry(version: str) -> Registry:
    """Return a registry holding every schema document of ``version``."""
    resources = []
    for name in schema_documents(version):
        schema = load_schema(version, name)
        Draft202012Validator.check_schema(schema)
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


@cache
def _validator(version: str, document: str) -> Draft202012Validator:
    """Return the validator of one document, with every document of its version."""
    return Draft202012Validator(
        load_schema(version, document), registry=_registry(version)
    )


@cache
def _declaration_validator() -> Draft202012Validator:
    """Return a validator of ``meta`` alone, as the latest version states it."""
    meta = f"{load_schema(SCHEMA_VERSION, 'core')['$id']}#/$defs/Meta"
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["meta"],
        "properties": {"meta": {"$ref": meta}},
    }
    return Draft202012Validator(schema, registry=_registry(SCHEMA_VERSION))


@cache
def _definitions(version: str) -> dict[str, Any]:
    """Return the ``$defs`` of every document of ``version`` by name.

    Definition names are unique across the documents of a version, so a
    reference ``#/$defs/<name>`` resolves by its name alone.
    """
    definitions: dict[str, Any] = {}
    for name in schema_documents(version):
        definitions.update(load_schema(version, name).get("$defs", {}))
    return definitions


def declared_version(value: object) -> str | None:
    """Return ``meta.schema_version`` if present as a string, else ``None``."""
    if not isinstance(value, Mapping):
        return None
    meta = value.get("meta")
    if not isinstance(meta, Mapping):
        return None
    version = meta.get("schema_version")
    return version if isinstance(version, str) else None


def file_kind(value: object) -> str | None:
    """Return the kind of a file: the one member of :data:`FILE_KINDS` it holds.

    Returns ``None`` for a value that holds none or several of them, or is no
    object.
    """
    if not isinstance(value, Mapping):
        return None
    present = [kind for kind in FILE_KINDS if kind in value]
    return present[0] if len(present) == 1 else None


def _branch_tag(
    candidate: Mapping[str, Any], definitions: Mapping[str, Any], tag: str
) -> Any:
    """Return the ``const`` a ``oneOf`` candidate requires of the tag property.

    A candidate is either inline or a local ``#/$defs/<name>`` reference,
    which is resolved by name among the version's definitions.
    """
    reference = candidate.get("$ref")
    if isinstance(reference, str) and reference.startswith("#/$defs/"):
        candidate = definitions[reference.removeprefix("#/$defs/")]
    return candidate.get("properties", {}).get(tag, {}).get("const")


def _candidate_leaves(
    error: ValidationError, definitions: Mapping[str, Any]
) -> Iterable[ValidationError]:
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
                if value is not None
                and _branch_tag(candidate, definitions, tag) == value
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
        yield from _candidate_leaves(child, definitions)


def _select(
    errors: Iterable[ValidationError], definitions: Mapping[str, Any]
) -> ValidationError | None:
    """Pick the error to report under the shared path rule.

    The rule, shared with the TypeScript validator: among the diagnostic
    leaves of every violation, report the one with the deepest instance
    path; ties go to the first leaf reported. A discriminated ``oneOf``
    contributes only the candidate its tag selects.
    """
    best: ValidationError | None = None
    for error in errors:
        for leaf in _candidate_leaves(error, definitions):
            if best is None or len(leaf.absolute_path) > len(best.absolute_path):
                best = leaf
    return best


def _kind_problem(value: Mapping[str, Any]) -> SchemaValidationError:
    """Return the problem of a value holding none or several file kinds."""
    present = [kind for kind in FILE_KINDS if kind in value]
    found = ", ".join(repr(kind) for kind in present) if present else "none"
    return SchemaValidationError(
        (),
        f"exactly one of 'timeline', 'group' or 'bundle' is required; found {found}",
    )


def validate(value: Mapping[str, Any]) -> None:
    """Check ``value`` against the schema of the version and kind it declares.

    A value whose ``meta.schema_version`` is one of ``SUPPORTED_VERSIONS`` is
    checked against that version's schema; from 0.7.0 on, against the
    document of its kind (:func:`file_kind`), and a value holding none or
    several of ``timeline``, ``group`` and ``bundle`` is rejected at the root.
    Any other value is refused for its declaration alone: its ``meta`` is
    checked against the latest version's, which rejects it at
    ``meta.schema_version``, or at the root when it has no ``meta``.

    A value the schema accepts is then checked for the identity rules the
    schema cannot express (:func:`identity_problems`).

    Raises:
        SchemaValidationError: On the first violation found, with the path to
            the offending value.
    """
    version = declared_version(value)
    if version not in SUPPORTED_VERSIONS:
        validator = _declaration_validator()
        target = SCHEMA_VERSION
    elif schema_documents(version) == ("timeline",):
        validator, target = _validator(version, "timeline"), version
    elif (kind := file_kind(value)) is not None:
        validator, target = _validator(version, kind), version
    else:
        raise _kind_problem(value)
    error = _select(validator.iter_errors(value), _definitions(target))
    if error is not None:
        raise SchemaValidationError(tuple(error.absolute_path), error.message)
    problems = identity_problems(value)
    if problems:
        raise problems[0]


def _element_ids(
    timeline: Mapping[str, Any], path: tuple[str | int, ...]
) -> Iterable[tuple[str, tuple[str | int, ...]]]:
    """Yield every id of a timeline tree with its path, in identity order.

    A timeline contributes its own id, then the ids of its conversion maps,
    regions, breaks, jumps and markers in array order, then its children's
    trees in code-point order of their keys.
    """
    yield timeline["id"], (*path, "id")
    for member in ("conversion_maps", "regions"):
        for index, entry in enumerate(timeline[member]):
            yield entry["id"], (*path, member, index, "id")
    flow = timeline["flow_control"]
    for member in ("breaks", "jumps", "markers"):
        for index, entry in enumerate(flow[member]):
            yield entry["id"], (*path, "flow_control", member, index, "id")
    for key in sorted(timeline["children"]):
        yield from _element_ids(
            timeline["children"][key]["timeline"], (*path, "children", key, "timeline")
        )


def _dangling_targets(
    timeline: Mapping[str, Any], path: tuple[str | int, ...]
) -> Iterable[SchemaValidationError]:
    """Yield a problem for each jump whose target names no marker of its timeline."""
    flow = timeline["flow_control"]
    markers = {marker["id"] for marker in flow["markers"]}
    for index, jump in enumerate(flow["jumps"]):
        if jump["target"] is not None and jump["target"] not in markers:
            yield SchemaValidationError(
                (*path, "flow_control", "jumps", index, "target"),
                f"{jump['target']!r} names no marker of this timeline",
            )
    for key in sorted(timeline["children"]):
        yield from _dangling_targets(
            timeline["children"][key]["timeline"], (*path, "children", key, "timeline")
        )


def _timeline_problems(
    timeline: Mapping[str, Any], path: tuple[str | int, ...]
) -> list[SchemaValidationError]:
    """Return the identity problems of one timeline manifest, its own id scope."""
    problems: list[SchemaValidationError] = []
    first: dict[str, tuple[str | int, ...]] = {}
    for identifier, at in _element_ids(timeline, path):
        if identifier in first:
            problems.append(_duplicate(identifier, at, first[identifier]))
        else:
            first[identifier] = at
    problems.extend(_dangling_targets(timeline, path))
    problems.extend(_segment_problems(timeline, path))
    return problems


def _segment_problems(
    timeline: Mapping[str, Any], path: tuple[str | int, ...]
) -> Iterable[SchemaValidationError]:
    """Yield the problems of every segment line of a timeline tree.

    A timeline with ``is_segment_line`` true holds only its segments, which
    are visited in offset order (ties by key in code-point order): a segment
    of another class than the segment line, at its ``class``; a segment whose
    ``is_segment_line`` differs from the first segment's, at that member; a
    segment that does not start where the one before it ends (the first at
    0), at its ``offset``; then, if the last segment does not end at the
    segment line's length, one problem at the ``length``. Coordinates
    compare by exact value. The tree is visited in identity order.
    """
    if timeline.get("is_segment_line") is True:
        children = timeline["children"]
        keys = sorted(children, key=lambda key: (_exact(children[key]["offset"]), key))
        end = Fraction(0)
        flag = None
        for index, key in enumerate(keys):
            child = children[key]
            segment = child["timeline"]
            at = (*path, "children", key)
            if segment["class"] != timeline["class"]:
                yield SchemaValidationError(
                    (*at, "timeline", "class"),
                    f"segment {key!r} of segment line {timeline['id']!r} is no "
                    f"{timeline['class']}",
                )
            if index == 0:
                flag = segment["is_segment_line"]
            elif segment["is_segment_line"] != flag:
                yield SchemaValidationError(
                    (*at, "timeline", "is_segment_line"),
                    f"segment {key!r} of segment line {timeline['id']!r} differs "
                    f"from segment {keys[0]!r} in is_segment_line",
                )
            if _exact(child["offset"]) != end:
                yield SchemaValidationError(
                    (*at, "offset"),
                    f"segment {key!r} of segment line {timeline['id']!r} does not "
                    + (
                        "start at 0"
                        if index == 0
                        else "start where the one before it ends"
                    ),
                )
            end = _exact(child["offset"]) + _exact(segment["length"])
        if end != _exact(timeline["length"]):
            yield SchemaValidationError(
                (*path, "length"),
                f"the segments of segment line {timeline['id']!r} do not end at "
                "its length",
            )
    for key in sorted(timeline["children"]):
        yield from _segment_problems(
            timeline["children"][key]["timeline"], (*path, "children", key, "timeline")
        )


def _duplicate(
    identifier: str, path: tuple[str | int, ...], first: tuple[str | int, ...]
) -> SchemaValidationError:
    return SchemaValidationError(
        path, f"duplicate id {identifier!r}, first at {json_pointer(first)}"
    )


def _timeline_ids(
    timeline: Mapping[str, Any], path: tuple[str | int, ...]
) -> Iterable[tuple[str, tuple[str | int, ...]]]:
    """Yield the id of every timeline of a tree with its path, in identity order."""
    yield timeline["id"], (*path, "id")
    for key in sorted(timeline["children"]):
        yield from _timeline_ids(
            timeline["children"][key]["timeline"], (*path, "children", key, "timeline")
        )


def _file_timelines(
    roots: list[Mapping[str, Any]], problems: list[SchemaValidationError]
) -> dict[str, tuple[str | int, ...]]:
    """Return the first path of every timeline id of a file's roots.

    Each root is its own id scope under the rules of a timeline file. A
    timeline id is moreover unique across the file: each one that repeats a
    timeline id of an earlier root is one problem, located at its later
    occurrence (a repetition within one root is that root's problem).
    """
    first: dict[str, tuple[str | int, ...]] = {}
    for index, root in enumerate(roots):
        problems.extend(_timeline_problems(root, ("timelines", index)))
    for index, root in enumerate(roots):
        seen: dict[str, tuple[str | int, ...]] = {}
        for identifier, path in _timeline_ids(root, ("timelines", index)):
            if identifier in seen:
                continue
            seen[identifier] = path
            if identifier in first:
                problems.append(_duplicate(identifier, path, first[identifier]))
        for identifier, path in seen.items():
            first.setdefault(identifier, path)
    return first


def _order_problems(
    group: Mapping[str, Any],
    order: list[str],
    path: tuple[str | int, ...],
) -> Iterable[SchemaValidationError]:
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
        for key in sorted(timeline["children"]):
            visit(timeline["children"][key]["timeline"], (timeline["id"], *above))

    for root in roots:
        visit(root, ())
    return found


def _nesting(
    member: str,
    earlier: list[str],
    ancestors: Mapping[str, tuple[str, ...]],
    path: tuple[str | int, ...],
) -> SchemaValidationError | None:
    """Return the problem of a member nested with an earlier member of its group.

    A member inside an earlier member (its descendant) or containing one (its
    ancestor) is one problem at the member; the first such earlier member is
    named.
    """
    for other in earlier:
        if other in ancestors[member]:
            relation = "lies inside"
        elif member in ancestors.get(other, ()):
            relation = "contains"
        else:
            continue
        return SchemaValidationError(
            path, f"member {member!r} {relation} member {other!r} of the same group"
        )
    return None


def _member_problems(
    group: Mapping[str, Any],
    path: tuple[str | int, ...],
    ancestors: Mapping[str, tuple[str, ...]],
    first_member: dict[str, tuple[str | int, ...]] | None,
) -> Iterable[SchemaValidationError]:
    """Yield the problems of a group's members, member by member.

    A member naming no timeline of the file is one problem and is not checked
    further. In a bundle (``first_member`` given) a member named by an earlier
    group is one problem; then, in either file, a member nested with an
    earlier member of the same group is one.
    """
    checked: list[str] = []
    for index, member in enumerate(group["members"]):
        at = (*path, index)
        if member not in ancestors:
            yield SchemaValidationError(
                at, f"{member!r} names no timeline of this file"
            )
            continue
        if first_member is not None:
            if member in first_member:
                earlier = json_pointer(first_member[member])
                yield SchemaValidationError(
                    at, f"duplicate member {member!r}, first at {earlier}"
                )
            else:
                first_member[member] = at
        problem = _nesting(member, checked, ancestors, at)
        if problem is not None:
            yield problem
        checked.append(member)


def _group_problems(value: Mapping[str, Any]) -> list[SchemaValidationError]:
    problems: list[SchemaValidationError] = []
    roots = value["timelines"]
    timelines = _file_timelines(roots, problems)
    group = value["group"]
    if group["id"] in timelines:
        problems.append(
            _duplicate(group["id"], ("group", "id"), timelines[group["id"]])
        )
    problems.extend(
        _member_problems(group, ("group", "members"), _ancestors(roots), None)
    )
    members = set(group["members"])
    for index, root in enumerate(roots):
        if members.isdisjoint(identifier for identifier, _ in _timeline_ids(root, ())):
            problems.append(
                SchemaValidationError(
                    ("timelines", index),
                    f"timeline {root['id']!r} contains no member of the group",
                )
            )
    order = value.get("graphical", {}).get("order")
    if order is not None:
        problems.extend(_order_problems(group, order, ("graphical", "order")))
    return problems


def _bundle_problems(value: Mapping[str, Any]) -> list[SchemaValidationError]:
    problems: list[SchemaValidationError] = []
    timelines = _file_timelines(value["timelines"], problems)
    groups = value["bundle"]["groups"]
    first_group: dict[str, int] = {}
    for index, group in enumerate(groups):
        path = ("bundle", "groups", index, "id")
        identifier = group["id"]
        if identifier in timelines:
            problems.append(_duplicate(identifier, path, timelines[identifier]))
        elif identifier in first_group:
            earlier = ("bundle", "groups", first_group[identifier], "id")
            problems.append(_duplicate(identifier, path, earlier))
        first_group.setdefault(identifier, index)
    ancestors = _ancestors(value["timelines"])
    first_member: dict[str, tuple[str | int, ...]] = {}
    for group_index, group in enumerate(groups):
        path = ("bundle", "groups", group_index, "members")
        problems.extend(_member_problems(group, path, ancestors, first_member))
    orders = value.get("graphical", {}).get("order", {})
    for key in sorted(orders):
        path = ("graphical", "order", key)
        if key not in first_group:
            problems.append(
                SchemaValidationError(path, f"{key!r} names no group of this bundle")
            )
        else:
            problems.extend(
                _order_problems(groups[first_group[key]], orders[key], path)
            )
    return problems


def identity_problems(value: Mapping[str, Any]) -> list[SchemaValidationError]:
    """Return the violations of the identity rules in a schema-valid file.

    **Timeline file.** Every id of the manifest (timelines, conversion maps,
    regions, breaks, jumps and markers) is unique within it across all kinds:
    each repeated id is one problem, located at its second occurrence in
    identity order (a timeline, then its maps, regions, breaks, jumps and
    markers, then its children by key). A jump's non-null ``target`` names a
    marker of the same timeline; each one that does not is one problem,
    located at the ``target``. A segment line's segments are contiguous from 0
    to its length, of its class, with one ``is_segment_line`` value (see
    ``_segment_problems``). The duplicate problems come first, then the
    targets, then the segment lines.

    **Group and bundle files**, in this order:

    1. each root of ``timelines``, in array order, is its own scope under the
       timeline-file rules, its problems located under ``timelines/<i>``;
    2. a timeline id (of a root or a descendant) repeating a timeline id of an
       earlier root: at the later occurrence, ``duplicate id``;
    3. a group id equal to a timeline id (at the group's ``id``, first at the
       timeline), or, in a bundle, to the id of an earlier group (first at
       that group);
    4. member by member: a member naming no timeline of the file, at the
       member; in a bundle, a member already named by an earlier group, at the
       later member, ``duplicate member``; a member nested with an earlier
       member of the same group (inside it or containing it), at the later
       member;
    5. in a group file, a root containing no member, at the root;
    6. ``graphical.order`` (a group file's array, or each entry of a bundle's
       object in code-point order of its keys): a key naming no group, at the
       key; each entry that is not a member of the group, at the entry; then
       each member missing from the order, at the order.
    """
    kind = file_kind(value)
    if kind == "group":
        return _group_problems(value)
    if kind == "bundle":
        return _bundle_problems(value)
    return _timeline_problems(value["timeline"], ("timeline",))
