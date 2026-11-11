import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from render_ppu import pixel


class RenderTests(unittest.TestCase):
    def test_pattern_planes_and_table_offsets(self):
        data = bytearray(8192)
        data[4096] = 0b01010000
        data[4104] = 0b00110000
        self.assertEqual([pixel(data, 1, 0, x, 0) for x in range(4)], [0, 1, 2, 3])
        self.assertEqual(pixel(data, 0, 0, 1, 0), 0)

    def test_tile_and_row_offsets(self):
        data = bytearray(8192)
        data[16*42+7] = 0x01
        self.assertEqual(pixel(data, 0, 42, 7, 7), 1)
        self.assertEqual(pixel(data, 0, 42, 0, 7), 0)


if __name__ == '__main__':
    unittest.main()
