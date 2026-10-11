from __future__ import annotations

import copy
import warnings

from timeskeleton import MissingStyleWarning, complete_styles


def test_missing_styles_are_completed_once_in_code_point_order() -> None:
    graphical = {
        "statements": [
            {"select": {}, "set": "😀"},
            {"select": {}, "set": "ﬀ"},
            {"select": {}, "set": "😀"},
            {"select": {}, "set": {"opacity": 0.5}},
        ]
    }
    original = copy.deepcopy(graphical)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        completed, missing = complete_styles(graphical)

    assert missing == ["ﬀ", "😀"]
    assert completed == {
        "statements": original["statements"],
        "styles": {"ﬀ": {}, "😀": {}},
    }
    assert graphical == original
    assert completed is not graphical
    assert len(caught) == 1
    assert caught[0].category is MissingStyleWarning
    assert str(caught[0].message) == "Missing graphical styles: 'ﬀ', '😀'"


def test_existing_styles_are_preserved_without_a_warning() -> None:
    graphical = {
        "styles": {"kept": {"fill": "#ABCDEF"}},
        "statements": [{"select": {}, "set": "kept"}],
    }

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        completed, missing = complete_styles(graphical)

    assert completed == graphical
    assert completed is not graphical
    assert completed["styles"] is not graphical["styles"]
    assert missing == []
    assert caught == []


def test_missing_styles_are_added_beside_existing_ones() -> None:
    graphical = {
        "styles": {"kept": {"fill": "#000000"}},
        "statements": [
            {"select": {}, "set": "kept"},
            {"select": {}, "set": "absent"},
        ],
    }

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        completed, missing = complete_styles(graphical)

    assert completed["styles"] == {"kept": {"fill": "#000000"}, "absent": {}}
    assert missing == ["absent"]
    assert graphical["styles"] == {"kept": {"fill": "#000000"}}
    assert len(caught) == 1
    assert str(caught[0].message) == "Missing graphical styles: 'absent'"
