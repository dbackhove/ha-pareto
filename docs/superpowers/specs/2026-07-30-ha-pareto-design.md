# Pareto — Design (Phase 1: Backend)

**Datum:** 2026-07-30
**Status:** Freigegeben
**Repo:** `ha-pareto` (public auf GitHub geplant)
**HA-Domain:** `pareto`

> Dieses Dokument ist auf Deutsch, weil es Arbeitsgrundlage ist. Code, Kommentare,
> README und `strings.json` werden auf Englisch geschrieben, mit deutscher
> Übersetzung in `translations/de.json` — das Repo ist für die HACS-Community gedacht.

## 1. Ziel

Home Assistant weiß nicht, welche Entities ein Mensch tatsächlich bedient. In einer
gewachsenen Installation stehen ein paar Dutzend real genutzte Entities Tausenden
gegenüber, die nur Daten liefern. Dashboards werden deshalb von Hand kuratiert und
veralten.

Pareto zählt mit, welche Entities über Home Assistant bedient werden, und stellt
zwei gerankte Listen bereit:

- **Top X** — die am häufigsten bedienten Entities, zeitlich gewichtet
- **Recent X** — die zuletzt bedienten Entities

Diese Listen sind die Datengrundlage für eine Dashboard-Kachel, die sich selbst
aktuell hält.

**Referenzinstallation** (Grundlage aller Dimensionierungen): HA 2026.7.4, 1.785
Entities, 35 Domains, 15 Bereiche, 2 Personen, ~21.600 Logbuch-Einträge pro Tag,
Recorder-Retention ~10 Tage (HA-Default `purge_keep_days`).

## 2. Scope

### In Phase 1

Vollständige Backend-Integration: Erfassung, Persistenz, Scoring, Konfiguration,
Backfill, zwei Sensor-Entities. Installierbar über HACS.

### Explizit Phase 2 (eigener Spec-Zyklus)

Eine eigene Lovelace-Card. Sie wird erst gebaut, wenn die Ranglisten im Alltag
belegen, dass sie brauchbare Ergebnisse liefern. HACS erlaubt pro Repository nur
eine Kategorie; die Card wird deshalb von der Integration selbst als statische
Ressource ausgeliefert und registriert (Vorbild: Browser Mod), nicht als zweiter
HACS-Eintrag.

### Nicht in diesem Projekt

- Automatisches Erzeugen oder Verändern von Dashboards
- Auswertungen jenseits von Häufigkeit und Aktualität (Tageszeit, Korrelationen)
- Export der Nutzungsdaten

## 3. Erfassung

### Signal

Listener auf `EVENT_CALL_SERVICE`. Ein Aufruf zählt genau dann als Bedienung, wenn

```python
event.context.user_id is not None    # ein Mensch, keine Automation
and event.context.parent_id is None  # eine direkte Aktion, keine Folgewirkung
```

Die zweite Bedingung ist nicht optional. Home Assistant vererbt den Kontext: Startet
ein Mensch ein Skript, das fünf Lampen schaltet, tragen alle fünf Folgeaufrufe
dieselbe `user_id` — aber mit gesetzter `parent_id`. Ohne den Filter würde ein
einzelner Klick als sechs Bedienungen gezählt und die Top-Liste von Entities
dominiert, die nie direkt angefasst werden.

Belegt in der Referenzinstallation, Logbuch-Eintrag einer manuell geschalteten Lampe:

```json
{ "entity_id": "light.stehlampe_wohnzimmer", "state": "on",
  "context_user_id": "69d919fb68524e7086650439297dd452",
  "context_domain": "light", "context_service": "turn_on",
  "context_event_type": "call_service" }
```

### Auflösung der Ziel-Entities

Über `homeassistant.helpers.service.async_extract_referenced_entity_ids`. Damit
werden auch Aufrufe auf Bereich, Gerät oder Label korrekt aufgelöst, nicht nur auf
`entity_id`. Jede aufgelöste Entity bekommt einen Zähler.

### Verworfene Alternative

