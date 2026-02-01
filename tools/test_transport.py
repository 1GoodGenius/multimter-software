import unittest
from tools.file_transfer import parse_frame, build_frame

class TestTransportParsing(unittest.TestCase):
    def test_partial_frame(self):
        payload = b'abc'
        ft = 0x10
        frame = build_frame(ft, payload)
        # feed partial data
        for i in range(1, len(frame)):
            partial = frame[:i]
            self.assertIsNone(parse_frame(partial))
        # full frame should parse
        parsed = parse_frame(frame)
        self.assertIsNotNone(parsed)

    def test_crc_mismatch(self):
        payload = b'abc'
        ft = 0x10
        frame = bytearray(build_frame(ft, payload))
        # corrupt a byte in payload
        frame[5] ^= 0xFF
        self.assertIsNone(parse_frame(bytes(frame)))

if __name__ == '__main__':
    unittest.main()
