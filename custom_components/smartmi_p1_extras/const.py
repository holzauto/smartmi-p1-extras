"""Smartmi P1 local controls."""

DOMAIN = "smartmi_p1_extras"
CONF_DEVICE_ID = "device_id"
CONF_LOCAL_KEY = "local_key"
CONF_PROTOCOL = "protocol_version"
LEGACY_HOMEKIT_DEVICE = "homekit_device"
NAME = "Smartmi P1 Local"
PROTOCOLS = ("3.3", "3.4", "3.5")
DP_POWER = "1"
DP_PM25 = "2"
DP_MODE = "3"
DP_CHILD_LOCK = "7"
DP_SOUND = "101"
DP_PM10 = "102"
DP_TIMER = "103"
DP_FILTER_HOURS = "105"
DP_FILTER_LIFE = "104"
DP_SPEED = "109"
DP_DISPLAY = "110"
# Status query only: null values request the published P1 datapoints without writing them.
P1_QUERY_DPS = ("1", "2", "3", "7", "101", "102", "103", "104", "105", "109", "110")
MODES = ("auto", "sleep", "strong", "manual")
TIMERS = ("0_hour", "1_hour", "2_hour", "4_hour", "8_hour")
DISPLAY_MODES = ("BRIGHTNESS_HIGH", "BRIGHTNESS_LOW", "BRIGHTNESS_OFF", "BRIGHTNESS_AUTO")
