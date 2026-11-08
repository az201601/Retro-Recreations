import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools' / 'extract_chr.py'


class ChrExtractionTests(unittest.TestCase):
    def test_planes_order_and_manifest(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            # 16 KiB PRG, 8 KiB CHR; first tile's first row is 0,1,2,3,0,1,2,3.
            header = b'NES\x1a' + bytes([1, 1, 0x10, 0]) + bytes(8)
            tile = bytes([0x55] + [0] * 7 + [0x33] + [0] * 7)
            rom = root / 'test.nes'
            rom.write_bytes(header + bytes(16384) + tile + bytes(8192 - 16))
            out = root / 'out'
            subprocess.run([sys.executable, str(SCRIPT), str(rom), str(out)], check=True, capture_output=True)
            manifest = json.loads((out / 'manifest.json').read_text())
            self.assertEqual((manifest['mapper'], manifest['tile_count'], len(manifest['sheets'])), (1, 512, 2))
            data = (out / 'chr_000.png').read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            pos, compressed = 8, b''
            while pos < len(data):
                size = struct.unpack_from('>I', data, pos)[0]
                kind = data[pos+4:pos+8]
                if kind == b'IDAT':
                    compressed += data[pos+8:pos+8+size]
                pos += 12 + size
            row = zlib.decompress(compressed)[:129]
            self.assertEqual(row[:9], bytes([0, 0, 85, 170, 255, 0, 85, 170, 255]))

    def test_rejects_truncated_rom(self):
        with tempfile.TemporaryDirectory() as temp:
            rom = Path(temp) / 'bad.nes'
            rom.write_bytes(b'NES\x1a' + bytes([1, 1]) + bytes(10))
            result = subprocess.run([sys.executable, str(SCRIPT), str(rom), str(Path(temp) / 'out')], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'truncated ROM', result.stderr)


if __name__ == '__main__':
    unittest.main()
