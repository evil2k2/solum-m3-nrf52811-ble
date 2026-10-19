# Attribution and retained licenses

The firmware/application originates from OpenDisplay/Firmware_NRF release 1.4, commit `71b870c12855b2bab4db11fdf1fb213818f3f3a8`, itself derived from tsl0922/EPD-nRF5. Its top-level GPL-3.0 license is reproduced as this project's LICENSE. All original notices are retained in the source archive.

The upstream SDK contains Nordic Semiconductor and other third-party components under their own notices. Nordic nrfx's license is separately reproduced in NORDIC-NRFX-LICENSE.txt; consult the SDK files for their applicable notices. This project is intended for the Nordic nRF52811. Do not treat the top-level GPL notice as relicensing third-party SDK code.

The S112 SoftDevice is downloaded from the upstream release for installation; this repository's HEX does not contain it. No SoftDevice bytes or Nordic binary-library bytes are modified by the patch: the changed instruction locations are in the application's SSD16xx driver. The source archive retains upstream binary libraries and associated notices required by its original build layout.

The upstream public example signing key is omitted, because this application-only procedure does not need an OTA signing key. User-specific factory flash/UICR dumps, pairing data, account details, encryption keys and browser screenshots are not included.

Photos were provided by the repository owner and published at their request. Metadata was removed without recompressing or modifying the image pixels. Photos do not inherit the firmware's GPL license; no separate photo reuse license is specified.
