import type { JsonObject } from "../json/value.js";
import { timelineContainmentProblems } from "./containment.js";
import {
  entries,
  jsonPointer,
  type PathSegment,
  SchemaValidationError,
  text,
} from "./diagnostics.js";
import { MEASURE_VIEWS, timelineMapProblems, timelineMaps } from "./maps.js";
import { orderProblems } from "./order.js";
import { timelineSegmentProblems } from "./segments.js";

function* elementIds(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<[string, PathSegment[]]> {
  yield [text(timeline, "id"), [...path, "id"]];
  for (const member of ["conversion_maps", "regions"]) {
    for (const [index, entry] of entries(timeline, member).entries()) {
      yield [text(entry, "id"), [...path, member, index, "id"]];
    }
  }
  for (const [index, entry] of entries(timeline, "flow_control").entries()) {
    yield [text(entry, "id"), [...path, "flow_control", index, "id"]];
  }
  for (const [index, child] of entries(timeline, "children").entries()) {
    yield* elementIds(child, [...path, "children", index]);
  }
}

function* nestedMapIds(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<[string, PathSegment[]]> {
  for (const [map, at] of timelineMaps(timeline, path)) {
    if (at[at.length - 2] === "maps") yield [text(map, "id"), [...at, "id"]];
  }
  for (const [index, child] of entries(timeline, "children").entries()) {
    yield* nestedMapIds(child, [...path, "children", index]);
  }
}

function* timelineIds(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<[string, PathSegment[]]> {
  yield [text(timeline, "id"), [...path, "id"]];
  for (const [index, child] of entries(timeline, "children").entries()) {
    yield* timelineIds(child, [...path, "children", index]);
  }
}

function* danglingTargets(
  timeline: JsonObject,
  path: readonly PathSegment[],
  measureMaps: ReadonlySet<string>,
): Generator<SchemaValidationError> {
  const flow = entries(timeline, "flow_control");
  const targets = new Set(
    flow.filter((entry) => entry.type === "jump_to").map((entry) => entry.id),
  );
  for (const [index, entry] of flow.entries()) {
    if (Object.hasOwn(entry, "target") && !targets.has(entry.target)) {
      yield new SchemaValidationError(
        "dangling_target",
        [...path, "flow_control", index, "target"],
        `${JSON.stringify(entry.target)} names no jump_to of this timeline`,
      );
    }
  }
  for (const [map, at] of timelineMaps(timeline, path)) {
    const reference = map.measure_map;
    if (MEASURE_VIEWS.has(text(map, "type")) && !measureMaps.has(reference as string)) {
      yield new SchemaValidationError(
        "dangling_target",
        [...at, "measure_map"],
        `${JSON.stringify(reference)} names no measure map of this manifest`,
      );
    }
  }
  for (const [index, child] of entries(timeline, "children").entries()) {
    yield* danglingTargets(child, [...path, "children", index], measureMaps);
  }
}

function duplicate(
  id: string,
  path: readonly PathSegment[],
  first: readonly PathSegment[],
  code: "duplicate_id" | "manifest_id" = "duplicate_id",
): SchemaValidationError {
  return new SchemaValidationError(
    code,
    path,
    `duplicate id ${JSON.stringify(id)}, first at ${jsonPointer(first)}`,
  );
}

function* rootProblems(
  root: JsonObject,
  path: readonly PathSegment[],
  measureMaps: ReadonlySet<string>,
): Generator<SchemaValidationError> {
  const first = new Map<string, PathSegment[]>();
  for (const ids of [elementIds(root, path), nestedMapIds(root, path)]) {
    for (const [id, at] of ids) {
      const earlier = first.get(id);
      if (earlier === undefined) first.set(id, at);
      else yield duplicate(id, at, earlier);
    }
  }
  yield* danglingTargets(root, path, measureMaps);
  yield* timelineMapProblems(root, path);
  yield* timelineContainmentProblems(root, path);
  yield* timelineSegmentProblems(root, path);
}

const PART_WORDS: ReadonlySet<string> = new Set(["start", "end", "name", "label", "card"]);
const BAND_ID = /^(markers|conversion_maps|children|regions|flow_control)_[1-9][0-9]*$/;

function* reserved(id: string, path: readonly PathSegment[]): Generator<SchemaValidationError> {
  const what = PART_WORDS.has(id)
    ? "the parts of an address"
    : BAND_ID.test(id)
      ? "the bands of a timeline"
      : null;
  if (what !== null) {
    yield new SchemaValidationError(
      "reserved_id",
      path,
      `id ${JSON.stringify(id)} is reserved for ${what}`,
    );
  }
}

/** Parent ids for every timeline; the first occurrence of a repeated id wins. */
function parentsOf(roots: readonly JsonObject[]): Map<string, string | null> {
  const parents = new Map<string, string | null>();
  const visit = (timeline: JsonObject, parent: string | null): void => {
    const id = text(timeline, "id");
    if (!parents.has(id)) parents.set(id, parent);
    for (const child of entries(timeline, "children")) visit(child, id);
  };
  for (const root of roots) visit(root, null);
  return parents;
}

function ancestorsOf(id: string, parents: ReadonlyMap<string, string | null>): string[] {
  const ancestors: string[] = [];
  let parent = parents.get(id) ?? null;
  while (parent !== null) {
    ancestors.push(parent);
    parent = parents.get(parent) ?? null;
  }
  return ancestors;
}

function* memberProblems(
  group: JsonObject,
  path: readonly PathSegment[],
  parents: ReadonlyMap<string, string | null>,
): Generator<SchemaValidationError> {
  const selected = new Map<string, number>();
  const earliestDescendant = new Map<string, { index: number; member: string }>();
  for (const [index, member] of (group.members as string[]).entries()) {
    const at = [...path, index];
    if (!parents.has(member)) {
      yield new SchemaValidationError(
        "group_member",
        at,
        `${JSON.stringify(member)} names no timeline of this manifest`,
      );
      continue;
    }
    const earlier = selected.get(member);
    if (earlier !== undefined) {
      yield new SchemaValidationError(
        "group_member",
        at,
        `duplicate member ${JSON.stringify(member)}, first at ${jsonPointer([...path, earlier])}`,
      );
    }

    const ancestors = ancestorsOf(member, parents);
    let relation: { index: number; member: string; word: "lies inside" | "contains" } | null = null;
    for (const ancestor of ancestors) {
      const selectedIndex = selected.get(ancestor);
      if (selectedIndex !== undefined && (relation === null || selectedIndex < relation.index)) {
        relation = { index: selectedIndex, member: ancestor, word: "lies inside" };
      }
    }
    const descendant = earliestDescendant.get(member);
    if (descendant !== undefined && (relation === null || descendant.index < relation.index)) {
      relation = { ...descendant, word: "contains" };
    }
    if (relation !== null) {
      yield new SchemaValidationError(
        "group_member",
        at,
        `member ${JSON.stringify(member)} ${relation.word} member ${JSON.stringify(relation.member)} of the same group`,
      );
    }

    if (!selected.has(member)) selected.set(member, index);
    for (const ancestor of ancestors) {
      if (!earliestDescendant.has(ancestor)) {
        earliestDescendant.set(ancestor, { index, member });
      }
    }
  }
}

/**
 * Yield semantic problems in the public identity order.
 *
 * Root by root: duplicates, dangling targets, conversion maps, containment
 * and segment lines; then reserved ids, cross-root timeline ids, group ids,
 * measure-map ids, the manifest id, group members, and graphical orders.
 */
export function* identityProblems(manifest: JsonObject): Generator<SchemaValidationError> {
  const roots = entries(manifest, "timelines");
  const groups = entries(manifest, "groups");
  const measureMaps = entries(manifest, "measure_maps");
  const measureMapIds = new Set(measureMaps.map((measureMap) => text(measureMap, "id")));
  for (const [index, root] of roots.entries()) {
    yield* rootProblems(root, ["timelines", index], measureMapIds);
  }

  const manifestId = typeof manifest.id === "string" ? manifest.id : null;
  if (manifestId !== null) yield* reserved(manifestId, ["id"]);
  for (const [index, root] of roots.entries()) {
    for (const [id, at] of elementIds(root, ["timelines", index])) yield* reserved(id, at);
    for (const [id, at] of nestedMapIds(root, ["timelines", index])) yield* reserved(id, at);
  }
  for (const [index, group] of groups.entries()) {
    yield* reserved(text(group, "id"), ["groups", index, "id"]);
  }
  for (const [index, measureMap] of measureMaps.entries()) {
    yield* reserved(text(measureMap, "id"), ["measure_maps", index, "id"]);
  }

  const timelines = new Map<string, PathSegment[]>();
  for (const [index, root] of roots.entries()) {
    const seen = new Map<string, PathSegment[]>();
    for (const [id, path] of timelineIds(root, ["timelines", index])) {
      if (seen.has(id)) continue;
      seen.set(id, path);
      const earlier = timelines.get(id);
      if (earlier !== undefined) yield duplicate(id, path, earlier);
    }
    for (const [id, path] of seen) if (!timelines.has(id)) timelines.set(id, path);
  }

  const firstGroup = new Map<string, number>();
  for (const [index, group] of groups.entries()) {
    const id = text(group, "id");
    const path = ["groups", index, "id"];
    const timeline = timelines.get(id);
    const earlier = firstGroup.get(id);
    if (timeline !== undefined) yield duplicate(id, path, timeline);
    else if (earlier !== undefined) yield duplicate(id, path, ["groups", earlier, "id"]);
    if (earlier === undefined) firstGroup.set(id, index);
  }

  const firstMeasureMap = new Map<string, number>();
  for (const [index, measureMap] of measureMaps.entries()) {
    const id = text(measureMap, "id");
    const path = ["measure_maps", index, "id"];
    const timeline = timelines.get(id);
    const group = firstGroup.get(id);
    const earlier = firstMeasureMap.get(id);
    if (timeline !== undefined) yield duplicate(id, path, timeline);
    else if (group !== undefined) yield duplicate(id, path, ["groups", group, "id"]);
    else if (earlier !== undefined) yield duplicate(id, path, ["measure_maps", earlier, "id"]);
    if (earlier === undefined) firstMeasureMap.set(id, index);
  }

  if (manifestId !== null) {
    const groupIndex = firstGroup.get(manifestId);
    const measureMapIndex = firstMeasureMap.get(manifestId);
    const first =
      timelines.get(manifestId) ??
      (groupIndex === undefined ? undefined : ["groups", groupIndex, "id"]) ??
      (measureMapIndex === undefined ? undefined : ["measure_maps", measureMapIndex, "id"]);
    if (first !== undefined) yield duplicate(manifestId, ["id"], first, "manifest_id");
  }

  const parents = parentsOf(roots);
  for (const [index, group] of groups.entries()) {
    yield* memberProblems(group, ["groups", index, "members"], parents);
  }
  yield* orderProblems(manifest, timelines, firstGroup);
}
