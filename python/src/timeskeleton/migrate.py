"""Migrations between schema versions.

A migration is a pure function from a document at one version to the same
document at the next version. ``migrate`` chains them from the declared
version up to ``SCHEMA_VERSION`` and stamps the result. Each migration is
pinned by a fixture pair (the document before and after) in the test suite.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping
from typing import Any

from .validate import (
    SCHEMA_VERSION,
    SUPPORTED_VERSIONS,
    UnsupportedVersionError,
    declared_version,
)

Migration = Callable[[dict[str, Any]], dict[str, Any]]

MIGRATIONS: dict[str, tuple[str, Migration]] = {}
"""Source version to ``(target version, migration)``.

Empty while 0.1.0 is the only published version.
"""


def migrate(document: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deep copy of ``document`` brought to ``SCHEMA_VERSION``.

    A document already at the latest version is copied unchanged. The result
    is not validated; call :func:`~timeskeleton.validate` on it when the
    input is untrusted.

    Raises:
        UnsupportedVersionError: If ``meta.schema_version`` is missing, not a
            string, or not one of ``SUPPORTED_VERSIONS``.
    """
    version = declared_version(document)
    if version is None or version not in SUPPORTED_VERSIONS:
        raise UnsupportedVersionError(version)
    result = copy.deepcopy(dict(document))
    while version != SCHEMA_VERSION:
        version, step = MIGRATIONS[version]
        result = step(result)
        result["meta"]["schema_version"] = version
    return result
