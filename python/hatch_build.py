"""Bundle the repository-level files into the package.

The schema, fixture, font and documentation directories and the README live
at the repository root, beside ``python/``, so that one copy serves the Python
package, the npm package and the fixture script. A static ``force-include``
cannot reach them when the wheel is built from the sdist (hatchling raises
``FileNotFoundError`` for a missing source), so two hooks resolve them at build
time:

* ``AssetsHook`` (build hook): in a repository checkout, the root
  ``schema/``, ``fixtures/``, ``fonts/`` and ``docs/`` directories go into the
  sdist under ``src/timeskeleton/`` and into the wheel under ``timeskeleton/``,
  and the root ``README.md`` goes into the sdist. In an unpacked sdist those copies
  are ordinary package files and need no forcing. The root ``LICENSE`` goes
  into the sdist root and into the wheel's ``.dist-info/licenses/``. In an
  unpacked sdist it is the project's own ``LICENSE``, which hatchling's default
  licence-file pattern already puts there.
* ``ReadmeHook`` (metadata hook): fills the dynamic ``readme`` field from the
  root ``README.md`` in a checkout, or from the sdist's copy.

Nothing is ever written into the source tree.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.metadata.plugin.interface import MetadataHookInterface

ASSETS = ("schema", "fixtures", "fonts", "docs")
README = "README.md"
LICENSE = "LICENSE"


def _repository(project: Path) -> Path | None:
    """Return the repository root if ``project`` sits in a checkout, else ``None``."""
    candidate = project.parent
    return candidate if (candidate / ASSETS[0]).is_dir() else None


class AssetsHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        project = Path(self.root)
        package = project / "src" / "timeskeleton"
        repository = _repository(project)
        force_include: dict[str, str] = build_data.setdefault("force_include", {})
        if repository is None:
            missing = [name for name in ASSETS if not (package / name).is_dir()]
            if missing:
                raise FileNotFoundError(
                    f"{', '.join(missing)} missing from both the repository and "
                    f"{package}"
                )
            return
        prefix = "src/timeskeleton" if self.target_name == "sdist" else "timeskeleton"
        for name in ASSETS:
            force_include[str(repository / name)] = f"{prefix}/{name}"
        if self.target_name == "sdist":
            for name in (README, LICENSE):
                if (repository / name).is_file():
                    force_include[str(repository / name)] = name
        elif (repository / LICENSE).is_file():
            dist_info = f"{self.metadata.core.name}-{self.metadata.version}.dist-info"
            force_include[str(repository / LICENSE)] = f"{dist_info}/licenses/{LICENSE}"


class ReadmeHook(MetadataHookInterface):
    PLUGIN_NAME = "custom"

    def update(self, metadata: dict[str, Any]) -> None:
        project = Path(self.root)
        repository = _repository(project)
        candidates = [project / README]
        if repository is not None:
            candidates.insert(0, repository / README)
        for candidate in candidates:
            if candidate.is_file():
                metadata["readme"] = {
                    "content-type": "text/markdown",
                    "text": candidate.read_text(encoding="utf-8"),
                }
                return
