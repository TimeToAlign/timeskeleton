# Contributing

TimeSkeleton is schema-first. The current schema, 0.7.0, is the contract; the Python and
TypeScript packages validate it, and timetoalign emits its fixtures.

## Schema changes

For a format change, add a new version directory `schema/<version>/` holding
the full document set, `core.schema.json`, `timeline.schema.json`,
`group.schema.json` and `bundle.schema.json`, each with the `$id`
`https://timetoalign.github.io/timeskeleton/<version>/<name>.schema.json`
and every reference to another document relative; do not alter a published
schema. Copy the documents a change does not concern, so that one version's
documents are released together. Update the supported-version and
latest-version declarations in both packages. Every schema version from
0.5.0 onward remains validatable, and each later version has a pure, ordered
migration in both packages, pinned by a before-and-after fixture pair. Add
shared rejection fixtures, regenerate `js/src/generated/` with
`pnpm generate`, and re-emit the fixtures through timetoalign.

The timeline files under `fixtures/<version>/`, the group files under its
`groups/` and the bundle files under its `bundles/` are generated artifacts.
Use an environment containing the timetoalign revision represented by the
schema:

```bash
python scripts/emit_fixtures.py --timetoalign-commit "$(git -C /path/to/timetoalign rev-parse --short HEAD)"
```

`--kinds` followed by one or more of `timeline`, `group` and `bundle` emits
those kinds alone and leaves the others as they are. Do not edit a fixture
by hand. The script refuses to write into the fixtures of a version whose
`v<version>` tag exists. Rejection cases under
`fixtures/rejections/` and migration pairs under `fixtures/migrations/` are
authored by hand.

## The drawing specification

`docs/drawing.md` specifies the `graphical` block, arithmetic, default
styles, font, layout, and SVG and TikZ writers. A drawing is derived and has no
schema or exchanged JSON form. The specification pins the drawing. A rule a reader could not reproduce from the
specification alone is a defect of the specification.

The drawing uses `fonts/DejaVuSans.ttf` from DejaVu Sans 2.37.
`fonts/LICENSE` contains its licence, and
`fonts/dejavu-sans-2.37.metrics.json` contains the advance widths used to
measure text. Regenerate the metrics from `python/` with:

```bash
uv run python ../scripts/extract_font_metrics.py
```

Python exposes the font through `font_path()` and `font_metrics()`. The npm
package exports `fontMetrics` and the
`@timetoalign/timeskeleton/fonts/*` subpath.

## Dependencies and decisions

Add a dependency only with a numbered MADR in `decisions/`. The record must
assess writing the component here and its long-term maintenance cost, name the
audited version, and set a review date. Do not add speculative dependencies or
options.

Package manifests declare compatible version ranges because published
packages resolve in consumers' environments. The lockfiles,
`python/uv.lock` and `js/pnpm-lock.yaml`, pin exact versions. An audited
dependency release must have been available for at least 14 days before it is
added.

## Tests

Tests are README-first. Update the relevant `python/tests/README.md` or
`js/tests/README.md` to state the proof required, then write tests with exact
expected values.

Run the complete local checks:

```bash
cd python
uv sync
uv run ruff check .
uv run ruff format --check .
uv run pytest -q
uv build
```

```bash
cd js
pnpm install --frozen-lockfile
pnpm lint
pnpm typecheck
pnpm test
pnpm generate
pnpm build
```

From the repository root:

```bash
python3 scripts/check_versions.py
```

## Known limitations

- The validator tests do not pin the JSON implementation's maximum
  safe-integer boundary in either implementation.
- Python and TypeScript rejection paths are independently compared with
  expected values, but no test compares both implementations' paths for the
  same generated invalid manifests.

## Release

Releases are made by
[release-please](https://github.com/googleapis/release-please) and
`.github/workflows/release.yml`. Write commit messages in the
[Conventional Commits](https://www.conventionalcommits.org/) form;
release-please builds `CHANGELOG.md` from them.

A timeskeleton version is a schema version, so release-please does not compute
it from the commits. The commit that adds a schema version updates every
declaration (`python/pyproject.toml`, `js/package.json`, `SCHEMA_VERSION`
in `python/src/timeskeleton/validate.py` and `js/src/validate.ts`, and the
self entry in `python/uv.lock`), adds the documents
`schema/X.Y.Z/{core,timeline,group,bundle}.schema.json`, a non-empty
`fixtures/X.Y.Z/` with its `drawings/`, `groups/` and `bundles/`, and
rejection fixtures, and passes `python3 scripts/check_versions.py`. A version after 0.5.0 also adds its
migration pair. The commit carries the footer:

```text
Release-As: X.Y.Z
```

On every push to `main`, release-please opens or updates a release pull
request with that version and its changelog entry. Merging the pull request
tags `vX.Y.Z` and creates the GitHub release. The release job fails when the
version differs from the declarations, and the publish job checks the tag
again before publishing. It then runs the Python and JavaScript checks, builds
both packages, and publishes them through OIDC trusted publishing without
stored registry tokens. Do not push version tags by hand.

The workflow needs GitHub Actions to be allowed to create pull requests in
this repository, and a trusted publisher on each registry:

| Registry | Project or package | GitHub owner | Repository | Workflow file | Environment |
| --- | --- | --- | --- | --- | --- |
| PyPI | `timeskeleton` | `TimeToAlign` | `timeskeleton` | `release.yml` | `release` |
| npm | `@timetoalign/timeskeleton` | `TimeToAlign` | `timeskeleton` | `release.yml` | `release` |
