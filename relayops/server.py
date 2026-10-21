"""Loopback-only UI. No authentication: never expose this server publicly."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from .core import Engine, ROOT

def serve(db, port=8765):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass
        def reply(self, status, data, content_type='application/json'):
            raw = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(raw)
        def allowed(self):
            host = self.headers.get('Host', '')
            return host in ('127.0.0.1:' + str(port), 'localhost:' + str(port)) and self.headers.get('Origin') in (None, 'http://' + host)
        def do_GET(self):
            if not self.allowed():
                return self.reply(403, {'error': 'Local requests only'})
            if self.path == '/api/state':
                engine = Engine(db)
                try:
                    self.reply(200, engine.snapshot())
                finally:
                    engine.close()
            elif self.path in ('/', '/app.js', '/style.css'):
                name = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}[self.path]
                mime = {'/': 'text/html; charset=utf-8', '/app.js': 'text/javascript', '/style.css': 'text/css'}[self.path]
                self.reply(200, (ROOT / 'web' / name).read_bytes(), mime)
            else:
                self.reply(404, {'error': 'Not found'})
        def do_POST(self):
            if not self.allowed() or self.headers.get('Content-Type') != 'application/json':
                return self.reply(403, {'error': 'Local JSON requests only'})
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 16384:
                    raise ValueError('Invalid size')
                body = json.loads(self.rfile.read(length))
                engine = Engine(db)
                try:
                    if self.path == '/api/demo':
                        result = [engine.process(row) for row in json.loads((ROOT / 'data/leads.json').read_text())]
                    elif self.path == '/api/decision':
                        result = engine.decide(body['id'], body['decision'], 'local-dashboard-operator')
                    else:
                        return self.reply(404, {'error': 'Not found'})
                    self.reply(200, result)
                finally:
                    engine.close()
            except (ValueError, KeyError, TypeError):
                self.reply(400, {'error': 'Invalid request or conflicting decision'})
    print('RelayOps local demo: http://127.0.0.1:' + str(port), flush=True)
    HTTPServer(('127.0.0.1', port), Handler).serve_forever()
