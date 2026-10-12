from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from timeskeleton import SCHEMA_VERSION, fixture_paths


@pytest.fixture
def load_fixture() -> Callable[..., dict[str, Any]]:
    """Return a loader that parses one bundled fixture afresh on every call."""

    def _load(name: str, version: str = SCHEMA_VERSION) -> dict[str, Any]:
        path = next(p for p in fixture_paths(version) if p.name == f"{name}.json")
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    return _load


def _timeline(identifier: str, **children: tuple[int, dict[str, Any]]) -> dict:
    """The 0.7.0 ``bare`` manifest renamed, without a name, with children."""
    path = next(p for p in fixture_paths("0.7.0") if p.name == "bare.json")
    timeline = json.loads(path.read_text(encoding="utf-8"))["timeline"]
    timeline["id"] = identifier
    timeline["name"] = None
    for key, (offset, child) in children.items():
        child["length"]["value"] = [4, 1]
        timeline["children"][key] = {
            "offset": {
                "unit": "quarters",
                "number_type": "fraction",
                "value": [offset, 1],
            },
            "timeline": child,
        }
    return timeline


def group_value() -> dict[str, Any]:
    """The group document of the test README: a child and a root as members."""
    return {
        "meta": {"schema_version": "0.7.0"},
        "timelines": [
            _timeline("piece", **{"second-half": (4, _timeline("second-half"))}),
            _timeline("recording"),
        ],
        "group": {
            "id": "group_1",
            "name": "Second half",
            "meta": {},
            "members": ["recording", "second-half"],
        },
        "graphical": {"order": ["second-half", "recording"]},
    }


def bundle_value() -> dict[str, Any]:
    """The bundle document of the test README: two groups, two ungrouped roots."""

    def group(identifier: str, name: str, members: list[str]) -> dict[str, Any]:
        return {"id": identifier, "name": name, "meta": {}, "members": members}

    return {
        "meta": {"schema_version": "0.7.0"},
        "timelines": [
            _timeline("annotations"),
            _timeline("page"),
            _timeline("performance"),
            _timeline("recording", excerpt=(2, _timeline("excerpt"))),
            _timeline("score"),
        ],
        "bundle": {
            "id": "bundle_1",
            "name": "Mixed",
            "meta": {},
            "support_policy": "omit",
            "groups": [
                group("group_1", "Performance", ["performance", "score"]),
                group("group_2", "Facsimile", ["excerpt", "page"]),
            ],
        },
        "graphical": {
            "order": {
                "group_1": ["score", "performance"],
                "group_2": ["page", "excerpt"],
            }
        },
    }


@pytest.fixture
def group_document() -> dict[str, Any]:
    """The group document of the test README, built afresh."""
    return group_value()


@pytest.fixture
def bundle_document() -> dict[str, Any]:
    """The bundle document of the test README, built afresh."""
    return bundle_value()
