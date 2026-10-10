# Contributing

TimeSkeleton is schema-first. The versioned schema is the contract; the Python and TypeScript packages validate that contract, and timetoalign emits its fixtures.

## Schema changes

For a format change, add a new versioned file under `schema/`; do not alter a published schema. Update the supported-version and latest-version declarations in both packages, then implement an ordered, pure migration in each package from the prior version. Add before-and-after fixture pairs for each migration and shared rejection fixtures, regenerate `js/src/generated/` with `pnpm generate`, and re-emit the golden fixtures through timetoalign. Keep every earlier schema version and its fixtures validatable.

Fixtures under `fixtures/` are generated artifacts. Use an environment containing the timetoalign revision represented by the schema:

```bash
python scripts/emit_fixtures.py --timetoalign-commit "$(git -C /path/to/timetoalign rev-parse --short HEAD)"
```

Do not edit fixture JSON by hand.

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

Update the version in `python/pyproject.toml`, `js/package.json`, `python/src/timeskeleton/validate.py`, and `js/src/validate.ts`; add the matching `schema/timeskeleton-X.Y.Z.schema.json`, a non-empty `fixtures/X.Y.Z/` directory, its migration pair, and rejection fixtures. Then run:

```bash
python3 scripts/check_versions.py --tag vX.Y.Z
git tag vX.Y.Z
git push origin vX.Y.Z
```

Pushing the tag invokes `.github/workflows/release.yml`. It checks version declarations, builds and checks the Python distributions, installs and tests the npm package, builds it, then publishes both packages through OIDC trusted publishing without stored registry tokens.

Configure each trusted publisher once before the first release:

| Registry | Project or package | GitHub owner | Repository | Workflow file | Environment |
| --- | --- | --- | --- | --- | --- |
| PyPI | `timeskeleton` | `TimeToAlign` | `timeskeleton` | `.github/workflows/release.yml` | `release` |
| npm | `@timetoalign/timeskeleton` | `TimeToAlign` | `timeskeleton` | `.github/workflows/release.yml` | `release` |
