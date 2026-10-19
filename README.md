# SOLUM M3 2.9″ — Bluetooth reuse guide

Reuse a **SOLUM EL029H3BRA / Newton M3** shelf label as a Bluetooth e-paper display, without an OpenEPaperLink access point.

**[Deutsch: vollständige Anleitung](docs/README.de.md) · [English: complete guide](docs/README.en.md)**

![Working display: black and red on white, correct orientation](docs/images/working-display.jpg)

## Tested hardware / Getestete Hardware

| Item | Confirmed on the tested unit |
|---|---|
| Label | SOLUM EL029H3BRA; FCC family EL029H3WRA; manufactured November 2021 |
| MCU | Nordic nRF52811-QFAA, revision A0; 192 KiB flash, 24 KiB RAM |
| Panel | 2.9″, black/white/red, SSD-family UICR controller code `0x15` |
| Pixels | 168 × 384 in controller coordinates; 384 × 168 landscape |
| Programmer | ST-Link V2 clone, firmware V2J37S7; OpenOCD 0.12.0-1 on Windows |
| BLE firmware | OpenDisplay Firmware_NRF 1.4 + the documented panel correction |
| Result | Bluetooth image transfer, correct B/W/R colors and readable orientation |

**Verified on one physical label.** Matching model names do not guarantee identical hardware. This is an independent community project, not an official SOLUM or OpenDisplay release.

## What is included

- A hardware-tested, **application-only** [HEX file](firmware/OpenDisplay-v1.4-panel-fix.hex).
- A [configuration preset](config/solum-m3-29-ssd1619.json) with display and power blocks, and **no encryption key**.
- A [reproducible patch script](scripts/patch_firmware.py), byte-level checks and [source patch](source/panel-fix.patch).
- A [corresponding source archive](source/OpenDisplay-NRF-1.4-panel-fix-source.tar.gz), including upstream build files and source notices.
- German and English backup, flashing, configuration and troubleshooting instructions.

## What was fixed

The tested upstream binary produced inverted color planes and a horizontal mirror on this panel. The tested correction uses **`0x80` instead of `0x08`** for SSD16xx BWR display-update control, and ascending Y addressing for the SSD1619 2.9″ model IDs. See [technical notes](docs/TECHNICAL.md).

The HEX contains only **`0x19000..0x26F77`**. It requires **SoftDevice S112 7.3.0**, supplied by the pinned upstream `-sd.hex`. Do not flash it by itself onto a factory label. Follow the guide.

## Credits and licensing

The firmware is derived from [OpenDisplay/Firmware_NRF](https://github.com/OpenDisplay/Firmware_NRF), which is based on [tsl0922/EPD-nRF5](https://github.com/tsl0922/EPD-nRF5). [OpenEPaperLink](https://github.com/OpenEPaperLink/OpenEPaperLink) supplied the working hardware reference used during bring-up. Hardware testing and photos: **[@evil2k2](https://github.com/evil2k2)**. Documentation and the panel correction were prepared with Codex assistance.

Firmware/project code: **GPL-3.0**, subject to retained third-party notices. Nordic components retain their own terms and are for Nordic ICs; see [third-party notes](source/THIRD_PARTY.md). Photos are provided by the repository owner with permission to publish; no separate reuse license for the photos is granted here. No user flash dumps, UICR dumps, passwords or encryption keys are included.
