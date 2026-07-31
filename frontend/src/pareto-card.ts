// The Pareto card.
//
// It renders Home Assistant's own tile cards rather than its own controls, so
// every domain behaves the way it does everywhere else in the dashboard, and
// keeps doing so as Home Assistant moves on. The card's own job is small: ask
// for a ranking once per visit, lay the tiles out, and offer a way to tidy the
// list.

import { LitElement, css, html, nothing, type TemplateResult } from "lit";

import {
  applyPref,
  cardSize,
  errorMessage,
  friendlyName,
  gridColumns,
  parseConfig,
  shouldRefetch,
} from "./logic";
import "./editor";
import { translate, type StringKey } from "./strings";
import type {
  CardHelpers,
  HomeAssistant,
  LovelaceCard,
  ParetoCardConfig,
  ParetoLists,
  ParetoPrefs,
  ParetoRow,
} from "./types";

declare global {
  interface Window {
    loadCardHelpers?: () => Promise<CardHelpers>;
    customCards?: Array<Record<string, unknown>>;
  }
}

class ParetoCard extends LitElement {
  static override properties = {
    _config: { state: true },
    _lists: { state: true },
    _error: { state: true },
    _editing: { state: true },
  };

  _config?: ParetoCardConfig;
  _lists?: ParetoLists;
  _error?: string;
  _editing = false;

  private _hass?: HomeAssistant;
  private _helpers?: CardHelpers;
  private _tiles = new Map<string, LovelaceCard>();
  private _loading = false;
  // Deliberately the last *attempt*, not the last success. A card whose fetch
  // failed must still be throttled, or it retries forever at state-change rate.
  private _lastAttempt: number | null = null;

  private _onVisibility = (): void => {
    if (document.visibilityState === "visible") {
      void this._load(false);
    }
  };

  static getStubConfig(): Record<string, unknown> {
    return { mode: "top" };
  }

  static getConfigElement(): HTMLElement {
    return document.createElement("pareto-card-editor");
  }

  setConfig(config: unknown): void {
    this._config = parseConfig(config);
    // The mode may have changed, and the old tiles belong to the other list.
    this._tiles.clear();
    this._syncTiles();
    // Home Assistant calls setConfig before assigning hass and before adding
    // the card to the document, so in practice the load below is the one that
    // never runs. It is here so the card does not depend on that order: every
    // other entry point bails out while _config is still unset.
    void this._load(true);
  }

  set hass(hass: HomeAssistant | undefined) {
    this._hass = hass;
    // Tiles keep themselves current from this. The card itself deliberately
    // does not re-render here: hass changes on every state change in the
    // house, and redrawing the whole grid that often would be wasteful.
    for (const tile of this._tiles.values()) {
      tile.hass = hass;
    }
    if (this._lists === undefined) {
      // Not forced. hass is reassigned on every state change in the house, so
      // forcing here turns a single failed fetch into one request per state
      // change, for as long as the card is on screen.
      void this._load(false);
    }
  }

  get hass(): HomeAssistant | undefined {
    return this._hass;
  }

  override connectedCallback(): void {
    super.connectedCallback();
    document.addEventListener("visibilitychange", this._onVisibility);
    // Home Assistant rebuilds cards when a view is opened, which makes this
    // the moment the ranking is allowed to change.
    void this._load(true);
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    document.removeEventListener("visibilitychange", this._onVisibility);
  }

  getCardSize(): number {
    return cardSize(this._rows().length, this._config?.columns);
  }

  private _t(key: StringKey): string {
    return translate(this._hass?.locale?.language, key);
  }

  private _rows(): ParetoRow[] {
    if (!this._lists || !this._config) {
      return [];
    }
    return this._lists[this._config.mode];
  }

  private async _ensureHelpers(): Promise<void> {
    if (this._helpers) {
      return;
    }
    const loader = window.loadCardHelpers;
    if (!loader) {
      throw new Error(this._t("noHelpers"));
    }
    this._helpers = await loader();
  }

