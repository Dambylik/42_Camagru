"""Shared controller validation; HTTP state lives in Request."""
import os
from .. import security, mail
from ..http import Problem
from ..models.users import UserModel
from ..models.images import ImageModel
from ..models.comments import CommentModel
from ..models.overlays import OverlayModel


class BaseController:
    def __init__(self, request):
        self.request = request
        self.users = UserModel(request.db)
        self.images = ImageModel(request.db)
        self.comments = CommentModel(request.db)
        self.overlays = OverlayModel(request.db)

    def get_user(self, column, value):
        return self.users.find_by(column, value)

    def require_user(self):
        if not self.request.user:
            raise Problem('Please log in.', 401)

    def fail(self, message, status=400):
        raise Problem(message, status)

    def number(self, value):
        try:
            result = int(value)
            if not 0 < result <= 2147483647:
                raise ValueError()
            return result
        except (TypeError, ValueError):
            self.fail('Invalid number.')

    def email_link(self, email, title, page, token):
        url = os.environ.get('APP_URL', 'http://localhost:8000').rstrip('/')
        mail.send(email, title, f'Follow this link:\n{url}/?page={page}&token={token}\n\nIf you did not request this, ignore this email.')

    def check_email(self, email):
        if len(email) > 254 or not security.EMAIL.fullmatch(email):
            self.fail('Invalid email address.')
        local, domain = email.rsplit('@', 1)
        labels = domain.split('.')
        if len(local) > 64 or local.startswith('.') or local.endswith('.') or ('..' in local) or (len(labels) < 2) or any((not label or len(label) > 63 or label.startswith('-') or label.endswith('-') for label in labels)):
            self.fail('Invalid email address.')

    def check_username(self, username):
        if not security.USERNAME.fullmatch(username):
            self.fail('Username must be 3–30 characters (letters, digits, underscore).')

    def check_password(self, password):
        if not security.strong(password):
            self.fail('Password must be at least 8 characters and include an uppercase letter, a digit, and a special character (maximum 72 UTF-8 bytes).')
