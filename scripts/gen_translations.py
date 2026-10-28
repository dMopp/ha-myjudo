"""Generate strings.json and translations/*.json for the myjudo integration."""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent / "custom_components" / "myjudo"

# Message code mapped to the English and German text
MESSAGES = {
    "w_20": ("Leakage protection closed", "Leckageschutz geschlossen"),
    "w_21": (
        "Leakage protection closed: max. quantity exceeded",
        "Leckageschutz geschlossen: max. Entnahmemenge überschritten",
    ),
    "w_22": (
        "Leakage protection closed: max. duration exceeded",
        "Leckageschutz geschlossen: max. Entnahmedauer überschritten",
    ),
    "w_23": (
        "Leakage protection closed: max. flow exceeded",
        "Leckageschutz geschlossen: max. Durchfluss überschritten",
    ),
    "w_24": ("Leak sensor reports a leak", "Leckagesensor meldet Leckage"),
    "w_26": ("Leakage protection in sleep mode", "Leckageschutz im Sleepmode"),
    "w_27": ("Maintenance due", "Wartung fällig"),
    "w_28": ("Check salt supply", "Salzvorrat prüfen"),
    "w_29": ("Salt shortage", "Salzmangel"),
    "w_30": ("Regeneration running", "Regeneration läuft"),
    "w_31": ("Battery low", "Batterie schwach"),
    "w_32": ("Battery empty", "Batterie leer"),
    "w_40": (
        "Fault: regeneration drive defective",
        "Störung: Regenerationsantrieb defekt",
    ),
    "w_41": ("Fault: brine level too high", "Störung: Solestand zu hoch"),
    "w_42": ("Fault: filling valve malfunction", "Störung: Füllventil fehlerhaft"),
    "w_43": ("Fault: leakage protection defective", "Störung: Leckageschutz defekt"),
    "w_46": (
        "Leakage protection in special mode",
        "Leckageschutz im Sonderregelungsmodus",
    ),
    "w_51": (
        "Leakage protection: max. quantity exceeded",
        "Leckageschutz: max. Entnahmemenge überschritten",
    ),
    "w_52": (
        "Leakage protection: max. duration exceeded",
        "Leckageschutz: max. Entnahmedauer überschritten",
    ),
    "w_53": (
        "Leakage protection: max. flow exceeded",
        "Leckageschutz: max. Durchfluss überschritten",
    ),
    "w_61": (
        "Filling valve closed: max. filling time exceeded",
        "Füllventil geschlossen: max. Füllzeit überschritten",
    ),
    "w_62": (
        "Filling valve closed: max. filling quantity exceeded",
        "Füllventil geschlossen: max. Füllmenge überschritten",
    ),
    "w_63": (
        "Filling valve closed: max. filling cycles exceeded",
        "Füllventil geschlossen: max. Füllzyklen überschritten",
    ),
    "w_64": ("Cartridge used up", "Patrone verbraucht"),
    "w_65": ("Fault: pressure sensor defective", "Störung: Drucksensor defekt"),
    "w_66": ("Fault: home position", "Störung: Grundstellung"),
    "w_67": ("Fault: keypad defective", "Störung: Tastatur defekt"),
    "w_68": ("Fault: valve leaking", "Störung: Ventil undicht"),
    "w_69": ("Leakage protection in sleep mode", "Leckageschutz im Sleepmode"),
    "w_70": (
        "Leakage protection closed: floor sensor reports a leak",
        "Leckageschutz geschlossen: Bodensensor meldet Leckage",
    ),
    "w_71": (
        "Learning mode: closed, max. quantity exceeded",
        "Lernmodus: geschlossen, max. Entnahmemenge überschritten",
    ),
    "w_72": (
        "Learning mode: closed, max. flow exceeded",
        "Lernmodus: geschlossen, max. Durchfluss überschritten",
    ),
    "w_73": (
        "Learning mode: closed, max. duration exceeded",
        "Lernmodus: geschlossen, max. Entnahmedauer überschritten",
    ),
    "w_74": ("Fault: ball valve defective", "Störung: Kugelventil defekt"),
    "w_151": (
        "Leak alarm: max. quantity exceeded",
        "Leckagealarm: max. Entnahmemenge überschritten",
    ),
    "w_152": (
        "Leak alarm: max. duration exceeded",
        "Leckagealarm: max. Entnahmedauer überschritten",
    ),
    "w_153": (
        "Leak alarm: max. flow exceeded",
        "Leckagealarm: max. Durchfluss überschritten",
    ),
    "w_251": ("Holiday mode: reduced limits", "Urlaubsmodus: reduzierte Grenzwerte"),
    "w_253": (
        "Holiday mode: leakage protection closed",
        "Urlaubsmodus: Leckageschutz geschlossen",
    ),
    "e_1": ("Error: regeneration drive", "Fehler: Regenerationsantrieb"),
    "e_2": ("Error: brine level high", "Fehler: Solestand hoch"),
    "e_3": ("Error: refilling", "Fehler: Nachfüllen"),
    "e_4": ("Error: water stop drive", "Fehler: Wasserstopp-Antrieb"),
    "e_5": ("Error: VSV", "Fehler: VSV"),
    "e_6": ("Error: conductivity measurement", "Fehler: Leitwertmessung"),
    "e_7": ("Error: temperature measurement", "Fehler: Temperaturmessung"),
    "e_8": ("Error: soft water meter", "Fehler: Weichwasserzähler"),
    "e_9": ("Error: raw water meter", "Fehler: Rohwasserzähler"),
    "e_10": (
        "Error: raw hardness below twice the target",
        "Fehler: Rohhärte kleiner 2x Wunschhärte",
    ),
    "e_11": (
        "Error: level sensor not detected",
        "Fehler: Füllstandssensor nicht erkannt",
    ),
    "e_12": (
        "Error: upper level sensor always wet",
        "Fehler: oberer Füllstandssensor dauernd nass",
    ),
    "e_13": (
        "Error: level sensors (double fault)",
        "Fehler: Füllstandssensoren (Doppelfehler)",
    ),
    "e_14": ("Error: RS-485 connection", "Fehler: RS-485-Verbindung"),
    "other": ("Other message", "Sonstige Meldung"),
}

