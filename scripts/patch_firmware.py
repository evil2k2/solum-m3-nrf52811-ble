#!/usr/bin/env python3
"""Reproduce the hardware-tested application HEX; Python 3.10+, no dependencies.

Only three bytes of GPL application code are changed. The SoftDevice is not
modified or redistributed in the resulting HEX. See source/THIRD_PARTY.md.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import urllib.request

UPSTREAM_URL = "https://github.com/OpenDisplay/Firmware_NRF/releases/download/1.4/EPD-nRF52-v1.4-sd.hex"
UPSTREAM_SHA256 = "01dce87bc5c8e49b289a2d84d3537f4e8b7b9d377d47892786770598e5758f2c"
APP_START, APP_END = 0x19000, 0x26F77
CHANGES = {
    0x1E996: (0x11, 0x0F),  # Y increase: include SSD1619 model IDs 16 and 17.
    0x1EB20: (0x08, 0x80),  # Refresh: normal BW, inverted red interpretation.
    0x1EBC8: (0x08, 0x80),  # Init: same display update control.
}


def parse_hex(raw: bytes) -> dict[int, int]:
    memory: dict[int, int] = {}
    upper = 0
    eof = False
    for number, line in enumerate(raw.decode("ascii").splitlines(), 1):
        if not line:
            continue
        if eof or not line.startswith(":"):
            raise ValueError(f"Invalid HEX record at line {number}")
        record = bytes.fromhex(line[1:])
        if len(record) < 5 or len(record) != record[0] + 5 or sum(record) & 255:
            raise ValueError(f"Invalid length/checksum at line {number}")
        count, address, kind = record[0], int.from_bytes(record[1:3], "big"), record[3]
        payload = record[4:-1]
        if kind == 0:
            for i, value in enumerate(payload):
                target = upper + address + i
                if target in memory and memory[target] != value:
                    raise ValueError("Conflicting HEX data")
                memory[target] = value
        elif kind == 1:
            if count != 0:
                raise ValueError("Invalid EOF")
            eof = True
        elif kind == 4:
            if count != 2:
                raise ValueError("Invalid linear address record")
            upper = int.from_bytes(payload, "big") << 16
        elif kind == 5:
            if count != 4:
                raise ValueError("Invalid start address record")
        else:
            raise ValueError(f"Unsupported record type {kind}")
    if not eof or not memory:
        raise ValueError("Incomplete or empty HEX")
    return memory


def record(kind: int, address: int, payload: bytes) -> str:
    body = bytes([len(payload)]) + address.to_bytes(2, "big") + bytes([kind]) + payload
    return ":" + (body + bytes([-sum(body) & 255])).hex().upper()


def encode_hex(memory: dict[int, int]) -> bytes:
    addresses = sorted(memory)
    if not addresses:
        raise ValueError("Cannot encode an empty application")
    lines: list[str] = []
    upper = None
    i = 0
    while i < len(addresses):
        address = addresses[i]
        if address >> 16 != upper:
            upper = address >> 16
            lines.append(record(4, 0, upper.to_bytes(2, "big")))
        block = bytearray()
        while i < len(addresses) and len(block) < 16:
            current = addresses[i]
            if current != address + len(block) or current >> 16 != upper:
                break
            block.append(memory[current])
            i += 1
        lines.append(record(0, address & 65535, bytes(block)))
    lines.append(record(1, 0, b""))
    return ("\n".join(lines) + "\n").encode("ascii")


def patch(raw: bytes) -> dict[int, int]:
    if hashlib.sha256(raw).hexdigest() != UPSTREAM_SHA256:
        raise ValueError("Input is not the exact pinned upstream 1.4-sd.hex")
    original = parse_hex(raw)
    if min(original) != 0 or max(original) != APP_END:
        raise ValueError("Unexpected upstream address range")
    result = {a: v for a, v in original.items() if APP_START <= a <= APP_END}
    for address, (before, after) in CHANGES.items():
        if result.get(address) != before:
            raise ValueError(f"Unexpected instruction at 0x{address:X}")
        result[address] = after
    differences = {a for a, v in result.items() if original[a] != v}
    if differences != set(CHANGES) or len(result) != APP_END - APP_START + 1:
        raise ValueError("Unexpected application layout or changes")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", type=Path, help="Pinned upstream -sd.hex")
    source.add_argument("--download", action="store_true", help="Download pinned upstream release")
    parser.add_argument("--output", type=Path, default=Path("OpenDisplay-v1.4-panel-fix.hex"))
    parser.add_argument("--compare", type=Path, help="Compare address/data bytes against an existing HEX")
    args = parser.parse_args()
    if args.download:
        with urllib.request.urlopen(UPSTREAM_URL, timeout=60) as response:
            raw = response.read()
    else:
        raw = args.input.read_bytes()
    result = patch(raw)
    output = encode_hex(result)
    if parse_hex(output) != result:
        raise ValueError("HEX round-trip failed")
    if args.compare and parse_hex(args.compare.read_bytes()) != result:
        raise ValueError("Existing firmware does not match")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(output)
    print(f"Wrote {args.output}: {len(result)} application bytes, three corrected instruction bytes")
    print("Flash address range: 0x19000..0x26F77; requires existing S112 7.3.0")
    print("SHA256:", hashlib.sha256(output).hexdigest())


if __name__ == "__main__":
    main()
