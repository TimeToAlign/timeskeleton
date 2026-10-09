# 0004. Package Python with uv, hatchling, and Ruff

Date: 2026-10-09

## Context

The Python distribution must bundle root-level schema assets and maintain the
same compact style as timetoalign.

## Considered options

- uv, hatchling, and Ruff.
- pip tooling and setuptools.
- Poetry.
- Black plus isort plus flake8.
- Write packaging hooks and linting rules ourselves.

## Decision

Use uv for locked environments, hatchling for builds, and Ruff at line length
88. The TimeToAlign maintainers have one formatter/linter command, reducing
bus-factor risk. Primary sources: https://docs.astral.sh/uv/, https://pypi.org/project/hatchling/,
https://github.com/astral-sh/ruff/blob/main/LICENSE, and https://github.com/pypa/hatch/blob/hatch-v1.16.5/LICENSE.txt.

## Consequences

These MIT-licensed tools are development/build dependencies rather than wheel
runtime dependencies. They keep the package small and suit the release
cadence. Changing builders requires testing sdists and wheels; writing the
equivalent ourselves would enlarge maintenance and compatibility costs.

## Review date

2027-10-09.
