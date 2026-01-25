"""Constants for the Consul Smart Beer integration."""

from typing import Final

DOMAIN: Final = "consul_smart_beer"

# Configuration keys
CONF_BRAND: Final = "brand"

# Default values
DEFAULT_SCAN_INTERVAL: Final = 30

# Temperature settings for Smart Beer (TED refrigerator)
# Maps user-friendly temperatures (°C) to API values
TEMP_MAP: dict[int, int] = {
    -4: 12,
    -2: 11,
    0: 10,
    3: 9,
    5: 8,
}

# Reverse map for API value to temperature
TEMP_MAP_REVERSE: dict[int, int] = {v: k for k, v in TEMP_MAP.items()}

# Valid temperature values
TEMP_MIN: Final = -4
TEMP_MAX: Final = 5
TEMP_STEP: Final = 1

# API attribute names
ATTR_TEMP: Final = "Refrigerator_OpSetTempPreset"
ATTR_DISPLAY_LOCK: Final = "Sys_OpSetControlLock"
ATTR_TURBO_MODE: Final = "Sys_OpSetMaxCool"
ATTR_ONLINE: Final = "Online"

# Attribute values
ATTR_VALUE_ON: Final = "1"
ATTR_VALUE_OFF: Final = "0"