  private async _load(force: boolean): Promise<void> {
    if (!this._hass || !this._config || this._loading) {
      return;
    }
    if (!force && !shouldRefetch(this._lastAttempt, Date.now())) {
      return;
    }

    this._loading = true;
    try {
      await this._ensureHelpers();
      const lists = await this._hass.callWS<ParetoLists>({ type: "pareto/lists" });
      this._lists = lists;
      this._error = undefined;
      this._syncTiles();
    } catch (error) {
      this._error = errorMessage(error);
    } finally {
      // Stamped whichever way it went, so a failing card retries at most once
      // per interval instead of once per state change.
      this._lastAttempt = Date.now();
      this._loading = false;
    }
  }

  private _syncTiles(): void {
    if (!this._helpers || !this._config || !this._lists) {
      return;
    }

    const rows = this._rows();
    const wanted = new Set(rows.map((row) => row.entity_id));
    for (const entityId of [...this._tiles.keys()]) {
      if (!wanted.has(entityId)) {
        this._tiles.delete(entityId);
      }
    }

    for (const row of rows) {
      if (this._tiles.has(row.entity_id)) {
        continue;
      }
      const tile = this._helpers.createCardElement({ type: "tile", entity: row.entity_id });
      tile.hass = this._hass;
      this._tiles.set(row.entity_id, tile);
    }
  }

  private _toggleEdit(): void {
    // Leaving edit mode deliberately does not refetch: that would reorder the
    // list the moment somebody finished tidying it.
    this._editing = !this._editing;
  }

  private async _setPref(
    entityId: string,
    change: { hidden?: boolean; pinned?: boolean },
  ): Promise<void> {
    if (!this._hass || !this._lists) {
      return;
    }

    try {
      const prefs = await this._hass.callWS<ParetoPrefs>({
        type: "pareto/set_pref",
        entity_id: entityId,
        ...change,
      });
      this._lists = applyPref(this._lists, entityId, change, prefs);
      this._error = undefined;
      this._syncTiles();

      if (change.hidden === false) {
        // Restoring is the one change that has to reorder. An entry can only
        // reappear where it belongs if the ranking is asked again.
        await this._load(true);
      }
    } catch (error) {
      this._error = errorMessage(error);
    }
  }

  override render(): TemplateResult | typeof nothing {
    if (!this._config) {
      return nothing;
    }
    const rows = this._rows();

    return html`
      <ha-card>
        <div class="head ${this._config.show_title ? "" : "bare"}">
          ${this._config.show_title
            ? html`<span class="title">${this._config.title ?? this._t(this._config.mode)}</span>`
            : nothing}
          <button
            class="icon"
            title=${this._t(this._editing ? "done" : "edit")}
            @click=${this._toggleEdit}
          >
            <ha-icon icon=${this._editing ? "mdi:check" : "mdi:pencil"}></ha-icon>
          </button>
        </div>
        ${this._error ? html`<div class="notice error">${this._error}</div>` : nothing}
        ${rows.length ? this._grid(rows) : this._emptyNotice()}
        ${this._editing ? this._hiddenSection() : nothing}
      </ha-card>
    `;
  }

  private _grid(rows: ParetoRow[]): TemplateResult {
    return html`
      <div class="grid" style="grid-template-columns: ${gridColumns(this._config?.columns)}">
        ${rows.map((row) => this._cell(row))}
      </div>
    `;
  }

  private _cell(row: ParetoRow): TemplateResult {
    return html`
      <div class="cell ${this._editing ? "editing" : ""}">
        ${this._tiles.get(row.entity_id)}
        ${this._editing
          ? html`
              <div class="overlay">
                <button
                  class="chip"
                  title=${this._t("hide")}
                  @click=${() => this._setPref(row.entity_id, { hidden: true })}
                >
                  <ha-icon icon="mdi:close"></ha-icon>
                </button>
                <button
                  class="chip ${row.pinned ? "on" : ""}"
                  title=${this._t(row.pinned ? "unpin" : "pin")}
                  @click=${() => this._setPref(row.entity_id, { pinned: !row.pinned })}
                >
                  <ha-icon icon="mdi:pin"></ha-icon>
                </button>
              </div>
            `
          : nothing}
      </div>
    `;
  }

