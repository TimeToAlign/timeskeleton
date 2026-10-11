# Contributor Rules

These rules apply to every contributor, human or automated.

## Repository layout

- `schema/`: versioned JSON Schema files of the manifest (0.4.0) and of the published envelopes (0.1.0 to 0.3.0), the format contract and source of truth; plus the frozen 0.3.0 geometry schema, which constrains nothing.
- `docs/`: `geometry.md`, the specification of how a manifest is drawn (the layout and the SVG and TikZ writers); part of the contract.
- `fixtures/`: manifest fixtures (0.4.0, one per top-level timeline) and envelope fixtures (0.1.0 to 0.3.0) emitted by timetoalign, the frozen geometry, SVG and TikZ fixtures of the 0.3.0 envelopes, plus hand-authored rejection cases, migration pairs and the `split` case; see `fixtures/README.md`.
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
- Emit the manifest and envelope fixtures under `fixtures/<version>/` only through `scripts/emit_fixtures.py`; never hand-edit them. The script refuses to overwrite the fixtures of a version whose `v<version>` tag exists, because a released version's fixtures are frozen.
- `docs/geometry.md` and the SVG and TikZ fixtures of a version pin the drawing; from 0.4.0 on there is no geometry schema, and the JSON form of geometry is internal to an implementation. A rule a reader could not reproduce from the specification alone is a defect of the specification. This repository never depends on the TimeLineEditor.
- `schema/geometry-0.3.0.schema.json` and `fixtures/0.3.0/geometry/` are a frozen record of the 0.3.0 drawing: never edit them, and never treat them as a constraint on the specification.
- Write every manifest and envelope fixture, rejection case, migration `after.json` and `split` output with the standard writer `dumps` of either package (canonical order, two-space indentation, final newline, floats spelled as Python's `repr`). In JavaScript, read manifests and envelopes with `parse` or `parseJson` and never with `JSON.parse`, and write them with `dumps` or `compactJson` and never with `JSON.stringify`: both lose the difference between `2.0` and `2`, integers beyond 2^53 and the order of array-index keys.
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
