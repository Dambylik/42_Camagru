from .models.sessions import SessionModel
'Passwords, validation and server-side sessions. No authentication framework.'
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

def session(db, cookie_header):
    sessions = SessionModel(db)
    cookies = SimpleCookie()
    try:
        cookies.load(cookie_header or '')
        sid = cookies['camagru_session'].value if 'camagru_session' in cookies else ''
    except CookieError:
        sid = ''
    now = int(time.time())
    sessions.expire((now,))
    row = sessions.find((token_hash(sid), now)) if TOKEN.fullmatch(sid) else None
    if row is None:
        sid = secrets.token_hex(32)
        row = {'id': token_hash(sid), 'user_id': None, 'session_version': None, 'csrf_token': secrets.token_hex(32), 'expires_at': now + 86400}
        sessions.create_anonymous((row['id'], row['csrf_token'], row['expires_at']))
    return (sid, row)

def rotate(db, row, user=None):
    sessions = SessionModel(db)
    sessions.delete((row['id'],))
    sid = secrets.token_hex(32)
    row.update(id=token_hash(sid), csrf_token=secrets.token_hex(32), user_id=user['id'] if user else None, session_version=user['session_version'] if user else None, expires_at=int(time.time()) + 86400)
    sessions.create_authenticated(tuple((row[k] for k in ('id', 'user_id', 'session_version', 'csrf_token', 'expires_at'))))
    return sid
