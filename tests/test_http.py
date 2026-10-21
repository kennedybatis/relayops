import json
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from relayops.core import ROOT

class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            cls.port = sock.getsockname()[1]
        script = 'from relayops.server import serve; serve(' + repr(str(Path(cls.temp.name) / 'demo.db')) + ',' + str(cls.port) + ')'
        cls.process = subprocess.Popen([sys.executable, '-c', script], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cls.base = 'http://127.0.0.1:' + str(cls.port)
        for _ in range(100):
            try:
                with urlopen(cls.base + '/api/state', timeout=1):
                    return
            except OSError:
                time.sleep(.03)
        cls.process.terminate()
        raise RuntimeError('Local server did not start')
    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.communicate(timeout=5)
        cls.temp.cleanup()
    def test_local_workflow(self):
        req = Request(self.base + '/api/demo', data=b'{}', headers={'Content-Type': 'application/json'})
        with urlopen(req) as response:
            rows = json.load(response)
        self.assertEqual(len(rows), 6)
        req = Request(self.base + '/api/decision', data=json.dumps({'id':rows[0]['approval_id'], 'decision':'approved'}).encode(), headers={'Content-Type':'application/json'})
        with urlopen(req) as response:
            self.assertEqual(json.load(response)['status'], 'approved')
        with urlopen(self.base + '/api/state') as response:
            state = json.load(response)
        self.assertEqual(state['outbox_count'], 1)
        self.assertTrue(state['audit_valid'])
    def test_cross_origin_write_rejected(self):
        req = Request(self.base + '/api/demo', data=b'{}', headers={'Content-Type':'application/json','Origin':'https://untrusted.invalid'})
        with self.assertRaises(HTTPError) as error:
            urlopen(req)
        self.assertEqual(error.exception.code, 403)
    def test_invalid_host_rejected(self):
        req = Request(self.base + '/api/state', headers={'Host':'untrusted.invalid'})
        with self.assertRaises(HTTPError) as error:
            urlopen(req)
        self.assertEqual(error.exception.code, 403)
    def test_filesystem_not_exposed(self):
        with self.assertRaises(HTTPError) as error:
            urlopen(self.base + '/data/leads.json')
        self.assertEqual(error.exception.code, 404)
    def test_invalid_json_does_not_write(self):
        req = Request(self.base + '/api/decision', data=b'not-json', headers={'Content-Type':'application/json'})
        with self.assertRaises(HTTPError) as error:
            urlopen(req)
        self.assertEqual(error.exception.code, 400)

if __name__ == '__main__':
    unittest.main()
