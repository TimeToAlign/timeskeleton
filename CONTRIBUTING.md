# Contributing

TimeSkeleton is schema-first. The versioned schema is the contract; the Python and TypeScript packages validate that contract, and timetoalign emits its fixtures.

## Schema changes

For a format change, add a new versioned file under `schema/`; do not alter a published schema. Update the supported-version and latest-version declarations in both packages, then implement an ordered, pure migration in each package from the prior version. Add before-and-after fixture pairs for each migration and shared rejection fixtures, regenerate `js/src/generated/` with `pnpm generate`, and re-emit the golden fixtures through timetoalign. Keep every earlier schema version and its fixtures validatable.

The golden fixtures under `fixtures/<version>/` are generated artifacts. Use an environment containing the timetoalign revision represented by the schema:

```bash
python scripts/emit_fixtures.py --timetoalign-commit "$(git -C /path/to/timetoalign rev-parse --short HEAD)"
```

Do not edit golden fixture JSON by hand. The script refuses to write into the fixtures of a version whose `v<version>` tag exists. Rejection cases under `fixtures/rejections/` and migration pairs under `fixtures/migrations/` are authored by hand.

## Dependencies and decisions

Add a dependency only with a numbered MADR in `decisions/`. The record must assess writing it ourselves and its long-term maintenance cost, name the audited version, and set a review date. Do not add speculative dependencies or options.

The package manifests declare compatible version ranges because published packages resolve in consumers' environments. The lockfiles, `python/uv.lock` and `js/pnpm-lock.yaml`, pin exact versions. An audited dependency release must have been available for at least 14 days before it is added.

## Tests

Tests are README-first. Update the relevant `python/tests/README.md` or `js/tests/README.md` to state the proof required, then write tests with exact expected values.

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

- The validator tests do not pin the JSON implementation's maximum safe-integer boundary in either implementation.
- Python and TypeScript rejection paths are independently compared with expected values, but no test compares both implementations' paths for the same generated invalid documents.

## Release

Releases are made by [release-please](https://github.com/googleapis/release-please) and `.github/workflows/release.yml`. Write commit messages in the [Conventional Commits](https://www.conventionalcommits.org/) form; release-please builds `CHANGELOG.md` from them.

A timeskeleton version is a schema version, so release-please never computes it from the commits. The commit that adds a schema version updates every declaration (`python/pyproject.toml`, `js/package.json`, `SCHEMA_VERSION` in `python/src/timeskeleton/validate.py` and `js/src/validate.ts`, the self entry in `python/uv.lock`), adds `schema/timeskeleton-X.Y.Z.schema.json`, a non-empty `fixtures/X.Y.Z/`, its migration pair and rejection fixtures, passes `python3 scripts/check_versions.py`, and carries the footer

```text
Release-As: X.Y.Z
```

On every push to `main`, release-please opens or updates a release pull request with that version and its changelog entry. Merging the pull request tags `vX.Y.Z` and creates the GitHub release; the release job fails on a merged release pull request whose version differs from the declarations, and the publish job checks the tag against them again before anything is published. The publish job then checks out the tag, runs `scripts/check_versions.py --tag vX.Y.Z`, lints and tests the Python package, builds and checks the Python distributions, installs, tests and builds the npm package, and publishes both packages through OIDC trusted publishing without stored registry tokens. Do not push version tags by hand.

The workflow needs GitHub Actions to be allowed to create pull requests in this repository, and a trusted publisher on each registry:

| Registry | Project or package | GitHub owner | Repository | Workflow file | Environment |
| --- | --- | --- | --- | --- | --- |
| PyPI | `timeskeleton` | `TimeToAlign` | `timeskeleton` | `release.yml` | `release` |
| npm | `@timetoalign/timeskeleton` | `TimeToAlign` | `timeskeleton` | `release.yml` | `release` |
