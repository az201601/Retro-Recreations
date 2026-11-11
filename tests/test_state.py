import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from inspect_fceumm_state import parse_state


def state(payload):
    return b'FCS\xff' + struct.pack('<I', len(payload)) + bytes(8) + payload


class StateTests(unittest.TestCase):
    def test_parse_fields(self):
        field = b'PRAM' + struct.pack('<I', 3) + b'abc'
        chunk = bytes([3]) + struct.pack('<I', len(field)) + field
        self.assertEqual(parse_state(state(chunk))[(3, b'PRAM')], b'abc')

    def test_rejects_truncated_field(self):
        field = b'PRAM' + struct.pack('<I', 4) + b'abc'
        chunk = bytes([3]) + struct.pack('<I', len(field)) + field
        with self.assertRaises(ValueError):
            parse_state(state(chunk))

    def test_rejects_truncated_chunk(self):
        with self.assertRaises(ValueError):
            parse_state(state(bytes([3]) + struct.pack('<I', 20)))


if __name__ == '__main__':
    unittest.main()
