// The card's visual editor.
//
// Built on Home Assistant's own `ha-form` and its selectors, so the controls
// look and behave like every other card editor, and so this file carries no
// widgets of its own.

import { LitElement, html, nothing, type TemplateResult } from "lit";

import { translate, type StringKey } from "./strings";
import type { HomeAssistant } from "./types";

interface SchemaEntry {
  name: string;
  selector: Record<string, unknown>;
}

const SCHEMA: SchemaEntry[] = [
  {
    name: "mode",
    selector: {
      select: {
        mode: "dropdown",
        options: [
          { value: "top", label: "Most used" },
          { value: "recent", label: "Recently used" },
        ],
      },
    },
  },
  { name: "show_title", selector: { boolean: {} } },
  { name: "title", selector: { text: {} } },
  { name: "columns", selector: { number: { min: 1, max: 6, mode: "box" } } },
];

class ParetoCardEditor extends LitElement {
  static override properties = {
    hass: { attribute: false },
    _config: { state: true },
  };

  hass?: HomeAssistant;
  _config?: Record<string, unknown>;

  setConfig(config: Record<string, unknown>): void {
    // Shown, not validated. The card's own setConfig is the authority; an
    // editor that rejected a half-typed value would fight the person typing.
    this._config = { show_title: true, ...config };
  }

  private _label = (schema: SchemaEntry): string =>
    translate(this.hass?.locale?.language, schema.name as StringKey);

  private _changed(event: CustomEvent): void {
    const config = { ...(event.detail.value as Record<string, unknown>) };

    // ha-form drops a cleared text field. Left alone that would read as "no
    // title set" and bring the default name back, so an explicit switch is
    // what turns the title off -- this only keeps the two from contradicting.
    if (config.title === "") {
      delete config.title;
    }

    this.dispatchEvent(
      new CustomEvent("config-changed", {
        detail: { config },
        bubbles: true,
        composed: true,
      }),
    );
  }

  override render(): TemplateResult | typeof nothing {
    if (!this._config) {
      return nothing;
    }

    return html`
      <ha-form
        .hass=${this.hass}
        .data=${this._config}
        .schema=${SCHEMA}
        .computeLabel=${this._label}
        @value-changed=${this._changed}
      ></ha-form>
    `;
  }
}

if (!customElements.get("pareto-card-editor")) {
  customElements.define("pareto-card-editor", ParetoCardEditor);
}
