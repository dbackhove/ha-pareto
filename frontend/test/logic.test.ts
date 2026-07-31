import { describe, expect, it } from "vitest";

import {
  applyPref,
  cardSize,
  errorMessage,
  friendlyName,
  gridColumns,
  parseConfig,
  REFETCH_AFTER_MS,
  shouldRefetch,
} from "../src/logic";
import type { HomeAssistant, ParetoLists, ParetoRow } from "../src/types";

function row(entityId: string, pinned = false): ParetoRow {
  return { entity_id: entityId, count: 1, last_used: null, pinned, personal: true };
}

function lists(top: ParetoRow[], hidden: string[] = []): ParetoLists {
  return { top, recent: [...top], hidden };
}

describe("parseConfig", () => {
  it("defaults to the top list", () => {
    expect(parseConfig({ type: "custom:pareto-card" }).mode).toBe("top");
  });

  it("accepts recent", () => {
    expect(parseConfig({ mode: "recent" }).mode).toBe("recent");
  });

  it("rejects an unknown mode instead of quietly showing the other list", () => {
    expect(() => parseConfig({ mode: "toppp" })).toThrow(/unknown mode/);
  });

  it("rejects a missing configuration", () => {
    expect(() => parseConfig(null)).toThrow();
  });

  it("keeps a title as given", () => {
    expect(parseConfig({ title: "Meistgenutzt" }).title).toBe("Meistgenutzt");
  });

  it("leaves columns unset when absent", () => {
    expect(parseConfig({}).columns).toBeUndefined();
  });

  it("rejects nonsensical column counts", () => {
    expect(() => parseConfig({ columns: 0 })).toThrow(/columns/);
    expect(() => parseConfig({ columns: 2.5 })).toThrow(/columns/);
    expect(() => parseConfig({ columns: "two" })).toThrow(/columns/);
  });

  it("shows the title unless asked not to", () => {
    expect(parseConfig({}).show_title).toBe(true);
    expect(parseConfig({ show_title: false }).show_title).toBe(false);
  });

  it("rejects a non-boolean show_title", () => {
    expect(() => parseConfig({ show_title: "no" })).toThrow(/show_title/);
  });

  it("keeps an explicitly empty title", () => {
    // Still honoured for anyone who wrote it before show_title existed.
    expect(parseConfig({ title: "" }).title).toBe("");
  });
});

describe("shouldRefetch", () => {
  it("fetches when nothing has been fetched yet", () => {
    expect(shouldRefetch(null, 1_000)).toBe(true);
  });

  it("does not refetch a ranking that is still fresh", () => {
    expect(shouldRefetch(1_000, 1_000 + REFETCH_AFTER_MS - 1)).toBe(false);
  });

  it("refetches once the ranking is stale", () => {
    expect(shouldRefetch(1_000, 1_000 + REFETCH_AFTER_MS)).toBe(true);
  });
});

describe("gridColumns", () => {
  it("is responsive without an explicit count", () => {
    expect(gridColumns()).toContain("auto-fill");
  });

  it("honours an explicit count", () => {
    expect(gridColumns(3)).toBe("repeat(3, minmax(0, 1fr))");
  });
});

describe("cardSize", () => {
  it("grows with the number of rows", () => {
    expect(cardSize(4, 2)).toBeGreaterThan(cardSize(2, 2));
  });

  it("counts an empty list as just the header", () => {
    expect(cardSize(0)).toBe(1);
  });
});

describe("friendlyName", () => {
  const hass = {
    states: { "light.a": { entity_id: "light.a", state: "on", attributes: { friendly_name: "Lamp" } } },
  } as unknown as HomeAssistant;

  it("prefers the friendly name", () => {
    expect(friendlyName(hass, "light.a")).toBe("Lamp");
  });

  it("falls back to the entity id", () => {
    expect(friendlyName(hass, "light.gone")).toBe("light.gone");
  });
});

describe("applyPref", () => {
  it("removes a hidden entry from both lists", () => {
    const before = lists([row("light.a"), row("light.b")]);
    const after = applyPref(before, "light.a", { hidden: true }, { hidden: ["light.a"] });

    expect(after.top.map((r) => r.entity_id)).toEqual(["light.b"]);
    expect(after.recent.map((r) => r.entity_id)).toEqual(["light.b"]);
    expect(after.hidden).toEqual(["light.a"]);
  });

  it("does not pull a replacement up when one is hidden", () => {
    const before = lists([row("light.a"), row("light.b")]);
    const after = applyPref(before, "light.a", { hidden: true }, { hidden: ["light.a"] });
    expect(after.top).toHaveLength(1);
  });

  it("marks a pin without moving the entry", () => {
    const before = lists([row("light.a"), row("light.b")]);
    const after = applyPref(before, "light.b", { pinned: true }, { hidden: [] });

    expect(after.top.map((r) => r.entity_id)).toEqual(["light.a", "light.b"]);
    expect(after.top[1].pinned).toBe(true);
  });

  it("clears a pin again", () => {
    const before = lists([row("light.a", true)]);
    const after = applyPref(before, "light.a", { pinned: false }, { hidden: [] });
    expect(after.top[0].pinned).toBe(false);
  });

  it("only updates the hidden list when an entry is restored", () => {
    const before = lists([row("light.b")], ["light.a"]);
    const after = applyPref(before, "light.a", { hidden: false }, { hidden: [] });

    expect(after.top.map((r) => r.entity_id)).toEqual(["light.b"]);
    expect(after.hidden).toEqual([]);
  });

  it("leaves the entries it was given untouched", () => {
    const before = lists([row("light.a")]);
    applyPref(before, "light.a", { pinned: true }, { hidden: [] });
    expect(before.top[0].pinned).toBe(false);
  });
});

describe("errorMessage", () => {
  it("uses the message a websocket error carries", () => {
    expect(errorMessage({ code: "not_loaded", message: "Pareto is not set up" })).toBe(
      "Pareto is not set up",
    );
  });

  it("copes with anything else", () => {
    expect(errorMessage("boom")).toBe("boom");
  });
});
