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

A card is planned. Until then, a Markdown card is enough to see the ranking:

```yaml
type: markdown
content: |
  {% for e in state_attr('sensor.pareto_top','entities') %}
  {{ loop.index }}. {{ state_attr(e.entity_id,'friendly_name') or e.entity_id }}
     — {{ e.count }}x (score {{ e.score }})
  {% endfor %}
```

## Service

`pareto.import_history` re-reads the logbook. It only fills days that hold no
data yet, so running it twice changes nothing and it can never overwrite what
was recorded live.

## How the score works

Every use is bucketed by local day. The score sums those buckets, weighting each
by `0.5 ^ (age_in_days / half_life)`. With the default half-life, something used
twice yesterday outranks something used ten times six weeks ago. The lists are
also recomputed once a day, because decay alone changes the order — otherwise a
quiet week would leave the ranking frozen.

## License

[MIT](LICENSE) © 2026 Daniel Backhove.