ENTITIES = {
    "binary_sensor": {
        "online": ("Cloud connection", "Cloud-Verbindung"),
        "regeneration_running": ("Regeneration", "Regeneration"),
    },
    "button": {"start_regeneration": ("Start regeneration", "Regeneration starten")},
    "number": {
        "output_hardness": ("Target hardness", "Wunschwasserhärte"),
        "salt_stock": ("Salt stock", "Salzvorrat"),
        "sleep_mode": ("Sleep mode", "Sleepmode"),
        "max_flow": ("Max. flow", "Max. Durchfluss"),
        "extraction_quantity": ("Max. extraction quantity", "Max. Entnahmemenge"),
        "extraction_time": ("Max. extraction time", "Max. Entnahmedauer"),
    },
    "select": {"holiday_mode": ("Holiday mode", "Urlaubsmodus")},
    "sensor": {
        "total_water": ("Total water", "Gesamtwasser"),
        "soft_water": ("Soft water", "Weichwasser"),
        "hard_water": ("Hard water", "Hartwasser"),
        "water_flow": ("Water flow", "Durchfluss"),
        "input_hardness": ("Raw water hardness", "Rohwasserhärte"),
        "salt_range": ("Salt range", "Salzreichweite"),
        "next_service": ("Next service", "Nächste Wartung"),
        "regeneration_count": ("Regenerations", "Regenerationen"),
        "battery": ("Battery", "Batterie"),
        "last_message": ("Last message", "Letzte Meldung"),
        "last_message_time": ("Last message time", "Zeitpunkt letzte Meldung"),
        "last_update": ("Last device update", "Letzte Geräteaktualisierung"),
        "last_regeneration": ("Last regeneration", "Letzte Regeneration"),
    },
    "valve": {"valve": ("Water supply", "Wasserzufuhr")},
}

HOLIDAY = {
    "off": ("Off", "Aus"),
    "lock": ("Shut off", "Absperren"),
    "mode_1": ("Holiday mode 1", "Urlaubsmodus 1"),
    "mode_2": ("Holiday mode 2", "Urlaubsmodus 2"),
}

