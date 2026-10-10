from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from timeskeleton import SCHEMA_VERSION, fixture_paths

FIXTURE_NAMES = [
    "continuous_graphical",
    "continuous_logical",
    "continuous_physical",
    "discrete_graphical",
    "discrete_logical",
    "discrete_physical",
    "empty",
    "nested",
    "with_region",
]


@pytest.fixture
def load_fixture() -> Callable[[str, str], dict[str, Any]]:
    """Return a loader that parses one bundled fixture afresh on every call."""

    def _load(name: str, version: str = SCHEMA_VERSION) -> dict[str, Any]:
        path = next(p for p in fixture_paths(version) if p.name == f"{name}.json")
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    return _load
