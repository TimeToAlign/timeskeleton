from __future__ import annotations

import json

import pytest

from timeskeleton import (
    FILE_KINDS,
    SUPPORTED_VERSIONS,
    SchemaValidationError,
    declared_version,
    dumps,
    fixture_paths,
    identity_problems,
    json_pointer,
    rejection_paths,
    validate,
)


@pytest.mark.parametrize("version", SUPPORTED_VERSIONS)
def test_every_fixture_validates(version: str) -> None:
    paths = fixture_paths(version)
    assert paths
    for kind in FILE_KINDS:
        for path in fixture_paths(version, kind):
            validate(json.loads(path.read_text(encoding="utf-8")))


@pytest.mark.parametrize(
    "path",
    [path for version in SUPPORTED_VERSIONS for path in rejection_paths(version)],
    ids=lambda path: f"{path.parent.name}/{path.stem}",
)
def test_shared_rejection_is_rejected_at_its_path(path) -> None:
    case = json.loads(path.read_text(encoding="utf-8"))
    with pytest.raises(SchemaValidationError) as caught:
        validate(case["manifest"])
    assert caught.value.path == tuple(case["path"])


def test_the_rejection_cases_number_fifty_five_and_ninety_seven() -> None:
    counts = [len(rejection_paths(version)) for version in SUPPORTED_VERSIONS]
    assert counts == [55, 55, 100]


@pytest.mark.parametrize("version", SUPPORTED_VERSIONS)
def test_every_rejection_declares_its_version_except_two(version: str) -> None:
    exempt = {"meta_schema_version_unknown", "root_missing_meta"}
    declared = {
        path.stem: declared_version(
            json.loads(path.read_text(encoding="utf-8"))["manifest"]
        )
        for path in rejection_paths(version)
    }
    assert declared.pop("meta_schema_version_unknown") == "9.9.9"
    assert declared.pop("root_missing_meta") is None
    assert len(declared) == len(rejection_paths(version)) - 2
    assert set(declared.values()) == {version}
    assert exempt.isdisjoint(declared)


def test_error_renders_as_json_pointer() -> None:
    case = json.loads(rejection_paths()[0].read_text(encoding="utf-8"))
    with pytest.raises(SchemaValidationError) as caught:
        validate(case["manifest"])
    assert str(caught.value).startswith(f"{json_pointer(caught.value.path)}: ")


def test_json_pointer_rendering() -> None:
    assert json_pointer(()) == "#"
    assert json_pointer(("a/b", "c~d", 0)) == "#/a~1b/c~0d/0"


@pytest.mark.parametrize("value", [9007199254740993, 9223372036854775807])
def test_integer_boundaries_validate_and_preserve(value: int, load_fixture) -> None:
    manifest = load_fixture("discrete_logical")
    manifest["timeline"]["length"]["value"] = value
    validate(manifest)
    assert json.loads(dumps(manifest))["timeline"]["length"]["value"] == value


@pytest.mark.parametrize(
    "declaration",
    [
        {
            "stroke-width": 0,
            "stroke-dasharray": "none",
            "opacity": 0,
            "font-size": 0.1,
            "rx": 0,
            "content": "row\tname",
            "max-width": "none",
        },
        {
            "stroke-dasharray": "0 1.5 2",
            "opacity": 1,
            "max-width": 1,
        },
    ],
)
def test_graphical_property_bounds_accept_exact_valid_values(
    declaration, load_fixture
) -> None:
    manifest = load_fixture("bare")
    manifest["graphical"] = {"styles": {"valid": declaration}}
    validate(manifest)


@pytest.mark.parametrize(
    ("property_name", "value"),
    [
        ("stroke-width", -0.1),
        ("stroke-dasharray", "3,3"),
        ("opacity", -0.1),
        ("opacity", 1.1),
        ("font-size", 0),
        ("rx", -0.1),
        ("content", 5),
        ("max-width", 0),
    ],
)
def test_graphical_property_bounds_reject_at_the_property(
    property_name, value, load_fixture
) -> None:
    manifest = load_fixture("bare")
    manifest["graphical"] = {"styles": {"invalid": {property_name: value}}}
    with pytest.raises(SchemaValidationError) as caught:
        validate(manifest)
    assert caught.value.path == ("graphical", "styles", "invalid", property_name)


def test_names_remain_unrestricted(load_fixture) -> None:
    manifest = load_fixture("bare")
    manifest["timeline"]["name"] = "name\x00with\tcontrols"
    validate(manifest)


