"""Constants for the Pareto integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "pareto"

STORAGE_KEY: Final = "pareto_usage"
STORAGE_VERSION: Final = 1
SAVE_DELAY: Final = 60
UPDATE_DEBOUNCE: Final = 5

CONF_TOP_COUNT: Final = "top_count"
CONF_RECENT_COUNT: Final = "recent_count"
CONF_HALF_LIFE_DAYS: Final = "half_life_days"
CONF_INCLUDE_DOMAINS: Final = "include_domains"
CONF_EXCLUDE_DOMAINS: Final = "exclude_domains"
CONF_EXCLUDE_ENTITIES: Final = "exclude_entities"
CONF_PINNED_ENTITIES: Final = "pinned_entities"

DEFAULT_TOP_COUNT: Final = 10
DEFAULT_RECENT_COUNT: Final = 5
DEFAULT_HALF_LIFE_DAYS: Final = 14

MIN_RETENTION_DAYS: Final = 90
RETENTION_HALF_LIVES: Final = 6

# Service calls that are configuration plumbing, not "using" an entity.
BLOCKED_DOMAINS: Final = frozenset(
    {"persistent_notification", "recorder", "system_log", "frontend", DOMAIN}
)
BLOCKED_SERVICES: Final = frozenset({"homeassistant.update_entity", "logbook.log"})

SERVICE_IMPORT_HISTORY: Final = "import_history"
ATTR_DAYS: Final = "days"
DEFAULT_IMPORT_DAYS: Final = 10

# The card ships inside the integration -- HACS allows one category per
# repository, so it cannot be a second, Lovelace-category entry.
CARD_FILENAME: Final = "pareto-card.js"
CARD_URL: Final = "/pareto_static/pareto-card.js"
