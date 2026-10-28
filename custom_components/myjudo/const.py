"""Constants for the JUDO myjudo integration."""

from typing import Final

DOMAIN: Final = "myjudo"
MANUFACTURER: Final = "JUDO"

CONF_MODEL: Final = "model"
# Replaced by CONF_MODEL in config entry minor version 2
CONF_SOFTWELL_P: Final = "softwell_p"

MODEL_AUTO: Final = "auto"
MODEL_I_SOFT_SAFE: Final = "i_soft_safe"
MODEL_SOFTWELL_P: Final = "softwell_p"
MODELS: Final = [MODEL_AUTO, MODEL_I_SOFT_SAFE, MODEL_SOFTWELL_P]
MODEL_NAMES: Final = {
    MODEL_I_SOFT_SAFE: "i-soft safe / safe+",
    MODEL_SOFTWELL_P: "SOFTwell P",
}
CONF_SODIUM_INPUT: Final = "sodium_input"
CONF_SODIUM_LIMIT: Final = "sodium_limit"

DEFAULT_SCAN_INTERVAL: Final = 30
MIN_SCAN_INTERVAL: Final = 15
DEFAULT_SODIUM_INPUT: Final = 0.0
DEFAULT_SODIUM_LIMIT: Final = 200.0
# Sodium added per °dH of softening (mg/L)
SODIUM_PER_DH: Final = 8.2

# Codes of the device message log, prefixed with their type (w = warning, e = error)
MESSAGE_CODES: Final = [
    *(
        f"w_{code}"
        for code in (
            20,
            21,
            22,
            23,
            24,
            26,
            27,
            28,
            29,
            30,
            31,
            32,
            40,
            41,
            42,
            43,
            46,
            51,
            52,
            53,
            61,
            62,
            63,
            64,
            65,
            66,
            67,
            68,
            69,
            70,
            71,
            72,
            73,
            74,
            151,
            152,
            153,
            251,
            253,
        )
    ),
    *(f"e_{code}" for code in range(1, 15)),
    "other",
]
