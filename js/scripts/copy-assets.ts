/**
 * Copy the repository's `schema/`, `fixtures/`, `fonts/` and `docs/` directories, its
 * `README.md` and its `LICENSE` into the package directory so that `npm publish`
 * ships them (see the `files` field; npm always includes a README and a LICENSE). The copies are
 * ignored by git; the files at the repository root are the only originals.
 *
 *     node scripts/copy-assets.ts
 */

import { cpSync, existsSync, rmSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const repository = resolve(here, "../..");
const packageDirectory = resolve(here, "..");

for (const name of ["schema", "fixtures", "fonts", "docs", "README.md", "LICENSE"]) {
  const source = resolve(repository, name);
  const destination = resolve(packageDirectory, name);
  rmSync(destination, { recursive: true, force: true });
  if (!existsSync(source)) {
    console.log(`skipped ${name}: not present at the repository root`);
    continue;
  }
  cpSync(source, destination, { recursive: true });
  console.log(`copied ${name}`);
}