Listener auf `EVENT_STATE_CHANGED` mit demselben Kontextfilter. Wäre einfacher — die
betroffenen Entities stehen direkt im Event, keine Target-Auflösung nötig. Zwei
Gründe dagegen:

1. **No-Ops verschwinden.** „An" auf eine bereits eingeschaltete Lampe erzeugt keinen
   State-Change. Die Bedienung fand statt, würde aber nicht gezählt.
2. **Gruppen verzerren.** Ein Klick auf eine Lichtgruppe erzeugt ein Event je
   Mitglied — dieselbe Fehlgewichtung wie bei der Kontext-Vererbung, nur ohne
   sauberen Filter dagegen.

### Service-Blacklist (fest verdrahtet, wirkt auf die Erfassung)

Nicht zu verwechseln mit der konfigurierbaren Entity-/Domain-Blocklist aus
Abschnitt 7: Die hier ist im Code festgelegt, betrifft **Services** und verhindert,
dass ein Ereignis überhaupt gezählt wird. Die andere ist Benutzereinstellung,
betrifft **Entities** und blendet nur die Ausgabe aus.

Gemeint sind technische Aufrufe, die beim Konfigurieren entstehen, ohne dass eine
Entity „benutzt" wird:

| Regel | Beispiele |
|---|---|
| Blockierte Domains | `persistent_notification`, `recorder`, `system_log`, `frontend`, `pareto` |
| Blockierte Services | `homeassistant.update_entity`, `logbook.log` |
| Namensmuster | Service heißt `reload` oder beginnt mit `reload_` |

Aufrufe ohne aufgelöste Ziel-Entities (z. B. `notify.*`) fallen ohnehin heraus.

## 4. Datenmodell

Persistenz über HAs `Store`-Helper unter `.storage/pareto_usage`, versioniert für
spätere Migrationen. Geschrieben wird über `async_delay_save` mit 60 s Verzögerung:
Ein Burst — etwa eine Lichtszene durchklicken — erzeugt so einen Write statt zwanzig.
Auf SD-Karte oder SSD ist das Lebensdauer, kein Detail.

```json
{
  "version": 1,
  "data": {
    "light.stehlampe_wohnzimmer": {
      "last_used": "2026-07-30T14:05:12+02:00",
      "buckets": {
        "69d919fb68524e7086650439297dd452": { "2026-07-30": 3, "2026-07-29": 1 },
        "a3f1c2...": { "2026-07-28": 2 }
      }
    }
  }
}
```

**Entity außen, User innen.** Phase 1 summiert über alle User-Buckets. Phase 2 greift
für persönliche Listen nur einen Schlüssel tiefer — ohne Datenmigration und ohne
erneutes Sammeln.

**Bucket-Grenze ist lokale Mitternacht** (`hass.config.time_zone`), nicht UTC. Sonst
fallen im Sommer alle Bedienungen nach 23:00 Uhr auf den Folgetag — genau die
Abendstunden mit der höchsten Aktivität.

`last_used` wird über alle User hinweg geführt (jüngster Zeitpunkt gewinnt) und ist
die alleinige Sortiergrundlage für die Recent-Liste.

## 5. Scoring

```
score(entity) = Σ  count(tag) × 0.5 ^ (alter_in_tagen / halbwertszeit)
```

`alter_in_tagen` ist die Differenz zum heutigen lokalen Datum. Halbwertszeit ist
konfigurierbar, Default 14 Tage.

**Pruning:** Buckets älter als `max(90, 6 × halbwertszeit)` Tage werden verworfen. Ab
dort trägt ein Eintrag unter 1,5 % zum Score bei. Läuft beim täglichen Recompute.

**Recent** braucht kein Scoring: nach `last_used` absteigend sortieren.

Die beiden Listen sind unabhängig; eine Entity darf in beiden stehen.

### Zwei Auslöser für die Neuberechnung

| Auslöser | Warum |
|---|---|
| Erfasstes Event, 5 s entprellt | Neue Nutzung kann die Reihenfolge ändern |
| Einmal täglich kurz nach lokaler Mitternacht | Der Verfall allein verschiebt Ränge — auch ohne jede Nutzung |

