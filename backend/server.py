"""Web Server Gateway Interface entry point behind Nginx; no web framework."""

import time
import traceback
from http import HTTPStatus
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server, WSGIRequestHandler
from .app import handle

MAX_BODY = 8 * 1024 * 1024
rates = {}


def parameters(value):
    # PHP: parse_str(); duplicate-field rejection is our additional validation.
    fields = parse_qs(value, keep_blank_values=True, max_num_fields=30, errors="strict")
    if any(len(items) != 1 for items in fields.values()):
        raise ValueError("Duplicate fields")
    return {key: items[0] for key, items in fields.items()}


def response(status, body):
    return status, [("Content-Type", "text/plain; charset=utf-8")], body


def dispatch(environ):
    if environ.get("PATH_INFO", "/") != "/":
        return response(404, b"Not found.")
    method = environ["REQUEST_METHOD"]
    if method not in ("GET", "POST"):
        return response(405, b"Method not allowed.")
    query = parameters(environ.get("QUERY_STRING", ""))
    data = {}
    if method == "POST":
        length = int(environ.get("CONTENT_LENGTH") or "0")
        if not 0 < length <= MAX_BODY:
            return response(413, b"Request too large or empty.")
        if (
            environ.get("CONTENT_TYPE", "").split(";")[0]
            != "application/x-www-form-urlencoded"
        ):
            return response(415, b"Unsupported form encoding.")
        now = time.monotonic()
        for key in list(rates):
            if now - rates[key][0] >= 900:
                del rates[key]
        ip = environ.get("HTTP_X_REAL_IP", environ.get("REMOTE_ADDR", ""))
        start, count = rates.get(ip, (now, 0))
        if count >= 120:
            return response(429, b"Too many requests. Please try again later.")
        rates[ip] = (start, count + 1)
        # PHP: file_get_contents("php://input") reads the raw request body.
        raw = environ["wsgi.input"].read(length)
        if len(raw) != length:
            raise ValueError("Incomplete request")
        data = parameters(raw.decode("utf-8"))
    return handle(
        method,
        query.get("page", "home"),
        query,
        data,
        environ.get("HTTP_COOKIE", ""),
        environ.get("HTTP_ORIGIN", ""),
    )


def application(environ, start_response):
    try:
        status, headers, body = dispatch(environ)
    except (ValueError, UnicodeError):
        status, headers, body = response(400, b"Invalid request.")
    except Exception:
        with open("/tmp/camagru-errors.log", "a", encoding="utf-8") as log:
            log.write(traceback.format_exc())
        status, headers, body = response(
            500, b"Temporarily unavailable. Please try again later."
        )
    headers.extend([("Content-Length", str(len(body))), ("Cache-Control", "no-store")])
    # PHP: http_response_code() and header(); echo outputs the response body.
    start_response(f"{status} {HTTPStatus(status).phrase}", headers)
    return [body]


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


# WSGI is a Python interface, not a PHP function. PHP uses its web-server
# SAPI or built-in development server to invoke application code.
if __name__ == "__main__":
    make_server(
        "0.0.0.0", 8000, application, handler_class=QuietHandler
    ).serve_forever()
