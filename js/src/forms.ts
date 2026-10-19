/**
 * The typed forms of a TimeSkeleton manifest. A manifest read by
 * `parseJson` is a `LosslessTimeSkeleton`; its complete form, every key with a
 * default written out at every depth, is a `CompleteTimeSkeleton`; both are
 * generated from the schema (`./generated/types.ts`). The three functions
 * here convert between them and put either in canonical order; they are the
 * typed entry points to `complete`, `minimal` and `canonicalOrder`, which
 * take any value.
 */

import { complete, minimal } from "./defaults.js";
import type { CompleteTimeSkeleton, LosslessTimeSkeleton } from "./generated/types.js";
import { canonicalOrder } from "./manifest/order.js";

/** The complete form of a manifest: every key with a default present, at every depth. */
export function completeManifest(value: LosslessTimeSkeleton): CompleteTimeSkeleton {
  return complete(value);
}

/** The minimal form of a manifest: every key whose value is its default left out. */
export function minimalManifest(value: CompleteTimeSkeleton): LosslessTimeSkeleton {
  return minimal(value);
}

/** A manifest with every array whose order carries no meaning in canonical order. */
export function canonicalManifest<T extends LosslessTimeSkeleton>(value: T): T {
  return canonicalOrder(value);
}