  private _hiddenSection(): TemplateResult | typeof nothing {
    const hidden = this._lists?.hidden ?? [];
    if (!hidden.length) {
      return nothing;
    }

    return html`
      <div class="hidden-list">
        <div class="subhead">${this._t("hiddenHeading")}</div>
        ${hidden.map(
          (entityId) => html`
            <div class="hidden-row">
              <span class="name">${friendlyName(this._hass, entityId)}</span>
              <button
                class="chip"
                title=${this._t("restore")}
                @click=${() => this._setPref(entityId, { hidden: false })}
              >
                <ha-icon icon="mdi:restore"></ha-icon>
              </button>
            </div>
          `,
        )}
      </div>
    `;
  }

  private _emptyNotice(): TemplateResult | typeof nothing {
    if (this._error || !this._lists) {
      return nothing;
    }
    return html`<div class="notice">
      ${this._t(this._lists.hidden.length ? "allHidden" : "empty")}
    </div>`;
  }

  static override styles = css`
    ha-card {
      padding: 8px;
    }

    .head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 8px 12px;
    }

    /* Without a title the row exists only to carry the pencil, so it stops
       claiming the height of a heading. */
    .head.bare {
      padding: 0 4px 4px;
      justify-content: flex-end;
    }

    .title {
      font-size: var(--ha-card-header-font-size, 24px);
      font-weight: 400;
      color: var(--ha-card-header-color, var(--primary-text-color));
    }

    button.icon,
    button.chip {
      background: none;
      border: none;
      cursor: pointer;
      color: var(--secondary-text-color);
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 4px;
      border-radius: 50%;
    }

    /* The pencil is a rarely-used affordance sitting next to a heading, so it
       is deliberately smaller than a normal icon button. */
    button.icon {
      --mdc-icon-size: 18px;
      padding: 2px;
      opacity: 0.7;
    }

    button.icon:hover {
      opacity: 1;
    }

    button.icon:hover,
    button.chip:hover {
      color: var(--primary-text-color);
    }

    .grid {
      display: grid;
      gap: 8px;
    }

    .cell {
      position: relative;
    }

    /* In edit mode the tiles are decoration: a tap must tidy the list, not
       switch the light it happens to land on. */
    .cell.editing > *:not(.overlay) {
      pointer-events: none;
      opacity: 0.55;
    }

    .overlay {
      position: absolute;
      inset: 0;
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      padding: 4px;
    }

    .overlay .chip {
      background: var(--card-background-color);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
    }

    .overlay .chip.on {
      color: var(--primary-color);
    }

    .hidden-list {
      margin-top: 12px;
      border-top: 1px solid var(--divider-color);
      padding-top: 8px;
    }

    .subhead {
      font-size: 0.9em;
      color: var(--secondary-text-color);
      padding: 0 8px 4px;
    }

    .hidden-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 2px 8px;
    }

    .hidden-row .name {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .notice {
      padding: 8px 16px 16px;
      color: var(--secondary-text-color);
    }

    .notice.error {
      color: var(--error-color, #db4437);
    }
  `;
}

// Guarded as one unit: a second evaluation of this bundle must not throw on
// the redefinition, nor leave the card listed twice in the card picker.
if (!customElements.get("pareto-card")) {
  customElements.define("pareto-card", ParetoCard);

  window.customCards = window.customCards ?? [];
  window.customCards.push({
    type: "pareto-card",
    name: "Pareto",
    description: "The entities you actually operate, ranked.",
    preview: false,
    documentationURL: "https://github.com/dbackhove/ha-pareto",
  });
}
