from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from timeskeleton import dumps, font_metrics, font_path

RELEASE_SHA256 = "7da195a74c55bef988d0d48f9508bd5d849425c1770dba5d7bfc6ce9ed848954"
SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "extract_font_metrics.py"


def _metrics_path() -> Path:
    return font_path().parent / "dejavu-sans-2.37.metrics.json"


def test_the_font_is_the_release_file_with_its_licence() -> None:
    assert font_path().name == "DejaVuSans.ttf"
    assert hashlib.sha256(font_path().read_bytes()).hexdigest() == RELEASE_SHA256
    assert (font_path().parent / "LICENSE").is_file()


def test_the_metrics_hold_the_stated_values() -> None:
    metrics = font_metrics()
    assert list(metrics) == [
        "advances",
        "ascender",
        "descender",
        "fallback",
        "units_per_em",
    ]
    assert metrics["units_per_em"] == 2048
    assert metrics["ascender"] == 1901
    assert metrics["descender"] == 483
    assert metrics["fallback"] == 1229
    advances = metrics["advances"]
    assert len(advances) == 5918
    assert list(advances) == sorted(advances)
    assert advances["9833"] == 966
    assert advances["48"] == 1303
    assert advances["32"] == 651


def test_the_metrics_file_is_written_by_dumps() -> None:
    text = _metrics_path().read_text(encoding="utf-8")
    assert dumps(json.loads(text)) == text


def test_font_accessors_work_from_any_working_directory(tmp_path, monkeypatch) -> None:
    expected_path = font_path()
    monkeypatch.chdir(tmp_path)
    assert font_path() == expected_path
    assert font_path().is_file()
    assert font_metrics()["units_per_em"] == 2048


def _script():
    pytest.importorskip("fontTools")
    spec = importlib.util.spec_from_file_location("extract_font_metrics", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_the_extraction_reproduces_the_metrics_file() -> None:
    script = _script()
    assert dumps(script.metrics(font_path())) == _metrics_path().read_text(
        encoding="utf-8"
    )


def test_the_extraction_refuses_another_file(tmp_path) -> None:
    script = _script()
    altered = tmp_path / "DejaVuSans.ttf"
    altered.write_bytes(font_path().read_bytes() + b"\0")
    digest = hashlib.sha256(altered.read_bytes()).hexdigest()
    with pytest.raises(SystemExit) as caught:
        script.metrics(altered)
    assert (
        str(caught.value) == f"{altered}: SHA-256 {digest}, expected {RELEASE_SHA256}"
    )
