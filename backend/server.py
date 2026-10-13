"""Bounded HTTP server using Python's standard library."""
import mimetypes
import os
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit
from .application import Request, handle, ROOT
from .bootstrap import initialize

MAX_BODY = 8 * 1024 * 1024
rates = {}
rate_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def setup(self):
        super().setup()
        self.connection.settimeout(20)

    def respond(self, status, headers, body):
        self.send_response(status)
        for key, value in headers:
            self.send_header(key,value)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','same-origin')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        self.send_header('Cache-Control','no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self.run_request()

    def do_POST(self):
        self.run_request()

    def do_HEAD(self):
        self.respond(405, [('Allow','GET, POST')], b'')

    def run_request(self):
        try:
            url = urlsplit(self.path)
            if url.path == '/health' and self.command == 'GET':
                self.respond(200,[('Content-Type','text/plain')],b'ok')
                return
            if url.path not in ('/','/index.php','/index.html'):
                self.static(url.path)
                return
            query = self.parameters(url.query)
            data = {}
            if self.command == 'POST':
                if self.headers.get('Transfer-Encoding'):
                    self.respond(400,[],b'Unsupported request encoding.')
                    return
                length = int(self.headers.get('Content-Length','0'))
                if not 0 < length <= MAX_BODY:
                    self.respond(413,[],b'Request too large or empty.')
                    return
                if self.headers.get('Content-Type','').split(';')[0] != 'application/x-www-form-urlencoded':
                    self.respond(415,[],b'Unsupported form encoding.')
                    return
                if not self.allowed_rate():
                    self.respond(429,[('Retry-After','900')],b'Too many requests. Please try again later.')
                    return
                raw = self.rfile.read(length)
                if len(raw) != length:
                    raise ValueError('Incomplete request')
                data = self.parameters(raw.decode('utf-8'))
            request = Request(self.command,query.get('page','home'),query,data,
                              self.headers.get('Cookie',''),self.headers.get('Origin',''))
            self.respond(*handle(request))
        except (ValueError,UnicodeError):
            self.respond(400,[],b'Invalid request.')
        except (BrokenPipeError,ConnectionResetError,TimeoutError):
            pass
        except Exception:
            with open(os.environ.get('ERROR_LOG','/tmp/camagru-errors.log'),'a',encoding='utf-8') as log:
                log.write(traceback.format_exc())
            self.respond(500,[('Content-Type','text/html; charset=utf-8')],
                         b'<!DOCTYPE html><html lang="en"><title>Unavailable</title><h1>Temporarily unavailable</h1><p>Please try again later.</p></html>')

    def parameters(self, value):
        fields = parse_qs(value,keep_blank_values=True,max_num_fields=30,errors='strict')
        if any(len(values) != 1 for values in fields.values()):
            raise ValueError('Duplicate fields')
        return {key:values[0] for key,values in fields.items()}

    def allowed_rate(self):
        now = time.monotonic()
        ip = self.client_address[0]
        with rate_lock:
            for key in list(rates):
                if now - rates[key][0] >= 900:
                    del rates[key]
            start,count = rates.get(ip,(now,0))
            if count >= 120:
                return False
            rates[ip] = (start,count+1)
        return True

    def static(self, url_path):
        if self.command != 'GET':
            self.respond(405,[],b'Method not allowed.')
            return
        relative = unquote(url_path).lstrip('/')
        path = (ROOT / relative).resolve()
        allowed = relative.startswith(('css/','js/','overlays/','uploads/')) or relative == 'cat-cartoon.png'
        if not allowed or ROOT.resolve() not in path.parents or any(p.startswith('.') for p in Path(relative).parts) or not path.is_file():
            self.respond(404,[],b'Not found.')
            return
        if path.suffix.lower() not in {'.css','.js','.png','.jpg','.jpeg','.webp'}:
            self.respond(404,[],b'Not found.')
            return
        mime = mimetypes.guess_type(str(path))[0] or 'application/octet-stream'
        self.respond(200,[('Content-Type',mime)],path.read_bytes())


class Server(ThreadingHTTPServer):
    daemon_threads = True
    slots = threading.BoundedSemaphore(16)

    def process_request(self, request, client_address):
        self.slots.acquire()
        try:
            super().process_request(request,client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request,client_address)
        finally:
            self.slots.release()

    def handle_error(self, request, client_address):
        pass


def main():
    initialize()
    Server(('0.0.0.0',8000),Handler).serve_forever()


if __name__ == '__main__':
    main()
