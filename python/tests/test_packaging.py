from __future__ import annotations

import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SPECIFICATION = (REPOSITORY_ROOT / "docs" / "drawing.md").read_bytes()
LICENCE = (REPOSITORY_ROOT / "LICENSE").read_bytes()
DOCUMENTS = {
    f"schema/0.7.0/{name}.schema.json": (
        REPOSITORY_ROOT / "schema" / "0.7.0" / f"{name}.schema.json"
    ).read_bytes()
    for name in ("core", "timeline", "group", "bundle")
}


@pytest.mark.parametrize(
    "arguments",
    [["--sdist", "--wheel"], []],
    ids=["wheel from the checkout", "wheel from the sdist"],
)
def test_the_distributions_ship_the_specification_schemas_and_licence(
    arguments: list[str], tmp_path: Path
) -> None:
    uv = shutil.which("uv")
    assert uv is not None, "building the distributions needs uv"
    subprocess.run(
        [uv, "build", *arguments, "--out-dir", str(tmp_path)],
        cwd=REPOSITORY_ROOT / "python",
        check=True,
        capture_output=True,
    )
    (wheel,) = tmp_path.glob("timeskeleton-*.whl")
    with zipfile.ZipFile(wheel) as archive:
        assert archive.read("timeskeleton/docs/drawing.md") == SPECIFICATION
        for path, document in DOCUMENTS.items():
            assert archive.read(f"timeskeleton/{path}") == document
        name, version = wheel.name.split("-")[:2]
        assert archive.read(f"{name}-{version}.dist-info/licenses/LICENSE") == LICENCE
    (sdist,) = tmp_path.glob("timeskeleton-*.tar.gz")
    with tarfile.open(sdist) as archive:
        member = archive.extractfile(
            f"{sdist.name.removesuffix('.tar.gz')}/src/timeskeleton/docs/drawing.md"
        )
        assert member is not None
        assert member.read() == SPECIFICATION
        root = sdist.name.removesuffix(".tar.gz")
        for path, document in DOCUMENTS.items():
            shipped = archive.extractfile(f"{root}/src/timeskeleton/{path}")
            assert shipped is not None
            assert shipped.read() == document
        licence = archive.extractfile(f"{sdist.name.removesuffix('.tar.gz')}/LICENSE")
        assert licence is not None
        assert licence.read() == LICENCE
