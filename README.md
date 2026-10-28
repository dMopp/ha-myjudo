# JUDO myjudo for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)

Unofficial Home Assistant integration for JUDO water softeners with leakage protection (e.g. **i-soft safe**, **i-soft safe+**, **SOFTwell P**) that are connected to the **myjudo.eu** cloud, the same service the JUDO app uses.

No MQTT broker, no AppDaemon, no extra hardware: log in with your myjudo.eu username and the integration polls the cloud.

> Not affiliated with or endorsed by JUDO Wasseraufbereitung GmbH. JUDO and the JUDO logo are trademarks of their owner. The myjudo.eu interface is undocumented and may change at any time.

## Features

| Platform | Entities |
| --- | --- |
| Sensor | Total / soft / hard water (energy dashboard ready), water flow, raw water hardness, salt range, days to next service, regeneration count, battery, last message (translated warning/error), time of last message, last regeneration, last device update |
| Number | Target hardness, salt stock, sleep mode (hours), max. flow, max. extraction quantity, max. extraction time |
| Valve | Water supply (leakage protection valve) open/close |
| Select | Holiday mode (off, shut off, mode 1, mode 2) |
| Button | Start regeneration |
| Binary sensor | Cloud connection, regeneration running |

Entities are only created for values your device reports. Several devices on one account are supported.

## Installation

### HACS

1. HACS → ⋮ → *Custom repositories* → add `https://github.com/dMopp/ha-myjudo`, category *Integration*.
2. Install **JUDO myjudo** and restart Home Assistant.
3. *Settings → Devices & services → Add integration → JUDO myjudo*.

### Manual

Copy `custom_components/myjudo` into your `config/custom_components` folder and restart Home Assistant.

## Options

| Option | Default | Meaning |
| --- | --- | --- |
| Update interval | 30 s | How often myjudo.eu is polled (min. 15 s). |
| Device is a SOFTwell P | off | SOFTwell P has no leakage protection and stores total water in another register. |
| Sodium in raw water | 0 mg/L | If set, target hardness values that would push sodium over the limit are refused. Ask your water supplier. 0 disables the check. |
| Sodium limit | 200 mg/L | Legal limit in Germany. |

Daily or monthly consumption: create a *Utility meter* helper on the *Total water* sensor.

## Migrating from the getjudo AppDaemon/MQTT script

1. Install this integration; it creates new entities next to the old MQTT ones.
2. Update automations, dashboards and the energy dashboard to the new entities.
3. Stop the script and delete the old MQTT device. To keep long-term statistics, rename the new *Total water* entity to the old entity ID after the old entity is gone.

## Credits

Register map and commands are based on the community project [Judo-i-soft-save-plus-to-mqtt-bridge](https://github.com/www-ShapeLabs-de/Judo-i-soft-save-plus-to-mqtt-bridge) (getjudo) by ShapeLabs, which reverse-engineered the myjudo.eu interface. No code from it is included.

Written with the help of an AI assistant.

## License

MIT