@pytest.mark.parametrize("version", ["0.3.0", "0.1.0", "0.4.0", "1.0.0"])
def test_any_other_declared_version_is_rejected_at_its_declaration(
    version: str, load_fixture
) -> None:
    manifest = load_fixture("bare")
    manifest["meta"]["schema_version"] = version
    with pytest.raises(SchemaValidationError) as caught:
        validate(manifest)
    assert caught.value.path == ("meta", "schema_version")


def _coordinate(value: int) -> dict:
    return {"unit": "quarters", "number_type": "fraction", "value": [value, 1]}


def _marker(marker_id: str) -> dict:
    return {"id": marker_id, "name": None, "coordinate": _coordinate(1)}


def _jump(jump_id: str, target: str | None) -> dict:
    return {
        "id": jump_id,
        "from_coordinate": _coordinate(4),
        "to_coordinate": _coordinate(0),
        "control_type": "repeat_end",
        "condition": "always",
        "repeat_count": 1,
        "target": target,
        "label": None,
        "meta": {},
    }


def _with_child(manifest: dict, child_id: str) -> dict:
    """Add a copy of the root, without its children, as child ``child_id``."""
    child = json.loads(json.dumps(manifest["timeline"]))
    child["id"] = child_id
    child["children"] = {}
    manifest["timeline"]["children"][child_id] = {
        "offset": _coordinate(0),
        "timeline": child,
    }
    return child


def test_every_fixture_has_no_identity_problem() -> None:
    for path in fixture_paths():
        assert identity_problems(json.loads(path.read_text(encoding="utf-8"))) == []


def test_each_repeated_id_is_one_problem_at_its_later_occurrence(load_fixture) -> None:
    manifest = load_fixture("bare")
    child = _with_child(manifest, "c")
    flow = manifest["timeline"]["flow_control"]
    flow["markers"] = [_marker("m"), _marker("m"), _marker("bare")]
    child["flow_control"]["markers"] = [_marker("m")]
    problems = identity_problems(manifest)
    assert [problem.path for problem in problems] == [
        ("timeline", "flow_control", "markers", 1, "id"),
        ("timeline", "flow_control", "markers", 2, "id"),
        ("timeline", "children", "c", "timeline", "flow_control", "markers", 0, "id"),
    ]
    assert [problem.message for problem in problems] == [
        "duplicate id 'm', first at #/timeline/flow_control/markers/0/id",
        "duplicate id 'bare', first at #/timeline/id",
        "duplicate id 'm', first at #/timeline/flow_control/markers/0/id",
    ]
    with pytest.raises(SchemaValidationError) as caught:
        validate(manifest)
    assert caught.value.path == ("timeline", "flow_control", "markers", 1, "id")


def test_children_are_visited_in_code_point_order_of_their_keys(load_fixture) -> None:
    manifest = load_fixture("bare")
    for key in ["\U0001f600", "\ufb00"]:
        child = _with_child(manifest, key)
        child["flow_control"]["markers"] = [_marker("shared")]
    (problem,) = identity_problems(manifest)
    assert problem.path == (
        "timeline",
        "children",
        "\U0001f600",
        "timeline",
        "flow_control",
        "markers",
        0,
        "id",
    )


def test_a_jump_targets_a_marker_of_its_own_timeline(load_fixture) -> None:
    manifest = load_fixture("bare")
    child = _with_child(manifest, "c")
    flow = manifest["timeline"]["flow_control"]
    flow["markers"] = [_marker("here")]
    flow["jumps"] = [_jump("j1", "here"), _jump("j2", None), _jump("j3", "there")]
    child["flow_control"]["markers"] = [_marker("there")]
    child["flow_control"]["jumps"] = [_jump("j4", "here")]
    problems = identity_problems(manifest)
    assert [(problem.path, problem.message) for problem in problems] == [
        (
            ("timeline", "flow_control", "jumps", 2, "target"),
            "'there' names no marker of this timeline",
        ),
        (
            (
                "timeline",
                "children",
                "c",
                "timeline",
                "flow_control",
                "jumps",
                0,
                "target",
            ),
            "'here' names no marker of this timeline",
        ),
    ]


def test_duplicates_come_before_dangling_targets(load_fixture) -> None:
    manifest = load_fixture("bare")
    flow = manifest["timeline"]["flow_control"]
    flow["jumps"] = [_jump("j", "nowhere")]
    flow["markers"] = [_marker("j")]
    assert [problem.path for problem in identity_problems(manifest)] == [
        ("timeline", "flow_control", "markers", 0, "id"),
        ("timeline", "flow_control", "jumps", 0, "target"),
    ]
