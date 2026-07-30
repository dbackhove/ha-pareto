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
therefore needs a custom card, always. Pareto brings its own.

### The Pareto card

The card ships with the integration and registers itself — there is no second
HACS entry to install and no Lovelace resource to add by hand. Add it to a
dashboard:

```yaml
type: custom:pareto-card
mode: top          # top | recent — default: top
title: Most used   # optional
columns: 2         # optional; responsive when left out
```

Each entry is rendered as Home Assistant's own tile card, so every domain
behaves exactly as it does elsewhere on your dashboard, dialogs included.

Two things it does that the sensors cannot:

**The list is yours.** The sensors count the household; the card ranks what
*you* operated, per signed-in user. Until you have enough history of your own,
it fills the remaining places from the household ranking, so it is useful from
the first minute and personalises itself as it goes.

**You can tidy it.** The pencil in the header turns the tiles into controls for
the list itself: ✕ hides an entry, the pin keeps one at the top, and everything
you have hidden is listed below with a way to bring it back. This is per user,
takes effect immediately, and needs no admin rights — unlike the blocklists
under Options, which are house-wide settings. You will want it: a ranking built
from service calls picks up entities nobody wants a tile for, such as a
`binary_sensor` that changed because of your click, or the `automation` that ran
because of it.

The order is deliberately frozen while you are looking at the card. It is
decided when you open the view and stays put until you come back, so the tile
you are reaching for does not move out from under your finger. States stay live
throughout — it is the ordering that is held still, not the contents.

### Alternatives without the card

Both of these predate the card and still work. They are worth knowing if you
want the ranking somewhere the card does not fit.

A Markdown card renders the ranking as text:

```yaml
type: markdown
content: |
  {% for e in state_attr('sensor.pareto_top','entities') %}
  {{ loop.index }}. {{ state_attr(e.entity_id,'friendly_name') or e.entity_id }}
     — {{ e.count }}x (score {{ e.score }})
  {% endfor %}
```

With [auto-entities](https://github.com/thomasloven/lovelace-auto-entities) —
HACS, category Lovelace — you get real tiles from the household ranking, built
from a template:

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

`card_param: cards` is the line that is easy to leave out and hard to debug
without: auto-entities writes its generated list into the card's `entities` key
by default, and a grid card has no `entities` — you get an empty card and no
error. Point the template at `sensor.pareto_recent` for the other list.

This route shows the household ranking and has no way to tidy it, so the
entities nobody wants a tile for have to go into the blocklists under Options.
And note that a tap on any of these tiles is itself a counted service call, so
the list feeds itself: whatever reaches a dashboard gets used more, and stays
there. The card's edit mode exists for exactly that reason.

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
  "buckets": { "0123456789ab…": { "2026-07-30": 7, "2026-07-29": 3 } },
  "user_last_used": { "0123456789ab…": "2026-07-30T23:41:12+02:00" }
}
```

A user id maps back to a real person through Settings → People, so this is a
per-person usage profile in plain text. `.storage/` is part of every Home
Assistant backup, so it travels with any backup you send to cloud storage. The
per-user split is what lets the card show each household member their own list;
the sensors always sum across everyone.

The same file also holds what each person hid or pinned in their card, under
`prefs`, keyed by user id. Those are preferences rather than usage, but they are
still a record of one person's choices, and they are not expired automatically:
a hidden entry usually has no usage left to expire.

Old entries are dropped automatically after `max(90, 6 × half-life)` days.
Removing the integration deletes the file.

**In the UI.** The sensor attributes include `last_used` down to the second,
and Home Assistant states are readable by **every** signed-in account, not just
administrators. In a shared home that means anyone can see when a given entity
was last operated. If that matters to you — guest or child accounts, say —
exclude the entities you would rather not expose.

**The card's API.** `pareto/lists` answers with the calling account's own list
and its own hidden entries, and `pareto/set_pref` writes only under the calling
account. Both take the identity from the authenticated connection, never from
the message, so one account cannot read or rewrite another's. Neither requires
administrator rights: they touch nothing outside the caller's own preferences.

**What leaves your instance:** nothing. Pareto has no external dependencies
(`"requirements": []`), makes no network calls, and reads the recorder database
only through Home Assistant's own logbook API.

## License

[MIT](LICENSE) © 2026 Daniel Backhove.