Ohne den zweiten Auslöser friert die Liste in einer Urlaubswoche ein.

## 6. Ausgabe

Zwei Sensor-Entities. HA begrenzt State-Werte auf 255 Zeichen, eine Liste passt dort
nicht hinein — der State trägt die Anzahl, die Nutzlast liegt im Attribut.

`sensor.pareto_top` und `sensor.pareto_recent`:

```yaml
state: 10
attributes:
  entities:
    - entity_id: light.stehlampe_wohnzimmer
      score: 7.32          # verfallsgewichtet, nur bei pareto_top
      count: 12            # roher Zähler, für die Anzeige
      last_used: "2026-07-30T14:05:12+02:00"
      pinned: false
```

`score` entfällt in `sensor.pareto_recent`, dort ist es bedeutungslos.

### Filter-Pipeline

```
erfasste Entities
  → Domain-Whitelist anwenden (leer = alle durchlassen)
  → Blocklist abziehen (Entities und Domains)
  → nach Score bzw. last_used sortieren
  → Pins voranstellen, dedupliziert, in konfigurierter Reihenfolge
  → nicht mehr existierende Entities verwerfen
  → auf X kürzen
```

Zwei bewusste Festlegungen:

- **Pins zählen gegen X.** Bei X=10 und 3 Pins bleiben 7 automatische Plätze. Sonst
  sprengt die Kachel ihre Größe.
- **Pins stammen aus der Konfiguration, nicht aus den Nutzungsdaten.** Eine gepinnte
  Entity erscheint auch dann, wenn sie nie bedient wurde — das ist ihr Zweck.
  Gepinnte Einträge tragen `pinned: true` und `count`/`score` aus den Nutzungsdaten,
  sofern vorhanden, sonst `0`.

