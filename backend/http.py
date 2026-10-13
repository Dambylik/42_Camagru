"""Request state, response construction and controlled failures."""
import json
from . import views

class Problem(Exception):

    def __init__(self, message, status=400):
        self.message, self.status = (message, status)

class Request:

    def __init__(self, method, page, query, data, cookie, origin):
        self.method, self.page, self.query, self.data = (method, page, query, data)
        self.cookie, self.origin = (cookie, origin)
        self.sid, self.session, self.user = ('', None, None)
        self.db = None
        self.message, self.error = ('', False)

    def html(self, body, status=200):
        text = views.layout(self.page.title(), body, self.session['csrf_token'], self.user, self.message, self.error)
        return (status, [('Content-Type', 'text/html; charset=utf-8')], text.encode())

    def redirect(self, page):
        return (303, [('Location', '/?page=' + page)], b'')

    def json(self, result, status=200):
        return (status, [('Content-Type', 'application/json')], json.dumps(result, default=str).encode())
