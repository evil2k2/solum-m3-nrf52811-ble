"""Offline integrity checks for the public artifact, not a hardware simulation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("patcher", ROOT / "scripts/patch_firmware.py")
patcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(patcher)


class FirmwareTests(unittest.TestCase):
    def test_image_is_application_only(self):
        image = patcher.parse_hex((ROOT / "firmware/OpenDisplay-v1.4-panel-fix.hex").read_bytes())
        self.assertEqual(min(image), 0x19000)
        self.assertEqual(max(image), 0x26F77)
        self.assertEqual(len(image), 0x26F78 - 0x19000)
        self.assertFalse(any(a >= 0x27000 for a in image))
        self.assertEqual(bytes(image[a] for a in range(0x19000, 0x19004)), b"\x00\x60\x00\x20")
        for address, (_, value) in patcher.CHANGES.items():
            self.assertEqual(image[address], value)

    def test_rejects_corrupt_record(self):
        with self.assertRaises(ValueError):
            patcher.parse_hex(b":0100000000FE\n:00000001FF\n")

    def test_rejects_wrong_upstream_before_patching(self):
        with self.assertRaisesRegex(ValueError, "exact pinned"):
            patcher.patch(b":00000001FF\n")

    def test_round_trip_across_address_boundary(self):
        memory = {0x1FFFE: 10, 0x1FFFF: 20, 0x20000: 30, 0x20001: 40}
        self.assertEqual(patcher.parse_hex(patcher.encode_hex(memory)), memory)

    def test_preset_has_display_power_and_no_secrets(self):
        cfg = json.loads((ROOT / "config/solum-m3-29-ssd1619.json").read_text())
        packets = {int(p["id"]): p["fields"] for p in cfg["packets"]}
        self.assertEqual(set(packets), {1, 2, 4, 32, 33, 37})
        self.assertEqual(int(packets[32]["panel_ic_type"]), 1016)
        self.assertEqual(int(packets[32]["pixel_width"]), 168)
        self.assertEqual(int(packets[32]["pixel_height"]), 384)
        self.assertNotIn("encryption_key", json.dumps(cfg).lower())

    def test_manifest_matches(self):
        for line in (ROOT / "firmware/SHA256SUMS").read_text().splitlines():
            digest, name = line.split(maxsplit=1)
            self.assertEqual(hashlib.sha256((ROOT / "firmware" / name).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
