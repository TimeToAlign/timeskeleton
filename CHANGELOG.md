# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Schema 0.2.0 specifies conversion maps, regions, flow control, and Measure Map standard compressed rows with the `volta` extension while retaining an opaque metric hierarchy.
- Golden map, flow-control, and corpus fixtures, shared rejection cases, and the 0.1.0 to 0.2.0 migration fixture pair.
- Version-aware validators and migration support in both packages.
- The 0.1.0 TimeSkeleton JSON Schema for eventless structural musical timelines.
- Nine golden fixtures emitted by timetoalign, including all six timeline classes, nested timelines, regions, and an empty document.
- The `timeskeleton` Python package with schema resources, validation, migrations, and fixture helpers.
- The `@timetoalign/timeskeleton` npm package with generated TypeScript types, validation, and migrations.
- Continuous integration, version consistency checks, fixture emission, and OIDC trusted publishing for both packages.
- MADR decision records for format, tooling, packaging, validation, generation, and release choices.
