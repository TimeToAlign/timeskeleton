# Contributor Rules

These rules apply to every contributor, human or automated.

## Repository layout

- `schema/`: the JSON Schema of every version; it is the format contract
  and source of truth. Versions 0.5.0 and 0.6.0 have one document each,
  `timeskeleton-<version>.schema.json`, for the one file kind they know, the
  timeline file `{meta, timeline, graphical?}`. From 0.7.0 on a version is a
  directory `<version>/` of four documents, `core`, `timeline`, `group` and
  `bundle` (`<name>.schema.json`), for the timeline file, the group file
  `{meta, timelines, group, graphical?}` and the bundle file `{meta,
  timelines, bundle, graphical?}`; `core` holds the definitions they share,
  and the documents refer to each other by relative `$ref`.
- `docs/`: `drawing.md`, the specification of the style cascade, layout,
  the box of groups, frames and cards, and SVG and TikZ writers; it is part
  of the contract, and both packages ship it.
- `fixtures/`: generated files under `fixtures/<version>/` (timeline files
  directly in it, group files in `groups/`, bundle files in `bundles/`),
  hand-authored rejection cases under `fixtures/rejections/<version>/`,
  hand-authored migration pairs under `fixtures/migrations/`, and the
  drawings (`inputs.json`, `figure.svg` and `figure.tex` per drawing;
  twelve `figure.svg` of 0.7.0 derived by hand, seven of 0.5.0 and of 0.6.0,
  everything else emitted; each version's `drawings/README.md` gives the
  arithmetic of its hand-derived figures); see `fixtures/README.md`.
- `fonts/`: DejaVu Sans 2.37, its licence, and the advance-width metrics used
  by the drawing.
- `python/`: the PyPI package, tests, lockfile, and build configuration.
- `js/`: the npm package, generated TypeScript types, tests, and lockfile.
- `scripts/`: fixture emission, font-metrics extraction, and
  cross-repository version checks.
- `decisions/`: numbered MADR decision records.
- `.github/workflows/`: continuous integration and dual-package release
  automation.

## Rules

- Work schema-first: change the versioned schema, then both packages, then
  fixtures.
- Add a numbered MADR in `decisions/` before adding a dependency. It must
  compare the dependency with writing the component here, record long-term
  maintenance cost, name the audited version, and include a review date.
- Do not add speculative options or dependencies.
- Package manifests declare compatible dependency ranges for published
  consumers. Lockfiles pin exact audited versions. A dependency may enter only
  after its selected release has been available for at least 14 days.
- Write tests README-first: update the relevant `tests/README.md` with what
  proves the behavior, then implement tests with exact expected values.
- Emit the timeline, group and bundle fixtures under `fixtures/<version>/`
  only through `scripts/emit_fixtures.py`; never hand-edit them. The script refuses to
  overwrite the fixtures of a version whose `v<version>` tag exists. Emit
  the drawings under `fixtures/<version>/drawings/` only through
  TimeLineEditor's `emit-drawings` script, which never rewrites the twelve
  hand-derived figures but compares them with its own output.
- `docs/drawing.md` pins the drawing. There is no drawing schema, and a drawing's JSON form is internal to
  an implementation. A rule a reader could not reproduce from the
  specification alone is a defect of the specification. This repository never
  depends on TimeLineEditor in code or packages; only the emitted drawing
  figures are produced by TimeLineEditor's writers (its `emit-drawings`
  script, writing into a timeskeleton checkout).
- Write every fixture and rejection case with the standard writer
  `dumps` of either package: object keys sorted by code point at every depth,
  arrays in canonical order, two-space indentation, final newline, and floats
  spelled as Python's `repr`. Never keep a fixed list of key orders; key order
  is sorted order, and `canonical_order` covers only the order of array
  elements. In JavaScript, read
  files with `parse` or `parseJson`, never `JSON.parse`, and write
  them with `dumps` or `compactJson`, never `JSON.stringify`; the native
  methods lose the distinction between `2.0` and `2`, integers beyond 2^53,
  and the order of array-index keys.
- Author rejection cases under `fixtures/rejections/` by hand, one rule per
  case, and migration pairs under `fixtures/migrations/` by hand; the fixture
  script emits neither.
- Regenerate `js/src/generated/` after changing the schema or font metrics.
  The generated TypeScript files belong in this repository.
- Regenerate `fonts/dejavu-sans-2.37.metrics.json` with
  `scripts/extract_font_metrics.py`; do not calculate or edit its advances by
  hand.
- Keep every schema version from 0.5.0 onward validatable. Each later version
  adds pure, ordered migrations in both packages, with every step pinned by a
  before-and-after fixture pair.

## Commands

Run these commands from the stated directory.

| Directory | Command | Purpose |
| --- | --- | --- |
| repository root | `python3 scripts/check_versions.py` | Check version declarations agree. |
| repository root | `python scripts/emit_fixtures.py --timetoalign-commit "$(git -C /path/to/timetoalign rev-parse --short HEAD)"` | Emit and round-trip the timeline, group and bundle fixtures with an environment containing timetoalign; `--kinds` limits the run to the kinds it names. |
| `python/` | `uv sync` | Synchronize Python dependencies. |
| `python/` | `uv run ruff check .` | Run Python lint checks. |
| `python/` | `uv run ruff format --check .` | Check Python formatting. |
| `python/` | `uv run pytest -q` | Run Python tests. |
| `python/` | `uv run python ../scripts/extract_font_metrics.py` | Regenerate the bundled font metrics. |
| `python/` | `uv build` | Build Python distributions. |
| `js/` | `pnpm install --frozen-lockfile` | Install locked JavaScript dependencies. |
| `js/` | `pnpm lint` | Run JavaScript lint checks. |
| `js/` | `pnpm typecheck` | Check TypeScript types. |
| `js/` | `pnpm test` | Run JavaScript tests. |
| `js/` | `pnpm generate` | Regenerate schema- and font-derived TypeScript files. |
| `js/` | `pnpm build` | Copy assets and build the npm package. |
