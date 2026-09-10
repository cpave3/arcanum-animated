from pathlib import Path
import subprocess
import sys
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


class ViewerServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.process = subprocess.Popen([sys.executable, str(ROOT / 'serve.py'), '--port', '0'],
                                       cwd='/tmp', stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        cls.url = cls.process.stdout.readline().strip().removeprefix('Rift viewer: ')
        cls.path = '/assets/rift/purple.webm'
        cls.data = (ROOT / cls.path.lstrip('/')).read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.wait(timeout=5)
        cls.process.stdout.close()

    def test_page_and_full_video_from_another_working_directory(self):
        with urlopen(self.url) as response:
            page = response.read()
            self.assertIn(b'id="library-list"', page)
            self.assertIn(b'id="workspace"', page)
        with urlopen(self.url + self.path) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers['Accept-Ranges'], 'bytes')
            self.assertEqual(response.headers['Content-Type'], 'video/webm')
            self.assertEqual(response.read(), self.data)

    def test_byte_ranges_return_only_requested_video_bytes(self):
        size = len(self.data)
        for header, start, end in [('bytes=0-31', 0, 31), ('bytes=-16', size-16, size-1),
                                   (f'bytes={size-17}-', size-17, size-1),
                                   (f'bytes={size-10}-{size+100}', size-10, size-1)]:
            with self.subTest(header=header):
                request = Request(self.url + self.path, headers={'Range': header})
                with urlopen(request) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.headers['Content-Range'], f'bytes {start}-{end}/{size}')
                    self.assertEqual(int(response.headers['Content-Length']), end-start+1)
                    self.assertEqual(response.read(), self.data[start:end+1])

    def test_head_range_has_headers_but_no_body(self):
        request = Request(self.url + self.path, method='HEAD', headers={'Range': 'bytes=10-19'})
        with urlopen(request) as response:
            self.assertEqual(response.status, 206)
            self.assertEqual(response.headers['Content-Length'], '10')
            self.assertEqual(response.read(), b'')

    def test_unsatisfiable_range_returns_416(self):
        request = Request(self.url + self.path, headers={'Range': f'bytes={len(self.data)}-'})
        with self.assertRaises(HTTPError) as caught:
            urlopen(request)
        with caught.exception as response:
            self.assertEqual(response.code, 416)
            self.assertEqual(response.headers['Content-Range'], f'bytes */{len(self.data)}')

    def test_stale_conditional_range_falls_back_to_full_response(self):
        request = Request(self.url + self.path, headers={
            'Range': 'bytes=0-10', 'If-Range': 'Thu, 01 Jan 1970 00:00:00 GMT'})
        with urlopen(request) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), self.data)


if __name__ == '__main__':
    unittest.main()
