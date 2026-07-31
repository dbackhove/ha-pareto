// Everything the card decides that does not involve the DOM. Split out so it
// can be tested without standing up a fake Home Assistant frontend.

import type { HomeAssistant, Mode, ParetoCardConfig, ParetoLists, ParetoRow } from "./types";

/** How stale a ranking may be before returning to a view refetches it. */
export const REFETCH_AFTER_MS = 30_000;

const MODES: readonly string[] = ["top", "recent"];

export function parseConfig(config: unknown): ParetoCardConfig {
  if (typeof config !== "object" || config === null) {
    throw new Error("pareto-card: configuration is missing");
  }
  const raw = config as Record<string, unknown>;

  const mode = raw.mode === undefined ? "top" : raw.mode;
  if (typeof mode !== "string" || !MODES.includes(mode)) {
    // Falling back to "top" would silently show the wrong list, and a typo in
    // a dashboard is much easier to find when it says so.
    throw new Error(`pareto-card: unknown mode "${String(mode)}", expected top or recent`);
  }

  let columns: number | undefined;
  if (raw.columns !== undefined) {
    if (typeof raw.columns !== "number" || !Number.isInteger(raw.columns) || raw.columns < 1) {
      throw new Error("pareto-card: columns must be a whole number of 1 or more");
    }
    columns = raw.columns;
  }

  if (raw.show_title !== undefined && typeof raw.show_title !== "boolean") {
    throw new Error("pareto-card: show_title must be true or false");
  }

  return {
    type: typeof raw.type === "string" ? raw.type : "custom:pareto-card",
    mode: mode as Mode,
    title: raw.title === undefined ? undefined : String(raw.title),
    // Named after Home Assistant's own show_name / show_icon / show_state, and
    // separate from `title` for the same reason: one option says whether, the
    // other says what.
    show_title: raw.show_title === undefined ? true : raw.show_title,
    columns,
  };
}

/**
 * Whether returning to a visible view should fetch a fresh ranking.
 *
 * The order is frozen while the card is on screen, so this only ever runs on
 * arrival. The age check keeps a quick app switch on a wall tablet from
 * refetching -- and thereby reordering -- every few seconds.
 */
export function shouldRefetch(
  lastFetch: number | null,
  now: number,
  minAgeMs: number = REFETCH_AFTER_MS,
): boolean {
  if (lastFetch === null) {
    return true;
  }
  return now - lastFetch >= minAgeMs;
}

export function gridColumns(columns?: number): string {
  return columns && columns > 0
    ? `repeat(${columns}, minmax(0, 1fr))`
    : "repeat(auto-fill, minmax(140px, 1fr))";
}

export function cardSize(rowCount: number, columns?: number): number {
  const perRow = columns && columns > 0 ? columns : 2;
  return 1 + Math.ceil(rowCount / perRow);
}

export function friendlyName(hass: HomeAssistant | undefined, entityId: string): string {
  return hass?.states[entityId]?.attributes.friendly_name ?? entityId;
}

/**
 * Apply a preference change to the lists already on screen.
 *
 * Hiding removes the entry and does *not* pull a replacement up from the
 * global ranking: tidying several entries in a row would otherwise rebuild the
 * list under the reader's hands. The next visit fills it back up.
 *
 * Pinning only marks the entry. Its effect on order belongs to the next
 * ranking, which is the same rule that keeps the list still while it is read.
 */
export function applyPref(
  lists: ParetoLists,
  entityId: string,
  change: { hidden?: boolean; pinned?: boolean },
  prefs: { hidden: string[] },
): ParetoLists {
  if (change.hidden === true) {
    const drop = (rows: ParetoRow[]) => rows.filter((row) => row.entity_id !== entityId);
    return { top: drop(lists.top), recent: drop(lists.recent), hidden: prefs.hidden };
  }

  if (change.pinned !== undefined) {
    const mark = (rows: ParetoRow[]) =>
      rows.map((row) =>
        row.entity_id === entityId ? { ...row, pinned: change.pinned as boolean } : row,
      );
    return { top: mark(lists.top), recent: mark(lists.recent), hidden: prefs.hidden };
  }

  return { ...lists, hidden: prefs.hidden };
}

export function errorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "message" in error) {
    return String((error as { message: unknown }).message);
  }
  return String(error);
}