TEXT = {
    "config": {
        "step": {
            "user": {
                "description": (
                    "Log in with your myjudo.eu account (the same one the JUDO app uses).",
                    "Mit dem myjudo.eu-Konto anmelden (dasselbe wie in der JUDO-App).",
                ),
                "data": {
                    "username": ("Username", "Benutzername"),
                    "password": ("Password", "Passwort"),
                },
            },
            "reauth_confirm": {
                "title": ("Log in again", "Erneut anmelden"),
                "description": (
                    "The login for {username} was rejected. Enter the current password.",
                    "Die Anmeldung für {username} wurde abgelehnt. Bitte das aktuelle Passwort eingeben.",
                ),
                "data": {"password": ("Password", "Passwort")},
            },
        },
        "error": {
            "invalid_auth": (
                "Username or password is wrong.",
                "Benutzername oder Passwort ist falsch.",
            ),
            "cannot_connect": (
                "myjudo.eu could not be reached.",
                "myjudo.eu ist nicht erreichbar.",
            ),
            "unknown": ("Unexpected error.", "Unerwarteter Fehler."),
        },
        "abort": {
            "already_configured": (
                "This account is already set up.",
                "Dieses Konto ist bereits eingerichtet.",
            ),
            "reauth_successful": ("Login updated.", "Anmeldung aktualisiert."),
        },
    },
    "options": {
        "step": {
            "init": {
                "data": {
                    "scan_interval": ("Update interval", "Abfrageintervall"),
                    "model": ("Model", "Modell"),
                    "sodium_input": ("Sodium in raw water", "Natrium im Rohwasser"),
                    "sodium_limit": ("Sodium limit", "Natrium-Grenzwert"),
                },
                "data_description": {
                    "model": (
                        "Selects which registers are read. Automatic detects a SOFTwell P by its missing leakage protection data.",
                        "Legt fest, welche Register gelesen werden. Automatisch erkennt eine SOFTwell P an den fehlenden Leckageschutz-Daten.",
                    ),
                    "sodium_input": (
                        "Ask your water supplier. 0 turns the sodium check for the target hardness off.",
                        "Beim Wasserversorger erfragen. 0 schaltet die Natrium-Prüfung der Wunschwasserhärte ab.",
                    ),
                    "sodium_limit": (
                        "Target hardness values that would exceed this are refused (Germany: 200 mg/L).",
                        "Wunschwasserhärten, die diesen Wert überschreiten würden, werden abgelehnt (Deutschland: 200 mg/L).",
                    ),
                },
            }
        }
    },
    "exceptions": {
        "auth_failed": (
            "myjudo.eu rejected the login.",
            "myjudo.eu hat die Anmeldung abgelehnt.",
        ),
        "update_failed": (
            "Could not read data from myjudo.eu: {error}",
            "Daten von myjudo.eu nicht lesbar: {error}",
        ),
        "write_failed": (
            "Could not send the command to myjudo.eu: {error}",
            "Befehl an myjudo.eu fehlgeschlagen: {error}",
        ),
        "sodium_limit": (
            "This hardness would give {sodium} mg/L sodium (limit {limit} mg/L). Choose at least {minimum} °dH.",
            "Diese Härte ergäbe {sodium} mg/L Natrium (Grenzwert {limit} mg/L). Mindestens {minimum} °dH wählen.",
        ),
    },
}


MODEL_OPTIONS = {
    "auto": ("Automatic", "Automatisch"),
    "i_soft_safe": ("i-soft safe / safe+", "i-soft safe / safe+"),
    "softwell_p": ("SOFTwell P", "SOFTwell P"),
}


def pick(obj, idx):
    if isinstance(obj, tuple):
        return obj[idx]
    return {k: pick(v, idx) for k, v in obj.items()}


def build(idx):
    out = pick(TEXT, idx)
    entity = {}
    for platform, items in ENTITIES.items():
        entity[platform] = {key: {"name": names[idx]} for key, names in items.items()}
    entity["sensor"]["last_message"]["state"] = {k: v[idx] for k, v in MESSAGES.items()}
    entity["select"]["holiday_mode"]["state"] = {k: v[idx] for k, v in HOLIDAY.items()}
    out["entity"] = entity
    out["selector"] = {
        "model": {"options": {k: v[idx] for k, v in MODEL_OPTIONS.items()}}
    }
    out["exceptions"] = {
        key: {"message": text} for key, text in out["exceptions"].items()
    }
    return out


def dump(path, data):
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


dump(ROOT / "strings.json", build(0))
dump(ROOT / "translations" / "en.json", build(0))
dump(ROOT / "translations" / "de.json", build(1))
