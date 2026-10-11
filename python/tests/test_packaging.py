from __future__ import annotations

import shutil
import subprocess
import tarfile
import zipfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SPECIFICATION = (REPOSITORY_ROOT / "docs" / "drawing.md").read_bytes()


def test_the_distributions_ship_the_drawing_specification(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    assert uv is not None, "building the distributions needs uv"
    subprocess.run(
        [uv, "build", "--sdist", "--wheel", "--out-dir", str(tmp_path)],
        cwd=REPOSITORY_ROOT / "python",
        check=True,
        capture_output=True,
    )
    (wheel,) = tmp_path.glob("timeskeleton-*.whl")
    with zipfile.ZipFile(wheel) as archive:
        assert archive.read("timeskeleton/docs/drawing.md") == SPECIFICATION
    (sdist,) = tmp_path.glob("timeskeleton-*.tar.gz")
    with tarfile.open(sdist) as archive:
        member = archive.extractfile(
            f"{sdist.name.removesuffix('.tar.gz')}/src/timeskeleton/docs/drawing.md"
        )
        assert member is not None
        assert member.read() == SPECIFICATION
