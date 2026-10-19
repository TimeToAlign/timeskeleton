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


def _respellable(canonical: bool) -> dict:
    def number(written: Any, spelled: Any) -> Any:
        return spelled if canonical else written

    return manifest(
        timeline(
            "midi",
            "ticks",
            number(480.0, 480),
            children=[timeline("b", "ticks", 120, offset=number(240.0, 240))],
        ),
        timeline(
            "score",
            length=[32, number(1.0, 1)],
            children=[timeline("a", length=[4, 1], offset=[number(8.0, 8), 1])],
            conversion_maps=[
                {
                    "type": "ChainMap",
                    "id": "chain",
                    "source_unit": "quarters",
                    "target_unit": "seconds",
                    "maps": [
                        {
                            "type": "TableMap",
                            "id": "table",
                            "source_unit": "quarters",
                            "target_unit": "seconds",
                            "x_values": [[0, 1], [number(1.0, 1), 2]],
                            "y_values": [0.0, 0.5],
                            "kind": "linear",
                            "extrapolate": "none",
                        }
                    ],
                },
                {
                    "type": "LinearMap",
                    "id": "linear",
                    "source_unit": "quarters",
                    "target_unit": "seconds",
                    "scalar": 1.0,
                    "offset": [0, number(1.0, 1)],
                },
            ],
            regions=[
                {"id": "r", "start": [0, number(1.0, 1)], "end": [number(1.0, 1), 2]}
            ],
            flow_control=[
                {
                    "id": "m",
                    "type": "jump_to",
                    "manifestation": "segno",
                    "coordinate": [number(2.0, 2), 1],
                }
            ],
        ),
        timeline(
            "take",
            "seconds",
            number(60, 60.0),
            regions=[{"id": "s", "start": number(0, 0.0), "end": 1.5}],
        ),
        measure_maps=[
            {
                "id": "bars",
                "rows": [
                    {
                        "count": 1,
                        "qstamp": [0, number(1.0, 1)],
                        "actual_length": [number(4.0, 4), 1],
                        "nominal_length": 4.0,
                    }
                ],
            }
        ],
    )


def respellable() -> dict:
    """A manifest in canonical order whose values are spelled unlike their number types.

    A Fraction member is written as an integral float in a length, a child
    offset, a region, a jump target, a nested TableMap's x value, a LinearMap's
    offset and two values of a measure-map row; a ticks length and offset as
    integral floats; a seconds length and region start as integers. The bare
    LinearMap scalar ``1.0``, the TableMap's y values and the row's bare
    ``nominal_length`` ``4.0`` have no declared number type.
    """
    return _respellable(canonical=False)


def respelled() -> dict:
    """``respellable()`` with every value spelled as its number type selects."""
    return _respellable(canonical=True)
