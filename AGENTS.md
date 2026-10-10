# Contributor Rules

These rules apply to every contributor, human or automated.

## Repository layout

- `schema/`: versioned JSON Schema files, the document's and (from 0.3.0) the geometry's; the format contract and source of truth.
- `docs/`: `geometry.md`, the specification of the layout and the SVG and TikZ writers; part of the contract, versioned with the schema.
- `fixtures/`: golden JSON documents emitted by timetoalign, their golden geometry and figures, plus hand-authored rejection cases and migration pairs; see `fixtures/README.md`.
- `python/`: the PyPI package, tests, lockfile, and build configuration.
- `js/`: the npm package, generated TypeScript types, tests, and lockfile.
- `scripts/`: fixture emission and cross-repository version checks.
- `decisions/`: numbered MADR decision records.
- `.github/workflows/`: continuous integration and dual-package release automation.

## Rules

- Work schema-first: change the versioned schema, then both packages, then fixtures.
- Add a numbered MADR in `decisions/` before adding a dependency. It must compare the option with writing it ourselves, record long-term maintenance cost, name the audited version, and include a review date.
- Do not add speculative options or dependencies.
- Package manifests declare compatible dependency ranges for published consumers. Lockfiles pin the exact audited versions, and a dependency may enter only after its selected release has been available for at least 14 days.
- Write tests README-first: update the relevant `tests/README.md` with what proves the behavior, then implement tests with exact expected values.
- Emit the golden documents under `fixtures/<version>/` only through `scripts/emit_fixtures.py`; never hand-edit them. The script refuses to overwrite the fixtures of a version whose `v<version>` tag exists, because a released version's fixtures are frozen, its golden geometry and figures included.
- Under `fixtures/<version>/geometry/`, the geometries listed as hand-derived in its `README.md` are authored by hand from `docs/geometry.md`, with their arithmetic in that README; every other geometry and every figure is written by the TimeLineEditor's `app/packages/writers/scripts/emit-geometry.ts`, which refuses to run unless its layout reproduces the hand-derived ones, and once the tag `v<version>` exists. Never hand-edit an emitted geometry or figure. This repository never depends on the TimeLineEditor.
- Change `docs/geometry.md`, the geometry schema and the golden geometry together: a rule a reader could not reproduce from the specification alone is a defect of the specification.
- Write every golden document and geometry, rejection case and migration `after.json` with the standard writer `dumps` of either package (canonical order, two-space indentation, final newline, floats spelled as Python's `repr`). In JavaScript, read documents with `parse` or `parseJson` and never with `JSON.parse`, and write them with `dumps` or `compactJson` and never with `JSON.stringify`: both lose the difference between `2.0` and `2`, integers beyond 2^53 and the order of array-index keys.
- Author rejection cases (`fixtures/rejections/`) and migration pairs (`fixtures/migrations/`) by hand, one rule or migration step per case; the script does not emit them.
- Regenerate `js/src/generated/` after changing a schema. Those TypeScript types are generated here, not downstream.
- Keep every published schema version validatable. Add pure ordered migrations in both packages and pin each with a before-and-after fixture pair.

## Commands

Run these commands from the stated directory.

| Directory | Command | Purpose |
| --- | --- | --- |
| repository root | `python3 scripts/check_versions.py` | Check version declarations agree. |
| repository root | `python scripts/emit_fixtures.py --timetoalign-commit "$(git -C /path/to/timetoalign rev-parse --short HEAD)"` | Emit and round-trip fixtures with an environment containing timetoalign. |
| `python/` | `uv sync` | Synchronize Python dependencies. |
| `python/` | `uv run ruff check .` | Run Python lint checks. |
| `python/` | `uv run ruff format --check .` | Check Python formatting. |
| `python/` | `uv run pytest -q` | Run Python tests. |
| `python/` | `uv build` | Build Python distributions. |
| `js/` | `pnpm install --frozen-lockfile` | Install locked JavaScript dependencies. |
| `js/` | `pnpm lint` | Run JavaScript lint checks. |
| `js/` | `pnpm typecheck` | Check TypeScript types. |
| `js/` | `pnpm test` | Run JavaScript tests. |
| `js/` | `pnpm generate` | Regenerate schema-derived TypeScript files. |
| `js/` | `pnpm build` | Copy assets and build the npm package. |
