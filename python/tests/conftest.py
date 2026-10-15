from __future__ import annotations

from typing import Any


def timeline(
    identifier: str, unit: str = "quarters", length: Any = (8, 1), **members: Any
) -> dict:
    """A timeline of the minimal form; a tuple length or offset is written as a pair."""
    pairs = {"length": length, **members}
    for key in ("length", "offset"):
        if isinstance(pairs.get(key), tuple):
            pairs[key] = list(pairs[key])
    return {"id": identifier, "unit": unit, **pairs}


def manifest(*timelines: dict, **members: Any) -> dict:
    """A manifest of the given roots in the minimal form."""
    return {"timeskeleton": "0.7.0", "timelines": list(timelines), **members}


def group(identifier: str, *members: str, **rest: Any) -> dict:
    return {"id": identifier, "members": list(members), **rest}


def bundle() -> dict:
    """A named manifest: two groups, two ungrouped roots, a child as a member."""
    return manifest(
        timeline("annotations"),
        timeline("page", "pixels", 1200),
        timeline("performance", "seconds", 61.5),
        timeline(
            "recording",
            "seconds",
            120.0,
            children=[timeline("excerpt", "seconds", 30.0, offset=2.0)],
        ),
        timeline("score"),
        id="op35",
        name="Mixed",
        groups=[
            group("group_1", "performance", "score"),
            group("group_2", "excerpt", "page"),
        ],
        graphical={
            "order": {
                "group_1": ["score", "performance"],
                "group_2": ["page", "excerpt"],
            }
        },
    )
