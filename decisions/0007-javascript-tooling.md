# 0007. Use pnpm, TypeScript, Biome, and Vitest

Date: 2026-10-09

## Context

The npm package needs reproducible installs, strict declarations, formatting,
and a fast test runner.

## Considered options

- pnpm, TypeScript, Biome, and Vitest.
- npm or yarn.
- ESLint plus Prettier.
- Jest.
- Write the surrounding tooling ourselves.

## Decision

Use pnpm, strict TypeScript, Biome, and Vitest. The TimeToAlign maintainers
get lockfile-backed installs and one lint/format tool, reducing the bus factor.
Primary sources: https://pnpm.io/, https://www.typescriptlang.org/docs/,
https://github.com/biomejs/biome/blob/main/LICENSE-MIT, and https://github.com/vitest-dev/vitest/blob/main/LICENSE.

## Consequences

These tools are MIT-licensed development dependencies; the published package
contains compiled JavaScript and declarations, not the toolchain. Their size
and transitive dependencies live in the lockfile. They suit the release
cadence; exiting is limited to scripts and configuration. Writing equivalent
tools ourselves has an unjustified maintenance cost.

## Review date

2027-10-09.
