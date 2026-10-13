"""Password checks, form validation and login sessions."""
from . import database
import hashlib
import re
import secrets
import time
from http.cookies import SimpleCookie, CookieError
import bcrypt
USERNAME = re.compile('[A-Za-z0-9_]{3,30}\\Z')
EMAIL = re.compile("[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\\Z")
TOKEN = re.compile('[a-f0-9]{64}\\Z')

def strong(password):
    return 8 <= len(password) and len(password.encode('utf-8')) <= 72 and re.search('[A-Z]', password) and re.search('[0-9]', password) and re.search('[^A-Za-z0-9]', password)

def password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('ascii')

def password_matches(password, hashed):
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('ascii'))
    except (ValueError, UnicodeError):
        return False

def token_hash(token):
    return hashlib.sha256(token.encode('ascii')).hexdigest()

def session(connection, cookie_header):
    cookies = SimpleCookie()
    try:
        cookies.load(cookie_header or '')
        sid = cookies['camagru_session'].value if 'camagru_session' in cookies else ''
    except CookieError:
        sid = ''
    now = int(time.time())
    database.sessions_expire(connection, (now,))
    row = database.sessions_find(connection, (token_hash(sid), now)) if TOKEN.fullmatch(sid) else None
    if row is None:
        sid = secrets.token_hex(32)
        row = {'id': token_hash(sid), 'user_id': None, 'session_version': None, 'csrf_token': secrets.token_hex(32), 'expires_at': now + 86400}
        database.sessions_create_anonymous(connection, (row['id'], row['csrf_token'], row['expires_at']))
    return (sid, row)

def rotate(connection, row, user=None):
    database.sessions_delete(connection, (row['id'],))
    sid = secrets.token_hex(32)
    row.update(id=token_hash(sid), csrf_token=secrets.token_hex(32), user_id=user['id'] if user else None, session_version=user['session_version'] if user else None, expires_at=int(time.time()) + 86400)
    database.sessions_create_authenticated(connection, tuple((row[k] for k in ('id', 'user_id', 'session_version', 'csrf_token', 'expires_at'))))
    return sid

class Problem(Exception):

    def __init__(self, message, status=400):
        self.message, self.status = (message, status)

def fail(message, status=400):
    raise Problem(message, status)

def number(value):
    try:
        result = int(value)
        if not 0 < result <= 2147483647:
            raise ValueError()
        return result
    except (TypeError, ValueError):
        fail('Invalid number.')

def check_email(email):
    if len(email) > 254 or not EMAIL.fullmatch(email):
        fail('Invalid email address.')
    local, domain = email.rsplit('@', 1)
    labels = domain.split('.')
    if len(local) > 64 or local.startswith('.') or local.endswith('.') or ('..' in local) or (len(labels) < 2) or any((not label or len(label) > 63 or label.startswith('-') or label.endswith('-') for label in labels)):
        fail('Invalid email address.')

def check_username(username):
    if not USERNAME.fullmatch(username):
        fail('Username must be 3–30 characters (letters, digits, underscore).')

def check_password(password):
    if not strong(password):
        fail('Password must be at least 8 characters and include an uppercase letter, a digit, and a special character (maximum 72 UTF-8 bytes).')
