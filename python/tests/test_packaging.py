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


@pytest.mark.parametrize(
    "arguments",
    [["--sdist", "--wheel"], []],
    ids=["wheel from the checkout", "wheel from the sdist"],
)
def test_the_distributions_ship_the_drawing_specification_and_licence(
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
        name, version = wheel.name.split("-")[:2]
        assert archive.read(f"{name}-{version}.dist-info/licenses/LICENSE") == LICENCE
    (sdist,) = tmp_path.glob("timeskeleton-*.tar.gz")
    with tarfile.open(sdist) as archive:
        member = archive.extractfile(
            f"{sdist.name.removesuffix('.tar.gz')}/src/timeskeleton/docs/drawing.md"
        )
        assert member is not None
        assert member.read() == SPECIFICATION
        licence = archive.extractfile(f"{sdist.name.removesuffix('.tar.gz')}/LICENSE")
        assert licence is not None
        assert licence.read() == LICENCE
