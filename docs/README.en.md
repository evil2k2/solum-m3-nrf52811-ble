# English guide

[Deutsch](README.de.md) · [Project overview](../README.md)

This guide documents a successful Bluetooth conversion of a **SOLUM EL029H3BRA / Newton M3, 2.9-inch** shelf label. The tested unit has an **nRF52811**, SSD-family UICR controller code **`0x15`**, and a black/white/red panel with **384 × 168 landscape pixels**. Hardware can differ between production batches.

## 1. Requirements

- Your own compatible SOLUM label.
- ST-Link V2 with direct DAP support, firmware V2J24 or newer; tested: blue clone with V2J37S7.
- Windows computer with Bluetooth and Chrome or Edge.
- [xPack OpenOCD 0.12.0-1](https://github.com/xpack-dev-tools/openocd-xpack/releases/tag/v0.12.0-1), Windows x64 ZIP, fully extracted.
- [Official ST-Link Windows USB driver](https://www.st.com/en/development-tools/stsw-link009.html), if needed.
- Short wires or spring contacts, and a multimeter.

No ESP32 or OpenEPaperLink access point is required. ST-Link programs the chip; Bluetooth sends images afterwards. This procedure does not install a Bluetooth OTA bootloader. Continue using ST-Link for firmware updates.

## 2. Wiring

![Battery compartment, programming pads at bottom left](images/battery-compartment.jpg)

The following positions refer to this photo orientation: rear battery compartment facing you, programming-pad cluster at bottom left. The top row has three pads with a gap before the rightmost pad, the middle row has two staggered pads, and the bottom row has four.

| Label pad | Signal | Pin on the pictured ST-Link clone |
|---|---|---|
| Top right, isolated | VCC | 7 or 8, **3.3 V** |
| Middle left | SWDIO | 4 |
| Middle right | SWCLK | 2 |
| Bottom right | GND | 5 or 6 |
| Bottom third from left | nRESET | Left disconnected on tested clone |

![Tested ST-Link V2 clone and its printed pinout](images/st-link-v2.jpg)

**Remove the batteries. Verify VCC and ground with a multimeter. Never connect 5 V.** Clone pinouts and power outputs can differ. Some probes only sense the target supply voltage. A clone's RST pin is not necessarily an ARM NRST output.

## 3. Identify and back up the controller

Open PowerShell in OpenOCD's `bin` directory. All relative paths below refer to that directory. Separate `-c` options avoid the command-passing issue observed during this Windows setup.

```powershell
.\openocd.exe -s ..\scripts -f interface/stlink-dap.cfg -c "transport select dapdirect_swd" -f target/nrf52.cfg -c "adapter speed 100" -c "init" -c "mdw 0x10000100 5" -c "shutdown"
```

The tested chip returned:

```text
0x10000100: 00052811 41414130 00002000 00000018 000000c0
```

This identifies an nRF52811 with 24 KiB RAM and 192 KiB flash. If the part differs, access is locked, or commands fail, do not blindly continue. **Do not run `nrf52_recover`: it also erases UICR and is unnecessary for this unlocked unit.**

```powershell
New-Item -ItemType Directory -Force .\display-backup | Out-Null
.\openocd.exe -s ..\scripts -f interface/stlink-dap.cfg -c "transport select dapdirect_swd" -f target/nrf52.cfg -c "adapter speed 100" -c "init" -c "halt" -c "dump_image display-backup/original-flash.bin 0x00000000 0x30000" -c "dump_image display-backup/original-uicr.bin 0x10001000 0x1000" -c "resume" -c "shutdown"
Get-ChildItem .\display-backup | Select-Object Name,Length
```

Expected sizes: `original-flash.bin` **196608 bytes**, `original-uicr.bin` **4096 bytes**. Keep these backups private. They cover the controller's internal storage, not the separate SPI flash, and do not guarantee restoration of the complete factory state.

## 4. Install the Bluetooth base — first conversion only

The application needs the Bluetooth SoftDevice. Download the pinned, unchanged OpenDisplay 1.4 `-sd.hex`:

```powershell
Invoke-WebRequest -Uri "https://github.com/OpenDisplay/Firmware_NRF/releases/download/1.4/EPD-nRF52-v1.4-sd.hex" -OutFile ".\OpenDisplay-v1.4-sd.hex"
if ((Get-FileHash .\OpenDisplay-v1.4-sd.hex -Algorithm SHA256).Hash -ne "01DCE87BC5C8E49B289A2D84D3537F4E8B7B9D377D47892786770598E5758F2C") { throw "Unexpected base firmware" }
```

**The next command erases all internal program flash, including existing OpenDisplay settings. UICR is preserved. Use this only for initial installation, after successful backups.**

```powershell
.\openocd.exe -s ..\scripts -f interface/stlink-dap.cfg -c "transport select dapdirect_swd" -f target/nrf52.cfg -c "adapter speed 100" -c "init" -c "reset init" -c "flash erase_sector 0 0 last" -c "flash write_image OpenDisplay-v1.4-sd.hex 0 ihex" -c "verify_image OpenDisplay-v1.4-sd.hex 0 ihex" -c "verify_image display-backup/original-uicr.bin 0x10001000 bin" -c "reset run" -c "shutdown"
```

Resolve errors before continuing. Do not replace your device's UICR with somebody else's dump.

## 5. Install the tested panel correction

Copy [`OpenDisplay-v1.4-panel-fix.hex`](../firmware/OpenDisplay-v1.4-panel-fix.hex) into the `bin` directory. **This is application-only and requires step 4's base.**

```powershell
.\openocd.exe -s ..\scripts -f interface/stlink-dap.cfg -c "transport select dapdirect_swd" -f target/nrf52.cfg -c "adapter speed 100" -c "program OpenDisplay-v1.4-panel-fix.hex verify reset exit"
```

Expect `Verified OK`. **Do not add a mass erase.** This update touches application pages through `0x26FFF`, not UICR or the configuration pages at the end of flash.

## 6. Configure over Bluetooth

1. Enable Bluetooth and open the [OpenDisplay Toolbox editor](https://opendisplay.org/firmware/toolbox/index.html?mode=edit).
2. Connect to your label. Its individual Bluetooth name starts with **OD**.
3. **Import JSON** → [`solum-m3-29-ssd1619.json`](../config/solum-m3-29-ssd1619.json).
4. Select **Write to device**, disconnect and briefly remove power.
5. Open the [display tester](https://opendisplay.org/firmware/display/index.html), connect and send an image.

The preset includes System, Manufacturer, Power, Display, LED and buttons. Its serialized size is **189 bytes**, below firmware 1.4's **512-byte limit**. There is no Encryption block. Unencrypted operation was the working configuration tested here; it does not require a key for BLE-range control.

Important display fields: **SSD1619 2.9″ B/W/R**, panel ID **1016**, **168 × 384**, MOSI **20**, SCLK **19**, CS **6**, DC **5**, RESET **4**, BUSY **3**, power pin **7**, Direct Write enabled. The controller uses portrait coordinates; use the tester's rotation for landscape content, then resend.

An empty device configuration could cause “Couldn't read its settings” during first setup. The alternate wizard route is “Install OpenDisplay over USB” → “The firmware is already installed”. ST-Link has already installed the firmware; do not reinstall it from the browser.

## 7. Check the result

Send a white image containing black text, red text and asymmetric left/right marks. Check white background, correct ink colors and readable, unmirrored text.

![Confirmed hardware result](images/working-display.jpg)

## Troubleshooting

| Symptom | Observed cause / next step |
|---|---|
| `No AP Found` | Still running OpenEPaperLink, which needs its own AP. Install the BLE firmware. |
| `Config write failed`, 545 bytes | Above 512-byte limit. Remove the entire **Names and strings** packet; clearing its text fields does not shrink it. |
| `No display config found` | Missing Display packet or encrypted bytes misread as plaintext. Inspect the log and exported JSON. |
| Key prompt or nonsensical chunk numbers | Encryption caused problems in the tested web workflow. Remove the Encryption block in the editor, write and fully power-cycle. |
| Red background, then reversed B/W | Install this exact panel correction, rather than selecting a different panel. |
| Mirrored text | This correction enables ascending Y addressing. Rotation alone cannot fix a reflection. |
| `MSD read timeout` | Not sufficient evidence that image upload is broken. Check the display configuration and physical image. |
| Old picture remains without power | Normal for e-paper; a new refresh changes the image. |

An official firmware update may overwrite this local correction. Keep the working HEX and a JSON export before updating. A generic toolbox inch label may be calculated from the preset's active millimeter dimensions; the verified controller and pixel dimensions are what matter.

## Reproduce and develop

See [technical notes](TECHNICAL.md). A standard-library Python script reproduces the exact tested HEX from the checksum-pinned upstream file. The corresponding source archive and patch are included in `source/`. Ubuntu/OpenOCD is another possible host, but this guide's complete end-to-end hardware test used Windows.
