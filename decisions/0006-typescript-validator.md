# 0006. Validate TypeScript documents with Ajv 8

Date: 2026-10-09

## Context

The npm package needs runtime validation of draft 2020-12 documents, including
recursive timeline definitions.

## Considered options

- Ajv 8.
- Ajv standalone code.
- TypeBox Value.
- `@cfworker/json-schema`.
- Write the validator ourselves.

## Decision

Use Ajv 8 with its 2020-12 entry point. Its published error information lets
the package expose stable document paths. TimeToAlign maintainers avoid owning
a validator implementation, improving the bus factor. Primary sources:
https://ajv.js.org/json-schema.html and https://github.com/ajv-validator/ajv/blob/master/LICENSE.

## Consequences

Ajv is an MIT-licensed runtime dependency with a bounded dependency tree and
modest installed size. Standalone code could reduce runtime dependencies but
would complicate generation and review. The selected route fits the release
cadence; the adapter in `validate.ts` caps exit cost. Writing it ourselves
would require ongoing draft compatibility and security work.

## Review date

2027-10-09.
