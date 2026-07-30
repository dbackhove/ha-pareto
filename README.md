# Pareto for Home Assistant

Home Assistant knows everything about your entities except the one thing a
dashboard needs: which of them you actually touch. Pareto watches the service
calls you make yourself and publishes two lists — the ones you use most, and the
ones you used last.

## What counts as usage

A service call counts when Home Assistant recorded a user behind it **and** it
was a direct action rather than a consequence of one. In practice that means
clicking in the web UI, the companion app, or a voice assistant — not
automations, and not the ten follow-on calls a script makes on your behalf.

Not counted, deliberately: HomeKit commands, physical switches, and other
integrations acting on their own. Home Assistant does not attribute those to a
user. Making this configurable is on the roadmap.

**Anything acting through a long-lived access token counts as a human too.**
Every such token belongs to an HA user, so Node-RED, AppDaemon, MCP servers and
most third-party apps produce calls indistinguishable from a real click. If you
run any of those, expect the Top list to include entities you never touch
yourself — use the entity blocklist below as a workaround until a per-user
filter exists.

## Installation

1. Add this repository to HACS as a custom repository (category: Integration).
2. Install **Pareto** and restart Home Assistant.
3. Add the integration under **Settings → Devices & Services**.

The first time Pareto is set up — before anything has ever been recorded — it
imports whatever usage your recorder still holds, normally about ten days, so
the lists are useful immediately rather than after a fortnight of learning.
Later setups and reloads (for instance after an options change) skip this scan
since it would just re-read history it already has; run the
`pareto.import_history` service any time you want to repeat it.

Note that the backfill cannot exclude a script's follow-on calls the way the
live tracker does, because the logbook row that Pareto reads them from does
not carry that information. Those calls are therefore imported even though the
live tracker would have ignored them, so day-1 rankings can look slightly
different from the ranking a week in, once the backfilled days have aged out
and only live-tracked days remain.

## Entities

| Entity | State | Attribute `entities` |
|---|---|---|
| `sensor.pareto_top` | Number of entries | Ranked by decayed usage |
| `sensor.pareto_recent` | Number of entries | Ranked by last use |

Each entry holds `entity_id`, `count`, `last_used`, `pinned`, and — on the top
sensor — `score`.

## Options

| Option | Default | Meaning |
|---|---|---|
| Top count | 10 | Length of the most-used list |
| Recent count | 5 | Length of the recently-used list |
| Half-life | 14 days | How fast past usage loses weight |
| Only these domains | empty | Whitelist; empty allows all |
| Never these domains | empty | Domain blocklist |
| Never these entities | empty | Entity blocklist |
| Always these entities | empty | Pins, shown first, counting towards the numbers above |

## Showing the list

Home Assistant has no native way to build a list of cards from data. `tile` and
`entities` take entity ids you wrote down in advance, and `entity-filter` only
narrows a list that already exists. Turning a ranking into actual tiles
therefore needs a custom card, always. A Pareto card is planned; until it
exists, one of the two below will do.

### Without installing anything

A Markdown card renders the ranking as text:

```yaml
type: markdown
content: |
  {% for e in state_attr('sensor.pareto_top','entities') %}
  {{ loop.index }}. {{ state_attr(e.entity_id,'friendly_name') or e.entity_id }}
     — {{ e.count }}x (score {{ e.score }})
  {% endfor %}
```

### As real tiles, with auto-entities

[auto-entities](https://github.com/thomasloven/lovelace-auto-entities) — HACS,
category Lovelace — can build card configurations from a template, which is
enough to get one working tile per ranked entity:

```yaml
type: custom:auto-entities
show_empty: false
card:
  type: grid
  columns: 2
  square: false
card_param: cards
filter:
  template: |
    {%- for e in state_attr('sensor.pareto_top','entities') -%}
      {{ {'type': 'tile', 'entity': e.entity_id} }},
    {%- endfor -%}
```

`card_param: cards` is the line that is easy to leave out and hard to debug
without: auto-entities writes its generated list into the card's `entities` key
by default, and a grid card has no `entities` — you get an empty card and no
error. Point the template at `sensor.pareto_recent` for the other list. The
template is subscribed over the websocket, so the tiles re-render as soon as
either sensor changes.

Two things to expect once the tiles are on screen. Entities that only ever
arrived through the history import get tiles too — a `binary_sensor` that
changed as a *consequence* of your click, or an `automation` that ran because
of it — and a tile for an automation toggles that automation. The domain
blocklist under Options is the fix. And a tap on one of these tiles is itself
a user service call, so the list feeds itself: whatever reaches the dashboard
gets used more, and stays there. Neither is a reason not to do it, but both
are easier to recognise than to diagnose later.

## Service

`pareto.import_history` re-reads the logbook. It only fills days that hold no
data yet, so running it twice changes nothing and it can never overwrite what
was recorded live.

The call is **restricted to administrators**, and only one import runs at a
time — a second request while one is in progress is declined rather than
queued. A full scan reads the recorder on the same thread pool that serves your
history and logbook views, so an unrestricted version of this would be an easy
way for any account to stall them. Calls made from automations and scripts,
which carry no user, are allowed through as usual.

## How the score works

Every use is bucketed by local day. The score sums those buckets, weighting each
by `0.5 ^ (age_in_days / half_life)`. With the default half-life, something used
twice yesterday outranks something used ten times six weeks ago. The lists are
also recomputed once a day, because decay alone changes the order — otherwise a
quiet week would leave the ranking frozen.

## What Pareto stores, and who can read it

Worth knowing before you install this, because it records something about the
people in your home rather than about your devices.

**On disk.** Counts live in `.storage/pareto_usage`, keyed by entity and by the
Home Assistant **user id** of whoever operated it:

```json
"light.living_room_lamp": {
  "last_used": "2026-07-30T23:41:12+02:00",
  "buckets": { "0123456789ab…": { "2026-07-30": 7, "2026-07-29": 3 } }
}
```

A user id maps back to a real person through Settings → People, so this is a
per-person usage profile in plain text. `.storage/` is part of every Home
Assistant backup, so it travels with any backup you send to cloud storage.
Pareto keeps the per-user split only so a future card can show each household
member their own list; Phase 1 itself always sums across everyone.

Old entries are dropped automatically after `max(90, 6 × half-life)` days.
Removing the integration deletes the file.

**In the UI.** The sensor attributes include `last_used` down to the second,
and Home Assistant states are readable by **every** signed-in account, not just
administrators. In a shared home that means anyone can see when a given entity
was last operated. If that matters to you — guest or child accounts, say —
exclude the entities you would rather not expose.

**What leaves your instance:** nothing. Pareto has no external dependencies
(`"requirements": []`), makes no network calls, and reads the recorder database
only through Home Assistant's own logbook API.

## License

[MIT](LICENSE) © 2026 Daniel Backhove.
