# JUDO myjudo for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://hacs.xyz)

Unofficial Home Assistant integration for JUDO water softeners with leakage protection (e.g. **i-soft safe**, **i-soft safe+**, **SOFTwell P**) that are connected to JUDO's **JU-Control** cloud, the same service the [JU-Control app](https://www.ju-control.app) uses.

No MQTT broker, no AppDaemon, no extra hardware: log in with your JU-Control account and the integration polls the cloud. The JU-Control app, ju-control.app and the older myjudo.eu website share the same login and server (`www.myjudo.eu/interface/`), so existing myjudo.eu accounts keep working.

> Not affiliated with or endorsed by JUDO Wasseraufbereitung GmbH. JUDO and the JUDO logo are trademarks of their owner. The JU-Control cloud interface is undocumented and may change at any time.

## Features

| Platform | Entities |
| --- | --- |
| Sensor | Total / soft / hard water (energy dashboard ready), water flow, raw water hardness, salt range, days to next service, regeneration count, battery, last message (translated warning/error), time of last message, last regeneration, last device update |
| Number | Target hardness, salt stock, sleep mode (hours), max. flow, max. extraction quantity, max. extraction time |
| Valve | Water supply (leakage protection valve) open/close |
| Select | Holiday mode (off, shut off, mode 1, mode 2) |
| Button | Start regeneration |
| Binary sensor | Cloud connection, regeneration running |

Entities are only created for values your device reports (e.g. the battery only if a backup battery is fitted). Several devices on one account are supported.

## Installation

### HACS

JUDO myjudo is in the HACS default store, no custom repository needed.

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dMopp&repository=ha-myjudo&category=integration)

1. Click the button above, or search HACS for **JUDO myjudo**.
2. Install it and restart Home Assistant.
3. *Settings → Devices & services → Add integration → JUDO myjudo*.

If you added this repository as a custom repository before it was in the store, you can remove that entry in HACS → ⋮ → *Custom repositories*; the installed integration keeps working.

### Manual

Copy `custom_components/judo_myjudo` into your `config/custom_components` folder and restart Home Assistant.

## Options

| Option | Default | Meaning |
| --- | --- | --- |
| Update interval | 30 s | How often the JU-Control cloud is polled (min. 15 s). |
| Model | Automatic | Selects which registers are read: *i-soft safe / safe+* or *SOFTwell P*. Automatic detects a SOFTwell P by its missing leakage protection data. |
| Sodium in raw water | 0 mg/L | If set, target hardness values that would push sodium over the limit are refused. Ask your water supplier. 0 disables the check. |
| Sodium limit | 200 mg/L | Legal limit in Germany. |

Daily or monthly consumption: create a *Utility meter* helper on the *Total water* sensor.

## Login problems and cloud maintenance

The cloud also rejects valid logins while JUDO maintains its servers. The integration therefore keeps retrying for an hour and only then asks for the password again (a notice appears under *Settings → Devices & services*). As soon as a login works again, the entities come back by themselves and an open password prompt is withdrawn.

## Migrating from the getjudo AppDaemon/MQTT script

1. Install this integration; it creates new entities next to the old MQTT ones.
2. Update automations, dashboards and the energy dashboard to the new entities.
3. Stop the script and delete the old MQTT device. To keep long-term statistics, rename the new *Total water* entity to the old entity ID after the old entity is gone.

## Credits

Register map and commands are based on the community project [Judo-i-soft-save-plus-to-mqtt-bridge](https://github.com/www-ShapeLabs-de/Judo-i-soft-save-plus-to-mqtt-bridge) (getjudo) by ShapeLabs, which reverse-engineered the cloud interface. Login and register decoding were checked against the JU-Control web app. No code from either is included.

Written with the help of an AI assistant.

## License

MIT