Der Schritt „nicht mehr existierende Entities verwerfen" (`hass.states.get(...) is
None`) verhindert Karteileichen nach Umbenennung oder Löschung. Die Nutzungsdaten
selbst bleiben erhalten — eine kurzzeitig nicht geladene Integration soll keine
Historie vernichten.

## 7. Konfiguration

Config-Flow mit Single-Instance-Sperre (`async_set_unique_id` +
`_abort_if_unique_id_configured`); der Setup-Schritt selbst braucht keine Eingaben.
Alles Weitere im Options-Flow, jederzeit änderbar:

| Option | Selector | Default | Wirkung |
|---|---|---|---|
| `top_count` | Number 1–50 | 10 | Länge der Top-Liste |
| `recent_count` | Number 1–50 | 5 | Länge der Recent-Liste |
| `half_life_days` | Number 1–90 | 14 | Halbwertszeit des Verfalls |
| `include_domains` | Select, multiple | `[]` | Whitelist; leer = alle Domains |
| `exclude_domains` | Select, multiple | `[]` | Domain-Blocklist |
| `exclude_entities` | Entity, multiple | `[]` | Entity-Blocklist |
| `pinned_entities` | Entity, multiple | `[]` | Immer anzeigen, in dieser Reihenfolge |

Optionsänderungen lösen einen Reload des Config-Entries aus; Nutzungsdaten bleiben
unangetastet. Blocklist und Whitelist wirken nur auf die **Ausgabe**, nicht auf die
Erfassung — so kann eine Entity später wieder eingeblendet werden, ohne dass ihre
Historie fehlt.

## 8. Backfill

Läuft beim Setup automatisch als Hintergrund-Task und ist zusätzlich als Service
`pareto.import_history` (optionaler Parameter `days`) jederzeit erneut auslösbar.

**Quelle:** die interne Python-API des Logbooks (`logbook.processor.async_get_events`),
nicht die REST-Schnittstelle. Gelesen wird in Tagesscheiben. Grund: Bei der Recherche
lieferte dieselbe Entity über die REST-API je nach Fenstergröße widersprüchliche
Ergebnisse (72 h → 2 Treffer, 240 h → 1 anderer Treffer). Chunking macht das
Verhalten vorhersagbar und begrenzt den Speicherbedarf.

**Gefiltert wird** auf `context_event_type == "call_service"` mit gesetzter
`context_user_id` — dieselbe Semantik wie die Live-Erfassung, soweit das Logbuch sie
hergibt.

**Idempotenz-Regel: Der Import schreibt ausschließlich in Tages-Buckets, die noch
nicht existieren.** Das löst drei Probleme mit einer Regel:

- Ein zweiter Lauf verdoppelt keine Zahlen.
- Live erfasste Daten werden nie überschrieben.
- Ein abgebrochener Import wird beim Wiederholen genau dort ergänzt, wo er endete.

**Reichweite:** Begrenzt durch die Recorder-Retention, in der Referenzinstallation
~10 Tage. Bei 14 Tagen Halbwertszeit ist das trotzdem substanziell — die Liste ist ab
Tag 1 brauchbar statt erst nach ein bis zwei Wochen.

**Fehlertoleranz:** Der gesamte Import liegt in einem `try/except`. Scheitert er,
erscheint eine Warnung im Log und Pareto läuft normal weiter. Fehlt der Recorder
ganz, wird der Import übersprungen. Nach Abschluss eine persistente Notification mit
der Anzahl importierter Bedienungen — der Job läuft im Hintergrund, sonst bleibt sein
Ende unsichtbar.

## 9. Fehlerbehandlung

| Fall | Verhalten |
|---|---|
| Store beschädigt oder nicht lesbar | Warnung im Log, mit leerem Datensatz starten, nicht crashen |
| Store-Version unbekannt (neuer als Code) | Setup abbrechen mit klarer Meldung, Daten nicht anfassen |
| Entity aus Config existiert nicht | Beim Rendern überspringen, keine Fehlermeldung |
| Recorder/Logbook nicht verfügbar | Backfill überspringen, Live-Erfassung läuft |
| Target-Auflösung wirft | Event verwerfen, auf Debug-Level loggen |

Ein einzelnes fehlerhaftes Event darf den Listener nie beenden.

## 10. Dateistruktur

```
custom_components/pareto/
  __init__.py          Setup, Listener-Registrierung, Service-Registrierung
  const.py             Domain, Defaults, Blacklists
  config_flow.py       Setup- und Options-Flow
  tracker.py           Event-Listener, Kontextfilter, Buckets schreiben
  store.py             Persistenz, Pruning, Migration
  ranking.py           Decay-Score, Filter-Pipeline, Pins
  importer.py          Backfill aus dem Logbook
  sensor.py            sensor.pareto_top, sensor.pareto_recent
  services.yaml
  manifest.json
  strings.json
  translations/en.json
  translations/de.json
