import unittest
from tools.file_transfer import build_frame, crc16, chunk_file, parse_frame

class TestFileTransferHelpers(unittest.TestCase):
    def test_crc_and_frame_roundtrip(self):
        payload = b'hello'
        ft = 0x31
        frame = build_frame(ft, payload)
        parsed = parse_frame(frame)
        self.assertIsNotNone(parsed)
        ftype, pl = parsed
        self.assertEqual(ftype, ft)
        self.assertEqual(pl, payload)

    def test_chunking(self):
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'a' * 5000)
            path = f.name
        chunks = list(chunk_file(path, chunk_size=1024))
        self.assertTrue(len(chunks) >= 5)
        self.assertEqual(sum(len(c) for _, c in chunks), 5000)

if __name__ == '__main__':
    unittest.main()
