# 0005. Generate TypeScript types with json-schema-to-typescript

Date: 2026-10-09

## Context

Consumers need TypeScript declarations that track the normative JSON Schema
without hand-maintained duplication.

## Considered options

- `json-schema-to-typescript`.
- `json-schema-to-ts`.
- quicktype.
- Write generated declarations ourselves.

## Decision

Use `json-schema-to-typescript`, committing its deterministic output and
checking drift in tests. The TimeToAlign maintainers can inspect normal `.ts`
files, which limits bus-factor exposure. Primary sources: https://www.npmjs.com/package/json-schema-to-typescript
and https://github.com/bcherny/json-schema-to-typescript/blob/master/LICENSE.

## Consequences

The MIT-licensed generator is a development dependency and adds no package
runtime dependency. Its size and transitive dependencies remain lockfile
concerns only. It matches a modest release cadence; replacement cost is one
generator script and reviewed declarations. Writing it ourselves would shift
schema edge-case support to the maintainers.

## Review date

2027-10-09.