hacs.json
README.md
```

**`ranking.py` hat keine Home-Assistant-Abhängigkeit.** Es nimmt ein Dict aus
Nutzungsdaten plus Konfiguration und gibt sortierte Listen zurück. Das ist der
wichtigste Schnitt im Entwurf: Decay-Mathematik und Sortierreihenfolge sind das, was
am ehesten falsch wird, und sie sind so mit gewöhnlichen Unit-Tests ohne HA-Fixtures
prüfbar.

`manifest.json` verwendet `after_dependencies: ["recorder", "logbook"]`, nicht
`dependencies`. Pareto lädt damit nach dem Recorder, wenn dieser vorhanden ist,
funktioniert aber auch ohne ihn — nur eben ohne Backfill. `iot_class` ist
`calculated`, `config_flow` ist `true`.

Beim Anlegen des Repos sind `codeowners`, `documentation` und `issue_tracker` im
Manifest auf das reale GitHub-Konto zu setzen.

## 11. Tests

`pytest` mit `pytest-homeassistant-custom-component`. Schwerpunkt auf den Stellen, an
denen dieser Entwurf fehleranfällig ist:

- **Kontextfilter:** `user_id` gesetzt und `parent_id is None` → gezählt;
  `parent_id` gesetzt → nicht gezählt; `user_id is None` → nicht gezählt.
- **Target-Auflösung:** Aufruf auf einen Bereich zählt alle Entities des Bereichs
  je einmal.
- **Blacklist:** `homeassistant.update_entity` und `automation.reload` zählen nicht.
- **Decay:** Score gegen handgerechnete Werte bei fester Halbwertszeit.
- **Bucket-Grenze:** Bedienung um 23:30 Uhr Ortszeit landet im Bucket desselben
  lokalen Tages (eingefrorene Zeit, Zeitzone Europe/Berlin).
- **Filter-Pipeline:** Reihenfolge von Whitelist, Blocklist, Pins und Kürzung; Pins
  zählen gegen X; Pin ohne Nutzungshistorie erscheint mit `count: 0`.
- **Import-Idempotenz:** zweimaliger Lauf über dieselbe Periode → identische Zahlen.
- **Import kollidiert nicht mit Live-Daten:** existierender Bucket bleibt unverändert.
- **Robustheit:** beschädigter Store → leerer Start statt Crash.
- **Täglicher Recompute:** ohne neue Events ändert sich nach Zeitsprung die
  Reihenfolge erwartungsgemäß.

## 12. Sichtbarkeit in Phase 1

Bis es die Card gibt, genügt eine Markdown-Card zum Beurteilen der Ranglisten:

```yaml
type: markdown
content: |
  {% for e in state_attr('sensor.pareto_top','entities') %}
  {{ loop.index }}. {{ state_attr(e.entity_id,'friendly_name') or e.entity_id }}
     — {{ e.count }}× (Score {{ e.score }})
  {% endfor %}
```

Wer die Entities schon bedienen will, kann dieselben Daten über die vorhandene
`auto-entities`-Card als echte Kacheln rendern.

## 13. Bekannte Einschränkung

**Zugriffe über API-Tokens zählen wie Bedienungen.** Jeder Long-Lived Access Token
gehört zu einem HA-Benutzer. Schaltet ein Skript, ein Sprachassistent oder ein
MCP-Server über einen solchen Token eine Lampe, ist `context.user_id` gesetzt und
`parent_id` leer — die Aktion ist von einem echten Klick nicht unterscheidbar. In der
Referenzinstallation ist ein MCP-Server aktiv, das ist also real.

Für Phase 1 wird das bewusst in Kauf genommen; die Entity-Blocklist reicht als
Notbehelf. Ein Filter auf User-IDs steht unter Future Work.

## 14. Future Work

In dieser Reihenfolge zu erwägen, keine Zusagen:

1. **Eigene Lovelace-Card** (Phase 2) — der eigentliche Zweck des Ganzen. Kann über
   `hass.user.id` persönliche Listen zeigen; das Datenmodell trägt das bereits.
2. **Erweiterbare Signalquellen** — optional auch HomeKit-Kommandos, physische
   Zigbee-Taster und andere Integrationen als „menschliche Bedienung" werten. In der
   Referenzinstallation belegt: ein HomeKit-Schaltvorgang erscheint als
   `context_event_type: "homekit_state_change"` ganz ohne `context_user_id`, ist aber
   zweifelsfrei ein Mensch gewesen. Aus der Brainstorming-Runde bewusst zurückgestellt.
3. **User-ID-Filter** — einzelne HA-Benutzer von der Erfassung ausnehmen, um das
   Token-Problem aus Abschnitt 13 sauber zu lösen.
4. **Bereichsbezogene Listen** — Top X je Bereich statt global.

## 15. Erfolgskriterien für Phase 1

1. Nach der Installation enthalten beide Sensoren plausible Listen — ohne Wartezeit,
   dank Backfill.
2. Ein Skript mit fünf Lampen erzeugt genau eine gezählte Bedienung, nicht sechs.
3. Die Top-Liste besteht überwiegend aus Entities, die Daniel wiedererkennt.
4. Die Reihenfolge verändert sich über Wochen sichtbar, ohne bei Nichtbenutzung
   einzufrieren.
5. Ein zweiter Import-Lauf verändert keine Zahl.
