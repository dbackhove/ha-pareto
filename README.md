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

## Installation

1. Add this repository to HACS as a custom repository (category: Integration).
2. Install **Pareto** and restart Home Assistant.
3. Add the integration under **Settings → Devices & Services**.

On setup, Pareto imports whatever usage your recorder still holds — normally
about ten days — so the lists are useful immediately rather than after a
fortnight of learning.

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
