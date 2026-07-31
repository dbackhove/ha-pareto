// Home Assistant publishes no types for custom cards, so this is the smallest
// set the card actually touches. Keeping it hand-written and minimal beats
// depending on a third-party mirror that goes stale.

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: { friendly_name?: string } & Record<string, unknown>;
}

export interface HassLocale {
  language?: string;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  locale?: HassLocale;
  callWS<T>(message: Record<string, unknown>): Promise<T>;
}

/** One entry as `pareto/lists` sends it. `score` is absent in recent lists. */
export interface ParetoRow {
  entity_id: string;
  score?: number;
  count: number;
  last_used: string | null;
  pinned: boolean;
  personal: boolean;
}

export interface ParetoLists {
  top: ParetoRow[];
  recent: ParetoRow[];
  hidden: string[];
}

export interface ParetoPrefs {
  hidden: string[];
  pinned: string[];
}

export type Mode = "top" | "recent";

export interface ParetoCardConfig {
  type: string;
  mode: Mode;
  title?: string;
  show_title: boolean;
  columns?: number;
}

/** What `createCardElement` hands back. */
export interface LovelaceCard extends HTMLElement {
  hass?: HomeAssistant;
}

export interface CardHelpers {
  createCardElement(config: Record<string, unknown>): LovelaceCard;
}
